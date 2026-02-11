"""
SALUD INDICES v2.0 - Riesgos de Salud Ambiental

Índices para salud pública y personal:
  1. Índice UV personal (0-100) - riesgo quemadura solar
  2. Riesgo estrés por calor extremo (0-100)
  3. Riesgo hipotermia/frío extremo (0-100)
  4. Riesgo helada agrícola (0-100) - Yates-McLean
  5. Salud del aire interior (0-100) - ASHRAE 62.1
  6. Alerta calidad aire exterior (0-100)

Referencias:
  - OMS: Índice UV, alertas de calor
  - ISO 7243: WBGT (estrés térmico ocupacional)
  - Yates-McLean: Heladas radiativas agrarias
  - ASHRAE 62.1: Calidad aire interior

Fecha: 10 de febrero de 2026
"""

from typing import Dict, Optional
import logging
import math
import time

logger = logging.getLogger(__name__)

# Importar config de timing
try:
    from core.system.config_dominios import LOGGING_CONFIG
except ImportError:
    LOGGING_CONFIG = {"enabled": True, "log_timing_functions": True, "timing_threshold_ms": 10}


def _clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    """Clamp value between min and max."""
    return max(min(value, max_value), min_value)


# ============================================================================
# SUB-ÍNDICES ROBUSTOS DE SALUD
# ============================================================================

def indice_uv_personal_robusto(
    radiacion_global: Optional[float],
    elevacion_solar: Optional[float],
    historico: float = 30.0
) -> float:
    """
    Índice UV personal (0-100).
    
    Mapeo estándar OMS/WMO:
    - 0-2: bajo (0-25%)
    - 3-5: moderado (26-50%)
    - 6-7: alto (51-75%)
    - 8-10: muy alto (76-90%)
    - 11+: extremo (91-100%)
    
    Simplificado de radiación + elevación solar.
    
    Robusto: nunca None.
    """
    if all(v is None for v in [radiacion_global, elevacion_solar]):
        return _clamp(historico, 0, 100)
    
    rad = radiacion_global if radiacion_global is not None else 500.0
    elev = elevacion_solar if elevacion_solar is not None else 45.0
    
    # UVI ≈ (radiación × cos(zenith)) / 25
    # Simplificado: radiación en W/m², elev en grados
    
    # Zenith angle (90 - elevación)
    zenith = max(0, 90 - elev)
    cos_zenith = max(0, math.cos(math.radians(zenith)))
    
    # UVI estimado
    uvi = (rad * cos_zenith) / 25.0
    
    # Mapear UVI (0-12) a 0-100
    score = (uvi / 12.0) * 100.0
    
    return _clamp(score, 0, 100)


def riesgo_calor_extremo_robusto(
    temperatura_c: Optional[float],
    humedad_pct: Optional[float],
    radiacion_w_m2: Optional[float] = 0.0,
    viento_kmh: Optional[float] = None,
    historico: float = 20.0
) -> float:
    """
    Riesgo de estrés térmico por calor extremo (0-100).
    
    Basado en:
    - Temperatura > 32°C
    - Humedad > 60%
    - UV alto
    - Viento bajo (sin ventilación)
    
    Scoring:
    - 0-30: sin riesgo (verde)
    - 31-50: riesgo moderado (amarillo)
    - 51-75: riesgo alto (naranja)
    - 76-100: riesgo severo (rojo, golpe de calor)
    
    Robusto: nunca None.
    """
    if all(v is None for v in [temperatura_c, humedad_pct]):
        return _clamp(historico, 0, 100)
    
    temp = temperatura_c if temperatura_c is not None else 25.0
    humedad = humedad_pct if humedad_pct is not None else 50.0
    rad = radiacion_w_m2 if radiacion_w_m2 is not None else 0.0
    viento = viento_kmh if viento_kmh is not None else 5.0
    
    score = 0.0
    
    # Penalización por temperatura alta
    if temp > 32:
        score += min(40, (temp - 32) * 2)  # Hasta 40 puntos
    
    # Penalización por humedad alta
    if humedad > 60:
        score += min(30, (humedad - 60) * 0.5)  # Hasta 30 puntos
    
    # Penalización por radiación alta
    if rad > 500:
        score += min(20, (rad - 500) / 25)  # Hasta 20 puntos
    
    # Penalización por viento bajo (sin ventilación)
    if viento < 2:
        score += 10
    
    return _clamp(score, 0, 100)


def riesgo_frio_extremo_robusto(
    temperatura_c: Optional[float],
    humedad_pct: Optional[float],
    viento_kmh: Optional[float],
    historico: float = 10.0
) -> float:
    """
    Riesgo de hipotermia por frío extremo (0-100).
    
    Basado en wind chill (temperatura percibida):
    WC = 13.12 + 0.6215×T - 11.37×(v^0.16) + 0.3965×T×(v^0.16)
    
    Scoring:
    - 0-30: sin riesgo (verde)
    - 31-60: riesgo moderado (amarillo)
    - 61-100: riesgo severo (rojo, hipotermia)
    
    Robusto: nunca None.
    """
    if all(v is None for v in [temperatura_c, viento_kmh]):
        return _clamp(historico, 0, 100)
    
    temp = temperatura_c if temperatura_c is not None else 15.0
    viento = viento_kmh if viento_kmh is not None else 5.0
    humedad = humedad_pct if humedad_pct is not None else 50.0
    
    score = 0.0
    
    # Penalización por temperatura baja
    if temp < 5:
        score += min(40, (5 - temp) * 4)  # Hasta 40 puntos
    
    # Penalización por viento fuerte (wind chill)
    if viento > 10:
        score += min(30, (viento - 10) * 2)  # Hasta 30 puntos
    
    # Penalización por humedad baja (evaporación aumenta pérdida calor)
    if humedad < 40:
        score += min(30, (40 - humedad) * 0.5)  # Hasta 30 puntos
    
    return _clamp(score, 0, 100)


def riesgo_helada_local_robusto(
    punto_rocio_c: Optional[float],
    temperatura_c: Optional[float],
    humedad_pct: Optional[float],
    viento_kmh: Optional[float],
    radiacion_nocturna_factor: Optional[float] = None,
    historico: float = 20.0
) -> float:
    """
    Riesgo de helada local (Yates-McLean simplificado) (0-100).
    
    Para agricultura: riesgo de congelación en superficies/plantas.
    
    Factores:
    - Punto rocío cercano o bajo al suelo
    - Temperatura baja (<5°C)
    - Cielo despejado (radiación nocturna baja → enfriamiento radiativo)
    - Viento débil (no mezcla térmica)
    
    Scoring:
    - 0-30: sin riesgo (verde)
    - 31-60: riesgo moderado (amarillo)
    - 61-100: riesgo alto (rojo, helada probable)
    
    Robusto: nunca None.
    """
    if all(v is None for v in [punto_rocio_c, temperatura_c]):
        return _clamp(historico, 0, 100)
    
    pr = punto_rocio_c if punto_rocio_c is not None else 10.0
    temp = temperatura_c if temperatura_c is not None else 10.0
    humedad = humedad_pct if humedad_pct is not None else 60.0
    viento = viento_kmh if viento_kmh is not None else 5.0
    
    score = 0.0
    
    # Penalización: cuanto más cercano PR a T, más riesgo
    diff = temp - pr
    if diff < 3:
        score += min(40, (3 - diff) * 13)  # Hasta 40 puntos
    
    # Penalización por temperatura baja absoluta
    if temp < 5:
        score += min(30, (5 - temp) * 6)  # Hasta 30 puntos
    
    # Penalización por cielo despejado (absorción HR indica nubes)
    # Bajo HR de noche = cielo despejado = máxima radiación perdida
    if humedad < 50:
        score += min(20, (50 - humedad) * 0.4)  # Hasta 20 puntos
    
    # Penalización por viento débil (sin mezcla)
    if viento < 3:
        score += min(10, (3 - viento) * 3.3)  # Hasta 10 puntos
    
    return _clamp(score, 0, 100)


def salud_aire_interior_robusto(
    humedad_media_pct: Optional[float],
    humedad_alta_horas: Optional[float] = 0.0,
    historico: float = 75.0
) -> float:
    """
    Salud del aire interior (0-100) según ASHRAE 62.1.
    
    Factores:
    - Humedad media: 30-60% es óptimo (ASHRAE 160)
    - HR crónica > 60%: riesgo moho, ácaros, daño estructural
    - Tiempo exposición HR > 60%: acumulación temporal
    
    Scoring:
    - >70: edificio saludable (verde)
    - 40-70: aceptable (amarillo)
    - <40: muy seco o muy húmedo (rojo, riesgos respiratorios)
    
    Robusto: nunca None.
    """
    if humedad_media_pct is None:
        return _clamp(historico, 0, 100)
    
    humedad = humedad_media_pct
    hr_alta_h = humedad_alta_horas if humedad_alta_horas is not None else 0.0
    
    score = 100.0
    
    # Rango óptimo: 30-60%
    hr_opt_low = 30.0
    hr_opt_high = 60.0
    hr_warning = 70.0
    
    if humedad < hr_opt_low:
        # Muy seco: problemas respiratorios, grietas madera
        deficit = hr_opt_low - humedad
        score -= deficit * 0.5  # Penalización leve
    elif humedad <= hr_opt_high:
        # Óptimo: sin penalización
        pass
    elif humedad <= hr_warning:
        # Ligeramente elevada
        excess = humedad - hr_opt_high
        score -= excess * 1.0
    else:
        # Muy alta: riesgo moho, ácaros, daño
        excess = humedad - hr_warning
        score -= 10.0 + excess * 2.0
    
    # Penalización por tiempo crónico con HR alta
    if hr_alta_h > 24:  # Más de 1 día
        tiempo_factor = min(30.0, (hr_alta_h - 24) * 0.1)
        score -= tiempo_factor
    
    return _clamp(score, 0, 100)


def alerta_calidad_aire_exterior_robusto(
    visibilidad_km: Optional[float],
    humedad_pct: Optional[float],
    historico: float = 50.0
) -> float:
    """
    Alerta de calidad aire exterior (0-100, donde 100 = excelente).
    
    SIN sensor PM2.5: usar visibilidad como proxy.
    
    Lógica:
    - Visibilidad > 10km: aire bueno (75-100)
    - Visibilidad 5-10km: aire aceptable (50-75)
    - Visibilidad 1-5km: aire entre malo y muy malo (25-50)
    - Visibilidad < 1km: muy malo (0-25)
    
    Penalización adicional si HR > 80% (niebla contaminada).
    
    Robusto: nunca None.
    """
    if visibilidad_km is None:
        return _clamp(historico, 0, 100)
    
    visib = visibilidad_km
    humedad = humedad_pct if humedad_pct is not None else 60.0
    
    # Mapear visibilidad a 0-100
    if visib > 10:
        score = 100.0
    elif visib > 5:
        score = 50.0 + (visib - 5) * 10.0
    elif visib > 1:
        score = 25.0 + (visib - 1) * 6.25
    else:
        score = max(0.0, 25.0 - (1 - visib) * 25.0)
    
    # Penalización si niebla + humedad alta (niebla contaminada)
    if visib < 2 and humedad > 80:
        score *= 0.7  # Reducir 30%
    
    return _clamp(score, 0, 100)


# ============================================================================
# ÍNDICE SINTÉTICO DE SALUD
# ============================================================================

def indice_salud_sintetico(
    uvi: float,
    calor_extremo: float,
    frio_extremo: float,
    helada: float,
    aire_interior: float,
    aire_exterior: float,
    lluvia_1h: Optional[float] = None,
    amplitud_termica: Optional[float] = None,
    visibilidad_km: Optional[float] = None
) -> float:
    """
    Índice sintético de SALUD (0-100) - SUMA PONDERADA INVERTIDA DE 6 COMPONENTES + CONTEXTOS.
    
    PESOS EXPLÍCITOS (como RIESGOS, se invierten):
    - uvi: 25% - Riesgo UV (lo más importante)
    - calor_extremo: 20% - Riesgo de golpe de calor
    - frio_extremo: 20% - Riesgo de hipotermia
    - helada: 15% - Riesgo agrícola (menos crítico)
    - aire_interior: 10% - Riesgo mala ventilación (INVERTIDO: 100=salud, 0=riesgo)
    - aire_exterior: 10% - Riesgo contaminación (INVERTIDO: 100=salud, 0=riesgo)
    
    CONTEXTOS GLOBALES:
    - lluvia_1h: Lluvia = exposición mojado = hipotermia + dolor articular
    - amplitud_termica: Variación extrema = estrés térmico
    - visibilidad_km: Baja visibilidad = polución/niebla = riesgo respiratorio
    
    Lógica INVERSA:
    100 = sin riesgos (salud excelente)
    0 = múltiples riesgos críticos (salud muy pobre)
    """
    if lluvia_1h is None:
        lluvia_1h = 0.0
    if amplitud_termica is None:
        amplitud_termica = 50.0
    if visibilidad_km is None:
        visibilidad_km = 10.0
    
    # SUMA PONDERADA de RIESGOS base
    riesgo_base = (
        uvi * 0.25 +                          # UV: 25%
        calor_extremo * 0.20 +                # calor: 20%
        frio_extremo * 0.20 +                 # frío: 20%
        helada * 0.15 +                       # helada: 15%
        (100 - aire_interior) * 0.10 +        # aire interior: 10% (invertido)
        (100 - aire_exterior) * 0.10          # aire exterior: 10% (invertido)
    )
    
    # ESCENARIO 1: LLUVIA (aumenta riesgo de hipotermia y dolor articular)
    if lluvia_1h > 0.5:
        logger.debug(f"LLUVIA ({lluvia_1h:.2f}mm): Salud COMPROMETIDA (hipotermia, dolor)")
        
        # Lluvia aumenta riesgo de frío (mojado = pérdida térmica)
        frio_lluvia = _clamp(frio_extremo + (lluvia_1h / 50.0) * 30.0)  # Hasta +30%
        
        # Lluvia reduce aire exterior (atmósfera mojada)
        aire_ext_lluvia = _clamp(aire_exterior * (1.0 - (lluvia_1h / 30.0)))
        
        # Riesgo ajustado con lluvia
        riesgo_lluvia = (
            uvi * 0.25 +
            calor_extremo * 0.20 +
            frio_lluvia * 0.20 +               # Frío AUMENTADO
            helada * 0.15 +
            (100 - aire_interior) * 0.10 +
            (100 - aire_ext_lluvia) * 0.10
        )
        
        score = (1.0 - (riesgo_lluvia / 100.0)) * 100.0
        logger.debug(f"Salud con lluvia: {score:.1f}%")
        return _clamp(score)
    
    # ESCENARIO 2: AMPLITUD TÉRMICA EXTREMA (variación día-noche)
    elif amplitud_termica > 75.0:
        logger.debug(f"AMPLITUD TÉRMICA EXTREMA ({amplitud_termica:.0f}%): Salud INESTABLE")
        
        # Variación extrema = estrés térmico para el cuerpo
        penalizacion = (amplitud_termica - 75.0) / 25.0 * 20.0  # Hasta +20% riesgo
        riesgo_ampl = _clamp(riesgo_base + penalizacion)
        
        score = (1.0 - (riesgo_ampl / 100.0)) * 100.0
        logger.debug(f"Salud con amplitud térmica: {score:.1f}%")
        return _clamp(score)
    
    # ESCENARIO 3: VISIBILIDAD BAJA (polución, niebla)
    elif visibilidad_km < 3.0:
        logger.debug(f"VISIBILIDAD BAJA ({visibilidad_km:.1f}km): Salud RESPIRATORIA AFECTADA")
        
        # Baja visibilidad = contaminación/niebla = riesgo respiratorio
        aire_ext_reduced = _clamp(aire_exterior * (visibilidad_km / 10.0))
        
        riesgo_visib = (
            uvi * 0.25 +
            calor_extremo * 0.20 +
            frio_extremo * 0.20 +
            helada * 0.15 +
            (100 - aire_interior) * 0.10 +
            (100 - aire_ext_reduced) * 0.10  # Aire exterior REDUCIDO
        )
        
        score = (1.0 - (riesgo_visib / 100.0)) * 100.0
        logger.debug(f"Salud con baja visibilidad: {score:.1f}%")
        return _clamp(score)
    
    # ESCENARIO 4: CONDICIONES NORMALES
    else:
        score = (1.0 - (riesgo_base / 100.0)) * 100.0
        return _clamp(score)


# ============================================================================
# FUNCIONES CONVENIENCIA
# ============================================================================

def calcular_salud_completa(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Calcula TODOS los índices de salud en un call.
    
    Input: dict con llaves:
        - temperatura (°C)
        - humedad_relativa (%)
        - radiacion_w_m2
        - elevacion_solar (grados)
        - viento_kmh
        - punto_rocio (°C)
        - visibilidad_km
        - humedad_alta_hrs (opcional)
    
    Output: dict con:
        - indice_uvi (0-100)
        - riesgo_calor_extremo (0-100)
        - riesgo_frio_extremo (0-100)
        - riesgo_helada_local (0-100)
        - salud_aire_interior (0-100)
        - alerta_aire_exterior (0-100)
        - indice_salud_sintetico (0-100) ← PRINCIPAL
    
    Estructura: igual a cetreria/lluvia/deporte/confort v2.0
    """
    _t_inicio = time.time() if LOGGING_CONFIG.get("log_timing_functions") else None
    
    try:
        # Extraer inputs
        temp = data.get("temperatura")
        humedad = data.get("humedad_relativa")
        radiacion = data.get("radiacion_w_m2")
        elevacion = data.get("elevacion_solar")
        viento = data.get("viento_kmh")
        punto_rocio = data.get("punto_rocio")
        visibilidad = data.get("visibilidad_km")
        hr_alta_h = data.get("humedad_alta_hrs")
        
        # Calcular sub-índices
        uvi = indice_uv_personal_robusto(
            radiacion_global=radiacion,
            elevacion_solar=elevacion
        )
        
        calor = riesgo_calor_extremo_robusto(
            temperatura_c=temp,
            humedad_pct=humedad,
            radiacion_w_m2=radiacion,
            viento_kmh=viento
        )
        
        frio = riesgo_frio_extremo_robusto(
            temperatura_c=temp,
            humedad_pct=humedad,
            viento_kmh=viento
        )
        
        helada = riesgo_helada_local_robusto(
            punto_rocio_c=punto_rocio,
            temperatura_c=temp,
            humedad_pct=humedad,
            viento_kmh=viento
        )
        
        aire_int = salud_aire_interior_robusto(
            humedad_media_pct=humedad,
            humedad_alta_horas=hr_alta_h
        )
        
        aire_ext = alerta_calidad_aire_exterior_robusto(
            visibilidad_km=visibilidad,
            humedad_pct=humedad
        )
        
        # Sintético CON CONTEXTOS GLOBALES
        sintetico = indice_salud_sintetico(
            uvi=uvi,
            calor_extremo=calor,
            frio_extremo=frio,
            helada=helada,
            aire_interior=aire_int,
            aire_exterior=aire_ext,
            lluvia_1h=data.get("lluvia_1h"),
            amplitud_termica=data.get("amplitud_termica_tendencial"),
            visibilidad_km=visibilidad
        )
        
        resultado = {
            "indice_uvi": round(uvi, 1),
            "riesgo_calor_extremo": round(calor, 1),
            "riesgo_frio_extremo": round(frio, 1),
            "riesgo_helada_local": round(helada, 1),
            "salud_aire_interior": round(aire_int, 1),
            "alerta_aire_exterior": round(aire_ext, 1),
            "indice_salud_sintetico": round(sintetico, 1),
        }
        
        # Log timing
        if _t_inicio and LOGGING_CONFIG.get("log_timing_functions"):
            ms = (time.time() - _t_inicio) * 1000
            if ms > LOGGING_CONFIG.get("timing_threshold_ms", 10):
                logger.debug(f"[TIMING] calcular_salud_completa: {ms:.2f}ms")
        
        return resultado
    
    except Exception as e:
        logger.error(f"[ERROR] calcular_salud_completa: {e}", exc_info=True)
        
        # Log timing en error
        if _t_inicio and LOGGING_CONFIG.get("log_timing_functions"):
            ms = (time.time() - _t_inicio) * 1000
            if ms > LOGGING_CONFIG.get("timing_threshold_ms", 10):
                logger.debug(f"[TIMING] calcular_salud_completa (ERROR): {ms:.2f}ms")
        
        return {
            "indice_uvi": None,
            "riesgo_calor_extremo": None,
            "riesgo_frio_extremo": None,
            "riesgo_helada_local": None,
            "salud_aire_interior": None,
            "alerta_aire_exterior": None,
            "indice_salud_sintetico": 50.0,
        }
