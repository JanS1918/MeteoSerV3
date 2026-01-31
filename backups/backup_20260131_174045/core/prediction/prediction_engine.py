from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.logger import get_logger


class PredictionEngine:
    """
    Motor de predicción local basado en históricos reales.
    No usa fuentes externas. Solo sensores propios y derivados.
    """

    def __init__(self, system):
        self.system = system
        self.log = get_logger("PredictionEngine")

    def _trend(self, nombre: str, window_s: int = 3600) -> Optional[float]:
        historial = self.system.obtener_historial_sensor(nombre)
        if not historial or len(historial) < 2:
            return None
        now = time.time()
        recent = [(t, v) for t, v in historial if (now - t) <= window_s]
        if len(recent) < 2:
            recent = historial[-10:]
        if len(recent) < 2:
            return None
        t0, v0 = recent[0]
        t1, v1 = recent[-1]
        dt_h = (t1 - t0) / 3600.0
        if dt_h <= 0:
            return None
        return (v1 - v0) / dt_h

    def _last(self, nombre: str) -> Optional[float]:
        val = self.system.obtener_sensor(nombre)
        if val is None:
            return None
        try:
            return float(val)
        except Exception:
            return None

    def _sensor_reliability(self, nombre: str) -> Optional[float]:
        try:
            meta = getattr(self.system, "sensores_metadata", {}).get(nombre, {})
        except Exception:
            meta = {}
        if not meta:
            return None
        try:
            val = float(meta.get("fiabilidad"))
            if val > 1.5:
                val = val / 100.0
            return max(0.0, min(1.0, val))
        except Exception:
            return None

    def _support_factor(self, sensores: List[str]) -> float:
        if not sensores:
            return 1.0
        reliabs: List[float] = []
        for s in sensores:
            r = self._sensor_reliability(s)
            if r is not None:
                reliabs.append(r)
        if not reliabs:
            return 1.0
        avg = sum(reliabs) / max(1, len(reliabs))
        factor = 0.6 + avg * 0.5
        return max(0.6, min(1.1, factor))

    def _support_from_indices(self, indices: Dict[str, Any] | None, nombres: List[str]) -> float:
        if not indices or not nombres:
            return 1.0
        scores: List[float] = []
        for n in nombres:
            info = indices.get(n)
            if not isinstance(info, dict):
                continue
            conf_score = info.get("confianza_score")
            if conf_score is None:
                continue
            try:
                scores.append(float(conf_score))
            except Exception:
                continue
        if not scores:
            return 1.0
        avg = sum(scores) / max(1, len(scores))
        factor = 0.8 + (avg / 100.0) * 0.4
        return max(0.7, min(1.2, factor))

    def predecir(self) -> Dict[str, Any]:
        pred: Dict[str, Any] = {}
        indices: Dict[str, Any] | None = None
        try:
            from core.indices.environmental_indices import EnvironmentalIndices
            if not isinstance(self.system.indices, EnvironmentalIndices):
                self.system.indices = EnvironmentalIndices(self.system)
            indices = self.system.indices.obtener_todos()
        except Exception:
            indices = None
        # Tendencias
        tendencia_temp = self._trend("temperatura")
        tendencia_pres = self._trend("presion")
        tendencia_hum = self._trend("humedad")
        tendencia_rad = self._trend("radiacion")
        tendencia_viento = self._trend("viento")

        if tendencia_temp is not None:
            pred["tendencia_temperatura"] = {"valor": round(tendencia_temp, 3), "unidad": "C/h", "fuente": "historico"}
        if tendencia_pres is not None:
            pred["tendencia_presion"] = {"valor": round(tendencia_pres, 3), "unidad": "hPa/h", "fuente": "historico"}
        if tendencia_hum is not None:
            pred["tendencia_humedad"] = {"valor": round(tendencia_hum, 3), "unidad": "%/h", "fuente": "historico"}
        if tendencia_rad is not None:
            pred["tendencia_radiacion"] = {"valor": round(tendencia_rad, 3), "unidad": "W/m²/h", "fuente": "historico"}
        if tendencia_viento is not None:
            pred["tendencia_viento"] = {"valor": round(tendencia_viento, 3), "unidad": "km/h/h", "fuente": "historico"}

        # Predicción de lluvia local (solo con sensores propios)
        humedad = self._last("humedad")
        presion = self._last("presion")
        radiacion = self._last("radiacion")
        lluvia_rate = self._last("lluvia_rate")
        if lluvia_rate is None:
            lluvia_rate = self._last("lluvia")

        prob_lluvia = None
        lluvia_cumplida = False
        lluvia_continua = False
        if humedad is not None:
            base = min(100.0, max(0.0, (humedad - 60) * 2.0))
            if presion is not None and tendencia_pres is not None:
                if tendencia_pres < 0:
                    base += min(30.0, abs(tendencia_pres) * 10)
            if radiacion is not None and radiacion < 100:
                base += 10.0
            if lluvia_rate is not None and lluvia_rate > 0:
                # Si ya está lloviendo y la probabilidad era alta, la alerta se cumple
                lluvia_cumplida = True
                # Si la tendencia de lluvia_rate es positiva o estable, se espera lluvia continua
                tendencia_lluvia = self._trend("lluvia_rate")
                if tendencia_lluvia is not None and tendencia_lluvia >= 0:
                    lluvia_continua = True
                base = 100.0
            prob_lluvia = max(0.0, min(100.0, base))

        if prob_lluvia is not None:
            support = self._support_factor(["humedad", "presion", "radiacion", "lluvia_rate", "lluvia"])
            support *= self._support_from_indices(indices, ["riesgo_lluvia", "riesgo_micro_lluvias", "alerta_tormenta"])
            prob_lluvia = max(0.0, min(100.0, prob_lluvia * support))
            if lluvia_cumplida and lluvia_continua:
                pred["prob_lluvia_continua"] = {
                    "valor": round(prob_lluvia, 2),
                    "unidad": "%",
                    "fuente": "sensores_propios",
                    "explicacion": "Lluvia actual y tendencia positiva: alta probabilidad de lluvia continua"
                }
            elif lluvia_cumplida:
                pred["prob_lluvia_cumplida"] = {
                    "valor": round(prob_lluvia, 2),
                    "unidad": "%",
                    "fuente": "sensores_propios",
                    "explicacion": "La alerta de lluvia se ha cumplido: está lloviendo"
                }
            else:
                pred["prob_lluvia"] = {
                    "valor": round(prob_lluvia, 2),
                    "unidad": "%",
                    "fuente": "sensores_propios",
                    "explicacion": "HR + tendencia presión + radiación + lluvia actual"
                }

        # Predicción de incomodidad térmica (simple)
        temp = self._last("temperatura")
        viento = self._last("viento")
        if temp is not None:
            score = 0.0
            if temp > 28:
                score += (temp - 28) * 5
            if temp < 12:
                score += (12 - temp) * 4
            if viento is not None and viento > 30:
                score += (viento - 30) * 1.5
            support = self._support_factor(["temperatura", "viento"])
            support *= self._support_from_indices(indices, ["sensacion_termica_compuesta", "sensacion_calor", "sensacion_frio"])
            score = max(0.0, min(100.0, score * support))
            pred["riesgo_incomodidad_termica"] = {
                "valor": round(max(0.0, min(100.0, score)), 2),
                "unidad": "%",
                "fuente": "sensores_propios",
                "explicacion": "Temperatura + viento"
            }

        return pred
