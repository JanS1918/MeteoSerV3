"""
ASTRONOMÍA INDICES v2.0 - Posicionamiento Solar y Lunar

Índices derivados del posicionamiento celeste:
  1. Horas de luz solar disponible (0-100)
  2. Disponibilidad para observación nocturna (0-100)
  3. Amplitud térmica tendencial del día (0-100)
  4. Índice de claridad (K_t) - transmitancia atmosférica (0-100)
  5. Visibilidad nocturna sin instrumentos (0-100)

Basados en:
  - AstronomiaRecursiva (NREL SPA + Ciddor, precisión ±2 arcmin)
  - REST2 Gueymard (radiación extraterrestre)
  - Fases lunares (Meeus)

Fecha: 10 de febrero de 2026
"""

from typing import Dict, Optional
import logging
import math
import time
from datetime import datetime, timedelta

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
# SUB-ÍNDICES ROBUSTOS DE ASTRONOMÍA
# ============================================================================

def horas_luz_robusto(
    elevacion_solar_actual: Optional[float],
    hora_salida_sol: Optional[float] = None,
    hora_puesta_sol: Optional[float] = None,
    historico: float = 50.0
) -> float:
    """
    Índice de horas de luz disponible (0-100).
    
    0% = noche total (0 horas luz)
    100% = máximo anual (~16 horas en verano, 8 en invierno)
    
    Mapeo: (horas_luz / 16) * 100
    
    Robusto: nunca None.
    """
    if all(v is None for v in [hora_salida_sol, hora_puesta_sol]):
        return _clamp(historico, 0, 100)
    
    # Calcular duración día
    if hora_salida_sol is not None and hora_puesta_sol is not None:
        duracion_horas = hora_puesta_sol - hora_salida_sol
    else:
        # Estimada de elevación solar (fallback)
        duracion_horas = 12.0  # Media anual
    
    # Mapear: máximo ~16h en verano
    max_horas = 16.0
    proporcion = min(duracion_horas / max_horas, 1.0)
    score = proporcion * 100.0
    
    return _clamp(score, 0, 100)


def disponibilidad_observacion_nocturna_robusto(
    fase_lunar_pct: Optional[float],
    elevacion_solar: Optional[float],
    hora_local: Optional[float] = None,
    historico: float = 40.0
) -> float:
    """
    Disponibilidad para observación astronómica nocturna (0-100).
    
    100% = noche completamente oscura (fase lunar 0%, elevación solar <-18°)
    0% = día o luna llena
    
    Factores:
    - Fase lunar: luna nueva (0%) mejor, luna llena (100%) peor
    - Elevación solar: debe ser <-18° (twilight astral)
    
    Robusto: nunca None.
    """
    if all(v is None for v in [fase_lunar_pct, elevacion_solar]):
        return _clamp(historico, 0, 100)
    
    fase = fase_lunar_pct if fase_lunar_pct is not None else 50.0
    elev = elevacion_solar if elevacion_solar is not None else 45.0
    
    # Penalización por luna iluminada
    penalizacion_luna = fase / 100.0  # 0 (nueva) a 1 (llena)
    
    # Factorización por elevación solar
    if elev > 0:
        # Día → 0%
        factor_oscuridad = 0.0
    elif elev > -6:
        # Twilight civil → 20%
        factor_oscuridad = 0.2
    elif elev > -12:
        # Twilight náutico → 50%
        factor_oscuridad = 0.5
    elif elev > -18:
        # Twilight astral → 70%
        factor_oscuridad = 0.7
    else:
        # Noche completa → 100%
        factor_oscuridad = 1.0
    
    # Combinar: (oscuridad base) × (1 - penalización luna)
    score = factor_oscuridad * (1.0 - penalizacion_luna * 0.8) * 100.0
    
    return _clamp(score, 0, 100)


def amplitud_termica_tendencial_robusto(
    radiacion_extr_teorica_w_m2: Optional[float],
    radiacion_global_medida_w_m2: Optional[float],
    historico: float = 50.0
) -> float:
    """
    Amplitud térmica del día tendencial (0-100).
    
    Estima cuan "violento" será el ciclo de temperatura diurno.
    
    Basado en K_t (claridad del cielo) y radiación disponible.
    
    100% = máxima radiación posible (día despejado, máxima amplitud)
    0% = sin radiación (noche, sin amplitud)
    
    Robusto: nunca None.
    """
    if all(v is None for v in [radiacion_extr_teorica_w_m2, radiacion_global_medida_w_m2]):
        return _clamp(historico, 0, 100)
    
    rad_extr = radiacion_extr_teorica_w_m2 if radiacion_extr_teorica_w_m2 is not None else 1000.0
    rad_global = radiacion_global_medida_w_m2 if radiacion_global_medida_w_m2 is not None else 500.0
    
    # K_t = claridad
    kt = (rad_global / rad_extr) if rad_extr > 0 else 0.5
    
    # Score directamente proporcional a K_t
    # K_t > 0.85 = imposible (ruido)
    # K_t 0.75-0.85 = despejado ideal
    # K_t < 0.40 = muy nublado
    
    if kt > 0.85:
        # Probablemente ruido en sensor
        score = 85.0
    elif kt > 0.75:
        # Despejado ideal → amplitud alta
        score = kt * 100.0
    else:
        score = max(20.0, kt * 100.0)  # Mínimo 20% aunque esté nublado
    
    return _clamp(score, 0, 100)


def indice_claridad_kt_robusto(
    radiacion_extr_teorica_w_m2: Optional[float],
    radiacion_global_medida_w_m2: Optional[float],
    historico: float = 0.6
) -> float:
    """
    Índice de claridad K_t (0-100, mapeo de 0.0-1.0).
    
    K_t = Radiación global / Radiación extraterrestre
    
    0-50: Nublado, partículas (K_t < 0.5)
    51-75: Parcialmente nublado (0.5 < K_t < 0.75)
    76-85: Despejado ideal (0.75 < K_t < 0.85, mejor para solar)
    86-100: Imposible o error sensor (K_t > 0.85)
    
    Robusto: nunca None.
    """
    if all(v is None for v in [radiacion_extr_teorica_w_m2, radiacion_global_medida_w_m2]):
        return _clamp(historico * 100.0, 0, 100)
    
    rad_extr = radiacion_extr_teorica_w_m2 if radiacion_extr_teorica_w_m2 is not None else 1000.0
    rad_global = radiacion_global_medida_w_m2 if radiacion_global_medida_w_m2 is not None else 500.0
    
    kt = (rad_global / rad_extr) if rad_extr > 0 else 0.5
    
    # Clamp entre 0 y 1, mapear a 0-100
    kt_clamped = _clamp(kt, 0.0, 1.0)
    score = kt_clamped * 100.0
    
    return _clamp(score, 0, 100)


def visibilidad_nocturna_sin_instrumentos_robusto(
    elevacion_solar: Optional[float],
    humedad_relativa: Optional[float],
    radiacion_global: Optional[float] = 0.0,
    indice_claridad_kt: Optional[float] = None,
    historico: float = 30.0
) -> float:
    """
    Visibilidad de estrellas sin telescopio (0-100).
    
    Estimaciones simplificadas sin sensor de luz ambiente o aerosoles.
    
    Factores:
    - Elevación solar < -18° (twilight astral completo)
    - Humedad baja (<70%, menos nubosidad)
    - K_t alto (0.75+, menos partículas de día)
    
    100% = noche oscura, HR baja, buena visibilidad estelar
    0% = día, HR alta, contaminación
    
    Robusto: nunca None.
    """
    if all(v is None for v in [elevacion_solar, humedad_relativa]):
        return _clamp(historico, 0, 100)
    
    elev = elevacion_solar if elevacion_solar is not None else 45.0
    humedad = humedad_relativa if humedad_relativa is not None else 60.0
    
    # Factor oscuridad (elevación solar)
    if elev > 0:
        factor_osc = 0.0
    elif elev > -18:
        factor_osc = max(0.0, ((-elev) - 0) / 18.0) * 0.7  # Hasta -18°
    else:
        factor_osc = 1.0  # Completa oscuridad
    
    # Factor humedad (transparencia)
    if humedad < 50:
        factor_hum = 1.0  # Aire seco → buena visibilidad
    elif humedad < 70:
        factor_hum = 0.8
    elif humedad < 80:
        factor_hum = 0.5
    else:
        factor_hum = 0.1  # Muy húmedo → mala visibilidad
    
    # Combinar
    score = factor_osc * factor_hum * 100.0
    
    return _clamp(score, 0, 100)


# ============================================================================
# ÍNDICE SINTÉTICO DE ASTRONOMÍA
# ============================================================================

def indice_astronomia_sintetico(
    horas_luz: float,
    obs_nocturna: float,
    amplitud_termica: float,
    claridad_kt: float,
    visibilidad_noche: float,
    lluvia_1h: Optional[float] = None,
    probabilidad_lluvia_sundqvist: Optional[float] = None,
    visibilidad_km: Optional[float] = None
) -> float:
    """
    Índice sintético de ASTRONOMÍA (0-100) - SUMA PONDERADA DE 5 COMPONENTES + CONTEXTOS.
    
    PESOS EXPLÍCITOS:
    - horas_luz: 15% - Duración del día (energía solar disponible)
    - obs_nocturna: 25% - Oscuridad + fase lunar para observación estelar
    - amplitud_termica: 20% - Variación térmica día-noche (calidad óptica)
    - claridad_kt: 25% - Transparencia atmosférica (radiación clara)
    - visibilidad_noche: 15% - Ausencia de contaminación lumínica/nubosidad nocturna
    
    CONTEXTOS GLOBALES:
    - lluvia_1h: Lluvia actual penaliza FUERTE (lluvia destroza observación)
    - probabilidad_lluvia_sundqvist: Lluvia predicha penaliza MODERADO (precaución)
    - visibilidad_km: Polvo/niebla reduce claridad óptica
    
    Lógica: lluvia actual es un CANCELA (factor ~0), lluvia predicha es precaución (50%).
    """
    if lluvia_1h is None:
        lluvia_1h = 0.0
    if probabilidad_lluvia_sundqvist is None:
        probabilidad_lluvia_sundqvist = 0.0
    if visibilidad_km is None:
        visibilidad_km = 10.0
    
    # SUMA PONDERADA base de los 5 componentes
    score_base = (
        horas_luz * 0.15 +              # horas_luz: 15%
        obs_nocturna * 0.25 +           # obs_nocturna: 25%
        amplitud_termica * 0.20 +       # amplitud: 20%
        claridad_kt * 0.25 +            # claridad_kt: 25%
        visibilidad_noche * 0.15        # visibilidad_noche: 15%
    )
    
    # ESCENARIO 1: LLUVIA ACTUAL (lluvia_1h > 0.5 mm)
    if lluvia_1h > 0.5:
        logger.debug(f"LLUVIA EN PROGRESO ({lluvia_1h:.2f}mm): Astronomía CRÍTICA")
        
        # Lluvia destruye observación (nubes ocultan todo)
        penalizacion_lluvia = 1.0 - ((lluvia_1h / 50.0) ** 0.9)
        
        # Penalizar TODOS los componentes
        horas_lloviendo = _clamp(horas_luz * (1.0 - (lluvia_1h / 20.0)))
        obs_noc_lluvia = _clamp(obs_nocturna * max(0.1, 1.0 - (lluvia_1h / 5.0)))
        ampl_lluvia = _clamp(amplitud_termica * (1.0 - (lluvia_1h / 30.0)))
        kt_lluvia = _clamp(claridad_kt * (1.0 - (lluvia_1h / 4.0)))  # K_t muito afectado
        visib_noc_lluvia = _clamp(visibilidad_noche * max(0.05, 1.0 - (lluvia_1h / 3.0)))
        
        score_lluvia = (
            horas_lloviendo * 0.15 +
            obs_noc_lluvia * 0.25 +
            ampl_lluvia * 0.20 +
            kt_lluvia * 0.25 +
            visib_noc_lluvia * 0.15
        )
        
        # OVERRIDE: Lluvia actual es prácticamente un cancela
        score_final = score_lluvia * penalizacion_lluvia
        
        logger.debug(
            f"Astronomía con lluvia: base={score_base:.1f}, con lluvia={score_final:.1f}"
        )
        
        return _clamp(score_final)
    
    # ESCENARIO 2: LLUVIA PREDICHA (sundqvist > 70%)
    elif probabilidad_lluvia_sundqvist > 70.0:
        logger.debug(f"LLUVIA PREDICHA ({probabilidad_lluvia_sundqvist:.0f}%): Astronomía INCIERTA")
        
        # Lluvia predicha reduce confianza, pero no cancela
        penalizacion = 1.0 - ((probabilidad_lluvia_sundqvist - 70.0) / 30.0) * 0.5  # Max -50%
        score_final = score_base * penalizacion
        
        logger.debug(
            f"Astronomía con lluvia predicha: {score_base:.1f} → {score_final:.1f}"
        )
        
        return _clamp(score_final)
    
    # ESCENARIO 3: VISIBILIDAD REDUCIDA (polvo, niebla)
    elif visibilidad_km < 5.0:
        logger.debug(f"VISIBILIDAD BAJA ({visibilidad_km:.1f}km): Astronomía COMPROMETIDA")
        
        # Baja visibilidad = polvo/niebla = mala calidad óptica
        factor_visib = visibilidad_km / 10.0  # 0.0-1.0
        penalizacion = 1.0 - (1.0 - factor_visib) * 0.3  # Max -30%
        
        score_final = score_base * penalizacion
        
        logger.debug(
            f"Astronomía con visibilidad reducida: {score_base:.1f} → {score_final:.1f}"
        )
        
        return _clamp(score_final)
    
    # ESCENARIO 4: CONDICIONES NORMALES
    else:
        logger.debug(
            f"Astronomía sin lluvia: {score_base:.1f}%"
        )
        return _clamp(score_base)


# ============================================================================
# FUNCIONES CONVENIENCIA
# ============================================================================

def calcular_astronomia_completa(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Calcula TODOS los índices de astronomía en un call.
    
    Input: dict con llaves:
        - elevacion_solar (grados)
        - radiacion_w_m2 (radiación global medida)
        - radiacion_extr_w_m2 (radiación extraterrestre teórica)
        - humedad (%)
        - fase_lunar_pct (0-100)
        - [opcional] hora_salida_sol, hora_puesta_sol (horas)
    
    Output: dict con:
        - horas_luz (0-100)
        - disponibilidad_obs_nocturna (0-100)
        - amplitud_termica_tendencial (0-100)
        - indice_claridad_kt (0-100)
        - visibilidad_nocturna (0-100)
        - indice_astronomia_sintetico (0-100) ← PRINCIPAL
        + fase_lunar_pct, elevacion_solar (passthrough)
    
    Estructura: igual a cetreria/lluvia/deporte/confort v2.0
    """
    _t_inicio = time.time() if LOGGING_CONFIG.get("log_timing_functions") else None
    
    try:
        # Extraer inputs
        elev_solar = data.get("elevacion_solar")
        rad_global = data.get("radiacion_w_m2")
        rad_extr = data.get("radiacion_extr_w_m2")
        humedad = data.get("humedad")
        fase_lunar = data.get("fase_lunar_pct")
        hora_salida = data.get("hora_salida_sol")
        hora_puesta = data.get("hora_puesta_sol")
        
        # Calcular sub-índices
        horas_luz = horas_luz_robusto(
            elevacion_solar_actual=elev_solar,
            hora_salida_sol=hora_salida,
            hora_puesta_sol=hora_puesta
        )
        
        obs_noc = disponibilidad_observacion_nocturna_robusto(
            fase_lunar_pct=fase_lunar,
            elevacion_solar=elev_solar
        )
        
        amplitud = amplitud_termica_tendencial_robusto(
            radiacion_extr_teorica_w_m2=rad_extr,
            radiacion_global_medida_w_m2=rad_global
        )
        
        kt = indice_claridad_kt_robusto(
            radiacion_extr_teorica_w_m2=rad_extr,
            radiacion_global_medida_w_m2=rad_global
        )
        
        visib_noc = visibilidad_nocturna_sin_instrumentos_robusto(
            elevacion_solar=elev_solar,
            humedad_relativa=humedad,
            radiacion_global=rad_global,
            indice_claridad_kt=kt
        )
        
        # Sintético CON CONTEXTOS GLOBALES
        sintetico = indice_astronomia_sintetico(
            horas_luz=horas_luz,
            obs_nocturna=obs_noc,
            amplitud_termica=amplitud,
            claridad_kt=kt,
            visibilidad_noche=visib_noc,
            lluvia_1h=data.get("lluvia_1h"),
            probabilidad_lluvia_sundqvist=data.get("probabilidad_lluvia_sundqvist"),
            visibilidad_km=data.get("visibilidad_km")
        )
        
        resultado = {
            "horas_luz": round(horas_luz, 1),
            "disponibilidad_obs_nocturna": round(obs_noc, 1),
            "amplitud_termica_tendencial": round(amplitud, 1),
            "indice_claridad_kt": round(kt, 1),
            "visibilidad_nocturna": round(visib_noc, 1),
            "indice_astronomia_sintetico": round(sintetico, 1),
            "fase_lunar_pct": round(fase_lunar, 1) if fase_lunar is not None else None,
            "elevacion_solar_deg": round(elev_solar, 2) if elev_solar is not None else None,
        }
        
        # Log timing
        if _t_inicio and LOGGING_CONFIG.get("log_timing_functions"):
            ms = (time.time() - _t_inicio) * 1000
            if ms > LOGGING_CONFIG.get("timing_threshold_ms", 10):
                logger.debug(f"[TIMING] calcular_astronomia_completa: {ms:.2f}ms")
        
        return resultado
    
    except Exception as e:
        logger.error(f"[ERROR] calcular_astronomia_completa: {e}", exc_info=True)
        
        # Log timing en error
        if _t_inicio and LOGGING_CONFIG.get("log_timing_functions"):
            ms = (time.time() - _t_inicio) * 1000
            if ms > LOGGING_CONFIG.get("timing_threshold_ms", 10):
                logger.debug(f"[TIMING] calcular_astronomia_completa (ERROR): {ms:.2f}ms")
        
        return {
            "horas_luz": None,
            "disponibilidad_obs_nocturna": None,
            "amplitud_termica_tendencial": None,
            "indice_claridad_kt": None,
            "visibilidad_nocturna": None,
            "indice_astronomia_sintetico": 0.0,
        }
