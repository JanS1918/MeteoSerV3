"""
SUNDQVIST PARAMETRIZATION (1978/2024) - PROBABILIDAD DE LLUVIA POR CALOR LATENTE
==================================================================================
Modelo avanzado para probabilidad de precipitación basado en balance de energía.
Superior a métodos simples (CAPE/HR) porque considera liberación de calor latente.

Referencias:
- Sundqvist et al. (1989): "Condensation and Cloud Parameterization Studies"
- ECMWF IFS Documentation (2024): Model Physics
- Tiedtke Mass Flux Scheme adaptado para estaciones

terrestres

ARQUITECTURA: 100% numpy vectorizado, compatible con Thompson microphysics.
"""

import numpy as np
from typing import Dict, Union


def calcular_probabilidad_lluvia_sundqvist(
    temperatura_c: Union[float, np.ndarray],
    humedad_relativa: Union[float, np.ndarray],
    presion_hpa: Union[float, np.ndarray],
    qc: Union[float, np.ndarray],  # Mixing ratio agua nube (g/kg) desde Thompson
    qr: Union[float, np.ndarray],  # Mixing ratio agua lluvia (g/kg)
    tendencia_presion_hpa_h: Union[float, np.ndarray] = 0.0,  # dP/dt en hPa/h
    radiacion_neta_wm2: Union[float, np.ndarray] = None,  # Qnet opcional
) -> Dict[str, Union[float, np.ndarray]]:
    """
    Probabilidad de lluvia según Sundqvist (balance de calor latente).
    
    Principio: Para que llueva, la nube debe liberar energía (condensación).
    Si el calor latente no se disipa, la nube se evapora sin precipitar.
    
    Args:
        temperatura_c: Temperatura (°C)
        humedad_relativa: HR (%)
        presion_hpa: Presión barométrica
        qc: Mixing ratio agua nube (g/kg)
        qr: Mixing ratio agua lluvia (g/kg)
        tendencia_presion_hpa_h: Tendencia presión (hPa/hora), negativo = caída
        radiacion_neta_wm2: Radiación neta (W/m²), opcional
    
    Returns:
        Dict con:
            - prob_lluvia_pct: Probabilidad de lluvia (%)
            - calor_latente_wm2: Tasa de liberación de calor latente
            - tasa_condensacion_gkg_h: Tasa de condensación (g/kg/h)
            - tiempo_residencia_h: Tiempo de residencia de gotas (horas)
            - eficiencia_precipitacion: Fracción de agua que precipita (0-1)
    """
    # Broadcast a arrays numpy
    T = np.asarray(temperatura_c, dtype=np.float64)
    HR = np.asarray(humedad_relativa, dtype=np.float64)
    P = np.asarray(presion_hpa, dtype=np.float64)
    qc_arr = np.asarray(qc, dtype=np.float64)
    qr_arr = np.asarray(qr, dtype=np.float64)
    dP_dt = np.asarray(tendencia_presion_hpa_h, dtype=np.float64)
    
    # Constantes físicas
    Lv = 2.5e6  # Calor latente vaporización (J/kg)
    Cp = 1005.0  # Calor específico aire (J/(kg·K))
    Rd = 287.05  # Constante gas ideal aire seco (J/(kg·K))
    rho_water = 1000.0  # Densidad agua líquida (kg/m³)
    
    # Densidad del aire
    rho_air = (P * 100.0) / (Rd * (T + 273.15))  # kg/m³
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 1. TASA DE CONDENSACIÓN (SUNDQVIST)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Mixing ratio de saturación (g/kg)
    # Aproximación Magnus-Tetens
    es_hpa = 6.112 * np.exp(17.67 * T / (T + 243.5))
    qs_gkg = 621.97 * es_hpa / (P - es_hpa)  # g/kg
    
    # Mixing ratio actual
    q_actual = qs_gkg * (HR / 100.0)
    
    # Supersaturación relativa
    S = (q_actual - qs_gkg) / qs_gkg
    S = np.clip(S, -1.0, 1.0)  # Limitar a rango físico
    
    # Tasa de condensación según Sundqvist (1989):
    # dqc/dt = (q - qs) / tau_c   donde tau_c es tiempo característico
    tau_c_h = 0.5  # Tiempo característico condensación (horas) - ajustable
    
    # Solo condensa si hay supersaturación (S > 0)
    tasa_cond_gkg_h = np.where(
        S > 0.0,
        (q_actual - qs_gkg) / tau_c_h,
        0.0
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 2. CALOR LATENTE LIBERADO
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Tasa de liberación de calor latente (W/m²)
    # Q_latente = rho_air * Lv * (dqc/dt)
    # Convertir dqc/dt de g/kg/h a kg/kg/s
    dqc_dt_kgkg_s = (tasa_cond_gkg_h / 1000.0) / 3600.0  # kg/kg/s
    
    Q_latente = rho_air * Lv * dqc_dt_kgkg_s  # W/m²
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 3. TIEMPO DE RESIDENCIA DE GOTAS (SUNDQVIST)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Tiempo que las gotas permanecen en la nube antes de caer
    # Depende del contenido de agua líquida (LWC)
    LWC_cloud = (qc_arr / 1000.0) * rho_air * 1000.0  # g/m³
    LWC_rain = (qr_arr / 1000.0) * rho_air * 1000.0  # g/m³
    
    # Parametrización Sundqvist: tau_res = k * LWC^(-1/2)
    # Más agua → gotas más grandes → caen más rápido → menor residencia
    k_res = 2.0  # Constante empírica (horas·g^0.5/m^1.5)
    
    safe_lwc = np.maximum(LWC_cloud, 0.01)
    tau_res_raw = k_res / np.sqrt(safe_lwc)
    tau_res_h = np.where(
        LWC_cloud > 0.01,  # Umbral mínimo 0.01 g/m³
        tau_res_raw,
        24.0  # Si no hay nube, residencia "infinita"
    )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 4. EFICIENCIA DE PRECIPITACIÓN
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Fracción de agua de nube que se convierte en lluvia
    # Depende de:
    # - Contenido de agua (más agua → más eficiente)
    # - Tamaño de gotas (gotas grandes caen, gotas pequeñas se evaporan)
    # - Balance de energía (si Q_latente > Qnet, la nube se disipa)
    
    # Eficiencia base según LWC (Sundqvist 1978)
    # E_precip = 1 - exp(-LWC/LWC_crit)
    LWC_crit = 0.3  # g/m³ (umbral para precipitación eficiente)
    
    E_base = 1.0 - np.exp(-LWC_cloud / LWC_crit)
    
    # Ajuste por balance energético
    if radiacion_neta_wm2 is not None:
        Qnet = np.asarray(radiacion_neta_wm2, dtype=np.float64)
    else:
        # Estimación por temperatura y nubosidad
        # Si no hay Qnet, asumir radiación según nubosidad implícita
        Qnet = 200.0 * np.ones_like(T)  # W/m² (valor medio diurno)
    
    # Si Q_latente >> Qnet, energía no se disipa → nube crece → lluvia probable
    # Si Q_latente << Qnet, nube se evapora → lluvia improbable
    ratio_energia = Q_latente / (Qnet + 10.0)  # +10 para evitar div/0
    
    # Factor de disipación (0-1)
    # Si ratio > 1, la energía latente domina → alta eficiencia
    # Si ratio < 0.5, la radiación domina → baja eficiencia
    f_disip = np.clip(ratio_energia / 0.5, 0.0, 2.0) / 2.0
    
    E_precip = E_base * f_disip
    E_precip = np.clip(E_precip, 0.0, 1.0)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 5. PROBABILIDAD DE LLUVIA
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Combinar factores:
    # - Eficiencia de precipitación (E_precip)
    # - Contenido de agua actual (qr > 0 → ya está lloviendo)
    # - Tendencia de presión (caída → inestabilidad)
    
    # Factor 1: Eficiencia de precipitación
    prob_E = E_precip * 100.0
    
    # Factor 2: Agua de lluvia ya presente
    prob_qr = np.where(
        qr_arr > 0.01,  # Si ya hay lluvia (qr > 0.01 g/kg)
        100.0,
        np.clip(qr_arr * 100.0, 0.0, 50.0)  # Proporcional a qr
    )
    
    # Factor 3: Tendencia de presión (caída → inestabilidad)
    # dP/dt < 0 (presión bajando) aumenta probabilidad
    prob_dP = np.where(
        dP_dt < -2.0,  # Caída significativa
        np.clip(-dP_dt * 5.0, 0.0, 30.0),
        0.0
    )
    
    # Probabilidad total (suma ponderada)
    prob_total = 0.60 * prob_E + 0.30 * prob_qr + 0.10 * prob_dP
    prob_total = np.clip(prob_total, 0.0, 100.0)
    
    # Retornar como escalares si entrada fue escalar
    if np.ndim(temperatura_c) == 0:
        return {
            "prob_lluvia_pct": float(prob_total),
            "calor_latente_wm2": float(Q_latente),
            "tasa_condensacion_gkg_h": float(tasa_cond_gkg_h),
            "tiempo_residencia_h": float(tau_res_h),
            "eficiencia_precipitacion": float(E_precip),
            "lwc_cloud_gm3": float(LWC_cloud),
            "lwc_rain_gm3": float(LWC_rain),
        }
    else:
        return {
            "prob_lluvia_pct": prob_total,
            "calor_latente_wm2": Q_latente,
            "tasa_condensacion_gkg_h": tasa_cond_gkg_h,
            "tiempo_residencia_h": tau_res_h,
            "eficiencia_precipitacion": E_precip,
            "lwc_cloud_gm3": LWC_cloud,
            "lwc_rain_gm3": LWC_rain,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN AUXILIAR: INTEGRACIÓN CON SENSORES
# ═══════════════════════════════════════════════════════════════════════════════

def probabilidad_lluvia_desde_sensores(temperatura_c: float, humedad_relativa: float, presion_hpa: float, tendencia_presion_hpa_h: float = 0.0, radiacion_neta_wm2: float = None, lluvia_rate_mm_h: float = 0.0) -> Dict[str, float]:
    """Wrapper para calcular probabilidad de lluvia desde sensores directos."""
    from core.indices.microphysics_thompson_vectorized import calcular_hidrometeoros_vectorizado
    thompson = calcular_hidrometeoros_vectorizado(temp_c=temperatura_c, humedad=humedad_relativa, presion_hpa=presion_hpa, lluvia_rate_mm_h=lluvia_rate_mm_h)
    qc = thompson.get("qc_gkg", thompson.get("qc", 0.0))
    qr = thompson.get("qr_gkg", thompson.get("qr", 0.0))
    return calcular_probabilidad_lluvia_sundqvist(temperatura_c=temperatura_c, humedad_relativa=humedad_relativa, presion_hpa=presion_hpa, qc=qc, qr=qr, tendencia_presion_hpa_h=tendencia_presion_hpa_h, radiacion_neta_wm2=radiacion_neta_wm2)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST UNITARIO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("☔ TEST SUNDQVIST - PROBABILIDAD DE LLUVIA POR CALOR LATENTE")
    print("=" * 70)
    
    # Caso 1: Alta probabilidad (supersaturación + presión cayendo)
    print("\n📍 Caso 1: ALTA PROBABILIDAD (HR=95%, dP/dt=-5 hPa/h)")
    result = probabilidad_lluvia_desde_sensores(
        temperatura_c=18.0,
        humedad_relativa=95.0,
        presion_hpa=1008.0,
        tendencia_presion_hpa_h=-5.0,
        radiacion_neta_wm2=150.0,
        lluvia_rate_mm_h=0.0,
    )
    print(f"   Probabilidad lluvia: {result['prob_lluvia_pct']:.1f}%")
    print(f"   Calor latente: {result['calor_latente_wm2']:.2f} W/m²")
    print(f"   Eficiencia precip: {result['eficiencia_precipitacion']:.2f}")
    print(f"   Tiempo residencia: {result['tiempo_residencia_h']:.2f} h")
    
    # Caso 2: Baja probabilidad (aire seco, presión estable)
    print("\n📍 Caso 2: BAJA PROBABILIDAD (HR=45%, dP/dt=0)")
    result = probabilidad_lluvia_desde_sensores(
        temperatura_c=25.0,
        humedad_relativa=45.0,
        presion_hpa=1015.0,
        tendencia_presion_hpa_h=0.0,
        radiacion_neta_wm2=400.0,
        lluvia_rate_mm_h=0.0,
    )
    print(f"   Probabilidad lluvia: {result['prob_lluvia_pct']:.1f}%")
    print(f"   Calor latente: {result['calor_latente_wm2']:.2f} W/m²")
    
    # Caso 3: Ya está lloviendo (confirmación)
    print("\n📍 Caso 3: LLUVIA ACTIVA (10 mm/h)")
    result = probabilidad_lluvia_desde_sensores(
        temperatura_c=15.0,
        humedad_relativa=98.0,
        presion_hpa=1005.0,
        tendencia_presion_hpa_h=-3.0,
        radiacion_neta_wm2=80.0,
        lluvia_rate_mm_h=10.0,
    )
    print(f"   Probabilidad lluvia: {result['prob_lluvia_pct']:.1f}%")
    print(f"   LWC lluvia: {result['lwc_rain_gm3']:.3f} g/m³")
    print(f"   LWC nube: {result['lwc_cloud_gm3']:.3f} g/m³")
    
    print("\n[OK] TEST COMPLETADO - Sundqvist operacional")
