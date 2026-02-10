from __future__ import annotations

import importlib
import json
import logging
import math
import statistics
import time
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from core.bus.formula_hierarchy import FORMULA_HIERARCHY, NivelElite, Fórmula
from core.monitoring.formula_change_tracker import FormulaChangeTracker
from core.monitoring.formula_override_manager import FormulaOverrideManager
from core.monitoring.formula_candidate_registry import FormulaCandidateRegistry
from core.monitoring.sensor_data_bridge import SensorDataBridge
from core.monitoring.formula_optimizer import FormulaOptimizer
from core.monitoring.thermodynamic_judge import ThermodynamicJudge

# ✅ Importar recorders para guardar duelos
try:
    from core.monitoring.history_recorders import get_recorders
    RECORDERS_AVAILABLE = True
except Exception:
    RECORDERS_AVAILABLE = False

logger = logging.getLogger("meteoser.formula_duel")


@dataclass
class DuelScore:
    score: float
    estabilidad: float
    precision: float
    robustez: float
    eficiencia: float
    validos: int
    total: int


class FormulaDuelEngine:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._state_path = base_dir / "data" / "formula_duel_state.json"
        self._results_path = base_dir / "data" / "formula_duel_results.json"
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_run = None
        self._pending: Dict[str, Dict[str, Any]] = {}
        self._load_state()
        self._change_tracker = FormulaChangeTracker(base_dir)
        self._override_manager = FormulaOverrideManager(base_dir)
        self._candidate_registry = FormulaCandidateRegistry(base_dir)
        self._data_bridge = SensorDataBridge(base_dir)
        self._optimizer = FormulaOptimizer()  # ✅ Auto-mejora pre-duelo
        self._judge = ThermodynamicJudge()

        # Configurable (no fijo): valores por defecto razonables
        self.peso_precision = 0.6
        self.peso_estabilidad = 0.3
        self.peso_eficiencia = 0.1
        self.max_parametros_por_run = 4
        self.sample_size = 100
        self.audit_days = 7
        self.margin_base = 0.2
        self.dry_run = True
        self.clean_window_seconds = 6 * 3600
        self.min_clean_samples = 30
        # Validación multi-etapa (anti aceptación a ciegas)
        self.validation_required_wins = 3
        self.validation_min_score_delta = 0.01
        self.validation_min_robustez = 0.6
        self.validation_min_precision = 0.6
        self.validation_min_estabilidad = 0.4
        self.validation_rounds = 3
        self.validation_round_min_wins = 2
        self.validation_round_min_samples = 20

    def _load_state(self) -> None:
        if not self._state_path.exists():
            return
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            self._last_run = data.get("last_run")
            self._pending = data.get("pending") or {}
        except Exception:
            logger.exception("No se pudo cargar formula_duel_state.json")
            self._last_run = None
            self._pending = {}

    def _save_state(self) -> None:
        try:
            payload = {"last_run": self._last_run, "pending": self._pending}
            self._state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("No se pudo guardar formula_duel_state.json")

    def _reset_pendiente(self, parametro: str) -> None:
        if parametro in self._pending:
            del self._pending[parametro]

    def _registrar_pendiente(
        self,
        parametro: str,
        ganador_id: str,
        score: DuelScore,
        delta: float,
        escenarios: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Registra una victoria pendiente y decide si se autovalida."""
        if (
            score.robustez < self.validation_min_robustez
            or score.precision < self.validation_min_precision
            or score.estabilidad < self.validation_min_estabilidad
            or delta < self.validation_min_score_delta
        ):
            logger.warning(
                "⚠️ Validación: incoherencias graves para %s (%s). "
                "robustez=%.3f precision=%.3f estabilidad=%.3f delta=%.4f",
                parametro,
                ganador_id,
                score.robustez,
                score.precision,
                score.estabilidad,
                delta,
            )
            self._reset_pendiente(parametro)
            return False

        pendiente = self._pending.get(parametro)
        if not pendiente or pendiente.get("ganador_id") != ganador_id:
            pendiente = {
                "ganador_id": ganador_id,
                "wins": 1,
                "last_ts": time.time(),
                "escenarios": escenarios,
            }
        else:
            pendiente["wins"] = int(pendiente.get("wins", 0)) + 1
            pendiente["last_ts"] = time.time()

        self._pending[parametro] = pendiente
        self._save_state()

        if pendiente["wins"] >= self.validation_required_wins:
            logger.info(
                "✅ Validación multi-etapa superada para %s (%s) con %s victorias",
                parametro,
                ganador_id,
                pendiente["wins"],
            )
            return True

        logger.info(
            "⏳ Validación en curso para %s (%s): %s/%s victorias",
            parametro,
            ganador_id,
            pendiente["wins"],
            self.validation_required_wins,
        )
        return False

    def is_due(self) -> bool:
        if not self._last_run:
            return True
        try:
            last = float(self._last_run)
        except Exception:
            return True
        return (time.time() - last) >= (24 * 3600)

    def run_if_due(self, system) -> None:
        if not self.is_due():
            return
        try:
            self.run(system)
        except Exception:
            logger.exception("Error ejecutando duelos de fórmula")

    def run(self, system) -> None:
        # Llenar históricos desde last_sensores.json
        rellenados = self._data_bridge.cargar_y_llenar(system)
        if rellenados > 0:
            logger.info(f"FormulaDuelEngine: {rellenados} parámetros cargados desde SensorDataBridge")
        
        if not self.dry_run:
            self._auditar_cambios(system)
        resultados = []
        params = list(FORMULA_HIERARCHY.keys())
        processed = 0
        for parametro in params:
            if processed >= self.max_parametros_por_run:
                break
            res = self._duelo_parametro(system, parametro)
            if res:
                resultados.append(res)
                processed += 1
        self._results_path.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
        self._last_run = str(time.time())
        self._save_state()

    def _auditar_cambios(self, system) -> None:
        ahora = time.time()
        for parametro in self._change_tracker.listar_parametros():
            ultimo = self._change_tracker.ultimo_cambio(parametro)
            if not ultimo:
                continue
            ts = ultimo.get("ts")
            if not ts or (ahora - ts) < (self.audit_days * 86400):
                continue
            anterior = ultimo.get("formula_anterior")
            nueva = ultimo.get("formula_nueva")
            if not anterior or not nueva:
                continue
            # Auditar: si la nueva no supera a la anterior, revertir
            jerarquia = FORMULA_HIERARCHY.get(parametro, {})
            f_anterior = next((f for f in jerarquia.values() if f.nombre_tecnico == anterior), None)
            f_nueva = next((f for f in jerarquia.values() if f.nombre_tecnico == nueva), None)
            cand_nueva = None
            if not f_nueva:
                cand_nueva = self._candidate_registry.resolver(nueva)
            if not f_anterior or (not f_nueva and not cand_nueva):
                continue
            datos = self._build_samples(system, f_anterior.requisitos_datos)
            if not datos:
                continue
            score_prev = self._evaluar_formula(f_anterior, datos, system)
            if f_nueva:
                score_new = self._evaluar_formula(f_nueva, datos, system)
            else:
                score_new = self._evaluar_candidata(cand_nueva, datos, system)
            if not score_prev or not score_new:
                continue
            if score_new.score < score_prev.score:
                self._override_manager.set_default(parametro, f_anterior.nombre_tecnico)
                self._change_tracker.registrar_auditoria(parametro, "revertido_por_auditoria")
                self._change_tracker.marcar_estabilizado(parametro, True)
            else:
                self._change_tracker.registrar_auditoria(parametro, "validado_en_auditoria")
                self._change_tracker.marcar_estabilizado(parametro, True)

    def _duelo_parametro(self, system, parametro: str) -> Optional[Dict[str, Any]]:
        jerarquia = FORMULA_HIERARCHY.get(parametro, {})
        if len(jerarquia) < 2:
            return None
        # Ordenar por nivel (alto a bajo)
        niveles = sorted(jerarquia.keys(), key=lambda n: n.value, reverse=True)
        formula_actual = jerarquia[niveles[0]]
        formula_alt = jerarquia[niveles[1]]

        # Construir dataset (solo si histórico limpio)
        datos = self._build_samples(system, formula_actual.requisitos_datos)
        if not datos:
            return None

        score_actual = self._evaluar_formula(formula_actual, datos, system)
        score_alt = self._evaluar_formula(formula_alt, datos, system)
        if not score_actual or not score_alt:
            return None

        ganador = formula_alt if score_alt.score > score_actual.score else formula_actual
        if ganador == formula_alt:
            if not self._validar_multiround(formula_actual, formula_alt, datos, system):
                logger.warning(
                    "⚠️ Duelo multiround no confirmado para %s. Manteniendo fórmula actual.",
                    parametro,
                )
                ganador = formula_actual
        perdedor = formula_alt if ganador == formula_actual else formula_actual
        mejor_score = score_alt if ganador == formula_alt else score_actual

        candidatas = self._candidate_registry.listar_por_parametro(parametro)
        candidatas += self._candidatas_de_ojeador(parametro, formula_actual.requisitos_datos)
        mejor_candidata = None
        mejor_candidata_score = None
        for cand in candidatas:
            score_cand = self._evaluar_candidata(cand, datos, system)
            if not score_cand:
                continue
            if not mejor_candidata_score or score_cand.score > mejor_candidata_score.score:
                mejor_candidata_score = score_cand
                mejor_candidata = cand

        if mejor_candidata_score and mejor_candidata_score.score > mejor_score.score:
            ganador = mejor_candidata
            mejor_score = mejor_candidata_score

        # Selector de escenario
        escenarios = None
        if isinstance(ganador, Fórmula) and isinstance(perdedor, Fórmula):
            escenarios = self._escenarios_por_temperatura(system, formula_actual, formula_alt, datos)
        if not self.dry_run:
            if ganador == formula_actual:
                self._reset_pendiente(parametro)
                self._change_tracker.marcar_estabilizado(parametro, True)
            else:
                ganador_id = ganador.nombre_tecnico if isinstance(ganador, Fórmula) else ganador.get("id")
                delta = abs(mejor_score.score - score_actual.score)
                aprobado = self._registrar_pendiente(parametro, ganador_id, mejor_score, delta, escenarios)
                if aprobado:
                    if escenarios:
                        self._override_manager.set_scenarios(parametro, escenarios)
                    else:
                        if isinstance(ganador, Fórmula):
                            self._override_manager.set_default(parametro, ganador.nombre_tecnico)
                        else:
                            self._override_manager.set_default(parametro, ganador.get("id"))

                    if isinstance(ganador, Fórmula):
                        nombre_ganador = ganador.nombre_tecnico
                        motivo = f"Duelo multi-etapa: {ganador.nombre_legible} supera a {formula_actual.nombre_legible}"
                    else:
                        nombre_ganador = ganador.get("id")
                        motivo = f"Duelo multi-etapa: candidata externa {nombre_ganador} supera a {formula_actual.nombre_legible}"
                        self._candidate_registry.agregar(ganador)
                    self._change_tracker.registrar_cambio(parametro, formula_actual.nombre_tecnico, nombre_ganador, motivo)

        resultado_duelo = {
            "parametro": parametro,
            "ganador": ganador.nombre_tecnico if isinstance(ganador, Fórmula) else ganador.get("id"),
            "perdedor": perdedor.nombre_tecnico,
            "score_actual": score_actual.score,
            "score_alt": score_alt.score,
            "escenarios": escenarios,
            "dry_run": self.dry_run,
        }
        
        # ✅ GUARDAR RESULTADO PARA AUDITORÍA (CRÍTICO PARA APRENDIZAJE)
        self._guardar_resultado_duelo(parametro, resultado_duelo, datos)
        
        return resultado_duelo

    def _validar_multiround(self, formula_actual: Fórmula, formula_alt: Fórmula,
                             datos: List[Dict[str, float]], system) -> bool:
        """Valida ganador en múltiples rondas con subconjuntos de datos."""
        if self.validation_rounds < 2:
            return True
        if len(datos) < (self.validation_round_min_samples * self.validation_rounds):
            logger.warning(
                "⚠️ Duelo multiround: datos insuficientes (%s) para %s rondas",
                len(datos),
                self.validation_rounds,
            )
            return False

        rondas = self._split_samples(datos, self.validation_rounds)
        wins_alt = 0
        for chunk in rondas:
            score_a = self._evaluar_formula(formula_actual, chunk, system)
            score_b = self._evaluar_formula(formula_alt, chunk, system)
            if not score_a or not score_b:
                continue
            if score_b.score > score_a.score:
                wins_alt += 1

        return wins_alt >= self.validation_round_min_wins

    @staticmethod
    def _split_samples(datos: List[Dict[str, float]], rounds: int) -> List[List[Dict[str, float]]]:
        if rounds <= 1:
            return [datos]
        size = max(1, len(datos) // rounds)
        chunks = [datos[i * size:(i + 1) * size] for i in range(rounds - 1)]
        chunks.append(datos[(rounds - 1) * size:])
        return [c for c in chunks if c]

    def _guardar_resultado_duelo(self, parametro: str, resultado: Dict[str, Any], datos: List[Dict]):
        """✅ Guarda el resultado del duelo en histórico para auditoría."""
        if not RECORDERS_AVAILABLE:
            return
        
        try:
            recorders = get_recorders()
            ts_ahora = time.time()
            
            # Datos de entrada promedio para context
            datos_entrada = {}
            if datos and len(datos) > 0:
                for req in ["temperatura", "humedad", "presion", "viento"]:
                    valores = [d.get(req) for d in datos if d.get(req) is not None]
                    if valores:
                        datos_entrada[req] = statistics.mean(valores)
            
            # ✅ CORRECCIÓN: Determinar quién es ganador basado en scores
            score_actual = resultado.get("score_actual", 0)
            score_alt = resultado.get("score_alt", 0)
            ganador_es_alt = score_alt > score_actual
            
            # resultado_a SIEMPRE es el ganador, resultado_b SIEMPRE es el perdedor
            resultado_ganador = score_alt if ganador_es_alt else score_actual
            resultado_perdedor = score_actual if ganador_es_alt else score_alt
            
            recorders["duelos"].guardar_duelo(
                timestamp=ts_ahora,
                parametro=parametro,
                formula_a={"nombre_tecnico": resultado["ganador"], "nivel": "ELITE"},
                formula_b={"nombre_tecnico": resultado["perdedor"], "nivel": "STANDARD"},
                resultado_a=resultado_ganador,  # ✅ Score del ganador (mayor)
                resultado_b=resultado_perdedor,  # ✅ Score del perdedor (menor)
                datos_entrada=datos_entrada,
                ganador=resultado["ganador"],
                diferencia=abs(resultado_ganador - resultado_perdedor),
                razon_victoria=f"Score: {resultado_ganador:.4f} > {resultado_perdedor:.4f}"
            )
        except Exception as e:
            logger.debug(f"Error guardando resultado de duelo: {e}")

    def _evaluar_formula(self, formula: Fórmula, datos: List[Dict[str, float]], system) -> Optional[DuelScore]:
        """
        Evalúa una fórmula CON OPTIMIZACIONES SIMULADAS:
        1. Calcula outputs brutos
        2. Diagnostica problemas
        3. Aplica mejoras simuladas (EWMA, clip, norm)
        4. Calcula score sobre versión mejorada
        
        Las mejoras NO modifican la fórmula original, solo se usan para duelo.
        """
        func = self._resolver_funcion(formula)
        if not func:
            return None

        outputs = []
        validos = 0
        in_range = 0
        for sample in datos:
            try:
                args = [sample.get(req) for req in formula.requisitos_datos]
                if any(v is None for v in args):
                    continue
                res = self._call_func(func, args)
                if isinstance(res, dict) and "valor" in res:
                    res = res["valor"]
                if res is None or (isinstance(res, float) and (math.isnan(res) or math.isinf(res))):
                    continue
                val = float(res)
                outputs.append(val)
                validos += 1
                if self._en_rango(formula, val):
                    in_range += 1
            except Exception:
                continue

        if not outputs:
            logger.debug(f"Fórmula {formula.nombre_tecnico}: Sin outputs válidos")
            return None

        # Juez termodinámico (no restrictivo): advertir y penalizar score
        penalty = 1.0
        try:
            salida_key = self._judge.clasificar_salida(formula.nombre_tecnico)
            if salida_key:
                juez = self._judge.check_limits({salida_key: statistics.mean(outputs)})
                if not juez.ok:
                    for v in juez.violations:
                        logger.warning("⚠️ Juez termodinámico: %s", v)
                    penalty = self._judge.penalty_factor(juez.violations)
        except Exception:
            penalty = 1.0

        # ✅ APLICAR MEJORAS SIMULADAS (reversible, solo para duelo)
        outputs_mejorados, mejoras, mejora_pct = self._optimizer.aplicar_mejora_simulada(
            outputs, 
            formula.nombre_tecnico
        )
        
        if mejoras:
            logger.debug(f"  ✅ {len(mejoras)} mejoras aplicadas a {formula.nombre_tecnico} (+{mejora_pct:.1f}%)")
        
        # Recalcular métricas sobre versión mejorada
        robustez = validos / max(1, len(datos))
        
        # Contar valores en rango usando versión mejorada
        in_range_mejorado = sum(1 for v in outputs_mejorados if self._en_rango(formula, v))
        precision = in_range_mejorado / max(1, len(outputs_mejorados))
        
        estabilidad = self._score_estabilidad(outputs_mejorados)  # Sobre versión mejorada
        eficiencia = min(1.0, max(0.0, formula.velocidad / 10.0))
        
        # Score ponderado con validaciones
        # IMPORTANTE: Multiplicar por robustez para penalizar fórmulas con muchos errores
        score = (
            self.peso_precision * precision
            + self.peso_estabilidad * estabilidad
            + self.peso_eficiencia * eficiencia
        ) * robustez * penalty
        
        logger.debug(
            f"Fórmula {formula.nombre_tecnico}: "
            f"score={score:.4f}, precision={precision:.4f}, estab={estabilidad:.4f}, "
            f"robust={robustez:.4f}, efic={eficiencia:.4f}, validos={validos}/{len(datos)}"
        )
        
        return DuelScore(score, estabilidad, precision, robustez, eficiencia, validos, len(datos))

    def _evaluar_candidata(self, cand: Dict[str, Any], datos: List[Dict[str, float]], system) -> Optional[DuelScore]:
        if not cand:
            return None
        fn = self._candidate_registry.obtener_funcion(cand)
        if not fn:
            return None
        requisitos = self._candidate_registry.obtener_inputs(cand)
        if not requisitos:
            return None

        outputs = []
        validos = 0
        in_range = 0
        rango = cand.get("rango_validez")
        for sample in datos:
            try:
                args = [sample.get(req) for req in requisitos]
                if any(v is None for v in args):
                    continue
                res = self._call_func(fn, args)
                if isinstance(res, dict) and "valor" in res:
                    res = res["valor"]
                if res is None or (isinstance(res, float) and (math.isnan(res) or math.isinf(res))):
                    continue
                val = float(res)
                outputs.append(val)
                validos += 1
                if self._en_rango_simple(rango, val):
                    in_range += 1
            except Exception:
                continue

        if not outputs:
            logger.debug(f"Candidata {cand.get('id', '?')}: Sin outputs válidos")
            return None

        # Calcular métricas con mayor precisión
        robustez = validos / max(1, len(datos))
        precision = in_range / max(1, validos)
        estabilidad = self._score_estabilidad(outputs)
        velocidad = cand.get("velocidad", 5)
        eficiencia = min(1.0, max(0.0, float(velocidad) / 10.0))
        score = (
            self.peso_precision * precision
            + self.peso_estabilidad * estabilidad
            + self.peso_eficiencia * eficiencia
        ) * robustez
        
        logger.debug(
            f"Candidata {cand.get('id', '?')}: "
            f"score={score:.4f}, precision={precision:.4f}, estab={estabilidad:.4f}, "
            f"robust={robustez:.4f}, efic={eficiencia:.4f}, validos={validos}/{len(datos)}"
        )
        
        return DuelScore(score, estabilidad, precision, robustez, eficiencia, validos, len(datos))

    def _candidatas_de_ojeador(self, parametro: str, inputs_default: List[str]) -> List[Dict[str, Any]]:
        try:
            base_dir = Path(__file__).resolve().parents[2]
            path = base_dir / "data" / "vanguard_alerts.json"
            if not path.exists():
                return []
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                return []
        except Exception:
            return []

        candidatos: List[Dict[str, Any]] = []
        for item in raw:
            if item.get("categoria") != parametro:
                continue
            modulo = item.get("modulo") or ""
            if "." not in modulo:
                continue
            partes = modulo.split(".")
            if len(partes) < 2:
                continue
            module_path = ".".join(partes[:-1])
            func_name = partes[-1]
            cand_id = f"vanguard::{parametro}::{func_name}"
            candidatos.append({
                "id": cand_id,
                "parametro": parametro,
                "module": module_path,
                "function": func_name,
                "inputs": inputs_default,
                "aliases": [item.get("formula"), item.get("titulo")],
                "velocidad": item.get("velocidad", 5),
                "rango_validez": None,
            })
        return candidatos

    def _resolver_funcion(self, formula: Fórmula):
        try:
            # Caso 1: módulo apunta directamente al módulo (normal)
            module = importlib.import_module(formula.módulo)
            fn = getattr(module, formula.nombre_tecnico, None)
            if callable(fn):
                return fn
        except Exception:
            pass

        # Caso 2: módulo incluye ruta completa con función (module.func)
        try:
            if "." in formula.módulo:
                partes = formula.módulo.rsplit(".", 1)
                if len(partes) == 2:
                    module_name, func_name = partes
                    module = importlib.import_module(module_name)
                    fn = getattr(module, func_name, None)
                    if callable(fn):
                        return fn
        except Exception:
            return None
        return None

    def _call_func(self, func, args):
        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            has_varargs = any(p.kind == p.VAR_POSITIONAL for p in params)
            if has_varargs:
                return func(*args)

            total_params = len(params)
            if len(args) < total_params:
                padded = list(args) + [None] * (total_params - len(args))
                return func(*padded)
            return func(*args[:total_params])
        except Exception:
            return func(*args)

    def _build_samples(self, system, requisitos: List[str]) -> List[Dict[str, float]]:
        from core.bus.parametros_canonicos import (
            normalizar_lista_parametros_entrada,
            obtener_valor_parametro_entrada,
        )

        requisitos = normalizar_lista_parametros_entrada(requisitos)
        if not self._historico_limpio(system, requisitos):
            return []
        muestras = []
        hist = getattr(system, "historial_sensores", {}) or {}
        hist = {k: v for k, v in (hist or {}).items()}
        # construir series por requisito
        series = {}
        max_len = 0
        missing_reqs = []
        for req in requisitos:
            datos = obtener_valor_parametro_entrada(hist, req, default=[]) or []
            valores = [v for _, v in datos if v is not None]
            if not valores:
                actual = obtener_valor_parametro_entrada(getattr(system, "sensores", {}) or {}, req)
                if actual is not None:
                    valores = [float(actual)]
            if not valores:
                missing_reqs.append(req)
                continue
            series[req] = valores[-self.sample_size:]
            max_len = max(max_len, len(series[req]))
        if not series:
            if missing_reqs:
                logger.warning(
                    "⚠️ DuelEngine: sin datos para requisitos %s",
                    sorted(set(missing_reqs)),
                )
            return []

        total = min(self.sample_size, max_len)
        for i in range(total):
            fila = {}
            for req, valores in series.items():
                idx = min(i, len(valores) - 1)
                fila[req] = valores[idx]
            muestras.append(self._inyectar_ruido(system, fila))
        if len(muestras) < self.min_clean_samples:
            logger.warning(
                "⚠️ DuelEngine: muestras insuficientes (%s < %s) para %s",
                len(muestras),
                self.min_clean_samples,
                requisitos,
            )
            return []
        return muestras

    def _historico_limpio(self, system, requisitos: List[str]) -> bool:
        from core.bus.parametros_canonicos import obtener_valor_parametro_entrada

        alertas = getattr(system, "sensores_alertas", {}) or {}
        metadata = getattr(system, "sensores_metadata", {}) or {}
        ahora = time.time()
        for req in requisitos:
            if obtener_valor_parametro_entrada(alertas, req) is not None:
                return False
            meta = obtener_valor_parametro_entrada(metadata, req, default={}) if isinstance(metadata, dict) else {}
            if meta.get("simulado"):
                return False
            ts_sim = meta.get("simulado_timestamp")
            if ts_sim and (ahora - float(ts_sim)) < self.clean_window_seconds:
                return False
        return True

    def _inyectar_ruido(self, system, fila: Dict[str, float]) -> Dict[str, float]:
        # Ruido realista + margen autoconfigurable
        for key, val in list(fila.items()):
            std = self._std_historial(system, key)
            if std is None or std <= 0:
                continue
            margen = self._margen_autoconfig(std, val)
            sigma = std * (1.0 + margen)
            ruido = random_gauss(0.0, sigma)
            fila[key] = val + ruido
        return fila

    def _std_historial(self, system, key: str) -> Optional[float]:
        hist = getattr(system, "historial_sensores", {}).get(key) or []
        valores = [v for _, v in hist if v is not None]
        if len(valores) < 5:
            return None
        try:
            return statistics.pstdev(valores[-50:])
        except Exception:
            return None

    def _margen_autoconfig(self, std: float, valor: float) -> float:
        # margen dinámico según variabilidad relativa
        denom = abs(valor) if valor not in (0, None) else 1.0
        ratio = min(1.0, max(0.0, std / denom))
        margen = self.margin_base + (ratio * 0.2)
        return max(0.05, min(0.5, margen))

    def _score_estabilidad(self, outputs: List[float]) -> float:
        try:
            if len(outputs) < 2:
                return 0.5
            std = statistics.pstdev(outputs)
            mean = statistics.fmean(outputs) if outputs else 0.0
            denom = abs(mean) if mean else 1.0
            norm = std / denom
            return 1.0 / (1.0 + norm)
        except Exception:
            return 0.0

    def _en_rango(self, formula: Fórmula, valor: float) -> bool:
        try:
            min_v, max_v = formula.rango_validez
            return (min_v is None or valor >= min_v) and (max_v is None or valor <= max_v)
        except Exception:
            return True

    @staticmethod
    def _en_rango_simple(rango, valor: float) -> bool:
        if not rango:
            return True
        try:
            min_v, max_v = rango
            return (min_v is None or valor >= min_v) and (max_v is None or valor <= max_v)
        except Exception:
            return True

    def _decidir(self, actual: DuelScore, alt: DuelScore) -> str:
        """
        Decide ganador entre dos fórmulas con criterios múltiples:
        1. Score principal (precisión + estabilidad + eficiencia)
        2. Si scores muy cercanos: usar estabilidad como criterio secundario
        3. Si aún empatado: usar eficiencia
        4. Si totalmente empatado: mantener actual (más seguro)
        """
        
        # Umbral de desempate: diferencia < 1%
        margen_minimo = 0.01
        diff_score = alt.score - actual.score
        
        # CASO 1: Alt tiene score CLARAMENTE superior (>1%)
        if diff_score > margen_minimo:
            logger.debug(f"Duelo: Alt gana por score ({alt.score:.4f} > {actual.score:.4f})")
            return "alt"
        
        # CASO 2: Actual tiene score CLARAMENTE superior (>1%)
        elif diff_score < -margen_minimo:
            logger.debug(f"Duelo: Actual gana por score ({actual.score:.4f} > {alt.score:.4f})")
            return "actual"
        
        # CASO 3: Scores EMPATADOS (<1% de diferencia) - USAR CRITERIOS SECUNDARIOS
        else:
            logger.debug(f"Duelo: Scores empatados ({actual.score:.4f} vs {alt.score:.4f}), evaluando criterios secundarios")
            
            # Criterio secundario 1: Estabilidad (consistencia)
            delta_estab = alt.estabilidad - actual.estabilidad
            if delta_estab > 0.05:  # Diferencia significativa en estabilidad (>5%)
                logger.debug(f"  → Alt gana por estabilidad ({alt.estabilidad:.4f} > {actual.estabilidad:.4f})")
                return "alt"
            elif delta_estab < -0.05:
                logger.debug(f"  → Actual gana por estabilidad ({actual.estabilidad:.4f} > {alt.estabilidad:.4f})")
                return "actual"
            
            # Criterio secundario 2: Precisión (% dentro de rango)
            delta_prec = alt.precision - actual.precision
            if delta_prec > 0.05:  # Diferencia significativa en precisión (>5%)
                logger.debug(f"  → Alt gana por precisión ({alt.precision:.4f} > {actual.precision:.4f})")
                return "alt"
            elif delta_prec < -0.05:
                logger.debug(f"  → Actual gana por precisión ({actual.precision:.4f} > {alt.precision:.4f})")
                return "actual"
            
            # Criterio secundario 3: Eficiencia (velocidad)
            delta_ef = alt.eficiencia - actual.eficiencia
            if delta_ef > 0.05:  # Diferencia significativa en eficiencia (>5%)
                logger.debug(f"  → Alt gana por eficiencia ({alt.eficiencia:.4f} > {actual.eficiencia:.4f})")
                return "alt"
            elif delta_ef < -0.05:
                logger.debug(f"  → Actual gana por eficiencia ({actual.eficiencia:.4f} > {alt.eficiencia:.4f})")
                return "actual"
            
            # CASO 4: TODO empatado - MANTENER ACTUAL (más conservador)
            logger.debug(f"  → TODO empatado - Mantener ACTUAL (criterio de seguridad)")
            return "actual"

    def _escenarios_por_temperatura(
        self,
        system,
        actual: Fórmula,
        alt: Fórmula,
        datos: List[Dict[str, float]]
    ) -> Optional[List[Dict[str, Any]]]:
        if not any("temperatura" in d for d in datos):
            return None
        frio = [d for d in datos if d.get("temperatura") is not None and d.get("temperatura") < 0]
        calor = [d for d in datos if d.get("temperatura") is not None and d.get("temperatura") >= 0]
        if len(frio) < 5 or len(calor) < 5:
            return None
        score_f = self._evaluar_formula(actual, frio, system)
        score_fc = self._evaluar_formula(alt, frio, system)
        score_c = self._evaluar_formula(actual, calor, system)
        score_cc = self._evaluar_formula(alt, calor, system)
        if not all([score_f, score_fc, score_c, score_cc]):
            return None
        ganador_frio = alt if score_fc.score > score_f.score else actual
        ganador_calor = alt if score_cc.score > score_c.score else actual
        if ganador_frio == ganador_calor:
            return None
        return [
            {"temp_min": None, "temp_max": 0, "formula": ganador_frio.nombre_tecnico},
            {"temp_min": 0, "temp_max": None, "formula": ganador_calor.nombre_tecnico},
        ]


def random_gauss(mu: float, sigma: float) -> float:
    # Implementación simple sin dependencia externa
    if sigma <= 0:
        return 0.0
    # Box-Muller
    import random
    u1 = random.random()
    u2 = random.random()
    z0 = math.sqrt(-2.0 * math.log(max(u1, 1e-9))) * math.cos(2 * math.pi * u2)
    return mu + z0 * sigma
