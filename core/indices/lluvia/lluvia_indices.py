"""
LLUVIA INDICES v2.0 - REEMPLAZADA FÍSICA REAL

Índices para predicción de lluvia y riesgo:
  1. Riesgo de inundación (basado en lluvia reciente + presión)
  2. Visibilidad en carretera (Kasten-Hanel PM2.5 + higroscopía)
  3. Adherencia terreno (lluvia + secado por viento)
  4. Probabilidad de rayos (Sundqvist calor latente + convección CAPE)

Cambios principales:
- probabilidad_lluvia: REEMPLAZADA por calcular_probabilidad_lluvia_sundqvist()
- visibilidad_carretera: REEMPLAZADA por visibilidad_kasten_hanel()
- Índice sintético: cálculo integral que NO es simple promedio

Fecha: 10 de febrero de 2026
"""

from typing import Dict, Optional, Union
import logging
import math
import numpy as np

logger = logging.getLogger(__name__)


def _clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min(value, max_value), min_value)


# ============================================================================
# ÍNDICES ROBUSTOS DE LLUVIA
# ============================================================================

def riesgo_inundacion_robusto(
    lluvia_24h: Optional[float],
    lluvia_72h: Optional[float],
    presion_hpa: Optional[float],
    historico: float = 20.0
) -> float:
    """
    Riesgo de inundación (0-100).
    
    0 = sin riesgo, 100 = riesgo máximo de inundación.
    Considera lluvia acumulada + presión barométrica baja.
    
    Robusto: nunca None.
    """
    if all(v is None for v in [lluvia_24h, lluvia_72h, presion_hpa]):
        return _clamp(historico, 0, 100)
    
    lluvia_24 = lluvia_24h if lluvia_24h is not None else 0.0
    lluvia_72 = lluvia_72h if lluvia_72h is not None else 0.0
    presion = presion_hpa if presion_hpa is not None else 1013.25
    
    # Factor lluvia: escalado a riesgo
    lluvia_24_factor = _clamp(lluvia_24 / 50.0)  # >50mm = riesgo alto
    lluvia_72_factor = _clamp(lluvia_72 / 100.0)  # >100mm en 72h = crítico
    
    # Factor presión: baja presión favoreceaguaceros
    presion_factor = _clamp(1.0 - (presion / 1013.25))  # <1000 hPa = riesgoso
    
    score = 100.0 * (
        0.5 * lluvia_24_factor +
        0.35 * lluvia_72_factor +
        0.15 * presion_factor
    )
    return _clamp(score, 0, 100)


def visibilidad_carretera_robusto(
    lluvia_horaria: Optional[float],
    nubosidad: Optional[float],
    humedad: Optional[float],
    pm25: Optional[float] = None,
    historico: float = 85.0
) -> float:
    """
    Visibilidad en carretera (0-100) usando KASTEN-HANEL.
    
    100 = excelente visibilidad, 0 = muy mala (lluvia + niebla + aerosoles).
    
    NUEVO: Usa fórmula Kasten-Hanel en lugar heurística simple.
    - Incorpora PM2.5 si disponible (aerosoles)
    - Crecimiento higroscópico del aerosol (RH > 80%)
    - Lluvia reduce visibilidad directamente
    
    Robusto: nunca None.
    """
    if all(v is None for v in [lluvia_horaria, nubosidad, humedad]):
        return _clamp(historico, 0, 100)
    
    lluvia = lluvia_horaria if lluvia_horaria is not None else 0.0
    hum = humedad if humedad is not None else 70.0
    pm = pm25 if pm25 is not None else 10.0  # Fallback a PM2.5 bajo
    
    # Usar visibilidad Kasten-Hanel directamente
    try:
        from core.indices.advanced_physics_models import visibilidad_kasten_hanel
        vis_km = visibilidad_kasten_hanel(hum, pm)
        # Convertir de km a escala 0-100
        # 50 km = visibilidad excelente (100%)
        # 1 km = visibilidad muy mala (0%)
        vis_factor = _clamp(vis_km / 50.0)
    except ImportError:
        # Fallback: heurístico simple
        logger.warning("Kasten-Hanel no disponible, usando fallback heurístico")
        vis_factor = 1.0 - _clamp(pm / 100.0) - _clamp((hum - 80.0) / 20.0)
    
    # Lluvia reduce visibilidad drásticamente
    lluvia_factor = 1.0 - _clamp(lluvia / 5.0)  # >5mm/h = muy mala
    
    # Combinación física: lluvia + visibilidad Kasten
    score = 100.0 * (
        0.6 * vis_factor * lluvia_factor +  # Lluvia * Kasten-Hanel
        0.4 * vis_factor  # Kasten-Hanel como base
    )
    return _clamp(score, 0, 100)


def adherencia_terreno_robusto(
    lluvia_24h: Optional[float],
    lluvia_1h: Optional[float],
    viento: Optional[float],
    temp: Optional[float],
    dew: Optional[float],
    historico: float = 70.0
) -> float:
    """
    Adherencia del terreno (0-100).
    
    100 = terreno seco (buen agarre), 0 = encharcado/resbaladizo.
    
    Robusto: nunca None.
    """
    if all(v is None for v in [lluvia_24h, viento, temp]):
        return _clamp(historico, 0, 100)
    
    lluvia_24 = lluvia_24h if lluvia_24h is not None else 0.0
    lluvia_1 = lluvia_1h if lluvia_1h is not None else 0.0
    v = viento if viento is not None else 8.0
    t = temp if temp is not None else 15.0
    d = dew if dew is not None else 10.0
    
    # Lluvia penaliza
    lluvia_factor = _clamp(lluvia_24 / 30.0)  # >30mm = muy mojado
    reciente_factor = _clamp(lluvia_1 / 5.0)  # lluvia reciente
    
    # Secado por viento y temp
    secado_factor = _clamp((v / 15.0) * ((t - d) / 10.0))
    
    score = 100.0 * (
        0.5 * (1.0 - lluvia_factor) +
        0.3 * (1.0 - reciente_factor) +
        0.2 * secado_factor
    )
    return _clamp(score, 0, 100)


def probabilidad_rayos_robusto(
    presion_hpa: Optional[float],
    temp_c: Optional[float],
    humedad: Optional[float],
    qc: Optional[float] = None,  # Agua nube (g/kg) si disponible
    qr: Optional[float] = None,  # Agua lluvia (g/kg) si disponible
    historico: float = 15.0
) -> float:
    """
    Probabilidad de rayos/tormentas (0-100) usando SUNDQVIST.
    
    0 = sin riesgo, 100 = alto riesgo de tormentas eléctricas.
    
    NUEVO: Usa Sundqvist calor latente + balance de energía en lugar heurística simple.
    - Si qc/qr disponibles: calor latente de condensación
    - Si no: fallback a presión + temperatura + humedad (CAPE simple)
    
    Principio: Rayos requieren energía térmica latente. Si no hay condensación, no hay tormenta.
    
    Robusto: nunca None.
    """
    if all(v is None for v in [presion_hpa, temp_c, humedad]):
        return _clamp(historico, 0, 100)
    
    presion = presion_hpa if presion_hpa is not None else 1013.25
    temp = temp_c if temp_c is not None else 15.0
    hum = humedad if humedad is not None else 65.0
    
    # INTENTO 1: Usar Sundqvist si disponemos de agua nube/lluvia
    try:
        from core.indices.sundqvist_precipitation import calcular_probabilidad_lluvia_sundqvist
        
        qc_val = qc if qc is not None else 0.1  # g/kg agua nube mínimo
        qr_val = qr if qr is not None else 0.01  # g/kg agua lluvia
        
        resultado_sundqvist = calcular_probabilidad_lluvia_sundqvist(
            temperatura_c=temp,
            humedad_relativa=hum,
            presion_hpa=presion,
            qc=qc_val,
            qr=qr_val,
            tendencia_presion_hpa_h=-1.0  # Asumimos caída leve (tormentoso)
        )
        
        # Probabilidad lluvia Sundqvist ≈ probabilidad rayos
        prob_lluvia = resultado_sundqvist.get("prob_lluvia_pct", 0.0)
        calor_latente = resultado_sundqvist.get("calor_latente_wm2", 0.0)
        
        # Score: combina probabilidad + energía
        rayo_factor = _clamp(prob_lluvia / 100.0)
        energia_factor = _clamp(calor_latente / 500.0)  # >500 W/m² = muy activo
        
        score = 100.0 * (
            0.6 * rayo_factor +     # Probabilidad lluvia
            0.4 * energia_factor    # Energía térmica
        )
        return _clamp(score, 0, 100)
        
    except ImportError:
        logger.warning("Sundqvist no disponible, usando fallback CAPE simple")
    
    # FALLBACK 2: CAPE heurístico simple (presión + convección)
    # Presión baja = inestabilidad
    presion_factor = _clamp(max(0, 1.0 - (presion / 1013.25)) * 2.0)  # <1000 hPa crítico
    
    # CAPE simple: (T - Td) para estabilidad
    #  (aproximamos Td desde HR)
    td_approx = temp - ((100.0 - hum) / 5.0)
    delta_t = temp - td_approx
    
    # Temperatura alta + humedad alta = convección
    temp_factor = _clamp((temp - 15.0) / 20.0)  # >35°C = alto riesgo
    hum_factor = _clamp(hum / 100.0)  # >90% = saturado
    unstable_factor = _clamp(delta_t / 5.0)  # >5°C = inestable
    
    convection = temp_factor * hum_factor * unstable_factor
    
    score = 100.0 * (
        0.5 * presion_factor +
        0.5 * convection
    )
    return _clamp(score, 0, 100)


# ============================================================================
# ÍNDICE SINTÉTICO LLUVIA
# ============================================================================

def indice_lluvia_sintetico(riesgo_inundacion: float, visibilidad_carretera: float, adherencia_terreno: float, probabilidad_rayos: float, lluvia_1h: Optional[float] = None) -> float:
    if lluvia_1h is None:
        lluvia_1h = 0.0
    if lluvia_1h > 0.1:
        vis_penalizacion = _clamp(1.0 - (lluvia_1h / 10.0))
        visib_ajustada = visibilidad_carretera * vis_penalizacion
        adher_penalizacion = _clamp(1.0 - (lluvia_1h / 5.0))
        adher_ajustada = adherencia_terreno * adher_penalizacion
        riesgo_lluvia_extra = _clamp((lluvia_1h / 50.0) ** 1.5 * 40.0)
        riesgo_ajustado = _clamp(riesgo_inundacion + riesgo_lluvia_extra, 0, 100)
        rayos_penalizacion = _clamp(1.0 + (lluvia_1h / 20.0))
        rayos_ajustados = _clamp(probabilidad_rayos * rayos_penalizacion, 0, 100)
        indice_lluvia = _clamp(0.30 * (100 - riesgo_ajustado) + 0.25 * visib_ajustada + 0.25 * adher_ajustada + 0.20 * (100 - rayos_ajustados), 0, 100)
        return indice_lluvia
    else:
        indice_lluvia = _clamp(0.30 * (100 - riesgo_inundacion) + 0.25 * visibilidad_carretera + 0.25 * adherencia_terreno + 0.20 * (100 - probabilidad_rayos), 0, 100)
        return indice_lluvia



def calcular_lluvia_completa(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Calcula TODOS los índices de lluvia/riesgo.
    
    Entrada: Dict con sensores clima
    Salida: 5 índices (4 componentes + 1 sintético)
    """
    
    lluvia_24h = data.get("lluvia_24h")
    lluvia_72h = data.get("lluvia_72h")
    lluvia_1h = data.get("lluvia_1h")
    presion = data.get("presion_barometrica")  # En hPa
    nubosidad = data.get("nubosidad_estimada")
    humedad = data.get("humedad")
    viento = data.get("viento_medio")
    temp = data.get("temperatura")
    dew = data.get("punto_rocio")
    
    # Convertir presión si está en Pa
    if presion is not None and presion > 2000:
        presion = presion / 100.0
    
    # Calcular índices robustos
    riesgo_inund = riesgo_inundacion_robusto(lluvia_24h, lluvia_72h, presion)
    visib_carr = visibilidad_carretera_robusto(lluvia_1h, nubosidad, humedad)
    adher_terr = adherencia_terreno_robusto(lluvia_24h, lluvia_1h, viento, temp, dew)
    prob_rayos = probabilidad_rayos_robusto(presion, temp, humedad)
    
    # Índice sintético con lluvia actual como entrada (INTEGRAL, no simple promedio)
    indice_sint = indice_lluvia_sintetico(riesgo_inund, visib_carr, adher_terr, prob_rayos, lluvia_1h=lluvia_1h)
    
    return {
        "riesgo_inundacion": riesgo_inund,
        "visibilidad_carretera": visib_carr,
        "adherencia_terreno": adher_terr,
        "probabilidad_rayos": prob_rayos,
        "indice_lluvia_sintetico": indice_sint,
        "indice_lluvia": indice_sint  # Compatibilidad
    }
