from __future__ import annotations

import math
from typing import Dict, Optional


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min(value, max_value), min_value)


def _clamp_pct(value: float) -> float:
    return _clamp(value, 0.0, 100.0)


def _dewpoint_c(temp_c: float, rh: float) -> float:
    a, b = 17.27, 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + math.log(max(1e-6, rh) / 100.0)
    return (b * alpha) / (a - alpha)


def viento_cetreria(viento_medio: Optional[float], rachas: Optional[float]) -> Optional[float]:
    if viento_medio is None and rachas is None:
        return None
    v = viento_medio if viento_medio is not None else rachas
    r = rachas if rachas is not None else v
    if v is None or r is None:
        return None
    score = 100.0 * (
        0.6 * _clamp(1.0 - (v / 30.0)) +
        0.3 * _clamp(1.0 - (r / 40.0)) +
        0.1 * _clamp(1.0 - (abs(r - v) / 20.0))
    )
    return _clamp_pct(score)


def visibilidad_terreno(temp_c: Optional[float], dew_c: Optional[float], rh: Optional[float],
                        nubosidad: Optional[float]) -> Optional[float]:
    if temp_c is None or rh is None or nubosidad is None:
        return None
    dew = dew_c if dew_c is not None else _dewpoint_c(temp_c, rh)
    delta_t = max(temp_c - dew, 0.0)
    sat_factor = _clamp((10.0 - delta_t) / 10.0)
    rh_factor = _clamp(rh / 100.0)
    nub_factor = 1.0 - _clamp(nubosidad / 100.0)
    score = 100.0 * (
        0.5 * nub_factor +
        0.3 * (1.0 - sat_factor) +
        0.2 * (1.0 - rh_factor)
    )
    return _clamp_pct(score)


def termales_probabilidad(radiacion_real: Optional[float], var_t_5min: Optional[float],
                          nubosidad: Optional[float], viento_medio: Optional[float],
                          rh: Optional[float]) -> Optional[float]:
    if radiacion_real is None or nubosidad is None or viento_medio is None or rh is None:
        return None
    var_t = var_t_5min if var_t_5min is not None else 0.0
    rad_factor = _clamp(radiacion_real / 800.0)
    var_factor = _clamp(var_t / 0.6)
    nub_factor = 1.0 - _clamp(nubosidad / 100.0)
    viento_factor = _clamp(1.0 - (viento_medio / 20.0))
    hum_factor = _clamp(1.0 - (rh / 100.0))
    score = 100.0 * (
        0.4 * rad_factor +
        0.2 * var_factor +
        0.2 * nub_factor +
        0.1 * viento_factor +
        0.1 * hum_factor
    )
    return _clamp_pct(score)


def barro_campo(lluvia_24h: Optional[float], lluvia_1h: Optional[float],
                viento_medio: Optional[float], temp_c: Optional[float],
                dew_c: Optional[float]) -> Optional[float]:
    if lluvia_24h is None and lluvia_1h is None and viento_medio is None:
        return None
    lluvia_24 = lluvia_24h if lluvia_24h is not None else 0.0
    lluvia_1 = lluvia_1h if lluvia_1h is not None else 0.0
    v = viento_medio if viento_medio is not None else 0.0
    if temp_c is None or dew_c is None:
        secado_factor = _clamp(v / 20.0)
    else:
        secado_factor = _clamp((v / 20.0) + ((temp_c - dew_c) / 10.0))
    lluvia_factor = _clamp(lluvia_24 / 20.0)
    reciente_factor = _clamp(lluvia_1 / 5.0)
    score = 100.0 * (
        0.6 * lluvia_factor +
        0.3 * reciente_factor -
        0.3 * secado_factor
    )
    return _clamp_pct(score)


def confort_ave(temp_c: Optional[float], sensacion_termica: Optional[float],
                radiacion_real: Optional[float], viento_medio: Optional[float]) -> Optional[float]:
    if temp_c is None and sensacion_termica is None:
        return None
    t = temp_c if temp_c is not None else sensacion_termica
    s = sensacion_termica if sensacion_termica is not None else t
    v = viento_medio if viento_medio is not None else 0.0
    r = radiacion_real if radiacion_real is not None else 0.0
    temp_factor = _clamp(1.0 - abs(t - 18.0) / 15.0)
    sens_factor = _clamp(1.0 - abs(s - 18.0) / 15.0)
    rad_factor = _clamp(1.0 - (r / 900.0))
    viento_factor = _clamp(1.0 - (v / 25.0))
    score = 100.0 * (
        0.4 * temp_factor +
        0.3 * sens_factor +
        0.2 * rad_factor +
        0.1 * viento_factor
    )
    return _clamp_pct(score)


def indice_seguridad_vuelo(viento_cet: Optional[float], visibilidad: Optional[float],
                           barro: Optional[float], termales: Optional[float]) -> Optional[float]:
    if viento_cet is None or visibilidad is None or barro is None or termales is None:
        return None
    score = 100.0 * (
        0.4 * (viento_cet / 100.0) +
        0.3 * (visibilidad / 100.0) +
        0.2 * (1.0 - barro / 100.0) +
        0.1 * (termales / 100.0)
    )
    return _clamp_pct(score)


def indice_cetreria_final(indice_seguridad: Optional[float], viento_cet: Optional[float],
                          visibilidad: Optional[float], confort: Optional[float]) -> Optional[float]:
    if indice_seguridad is None or viento_cet is None or visibilidad is None or confort is None:
        return None
    score = 100.0 * (
        0.4 * (indice_seguridad / 100.0) +
        0.3 * (viento_cet / 100.0) +
        0.2 * (visibilidad / 100.0) +
        0.1 * (confort / 100.0)
    )
    return _clamp_pct(score)


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

    viento = viento_cetreria(viento_med, rachas)
    visibilidad = visibilidad_terreno(temp_c, dew_c, rh, nub)
    termales = termales_probabilidad(radiacion, var_t_5min, nub, viento_med, rh)
    barro = barro_campo(lluvia_24h, lluvia_1h, viento_med, temp_c, dew_c)
    confort = confort_ave(temp_c, sensacion, radiacion, viento_med)
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
