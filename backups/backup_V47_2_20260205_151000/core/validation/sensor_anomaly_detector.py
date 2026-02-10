"""
DETECTOR DE ANOMALÍAS DE SENSORES V34.1
- Detecta inconsistencias físicas
- Escala severidad
- Decide simulación (3-5 repeticiones)
"""
from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from core.validation.sensor_simulator import SensorSimulator

logger = logging.getLogger("meteoser.sensor_anomaly_detector")


class SensorAnomalyDetector:
    def __init__(self):
        self.simulator = SensorSimulator()
        self.history: Dict[str, deque] = {}
        self.max_history = 20
        self.fail_counts: Dict[str, int] = {}
        self.alerts: Dict[str, Dict] = {}
        self.last_update: Optional[float] = None

        self.thresholds = {
            "temperatura": (-60.0, 60.0),
            "humedad": (0.0, 100.0),
            "presion": (870.0, 1085.0),
            "viento": (0.0, 160.0),
            "lluvia": (0.0, 500.0),
            "radiacion": (0.0, 1400.0),
            "uv": (0.0, 20.0),
        }

        self.jump_thresholds = {
            "temperatura": 8.0,
            "humedad": 40.0,
            "presion": 4.0,
            "viento": 30.0,
            "lluvia": 50.0,
            "radiacion": 400.0,
            "uv": 5.0,
        }

    def _add_history(self, sensor: str, value: float):
        if sensor not in self.history:
            self.history[sensor] = deque(maxlen=self.max_history)
        self.history[sensor].append((time.time(), value))

    def _recent_values(self, sensor: str) -> List[float]:
        return [v for _, v in self.history.get(sensor, [])]

    def _check_range(self, sensor: str, value: float) -> Tuple[bool, str, str]:
        if sensor not in self.thresholds:
            return False, "", ""
        vmin, vmax = self.thresholds[sensor]
        if value < vmin or value > vmax:
            dist = abs(value - (vmin if value < vmin else vmax))
            severidad = "alta" if dist >= 10 else "media"
            return True, f"fuera_rango_fisico ({vmin}..{vmax})", severidad
        return False, "", ""

    def _check_jump(self, sensor: str, value: float) -> Tuple[bool, str]:
        if sensor not in self.jump_thresholds:
            return False, ""
        hist = self._recent_values(sensor)
        if len(hist) < 1:
            return False, ""
        delta = abs(value - hist[-1])
        if delta > self.jump_thresholds[sensor]:
            return True, f"salto_temporal ({delta:.2f})"
        return False, ""

    def _check_cross_consistency(self, sensores: Dict[str, float]) -> Optional[Tuple[str, str]]:
        humedad = sensores.get("humedad")
        lluvia = sensores.get("lluvia")
        presion = sensores.get("presion")
        viento = sensores.get("viento")

        if humedad is not None and lluvia is not None:
            if humedad < 20 and lluvia > 1.0:
                return ("lluvia", "inconsistencia_humedad_baja_lluvia")
        if presion is not None and lluvia is not None and humedad is not None:
            if presion > 1025 and humedad < 30 and lluvia > 0.5:
                return ("lluvia", "inconsistencia_presion_alta_lluvia")
        if viento is not None and humedad is not None:
            if viento > 90 and humedad < 20:
                return ("humedad", "inconsistencia_viento_extremo_humedad_baja")
        return None

    def _threshold_required(self, severidad: str) -> int:
        if severidad == "alta":
            return 1
        if severidad == "media":
            return 3
        return 5

    def process_snapshot(self, system) -> Dict[str, Dict]:
        sensores = getattr(system, "sensores", {})
        sensores_clean: Dict[str, float] = {}
        for key in ["temperatura", "humedad", "presion", "viento", "lluvia", "radiacion", "uv"]:
            val = sensores.get(key)
            try:
                if val is not None:
                    sensores_clean[key] = float(val)
            except Exception:
                continue

        alerts = {}
        cross = self._check_cross_consistency(sensores_clean)
        if cross:
            sensor, motivo = cross
            alerts[sensor] = {
                "sensor": sensor,
                "status": "ALERTA",
                "motivo": motivo,
                "severidad": "media",
            }

        for sensor, value in sensores_clean.items():
            rango_bad, motivo_rango, severidad = self._check_range(sensor, value)
            salto_bad, motivo_salto = self._check_jump(sensor, value)

            if rango_bad or salto_bad:
                motivo = motivo_rango or motivo_salto
                sev = severidad or "media"
                alerts[sensor] = {
                    "sensor": sensor,
                    "status": "ALERTA",
                    "motivo": motivo,
                    "severidad": sev,
                }

            self._add_history(sensor, value)

        for sensor in sensores_clean.keys():
            if sensor in alerts:
                self.fail_counts[sensor] = self.fail_counts.get(sensor, 0) + 1
            else:
                # decay suave
                if self.fail_counts.get(sensor, 0) > 0:
                    self.fail_counts[sensor] -= 1

        resultado = {}
        for sensor, alert in alerts.items():
            repeticiones = self.fail_counts.get(sensor, 0)
            threshold = self._threshold_required(alert.get("severidad", "media"))
            simulado = repeticiones >= threshold
            detalle = {
                "sensor": sensor,
                "status": "ALERTA",
                "motivo": alert.get("motivo"),
                "severidad": alert.get("severidad", "media"),
                "repeticiones": repeticiones,
                "threshold": threshold,
                "timestamp": datetime.now().isoformat(),
                "simulado": False,
            }
            if simulado:
                sim = self.simulator.simulate(system, sensor)
                detalle.update({
                    "simulado": True,
                    "valor_simulado": sim.get("valor"),
                    "error_estimado": sim.get("error"),
                    "metodo": sim.get("metodo"),
                    "motivo_simulacion": sim.get("motivo"),
                })
            resultado[sensor] = detalle

        self.alerts = resultado
        self.last_update = time.time()
        return resultado

    def get_alerts(self) -> Dict[str, Dict]:
        return self.alerts.copy()
