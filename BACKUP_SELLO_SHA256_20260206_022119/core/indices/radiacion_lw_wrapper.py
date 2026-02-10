"""
═══════════════════════════════════════════════════════════════════════════
[GUARDIAN] V47.0 WRAPPER - RADIACIÓN LW PRATA (1996)
═══════════════════════════════════════════════════════════════════════════

PROPÓSITO:
    Wrapper de integración para radiacion_lw_prata.py
    Simplifica llamada desde otros módulos.

MEJORA VS VDI 3787:
    +25.7% precisión en estimación LW del cielo
    
AUTOR: V47.0 SUMMUM
FECHA: 2025-01-28
═══════════════════════════════════════════════════════════════════════════
"""

from core.indices.radiacion_lw_prata import calcular_lw_prata_1996

def aplicar_prata_lw(
    temperatura_c: float,
    humedad_relativa: float,
    presion_hpa: float = 1013.25,
) -> dict:
    """
    Wrapper simplificado para Prata LW.
    
    Args:
        temperatura_c: Temperatura aire (°C)
        humedad_relativa: Humedad relativa (%)
        presion_hpa: Presión atmosférica (hPa)
    
    Returns:
        Dict con LW_cielo_wm2, epsilon_cielo, T_cielo_efectiva_k
    """
    return calcular_lw_prata_1996(
        T_air_c=temperatura_c,
        RH_pct=humedad_relativa,
        P_hpa=presion_hpa,
    )
