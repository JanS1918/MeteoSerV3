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

def calcular_derivada_regresion_lineal(
    historial: list,
    factor_tiempo: float = 1.0,
    min_puntos: int = 2
) -> float:
    """
    Regresión lineal para calcular derivadas (dGHI/dt, dP/dt, dHR/dt, etc)
    
    Retorna: dx/dt en unidades por unidad_tiempo
    """
    if not historial or len(historial) < min_puntos:
        return 0.0
    
    try:
        # historial puede ser list de dicts o list de floats
        valores = []
        tiempos = []
        
        for i, item in enumerate(historial):
            if isinstance(item, dict):
                valores.append(float(item.get("valor", 0)))
                tiempos.append(i)
            else:
                valores.append(float(item))
                tiempos.append(i)
        
        if len(valores) < min_puntos:
            return 0.0
        
        # Regresión mínimos cuadrados
        n = len(valores)
        t_mean = sum(tiempos) / n
        v_mean = sum(valores) / n
        
        numerador = sum((tiempos[i] - t_mean) * (valores[i] - v_mean) for i in range(n))
        denominador = sum((tiempos[i] - t_mean) ** 2 for i in range(n))
        
        if denominador == 0:
            return 0.0
        
        pendiente = numerador / denominador
        return pendiente * factor_tiempo
    except Exception as e:
        logger.warning(f"Error en regresión lineal: {e}")
        return 0.0


def derivada_ghi_w_m2_s(ghi_historial: list) -> float:
    """Derivada radiación GHI (W/m²/min)"""
    return calcular_derivada_regresion_lineal(ghi_historial, factor_tiempo=60.0)


def derivada_presion_hpa_min(presion_historial: list) -> float:
    """Derivada presión (hPa/min)"""
    return calcular_derivada_regresion_lineal(presion_historial, factor_tiempo=60.0)


def derivada_humedad_pct_min(humedad_historial: list) -> float:
    """Derivada humedad relativa (%/min)"""
    return calcular_derivada_regresion_lineal(humedad_historial, factor_tiempo=60.0)


def indice_lluvia_sintetico(
    # 4 componentes antiguos
    riesgo_inundacion: float,
    visibilidad_carretera: float,
    adherencia_terreno: float,
    probabilidad_rayos: float,
    # 5 componentes nuevos (derivadas)
    derivada_ghi: float = 0.0,
    derivada_presion: float = 0.0,
    derivada_humedad: float = 0.0,
    dt_solar: float = 0.0,
    prob_lluvia_sundqvist: float = 0.0,
    lluvia_1h: Optional[float] = None
) -> float:
    """
    Índice sintético lluvia = suma ponderada de 9 sub-índices.
    
    COMPONENTES ANTIGUOS (4):
    - riesgo_inundacion: 15% - lluvia acumulada + presión
    - visibilidad_carretera: 12% - PM2.5 + humedad + lluvia
    - adherencia_terreno: 10% - sequedad/humedad suelo
    - probabilidad_rayos: 13% - inestabilidad CAPE
    
    COMPONENTES NUEVOS (5):
    - derivada_ghi: 20% - oscurecimiento rápido (clearing/nube)
    - derivada_presion: 18% - caída presión (frentes)
    - derivada_humedad: 8% - aumento rápido HR (saturación)
    - dt_solar: 2% - colapso diferencial temperatura
    - prob_lluvia_sundqvist: 2% - probabilidad absoluta
    
    Total: 100% con máxima precisión de combined indicators
    """
    if lluvia_1h is None:
        lluvia_1h = 0.0
    
    # Normalizar derivadas a escala 0-100
    # (valores absolutos necesarios para que tenga sentido el scoring)
    ghi_score = _clamp(abs(derivada_ghi) / 200.0 * 100.0)  # >200 W/m²/min = 100
    presion_score = _clamp(abs(derivada_presion) / 3.0 * 100.0)  # >3 hPa/min = 100
    humedad_score = _clamp(abs(derivada_humedad) / 5.0 * 100.0)  # >5 %/min = 100
    dt_score = _clamp((2.0 - dt_solar) / 2.0 * 100.0) if dt_solar is not None else 0.0  # <0.5°C = 100
    
    # Ajustar componentes antiguos si hay lluvia activa
    if lluvia_1h > 0.1:
        vis_penalizacion = _clamp(1.0 - (lluvia_1h / 10.0))
        visib_ajustada = visibilidad_carretera * vis_penalizacion
        adher_penalizacion = _clamp(1.0 - (lluvia_1h / 5.0))
        adher_ajustada = adherencia_terreno * adher_penalizacion
        riesgo_lluvia_extra = _clamp((lluvia_1h / 50.0) ** 1.5 * 40.0)
        riesgo_ajustado = _clamp(riesgo_inundacion + riesgo_lluvia_extra, 0, 100)
        rayos_penalizacion = _clamp(1.0 + (lluvia_1h / 20.0))
        rayos_ajustados = _clamp(probabilidad_rayos * rayos_penalizacion, 0, 100)
    else:
        visib_ajustada = visibilidad_carretera
        adher_ajustada = adherencia_terreno
        riesgo_ajustado = riesgo_inundacion
        rayos_ajustados = probabilidad_rayos
    
    # SUMA PONDERADA DE TODOS LOS 9 ÍNDICES
    indice_lluvia = _clamp(
        0.15 * (100 - riesgo_ajustado) +      # riesgo inundación (invertido)
        0.12 * visib_ajustada +                # visibilidad
        0.10 * adher_ajustada +                # adherencia
        0.13 * (100 - rayos_ajustados) +      # rayos (invertido)
        0.20 * ghi_score +                     # derivada GHI (NUEVO)
        0.18 * presion_score +                 # derivada presión (NUEVO)
        0.08 * humedad_score +                 # derivada humedad (NUEVO)
        0.02 * dt_score +                      # dt solar (NUEVO)
        0.02 * (prob_lluvia_sundqvist * 1.0)   # sundqvist (NUEVO)
    , 0, 100)
    
    return indice_lluvia



def calcular_lluvia_completa(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Calcula TODOS los índices de lluvia: 4 antiguos + 5 nuevos + 1 sintético.
    
    COMPONENTES ANTIGUOS (4):
    - riesgo_inundacion: lluvia acumulada + presión
    - visibilidad_carretera: PM2.5 + humedad + lluvia
    - adherencia_terreno: sequedad suelo
    - probabilidad_rayos: inestabilidad convectiva
    
    COMPONENTES NUEVOS (5):
    - derivada_ghi: cambio radiación luminosa
    - derivada_presion: caída presión barométrica
    - derivada_humedad: aumento HR
    - dt_solar: colapso diferencial temperatura
    - prob_lluvia_sundqvist: probabilidad microfísica
    
    SINTÉTICO: suma ponderada de todos (100%)
    """
    
    # Datos básicos
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
    
    # ========== COMPONENTES ANTIGUOS (4) ==========
    riesgo_inund = riesgo_inundacion_robusto(lluvia_24h, lluvia_72h, presion)
    visib_carr = visibilidad_carretera_robusto(lluvia_1h, nubosidad, humedad)
    adher_terr = adherencia_terreno_robusto(lluvia_24h, lluvia_1h, viento, temp, dew)
    prob_rayos = probabilidad_rayos_robusto(presion, temp, humedad)
    
    # ========== COMPONENTES NUEVOS (5) ==========
    # Obtener históricos si existen
    ghi_historial = data.get("ghi_historial", [])
    presion_historial = data.get("presion_historial", [])
    humedad_historial = data.get("humedad_historial", [])
    dt_solar = data.get("dt_solar", None)  # Temperatura diferencial Sun-Shade
    
    # Calcular derivadas
    deriv_ghi = derivada_ghi_w_m2_s(ghi_historial)
    deriv_presion = derivada_presion_hpa_min(presion_historial)
    deriv_humedad = derivada_humedad_pct_min(humedad_historial)
    
    # Probabilidad lluvia Sundqvist (usa motor prediction si existe)
    prob_lluvia_sundq = 0.0
    try:
        from core.prediction.prediction_engine import obtener_motor_prediccion
        predictor = obtener_motor_prediccion()
        pred = predictor.predecir()
        prob_lluvia_val = pred.get("prob_lluvia", {})
        if isinstance(prob_lluvia_val, dict):
            prob_lluvia_sundq = float(prob_lluvia_val.get("valor", 0.0))
        else:
            prob_lluvia_sundq = float(prob_lluvia_val) if prob_lluvia_val else 0.0
    except Exception as e:
        logger.debug(f"Sundqvist no disponible: {e}")
        prob_lluvia_sundq = prob_rayos  # Fallback a rayos como proxy
    
    # ========== ÍNDICE SINTÉTICO (suma ponderada de 9) ==========
    indice_sint = indice_lluvia_sintetico(
        # Antiguos
        riesgo_inund,
        visib_carr,
        adher_terr,
        prob_rayos,
        # Nuevos
        deriv_ghi,
        deriv_presion,
        deriv_humedad,
        dt_solar if dt_solar is not None else 2.0,
        prob_lluvia_sundq,
        lluvia_1h=lluvia_1h
    )
    
    # RETORNAR: 4 antiguos + 5 nuevos + 1 sintético + compatible
    return {
        # Antiguos
        "riesgo_inundacion": riesgo_inund,
        "visibilidad_carretera": visib_carr,
        "adherencia_terreno": adher_terr,
        "probabilidad_rayos": prob_rayos,
        # Nuevos
        "derivada_ghi_w_m2_min": deriv_ghi,
        "derivada_presion_hpa_min": deriv_presion,
        "derivada_humedad_pct_min": deriv_humedad,
        "dt_solar_grados": dt_solar if dt_solar is not None else 0.0,
        "probabilidad_lluvia_sundqvist": prob_lluvia_sundq,
        # Sintético
        "indice_lluvia_sintetico": indice_sint,
        "indice_lluvia": indice_sint  # Compatibilidad
    }
