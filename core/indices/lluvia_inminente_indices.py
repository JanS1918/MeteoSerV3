"""
ÍNDICES DE LLUVIA INMINENTE - V51
==================================
Predicción de lluvia en corto plazo (10-20 minutos)
Basado en análisis de derivadas + microfísica + termodinámica

ARQUITECTURA:
1. Capa de Cálculos: funciones individuales de derivadas
2. Capa de Índices: índice compuesto de lluvia inminente
3. Capa de Bus: publicación ENTERA + DESCOMPUESTA

VALIDACIÓN CIENTÍFICA:
- dGHI/dt: Cambridge Radiative Transfer
- dHR/dt: Clausius-Clapeyron
- dP/dt: Hydrostatic Balance
- Sundqvist: Thompson Microphysics
"""

import logging
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
# LAYER 1: Cálculos de Derivadas
# ═════════════════════════════════════════════════════════════════════════════

def calcular_derivada_regresion_lineal(
    historial: deque,
    factor_tiempo: float = 1.0,
    min_puntos: int = 2
) -> float:
    """
    Calcula derivada usando regresión lineal simple
    
    Método: Minimización de mínimos cuadrados
    Fórmula: b = Σ[(t - t̄)(x - x̄)] / Σ[(t - t̄)²]
    
    Args:
        historial: deque([(timestamp, valor), ...])
        factor_tiempo: 1.0 para /s, 60.0 para /min
        min_puntos: Puntos mínimos requeridos
    
    Returns:
        Derivada dx/dt en unidades por unidad_tiempo
    """
    if len(historial) < min_puntos:
        return 0.0
    
    try:
        datos = list(historial)
        t_inicio = datos[0][0]
        
        # Convertir tiempos a segundos desde t0
        tiempos = np.array([(d[0] - t_inicio).total_seconds() for d in datos])
        valores = np.array([d[1] for d in datos])
        
        # Validar
        if len(tiempos) < 2 or np.max(tiempos) == np.min(tiempos):
            return 0.0
        
        # Regresión lineal: y = a + b*t
        n = len(tiempos)
        t_mean = np.mean(tiempos)
        v_mean = np.mean(valores)
        
        numerador = np.sum((tiempos - t_mean) * (valores - v_mean))
        denominador = np.sum((tiempos - t_mean) ** 2)
        
        if abs(denominador) < 1e-6:
            return 0.0
        
        pendiente_seg = numerador / denominador
        return pendiente_seg * factor_tiempo
    
    except Exception as e:
        logger.debug(f"[DERIVADAS] Error: {e}")
        return 0.0


def calcular_derivada_ghi_w_m2_s(
    historial_ghi: deque,
    ventana_min: int = 5
) -> Dict:
    """
    Calcula derivada de radiación global horizontal
    
    Interpretación:
        dGHI/dt > +50 W/m²/s: Clearing rápido (nubes alejándose)
        dGHI/dt < -50 W/m²/s: Ocultamiento rápido (nube pasando)
        |dGHI/dt| < ±10: Estable (sin cambios nubosos)
    
    Args:
        historial_ghi: deque([(timestamp, ghi_w_m2), ...])
        ventana_min: Ventana de análisis en minutos
    
    Returns:
        Dict con:
            - derivada: valor en W/m²/s
            - clasificacion: 'estable', 'clearing', 'nube'
            - severidad: 'baja', 'media', 'alta'
    """
    derivada = calcular_derivada_regresion_lineal(historial_ghi)
    
    if abs(derivada) < 10:
        clasif = "estable"
        sever = "baja"
    elif derivada > 50:
        clasif = "clearing"
        sever = "media" if derivada < 100 else "alta"
    elif derivada < -50:
        clasif = "nube"
        sever = "media" if abs(derivada) < 100 else "alta"
    else:
        clasif = "cambio_leve"
        sever = "baja"
    
    return {
        "derivada_w_m2_s": float(derivada),
        "clasificacion": clasif,
        "severidad": sever,
        "umbral_nube": abs(derivada) > 50
    }


def calcular_derivada_humedad_pct_min(
    historial_hr: deque
) -> Dict:
    """
    Calcula derivada de humedad relativa
    
    Interpretación:
        dHR/dt > +2 %/min: Aumento rápido (lluvia inminente)
        dHR/dt < -1 %/min: Secado rápido
        |dHR/dt| < 0.5: Estable
    
    Returns:
        Dict con derivada y clasificación
    """
    derivada = calcular_derivada_regresion_lineal(historial_hr, factor_tiempo=60.0)
    
    if derivada > 2:
        clasif = "aumento_rapido"
        sever = "alta"
    elif derivada > 0.5:
        clasif = "aumento_leve"
        sever = "media"
    elif abs(derivada) <= 0.5:
        clasif = "estable"
        sever = "baja"
    elif derivada < -1:
        clasif = "secado_rapido"
        sever = "alta"
    else:
        clasif = "secado_leve"
        sever = "media"
    
    return {
        "derivada_pct_min": float(derivada),
        "clasificacion": clasif,
        "severidad": sever,
        "umbral_lluvia": derivada > 2
    }


def calcular_derivada_presion_hpa_min(
    historial_presion: deque
) -> Dict:
    """
    Calcula derivada de presión barométrica
    
    Interpretación:
        dP/dt < -3 hPa/h: Sistema frontal pasando (tormenta inminente)
        dP/dt < -1 hPa/h: Cambio significativo
        dP/dt > +2 hPa/h: Mejora de presión
    
    Returns:
        Dict con derivada y clasificación
    """
    derivada = calcular_derivada_regresion_lineal(historial_presion, factor_tiempo=60.0)
    
    if derivada < -3:
        clasif = "caida_severa"
        sever = "alta"
    elif derivada < -1:
        clasif = "caida_moderada"
        sever = "media"
    elif abs(derivada) <= 0.5:
        clasif = "estable"
        sever = "baja"
    elif derivada > 2:
        clasif = "aumento_presion"
        sever = "baja"
    else:
        clasif = "cambio_leve"
        sever = "baja"
    
    return {
        "derivada_hpa_min": float(derivada),
        "clasificacion": clasif,
        "severidad": sever,
        "umbral_sistema": derivada < -1
    }


# ═════════════════════════════════════════════════════════════════════════════
# LAYER 2: Índice Compuesto de Lluvia Inminente
# ═════════════════════════════════════════════════════════════════════════════

def calcular_indice_lluvia_inminente_v51(
    ghi_w_m2: float,
    humedad_pct: float,
    presion_hpa: float,
    temp_c: float,
    dt_solar: float,
    historial_ghi: Optional[deque] = None,
    historial_hr: Optional[deque] = None,
    historial_presion: Optional[deque] = None,
    prob_sundqvist_pct: float = 0.0
) -> Dict:
    """
    Calcula índice compuesto de lluvia inminente (0-100)
    
    ARQUITECTURA:
    1. Evalúa 5 componentes independientes
    2. Pondera cada uno
    3. Calcula score final
    4. Estima ETA
    5. Determina confianza
    
    COMPONENTES:
    - GHI (radiación drop): 25%
    - Presión (caída barométrica): 25%
    - Humedad (aumento rápido): 15%
    - ΔT solar (colapso): 10%
    - Sundqvist (microfísica): 25%
    
    Args:
        ghi_w_m2: Radiación actual
        humedad_pct: Humedad actual
        presion_hpa: Presión actual
        temp_c: Temperatura
        dt_solar: Diferencia sol/sombra
        historial_*: deque con histórico (opcional)
        prob_sundqvist_pct: Probabilidad Sundqvist si disponible
    
    Returns:
        Dict completo con score, ETA, componentes descompuestos
    """
    # ───────────────────────────────────────────────────────────────────────
    # Calcular componentes de derivadas
    # ───────────────────────────────────────────────────────────────────────
    
    comp_ghi = calcular_derivada_ghi_w_m2_s(historial_ghi) if historial_ghi else {
        "derivada_w_m2_s": 0.0,
        "clasificacion": "no_disponible",
        "severidad": "baja",
        "umbral_nube": False
    }
    
    comp_hr = calcular_derivada_humedad_pct_min(historial_hr) if historial_hr else {
        "derivada_pct_min": 0.0,
        "clasificacion": "no_disponible",
        "severidad": "baja",
        "umbral_lluvia": False
    }
    
    comp_presion = calcular_derivada_presion_hpa_min(historial_presion) if historial_presion else {
        "derivada_hpa_min": 0.0,
        "clasificacion": "no_disponible",
        "severidad": "baja",
        "umbral_sistema": False
    }
    
    # ───────────────────────────────────────────────────────────────────────
    # Scoring de cada componente (0-100)
    # ───────────────────────────────────────────────────────────────────────
    
    # Score GHI: caída radiativa
    deriv_ghi = comp_ghi["derivada_w_m2_s"]
    if deriv_ghi < -200:
        score_ghi = 100
    elif deriv_ghi < -100:
        score_ghi = 80
    elif deriv_ghi < -50:
        score_ghi = 50
    elif deriv_ghi < -20:
        score_ghi = 20
    else:
        score_ghi = 0
    
    # Score Presión: caída barométrica
    deriv_p = comp_presion["derivada_hpa_min"]
    if deriv_p < -5:
        score_presion = 100
    elif deriv_p < -3:
        score_presion = 80
    elif deriv_p < -1:
        score_presion = 50
    elif deriv_p < -0.5:
        score_presion = 20
    else:
        score_presion = 0
    
    # Score Humedad: aumento rápido
    deriv_hr = comp_hr["derivada_pct_min"]
    if deriv_hr > 5:
        score_hr = 100
    elif deriv_hr > 3:
        score_hr = 70
    elif deriv_hr > 2:
        score_hr = 50
    elif deriv_hr > 1:
        score_hr = 20
    else:
        score_hr = 0
    
    # Score ΔT solar: colapso de diferencial
    if dt_solar < 0.5:
        score_dt_solar = 100
    elif dt_solar < 1:
        score_dt_solar = 50
    elif dt_solar < 2:
        score_dt_solar = 20
    else:
        score_dt_solar = 0
    
    # Score Sundqvist: probabilidad microfísica
    score_sundqvist = min(100.0, max(0.0, prob_sundqvist_pct))
    
    # ───────────────────────────────────────────────────────────────────────
    # Score Compuesto (ponderado)
    # ───────────────────────────────────────────────────────────────────────
    
    pesos = {
        "ghi": 0.25,
        "presion": 0.25,
        "hr": 0.15,
        "dt_solar": 0.10,
        "sundqvist": 0.25
    }
    
    score_final = (
        pesos["ghi"] * score_ghi +
        pesos["presion"] * score_presion +
        pesos["hr"] * score_hr +
        pesos["dt_solar"] * score_dt_solar +
        pesos["sundqvist"] * score_sundqvist
    )
    
    score_final = min(100.0, max(0.0, float(score_final)))
    
    # ───────────────────────────────────────────────────────────────────────
    # Estimación de ETA
    # ───────────────────────────────────────────────────────────────────────
    
    if abs(deriv_p) > 2:
        eta_minutos = 10 + (30 / (1 + abs(deriv_p)))  # Entre 10-20 min
    else:
        eta_minutos = 15.0
    
    eta_minutos = float(max(10.0, min(20.0, eta_minutos)))
    
    # ───────────────────────────────────────────────────────────────────────
    # Confianza
    # ───────────────────────────────────────────────────────────────────────
    
    num_componentes_alerta = sum([
        comp_ghi["umbral_nube"],
        comp_hr["umbral_lluvia"],
        comp_presion["umbral_sistema"],
        score_dt_solar >= 50,
        prob_sundqvist_pct >= 30
    ])
    
    confianza = 0.5 + (0.1 * num_componentes_alerta)
    confianza = float(max(0.0, min(1.0, confianza)))
    
    # ───────────────────────────────────────────────────────────────────────
    # Resultado Descompuesto
    # ───────────────────────────────────────────────────────────────────────
    
    return {
        "score_final": score_final,
        "eta_minutos": eta_minutos,
        "confianza": confianza,
        
        # Componentes DESCOMPUESTOS (cada uno publicable por separado)
        "componente_ghi": {
            "derivada": comp_ghi["derivada_w_m2_s"],
            "score": score_ghi,
            "clasificacion": comp_ghi["clasificacion"],
            "severidad": comp_ghi["severidad"],
            "peso": pesos["ghi"]
        },
        "componente_presion": {
            "derivada": comp_presion["derivada_hpa_min"],
            "score": score_presion,
            "clasificacion": comp_presion["clasificacion"],
            "severidad": comp_presion["severidad"],
            "peso": pesos["presion"]
        },
        "componente_humedad": {
            "derivada": comp_hr["derivada_pct_min"],
            "score": score_hr,
            "clasificacion": comp_hr["clasificacion"],
            "severidad": comp_hr["severidad"],
            "peso": pesos["hr"]
        },
        "componente_dt_solar": {
            "valor": float(dt_solar),
            "score": score_dt_solar,
            "severidad": "baja" if score_dt_solar < 50 else "media" if score_dt_solar < 75 else "alta",
            "peso": pesos["dt_solar"]
        },
        "componente_sundqvist": {
            "probabilidad": prob_sundqvist_pct,
            "score": score_sundqvist,
            "clasificacion": "improbable" if prob_sundqvist_pct < 10 else "posible" if prob_sundqvist_pct < 35 else "probable",
            "peso": pesos["sundqvist"]
        }
    }


if __name__ == "__main__":
    print("[INDICES LLUVIA] Módulo de cálculos de lluvia inminente cargado correctamente")
