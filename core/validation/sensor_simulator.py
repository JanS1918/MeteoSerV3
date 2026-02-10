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
        # [FIX CRÍTICO] NO usar defaults ISA como valores "normales"
        # Estos SÓ1O se usan si hay historial de sensor, NO como fallback ciego
        self.default_values = {
            "temperatura": None,  # CRÍTICO: Sin sensor, retornar None (no 15.0°C falso)
            "humedad": None,      # CRÍTICO: Sin sensor, retornar None (no 50% falso)
            "presion": None,      # CRÍTICO: Usar ISA solo si hay historial de presión real
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
            from core.system.constants import ESTACION
            
            # B-1 CORRECCIÓN: Usar altitud real (124m SRTM) no 96m hardcodeado
            # Error anterior: 28m de diferencia causaba 3.0 hPa de error sistemático
            altitud = _safe_float(
                getattr(system, "sensores", {}).get("altitud", ESTACION.ALTITUD_SRTM),
                ESTACION.ALTITUD_SRTM
            )
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
            # C-1 CORRECCIÓN: Marcar valor como fallback ISA (no medición real)
            return {
                "valor": round(valor, 2),
                "error": err,
                "metodo": "ISA_DINAMICO",
                "motivo": razon,
                "es_real": False,  # NUEVO: Indica que NO es medición de sensor
                "confianza": 0.2,  # NUEVO: Baja confianza (es especulativo)
                "estado_fisico": "ESTIMADO",  # NUEVO: Trazabilidad física
                "advertencia": "[PHYSICS_FALLBACK] Sensor presión no disponible. "
                              "Valor es derivado de ISA, NO medición real.",
            }

        if sensor == "radiacion":
            # Intentar usar radiación teórica si existe
            indices = getattr(system, "indices", None)
            rad_teo = None
            try:
                if indices and hasattr(indices, "obtener_todos"):
                    datos = indices.obtener_todos()
                    rad_teo = datos.get("nubosidad")
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
