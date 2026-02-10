"""
HIDROLOGÍA INDICES v2.0 - Balance Hídrico y Escorrentía

Índices para ingeniería hidráulica y agraria:
  1. Tasa de infiltración potencial (0-100)
  2. Riesgo de escorrentía (0-100)
  3. Índice estandarizado precipitación SPI (0-100)
  4. Estado de humedad del suelo tendencial (0-100)

Referencias:
  - Green-Ampt: Infiltración (Green & Ampt, 1911)
  - USDA: Capacidad de campo, conductividad saturada
  - WMO: Índice Estandarizado de Precipitación (SPI)
  - FAO: Balance hídrico agrario

Fecha: 10 de febrero de 2026
"""

from typing import Dict, Optional, List
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
# SUB-ÍNDICES ROBUSTOS DE HIDROLOGÍA
# ============================================================================

def tasa_infiltracion_potencial_robusto(
    lluvia_rate_mm_h: Optional[float],
    tipo_suelo: str = "franco",
    pendiente_terreno_pct: float = 5.0,
    historico: float = 60.0
) -> float:
    """
    Tasa de infiltración potencial (0-100).
    
    Green-Ampt simplificado: velocidad máxima agua penetra suelo.
    
    K_s (conductividad saturada) por tipo suelo:
    - Arenoso: 25 mm/h (drena muy rápido)
    - Franco: 6 mm/h (infiltración normal)
    - Arcilloso: 0.3 mm/h (casi no infiltra)
    
    Mapeo: K_s a 0-100 (0 mm/h = 0%, 25 mm/h = 100%)
    
    Reducción por pendiente: agua escurre, menos infiltra.
    
    Robusto: nunca None.
    """
    if lluvia_rate_mm_h is None:
        return _clamp(historico, 0, 100)
    
    # K_s por tipo suelo (mm/h)
    ks_map = {
        'arenoso': 25.0,
        'franco_arenoso': 10.0,
        'franco': 6.0,
        'franco_arcilloso': 2.0,
        'arcilla': 0.3
    }
    
    ks = ks_map.get(tipo_suelo, ks_map['franco'])
    
    # Factor reducción por pendiente
    # Pendiente 0% → factor=1.0, pendiente 20%+ → factor=0.3
    pendiente_factor = max(0.3, 1.0 - (pendiente_terreno_pct / 100.0) * 0.7)
    
    # Infiltración potencial reducida
    infiltr_pot = ks * pendiente_factor
    
    # Mapear a 0-100 (máximo 25 mm/h)
    score = (infiltr_pot / 25.0) * 100.0
    
    return _clamp(score, 0, 100)


def riesgo_escorrentia_robusto(
    lluvia_rate_mm_h: Optional[float],
    tipo_suelo: str = "franco",
    pendiente_terreno_pct: float = 5.0,
    historico: float = 30.0
) -> float:
    """
    Riesgo de escorrentía (0-100, donde 100 = máximo riesgo, toda agua escurre).
    
    Escorrentía = lluvia que NO infiltra.
    
    Escor = lluvia_rate - infiltración_potencial
    
    Riesgo alto (80-100): avenidas, inundación, erosión, contaminación difusa.
    
    Robusto: nunca None.
    """
    if lluvia_rate_mm_h is None:
        return _clamp(historico, 0, 100)
    
    luvia_rate = lluvia_rate_mm_h
    
    # Calcular infiltración potencial igual a función anterior
    ks_map = {
        'arenoso': 25.0,
        'franco_arenoso': 10.0,
        'franco': 6.0,
        'franco_arcilloso': 2.0,
        'arcilla': 0.3
    }
    
    ks = ks_map.get(tipo_suelo, ks_map['franco'])
    pendiente_factor = max(0.3, 1.0 - (pendiente_terreno_pct / 100.0) * 0.7)
    infiltr_pot = ks * pendiente_factor
    
    # Escorrentía
    escor = max(0.0, luvia_rate - infiltr_pot)
    
    # Mapear a 0-100 (máximo escorrentía ~25 mm/h si lluvia muy intensa)
    if escor >= 25:
        score = 100.0  # Escurre todo, inundación probable
    else:
        score = (escor / 25.0) * 100.0
    
    return _clamp(score, 0, 100)


def indice_spi_robusto(
    lluvia_actual_mm: Optional[float],
    lluvia_media_historica_mm: Optional[float],
    desviacion_estandar_mm: Optional[float],
    historico: float = 50.0
) -> float:
    """
    Índice Estandarizado de Precipitación (SPI) simplificado (0-100).
    
    SPI = (Precip - Media) / Desviación
    
    Interpretación:
    - SPI > 1.5: lluvia excesiva (> percentil 93) → inundación
    - SPI 0.5 a 1.5: normal
    - SPI -0.5 a 0.5: tendencia normal
    - SPI -1.5 a -0.5: sequía inicial
    - SPI < -1.5: sequía moderada-severa
    
    Mapeo a 0-100:
    - 0: sequía severa (SPI < -1.5)
    - 50: normal (SPI ≈ 0)
    - 100: lluvia excesiva (SPI > 1.5)
    
    Robusto: nunca None (sin histórico, asume normal).
    """
    if all(v is None for v in [lluvia_actual_mm, lluvia_media_historica_mm]):
        return _clamp(historico, 0, 100)
    
    lluvia_act = lluvia_actual_mm if lluvia_actual_mm is not None else 0.0
    media = lluvia_media_historica_mm if lluvia_media_historica_mm is not None else 5.0
    desv = desviacion_estandar_mm if desviacion_estandar_mm is not None else 2.0
    
    if desv == 0:
        # Sin variabilidad histórica, asumir normal
        return _clamp(50.0, 0, 100)
    
    # Calcular SPI
    spi = (lluvia_act - media) / desv
    
    # Mapear SPI a 0-100
    # SPI -3 a +3 → 0 a 100
    score = 50.0 + (spi / 3.0) * 50.0
    
    return _clamp(score, 0, 100)


def estado_humedad_suelo_tendencial_robusto(
    delta_h_acumulado_mm: Optional[float],
    historico: float = 50.0
) -> float:
    """
    Estado de humedad del suelo tendencial (0-100).
    
    Basado en acumulación de balance hídrico (ΔH) últimos 7-30 días.
    
    Mapeo:
    - -50mm acumulado (déficit severo): 0%
    - 0mm (equilibrio): 50%
    - +50mm (superávit, saturación): 100%
    
    Predictor de sequía/inundación a escala agraria.
    
    Robusto: nunca None.
    """
    if delta_h_acumulado_mm is None:
        return _clamp(historico, 0, 100)
    
    delta_h = delta_h_acumulado_mm
    
    # Mapear linealmente
    # -50 → 0%, 0 → 50%, +50 → 100%
    if delta_h <= -50:
        score = 0.0
    elif delta_h >= 50:
        score = 100.0
    else:
        # Interpolación lineal: (-50..50) → (0..100)
        score = 50.0 + (delta_h / 50.0) * 50.0
    
    return _clamp(score, 0, 100)


# ============================================================================
# ÍNDICE SINTÉTICO DE HIDROLOGÍA
# ============================================================================

def indice_hidrologia_sintetico(
    tasa_infiltracion: float,
    riesgo_escorrentia: float,
    spi: float,
    estado_humedad_tendencial: float
) -> float:
    """
    Índice sintético de HIDROLOGÍA (0-100).
    
    100 = condiciones hídricas ideales (infiltración buena, sin escorrentía extrema, humedad normal)
    0 = condiciones severas (avenida/sequía)
    
    Ponderación:
    - 30% tasa_infiltración (capacidad del suelo)
    - 25% riesgo_escorrentia (inverso: menor es mejor)
    - 25% SPI (estado de lluvia relativo)
    - 20% estado_humedad_tendencial (humedad del suelo)
    
    Ojo: riesgo_escorrentía se invierte.
    """
    score = (
        tasa_infiltracion * 0.30 +
        (100 - riesgo_escorrentia) * 0.25 +  # Invertir: bajo riesgo = bueno
        spi * 0.25 +
        estado_humedad_tendencial * 0.20
    )
    
    return _clamp(score, 0, 100)


# ============================================================================
# FUNCIONES CONVENIENCIA
# ============================================================================

def calcular_hidrologia_completa(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Calcula TODOS los índices de hidrología en un call.
    
    Input: dict con llaves:
        - lluvia_rate_mm_h (tasa lluvia actual)
        - lluvia_actual_mm (precipitación diaria)
        - tipo_suelo (arenoso/franco_arenoso/franco/franco_arcilloso/arcilla)
        - pendiente_terreno_pct
        - [opcional] lluvia_media_historica_mm, desviacion_estandar_mm
        - [opcional] delta_h_acumulado_mm (balance hídrico acumulado)
    
    Output: dict con:
        - tasa_infiltracion_potencial (0-100)
        - riesgo_escorrentia (0-100)
        - indice_spi (0-100)
        - estado_humedad_tendencial (0-100)
        - indice_hidrologia_sintetico (0-100) ← PRINCIPAL
    
    Estructura: igual a cetreria/lluvia/deporte/confort v2.0
    """
    _t_inicio = time.time() if LOGGING_CONFIG.get("log_timing_functions") else None
    
    try:
        # Extraer inputs
        lluvia_rate = data.get("lluvia_rate_mm_h")
        lluvia_actual = data.get("lluvia_actual_mm")
        tipo_suelo = data.get("tipo_suelo", "franco")
        pendiente = data.get("pendiente_terreno_pct", 5.0)
        lluvia_media = data.get("lluvia_media_historica_mm")
        desv = data.get("desviacion_estandar_mm")
        delta_h_acum = data.get("delta_h_acumulado_mm")
        
        # Calcular sub-índices
        infiltr = tasa_infiltracion_potencial_robusto(
            lluvia_rate_mm_h=lluvia_rate,
            tipo_suelo=tipo_suelo,
            pendiente_terreno_pct=pendiente
        )
        
        escor = riesgo_escorrentia_robusto(
            lluvia_rate_mm_h=lluvia_rate,
            tipo_suelo=tipo_suelo,
            pendiente_terreno_pct=pendiente
        )
        
        spi_val = indice_spi_robusto(
            lluvia_actual_mm=lluvia_actual,
            lluvia_media_historica_mm=lluvia_media,
            desviacion_estandar_mm=desv
        )
        
        humedad_tend = estado_humedad_suelo_tendencial_robusto(
            delta_h_acumulado_mm=delta_h_acum
        )
        
        # Sintético
        sintetico = indice_hidrologia_sintetico(
            tasa_infiltracion=infiltr,
            riesgo_escorrentia=escor,
            spi=spi_val,
            estado_humedad_tendencial=humedad_tend
        )
        
        resultado = {
            "tasa_infiltracion_potencial": round(infiltr, 1),
            "riesgo_escorrentia": round(escor, 1),
            "indice_spi": round(spi_val, 1),
            "estado_humedad_tendencial": round(humedad_tend, 1),
            "indice_hidrologia_sintetico": round(sintetico, 1),
        }
        
        # Log timing
        if _t_inicio and LOGGING_CONFIG.get("log_timing_functions"):
            ms = (time.time() - _t_inicio) * 1000
            if ms > LOGGING_CONFIG.get("timing_threshold_ms", 10):
                logger.debug(f"[TIMING] calcular_hidrologia_completa: {ms:.2f}ms")
        
        return resultado
    
    except Exception as e:
        logger.error(f"[ERROR] calcular_hidrologia_completa: {e}", exc_info=True)
        
        # Log timing en error
        if _t_inicio and LOGGING_CONFIG.get("log_timing_functions"):
            ms = (time.time() - _t_inicio) * 1000
            if ms > LOGGING_CONFIG.get("timing_threshold_ms", 10):
                logger.debug(f"[TIMING] calcular_hidrologia_completa (ERROR): {ms:.2f}ms")
        
        return {
            "tasa_infiltracion_potencial": None,
            "riesgo_escorrentia": None,
            "indice_spi": None,
            "estado_humedad_tendencial": None,
            "indice_hidrologia_sintetico": 50.0,
        }
