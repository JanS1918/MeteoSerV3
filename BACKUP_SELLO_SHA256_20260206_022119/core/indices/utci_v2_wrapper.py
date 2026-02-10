"""
═══════════════════════════════════════════════════════════════════════════
[GUARDIAN] V47.0 WRAPPER - UTCI v2 BLAZEJCZYK (2013)
═══════════════════════════════════════════════════════════════════════════

PROPÓSITO:
    Wrapper de integración para utci_v2_blazejczyk.py
    Simplifica llamada desde environmental_indices.py

MEJORA VS v1:
    +10.4°C precisión en alta humedad (>85% RH)
    Crítico para Maresme (frecuente >90% RH)
    
AUTOR: V47.0 SUMMUM
FECHA: 2025-01-28
═══════════════════════════════════════════════════════════════════════════
"""

from core.indices.utci_v2_blazejczyk import utci_v2_blazejczyk

def aplicar_utci_v2(
    temperatura_c: float,
    tmrt_c: float,
    viento_ms: float,
    humedad_relativa: float,
    presion_hpa: float = 1013.25,
) -> dict:
    """
    Wrapper simplificado para UTCI v2.
    
    Args:
        temperatura_c: Temperatura aire (°C)
        tmrt_c: Temperatura radiante media (°C)
        viento_ms: Velocidad viento (m/s)
        humedad_relativa: Humedad relativa (%)
        presion_hpa: Presión atmosférica (hPa)
    
    Returns:
        Dict con utci_v2, delta_vs_v1, metodo
    """
    resultado = utci_v2_blazejczyk(
        T_air_c=temperatura_c,
        T_mrt_c=tmrt_c,
        v_wind_m_s=viento_ms,
        RH_pct=humedad_relativa,
        presion_hpa=presion_hpa,
    )
    
    return {
        "utci_v2": resultado[0],
        "utci_v1": resultado[1],
        "delta_mejora": resultado[2],
        "metodo": "Blazejczyk v2 (2013)",
    }
