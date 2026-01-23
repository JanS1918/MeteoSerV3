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


def mrt_from_radiation_with_solar(ta_c: float, total_radiation_wm2: float, sun_altitude_deg: float = None,
                                  absorptivity: float = 0.7, proj_factor: float = 1.3,
                                  epsilon: float = 0.95) -> Optional[float]:
    """Estimate MRT (°C) using total radiation and optional sun altitude.

    Approach:
    - Split `total_radiation_wm2` into a direct component proportional to sin(sun_altitude)
      and the remainder as diffuse.
    - Compute an effective absorbed flux Q = absorptivity * (diffuse * 0.5 + direct * proj_factor)
      where diffuse is assumed isotropic (projected factor ~0.5) and direct uses a projection
      factor representing typical body/surface orientation.
    - Convert Q into an equivalent radiative temperature increase using Stefan-Boltzmann.

    Returns None on invalid inputs.
    """
    try:
        if ta_c is None or total_radiation_wm2 is None:
            return None
        TaK = float(ta_c) + 273.15
        total = max(0.0, float(total_radiation_wm2))
        # estimate direct fraction from sun altitude if available
        direct_frac = 0.0
        if sun_altitude_deg is not None:
            try:
                import math

                alt_rad = math.radians(float(sun_altitude_deg))
                direct_frac = max(0.0, math.sin(alt_rad))
            except Exception:
                direct_frac = 0.0
        # clamp
        direct_frac = min(1.0, max(0.0, direct_frac))
        direct = total * direct_frac
        diffuse = max(0.0, total - direct)
        # absorbed energy per unit area (W/m2)
        absorbed = float(absorptivity) * (diffuse * 0.5 + direct * float(proj_factor))
        eps = float(epsilon) if float(epsilon) > 0 else 0.95
        Tr4 = TaK ** 4 + absorbed / (eps * SIGMA)
        TrK = Tr4 ** 0.25
        return TrK - 273.15
    except Exception:
        return None
