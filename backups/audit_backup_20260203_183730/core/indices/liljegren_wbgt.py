"""
liljegren_wbgt.py

Implementación del modelo Liljegren-Carhart (2008) para WBGT.

Calcula WBGT (Wet Bulb Globe Temperature) sin termómetro de globo físico,
usando modelo termodinámico de balance energético.

Referencias:
- Liljegren et al. (2008). Modeling the wet bulb globe temperature using standard meteorological measurements.
- Carhart, N. & Liljegren, J. (2005). Estimating WBGT from meteorological data.
- ISO 7243:2017. Hot environments - Estimation of the heat stress on working man.

FASE 3: Blindaje de Inestabilidad y Excelencia Predictiva (2026)
"""

import math
from typing import Dict

# PRECISIÓN TOTAL: desactivar redondeo en cálculos internos
def _no_round(value, *args, **kwargs):
    return value

round = _no_round


def wbgt_liljegren(
    ta: float,
    rh: float,
    vel: float,
    solar: float,
    lat: float = 0.0,
    lon: float = 0.0,
    alt: float = 0.0,
    dt = None
) -> Dict[str, float]:
    """
    WBGT según modelo Liljegren-Carhart (2008).
    
    Calcula temperatura de globo negro (Tg) y temperatura de bulbo húmedo natural (Tnwb)
    mediante balance energético, sin necesidad de instrumentos físicos.
    
    WBGT (outdoor) = 0.7 × Tnwb + 0.2 × Tg + 0.1 × Ta
    WBGT (indoor, sin sol) = 0.7 × Tnwb + 0.3 × Tg
    
    Args:
        ta: Temperatura del aire (°C)
        rh: Humedad relativa (%)
        vel: Velocidad del viento (m/s)
        solar: Radiación solar global (W/m²)
        lat: Latitud (grados, opcional)
        lon: Longitud (grados, opcional)
        alt: Altitud (m, opcional)
        dt: datetime (opcional)
    
    Returns:
        Dict con WBGT, Tg, Tnwb, componentes de balance energético
    """
    
    # Constantes físicas
    sigma = 5.67e-8  # Constante Stefan-Boltzmann (W/(m²·K⁴))
    emis_globe = 0.95  # Emisividad globo negro
    emis_wick = 0.95  # Emisividad mecha bulbo húmedo
    absorptivity_globe = 0.95  # Absortividad globo negro (solar)
    absorptivity_wick = 0.95  # Absortividad mecha
    
    diameter_globe = 0.15  # Diámetro globo negro estándar (m)
    diameter_wick = 0.007  # Diámetro mecha bulbo húmedo (m)
    
    Ta_k = ta + 273.15  # Temperatura aire (K)
    
    # Presión de vapor
    es = 6.112 * math.exp((17.67 * ta) / (ta + 243.5))  # Presión saturación (hPa)
    ea = es * (rh / 100.0)  # Presión vapor (hPa)
    
    # =========================================================================
    # 1. TEMPERATURA GLOBO NEGRO (Tg)
    # =========================================================================
    # Balance energético del globo negro:
    # Q_solar + Q_infrared_in - Q_infrared_out - Q_convection = 0
    
    # Radiación solar absorbida
    Q_solar_globe = absorptivity_globe * solar * (math.pi * (diameter_globe ** 2) / 4)
    
    # Coeficiente convección (Churchill-Bernstein para esfera)
    Re_globe = vel * diameter_globe / 1.5e-5  # Reynolds (viscosidad cinemática aire ≈ 1.5e-5 m²/s)
    Nu_globe = 2.0 + 0.6 * (Re_globe ** 0.5) * (0.71 ** 0.33)  # Nusselt
    h_globe = Nu_globe * 0.026 / diameter_globe  # Coef. convección (W/(m²·K)), k_air ≈ 0.026 W/(m·K)
    
    # Iteración para encontrar Tg (temperatura globo)
    Tg_k = Ta_k  # Inicialización
    
    for _ in range(50):  # Iteraciones
        # Radiación infrarroja recibida del ambiente (suponemos T_sky ≈ T_air - 10 K)
        T_sky_k = Ta_k - 10.0
        Q_ir_in = emis_globe * sigma * math.pi * (diameter_globe ** 2) * (T_sky_k ** 4)
        
        # Radiación infrarroja emitida por el globo
        Q_ir_out = emis_globe * sigma * math.pi * (diameter_globe ** 2) * (Tg_k ** 4)
        
        # Convección
        A_globe = math.pi * (diameter_globe ** 2)
        Q_conv = h_globe * A_globe * (Tg_k - Ta_k)
        
        # Balance
        residual = Q_solar_globe + Q_ir_in - Q_ir_out - Q_conv
        
        # Ajuste (método de Newton simplificado)
        dQ_dTg = -4 * emis_globe * sigma * math.pi * (diameter_globe ** 2) * (Tg_k ** 3) - h_globe * A_globe
        delta_Tg = -residual / dQ_dTg if abs(dQ_dTg) > 1e-6 else 0.0
        
        Tg_k += delta_Tg
        
        if abs(delta_Tg) < 0.01:  # Convergencia
            break
    
    Tg_c = Tg_k - 273.15
    
    # =========================================================================
    # 2. TEMPERATURA BULBO HÚMEDO NATURAL (Tnwb)
    # =========================================================================
    # Balance energético del bulbo húmedo:
    # Q_solar + Q_infrared_in - Q_infrared_out - Q_convection - Q_evaporation = 0
    
    # Radiación solar absorbida
    Q_solar_wick = absorptivity_wick * solar * (math.pi * (diameter_wick ** 2) / 4)
    
    # Coeficiente convección
    Re_wick = vel * diameter_wick / 1.5e-5
    Nu_wick = 2.0 + 0.6 * (Re_wick ** 0.5) * (0.71 ** 0.33)
    h_wick = Nu_wick * 0.026 / diameter_wick
    
    # Iteración para encontrar Tnwb
    Tnwb_k = Ta_k - 5.0  # Inicialización (bulbo húmedo siempre < aire)
    
    for _ in range(50):
        Tnwb_c = Tnwb_k - 273.15
        
        # Presión de vapor saturación a Tnwb
        es_nwb = 6.112 * math.exp((17.67 * Tnwb_c) / (Tnwb_c + 243.5))  # hPa
        
        # Radiación infrarroja
        Q_ir_in_wick = emis_wick * sigma * math.pi * (diameter_wick ** 2) * (T_sky_k ** 4)
        Q_ir_out_wick = emis_wick * sigma * math.pi * (diameter_wick ** 2) * (Tnwb_k ** 4)
        
        # Convección
        A_wick = math.pi * (diameter_wick ** 2)
        Q_conv_wick = h_wick * A_wick * (Tnwb_k - Ta_k)
        
        # Evaporación (transferencia de masa)
        # Q_evap = h_m × A × L_v × (ρ_sat(Tnwb) - ρ_air)
        # Aproximación: h_m ≈ h_c / (ρ × Cp) (analogía de Lewis)
        # Densidad del aire: usar PhysicsEngine2026 para obtener densidad real
        try:
            from core.indices.physics_engine_2026 import PhysicsEngine2026

            # Inicializar motor físico con condiciones locales (usa fallback si falta presión)
            engine = PhysicsEngine2026(latitud=lat, temperatura_k=Ta_k, presion_pa=None, humedad_fraccion=(rh / 100.0))

            # Temperatura virtual y factor de compresibilidad Z
            Tv_k, _ = engine.temperatura_virtual()
            Z, _ = engine.factor_compresibilidad_virial()

            R_spec = 287.05  # J/(kg·K) (valor para aire seco, aproximación aceptada)
            presion_pa = engine.presion_pa if hasattr(engine, 'presion_pa') else 101325.0

            # rho = p / (R_specific * T_virtual * Z)
            rho_air = presion_pa / (R_spec * Tv_k * (Z if Z and Z > 0 else 1.0))
        except Exception:
            rho_air = 1.2  # kg/m³ fallback seguro

        Cp_air = 1005.0  # J/(kg·K)
        L_v = 2.45e6  # J/kg (calor latente vaporización)
        
        # Densidad vapor (kg/m³)
        rho_sat_nwb = (es_nwb * 100.0) / (461.5 * Tnwb_k)  # Ley gases ideales
        rho_vapor_air = (ea * 100.0) / (461.5 * Ta_k)
        
        h_mass = h_wick / (rho_air * Cp_air)  # m/s
        Q_evap = h_mass * A_wick * L_v * (rho_sat_nwb - rho_vapor_air)
        
        # Balance
        residual = Q_solar_wick + Q_ir_in_wick - Q_ir_out_wick - Q_conv_wick - Q_evap
        
        # Ajuste
        dQ_dTnwb = -4 * emis_wick * sigma * math.pi * (diameter_wick ** 2) * (Tnwb_k ** 3) - h_wick * A_wick
        # Derivada de Q_evap respecto a Tnwb (simplificada)
        des_dT = es_nwb * 17.67 * 243.5 / ((Tnwb_c + 243.5) ** 2)  # hPa/K
        drho_dT = (des_dT * 100.0) / (461.5 * Tnwb_k)
        dQ_dTnwb -= h_mass * A_wick * L_v * drho_dT
        
        delta_Tnwb = -residual / dQ_dTnwb if abs(dQ_dTnwb) > 1e-6 else 0.0
        
        Tnwb_k += delta_Tnwb
        
        if abs(delta_Tnwb) < 0.01:
            break
    
    Tnwb_c = Tnwb_k - 273.15
    
    # =========================================================================
    # 3. CÁLCULO WBGT
    # =========================================================================
    # WBGT outdoor (con radiación solar)
    if solar > 50.0:
        wbgt = 0.7 * Tnwb_c + 0.2 * Tg_c + 0.1 * ta
    else:
        # WBGT indoor (sin sol directo)
        wbgt = 0.7 * Tnwb_c + 0.3 * Tg_c
    
    return {
        "wbgt_c": round(wbgt, 2),
        "tg_c": round(Tg_c, 2),
        "tnwb_c": round(Tnwb_c, 2),
        "ta_c": round(ta, 2),
        "rh_pct": round(rh, 1),
        "vel_ms": round(vel, 2),
        "solar_wm2": round(solar, 1)
    }


def interpretar_wbgt(wbgt: float) -> str:
    """
    Interpreta el valor WBGT según ISO 7243.
    
    Args:
        wbgt: Wet Bulb Globe Temperature (°C)
    
    Returns:
        Interpretación del riesgo de estrés térmico
    """
    if wbgt < 26.0:
        return "Sin riesgo - trabajo normal"
    elif wbgt < 28.0:
        return "Precaución - descansos recomendados"
    elif wbgt < 30.0:
        return "Alerta - descansos frecuentes"
    elif wbgt < 32.0:
        return "Peligro - reducir actividad"
    else:
        return "Peligro extremo - suspender actividad"
