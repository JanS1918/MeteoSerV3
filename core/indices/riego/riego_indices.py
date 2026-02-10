"""
RIEGO INDICES v2.0 - Necesidad de Riego y Balance Hídrico

Índices para gestión agrícola de agua:
  1. Balance hídrico neto (ΔH = Lluvia - ET0 - Escorrentía - Infiltración)
  2. Estrés hídrico del cultivo (factor 0-1, parametrizable por cultivo/suelo)
  3. Disponibilidad de agua cultivable (días hasta sequedad)
  4. Eficiencia de infiltración vs escorrentía

Referencias:
  - FAO-56: Evapotranspiración del cultivo (Allen et al., 1998)
  - Green-Ampt: Infiltración (Green & Ampt, 1911)
  - USDA: Capacidad de campo por tipo de suelo

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
# SUB-ÍNDICES ROBUSTOS DE RIEGO
# ============================================================================

def balance_hidrico_neto_robusto(
    lluvia_1h: Optional[float],
    lluvia_24h: Optional[float],
    et0_mm: Optional[float],
    escorrentia_mm: Optional[float] = None,
    infiltracion_mm: Optional[float] = None,
    historico: float = 50.0
) -> float:
    """
    Balance hídrico neto del día (0-100).
    
    ΔH = Lluvia - ET0 - Escorrentía - Infiltración
    
    100 = ganancia neta (>2mm), 0 = pérdida severa (<-3mm)
    50 = equilibrio
    
    Robusto: nunca None.
    """
    if all(v is None for v in [lluvia_24h, et0_mm]):
        return _clamp(historico, 0, 100)
    
    rain = lluvia_24h if lluvia_24h is not None else 0.0
    et0 = et0_mm if et0_mm is not None else 5.0  # ET0 medio ~5mm/día
    escor = escorrentia_mm if escorrentia_mm is not None else 0.0
    infil = infiltracion_mm if infiltracion_mm is not None else 0.5
    
    # ΔH = ganancia/pérdida neta
    delta_h = rain - et0 - escor - infil
    
    # Mapear a 0-100
    if delta_h >= 2.0:
        score = 100.0  # Ganancia importante
    elif delta_h >= 0.5:
        score = 75.0  # Ganancia moderada
    elif delta_h >= -0.5:
        score = 50.0  # Equilibrio
    elif delta_h >= -3.0:
        score = 25.0  # Pérdida moderada
    else:
        score = 0.0  # Pérdida severa (riego urgente)
    
    return _clamp(score, 0, 100)


def estres_hidrico_cultivo_robusto(
    humedad_suelo_pct: Optional[float],
    cultivo_tipo: str = "general",
    tipo_suelo: str = "franco",
    historico: float = 70.0
) -> float:
    """
    Factor de estrés hídrico del cultivo (0-100, donde 100 = sin estrés).
    
    Basado en humedad actual vs punto marchitez y capacidad de campo.
    Parámetricos por cultivo y tipo de suelo (FAO-56).
    
    Robusto: nunca None.
    """
    if humedad_suelo_pct is None:
        return _clamp(historico, 0, 100)
    
    # Parámetros por cultivo: punto marchitez permanente (%)
    cultivos = {
        'maíz': 12.0,
        'trigo': 14.0,
        'general': 15.0
    }
    
    # Parámetros por tipo suelo: capacidad de campo (%)
    suelos = {
        'arenoso': 18.0,
        'franco_arenoso': 24.0,
        'franco': 35.0,
        'franco_arcilloso': 42.0,
        'arcilla': 48.0
    }
    
    cultivo = cultivos.get(cultivo_tipo, cultivos['general'])
    h_cc = suelos.get(tipo_suelo, suelos['franco'])
    h_pm = cultivo
    
    # Factor de estrés
    if humedad_suelo_pct <= h_pm:
        factor = 0.0  # Marchito
    elif humedad_suelo_pct >= h_cc:
        factor = 1.0  # Sin estrés
    else:
        factor = (humedad_suelo_pct - h_pm) / (h_cc - h_pm)
    
    # Mapear a 0-100
    score = factor * 100.0
    return _clamp(score, 0, 100)


def disponibilidad_agua_robusto(
    humedad_suelo_pct: Optional[float],
    et0_promedio_7d_mm: Optional[float],
    cultivo_tipo: str = "general",
    tipo_suelo: str = "franco",
    historico: float = 70.0
) -> float:
    """
    Disponibilidad de agua cultivable (0-100).
    
    Estima días hasta sequedad: score=100 si >7 días, 0 si <0.5 días.
    
    Robusto: nunca None.
    """
    if all(v is None for v in [humedad_suelo_pct, et0_promedio_7d_mm]):
        return _clamp(historico, 0, 100)
    
    h_actual = humedad_suelo_pct if humedad_suelo_pct is not None else 40.0
    et0 = et0_promedio_7d_mm if et0_promedio_7d_mm is not None else 5.0
    
    # Parámetros
    cultivos = {
        'maíz': {'pm': 12.0, 'prof': 80},
        'trigo': {'pm': 14.0, 'prof': 60},
        'general': {'pm': 15.0, 'prof': 60}
    }
    
    suelos = {
        'arenoso': 18.0,
        'franco_arenoso': 24.0,
        'franco': 35.0,
        'franco_arcilloso': 42.0,
        'arcilla': 48.0
    }
    
    cp = cultivos.get(cultivo_tipo, cultivos['general'])
    h_pm = cp['pm']
    prof = cp['prof']
    h_cc = suelos.get(tipo_suelo, suelos['franco'])
    
    # Agua disponible (mm)
    agua_disp = max(0.0, (h_actual - h_pm) * prof * 10 / 100)
    
    # Días
    dias = agua_disp / et0 if et0 > 0 else 999.0
    
    # Mapear días a 0-100
    if dias > 7:
        score = 100.0
    elif dias > 4:
        score = 75.0
    elif dias > 1:
        score = 50.0
    elif dias > 0.5:
        score = 25.0
    else:
        score = 0.0
    
    return _clamp(score, 0, 100)


def eficiencia_infiltracion_robusto(
    lluvia_rate_mm_h: Optional[float],
    tipo_suelo: str = "franco",
    pendiente_terreno_pct: float = 5.0,
    historico: float = 60.0
) -> float:
    """
    Eficiencia de infiltración (0-100, donde 100 = toda el agua infiltra).
    
    Basado en Green-Ampt simplificado.
    Mapea tanto el tipo de suelo como el rate de lluvia.
    
    Robusto: nunca None.
    """
    if lluvia_rate_mm_h is None:
        return _clamp(historico, 0, 100)
    
    # Conductividad saturada por tipo suelo (mm/h)
    ks_valores = {
        'arenoso': 25.0,
        'franco_arenoso': 10.0,
        'franco': 6.0,
        'franco_arcilloso': 2.0,
        'arcilla': 0.3
    }
    
    ks = ks_valores.get(tipo_suelo, ks_valores['franco'])
    
    # Reducción por pendiente (agua escurre)
    pendiente_factor = max(0.3, 1.0 - (pendiente_terreno_pct / 100.0) * 0.7)
    
    # Infiltración potencial
    infiltr_potencial = ks * pendiente_factor
    
    # Proporción que infiltra
    if lluvia_rate_mm_h <= infiltr_potencial:
        score = 100.0  # Toda infiltra
    else:
        proporcion = infiltr_potencial / lluvia_rate_mm_h
        score = proporcion * 100.0
    
    return _clamp(score, 0, 100)


# ============================================================================
# ÍNDICE SINTÉTICO DE RIEGO
# ============================================================================

def indice_riego_sintetico(
    balance_hidrico: float,
    estres_hidrico: float,
    disponibilidad: float,
    eficiencia_infiltr: float,
    lluvia_1h: Optional[float] = None
) -> float:
    """
    Índice sintético de RIEGO (0-100).
    
    100 = riego no necesario (agua abundante)
    0 = riego urgente (sequedad crítica)
    
    Ponderación:
    - 40% disponibilidad (lo más importante)
    - 30% estrés cultivo
    - 20% balance hídrico
    - 10% eficiencia infiltración
    
    Con penalización por lluvia reciente (lluvia_1h).
    """
    # Ponderación base
    score = (
        disponibilidad * 0.40 +
        estres_hidrico * 0.30 +
        balance_hidrico * 0.20 +
        eficiencia_infiltr * 0.10
    )
    
    # Penalización si lluvia en última hora (riego no necesario ahora)
    if lluvia_1h is not None and lluvia_1h > 0.5:
        penalizacion = min(30.0, lluvia_1h * 10)  # Hasta -30 si lluvia reciente fuerte
        score = max(score - penalizacion, 0.0)
    
    return _clamp(score, 0, 100)


# ============================================================================
# FUNCIONES CONVENIENCIA
# ============================================================================

def calcular_riego_completa(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Calcula TODOS los índices de riego en un call.
    
    Input: dict con llaves:
        - lluvia_1h, lluvia_24h, lluvia_72h
        - humedad_suelo
        - et0_mm, et0_promedio_7d_mm
        - elevacion_solar (para validación)
        - [opcional] escorrentia_mm, infiltracion_mm, pendiente_terreno_pct
    
    Output: dict con:
        - balance_hidrico_neto (0-100)
        - estres_hidrico_cultivo (0-100)
        - disponibilidad_agua (0-100)
        - eficiencia_infiltacion (0-100)
        - indice_riego_sintetico (0-100) ← PRINCIPAL
        + componentes individuales
    
    Estructura: igual a cetreria/lluvia/deporte/confort v2.0
    """
    _t_inicio = time.time() if LOGGING_CONFIG.get("log_timing_functions") else None
    
    try:
        # Extraer inputs
        lluvia_1h = data.get("lluvia_1h")
        lluvia_24h = data.get("lluvia_24h")
        humedad_suelo = data.get("humedad_suelo")
        et0 = data.get("et0_mm")
        et0_7d = data.get("et0_promedio_7d_mm")
        escor = data.get("escorrentia_mm")
        infil = data.get("infiltracion_mm")
        pendiente = data.get("pendiente_terreno_pct", 5.0)
        tipo_suelo = data.get("tipo_suelo", "franco")
        cultivo = data.get("cultivo_tipo", "general")
        
        # Calcular sub-índices
        balance = balance_hidrico_neto_robusto(
            lluvia_1h=lluvia_1h,
            lluvia_24h=lluvia_24h,
            et0_mm=et0,
            escorrentia_mm=escor,
            infiltracion_mm=infil
        )
        
        estres = estres_hidrico_cultivo_robusto(
            humedad_suelo_pct=humedad_suelo,
            cultivo_tipo=cultivo,
            tipo_suelo=tipo_suelo
        )
        
        disponib = disponibilidad_agua_robusto(
            humedad_suelo_pct=humedad_suelo,
            et0_promedio_7d_mm=et0_7d,
            cultivo_tipo=cultivo,
            tipo_suelo=tipo_suelo
        )
        
        eficiencia = eficiencia_infiltracion_robusto(
            lluvia_rate_mm_h=data.get("lluvia_rate_mm_h"),
            tipo_suelo=tipo_suelo,
            pendiente_terreno_pct=pendiente
        )
        
        # Sintético
        sintetico = indice_riego_sintetico(
            balance_hidrico=balance,
            estres_hidrico=estres,
            disponibilidad=disponib,
            eficiencia_infiltr=eficiencia,
            lluvia_1h=lluvia_1h
        )
        
        resultado = {
            "balance_hidrico_neto": round(balance, 1),
            "estres_hidrico_cultivo": round(estres, 1),
            "disponibilidad_agua_cultivable": round(disponib, 1),
            "eficiencia_infiltracion": round(eficiencia, 1),
            "indice_riego_sintetico": round(sintetico, 1),
        }
        
        # Log timing
        if _t_inicio and LOGGING_CONFIG.get("log_timing_functions"):
            ms = (time.time() - _t_inicio) * 1000
            if ms > LOGGING_CONFIG.get("timing_threshold_ms", 10):
                logger.debug(f"[TIMING] calcular_riego_completa: {ms:.2f}ms")
        
        return resultado
    
    except Exception as e:
        logger.error(f"[ERROR] calcular_riego_completa: {e}", exc_info=True)
        
        # Log timing en error
        if _t_inicio and LOGGING_CONFIG.get("log_timing_functions"):
            ms = (time.time() - _t_inicio) * 1000
            if ms > LOGGING_CONFIG.get("timing_threshold_ms", 10):
                logger.debug(f"[TIMING] calcular_riego_completa (ERROR): {ms:.2f}ms")
        
        return {
            "balance_hidrico_neto": None,
            "estres_hidrico_cultivo": None,
            "disponibilidad_agua_cultivable": None,
            "eficiencia_infiltracion": None,
            "indice_riego_sintetico": 0.0,
        }
