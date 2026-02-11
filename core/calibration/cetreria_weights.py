import json
import os
from typing import Dict, List, Tuple

from core.indices.cetreria.cetreria_indices import (
    DEFAULT_WEIGHTS,
    _dewpoint_c,
    componentes_barro_campo,
    componentes_confort_ave,
    componentes_termales_probabilidad,
    componentes_viento_cetreria,
    componentes_visibilidad_terreno,
)

FEEDBACK_PATH = os.path.join("data", "feedback_registros.jsonl")
CALIB_PATH = os.path.join("data", "cetreria_calibracion.json")


def load_feedback(path: str = FEEDBACK_PATH) -> List[dict]:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _get_val(container: dict, key: str):
    val = container.get(key)
    if isinstance(val, dict):
        return val.get("valor")
    return val


def _get_sensor(sensores: dict, keys: List[str]):
    for k in keys:
        if k in sensores:
            return sensores.get(k)
    return None


def _fit_weights(samples: List[Tuple[dict, float]], init_weights: Dict[str, float],
                 lr: float = 0.05, epochs: int = 1500) -> Tuple[Dict[str, float], float, float]:
    if not samples:
        return init_weights, 0.0, 0.0
    keys = list(init_weights.keys())
    w = [init_weights.get(k, 0.0) for k in keys]
    total_w = sum(w)
    if total_w > 0:
        w = [wi / total_w for wi in w]
    b = 0.0
    n = len(samples)
    for _ in range(epochs):
        grad_w = [0.0] * len(w)
        grad_b = 0.0
        for comps, y in samples:
            y_n = y / 100.0
            pred = sum(wi * comps[k] for wi, k in zip(w, keys)) + b
            err = pred - y_n
            for i, k in enumerate(keys):
                grad_w[i] += (2.0 / n) * err * comps[k]
            grad_b += (2.0 / n) * err
        w = [max(0.0, wi - lr * gi) for wi, gi in zip(w, grad_w)]
        total_w = sum(w)
        if total_w > 0:
            w = [wi / total_w for wi in w]
        b = max(-0.2, min(0.2, b - lr * grad_b))
    mae = 0.0
    for comps, y in samples:
        pred = (sum(wi * comps[k] for wi, k in zip(w, keys)) + b) * 100.0
        mae += abs(pred - y)
    mae = mae / len(samples)
    return {k: round(wi, 6) for k, wi in zip(keys, w)}, round(b, 6), round(mae, 3)


def _build_samples(rows: List[dict], nombre: str) -> List[Tuple[dict, float]]:
    samples = []
    for row in rows:
        if row.get("nombre") != nombre:
            continue
        valor_real = row.get("valor_real")
        if valor_real is None:
            continue
        snapshot = row.get("snapshot") or {}
        sensores = snapshot.get("sensores") or {}
        indices = snapshot.get("indices") or {}

        temp = _get_sensor(sensores, ["temperatura"]) 
        rh = _get_sensor(sensores, ["humedad"]) 
        viento = _get_sensor(sensores, ["viento", "wind", "windspeed"])
        rachas = _get_sensor(sensores, ["rachas", "racha", "viento_racha", "wind_gust", "gust"])
        rad = _get_sensor(sensores, ["radiacion", "solarradiation"])
        lluvia_1h = _get_sensor(sensores, ["lluvia_1h", "rain_1h", "lluvia_h"])
        lluvia_24h = _get_sensor(sensores, ["lluvia_24h", "rain_24h", "lluvia_dia"])
        lluvia_rate = _get_sensor(sensores, ["lluvia_rate", "rain_rate", "rainrate"])
        pm25 = _get_sensor(sensores, ["pm25", "pm2_5", "pm2.5", "pm_25"])
        hum_suelo = _get_sensor(sensores, ["humedad_suelo", "soil_moisture", "soil", "wh51"])
        uv = _get_sensor(sensores, ["uv", "uv_index", "indice_uv"])
        sensacion = _get_val(indices, "sensacion_termica")
        nub = _get_val(indices, "nubosidad_estimada")
        viento_std = _get_val(indices, "variabilidad_viento_30m")

        try:
            temp = float(temp) if temp is not None else None
            rh = float(rh) if rh is not None else None
            viento = float(viento) if viento is not None else None
            rachas = float(rachas) if rachas is not None else None
            rad = float(rad) if rad is not None else None
            lluvia_1h = float(lluvia_1h) if lluvia_1h is not None else None
            lluvia_24h = float(lluvia_24h) if lluvia_24h is not None else None
            lluvia_rate = float(lluvia_rate) if lluvia_rate is not None else None
            pm25 = float(pm25) if pm25 is not None else None
            hum_suelo = float(hum_suelo) if hum_suelo is not None else None
            uv = float(uv) if uv is not None else None
            sensacion = float(sensacion) if sensacion is not None else None
            nub = float(nub) if nub is not None else None
            viento_std = float(viento_std) if viento_std is not None else None
        except Exception:
            continue

        dew = None
        if temp is not None and rh is not None:
            try:
                dew = _dewpoint_c(temp, rh)
            except Exception:
                dew = None

        if nombre == "viento_cetreria":
            comps = componentes_viento_cetreria(viento, rachas, viento_std=viento_std)
        elif nombre == "visibilidad_terreno":
            comps = componentes_visibilidad_terreno(temp, dew, rh, nub, pm25=pm25, lluvia_rate=lluvia_rate)
        elif nombre == "termales_probabilidad":
            comps = componentes_termales_probabilidad(rad, None, nub, viento, rh, temp_c=temp, dew_c=dew)
        elif nombre == "barro_campo":
            comps = componentes_barro_campo(lluvia_24h, lluvia_1h, viento, temp, dew, lluvia_rate=lluvia_rate, humedad_suelo=hum_suelo)
        elif nombre == "confort_ave":
            comps = componentes_confort_ave(temp, sensacion, rad, viento, rh=rh, uv=uv)
        else:
            continue

        if not comps:
            continue
        if any(v is None for v in comps.values()):
            continue
        samples.append((comps, float(valor_real)))
    return samples


def build_cetreria_weights(rows: List[dict] | None = None, min_samples: int = 8,
                           only: str | None = None, lr: float = 0.05,
                           epochs: int = 1500) -> Dict[str, dict]:
    rows = rows if rows is not None else load_feedback()
    if not rows:
        return {}
    targets = [
        "viento_cetreria",
        "visibilidad_terreno",
        "termales_probabilidad",
        "barro_campo",
        "confort_ave",
    ]
    resultados: Dict[str, dict] = {}
    for nombre in targets:
        if only and nombre != only:
            continue
        samples = _build_samples(rows, nombre)
        if len(samples) < min_samples:
            continue
        init = DEFAULT_WEIGHTS.get(nombre, {})
        weights, bias, mae = _fit_weights(samples, init, lr=lr, epochs=epochs)
        resultados[nombre] = {
            "weights": weights,
            "bias": bias,
            "muestras": len(samples),
            "mae": mae,
            "version": 2,
        }
    return resultados


def save_cetreria_weights(resultados: Dict[str, dict], path: str = CALIB_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
