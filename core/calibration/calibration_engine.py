import json
import os
from typing import Dict, Iterable, Tuple

FEEDBACK_PATH = os.path.join("data", "feedback_registros.jsonl")
FACTORS_PATH = os.path.join("data", "calibration_factors.json")


def _load_feedback() -> list[dict]:
    if not os.path.exists(FEEDBACK_PATH):
        return []
    rows = []
    with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _extract_pairs(rows: Iterable[dict], nombre: str) -> list[Tuple[float, float]]:
    pairs = []
    for row in rows:
        if row.get("nombre") != nombre:
            continue
        valor = row.get("valor")
        real = row.get("valor_real")
        try:
            if valor is None or real is None:
                continue
            x = float(valor)
            y = float(real)
            pairs.append((x, y))
        except Exception:
            continue
    return pairs


def _linear_fit(pairs: list[Tuple[float, float]]) -> Tuple[float, float]:
    if not pairs:
        return 1.0, 0.0
    n = len(pairs)
    sx = sum(x for x, _ in pairs)
    sy = sum(y for _, y in pairs)
    sxx = sum(x * x for x, _ in pairs)
    sxy = sum(x * y for x, y in pairs)
    denom = n * sxx - sx * sx
    if denom == 0:
        return 1.0, 0.0
    a = (n * sxy - sx * sy) / denom
    b = (sy - a * sx) / n
    return a, b


def _mae(pairs: list[Tuple[float, float]]) -> float:
    if not pairs:
        return 0.0
    return sum(abs(x - y) for x, y in pairs) / len(pairs)


def build_calibration_factors(min_muestras: int = 5) -> Dict[str, Dict[str, float]]:
    rows = _load_feedback()
    nombres = sorted({row.get("nombre") for row in rows if row.get("nombre")})
    factors: Dict[str, Dict[str, float]] = {}
    for nombre in nombres:
        pairs = _extract_pairs(rows, nombre)
        if len(pairs) < min_muestras:
            continue
        a, b = _linear_fit(pairs)
        mae = _mae(pairs)
        factors[nombre] = {
            "a": round(a, 6),
            "b": round(b, 6),
            "muestras": len(pairs),
            "mae": round(mae, 3),
        }
    return factors


def save_factors(factors: Dict[str, Dict[str, float]]) -> None:
    os.makedirs("data", exist_ok=True)
    with open(FACTORS_PATH, "w", encoding="utf-8") as f:
        json.dump(factors, f, ensure_ascii=False, indent=2)


def load_factors() -> Dict[str, Dict[str, float]]:
    if not os.path.exists(FACTORS_PATH):
        return {}
    try:
        with open(FACTORS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def apply_calibration_value(valor: float, factor: Dict[str, float]) -> float:
    a = float(factor.get("a", 1.0))
    b = float(factor.get("b", 0.0))
    return a * valor + b


def apply_calibration(
    payload: Dict[str, dict], factors: Dict[str, Dict[str, float]]
) -> Dict[str, dict]:
    for nombre, info in payload.items():
        if nombre not in factors:
            continue
        if not isinstance(info, dict):
            continue
        if "valor" not in info or info.get("valor") is None:
            continue
        try:
            v = float(info.get("valor"))
        except Exception:
            continue
        ajustado = apply_calibration_value(v, factors[nombre])
        info["valor"] = round(ajustado, 2)
        info["calibrado"] = True
        info["calibracion"] = {
            "a": factors[nombre].get("a"),
            "b": factors[nombre].get("b"),
            "muestras": factors[nombre].get("muestras"),
            "mae": factors[nombre].get("mae"),
        }
    return payload
