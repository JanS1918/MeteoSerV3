from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Optional


@dataclass
class SensorSelfCheck:
    estado: str
    confianza_pct: float
    sigma: float
    baseline_ready: bool
    delta: Optional[float]
    valor: float


class HardwareSelfValidator:
    """
    Validador auto-adaptativo por hardware.

    - Aprende el comportamiento real del sensor (baseline).
    - Detecta desviaciones rápidas (degradación o fallas).
    - Genera confianza dinámica sin depender de ISO.
    """

    def __init__(self,
                 sensores=None,
                 max_historia: int = 120,
                 min_muestras: int = 30):
        self.sensores = sensores or ["temperatura", "humedad", "presion", "radiacion", "viento"]
        self.max_historia = int(max_historia)
        self.min_muestras = int(min_muestras)
        self._hist: Dict[str, Deque[float]] = {s: deque(maxlen=self.max_historia) for s in self.sensores}
        self._delta_hist: Dict[str, Deque[float]] = {s: deque(maxlen=self.max_historia) for s in self.sensores}
        self._baseline_std: Dict[str, Optional[float]] = {s: None for s in self.sensores}

    def _update_baseline(self, sensor: str):
        deltas = self._delta_hist.get(sensor, deque())
        if len(deltas) < self.min_muestras:
            return
        mean = sum(deltas) / len(deltas)
        var = sum((d - mean) ** 2 for d in deltas) / len(deltas)
        self._baseline_std[sensor] = var ** 0.5

    def process_snapshot(self, datos: Dict[str, float]) -> Dict[str, SensorSelfCheck]:
        resultados: Dict[str, SensorSelfCheck] = {}

        for sensor in self.sensores:
            if sensor not in datos or datos[sensor] is None:
                continue

            val = float(datos[sensor])
            hist = self._hist[sensor]
            delta = None
            if hist:
                delta = val - hist[-1]
                self._delta_hist[sensor].append(delta)
            hist.append(val)

            self._update_baseline(sensor)
            baseline_std = self._baseline_std.get(sensor)

            if baseline_std is None or baseline_std == 0:
                resultados[sensor] = SensorSelfCheck(
                    estado="APRENDIENDO",
                    confianza_pct=60.0,
                    sigma=0.0,
                    baseline_ready=False,
                    delta=delta,
                    valor=val,
                )
                continue

            sigma = abs(delta) / baseline_std if delta is not None else 0.0

            if sigma >= 3.0:
                estado = "FALLO_PROBABLE"
                confianza = 20.0
            elif sigma >= 2.0:
                estado = "DEGRADADO"
                confianza = 50.0
            else:
                estado = "OK"
                confianza = 90.0

            resultados[sensor] = SensorSelfCheck(
                estado=estado,
                confianza_pct=confianza,
                sigma=round(sigma, 2),
                baseline_ready=True,
                delta=delta,
                valor=val,
            )

        return resultados

    def resumen_global(self, resultados: Dict[str, SensorSelfCheck]) -> Dict[str, float]:
        if not resultados:
            return {"confianza_global": 0.0, "sensores": 0}
        confianza = sum(r.confianza_pct for r in resultados.values()) / len(resultados)
        return {"confianza_global": round(confianza, 1), "sensores": len(resultados)}
