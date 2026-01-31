"""
PERFILADOR ATMOSFÉRICO DE ALTURA - FÍSICA RIGUROSA 2026

Implementa modelos científicos para estimar perfiles verticales:
- Temperatura a 100m (Adiabática Seca)
- Viento a 100m (Ley de Hellman)
- Altura de Nubes LCL (Fórmula de Lawrence)
- Número de Richardson (estabilidad atmosférica)
- Índice de Scorer (ondas de gravedad y turbulencia)

Referencias:
- Stull, R.B. (2017). "Practical Meteorology: An Algebra-based Survey"
- Garratt, J.R. (1994). "The Atmospheric Boundary Layer"
- Lawrence, M.G. (2005). "The relationship between relative humidity and the dewpoint"
"""

import math
from typing import Dict, Optional, Tuple
from datetime import datetime


def temperatura_adiabática_seca(temp_superficie_c: float, altura_m: float = 100.0) -> float:
    """
    Calcula temperatura a altura_m usando gradiente adiabático seco.
    
    Fórmula: T(z) = T₀ - Γ_d × z
    Donde Γ_d = 9.8 K/km (gradiente adiabático seco)
    
    Args:
        temp_superficie_c: Temperatura en superficie (°C)
        altura_m: Altura sobre la superficie (metros)
    
    Returns:
        Temperatura estimada a altura_m (°C)
    
    Referencia: Stull (2017), Cap. 3
    """
    gamma_d = 9.8 / 1000.0  # K/m (gradiente adiabático seco)
    temp_altura = temp_superficie_c - (gamma_d * altura_m)
    return temp_altura


def viento_ley_hellman(viento_superficie_ms: float, 
                        altura_superficie_m: float,
                        altura_objetivo_m: float = 100.0,
                        alpha: float = 0.143) -> float:
    """
    Calcula viento a altura objetivo usando Ley de Hellman (power law).
    
    Fórmula: V(z) = V₀ × (z/z₀)^α
    
    Args:
        viento_superficie_ms: Viento medido (m/s)
        altura_superficie_m: Altura del sensor (m)
        altura_objetivo_m: Altura objetivo (m)
        alpha: Exponente de Hellman (0.143 para campo abierto)
    
    Returns:
        Viento estimado a altura_objetivo_m (m/s)
    
    Referencia: Garratt (1994), Cap. 2
    
    Valores típicos de α:
    - 0.10: Superficie de agua, terreno muy liso
    - 0.143: Campo abierto, pasto corto
    - 0.20: Cultivos, arbustos dispersos
    - 0.30: Bosques, áreas urbanas
    """
    if altura_superficie_m <= 0 or altura_objetivo_m <= 0:
        return viento_superficie_ms
    
    # ESCUDO DE SEGURIDAD 2026: Validación adicional
    if viento_superficie_ms < 0:
        return 0.0
    
    try:
        ratio = altura_objetivo_m / altura_superficie_m
        viento_altura = viento_superficie_ms * (ratio ** alpha)
        # Validación física
        if math.isnan(viento_altura) or math.isinf(viento_altura) or viento_altura < 0:
            return viento_superficie_ms
        return max(0.0, viento_altura)
    except (ValueError, ZeroDivisionError, OverflowError):
        return viento_superficie_ms


def lifting_condensation_level_lawrence(temp_c: float, punto_rocio_c: float) -> float:
    """
    Calcula la Altura de la Base de Nubes (LCL) usando fórmula de Lawrence (2005).
    
    Fórmula: LCL (m) = 125 × (T - Td)
    
    Esta es la fórmula más simple y precisa para LCL en atmósfera estándar.
    
    Args:
        temp_c: Temperatura superficie (°C)
        punto_rocio_c: Punto de rocío (°C)
    
    Returns:
        Altura de la base de nubes sobre el suelo (metros)
    
    Referencia: Lawrence, M.G. (2005). Bull. Amer. Meteor. Soc., 86, 225-233
    """
    if temp_c <= punto_rocio_c:
        return 0.0  # Niebla o nubes tocando el suelo
    
    lcl_m = 125.0 * (temp_c - punto_rocio_c)
    return lcl_m


def numero_richardson(delta_temp_k: float,
                      altura_m: float,
                      delta_viento_ms: float) -> float:
    """
    Calcula el Número de Richardson (Ri) para estabilidad atmosférica.
    
    Fórmula: Ri = (g/T) × (ΔT/Δz) / (ΔV/Δz)²
    
    Interpretación:
    - Ri < 0.25: Flujo turbulento, térmicas fuertes (bueno para aves planeadoras)
    - 0.25 < Ri < 1: Transición, turbulencia débil
    - Ri > 1: Flujo laminar, atmósfera muy estable (no hay térmicas)
    
    Args:
        delta_temp_k: Diferencia de temperatura entre dos niveles (K)
        altura_m: Diferencia de altura entre los dos niveles (m)
        delta_viento_ms: Diferencia de velocidad de viento (m/s)
    
    Returns:
        Número de Richardson (adimensional)
    
    Referencia: Stull (2017), Cap. 5
    """
    g = 9.81  # m/s² (aceleración gravedad)
    T_ref = 288.15  # K (temperatura de referencia)
    
    # ESCUDO DE SEGURIDAD 2026: Proteger divisiones
    if abs(altura_m) < 1e-6:
        return float('inf')  # Atmósfera muy estable
    if abs(delta_viento_ms) < 1e-6:
        return float('inf')  # Sin cizalladura, muy estable
    
    # Gradientes
    dT_dz = delta_temp_k / altura_m
    dV_dz = delta_viento_ms / altura_m
    
    # ESCUDO DE SEGURIDAD 2026: Proteger división final
    if abs(dV_dz) < 1e-9:
        return float('inf')
    
    # Richardson
    Ri = (g / T_ref) * dT_dz / (dV_dz ** 2)
    
    # Validación física: Ri debe estar en rango razonable
    if math.isnan(Ri) or math.isinf(Ri):
        return float('inf')
    
    return Ri


def indice_scorer(temp_superficie_c: float,
                  temp_altura_c: float,
                  viento_superficie_ms: float,
                  viento_altura_ms: float,
                  altura_m: float = 100.0) -> Dict[str, float]:
    """
    Calcula el Índice de Scorer (l²) para ondas de gravedad y turbulencia.
    
    Fórmula simplificada: l² ≈ (N² - U'')/U
    Donde N es la frecuencia de Brunt-Väisälä
    
    Interpretación:
    - l² > 0: Ondas de gravedad posibles, atmósfera estable
    - l² < 0: Inestabilidad convectiva, turbulencia
    - |l²| grande: Mayor probabilidad de turbulencia mecánica
    
    Args:
        temp_superficie_c: Temperatura superficie (°C)
        temp_altura_c: Temperatura a altura_m (°C)
        viento_superficie_ms: Viento superficie (m/s)
        viento_altura_ms: Viento a altura_m (m/s)
        altura_m: Altura de la capa (m)
    
    Returns:
        Dict con: scorer_l2, frecuencia_brunt_vaisala, interpretacion
    
    Referencia: Nappo, C.J. (2012). "An Introduction to Atmospheric Gravity Waves"
    """
    g = 9.81  # m/s²
    T_ref = 288.15  # K
    
    # Convertir a Kelvin
    T_surf_K = temp_superficie_c + 273.15
    T_alt_K = temp_altura_c + 273.15
    
    # ESCUDO DE SEGURIDAD 2026: Proteger división
    if abs(altura_m) < 1e-6:
        return {
            "scorer_l2": 0.0,
            "brunt_vaisala_N2": 0.0,
            "cizalladura_viento_dV_dz": 0.0,
            "interpretacion": "Altura insuficiente para cálculo"
        }
    
    # Frecuencia de Brunt-Väisälä (N²)
    dT_dz = (T_alt_K - T_surf_K) / altura_m
    N2 = (g / T_ref) * dT_dz
    
    # Cizalladura de viento
    dV_dz = (viento_altura_ms - viento_superficie_ms) / altura_m
    
    # Velocidad media
    V_medio = (viento_superficie_ms + viento_altura_ms) / 2.0
    
    # ESCUDO DE SEGURIDAD 2026: Proteger división con umbral más robusto
    if abs(V_medio) < 0.1:
        V_medio = 0.1  # Mínimo físico para evitar divisiones extremas
    
    # Índice de Scorer simplificado
    scorer_l2 = N2 / (V_medio ** 2)
    
    # Validación física
    if math.isnan(scorer_l2) or math.isinf(scorer_l2):
        scorer_l2 = 0.0
    
    # Interpretación
    if scorer_l2 > 0.01:
        interpretacion = "Atmósfera muy estable, ondas de gravedad posibles"
    elif scorer_l2 > 0:
        interpretacion = "Atmósfera estable, poco favorable para térmicas"
    elif scorer_l2 > -0.01:
        interpretacion = "Transición, turbulencia moderada"
    else:
        interpretacion = "Inestabilidad convectiva, térmicas fuertes"
    
    return {
        "scorer_l2": scorer_l2,
        "brunt_vaisala_N2": N2,
        "cizalladura_viento_dV_dz": dV_dz,
        "interpretacion": interpretacion
    }


def perfil_atmosferico_completo(temp_superficie_c: float,
                                 punto_rocio_c: float,
                                 viento_superficie_ms: float,
                                 altura_sensor_m: float = 13.0,
                                 altura_objetivo_m: float = 100.0,
                                 alpha_hellman: float = 0.143) -> Dict[str, any]:
    """
    Calcula el perfil atmosférico completo hasta altura_objetivo_m.
    
    Args:
        temp_superficie_c: Temperatura superficie (°C)
        punto_rocio_c: Punto de rocío (°C)
        viento_superficie_ms: Viento superficie (m/s)
        altura_sensor_m: Altura del sensor sobre el suelo (m)
        altura_objetivo_m: Altura objetivo del perfil (m)
        alpha_hellman: Exponente de Hellman para viento
    
    Returns:
        Dict con todos los parámetros del perfil atmosférico
    """
    # Temperatura a altura objetivo (adiabática seca)
    temp_objetivo_c = temperatura_adiabática_seca(temp_superficie_c, altura_objetivo_m)
    
    # Viento a altura objetivo (Hellman)
    viento_objetivo_ms = viento_ley_hellman(viento_superficie_ms, 
                                            altura_sensor_m, 
                                            altura_objetivo_m, 
                                            alpha_hellman)
    
    # Altura de nubes (LCL)
    lcl_m = lifting_condensation_level_lawrence(temp_superficie_c, punto_rocio_c)
    
    # Número de Richardson (estabilidad)
    delta_temp_k = temp_objetivo_c - temp_superficie_c
    Ri = numero_richardson(delta_temp_k, altura_objetivo_m, 
                          viento_objetivo_ms - viento_superficie_ms)
    
    # Índice de Scorer (turbulencia)
    scorer = indice_scorer(temp_superficie_c, temp_objetivo_c,
                          viento_superficie_ms, viento_objetivo_ms,
                          altura_objetivo_m)
    
    return {
        "temperatura_100m_c": round(temp_objetivo_c, 2),
        "viento_100m_ms": round(viento_objetivo_ms, 2),
        "altura_nubes_lcl_m": round(lcl_m, 1),
        "richardson_Ri": round(Ri, 4),
        "scorer_l2": round(scorer["scorer_l2"], 6),
        "brunt_vaisala_N2": round(scorer["brunt_vaisala_N2"], 6),
        "interpretacion_estabilidad": scorer["interpretacion"],
        "favorable_termicas": Ri < 0.25,
        "favorable_vuelo_planeo": Ri < 0.25 and lcl_m > 300
    }
