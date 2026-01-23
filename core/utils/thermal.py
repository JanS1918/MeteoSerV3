"""Utilities for thermal estimations (MRT etc.).

This provides a pragmatic mean radiant temperature estimator derived from
absorbed radiant flux. It's intentionally simple and robust for use when no
direct MRT sensor is available.
"""
from typing import Optional

SIGMA = 5.670374419e-8  # Stefan-Boltzmann constant W/m2/K4


def mrt_from_radiation(ta_c: float, radiation_wm2: float, absorptivity: float = 0.7, epsilon: float = 0.95) -> Optional[float]:
    """Estimate mean radiant temperature (MRT) in °C from air temperature and radiant flux.

    Method:
    - Assumes additional absorbed radiant power per unit area Q = radiation * absorptivity.
    - Approximates the effective radiant temperature by solving:
        epsilon * sigma * Tr^4 = epsilon * sigma * Ta^4 + Q
      so Tr = ((Ta^4 + Q/(epsilon*sigma)) )^(1/4)

    This is a pragmatic estimator useful as a fallback when direct MRT measurements
    are unavailable. Accuracy depends on how representative `radiation_wm2` and
    `absorptivity` are for the surroundings and clothing exposure.

    Returns None if inputs are invalid.
    """
    try:
        if ta_c is None or radiation_wm2 is None:
            return None
        TaK = float(ta_c) + 273.15
        Q = max(0.0, float(radiation_wm2)) * float(absorptivity)
        # Prevent division by zero
        eps = float(epsilon) if float(epsilon) > 0 else 0.95
        Tr4 = TaK ** 4 + Q / (eps * SIGMA)
        TrK = Tr4 ** 0.25
        return TrK - 273.15
    except Exception:
        return None
