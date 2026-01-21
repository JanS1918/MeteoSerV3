from __future__ import annotations

import json
import math
import os
from typing import Dict, Optional

WEIGHTS_PATH = os.path.join("data", "cetreria_calibracion.json")

DEFAULT_WEIGHTS: dict[str, dict[str, float]] = {
    "viento_cetreria": {
        "viento": 0.40,
        "racha": 0.20,
        "variabilidad": 0.15,
        "turbulencia": 0.15,
        "var_hist": 0.10,
    },
    "visibilidad_terreno": {
        "nub": 0.40,
        "saturacion": 0.20,
        "humedad": 0.15,
        "aerosol": 0.15,
        "lluvia": 0.10,
    },
    "termales_probabilidad": {
        "radiacion": 0.35,
        "var_termica": 0.15,
        "nub": 0.15,
        "viento": 0.10,
        "humedad": 0.10,
        "sequedad": 0.10,
        "tendencia_temp": 0.05,
    },
    "barro_campo": {
        "lluvia_24h": 0.45,
        "lluvia_1h": 0.20,
        "lluvia_rate": 0.10,
        "suelo": 0.10,
        "secado": 0.15,
    },
    "confort_ave": {
        "temp": 0.30,
        "sensacion": 0.25,
        "radiacion": 0.15,
        "viento": 0.10,
        "humedad": 0.10,
        "uv": 0.10,
    },
    "indice_seguridad_vuelo": {
        "viento": 0.40,
        "visibilidad": 0.30,
        "barro": 0.20,
        "termales": 0.10,
    },
    "indice_cetreria": {
        "seguridad": 0.40,
        "viento": 0.30,
        "visibilidad": 0.20,
        "confort": 0.10,
    },
}


def _load_weights() -> dict[str, dict[str, float]]:
    if not os.path.exists(WEIGHTS_PATH):
        return {}
    try:
        with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f) or {}
        weights = {}
        for nombre, info in raw.items():
            if isinstance(info, dict) and "weights" in info:
                weights[nombre] = info.get("weights") or {}
        return weights
    except Exception:
        return {}


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min(value, max_value), min_value)


def _clamp_pct(value: float) -> float:
    return _clamp(value, 0.0, 100.0)


def _dewpoint_c(temp_c: float, rh: float) -> float:
    a, b = 17.27, 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(max(1e-6, rh) / 100.0)
    return (b * alpha) / (a - alpha)


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(v)) for v in weights.values())
    if total <= 0:
        return weights
    return {k: max(0.0, float(v)) / total for k, v in weights.items()}


def _weighted_score(components: dict[str, Optional[float]], weights: dict[str, float], bias: float = 0.0) -> Optional[float]:
    total_w = 0.0
    total = 0.0
    for k, w in weights.items():
        v = components.get(k)
        if v is None:
            continue
        total_w += w
        total += v * w
    if total_w <= 0:
        return None
    score = (total / total_w) + bias
    return _clamp_pct(score * 100.0)


def _get_weights(nombre: str) -> dict[str, float]:
    custom = _load_weights().get(nombre)
    if custom:
        return _normalize_weights(custom)
    return _normalize_weights(DEFAULT_WEIGHTS.get(nombre, {}))


def _get_bias(nombre: str) -> float:
    if not os.path.exists(WEIGHTS_PATH):
        return 0.0
    try:
        with open(WEIGHTS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f) or {}
        info = raw.get(nombre, {}) if isinstance(raw, dict) else {}
        bias = float(info.get("bias", 0.0)) if isinstance(info, dict) else 0.0
        return max(-0.2, min(0.2, bias))
    except Exception:
        return 0.0


def componentes_viento_cetreria(viento_medio: Optional[float], rachas: Optional[float],
                                viento_std: Optional[float] = None) -> dict[str, Optional[float]]:
    if viento_medio is None and rachas is None:
        return {}
    v = viento_medio if viento_medio is not None else rachas
    r = rachas if rachas is not None else v
    if v is None or r is None:
        return {}
    viento_factor = _clamp(1.0 - (v / 30.0))
    racha_factor = _clamp(1.0 - (r / 40.0))
    variabilidad = _clamp(1.0 - (abs(r - v) / 20.0))
    ratio = r / max(v, 1.0)
    turbulencia = _clamp(1.0 - max(0.0, ratio - 1.0) / 1.5)
    var_hist = None
    if viento_std is not None:
        var_hist = _clamp(1.0 - (viento_std / 6.0))
    return {
        "viento": viento_factor,
        "racha": racha_factor,
        "variabilidad": variabilidad,
        "turbulencia": turbulencia,
        "var_hist": var_hist,
    }


def componentes_visibilidad_terreno(temp_c: Optional[float], dew_c: Optional[float], rh: Optional[float],
                                    nubosidad: Optional[float], pm25: Optional[float] = None,
                                    lluvia_rate: Optional[float] = None) -> dict[str, Optional[float]]:
    if temp_c is None or rh is None or nubosidad is None:
        return {}
    dew = dew_c if dew_c is not None else _dewpoint_c(temp_c, rh)
    delta_t = max(temp_c - dew, 0.0)
    sat_factor = _clamp((10.0 - delta_t) / 10.0)
    rh_factor = _clamp(rh / 100.0)
    nub_factor = 1.0 - _clamp(nubosidad / 100.0)
    aerosol_factor = None
    if pm25 is not None:
        aerosol_factor = _clamp(1.0 - (pm25 / 150.0))
    lluvia_factor = None
    if lluvia_rate is not None:
        lluvia_factor = _clamp(1.0 - (lluvia_rate / 2.0))
    return {
        "nub": nub_factor,
        "saturacion": 1.0 - sat_factor,
        "humedad": 1.0 - rh_factor,
        "aerosol": aerosol_factor,
        "lluvia": lluvia_factor,
    }


def componentes_termales_probabilidad(radiacion_real: Optional[float], var_t_5min: Optional[float],
                                      nubosidad: Optional[float], viento_medio: Optional[float],
                                      rh: Optional[float], temp_c: Optional[float] = None,
                                      dew_c: Optional[float] = None,
                                      temp_tendencia_30m: Optional[float] = None) -> dict[str, Optional[float]]:
    if radiacion_real is None or nubosidad is None or viento_medio is None or rh is None:
        return {}
    var_t = var_t_5min if var_t_5min is not None else 0.0
    rad_factor = _clamp(radiacion_real / 800.0)
    var_factor = _clamp(var_t / 0.6)
    nub_factor = 1.0 - _clamp(nubosidad / 100.0)
    viento_factor = _clamp(1.0 - (viento_medio / 20.0))
    hum_factor = _clamp(1.0 - (rh / 100.0))
    sequedad_factor = None
    if temp_c is not None and dew_c is not None:
        delta_t = max(temp_c - dew_c, 0.0)
        sequedad_factor = _clamp(delta_t / 12.0)
    tendencia_factor = None
    if temp_tendencia_30m is not None:
        tendencia_factor = _clamp(temp_tendencia_30m / 2.0)
    return {
        "radiacion": rad_factor,
        "var_termica": var_factor,
        "nub": nub_factor,
        "viento": viento_factor,
        "humedad": hum_factor,
        "sequedad": sequedad_factor,
        "tendencia_temp": tendencia_factor,
    }


def componentes_barro_campo(lluvia_24h: Optional[float], lluvia_1h: Optional[float],
                            viento_medio: Optional[float], temp_c: Optional[float],
                            dew_c: Optional[float], lluvia_rate: Optional[float] = None,
                            humedad_suelo: Optional[float] = None) -> dict[str, Optional[float]]:
    if lluvia_24h is None and lluvia_1h is None and viento_medio is None and humedad_suelo is None:
        return {}
    lluvia_24 = lluvia_24h if lluvia_24h is not None else 0.0
    lluvia_1 = lluvia_1h if lluvia_1h is not None else 0.0
    v = viento_medio if viento_medio is not None else 0.0
    if temp_c is None or dew_c is None:
        secado_factor = _clamp(v / 20.0)
    else:
        secado_factor = _clamp((v / 20.0) + ((temp_c - dew_c) / 10.0))
    lluvia_factor = _clamp(lluvia_24 / 20.0)
    reciente_factor = _clamp(lluvia_1 / 5.0)
    lluvia_rate_factor = _clamp((lluvia_rate or 0.0) / 2.0) if lluvia_rate is not None else None
    suelo_factor = _clamp((humedad_suelo or 0.0) / 100.0) if humedad_suelo is not None else None
    return {
        "lluvia_24h": lluvia_factor,
        "lluvia_1h": reciente_factor,
        "lluvia_rate": lluvia_rate_factor,
        "suelo": suelo_factor,
        "secado": secado_factor,
    }


def componentes_confort_ave(temp_c: Optional[float], sensacion_termica: Optional[float],
                            radiacion_real: Optional[float], viento_medio: Optional[float],
                            rh: Optional[float] = None, uv: Optional[float] = None) -> dict[str, Optional[float]]:
    if temp_c is None and sensacion_termica is None:
        return {}
    t = temp_c if temp_c is not None else sensacion_termica
    s = sensacion_termica if sensacion_termica is not None else t
    v = viento_medio if viento_medio is not None else 0.0
    r = radiacion_real if radiacion_real is not None else 0.0
    temp_factor = _clamp(1.0 - abs(t - 18.0) / 15.0)
    sens_factor = _clamp(1.0 - abs(s - 18.0) / 15.0)
    rad_factor = _clamp(1.0 - (r / 900.0))
    viento_factor = _clamp(1.0 - (v / 25.0))
    hum_factor = None
    if rh is not None:
        hum_factor = _clamp(1.0 - abs(rh - 55.0) / 45.0)
    uv_factor = None
    if uv is not None:
        uv_factor = _clamp(1.0 - (uv / 9.0))
    return {
        "temp": temp_factor,
        "sensacion": sens_factor,
        "radiacion": rad_factor,
        "viento": viento_factor,
        "humedad": hum_factor,
        "uv": uv_factor,
    }


def viento_cetreria(viento_medio: Optional[float], rachas: Optional[float],
                    viento_std: Optional[float] = None) -> Optional[float]:
    componentes = componentes_viento_cetreria(viento_medio, rachas, viento_std=viento_std)
    if not componentes:
        return None
    pesos = _get_weights("viento_cetreria")
    bias = _get_bias("viento_cetreria")
    return _weighted_score(componentes, pesos, bias=bias)


def visibilidad_terreno(temp_c: Optional[float], dew_c: Optional[float], rh: Optional[float],
                        nubosidad: Optional[float], pm25: Optional[float] = None,
                        lluvia_rate: Optional[float] = None) -> Optional[float]:
    componentes = componentes_visibilidad_terreno(temp_c, dew_c, rh, nubosidad, pm25, lluvia_rate)
    if not componentes:
        return None
    pesos = _get_weights("visibilidad_terreno")
    bias = _get_bias("visibilidad_terreno")
    return _weighted_score(componentes, pesos, bias=bias)


def termales_probabilidad(radiacion_real: Optional[float], var_t_5min: Optional[float],
                          nubosidad: Optional[float], viento_medio: Optional[float],
                          rh: Optional[float], temp_c: Optional[float] = None,
                          dew_c: Optional[float] = None,
                          temp_tendencia_30m: Optional[float] = None) -> Optional[float]:
    componentes = componentes_termales_probabilidad(
        radiacion_real, var_t_5min, nubosidad, viento_medio, rh,
        temp_c=temp_c, dew_c=dew_c, temp_tendencia_30m=temp_tendencia_30m
    )
    if not componentes:
        return None
    pesos = _get_weights("termales_probabilidad")
    bias = _get_bias("termales_probabilidad")
    return _weighted_score(componentes, pesos, bias=bias)


def barro_campo(lluvia_24h: Optional[float], lluvia_1h: Optional[float],
                viento_medio: Optional[float], temp_c: Optional[float],
                dew_c: Optional[float], lluvia_rate: Optional[float] = None,
                humedad_suelo: Optional[float] = None) -> Optional[float]:
    componentes = componentes_barro_campo(
        lluvia_24h, lluvia_1h, viento_medio, temp_c, dew_c,
        lluvia_rate=lluvia_rate, humedad_suelo=humedad_suelo
    )
    if not componentes:
        return None
    pesos = _get_weights("barro_campo")
    bias = _get_bias("barro_campo")
    return _weighted_score(componentes, pesos, bias=bias)


def confort_ave(temp_c: Optional[float], sensacion_termica: Optional[float],
                radiacion_real: Optional[float], viento_medio: Optional[float],
                rh: Optional[float] = None, uv: Optional[float] = None) -> Optional[float]:
    componentes = componentes_confort_ave(temp_c, sensacion_termica, radiacion_real, viento_medio, rh, uv)
    if not componentes:
        return None
    pesos = _get_weights("confort_ave")
    bias = _get_bias("confort_ave")
    return _weighted_score(componentes, pesos, bias=bias)


def indice_seguridad_vuelo(viento_cet: Optional[float], visibilidad: Optional[float],
                           barro: Optional[float], termales: Optional[float]) -> Optional[float]:
    if viento_cet is None or visibilidad is None or barro is None or termales is None:
        return None
    componentes = {
        "viento": _clamp(viento_cet / 100.0),
        "visibilidad": _clamp(visibilidad / 100.0),
        "barro": _clamp(1.0 - barro / 100.0),
        "termales": _clamp(termales / 100.0),
    }
    pesos = _get_weights("indice_seguridad_vuelo")
    bias = _get_bias("indice_seguridad_vuelo")
    return _weighted_score(componentes, pesos, bias=bias)


def indice_cetreria_final(indice_seguridad: Optional[float], viento_cet: Optional[float],
                          visibilidad: Optional[float], confort: Optional[float]) -> Optional[float]:
    if indice_seguridad is None or viento_cet is None or visibilidad is None or confort is None:
        return None
    componentes = {
        "seguridad": _clamp(indice_seguridad / 100.0),
        "viento": _clamp(viento_cet / 100.0),
        "visibilidad": _clamp(visibilidad / 100.0),
        "confort": _clamp(confort / 100.0),
    }
    pesos = _get_weights("indice_cetreria")
    bias = _get_bias("indice_cetreria")
    return _weighted_score(componentes, pesos, bias=bias)


def calcular_cetreria(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    viento_med = data.get("viento_medio")
    rachas = data.get("rachas")
    temp_c = data.get("temperatura")
    dew_c = data.get("punto_rocio")
    rh = data.get("humedad")
    nub = data.get("nubosidad_estimada")
    radiacion = data.get("radiacion")
    var_t_5min = data.get("var_t_5min")
    lluvia_24h = data.get("lluvia_24h")
    lluvia_1h = data.get("lluvia_1h")
    sensacion = data.get("sensacion_termica")
    pm25 = data.get("pm25")
    lluvia_rate = data.get("lluvia_rate")
    humedad_suelo = data.get("humedad_suelo")
    temp_tendencia_30m = data.get("temp_tendencia_30m")
    uv = data.get("uv")
    viento_std_30m = data.get("viento_std_30m")

    viento = viento_cetreria(viento_med, rachas, viento_std=viento_std_30m)
    visibilidad = visibilidad_terreno(temp_c, dew_c, rh, nub, pm25=pm25, lluvia_rate=lluvia_rate)
    termales = termales_probabilidad(
        radiacion, var_t_5min, nub, viento_med, rh,
        temp_c=temp_c, dew_c=dew_c, temp_tendencia_30m=temp_tendencia_30m
    )
    barro = barro_campo(
        lluvia_24h, lluvia_1h, viento_med, temp_c, dew_c,
        lluvia_rate=lluvia_rate, humedad_suelo=humedad_suelo
    )
    confort = confort_ave(temp_c, sensacion, radiacion, viento_med, rh=rh, uv=uv)
    seguridad = indice_seguridad_vuelo(viento, visibilidad, barro, termales)
    indice_cetreria = indice_cetreria_final(seguridad, viento, visibilidad, confort)

    return {
        "viento_cetreria": viento,
        "visibilidad_terreno": visibilidad,
        "termales_probabilidad": termales,
        "barro_campo": barro,
        "confort_ave": confort,
        "indice_viento_cetreria": viento,
        "indice_visibilidad_cetreria": visibilidad,
        "indice_termales": termales,
        "indice_seguridad_vuelo": seguridad,
        "indice_cetreria": indice_cetreria,
    }
