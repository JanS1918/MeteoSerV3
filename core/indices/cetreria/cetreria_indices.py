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
    """Punto de rocío WEXLER NIST 2026 (Motor: Diamond_Refined_v1)
    Unificado con núcleo principal para coherencia total."""
    from core.indices.environmental_indices import _dew_point
    return _dew_point(temp_c, rh)


# ============================================================================
# FUNCIONES ROBUSTAS CONTRA None (NO COLAPSAN SIN SENSORES)
# ============================================================================

def viento_cetreria_robusto(
    viento_medio: Optional[float],
    rachas: Optional[float],
    historico_fallback: float = 12.5
) -> float:
    """
    Índice de viento para cetrería (0-100).
    
    Robusto: Si ambos sensores faltan, usa promedio histórico de Argentona.
    Nunca retorna None.
    
    Variables:
      - viento_medio: velocidad media (m/s o km/h)
      - rachas: velocidad máxima rachas (m/s o km/h)
      - historico_fallback: valor por defecto si ambos None (default Argentona: 12.5 km/h)
    
    Retorna: 0-100 (100 = condiciones ideales para cetrería)
    """
    # Fallback: si ambos None, usar histórico
    if viento_medio is None and rachas is None:
        v = historico_fallback
        r = historico_fallback
    else:
        v = viento_medio if viento_medio is not None else rachas
        r = rachas if rachas is not None else viento_medio
    
    if v is None:
        v = historico_fallback
    if r is None:
        r = historico_fallback
    
    # Fórmula: penalizar vientos muy altos (>30 km/h medio, >40 rachas)
    score = 100.0 * (
        0.6 * _clamp(1.0 - (v / 30.0)) +
        0.3 * _clamp(1.0 - (r / 40.0)) +
        0.1 * _clamp(1.0 - (abs(r - v) / 20.0))
    )
    return _clamp_pct(score)


def visibilidad_terreno_robusto(
    temp_c: Optional[float],
    dew_c: Optional[float],
    rh: Optional[float],
    nubosidad: Optional[float],
    historico_visibility: float = 75.0
) -> float:
    """
    Índice de visibilidad para cetrería (0-100).
    Robusto contra sensores faltantes.
    
    Nunca retorna None.
    """
    # Si faltan todos los sensores, usar fallback histórico
    if all(v is None for v in [temp_c, rh, nubosidad]):
        return _clamp_pct(historico_visibility)
    
    # Usar valores o aprox
    t = temp_c if temp_c is not None else 15.0
    h = rh if rh is not None else 70.0
    n = nubosidad if nubosidad is not None else 50.0
    
    # Calcular dew si falta
    if dew_c is None and temp_c is not None and rh is not None:
        try:
            dew_c = _dewpoint_c(temp_c, rh)
        except:
            dew_c = t - ((100.0 - h) / 5.0)  # Aproximación burda
    elif dew_c is None:
        dew_c = t - 10.0
    
    delta_t = max(t - dew_c, 0.0)
    sat_factor = _clamp((10.0 - delta_t) / 10.0)
    rh_factor = _clamp(h / 100.0)
    nub_factor = 1.0 - _clamp(n / 100.0)
    
    score = 100.0 * (
        0.5 * nub_factor +
        0.3 * (1.0 - sat_factor) +
        0.2 * (1.0 - rh_factor)
    )
    return _clamp_pct(score)


def termales_probabilidad_robusto(
    radiacion_real: Optional[float],
    var_t_5min: Optional[float],
    nubosidad: Optional[float],
    viento_medio: Optional[float],
    rh: Optional[float],
    historico_termales: float = 45.0
) -> float:
    """
    Probabilidad de térmicas para cetrería (0-100).
    Robusto contra sensores faltantes.
    """
    # Si faltan más de 3 sensores, fallback
    sensores_validos = sum([
        radiacion_real is not None,
        nubosidad is not None,
        viento_medio is not None,
        rh is not None
    ])
    
    if sensores_validos < 2:
        return _clamp_pct(historico_termales)
    
    rad = radiacion_real if radiacion_real is not None else 600.0
    var_t = var_t_5min if var_t_5min is not None else 0.0
    nub = nubosidad if nubosidad is not None else 50.0
    v = viento_medio if viento_medio is not None else 10.0
    h = rh if rh is not None else 65.0
    
    rad_factor = _clamp(rad / 800.0)
    var_factor = _clamp(var_t / 0.6)
    nub_factor = 1.0 - _clamp(nub / 100.0)
    viento_factor = _clamp(1.0 - (v / 20.0))
    hum_factor = _clamp(1.0 - (h / 100.0))
    
    score = 100.0 * (
        0.4 * rad_factor +
        0.2 * var_factor +
        0.2 * nub_factor +
        0.1 * viento_factor +
        0.1 * hum_factor
    )
    return _clamp_pct(score)


def barro_campo_robusto(
    lluvia_24h: Optional[float],
    lluvia_1h: Optional[float],
    viento_medio: Optional[float],
    temp_c: Optional[float],
    dew_c: Optional[float],
    historico_secado: float = 60.0
) -> float:
    """
    Índice de barro/secado de campo para cetrería (0-100).
    Robusto contra sensores faltantes.
    
    0-100: 0 = campos encharcados, 100 = terreno seco
    """
    if all(v is None for v in [lluvia_24h, lluvia_1h, viento_medio]):
        return _clamp_pct(historico_secado)
    
    lluvia_24 = lluvia_24h if lluvia_24h is not None else 0.0
    lluvia_1 = lluvia_1h if lluvia_1h is not None else 0.0
    v = viento_medio if viento_medio is not None else 10.0
    
    # Estimar secado por viento y temp
    if temp_c is None or dew_c is None:
        secado_factor = _clamp(v / 20.0)
    else:
        secado_factor = _clamp((v / 20.0) + ((temp_c - dew_c) / 10.0))
    
    lluvia_factor = _clamp(lluvia_24 / 20.0)
    reciente_factor = _clamp(lluvia_1 / 5.0)
    
    score = 100.0 * (
        0.6 * (1.0 - lluvia_factor) +
        0.3 * (1.0 - reciente_factor) +
        0.1 * secado_factor
    )
    return _clamp_pct(score)


def confort_ave_robusto(
    temp_c: Optional[float],
    sensacion_termica: Optional[float],
    radiacion_real: Optional[float],
    viento_medio: Optional[float],
    historico_confort: float = 70.0
) -> float:
    """
    Índice de confort del ave para cetrería (0-100).
    Robusto contra sensores faltantes.
    
    Ideal: 16-22°C, sin radiación excesiva, viento moderado.
    """
    if temp_c is None and sensacion_termica is None:
        return _clamp_pct(historico_confort)
    
    t = temp_c if temp_c is not None else sensacion_termica
    s = sensacion_termica if sensacion_termica is not None else t
    v = viento_medio if viento_medio is not None else 10.0
    r = radiacion_real if radiacion_real is not None else 500.0
    
    if t is None:
        t = 18.0
    if s is None:
        s = t
    
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


def sensacion_termica_cetrera(temp_c: Optional[float], humedad_pct: Optional[float], viento_ms: Optional[float]) -> Optional[float]:
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


def sensacion_termica_cetrera(temp_c: Optional[float], humedad_pct: Optional[float], viento_ms: Optional[float]) -> Optional[float]:
    """
    Estimador simple de sensación térmica para cetrería.
    Usa aproximación tipo 'apparent temperature' (BOM-style):
      AT = T + 0.33*e - 0.7*v - 4.0
    donde e es presión de vapor en hPa.
    Intentamos delegar en `saturacion_vapor_hyland_wexler` para calcular e_s.
    """
    if temp_c is None or humedad_pct is None:
        return None
    try:
        from core.indices.environmental_indices import saturacion_vapor_hyland_wexler
        presion_pa = saturacion_vapor_hyland_wexler(float(temp_c), 101325.0)
        if presion_pa is None:
            raise Exception("no es_pa")
        e_pa = float(presion_pa) * (float(humedad_pct) / 100.0)
        e_hpa = e_pa / 100.0
    except Exception:
        # Fallback sencillo si no se puede obtener Hyland-Wexler
        try:
            # Magnus-Tetens approx for e_s in hPa
            a = 6.116441
            b = 17.62391
            c = 243.12
            import math
            ln_es = (b * float(temp_c)) / (c + float(temp_c))
            es_hpa = a * math.exp(ln_es)
            e_hpa = es_hpa * (float(humedad_pct) / 100.0)
        except Exception:
            return None

    v = float(viento_ms) if viento_ms is not None else 0.0
    at = float(temp_c) + 0.33 * float(e_hpa) - 0.7 * v - 4.0
    return round(at, 1)


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

    viento = viento_cetreria_robusto(viento_med, rachas)
    visibilidad = visibilidad_terreno_robusto(temp_c, dew_c, rh, nub)
    termales = termales_probabilidad_robusto(radiacion, var_t_5min, nub, viento_med, rh)
    barro = barro_campo_robusto(lluvia_24h, lluvia_1h, viento_med, temp_c, dew_c)
    confort = confort_ave_robusto(temp_c, sensacion, radiacion, viento_med)
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
