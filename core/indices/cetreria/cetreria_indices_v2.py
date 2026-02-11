"""
CETRERÍA INDICES v2.0 - Robusto + Sintético

Mejoras:
  1. Cada función es robusta contra None (nunca colapsa)
  2. Usa fallback histórico de Argentona si sensores faltantes
  3. Integra índice sintético robusto dinámico
  4. Publica índice final 0-100 con pesos adaptativos

Fecha: 10 de febrero de 2026
"""

from __future__ import annotations
import math
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    """Acotar valor entre min y max."""
    return max(min(value, max_value), min_value)


def _clamp_pct(value: float) -> float:
    """Acotar a porcentaje 0-100."""
    return _clamp(value, 0.0, 100.0)


def _dewpoint_c(temp_c: float, rh: float) -> float:
    """Punto de rocío WEXLER NIST 2026."""
    from core.indices.environmental_indices import _dew_point
    return _dew_point(temp_c, rh)


# ============================================================================
# FUNCIONES ROBUSTAS CONTRA None
# ============================================================================

def viento_cetreria_robusto(
    viento_medio: Optional[float],
    rachas: Optional[float],
    historico_fallback: float = 12.5
) -> float:
    """Índice viento cetrería (0-100, nunca None)."""
    if viento_medio is None and rachas is None:
        v = historico_fallback
        r = historico_fallback
    else:
        v = viento_medio if viento_medio is not None else (rachas if rachas is not None else historico_fallback)
        r = rachas if rachas is not None else (viento_medio if viento_medio is not None else historico_fallback)
    
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
    historico: float = 75.0
) -> float:
    """Índice visibilidad cetrería (0-100, nunca None)."""
    if all(v is None for v in [temp_c, rh, nubosidad]):
        return _clamp_pct(historico)
    
    t = temp_c if temp_c is not None else 15.0
    h = rh if rh is not None else 70.0
    n = nubosidad if nubosidad is not None else 50.0
    
    if dew_c is None:
        try:
            dew = _dewpoint_c(t, h)
        except:
            dew = t - ((100.0 - h) / 5.0)
    else:
        dew = dew_c
    
    delta_t = max(t - dew, 0.0)
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
    historico: float = 45.0
) -> float:
    """Probabilidad de térmicas (0-100, nunca None)."""
    sensores_ok = sum([
        radiacion_real is not None,
        nubosidad is not None,
        viento_medio is not None,
        rh is not None
    ])
    
    if sensores_ok < 2:
        return _clamp_pct(historico)
    
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
    historico: float = 60.0
) -> float:
    """Índice secado campo (0-100, nunca None). 100=seco, 0=encharcado."""
    if all(v is None for v in [lluvia_24h, lluvia_1h, viento_medio]):
        return _clamp_pct(historico)
    
    lluvia_24 = lluvia_24h if lluvia_24h is not None else 0.0
    lluvia_1 = lluvia_1h if lluvia_1h is not None else 0.0
    v = viento_medio if viento_medio is not None else 10.0
    
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
    historico: float = 70.0
) -> float:
    """Índice confort del ave (0-100, nunca None). Ideal 16-22°C."""
    if temp_c is None and sensacion_termica is None:
        return _clamp_pct(historico)
    
    t = temp_c if temp_c is not None else (sensacion_termica if sensacion_termica is not None else 18.0)
    s = sensacion_termica if sensacion_termica is not None else t
    v = viento_medio if viento_medio is not None else 10.0
    r = radiacion_real if radiacion_real is not None else 500.0
    
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


def sensacion_termica_cetrera(
    temp_c: Optional[float],
    humedad_pct: Optional[float],
    viento_ms: Optional[float]
) -> Optional[float]:
    """Sensación térmica BOM-style. AT = T + 0.33*e - 0.7*v - 4.0"""
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
        try:
            a = 6.116441
            b = 17.62391
            c = 243.12
            ln_es = (b * float(temp_c)) / (c + float(temp_c))
            es_hpa = a * math.exp(ln_es)
            e_hpa = es_hpa * (float(humedad_pct) / 100.0)
        except Exception:
            return None

    v = float(viento_ms) if viento_ms is not None else 0.0
    at = float(temp_c) + 0.33 * float(e_hpa) - 0.7 * v - 4.0
    return round(at, 1)


# ============================================================================
# ÍNDICE SINTÉTICO ROBUSTO (Usa pesos adaptativos dinámicos)
# ============================================================================

def indice_cetreria_sintetico(
    viento: float,
    visibilidad: float,
    termales: float,
    barro: float,
    confort: float,
    lluvia_1h: Optional[float] = None,
    riesgo_escorrentia: Optional[float] = None
) -> float:
    """
    Índice sintético cetrería 0-100 - SUMA PONDERADA DE 5 COMPONENTES + CONTEXTOS.
    
    PESOS EXPLÍCITOS:
    - viento: 25% - Crucial para vuelo seguro del ave
    - visibilidad: 25% - Visibilidad del terreno para cazar
    - termales: 15% - Corrientes ascendentes para ahorrar energía
    - barro: 15% - Condición del campo para trabajo
    - confort: 20% - Bienestar térmico del ave
    
    CONTEXTOS:
    - lluvia_1h: Lluvia penaliza fuerte (TODOS los componentes)
    - riesgo_escorrentia: Barro extremadamente mojado/innavegable (penaliza barro)
    """
    
    if lluvia_1h is None:
        lluvia_1h = 0.0
    if riesgo_escorrentia is None:
        riesgo_escorrentia = 0.0
    
    # ESCENARIO 1: LLUVIA EN PROGRESO (lluvia_1h > 0.1 mm)
    if lluvia_1h > 0.1:
        logger.debug(f"LLUVIA EN PROGRESO ({lluvia_1h:.2f}mm): Cetrería NO RECOMENDADA")
        
        # Lluvia afecta TODO:
        viento_lluvia = _clamp_pct(viento * (1.0 - (lluvia_1h / 5.0)))
        visib_lluvia = _clamp_pct(visibilidad * (1.0 - (lluvia_1h / 3.0)))
        termales_lluvia = _clamp_pct(termales * max(0, 1.0 - (lluvia_1h / 2.0)))
        barro_lluvia = _clamp_pct(barro * 0.3)  # 70% reducción fija
        confort_lluvia = _clamp_pct(confort * (1.0 - (lluvia_1h / 4.0)))
        
        # SUMA PONDERADA de los 5 componentes penalizados
        indice_lluvia = _clamp_pct(
            0.25 * viento_lluvia +     # viento: 25%
            0.25 * visib_lluvia +      # visibilidad: 25%
            0.15 * termales_lluvia +   # termales: 15%
            0.15 * barro_lluvia +      # barro: 15% (ya mojado)
            0.20 * confort_lluvia      # confort: 20%
        )
        
        # PENALIZACIÓN ADICIONAL EXPONENCIAL: Si llueve, es un mal día
        penalizacion_lluvia = 1.0 - ((lluvia_1h / 50.0) ** 0.8)
        indice_final = indice_lluvia * penalizacion_lluvia
        
        logger.debug(
            f"Cetrería con lluvia: viento={viento_lluvia:.1f}, visib={visib_lluvia:.1f}, "
            f"termales={termales_lluvia:.1f}, barro={barro_lluvia:.1f}, "
            f"confort={confort_lluvia:.1f} -> final={indice_final:.1f}"
        )
        
        return _clamp_pct(indice_final)
    
    # ESCENARIO 2: ESCORRENTIA EXTREMA (barro muy mojado)
    elif riesgo_escorrentia > 75.0:
        logger.debug(f"ESCORRENTIA EXTREMA ({riesgo_escorrentia:.0f}%): Cetrería COMPROMETIDA (barro intransitable)")
        
        # Barro intransitable por exceso de agua
        barro_escor = _clamp_pct(barro * (1.0 - ((riesgo_escorrentia - 75.0) / 25.0) * 0.7))
        
        indice_escor = _clamp_pct(
            0.25 * viento +            # viento: normal
            0.25 * visibilidad +       # visibilidad: normal
            0.15 * termales +          # termales: normal
            0.15 * barro_escor +       # barro: REDUCIDO (mojado)
            0.20 * confort             # confort: normal
        )
        
        logger.debug(f"Cetrería con escorrentía: {indice_escor:.1f}%")
        return _clamp_pct(indice_escor)
    
    # ESCENARIO 3: SIN LLUVIA - SUMA PONDERADA estándar
    else:
        indice_normal = _clamp_pct(
            0.25 * viento +            # viento: 25%
            0.25 * visibilidad +       # visibilidad: 25%
            0.15 * termales +          # termales: 15%
            0.15 * barro +             # barro: 15%
            0.20 * confort             # confort: 20%
        )
        
        logger.debug(
            f"Cetrería sin lluvia: viento={viento:.1f}, visib={visibilidad:.1f}, "
            f"termales={termales:.1f}, barro={barro:.1f}, "
            f"confort={confort:.1f} -> indice={indice_normal:.1f}"
        )
        
        return indice_normal


# ============================================================================
# FUNCIÓN PRINCIPAL: CALCULAR TODOS LOS ÍNDICES
# ============================================================================

def calcular_cetreria_completa(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Calcula TODOS los índices de cetrería.
    
    Entrada: Dict con sensores clima (temperatura, viento, lluvia, humedad, etc.)
    Salida: Dict con 12+ índices incluyendo sintético final
    
    GARANTÍA: Nunca retorna None para índices principales. Si sensor falta,
             usa fallback histórico de Argentona.
    """
    
    # Extraer sensores
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
    viento_ms = data.get("velocidad_viento")  # En m/s si disponible

    # Calcular índices robustos (nunca None)
    viento = viento_cetreria_robusto(viento_med, rachas)
    visibilidad = visibilidad_terreno_robusto(temp_c, dew_c, rh, nub)
    termales = termales_probabilidad_robusto(radiacion, var_t_5min, nub, viento_med, rh)
    barro = barro_campo_robusto(lluvia_24h, lluvia_1h, viento_med, temp_c, dew_c)
    confort = confort_ave_robusto(temp_c, sensacion, radiacion, viento_med)
    
    # Índice sintético = valoración integral (lluvia incorporada en la fórmula)
    indice_sintetico = indice_cetreria_sintetico(viento, visibilidad, termales, barro, confort, lluvia_1h=lluvia_1h, riesgo_escorrentia=data.get("riesgo_escorrentia"))
    
    # Sensación térmica (puede ser None)
    sens_termica = sensacion_termica_cetrera(temp_c, rh, viento_ms)
    
    return {
        # Índices individuales (robustos)
        "viento_cetreria": viento,
        "visibilidad_terreno": visibilidad,
        "termales_probabilidad": termales,
        "barro_campo": barro,
        "confort_ave": confort,
        
        # Índice sintético final (más importante)
        "indice_cetreria_sintetico": indice_sintetico,
        
        # Información adicional
        "sensacion_termica_cetrera": sens_termica,
        
        # Para compatibilidad con código antiguo
        "indice_cetreria": indice_sintetico
    }
