"""
SIMULADOR DE SENSORES V34.1
Genera valores de respaldo cuando un sensor falla.
- Usa histórico local + física básica + fallback ISA
- Calcula error estimado (±X.XX)
"""

from __future__ import annotations

import math
from collections import deque
from typing import Dict, Optional, Tuple


def _safe_float(value: Optional[float], default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _std(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(var)


def _trend(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return values[-1] - values[-2]


class SensorSimulator:
    """Simula valores para sensores con fallo detectado."""

    def __init__(self):
        self.default_values = {
            "temperatura": 15.0,
            "humedad": 50.0,
            "presion": 1013.25,
            "viento": 0.0,
            "lluvia": 0.0,
            "radiacion": 0.0,
            "uv": 0.0,
        }

    def _historial(self, system, sensor: str, max_n: int = 20) -> list[float]:
        hist = getattr(system, "historial_sensores", {}).get(sensor, [])
        values = [float(v) for _, v in hist[-max_n:] if isinstance(v, (int, float))]
        return values

    def _estimate_error(self, values: list[float], min_err: float = 0.2) -> float:
        err = _std(values)
        if err <= 0:
            err = min_err
        return round(err, 2)

    def _fallback_isa(self, system) -> Tuple[float, str]:
        try:
            from core.atmosphere.isa_calculator import presion_isa_fallback
            altitud = _safe_float(getattr(system, "sensores", {}).get("altitud", 96.0), 96.0)
            presion_ultima = getattr(system, "sensores", {}).get("presion_ultima_valida")
            presion_fallback, razon = presion_isa_fallback(altitud, presion_ultima)
            return float(presion_fallback), razon
        except Exception:
            return self.default_values["presion"], "fallback_isa_default"

    def simulate(self, system, sensor: str) -> Dict[str, float | str]:
        sensor = (sensor or "").lower().strip()
        hist = self._historial(system, sensor)
        last = hist[-1] if hist else None
        trend = _trend(hist)
        base = last if last is not None else self.default_values.get(sensor, 0.0)

        motivo = "historial_local"
        if sensor == "presion":
            valor, razon = self._fallback_isa(system)
            err = self._estimate_error(hist, min_err=0.5)
            return {
                "valor": round(valor, 2),
                "error": err,
                "metodo": "ISA_DINAMICO",
                "motivo": razon,
            }

        if sensor == "radiacion":
            # Intentar usar radiación teórica si existe
            indices = getattr(system, "indices", None)
            rad_teo = None
            try:
                if indices and hasattr(indices, "obtener_todos"):
                    datos = indices.obtener_todos()
                    rad_teo = datos.get("radiacion_teorica")
                    if isinstance(rad_teo, dict):
                        rad_teo = rad_teo.get("valor")
            except Exception:
                rad_teo = None
            if rad_teo is not None:
                valor = _safe_float(rad_teo, self.default_values["radiacion"])
                err = max(self._estimate_error(hist, min_err=5.0), 5.0)
                return {
                    "valor": round(valor, 2),
                    "error": err,
                    "metodo": "RADIACION_TEORICA",
                    "motivo": "simulacion_teorica",
                }

        # Simulación simple por tendencia
        valor_sim = _safe_float(base, 0.0) + trend * 0.6
        err = self._estimate_error(hist)
        return {
            "valor": round(valor_sim, 2),
            "error": err,
            "metodo": "TENDENCIA_LOCAL",
            "motivo": motivo,
        }
