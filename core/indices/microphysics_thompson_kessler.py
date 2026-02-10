"""
Microfísica Thompson/Kessler V42.0

- Diferencia agua en suspensión (nube) y lluvia (precipitación)
- Ajuste de estabilidad por liberación de calor latente (Sundqvist)

NOTA: Implementación operacional para sensores de superficie.
"""

from __future__ import annotations

import math
from typing import Dict


def _es_tetens_hpa(temp_c: float) -> float:
    """Presión de vapor de saturación (hPa) - Tetens."""
    return 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))


def calcular_hidrometeoros(
    temp_c: float,
    humedad: float,
    presion_hpa: float,
    lluvia_rate_mm_h: float | None = None,
    tau_h: float = 1.0,
) -> Dict[str, float]:
    """
    Thompson/Kessler simplificado para hidrometeoros.

    Retorna:
    - qv: vapor específico (g/kg)
    - qc: agua en nube (g/kg)
    - qr: agua de lluvia (g/kg)
    - fase: 0 (líquido) a 1 (hielo)
    - fall_speed_ms: velocidad terminal media (m/s)
    - latent_heating_k_h: calentamiento latente estimado (K/h)
    """
    presion_hpa = max(1.0, presion_hpa)
    rh = max(0.0, min(100.0, humedad)) / 100.0

    es = _es_tetens_hpa(temp_c)
    qvs = 0.62198 * es / max(1e-6, (presion_hpa - es))  # kg/kg
    qv = rh * qvs

    # Kessler: condensación cuando RH alto (operacional)
    qc = 0.0
    if humedad >= 95.0:
        qc = min(2.0e-3, (humedad - 95.0) / 5.0 * 2.0e-3)  # kg/kg

    # Conversión a lluvia basada en tasa observada
    qr = 0.0
    if lluvia_rate_mm_h is not None and lluvia_rate_mm_h > 0:
        # Aproximación: 1 mm/h ~ 2.78e-7 m/s
        rain_ms = (lluvia_rate_mm_h / 1000.0) / 3600.0
        # Asumimos Vt ~ 5 m/s, ρw ~ 1000 kg/m³
        qr = min(5.0e-3, (rain_ms * 1000.0) / 5.0)  # kg/kg

    # Velocidad terminal media (Thompson/Kessler): función de tasa de lluvia
    fall_speed = 0.0
    if lluvia_rate_mm_h is not None and lluvia_rate_mm_h > 0:
        # Diámetro medio Marshall-Palmer (mm) aproximado
        dm_mm = 1.77 * (lluvia_rate_mm_h ** 0.12)
        # Velocidad terminal (m/s) aproximada
        fall_speed = 9.65 - 10.3 * math.exp(-0.6 * dm_mm)
        fall_speed = max(0.5, min(9.5, fall_speed))

    # Fracción de hielo por temperatura
    fase_hielo = 0.0
    if temp_c <= -10:
        fase_hielo = 1.0
    elif temp_c < 0:
        fase_hielo = abs(temp_c) / 10.0

    # Calentamiento latente (Sundqvist): liberación por condensación
    tau_h = max(0.1, float(tau_h))
    q_cond = max(0.0, qc + qr)
    L_v = 2.5e6
    Cp = 1005.0
    delta_theta = (L_v / Cp) * q_cond
    latent_heating_k_h = delta_theta / tau_h

    return {
        "qv_gkg": qv * 1000.0,
        "qc_gkg": qc * 1000.0,
        "qr_gkg": qr * 1000.0,
        "fase_hielo": round(fase_hielo, 3),
        "fall_speed_ms": round(fall_speed, 3),
        "latent_heating_k_h": round(latent_heating_k_h, 3),
    }


def ajustar_estabilidad_sundqvist(
    qc_gkg: float,
    qr_gkg: float,
) -> Dict[str, float]:
    """
    Ajuste de estabilidad (Sundqvist) por liberación de calor latente.

    Devuelve:
    - delta_theta_k: incremento térmico equivalente (K)
    - factor_estabilidad: multiplicador de inestabilidad (0-0.5)
    """
    # Convertir g/kg a kg/kg
    q_cond = (max(0.0, qc_gkg) + max(0.0, qr_gkg)) / 1000.0

    # Calor latente de condensación
    L_v = 2.5e6  # J/kg
    Cp = 1005.0  # J/kg/K

    delta_theta = (L_v / Cp) * q_cond
    factor = min(0.5, max(0.0, delta_theta / 10.0))

    return {
        "delta_theta_k": round(delta_theta, 3),
        "factor_estabilidad": round(factor, 3),
    }
