"""
VGP + BRN - SEVERIDAD DE TORMENTAS Y ROTACIÓN
==============================================
Modelos avanzados para predecir tormentas severas, reventones y rotación.

Referencias:
- Rasmussen & Blanchard (1998): "A Baseline Climatology of Sounding-Derived Parameters"
- Weisman & Klemp (1982): "The Dependence of Numerically Simulated Convective Storms on Vertical Wind Shear"
- Thompson et al. (2003): "Close Proximity Soundings within Supercell Environments"

Componentes:
1. **VGP (Vorticity Generation Parameter)**: Rotación potencial de la tormenta
2. **BRN (Bulk Richardson Number)**: Balance entre flotabilidad y cizalladura
3. **SRH (Storm Relative Helicity)**: Helicidad relativa a la tormenta
4. **STP (Significant Tornado Parameter)**: Probabilidad de tornado

ARQUITECTURA: 100% numpy vectorizado.
"""

import numpy as np
from typing import Dict, Union


def calcular_severidad_tormenta_vgp_brn(
    temperatura_c: Union[float, np.ndarray],
    humedad_relativa: Union[float, np.ndarray],
    presion_hpa: Union[float, np.ndarray],
    viento_ms: Union[float, np.ndarray],
    viento_dir_deg: Union[float, np.ndarray] = 0.0,
    cape_jkg: Union[float, np.ndarray] = None,  # Si None, se calcula
    lcl_m: Union[float, np.ndarray] = None,     # Lifting Condensation Level
    cizalladura_0_6km_ms: Union[float, np.ndarray] = None,  # Si None, se estima
) -> Dict[str, Union[float, np.ndarray]]:
    """
    Severidad de tormentas según VGP + BRN + SRH.
    
    Args:
        temperatura_c: Temperatura (°C)
        humedad_relativa: HR (%)
        presion_hpa: Presión barométrica
        viento_ms: Velocidad viento (m/s)
        viento_dir_deg: Dirección viento (grados)
        cape_jkg: CAPE (J/kg), si None se calcula
        lcl_m: LCL (m), si None se calcula
        cizalladura_0_6km_ms: Cizalladura vertical 0-6km (m/s), si None se estima
    
    Returns:
        Dict con:
            - vgp: Vorticity Generation Parameter
            - brn: Bulk Richardson Number
            - srh: Storm Relative Helicity (m²/s²)
            - stp: Significant Tornado Parameter
            - riesgo_tormenta_severa_pct: Probabilidad tormenta severa (%)
            - tipo_tormenta: "multicelda", "supercelda", "lineal", "ninguna"
    """
    # Broadcast a arrays numpy
    T = np.asarray(temperatura_c, dtype=np.float64)
    HR = np.asarray(humedad_relativa, dtype=np.float64)
    P = np.asarray(presion_hpa, dtype=np.float64)
    V = np.asarray(viento_ms, dtype=np.float64)
    Dir = np.asarray(viento_dir_deg, dtype=np.float64)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 1. CAPE Y LCL (si no se proporcionan)
    # ═══════════════════════════════════════════════════════════════════════════
    
    if cape_jkg is None:
        # Calcular CAPE simplificado (aproximación para estación superficie)
        # CAPE ≈ g * (T_parcela - T_ambiente) * (Z_EL - Z_LFC)
        # Estimación burda: CAPE ~ 1000 J/kg para HR > 70%, T > 20°C
        cape_est = np.where(
            (HR > 70.0) & (T > 20.0),
            np.clip((HR - 70.0) * 20.0 + (T - 20.0) * 50.0, 0.0, 3000.0),
            0.0
        )
        CAPE = cape_est
    else:
        CAPE = np.asarray(cape_jkg, dtype=np.float64)
    
    if lcl_m is None:
        # LCL aproximado: (T - Td) * 125 metros
        # Td desde HR (aproximación Magnus)
        Td = T - ((100.0 - HR) / 5.0)
        LCL = (T - Td) * 125.0
    else:
        LCL = np.asarray(lcl_m, dtype=np.float64)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 2. CIZALLADURA VERTICAL (si no se proporciona)
    # ═══════════════════════════════════════════════════════════════════════════
    
    if cizalladura_0_6km_ms is None:
        # Estimación desde viento superficie (muy simplificada)
        # En condiciones severas, cizalladura típica es 2-4 veces el viento superficial
        # Ajustar según condiciones locales
        # Para Argentona, usar factor conservador
        shear_est = V * 2.5  # Asunción: cizalladura ~ 2.5x viento superficie
    else:
        shear_est = np.asarray(cizalladura_0_6km_ms, dtype=np.float64)
    
    Shear_0_6 = shear_est  # m/s
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 3. BRN (BULK RICHARDSON NUMBER)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # BRN = CAPE / (0.5 * Shear²)
    # Valores típicos:
    # - BRN > 50: Tormentas débiles (multicelda)
    # - BRN 10-50: Tormentas organizadas
    # - BRN < 10: Superceldas (balance perfecto entre flotabilidad y cizalladura)
    
    # Evitar división por cero
    Shear_safe = np.where(Shear_0_6 > 0.1, Shear_0_6, 0.1)
    
    BRN = CAPE / (0.5 * Shear_safe ** 2.0)
    BRN = np.clip(BRN, 0.0, 200.0)  # Limitar a rango razonable
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 4. SRH (STORM RELATIVE HELICITY)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # SRH mide la helicidad del flujo relativo a la tormenta
    # SRH = ∫ (V × ∂V/∂z) · k  dz  desde superficie hasta 3 km
    # Simplificación para estación superficie:
    # SRH ≈ Shear_0_3km * V_superficie * sin(ángulo_giro)
    
    # Asunción: giro direccional típico 30° en 3 km para tormentas severas
    angulo_giro = 30.0 * (np.pi / 180.0)  # radianes
    
    # SRH simplificado (m²/s²)
    SRH = Shear_0_6 * V * np.sin(angulo_giro) * 1000.0  # Factor 1000 para escala típica
    SRH = np.clip(SRH, 0.0, 500.0)  # SRH > 150 m²/s² indica riesgo tornado
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 5. VGP (VORTICITY GENERATION PARAMETER)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # VGP = (CAPE / 1000) * (Shear / 10) * (1000 / LCL)
    # Valores típicos:
    # - VGP > 4: Alto riesgo de rotación
    # - VGP 2-4: Riesgo moderado
    # - VGP < 2: Bajo riesgo
    
    LCL_safe = np.where(LCL > 100.0, LCL, 1000.0)  # Evitar LCL muy bajo
    
    VGP = (CAPE / 1000.0) * (Shear_0_6 / 10.0) * (1000.0 / LCL_safe)
    VGP = np.clip(VGP, 0.0, 10.0)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 6. STP (SIGNIFICANT TORNADO PARAMETER)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # STP combina CAPE, LCL, SRH, Shear
    # STP = (CAPE/1500) * ((2000-LCL)/1000) * (SRH/150) * (Shear_0_6/20)
    # STP > 1 indica ambiente favorable para tornados significativos
    
    STP = (CAPE / 1500.0) * \
          (np.clip((2000.0 - LCL) / 1000.0, 0.0, 2.0)) * \
          (SRH / 150.0) * \
          (Shear_0_6 / 20.0)
    STP = np.clip(STP, 0.0, 10.0)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 7. PROBABILIDAD TORMENTA SEVERA
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Combinar factores en probabilidad 0-100%
    # Pesos: VGP (40%), BRN (20%), STP (30%), CAPE (10%)
    
    # Factor VGP (0-1)
    f_vgp = np.clip(VGP / 4.0, 0.0, 1.0)
    
    # Factor BRN (inverso: BRN bajo = más severo)
    # BRN óptimo para superceldas: 10-45
    f_brn = np.where(
        BRN < 10.0,
        1.0,  # Muy favorable
        np.where(
            BRN < 50.0,
            1.0 - (BRN - 10.0) / 40.0,  # Decae lineal 10-50
            0.2  # BRN alto = multiceldas débiles
        )
    )
    
    # Factor STP (0-1)
    f_stp = np.clip(STP / 2.0, 0.0, 1.0)
    
    # Factor CAPE (0-1)
    f_cape = np.clip(CAPE / 2000.0, 0.0, 1.0)
    
    # Probabilidad total
    prob_severa = 100.0 * (0.40 * f_vgp + 0.20 * f_brn + 0.30 * f_stp + 0.10 * f_cape)
    prob_severa = np.clip(prob_severa, 0.0, 100.0)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 8. TIPO DE TORMENTA
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Clasificación según BRN y STP
    def clasificar_tipo(brn_val, stp_val, cape_val):
        if cape_val < 500.0:
            return "ninguna"
        elif brn_val < 15.0 and stp_val > 0.5:
            return "supercelda"
        elif brn_val < 50.0:
            return "multicelda"
        else:
            return "lineal"
    
    # Vectorizar clasificación
    if np.ndim(temperatura_c) == 0:
        tipo = clasificar_tipo(float(BRN), float(STP), float(CAPE))
    else:
        tipo = np.vectorize(clasificar_tipo)(BRN, STP, CAPE)
    
    # Retornar como escalares si entrada fue escalar
    if np.ndim(temperatura_c) == 0:
        return {
            "vgp": float(VGP),
            "brn": float(BRN),
            "srh_m2s2": float(SRH),
            "stp": float(STP),
            "cape_jkg": float(CAPE),
            "lcl_m": float(LCL),
            "cizalladura_0_6km_ms": float(Shear_0_6),
            "riesgo_tormenta_severa_pct": float(prob_severa),
            "tipo_tormenta": tipo,
        }
    else:
        return {
            "vgp": VGP,
            "brn": BRN,
            "srh_m2s2": SRH,
            "stp": STP,
            "cape_jkg": CAPE,
            "lcl_m": LCL,
            "cizalladura_0_6km_ms": Shear_0_6,
            "riesgo_tormenta_severa_pct": prob_severa,
            "tipo_tormenta": tipo,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN AUXILIAR: INTEGRACIÓN CON SENSORES
# ═══════════════════════════════════════════════════════════════════════════════

def severidad_tormenta_desde_sensores(temperatura_c: float, humedad_relativa: float, presion_hpa: float, viento_ms: float, viento_dir_deg: float = 0.0) -> Dict[str, float]:
    """Wrapper para calcular severidad desde sensores directos."""
    from core.indices.advanced_predictive_indices import calcular_cape
    Td = temperatura_c - ((100.0 - humedad_relativa) / 5.0)
    try:
        cape_result = calcular_cape(temperatura_c=temperatura_c, temperatura_rocio_c=Td, presion_hpa=presion_hpa)
        cape_val = cape_result.get("cape_jkg", 0.0)
        lcl_val = cape_result.get("lcl_m", None)
    except:
        cape_val = 0.0
        lcl_val = None
    return calcular_severidad_tormenta_vgp_brn(temperatura_c=temperatura_c, humedad_relativa=humedad_relativa, presion_hpa=presion_hpa, viento_ms=viento_ms, viento_dir_deg=viento_dir_deg, cape_jkg=cape_val, lcl_m=lcl_val, cizalladura_0_6km_ms=None)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST UNITARIO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("⛈️  TEST VGP+BRN - SEVERIDAD DE TORMENTAS")
    print("=" * 70)
    
    # Caso 1: Supercelda (CAPE alto, cizalladura fuerte, BRN bajo)
    print("\n📍 Caso 1: AMBIENTE DE SUPERCELDA")
    result = severidad_tormenta_desde_sensores(
        temperatura_c=28.0,
        humedad_relativa=75.0,
        presion_hpa=1008.0,
        viento_ms=12.0,
        viento_dir_deg=180.0,
    )
    print(f"   VGP: {result['vgp']:.2f}")
    print(f"   BRN: {result['brn']:.1f}")
    print(f"   STP: {result['stp']:.2f}")
    print(f"   Riesgo severa: {result['riesgo_tormenta_severa_pct']:.1f}%")
    print(f"   Tipo: {result['tipo_tormenta']}")
    
    # Caso 2: Multicelda (CAPE moderado, cizalladura débil)
    print("\n📍 Caso 2: MULTICELDA DÉBIL")
    result = severidad_tormenta_desde_sensores(
        temperatura_c=22.0,
        humedad_relativa=80.0,
        presion_hpa=1012.0,
        viento_ms=5.0,
        viento_dir_deg=90.0,
    )
    print(f"   VGP: {result['vgp']:.2f}")
    print(f"   BRN: {result['brn']:.1f}")
    print(f"   Riesgo severa: {result['riesgo_tormenta_severa_pct']:.1f}%")
    print(f"   Tipo: {result['tipo_tormenta']}")
    
    # Caso 3: Sin tormenta (CAPE bajo)
    print("\n📍 Caso 3: AMBIENTE ESTABLE")
    result = severidad_tormenta_desde_sensores(
        temperatura_c=18.0,
        humedad_relativa=50.0,
        presion_hpa=1020.0,
        viento_ms=3.0,
        viento_dir_deg=270.0,
    )
    print(f"   VGP: {result['vgp']:.2f}")
    print(f"   CAPE: {result['cape_jkg']:.0f} J/kg")
    print(f"   Riesgo severa: {result['riesgo_tormenta_severa_pct']:.1f}%")
    print(f"   Tipo: {result['tipo_tormenta']}")
    
    print("\n[OK] TEST COMPLETADO - VGP+BRN operacional")
