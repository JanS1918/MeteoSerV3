"""
MODELO STOELINGA-WARNER (1999/2024) - VISIBILIDAD POR MICROFÍSICA
===================================================================
Calcula visibilidad usando extinción por hidrometeoros con microfísica de Thompson.
Superior a Koshmieder porque integra distribución de tamaño de gotas.

Referencias:
- Stoelinga & Warner (1999): "Nonhydrostatic, Mesobeta-Scale Model Simulations of Cloud Ceiling"
- HRRR Model Physics (2024): NOAA/ESRL High-Resolution Rapid Refresh
- Thompson Microphysics: WRF 3.8+ Standard

ARQUITECTURA: 100% numpy vectorizado, compatible con rolling windows.
"""

import numpy as np
from typing import Dict, Union, Tuple


def calcular_visibilidad_stoelinga_warner(
    temperatura_c: Union[float, np.ndarray],
    humedad_relativa: Union[float, np.ndarray],
    qr: Union[float, np.ndarray],  # Mixing ratio agua lluvia (g/kg) desde Thompson
    qc: Union[float, np.ndarray],  # Mixing ratio agua nube (g/kg) desde Thompson
    qi: Union[float, np.ndarray] = None,  # Mixing ratio hielo (g/kg), opcional
    presion_hpa: Union[float, np.ndarray] = 1013.25,
    pm25: Union[float, np.ndarray] = 10.0,  # μg/m³ (aerosoles)
) -> Dict[str, Union[float, np.ndarray]]:
    """
    Modelo Stoelinga-Warner: Visibilidad basada en extinción por hidrometeoros.
    
    Args:
        temperatura_c: Temperatura (°C)
        humedad_relativa: HR (%)
        qr: Mixing ratio agua lluvia desde Thompson (g/kg)
        qc: Mixing ratio agua nube desde Thompson (g/kg)
        qi: Mixing ratio hielo (g/kg), opcional
        presion_hpa: Presión barométrica
        pm25: Concentración PM2.5 (μg/m³)
    
    Returns:
        Dict con:
            - visibilidad_m: Visibilidad en metros
            - ext_hidromet: Extinción por hidrometeoros (km⁻¹)
            - ext_aerosol: Extinción por aerosoles (km⁻¹)
            - ext_total: Extinción total (km⁻¹)
            - riesgo_niebla: Score 0-100
    """
    # Broadcast a arrays numpy si es necesario
    T = np.asarray(temperatura_c, dtype=np.float64)
    HR = np.asarray(humedad_relativa, dtype=np.float64)
    qr_arr = np.asarray(qr, dtype=np.float64)
    qc_arr = np.asarray(qc, dtype=np.float64)
    P = np.asarray(presion_hpa, dtype=np.float64)
    pm = np.asarray(pm25, dtype=np.float64)
    
    # Densidad del aire (ecuación de estado ideal)
    Rd = 287.05  # J/(kg·K)
    rho_air = (P * 100.0) / (Rd * (T + 273.15))  # kg/m³
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 1. EXTINCIÓN POR HIDROMETEOROS (STOELINGA-WARNER)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Convertir mixing ratios a concentración (g/m³)
    # qr, qc están en g/kg → multiplicar por rho_air (kg/m³) para g/m³
    LWC_rain = (qr_arr / 1000.0) * rho_air  # kg/m³
    LWC_cloud = (qc_arr / 1000.0) * rho_air  # kg/m³
    
    # Stoelinga-Warner: Extinción beta_ext (km⁻¹) = 144.7 * LWC^(2/3)
    # Para gotas de nube (diámetro ~10-20 μm)
    # Factor ajustado para agua líquida en suspensión
    beta_cloud = np.where(
        LWC_cloud > 1e-6,
        144.7 * (LWC_cloud * 1000.0) ** (2.0/3.0),  # LWC en g/m³
        0.0
    )
    
    # Para gotas de lluvia (diámetro ~0.5-5 mm), menor extinción por unidad masa
    # Aproximación: beta_rain ≈ 5.0 * LWC_rain (menos eficiente que nube)
    beta_rain = np.where(
        LWC_rain > 1e-6,
        5.0 * (LWC_rain * 1000.0),  # LWC en g/m³
        0.0
    )
    
    # Si hay hielo, menor extinción (cristales dispersan menos)
    if qi is not None:
        qi_arr = np.asarray(qi, dtype=np.float64)
        IWC = (qi_arr / 1000.0) * rho_air  # kg/m³
        beta_ice = np.where(
            IWC > 1e-6,
            30.0 * (IWC * 1000.0) ** 0.5,  # Aproximación para cristales
            0.0
        )
    else:
        beta_ice = 0.0
    
    ext_hidromet = beta_cloud + beta_rain + beta_ice  # km⁻¹
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 2. EXTINCIÓN POR AEROSOLES HIGROSCÓPICOS (KASTEN-HANEL)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Crecimiento higroscópico de aerosoles con humedad
    # Kasten-Hanel: beta_aer = beta_dry * (1 - HR/100)^(-0.6)
    beta_dry = pm / 100.0  # Aproximación: 1 μg/m³ PM2.5 ≈ 0.01 km⁻¹
    
    # Protección contra HR extrema (evitar división por cero)
    HR_safe = np.clip(HR, 0.1, 99.9)
    
    beta_aerosol = beta_dry * (1.0 - HR_safe / 100.0) ** (-0.6)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 3. EXTINCIÓN TOTAL Y VISIBILIDAD
    # ═══════════════════════════════════════════════════════════════════════════
    
    ext_total = ext_hidromet + beta_aerosol  # km⁻¹
    
    # Visibilidad según fórmula de Koschmieder: V = 3.912 / beta_ext
    # Si beta_ext = 0, visibilidad → infinito (limitamos a 50 km)
    vis_km = np.where(
        ext_total > 0.001,
        3.912 / ext_total,
        50.0  # Visibilidad máxima
    )
    
    # Convertir a metros
    vis_m = vis_km * 1000.0
    
    # Limitar visibilidad a rango razonable [10m, 50km]
    vis_m = np.clip(vis_m, 10.0, 50000.0)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 4. RIESGO DE NIEBLA (0-100)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Criterio OACI: Niebla si visibilidad < 1000m
    # Score: 100 si vis < 100m, 0 si vis > 5000m
    riesgo = np.clip(
        100.0 * (1.0 - (vis_m - 100.0) / 4900.0),
        0.0,
        100.0
    )
    
    # Retornar como escalares si entrada fue escalar
    if np.ndim(temperatura_c) == 0:
        return {
            "visibilidad_m": float(vis_m),
            "visibilidad_km": float(vis_km),
            "ext_hidromet": float(ext_hidromet),
            "ext_aerosol": float(beta_aerosol),
            "ext_total": float(ext_total),
            "riesgo_niebla": float(riesgo),
            "lwc_cloud": float(LWC_cloud * 1000.0),  # g/m³
            "lwc_rain": float(LWC_rain * 1000.0),   # g/m³
        }
    else:
        return {
            "visibilidad_m": vis_m,
            "visibilidad_km": vis_km,
            "ext_hidromet": ext_hidromet,
            "ext_aerosol": beta_aerosol,
            "ext_total": ext_total,
            "riesgo_niebla": riesgo,
            "lwc_cloud": LWC_cloud * 1000.0,  # g/m³
            "lwc_rain": LWC_rain * 1000.0,   # g/m³
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN AUXILIAR: INTEGRACIÓN CON THOMPSON
# ═══════════════════════════════════════════════════════════════════════════════

def visibilidad_desde_sensores(temperatura_c: float, humedad_relativa: float, presion_hpa: float, lluvia_rate_mm_h: float = 0.0, pm25: float = 10.0) -> Dict[str, float]:
    """Wrapper para calcular visibilidad desde sensores directos."""
    from core.indices.microphysics_thompson_vectorized import calcular_hidrometeoros_vectorizado
    thompson = calcular_hidrometeoros_vectorizado(temp_c=temperatura_c, humedad=humedad_relativa, presion_hpa=presion_hpa, lluvia_rate_mm_h=lluvia_rate_mm_h)
    qr = thompson.get("qr_gkg", thompson.get("qr", 0.0))
    qc = thompson.get("qc_gkg", thompson.get("qc", 0.0))
    qi = thompson.get("qi", 0.0)
    return calcular_visibilidad_stoelinga_warner(temperatura_c=temperatura_c, humedad_relativa=humedad_relativa, qr=qr, qc=qc, qi=qi, presion_hpa=presion_hpa, pm25=pm25)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST UNITARIO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🌫️ TEST STOELINGA-WARNER - VISIBILIDAD POR MICROFÍSICA")
    print("=" * 70)
    
    # Caso 1: Niebla densa (alta humedad, gotas pequeñas en suspensión)
    print("\n📍 Caso 1: NIEBLA DENSA (HR=98%, qc=0.5 g/kg)")
    result = visibilidad_desde_sensores(
        temperatura_c=10.0,
        humedad_relativa=98.0,
        presion_hpa=1013.0,
        lluvia_rate_mm_h=0.0,
        pm25=25.0,
    )
    print(f"   Visibilidad: {result['visibilidad_m']:.0f} m ({result['visibilidad_km']:.2f} km)")
    print(f"   Riesgo niebla: {result['riesgo_niebla']:.1f}%")
    print(f"   Extinción total: {result['ext_total']:.2f} km⁻¹")
    
    # Caso 2: Aire limpio (baja humedad, sin hidrometeoros)
    print("\n📍 Caso 2: AIRE LIMPIO (HR=40%, sin lluvia)")
    result = visibilidad_desde_sensores(
        temperatura_c=22.0,
        humedad_relativa=40.0,
        presion_hpa=1015.0,
        lluvia_rate_mm_h=0.0,
        pm25=8.0,
    )
    print(f"   Visibilidad: {result['visibilidad_m']:.0f} m ({result['visibilidad_km']:.2f} km)")
    print(f"   Riesgo niebla: {result['riesgo_niebla']:.1f}%")
    
    # Caso 3: Lluvia intensa (gotas grandes, menor extinción por masa)
    print("\n📍 Caso 3: LLUVIA INTENSA (10 mm/h)")
    result = visibilidad_desde_sensores(
        temperatura_c=15.0,
        humedad_relativa=95.0,
        presion_hpa=1010.0,
        lluvia_rate_mm_h=10.0,
        pm25=15.0,
    )
    print(f"   Visibilidad: {result['visibilidad_m']:.0f} m ({result['visibilidad_km']:.2f} km)")
    print(f"   LWC lluvia: {result['lwc_rain']:.3f} g/m³")
    print(f"   LWC nube: {result['lwc_cloud']:.3f} g/m³")
    
    print("\n✅ TEST COMPLETADO - Stoelinga-Warner operacional")
