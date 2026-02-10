"""
Comparador de presiones de saturación: Hyland-Wexler vs Virial+Greenspan.
Genera salida CSV (T(°C), hyland_Pa, virial_greenspan_Pa, pct_diff_virial)
"""

from core.indices.environmental_indices import (
    saturacion_vapor_hyland_wexler,
    saturacion_vapor_virial_greenspan,
)

import math


def main():
    p_atm = 101325.0
    temps = [t for t in range(-40, 61)]  # -40..60 step 1
    out_path = "data/saturation_comparison_20260131.csv"
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("T_C,hyland_Pa,virial_greenspan_Pa,pct_diff_virial\n")
        for t in temps:
            try:
                h = float(saturacion_vapor_hyland_wexler(t, p_atm))
            except Exception:
                h = float('nan')
            try:
                v = float(saturacion_vapor_virial_greenspan(t, p_atm))
            except Exception:
                v = float('nan')
            pct_v = (v - h) / h * 100.0 if h and not math.isnan(h) else float('nan')
            fh.write(f"{t},{h:.6f},{v:.6f},{pct_v:.6f}\n")

    print(f"Wrote comparison CSV to {out_path}")


if __name__ == '__main__':
    main()
