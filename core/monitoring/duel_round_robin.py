#!/usr/bin/env python3
"""
Round-robin duel audit for formulas and internal fusions.

- No external candidates.
- No auto-apply of winners.
- Exhaustive pairwise comparisons inside each parameter group.
- Reports per-parameter winner only if it beats all others.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import random
import importlib
import inspect
import itertools
import pkgutil
from types import SimpleNamespace
from typing import Dict, List, Optional, Any, Tuple

from core.bus import formula_hierarchy as fh
from core.bus.parametros_canonicos import normalizar_lista_parametros_entrada
from core.monitoring.formula_duel_engine import FormulaDuelEngine
from core.indices.index_catalog import INDEX_CATALOG


@dataclass
class MatchResult:
    a_id: str
    b_id: str
    a_score: float
    b_score: float
    winner_id: str
    winner_score: float
    kind: str  # "formula" | "fusion"


def _make_samples(reqs: List[str], n: int, rng: random.Random) -> List[Dict[str, Any]]:
    reqs = normalizar_lista_parametros_entrada(reqs or [])
    samples: List[Dict[str, Any]] = []
    contexto_stub = SimpleNamespace(
        estacion=SimpleNamespace(latitud=0.0, longitud=0.0, altitud=0.0),
        latitud=0.0,
        longitud=0.0,
        altitud=0.0,
    )
    for _ in range(n):
        base_temp = rng.uniform(-10.0, 35.0)
        humedad = rng.uniform(20.0, 100.0)
        viento = rng.uniform(0.0, 12.0)
        radiacion = rng.uniform(0.0, 900.0)
        presion = rng.uniform(950.0, 1030.0)
        fila: Dict[str, Any] = {}
        for req in reqs:
            req_lower = req.lower()
            if req in ("temperatura", "temperatura_bulbo_seco"):
                fila[req] = base_temp
            elif req == "temperatura_bulbo_humedo":
                fila[req] = base_temp - rng.uniform(0.0, 5.0)
            elif req == "temperatura_globo_negro":
                fila[req] = base_temp + rng.uniform(0.0, 10.0)
            elif req in ("humedad", "hr", "humedad_relativa"):
                fila[req] = humedad
            elif req in ("viento", "velocidad_viento_10m"):
                fila[req] = viento
            elif req in ("radiacion", "radiacion_solar_global"):
                fila[req] = radiacion
            elif req in ("presion", "presion_hpa"):
                fila[req] = presion
            elif "fecha" in req_lower or "datetime" in req_lower or "tsv" in req_lower or req_lower in ("dt", "timestamp"):
                fila[req] = datetime.now()
            elif "hora" in req_lower:
                fila[req] = rng.uniform(0.0, 23.99)
            elif req_lower == "dia_ano":
                fila[req] = rng.randint(1, 365)
            elif req_lower == "contexto":
                fila[req] = contexto_stub
            elif (
                req_lower in ("params", "parametros", "data", "datos", "sensores", "inputs")
                or ("param" in req_lower and "temperatura" not in req_lower)
            ):
                fila[req] = {}
            elif req == "nubosidad":
                fila[req] = rng.uniform(0.0, 1.0)
            elif req == "altitud":
                fila[req] = rng.uniform(0.0, 1000.0)
            elif req == "latitud":
                fila[req] = rng.uniform(-90.0, 90.0)
            elif req == "longitud":
                fila[req] = rng.uniform(-180.0, 180.0)
            elif req == "uso_horario":
                fila[req] = 1
            elif req == "emitancia_ropa":
                fila[req] = 0.95
            else:
                fila[req] = 0.0
        samples.append(fila)
    return samples


FORMULA_HIERARCHY = fh.FORMULA_HIERARCHY
FormulaType = getattr(fh, "F\u00f3rmula")


@dataclass
class FormulaStub:
    nombre_tecnico: str
    nombre_legible: str
    modulo: str
    referencia: str
    precision: str
    velocidad: int
    rango_validez: Tuple[Optional[float], Optional[float]]
    requisitos_datos: List[str]

    def __post_init__(self) -> None:
        setattr(self, "m\u00f3dulo", self.modulo)


def _iter_modules(package_name: str) -> List[str]:
    modules: List[str] = []
    try:
        pkg = importlib.import_module(package_name)
        for mod in pkgutil.walk_packages(pkg.__path__, package_name + "."):
            modules.append(mod.name)
    except Exception:
        return []
    return modules


def _is_formula_candidate(fn_name: str) -> bool:
    tokens = (
        "indice_",
        "calcular_",
        "utci",
        "wbgt",
        "rocio",
        "presion",
        "radiacion",
        "evapo",
        "viento",
        "humedad",
        "temperatura",
        "densidad",
        "vpd",
        "entalpia",
        "humedex",
    )
    return any(t in fn_name for t in tokens)


def _infer_parametro(fn_name: str, module_name: str, catalog_keys: List[str]) -> Optional[str]:
    name = fn_name.lower()
    module = module_name.lower()

    # Normalizar prefijos comunes y guion bajo inicial
    normalized = name.lstrip("_")

    if any(t in name for t in ("utci", "wbgt", "apparent", "steadman", "wind_chill", "heat_index", "humidex")):
        return "sensacion_termica"
    if any(t in name for t in ("radiacion", "rest2", "irradi", "lw_", "sw_", "uv_")):
        return "radiacion_solar"
    if "rocio" in name or "dew" in name:
        return "punto_rocio"
    if "presion_vapor" in name or "vapor" in name:
        return "presion_vapor"
    if "vpd" in name or "deficit_presion_vapor" in name:
        return "vpd"
    if "evapo" in name or "et0" in name or "penman" in name:
        return "evapotranspiracion"
    if "densidad_aire" in name or "densidad" in name:
        return "densidad_aire"
    if "humedad_absoluta" in name:
        return "humedad_absoluta"
    if "entalpia" in name:
        return "entalpia_aire"
    if "nubosidad" in name:
        return "nubosidad"

    for prefix in ("indice_", "calcular_"):
        if normalized.startswith(prefix):
            candidate = normalized[len(prefix):]
            if candidate in catalog_keys:
                return candidate
            # Si no esta en catalogo, aun lo usamos como parametro nuevo
            if candidate:
                return candidate

    # Use catalog keys as a fallback (longest-first, avoid ultra-generic tokens)
    for key in catalog_keys:
        if len(key) < 6:
            continue
        if key in name or key in module:
            return key

    # Ultimo recurso: usar el propio nombre como parametro
    if normalized:
        return normalized

    return None


def _discover_formulas() -> Tuple[Dict[str, List[FormulaStub]], List[str]]:
    discovered: Dict[str, List[FormulaStub]] = {}
    unmapped: List[str] = []
    catalog_keys = sorted(set(INDEX_CATALOG.keys()), key=len, reverse=True)
    modules = _iter_modules("core.indices")
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not _is_formula_candidate(name):
                continue
            parametro = _infer_parametro(name, module_name, catalog_keys)
            if not parametro:
                unmapped.append(f"{module_name}.{name}")
                continue
            try:
                sig = inspect.signature(obj)
                inputs = [
                    p.name
                    for p in sig.parameters.values()
                    if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                ]
            except Exception:
                inputs = []
            stub = FormulaStub(
                nombre_tecnico=name,
                nombre_legible=name,
                modulo=module_name,
                referencia="discovered",
                precision="unknown",
                velocidad=5,
                rango_validez=(None, None),
                requisitos_datos=inputs,
            )
            discovered.setdefault(parametro, []).append(stub)
    return discovered, unmapped


def _select_range_formula(formulas: List[Any]) -> Any:
    def span(f):
        try:
            a, b = f.rango_validez
            if a is None or b is None:
                return float("inf")
            return abs(b - a)
        except Exception:
            return float("inf")

    return max(formulas, key=span)


def _formula_id(formula) -> str:
    return formula.nombre_tecnico


def _score_formula(engine: FormulaDuelEngine, formula, samples: List[Dict[str, Any]]) -> Optional[float]:
    score = engine._evaluar_formula(formula, samples, system=None)
    return score.score if score else None


def _calc_outputs(engine: FormulaDuelEngine, formula, samples: List[Dict[str, Any]]) -> List[Optional[float]]:
    outputs: List[Optional[float]] = []
    reqs = formula.requisitos_datos or []
    for sample in samples:
        args = [sample.get(req) for req in reqs]
        if any(v is None for v in args):
            outputs.append(None)
            continue
        res = engine._call_func(engine._resolver_funcion(formula), args)
        res = engine._extract_numeric_value(res)
        outputs.append(res if isinstance(res, (int, float)) else None)
    return outputs


def _score_outputs(engine: FormulaDuelEngine, formula, outputs: List[Optional[float]]) -> Optional[float]:
    vals = [v for v in outputs if isinstance(v, (int, float))]
    if not vals:
        return None
    robustez = len(vals) / max(1, len(outputs))
    in_range = sum(1 for v in vals if engine._en_rango(formula, v))
    precision = in_range / max(1, len(vals))
    estabilidad = engine._score_estabilidad(vals)
    eficiencia = min(1.0, max(0.0, formula.velocidad / 10.0))
    score = (
        engine.peso_precision * precision
        + engine.peso_estabilidad * estabilidad
        + engine.peso_eficiencia * eficiencia
    ) * robustez
    return score


def _tournament_winner(contenders: Dict[str, float], group_size: int) -> Tuple[List[str], Dict[str, Any]]:
    if not contenders:
        return [], {"rounds": 0, "group_size": group_size}
    ids = list(contenders.keys())
    meta = {"rounds": 0, "group_size": group_size}
    while len(ids) > 1:
        meta["rounds"] += 1
        next_ids: List[str] = []
        for i in range(0, len(ids), group_size):
            group = ids[i:i + group_size]
            if not group:
                continue
            top_score = max(contenders[g] for g in group)
            winners = [g for g in group if contenders[g] == top_score]
            next_ids.extend(winners)
        ids = next_ids
        if not ids:
            break
    return ids, meta


def run_round_robin(
    samples_per_param: int = 50,
    seed: int = 42,
    output_path: Optional[Path] = None,
    include_discovered: bool = True,
    max_combination_size: Optional[int] = None,
    max_total_combinations: int = 5000,
    use_tournament: bool = True,
    tournament_group_size: int = 12,
    parametros: Optional[List[str]] = None,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    engine = FormulaDuelEngine(Path.cwd())
    engine.dry_run = True
    if include_discovered:
        discovered, unmapped = _discover_formulas()
    else:
        discovered, unmapped = {}, []
    report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "parameters": {},
        "config": {
            "samples_per_param": samples_per_param,
            "seed": seed,
            "externals": False,
            "auto_apply": False,
            "include_discovered": include_discovered,
            "discovered_unmapped_count": len(unmapped),
            "discovered_unmapped": unmapped,
            "max_combination_size": max_combination_size,
            "max_total_combinations": max_total_combinations,
            "combination_types": ["avg", "weighted_score", "complement", "subfactor"],
            "use_tournament": use_tournament,
            "tournament_group_size": tournament_group_size,
            "parametros": parametros,
        },
    }

    all_parametros = sorted(set(FORMULA_HIERARCHY.keys()).union(discovered.keys()))
    if parametros:
        param_set = {p.lower() for p in parametros}
        all_parametros = [p for p in all_parametros if p.lower() in param_set]

    for parametro in all_parametros:
        jerarquia = FORMULA_HIERARCHY.get(parametro, {})
        formulas = list(jerarquia.values())
        formulas.extend(discovered.get(parametro, []))
        unique = {}
        for f in formulas:
            unique[getattr(f, "nombre_tecnico", str(f))] = f
        formulas = list(unique.values())
        formulas = [f for f in formulas if engine._resolver_funcion(f)]
        if not formulas:
            report["parameters"][parametro] = {
                "status": "no_formulas",
                "matches": [],
                "winner": None,
            }
            continue

        reqs = []
        for f in formulas:
            reqs.extend(f.requisitos_datos or [])
        samples = _make_samples(reqs, samples_per_param, rng)

        scores: Dict[str, float] = {}
        matches: List[Dict[str, Any]] = []
        contenders: Dict[str, float] = {}

        # Precompute formula scores
        for f in formulas:
            s = _score_formula(engine, f, samples)
            if s is not None:
                scores[_formula_id(f)] = s
                contenders[_formula_id(f)] = s

        # Build combination contenders (all internal combinations)
        outputs_cache: Dict[str, List[Optional[float]]] = {}
        for f in formulas:
            outputs_cache[_formula_id(f)] = _calc_outputs(engine, f, samples)

        max_k = max_combination_size or len(formulas)
        combos_checked = 0
        combos_skipped = False

        for k in range(2, min(max_k, len(formulas)) + 1):
            for combo in itertools.combinations(formulas, k):
                combos_checked += 1
                if combos_checked > max_total_combinations:
                    combos_skipped = True
                    break

                combo_ids = [_formula_id(f) for f in combo]
                outs_list = [outputs_cache.get(cid) or [] for cid in combo_ids]
                if any(not outs for outs in outs_list):
                    continue

                range_formula = _select_range_formula(list(combo))

                # AVG combination
                avg_outs: List[Optional[float]] = []
                for idx in range(len(samples)):
                    vals = [outs[idx] for outs in outs_list if outs[idx] is not None]
                    avg_outs.append(sum(vals) / len(vals) if vals else None)
                avg_score = _score_outputs(engine, range_formula, avg_outs)
                if avg_score is not None:
                    combo_id = f"COMBO_AVG_{'_'.join(combo_ids)}"
                    contenders[combo_id] = float(avg_score)

                # WEIGHTED by base scores
                weights = [scores.get(cid, 1.0) for cid in combo_ids]
                total_w = sum(weights) if weights else 0.0
                if total_w > 0:
                    weighted_outs: List[Optional[float]] = []
                    for idx in range(len(samples)):
                        vals = []
                        for w, outs in zip(weights, outs_list):
                            v = outs[idx]
                            if v is not None:
                                vals.append((w, v))
                        if not vals:
                            weighted_outs.append(None)
                            continue
                        num = sum(w * v for w, v in vals)
                        den = sum(w for w, _ in vals)
                        weighted_outs.append(num / den if den else None)
                    weighted_score = _score_outputs(engine, range_formula, weighted_outs)
                    if weighted_score is not None:
                        combo_id = f"COMBO_WEIGHTED_{'_'.join(combo_ids)}"
                        contenders[combo_id] = float(weighted_score)

                # Pair-only fusion styles
                if k == 2:
                    outs_a = outs_list[0]
                    outs_b = outs_list[1]

                    complement_outs: List[Optional[float]] = []
                    subfactor_outs: List[Optional[float]] = []
                    for va, vb in zip(outs_a, outs_b):
                        if va is None or vb is None:
                            complement_outs.append(None)
                            subfactor_outs.append(None)
                            continue
                        if va != 0:
                            factor = (vb - va) / va
                            factor = max(-0.2, min(0.2, factor))
                            complement_outs.append(va * (1.0 + factor))
                        else:
                            complement_outs.append(va)
                        subfactor_outs.append(va + (0.1 * vb))

                    complement_score = _score_outputs(engine, range_formula, complement_outs)
                    if complement_score is not None:
                        combo_id = f"COMBO_COMPLEMENT_{'_'.join(combo_ids)}"
                        contenders[combo_id] = float(complement_score)

                    subfactor_score = _score_outputs(engine, range_formula, subfactor_outs)
                    if subfactor_score is not None:
                        combo_id = f"COMBO_SUBFACTOR_{'_'.join(combo_ids)}"
                        contenders[combo_id] = float(subfactor_score)

            if combos_skipped:
                break

        tournament_meta = None
        if use_tournament:
            winners, tournament_meta = _tournament_winner(contenders, tournament_group_size)
            if len(winners) == 1:
                winner = {"id": winners[0], "wins": None, "losses": 0}
            elif len(winners) > 1:
                winner = {"id": None, "note": "no_unique_winner", "undefeated": winners}
            else:
                winner = None
        else:
            # Pairwise matches across ALL contenders (formulas + fusions)
            contender_ids = list(contenders.keys())
            for i in range(len(contender_ids)):
                for j in range(i + 1, len(contender_ids)):
                    a_id = contender_ids[i]
                    b_id = contender_ids[j]
                    a_score = contenders.get(a_id)
                    b_score = contenders.get(b_id)
                    if a_score is None or b_score is None:
                        continue
                    if a_score >= b_score:
                        winner_id, winner_score = a_id, a_score
                    else:
                        winner_id, winner_score = b_id, b_score
                    matches.append({
                        "a": a_id,
                        "b": b_id,
                        "a_score": a_score,
                        "b_score": b_score,
                        "winner": winner_id,
                        "winner_score": winner_score,
                        "kind": "contender",
                    })

            # Determine winner only if it beats all others
            contenders_set = {m["a"] for m in matches}.union({m["b"] for m in matches})
            if not contenders_set and len(contenders) == 1:
                contenders_set = set(contenders.keys())
            wins = {c: 0 for c in contenders_set}
            losses = {c: 0 for c in contenders_set}
            for m in matches:
                w = m["winner"]
                l = m["a"] if w == m["b"] else m["b"]
                wins[w] = wins.get(w, 0) + 1
                losses[l] = losses.get(l, 0) + 1

            undefeated = [c for c in contenders_set if losses.get(c, 0) == 0]
            winner = None
            if len(undefeated) == 1:
                winner = {
                    "id": undefeated[0],
                    "wins": wins.get(undefeated[0], 0),
                    "losses": 0,
                }
            elif len(undefeated) > 1:
                winner = {
                    "id": None,
                    "note": "no_unique_winner",
                    "undefeated": undefeated,
                }

        report["parameters"][parametro] = {
            "status": "ok",
            "matches": matches,
            "contenders": contenders,
            "combination_stats": {
                "combos_checked": combos_checked,
                "combos_skipped": combos_skipped,
                "max_total_combinations": max_total_combinations,
                "max_combination_size": max_k,
            },
            "tournament": tournament_meta,
            "winner": winner,
        }

    if output_path:
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return report


if __name__ == "__main__":
    out_path = Path.cwd() / "data" / "duel_round_robin_report.json"
    report = run_round_robin(samples_per_param=50, seed=42, output_path=out_path)
    print("Round-robin report written to:", out_path)
    for parametro, data in report["parameters"].items():
        winner = data.get("winner")
        if winner and winner.get("id"):
            print(f"{parametro}: winner={winner['id']} wins={winner['wins']}")
        else:
            print(f"{parametro}: no unique winner")
