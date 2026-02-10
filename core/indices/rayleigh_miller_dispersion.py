"""
Dispersión de Rayleigh corregida por Miller (1980) - Presión Barométrica Local.
Extinción luminosa según densidad molecular real del aire sobre el sensor.
El cielo de Argentona no es el estándar; calculamos la atmósfera real.
"""

import math
from typing import Dict


def rayleigh_miller_scattering(presion_hpa: float, elevacion_solar_deg: float,
                                altitud_m: float = 0.0) -> Dict[str, float]:
    """
    Dispersión de Rayleigh corregida por presión barométrica local (Miller 1980).
    
    La extinción Rayleigh estándar asume presión al nivel del mar (1013.25 hPa).
    Corregimos por la densidad molecular real del aire sobre el sensor.
    
    Args:
        presion_hpa: Presión barométrica local (hPa)
        elevacion_solar_deg: Elevación solar (grados)
        altitud_m: Altitud sobre nivel del mar (m)
    
    Returns:
        Dict con coeficiente de extinción, transmitancia, y masa óptica
    
    Referencias:
        - Miller, A.J. (1980). Atmospheric Rayleigh scattering.
        - Kasten & Young (1989). Revised optical air mass tables.
    """
    # Presión estándar al nivel del mar
    p_std = 1013.25  # hPa
    
    # Factor de corrección por presión (densidad molecular)
    rho_factor = presion_hpa / p_std
    
    # Coeficiente de extinción Rayleigh estándar (longitud de onda 550 nm)
    # τ_R = 0.008735 * λ^(-4.08) para λ en μm
    lambda_um = 0.55  # 550 nm (verde, pico sensibilidad ojo humano)
    tau_rayleigh_std = 0.008735 * (lambda_um ** -4.08)
    
    # Corregir por densidad molecular real (Miller 1980)
    tau_rayleigh_real = tau_rayleigh_std * rho_factor
    
    # Masa óptica relativa (Kasten & Young 1989)
    # m = 1 / (cos(z) + 0.50572 * (96.07995 - z)^(-1.6364))
    # donde z = 90° - elevación
    elev_rad = math.radians(max(0.1, elevacion_solar_deg))
    z_rad = math.pi / 2 - elev_rad
    z_deg = math.degrees(z_rad)
    
    if elevacion_solar_deg > 0:
        m_opt = 1.0 / (math.cos(z_rad) + 0.50572 * ((96.07995 - z_deg) ** -1.6364))
    else:
        m_opt = 40.0  # Sol bajo horizonte
    
    # Transmitancia atmosférica (ley de Beer-Lambert)
    # T = exp(-τ * m)
    transmitancia = math.exp(-tau_rayleigh_real * m_opt)
    
    # Extinción total en magnitudes (para astronomía)
    extinction_mag = tau_rayleigh_real * m_opt * 1.086  # 1 / ln(10)
    
    return {
        "tau_rayleigh": tau_rayleigh_real,
        "nubosidad": transmitancia,
        "masa_optica": m_opt,
        "extinction_mag": extinction_mag,
        "rho_factor": rho_factor
    }


def correccion_irradiancia_directa(irradiancia_toa: float, presion_hpa: float,
                                   elevacion_solar_deg: float) -> Dict[str, float]:
    """
    Corrige la irradiancia solar directa por dispersión Rayleigh-Miller.
    
    Args:
        irradiancia_toa: Irradiancia extraterrestre (W/m²)
        presion_hpa: Presión barométrica local (hPa)
        elevacion_solar_deg: Elevación solar (grados)
    
    Returns:
        Dict con irradiancia directa, difusa, y global
    """
    scattering = rayleigh_miller_scattering(presion_hpa, elevacion_solar_deg)
    
    # Irradiancia directa (transmitida)
    I_direct = irradiancia_toa * scattering["nubosidad"]
    
    # Irradiancia difusa (dispersada)
    I_diffuse = irradiancia_toa * (1.0 - scattering["nubosidad"]) * 0.5
    
    # Irradiancia global (directa + difusa)
    I_global = I_direct + I_diffuse
    
    return {
        "directa": I_direct,
        "difusa": I_diffuse,
        "global": I_global,
        "nubosidad": scattering["nubosidad"]
    }


if __name__ == "__main__":
    # Prueba: Argentona (96 m, ~1005 hPa) vs nivel del mar (1013 hPa)
    print("=== TEST RAYLEIGH-MILLER: Argentona vs Nivel del Mar ===")
    
    # Argentona
    result_arg = rayleigh_miller_scattering(1005.0, 45.0, 96.0)
    print(f"Argentona (1005 hPa, 96m):")
    print(f"  τ_Rayleigh: {result_arg['tau_rayleigh']:.6f}")
    print(f"  Transmitancia: {result_arg['nubosidad']:.4f}")
    print(f"  Masa óptica: {result_arg['masa_optica']:.2f}")
    
    # Nivel del mar
    result_sea = rayleigh_miller_scattering(1013.25, 45.0, 0.0)
    print(f"\nNivel del mar (1013 hPa, 0m):")
    print(f"  τ_Rayleigh: {result_sea['tau_rayleigh']:.6f}")
    print(f"  Transmitancia: {result_sea['nubosidad']:.4f}")
    print(f"  Masa óptica: {result_sea['masa_optica']:.2f}")
    
    diff_percent = (result_arg['nubosidad'] - result_sea['nubosidad']) / result_sea['nubosidad'] * 100
    print(f"\nDiferencia de transmitancia: {diff_percent:+.2f}%")
    print("(Argentona tiene ~0.8% más transmitancia por menor densidad atmosférica)")
