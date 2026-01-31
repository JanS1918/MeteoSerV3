"""
ÍNDICES DE CAMPO AVANZADOS - BIOFÍSICA Y AGRONOMÍA PROFESIONAL 2026

Implementa modelos científicos rigurosos:
- Confort Animal (Porter & Gates 1971): Balance radiativo biofísico
- Barro en Campo (Modelo Bucket): Balance hídrico real
- Visibilidad (Kneizys): Ajuste higroscópico de partículas

Referencias:
- Porter, W.P. & Gates, D.M. (1971). "Thermodynamic Equilibria of Animals with Environment"
- Allen, R.G. et al. (1998). "FAO-56 Penman-Monteith"
- Kneizys, F.X. et al. (1988). "LOWTRAN 7 Computer Code"
"""

import math
from typing import Dict, Optional, Tuple
from datetime import datetime


def confort_ave_porter_gates(temperatura_c: float,
                              viento_ms: float,
                              radiacion_wm2: float,
                              humedad_relativa: float,
                              elevacion_solar_deg: float,
                              lluvia_mm_h: float = 0.0,
                              masa_ave_kg: float = 0.8,
                              area_proyectada_m2: Optional[float] = None) -> Dict[str, float]:
    """
    Calcula el confort térmico de un ave usando la Ecuación de Porter & Gates (1971).
    
    Balance energético del animal:
    Q_metabol + Q_solar - Q_convec - Q_evap - Q_radiacion = 0
    
    Args:
        temperatura_c: Temperatura del aire (°C)
        viento_ms: Velocidad del viento (m/s)
        radiacion_wm2: Radiación solar (W/m²)
        humedad_relativa: Humedad relativa (%)
        elevacion_solar_deg: Elevación solar (grados)
        masa_ave_kg: Masa del ave (kg, ej. 0.8 kg para halcón)
        area_proyectada_m2: Área proyectada del ave (m²), si None se estima
    
    Returns:
        Dict con balance energético y confort (0-100)
    
    Referencia: Porter & Gates (1971), Ecological Monographs 41:245-270
    """
    # Constantes físicas
    sigma = 5.67e-8  # W/(m²·K⁴) - Stefan-Boltzmann
    epsilon_plumaje = 0.95  # Emisividad del plumaje
    absortividad_solar = 0.85  # Absortividad solar del plumaje
    
    # Estimar área proyectada si no se proporciona
    if area_proyectada_m2 is None:
        # Ley alométrica: A ≈ 0.1 × M^(2/3)
        area_proyectada_m2 = 0.1 * (masa_ave_kg ** (2/3))
    
    # Temperatura en Kelvin
    T_aire_K = temperatura_c + 273.15
    T_piel_estimada_K = T_aire_K + 2.0  # Asunción: piel ~2K más caliente que aire
    
    # 1. GANANCIA SOLAR
    # Factor de proyección (Höppe)
    if elevacion_solar_deg > 0:
        f_p = 0.308 * math.cos(math.radians(90 - elevacion_solar_deg))
    else:
        f_p = 0.0
    
    # Atenuación Rayleigh-Miller corregida por presión local
    P_std = 1013.25
    P_local = 1013.25
    try:
        import inspect
        frame = inspect.currentframe()
        while frame:
            if "contexto" in frame.f_locals:
                contexto = frame.f_locals["contexto"]
                if hasattr(contexto, "presion_barometrica"):
                    P_local = float(contexto.presion_barometrica)
                break
            frame = frame.f_back
    except Exception:
        pass
    k_rayleigh = 0.008735
    longitud_onda_nm = 550.0
    masa_optica = 1.0 / max(0.01, math.sin(math.radians(elevacion_solar_deg)))
    tau_rayleigh = math.exp(-k_rayleigh * masa_optica * (P_local / P_std) * (550.0 / longitud_onda_nm) ** 4)
    Q_solar = absortividad_solar * radiacion_wm2 * area_proyectada_m2 * f_p * tau_rayleigh
    
    # 2. PÉRDIDA POR CONVECCIÓN
    # Coeficiente convectivo (Mitchell, 1976)
    if viento_ms > 0.1:
        # Número de Reynolds simplificado
        L_caracteristica = math.sqrt(area_proyectada_m2)  # longitud característica
        h_c = 10.45 - viento_ms + 10 * math.sqrt(viento_ms)  # W/(m²·K)
    else:
        h_c = 5.0  # Convección libre
    
    Q_convec = h_c * area_proyectada_m2 * (T_piel_estimada_K - T_aire_K)
    
    # 3. PÉRDIDA POR RADIACIÓN
    # Radiación de onda larga (cuerpo negro)
    Q_radiacion = epsilon_plumaje * sigma * area_proyectada_m2 * (T_piel_estimada_K**4 - T_aire_K**4)
    
    # 4. PÉRDIDA POR EVAPORACIÓN
    # Presión de vapor saturado (Magnus)
    # Presión de vapor CON FACTOR DE GREENSPAN
    T_k = temperatura_c + 273.15
    p_pa = 101325.0  # Presión estándar (idealmente del contexto)
    
    es_aire_base = 0.6108 * math.exp((17.27 * temperatura_c) / (temperatura_c + 237.3))
    Bm = -1.6e-5 + 1.8e-8 * T_k
    f_greenspan = math.exp(Bm * p_pa / (8.314472 * T_k))
    es_aire = es_aire_base * f_greenspan
    ea_aire = es_aire * (humedad_relativa / 100.0)
    vpd_kpa = es_aire - ea_aire
    
    # Pérdida evaporativa (respiración + piel)
    # Asunción: 20% de la pérdida de calor es evaporativa en condiciones normales
    calor_latente_vapor = 2450000  # J/kg (a 20°C)
    tasa_evaporacion_kg_s = max(0, vpd_kpa * 0.00001 * area_proyectada_m2)  # Estimación
    Q_evap = tasa_evaporacion_kg_s * calor_latente_vapor

    # 4b. ENFRIAMIENTO POR MOJADO (lluvia + viento)
    mojado_factor = 0.0
    try:
        lluvia_mm_h = max(0.0, float(lluvia_mm_h))
        viento_ms = max(0.0, float(viento_ms))
        mojado_factor = min(1.0, lluvia_mm_h / 2.0) * (1.0 + min(1.0, viento_ms / 8.0)) * 0.6
    except Exception:
        mojado_factor = 0.0
    
    # 5. PRODUCCIÓN METABÓLICA
    # Tasa metabólica basal (Kleiber, 1932): BMR ≈ 70 × M^0.75 kcal/día
    BMR_W = 70 * (masa_ave_kg ** 0.75) * 4184 / 86400  # Convertir kcal/día a W
    Q_metabol = BMR_W * 1.5  # Factor de actividad (1.5 para ave en reposo)
    
    # BALANCE ENERGÉTICO (base)
    balance_base = Q_metabol + Q_solar - Q_convec - Q_radiacion - Q_evap
    estres_base = abs(balance_base)
    confort_base = max(0, min(100, 100 - (estres_base / 2.0)))

    # Aplicar mojado si tiene impacto significativo
    Q_evap_mojado = Q_evap * (1.0 + mojado_factor)
    balance_mojado = Q_metabol + Q_solar - Q_convec - Q_radiacion - Q_evap_mojado
    estres_mojado = abs(balance_mojado)
    confort_mojado = max(0, min(100, 100 - (estres_mojado / 2.0)))
    if abs(confort_mojado - confort_base) >= 5.0:
        balance_total = balance_mojado
        confort = confort_mojado
        mojado_aplicado = True
    else:
        balance_total = balance_base
        confort = confort_base
        mojado_aplicado = False
    
    # Interpretación
    if confort > 80:
        interpretacion = "Confort térmico óptimo"
    elif confort > 60:
        interpretacion = "Confort aceptable"
    elif confort > 40:
        interpretacion = "Estrés térmico leve"
    elif confort > 20:
        interpretacion = "Estrés térmico moderado"
    else:
        interpretacion = "Estrés térmico severo"
    
    return {
        "confort_ave": round(confort, 2),
        "balance_energetico_W": round(balance_total, 2),
        "ganancia_solar_W": round(Q_solar, 2),
        "perdida_conveccion_W": round(Q_convec, 2),
        "perdida_radiacion_W": round(Q_radiacion, 2),
        "perdida_evaporacion_W": round(Q_evap, 2),
        "enfriamiento_mojado_W": round(Q_evap_mojado - Q_evap, 2),
        "mojado_aplicado": mojado_aplicado,
        "produccion_metabolica_W": round(Q_metabol, 2),
        "interpretacion": interpretacion
    }


def modelo_bucket_barro(lluvia_24h_mm: float,
                        evapotranspiracion_mm: float,
                        humedad_suelo_actual: Optional[float] = None,
                        capacidad_campo_mm: float = 200.0,
                        punto_marchitez_mm: float = 50.0,
                        drenaje_profundo_coef: float = 0.1) -> Dict[str, float]:
    """
    Modelo Bucket (capacidad de campo) para calcular saturación del suelo.
    
    Balance hídrico: ΔS = P - ET - D
    Donde:
    - P = Precipitación
    - ET = Evapotranspiración
    - D = Drenaje profundo
    
    Args:
        lluvia_24h_mm: Lluvia acumulada 24h (mm)
        evapotranspiracion_mm: ET calculada (Penman-Monteith) en 24h (mm)
        humedad_suelo_actual: Humedad del suelo actual (%), si disponible
        capacidad_campo_mm: Capacidad de campo del suelo (mm de agua)
        punto_marchitez_mm: Punto de marchitez permanente (mm)
        drenaje_profundo_coef: Coeficiente de drenaje (0-1)
    
    Returns:
        Dict con saturación, barro, y balance hídrico
    
    Referencia: Allen et al. (1998), FAO-56
    """
    # Agua disponible inicial (si hay sensor de humedad)
    if humedad_suelo_actual is not None:
        # Convertir % a mm usando capacidad de campo
        agua_disponible_mm = (humedad_suelo_actual / 100.0) * capacidad_campo_mm
    else:
        # Asumir 60% de capacidad si no hay sensor
        agua_disponible_mm = 0.6 * capacidad_campo_mm
    
    # Balance hídrico
    entrada_agua = lluvia_24h_mm
    salida_et = evapotranspiracion_mm
    
    # Calcular nuevo contenido de agua
    agua_nueva_mm = agua_disponible_mm + entrada_agua - salida_et
    
    # Drenaje profundo si excede capacidad de campo
    if agua_nueva_mm > capacidad_campo_mm:
        exceso = agua_nueva_mm - capacidad_campo_mm
        drenaje_mm = exceso * drenaje_profundo_coef
        agua_nueva_mm -= drenaje_mm
    else:
        drenaje_mm = 0.0
    
    # Saturación del suelo (%)
    saturacion = (agua_nueva_mm / capacidad_campo_mm) * 100.0
    saturacion = max(0, min(100, saturacion))
    
    # ÍNDICE DE BARRO (0-100)
    # Barro máximo cuando saturación > 90%
    if saturacion > 90:
        indice_barro = 100.0
    elif saturacion > 70:
        indice_barro = (saturacion - 70) * 5.0  # 0-100 entre 70-90%
    else:
        indice_barro = 0.0
    
    # Interpretación
    if indice_barro > 80:
        interpretacion = "Barro severo, campo impracticable"
    elif indice_barro > 50:
        interpretacion = "Barro moderado, campo difícil"
    elif indice_barro > 20:
        interpretacion = "Barro leve, campo transitable"
    else:
        interpretacion = "Sin barro, campo seco"
    
    return {
        "indice_barro": round(indice_barro, 2),
        "saturacion_suelo_pct": round(saturacion, 2),
        "agua_disponible_mm": round(agua_nueva_mm, 2),
        "entrada_lluvia_mm": round(entrada_agua, 2),
        "salida_et_mm": round(salida_et, 2),
        "drenaje_profundo_mm": round(drenaje_mm, 2),
        "balance_neto_mm": round(entrada_agua - salida_et - drenaje_mm, 2),
        "interpretacion": interpretacion
    }


def visibilidad_kneizys(pm25_ugm3: float,
                        humedad_relativa: float,
                        temperatura_c: float,
                        longitud_onda_nm: float = 550.0) -> Dict[str, float]:
    """
    Calcula visibilidad atmosférica usando modelo de Kneizys (LOWTRAN).
    
    Incorpora ajuste higroscópico: las partículas crecen con humedad.
    
    Fórmula de Koschmieder: V = 3.912 / β_ext
    Donde β_ext es el coeficiente de extinción (m⁻¹)
    
    Args:
        pm25_ugm3: Concentración de PM2.5 (µg/m³)
        humedad_relativa: Humedad relativa (%)
        temperatura_c: Temperatura del aire (°C)
        longitud_onda_nm: Longitud de onda de observación (nm)
    
    Returns:
        Dict con visibilidad, coeficiente de extinción y componentes
    
    Referencia: Kneizys et al. (1988), LOWTRAN 7
    """
    # Factor de crecimiento higroscópico (Kasten, 1969)
    if humedad_relativa >= 100:
        f_rh = 6.0  # Niebla
    elif humedad_relativa >= 90:
        f_rh = 3.0 + 0.5 * (humedad_relativa - 90)
    elif humedad_relativa >= 70:
        f_rh = 1.5 + 0.075 * (humedad_relativa - 70)
    else:
        f_rh = 1.0
    
    # Coeficiente de extinción por partículas (Mie)
    # PM2.5 típico tiene eficiencia de extinción Q ≈ 3-4 m²/g
    Q_ext = 3.5  # m²/g (eficiencia de extinción de Mie)
    rho_particula = 1.5e6  # g/m³ (densidad típica de aerosoles)
    
    # Convertir PM2.5 a coeficiente de extinción
    beta_particulas = (pm25_ugm3 * 1e-6) * Q_ext * f_rh  # m⁻¹
    
    # Extinción molecular (Rayleigh-Miller corregida por presión local)
    # β_rayleigh = k * P_local/P_std * (λ_std/λ)^4
    P_std = 1013.25  # hPa
    P_local = 1013.25
    try:
        import inspect
        frame = inspect.currentframe()
        while frame:
            if "contexto" in frame.f_locals:
                contexto = frame.f_locals["contexto"]
                if hasattr(contexto, "presion_barometrica"):
                    P_local = float(contexto.presion_barometrica)
                break
            frame = frame.f_back
    except Exception:
        pass
    k_rayleigh = 1.0e-5
    beta_rayleigh = k_rayleigh * (P_local / P_std) * (550.0 / longitud_onda_nm) ** 4
    
    # Extinción total
    beta_total = beta_particulas + beta_rayleigh
    
    # Visibilidad (Koschmieder)
    if beta_total > 0:
        visibilidad_m = 3.912 / beta_total
    else:
        visibilidad_m = 100000  # 100 km (visibilidad excepcional)
    
    # Limitar a rango razonable
    visibilidad_m = min(visibilidad_m, 100000)
    visibilidad_km = visibilidad_m / 1000.0
    
    # Índice de visibilidad (0-100)
    # 100 = excelente (>20 km)
    # 0 = muy pobre (<1 km)
    if visibilidad_km > 20:
        indice_visibilidad = 100
    elif visibilidad_km > 10:
        indice_visibilidad = 80 + 20 * (visibilidad_km - 10) / 10
    elif visibilidad_km > 4:
        indice_visibilidad = 50 + 30 * (visibilidad_km - 4) / 6
    elif visibilidad_km > 1:
        indice_visibilidad = 20 + 30 * (visibilidad_km - 1) / 3
    else:
        indice_visibilidad = 20 * visibilidad_km
    
    # Interpretación
    if visibilidad_km > 20:
        interpretacion = "Visibilidad excelente"
    elif visibilidad_km > 10:
        interpretacion = "Visibilidad buena"
    elif visibilidad_km > 4:
        interpretacion = "Visibilidad moderada"
    elif visibilidad_km > 1:
        interpretacion = "Visibilidad pobre"
    else:
        interpretacion = "Visibilidad muy pobre (niebla/smog)"
    
    return {
        "visibilidad_km": round(visibilidad_km, 2),
        "visibilidad_m": round(visibilidad_m, 1),
        "indice_visibilidad": round(indice_visibilidad, 2),
        "coef_extincion_total_m-1": round(beta_total, 6),
        "coef_extincion_particulas_m-1": round(beta_particulas, 6),
        "coef_extincion_rayleigh_m-1": round(beta_rayleigh, 6),
        "factor_higroscopico": round(f_rh, 2),
        "interpretacion": interpretacion
    }
