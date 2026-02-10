"""
Juez Termodinámico

Valida salidas contra límites físicos y/o referencias elite.
Modo no restrictivo: solo genera advertencias.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ThermoJudgeResult:
    ok: bool
    warnings: List[str]
    violations: List[str]


class ThermodynamicJudge:
    def __init__(self):
        # límites físicos base (ajustables)
        self.limits = {
            "temperatura": (-90.0, 70.0),
            "humedad": (0.0, 100.0),
            "presion": (870.0, 1085.0),  # hPa
            "viento": (0.0, 70.0),       # m/s
        }

    @staticmethod
    def clasificar_salida(nombre: str) -> Optional[str]:
        if not nombre:
            return None
        key = nombre.lower()
        if "temp" in key or "rocio" in key or "temperatura" in key:
            return "temperatura"
        if "hum" in key or "humidity" in key:
            return "humedad"
        if "presion" in key or "pressure" in key:
            return "presion"
        if "viento" in key or "wind" in key:
            return "viento"
        return None

    def check_limits(self, outputs: Dict[str, float]) -> ThermoJudgeResult:
        warnings: List[str] = []
        violations: List[str] = []
        if not outputs:
            return ThermoJudgeResult(ok=True, warnings=[], violations=[])

        for key, val in outputs.items():
            if key not in self.limits:
                continue
            try:
                v = float(val)
            except Exception:
                continue
            low, high = self.limits[key]
            if v < low or v > high:
                violations.append(f"{key} fuera de rango: {v} (lim {low}..{high})")

        ok = len(violations) == 0
        return ThermoJudgeResult(ok=ok, warnings=warnings, violations=violations)

    @staticmethod
    def penalty_factor(violations: List[str]) -> float:
        if not violations:
            return 1.0
        # Penalización suave por incoherencias físicas
        factor = 1.0 - (0.1 * len(violations))
        return max(0.5, factor)
