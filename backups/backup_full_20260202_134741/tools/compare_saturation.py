"""
Comparador de presiones de saturación: Hyland-Wexler vs Virial+Greenspan vs Magnus
Genera salida CSV (T(°C), hyland_Pa, virial_greenspan_Pa, magnus_Pa, pct_diff_virial, pct_diff_magnus)
"""

from core.indices.environmental_indices import (
    saturacion_vapor_hyland_wexler,
    saturacion_vapor_virial_greenspan,
)

import math


def magnus_saturation_pa(temp_c: float) -> float:
    # Magnus formula common form returns kPa; convert to Pa
    es_kpa = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    return es_kpa * 1000.0


def main():
    p_atm = 101325.0
    temps = [t for t in range(-40, 61)]  # -40..60 step 1
    out_path = "data/saturation_comparison_20260131.csv"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("T_C,hyland_Pa,virial_greenspan_Pa,magnus_Pa,pct_diff_virial,pct_diff_magnus\n")
        for t in temps:
            try:
                h = float(saturacion_vapor_hyland_wexler(t, p_atm))
            except Exception:
                h = float('nan')
            try:
                v = float(saturacion_vapor_virial_greenspan(t, p_atm))
            except Exception:
                v = float('nan')
            try:
                m = float(magnus_saturation_pa(t))
            except Exception:
                m = float('nan')

            pct_v = (v - h) / h * 100.0 if h and not math.isnan(h) else float('nan')
            pct_m = (m - h) / h * 100.0 if h and not math.isnan(h) else float('nan')
            fh.write(f"{t},{h:.6f},{v:.6f},{m:.6f},{pct_v:.6f},{pct_m:.6f}\n")

    print(f"Wrote comparison CSV to {out_path}")


if __name__ == '__main__':
    main()
