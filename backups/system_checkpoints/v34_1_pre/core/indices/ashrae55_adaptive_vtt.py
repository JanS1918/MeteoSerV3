"""
Modelo de Confort Adaptativo ASHRAE-55 + Modelo VTT de Moho.
Estándar de Laboratorio Nacional (QUANTUM_DIAMOND_REFINED_V1).

Referencias:
- ASHRAE Standard 55-2020: Thermal Environmental Conditions for Human Occupancy
- ASHRAE 160-2016: Criteria for Moisture-Control Design Analysis
- VTT Technical Research Centre of Finland: Dynamic mold growth models
- Ojanen et al. (2010): Mold growth modeling of building structures using sensitivity classes

ARQUITECTURA:
1. Confort Adaptativo ASHRAE-55 (temperatura operativa vs temperatura media exterior running)
2. Modelo VTT de crecimiento de moho (isotermas de sorción dinámicas, temperatura, HR)
3. Integración con sensores existentes (temperatura, HR, ocupación opcional)
"""

import math
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta


def temperatura_operativa(
    temp_aire_c: float,
    temp_radiante_media_c: Optional[float] = None,
    velocidad_aire_ms: float = 0.1
) -> float:
    """
    Calcula temperatura operativa según ASHRAE-55.
    
    T_op = A*T_aire + (1-A)*T_radiante
    
    Donde A depende de la velocidad del aire:
    - v < 0.2 m/s: A = 0.5 (convección = radiación)
    - v > 0.6 m/s: A = 0.6 (convección domina)
    
    Args:
        temp_aire_c: Temperatura del aire (°C)
        temp_radiante_media_c: Temperatura radiante media (°C), si disponible
        velocidad_aire_ms: Velocidad del aire (m/s)
    
    Returns:
        Temperatura operativa (°C)
    """
    # Si no hay medida de temperatura radiante, asumir T_rad ≈ T_aire + 1°C
    # (paredes/suelo típicamente 1-2°C más frías en invierno, más calientes en verano)
    if temp_radiante_media_c is None:
        temp_radiante_media_c = temp_aire_c + 1.0
    
    # Factor de ponderación según velocidad del aire
    if velocidad_aire_ms < 0.2:
        A = 0.5
    elif velocidad_aire_ms > 0.6:
        A = 0.6
    else:
        # Interpolación lineal
        A = 0.5 + (velocidad_aire_ms - 0.2) * (0.6 - 0.5) / (0.6 - 0.2)
    
    T_op = A * temp_aire_c + (1.0 - A) * temp_radiante_media_c
    return T_op


def temperatura_confort_ashrae55_adaptativo(
    temp_media_exterior_running_c: float,
    categoria: str = "80"
) -> Tuple[float, float, float]:
    """
    Límites de confort adaptativo ASHRAE-55 para edificios ventilados naturalmente.
    
    T_confort = 0.31 * T_rm_out + 17.8
    
    Donde T_rm_out es la temperatura media exterior "running" (promedio exponencial
    ponderado de los últimos 7-30 días).
    
    Args:
        temp_media_exterior_running_c: Temperatura media exterior running (°C)
        categoria: Aceptabilidad ("80" = 80%, "90" = 90%)
    
    Returns:
        (T_confort_neutral, T_min, T_max) en °C
    """
    # Temperatura neutral de confort (ASHRAE-55)
    T_neutral = 0.31 * temp_media_exterior_running_c + 17.8
    
    # Límites según categoría de aceptabilidad
    if categoria == "90":
        # 90% aceptabilidad: ±2.5°C
        delta = 2.5
    else:
        # 80% aceptabilidad: ±3.5°C
        delta = 3.5
    
    T_min = T_neutral - delta
    T_max = T_neutral + delta
    
    return T_neutral, T_min, T_max


def calcular_temp_running_mean(
    temperaturas_diarias: list,
    pesos_exponenciales: Optional[list] = None
) -> float:
    """
    Calcula temperatura media exterior "running" (promedio exponencial ponderado).
    
    T_rm = (T_d-1 + 0.8*T_d-2 + 0.6*T_d-3 + ... + 0.2*T_d-7) / sum(pesos)
    
    Args:
        temperaturas_diarias: Lista de temperaturas diarias (°C) [hoy-1, hoy-2, ..., hoy-n]
        pesos_exponenciales: Pesos opcionales (default: [1.0, 0.8, 0.6, 0.4, 0.2])
    
    Returns:
        Temperatura running mean (°C)
    """
    if not temperaturas_diarias:
        return 15.0  # Fallback
    
    if pesos_exponenciales is None:
        # Pesos default ASHRAE-55 (hasta 7 días)
        pesos_exponenciales = [1.0, 0.8, 0.6, 0.4, 0.2]
    
    n = min(len(temperaturas_diarias), len(pesos_exponenciales))
    
    suma_ponderada = sum(temperaturas_diarias[i] * pesos_exponenciales[i] for i in range(n))
    suma_pesos = sum(pesos_exponenciales[:n])
    
    T_rm = suma_ponderada / suma_pesos if suma_pesos > 0 else temperaturas_diarias[0]
    return T_rm


def confort_ashrae55_adaptativo(
    temp_aire_interior_c: float,
    temp_media_exterior_running_c: float,
    temp_radiante_media_c: Optional[float] = None,
    velocidad_aire_ms: float = 0.1,
    categoria: str = "80"
) -> Dict:
    """
    Evaluación de confort adaptativo ASHRAE-55.
    
    Args:
        temp_aire_interior_c: Temperatura del aire interior (°C)
        temp_media_exterior_running_c: Temperatura media exterior running (°C)
        temp_radiante_media_c: Temperatura radiante media (°C), opcional
        velocidad_aire_ms: Velocidad del aire (m/s)
        categoria: Aceptabilidad ("80" o "90")
    
    Returns:
        Dict con:
        - temperatura_operativa: T_op (°C)
        - temperatura_confort_neutral: T_neutral (°C)
        - temperatura_min_confort: T_min (°C)
        - temperatura_max_confort: T_max (°C)
        - desviacion_confort: T_op - T_neutral (°C)
        - confort_porcentaje: 0-100 (100 = óptimo)
        - categoria_confort: "FRIO", "OPTIMO", "CALIDO"
    """
    # Temperatura operativa
    T_op = temperatura_operativa(temp_aire_c, temp_radiante_media_c, velocidad_aire_ms)
    
    # Límites de confort
    T_neutral, T_min, T_max = temperatura_confort_ashrae55_adaptativo(
        temp_media_exterior_running_c, categoria
    )
    
    # Desviación respecto a la temperatura neutral
    desviacion = T_op - T_neutral
    
    # Porcentaje de confort (100% = óptimo, 0% = fuera de límites)
    if T_min <= T_op <= T_max:
        # Dentro de límites: confort proporcional a cercanía al neutral
        delta_max = T_max - T_neutral
        confort_pct = 100.0 * (1.0 - abs(desviacion) / delta_max) if delta_max > 0 else 100.0
    else:
        # Fuera de límites: penalización
        if T_op < T_min:
            exceso = T_min - T_op
            confort_pct = max(0.0, 50.0 - exceso * 10.0)
        else:
            exceso = T_op - T_max
            confort_pct = max(0.0, 50.0 - exceso * 10.0)
    
    # Categoría
    if T_op < T_neutral - 1.0:
        categoria_conf = "FRIO"
    elif T_op > T_neutral + 1.0:
        categoria_conf = "CALIDO"
    else:
        categoria_conf = "OPTIMO"
    
    return {
        "temperatura_operativa": round(T_op, 2),
        "temperatura_confort_neutral": round(T_neutral, 2),
        "temperatura_min_confort": round(T_min, 2),
        "temperatura_max_confort": round(T_max, 2),
        "desviacion_confort": round(desviacion, 2),
        "confort_porcentaje": round(confort_pct, 1),
        "categoria_confort": categoria_conf,
        "motor": "Quantum_Diamond_Refined_v1"
    }


# =============================================================================
# MODELO VTT DE MOHO (Estructura dinámica)
# =============================================================================

def clase_sensibilidad_superficie(
    material: str = "yeso"
) -> int:
    """
    Clase de sensibilidad al moho según VTT.
    
    Clases VTT:
    0: Muy resistente (pino, abeto tratado)
    1: Resistente (pino con barniz)
    2: Sensible (madera sin tratar, yeso)
    3: Muy sensible (materiales biodegradables, papel)
    
    Args:
        material: Tipo de material ("yeso", "madera", "papel", "pino")
    
    Returns:
        Clase de sensibilidad (0-3)
    """
    clases = {
        "pino_tratado": 0,
        "pino_barniz": 1,
        "madera": 2,
        "yeso": 2,
        "carton": 3,
        "papel": 3
    }
    return clases.get(material.lower(), 2)  # Default: sensible


def humedad_critica_moho_vtt(
    temp_c: float,
    clase_sensibilidad: int
) -> float:
    """
    Humedad relativa crítica para crecimiento de moho según VTT.
    
    RH_crit = RH_base + k_T * (T - 20)
    
    Donde RH_base y k_T dependen de la clase de sensibilidad.
    
    Args:
        temp_c: Temperatura (°C)
        clase_sensibilidad: Clase VTT (0-3)
    
    Returns:
        HR crítica (%) para inicio de crecimiento de moho
    """
    # Parámetros VTT (ajustados de Ojanen et al. 2010)
    parametros = {
        0: {"RH_base": 90.0, "k_T": -0.3},  # Muy resistente
        1: {"RH_base": 85.0, "k_T": -0.4},  # Resistente
        2: {"RH_base": 80.0, "k_T": -0.5},  # Sensible
        3: {"RH_base": 75.0, "k_T": -0.6}   # Muy sensible
    }
    
    params = parametros.get(clase_sensibilidad, parametros[2])
    RH_crit = params["RH_base"] + params["k_T"] * (temp_c - 20.0)
    
    # Límites físicos: moho no crece < 0°C o > 50°C, ni < 70% HR
    RH_crit = max(70.0, min(100.0, RH_crit))
    
    return RH_crit


def indice_moho_vtt(
    temp_c: float,
    hr_pct: float,
    duracion_exposicion_dias: float,
    clase_sensibilidad: int = 2
) -> Dict:
    """
    Índice de moho VTT (Mold Index).
    
    Modelo simplificado de crecimiento de moho basado en:
    - Temperatura
    - Humedad relativa
    - Duración de exposición
    - Sensibilidad del material
    
    Índice de moho VTT:
    0 = Sin crecimiento
    1 = Crecimiento inicial (invisible)
    2 = < 10% cobertura
    3 = 10-30% cobertura
    4 = 30-70% cobertura
    5 = 70-100% cobertura
    6 = > 100% cobertura (múltiples capas)
    
    Args:
        temp_c: Temperatura (°C)
        hr_pct: Humedad relativa (%)
        duracion_exposicion_dias: Días de exposición continua
        clase_sensibilidad: Clase VTT (0-3)
    
    Returns:
        Dict con índice de moho y metadata
    """
    # Temperatura óptima para crecimiento: 20-25°C
    if temp_c < 0 or temp_c > 50:
        # Fuera de rango: sin crecimiento
        return {
            "indice_moho_vtt": 0.0,
            "riesgo_moho": "NULO",
            "hr_critica_pct": 100.0,
            "tiempo_inicio_crecimiento_dias": 999.0,
            "motor": "Quantum_Diamond_Refined_v1"
        }
    
    # HR crítica
    hr_critica = humedad_critica_moho_vtt(temp_c, clase_sensibilidad)
    
    # Factor de crecimiento (0-1)
    if hr_pct < hr_critica:
        # Sin crecimiento
        factor_crecimiento = 0.0
        tiempo_inicio = 999.0
    else:
        # Crecimiento proporcional al exceso de HR
        exceso_hr = hr_pct - hr_critica
        factor_crecimiento = min(1.0, exceso_hr / 20.0)  # Saturación en +20% HR
        
        # Tiempo de inicio de crecimiento visible (días)
        # Más rápido con mayor HR y temperatura óptima
        factor_temp = 1.0 - abs(temp_c - 22.5) / 22.5  # Óptimo 22.5°C
        tiempo_inicio = 7.0 / (factor_crecimiento * factor_temp + 0.01)
    
    # Índice de moho (acumulativo según duración)
    if duracion_exposicion_dias < tiempo_inicio:
        indice_moho = 0.0
    else:
        dias_activos = duracion_exposicion_dias - tiempo_inicio
        # Crecimiento exponencial inicial, luego saturación
        indice_moho = 6.0 * (1.0 - math.exp(-factor_crecimiento * dias_activos / 30.0))
    
    indice_moho = max(0.0, min(6.0, indice_moho))
    
    # Categoría de riesgo
    if indice_moho < 1.0:
        riesgo = "NULO"
    elif indice_moho < 2.0:
        riesgo = "BAJO"
    elif indice_moho < 3.0:
        riesgo = "MEDIO"
    elif indice_moho < 4.0:
        riesgo = "ALTO"
    else:
        riesgo = "CRITICO"
    
    return {
        "indice_moho_vtt": round(indice_moho, 2),
        "riesgo_moho": riesgo,
        "hr_critica_pct": round(hr_critica, 1),
        "tiempo_inicio_crecimiento_dias": round(tiempo_inicio, 1),
        "factor_crecimiento": round(factor_crecimiento, 3),
        "motor": "Quantum_Diamond_Refined_v1"
    }


def evaluacion_edificio_confort_moho(
    temp_aire_interior_c: float,
    hr_interior_pct: float,
    temp_media_exterior_running_c: float,
    duracion_exposicion_hr_alta_dias: float = 0.0,
    temp_radiante_media_c: Optional[float] = None,
    velocidad_aire_ms: float = 0.1,
    material_superficie: str = "yeso"
) -> Dict:
    """
    Evaluación combinada de confort ASHRAE-55 y riesgo de moho VTT.
    
    Args:
        temp_aire_interior_c: Temperatura del aire interior (°C)
        hr_interior_pct: Humedad relativa interior (%)
        temp_media_exterior_running_c: Temperatura media exterior running (°C)
        duracion_exposicion_hr_alta_dias: Días con HR alta continua
        temp_radiante_media_c: Temperatura radiante media (°C), opcional
        velocidad_aire_ms: Velocidad del aire (m/s)
        material_superficie: Tipo de material de superficie
    
    Returns:
        Dict con evaluación completa de confort y moho
    """
    # Confort ASHRAE-55
    confort = confort_ashrae55_adaptativo(
        temp_aire_interior_c,
        temp_media_exterior_running_c,
        temp_radiante_media_c,
        velocidad_aire_ms,
        categoria="80"
    )
    
    # Riesgo de moho VTT
    clase_sens = clase_sensibilidad_superficie(material_superficie)
    moho = indice_moho_vtt(
        temp_aire_interior_c,
        hr_interior_pct,
        duracion_exposicion_hr_alta_dias,
        clase_sens
    )
    
    # Índice combinado de salud del edificio (0-100)
    # Penalización por disconfort y riesgo de moho
    salud_edificio = (
        confort["confort_porcentaje"] * 0.6 +
        (100.0 - moho["indice_moho_vtt"] * 16.67) * 0.4  # moho=6 → 0 salud
    )
    salud_edificio = max(0.0, min(100.0, salud_edificio))
    
    return {
        "confort_ashrae55": confort,
        "moho_vtt": moho,
        "salud_edificio_pct": round(salud_edificio, 1),
        "motor": "Quantum_Diamond_Refined_v1"
    }
