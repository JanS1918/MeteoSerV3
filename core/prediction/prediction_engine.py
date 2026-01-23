from __future__ import annotations

from datetime import datetime, timezone
import time
import os
import math
from typing import Any, Dict, List, Optional

from core.logger import get_logger
from core.utils.daynight import estado_dia_hibrido


class PredictionEngine:
    """
    Motor de predicción local basado en históricos reales.
    No usa fuentes externas. Solo sensores propios y derivados.
    """

    def __init__(self, system):
        self.system = system
        self.log = get_logger("PredictionEngine")
        self.model_version = "local_v1"
        try:
            self.feedback_uncertainty_threshold = float(
                os.environ.get("METEOSER_FEEDBACK_UNCERTAINTY", "12")
            )
        except Exception:
            self.feedback_uncertainty_threshold = 12.0

    def _time_features(self) -> dict:
        context_now = None
        try:
            indices = getattr(self.system, "indices", None)
            if indices and hasattr(indices, "_get_context_time"):
                context_now = indices._get_context_time()
        except Exception:
            context_now = None
        if context_now is None:
            context_now = datetime.now(timezone.utc).astimezone()
        else:
            try:
                context_now = context_now.astimezone()
            except Exception:
                pass
        hour = context_now.hour + context_now.minute / 60.0 + context_now.second / 3600.0
        tz_offset = context_now.utcoffset()
        offset_minutes = int(tz_offset.total_seconds() / 60) if tz_offset is not None else 0
        return {
            "hora": hour,
            "hora_iso": context_now.isoformat(),
            "es_noche": 1 if (hour < 6 or hour >= 20) else 0,
            "mes": context_now.month,
            "doy": context_now.timetuple().tm_yday,
            "timezone_offset_minutes": offset_minutes,
        }

    def _rolling_stats(self, nombre: str, window_s: int = 1800) -> tuple[Optional[float], Optional[float]]:
        historial = self.system.obtener_historial_sensor(nombre)
        if not historial:
            return None, None
        now = time.time()
        samples = [v for t, v in historial if (now - t) <= window_s]
        if len(samples) < 3:
            samples = [v for _, v in historial[-30:]]
        values = []
        for v in samples:
            try:
                values.append(float(v))
            except Exception:
                continue
        if len(values) < 2:
            return None, None
        mean = sum(values) / len(values)
        var = sum((v - mean) ** 2 for v in values) / max(1, len(values))
        return mean, math.sqrt(var)

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

    def _combine_estimators(self, values: List[float], weights: Optional[List[float]] = None) -> tuple[float, float]:
        if not values:
            return 0.0, 0.0
        if weights and len(weights) == len(values):
            total_w = sum(weights)
            if total_w > 0:
                avg = sum(v * w for v, w in zip(values, weights)) / total_w
            else:
                avg = sum(values) / len(values)
        else:
            avg = sum(values) / len(values)
        var = sum((v - avg) ** 2 for v in values) / max(1, len(values))
        std = var ** 0.5
        return max(0.0, min(100.0, avg)), max(0.0, std)

    def predecir(self) -> Dict[str, Any]:
        pred: Dict[str, Any] = {}
        indices: Dict[str, Any] | None = None
        time_feats = self._time_features()
        # intentar obtener ubicación y modelo de estación al inicio (para contexto)
        try:
            loc = None
            try:
                loc = self.system.obtener_coordenadas()
            except Exception:
                loc = None
        except Exception:
            loc = None
        try:
            station_model = (getattr(self.system, 'sensores', {}) or {}).get('model')
            if not station_model:
                station_model = (getattr(self.system, 'sensores_metadata', {}) or {}).get('station_model')
        except Exception:
            station_model = None
        try:
            from core.indices.environmental_indices import EnvironmentalIndices
            if not isinstance(self.system.indices, EnvironmentalIndices):
                self.system.indices = EnvironmentalIndices(self.system)
            indices = self.system.indices.obtener_todos()
        except Exception:
            indices = None
        # Determinar día/noche híbrido a partir de índices (amanecer/atardecer híbrido)
        es_noche_hibrido = None
        try:
            if isinstance(indices, dict):
                dia_info = estado_dia_hibrido(indices)
                es_noche_hibrido = dia_info.get("es_noche")
            else:
                dia_info = {}
        except Exception:
            es_noche_hibrido = None
            dia_info = {}
        # Tendencias
        tendencia_temp = self._trend("temperatura")
        tendencia_pres = self._trend("presion")
        tendencia_hum = self._trend("humedad")
        tendencia_rad = self._trend("radiacion")
        tendencia_viento = self._trend("viento")
        mean_hum_30m, std_hum_30m = self._rolling_stats("humedad", 1800)
        mean_pres_30m, std_pres_30m = self._rolling_stats("presion", 1800)
        mean_rad_30m, std_rad_30m = self._rolling_stats("radiacion", 1800)

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
            # usar bandera híbrida si está disponible, sino caer a la hora local
            use_es_noche = None
            if es_noche_hibrido is not None:
                use_es_noche = es_noche_hibrido
            else:
                use_es_noche = bool(time_feats.get("es_noche"))
            if use_es_noche and radiacion is not None and radiacion < 50:
                base += 5.0
            if std_pres_30m is not None and std_pres_30m > 1.5:
                base += min(10.0, std_pres_30m * 3.0)
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
            # incluir nubosidad_estimada como apoyo adicional (no decisorio por sí misma)
            support *= self._support_from_indices(indices, ["riesgo_lluvia", "riesgo_micro_lluvias", "alerta_tormenta", "nubosidad_estimada"])
            # Contextual multiplier basado en ubicación, día/año, estación, día/noche y hora
            try:
                loc = None
                try:
                    loc = self.system.obtener_coordenadas()
                except Exception:
                    loc = None
                station_model = None
                try:
                    # intentar recoger modelo/estación desde sensores o metadata
                    station_model = (getattr(self.system, 'sensores', {}) or {}).get('model')
                    if not station_model:
                        station_model = (getattr(self.system, 'sensores_metadata', {}) or {}).get('station_model')
                except Exception:
                    station_model = None
                # preferir la versión híbrida calculada desde índices
                is_day = not bool(es_noche_hibrido) if es_noche_hibrido is not None else not bool(time_feats.get('es_noche'))
                doy = int(time_feats.get('doy', 0) or 0)
                hour = float(time_feats.get('hora', 0.0) or 0.0)
                # multiplicador base
                ctx_mult = 1.0
                if loc and isinstance(loc, (list, tuple)) and len(loc) == 2 and loc[0] is not None:
                    ctx_mult += 0.03
                # día aumenta importancia de radiación/nubosidad
                ctx_mult += 0.02 if is_day else -0.02
                # influencia horaria: potenciar ligeramente cerca del mediodía, minorar por la noche
                try:
                    # valor entre -0.03 y +0.03 con pico al mediodía
                    hour_influence = 0.03 * math.cos(math.pi * (hour - 12.0) / 12.0)
                    ctx_mult += hour_influence
                except Exception:
                    pass
                # efecto estacional suave según día del año
                try:
                    import math as _math
                    seasonal = 0.02 * _math.cos(2.0 * _math.pi * (doy / 365.0)) if doy else 0.0
                    ctx_mult += seasonal
                except Exception:
                    pass
                # confianza según modelo de estación conocido (pequeño ajuste)
                try:
                    good_models = ("HP2550", "HP2550A", "EasyWeather", "WH65", "PMS5003")
                    if station_model:
                        sm = str(station_model)
                        if any(g in sm for g in good_models):
                            ctx_mult += 0.03
                except Exception:
                    pass
                # limitar multiplicador
                ctx_mult = max(0.7, min(1.25, ctx_mult))
                support *= ctx_mult
            except Exception:
                pass
            prob_lluvia = max(0.0, min(100.0, prob_lluvia * support))
            estimadores: List[float] = [prob_lluvia]
            # Estimador alterno basado en históricos cortos
            alt = None
            if mean_hum_30m is not None and mean_pres_30m is not None:
                alt = max(0.0, min(100.0, (mean_hum_30m - 55) * 1.6 + (1015 - mean_pres_30m) * 1.2))
            if alt is not None:
                estimadores.append(alt)
            if isinstance(indices, dict):
                riesgo_lluvia = indices.get("riesgo_lluvia")
                if isinstance(riesgo_lluvia, dict) and riesgo_lluvia.get("valor") is not None:
                    try:
                        estimadores.append(float(riesgo_lluvia.get("valor")))
                    except Exception:
                        pass
                alerta_tormenta = indices.get("alerta_tormenta")
                if isinstance(alerta_tormenta, dict) and alerta_tormenta.get("valor") is not None:
                    try:
                        estimadores.append(float(alerta_tormenta.get("valor")))
                    except Exception:
                        pass
            prob_lluvia, incert = self._combine_estimators(estimadores)
            if lluvia_cumplida and lluvia_continua:
                pred["prob_lluvia_continua"] = {
                    "valor": round(prob_lluvia, 2),
                    "unidad": "%",
                    "fuente": "sensores_propios",
                    "explicacion": "Lluvia actual y tendencia positiva: alta probabilidad de lluvia continua",
                    "modelo": self.model_version,
                    "incertidumbre": round(incert, 2),
                    "solicitar_feedback": incert >= self.feedback_uncertainty_threshold,
                }
            elif lluvia_cumplida:
                pred["prob_lluvia_cumplida"] = {
                    "valor": round(prob_lluvia, 2),
                    "unidad": "%",
                    "fuente": "sensores_propios",
                    "explicacion": "La alerta de lluvia se ha cumplido: está lloviendo",
                    "modelo": self.model_version,
                    "incertidumbre": round(incert, 2),
                    "solicitar_feedback": incert >= self.feedback_uncertainty_threshold,
                }
            else:
                pred["prob_lluvia"] = {
                    "valor": round(prob_lluvia, 2),
                    "unidad": "%",
                    "fuente": "sensores_propios",
                    "explicacion": "HR + tendencia presión + radiación + lluvia actual",
                    "modelo": self.model_version,
                    "incertidumbre": round(incert, 2),
                    "solicitar_feedback": incert >= self.feedback_uncertainty_threshold,
                }

        # Añadir contexto general en la salida para que todas las fórmulas puedan registrarlo
        try:
            contexto = {
                "hora": round(float(time_feats.get("hora", 0.0) or 0.0), 3),
                "hora_iso": time_feats.get("hora_iso"),
                "es_noche": bool(es_noche_hibrido) if es_noche_hibrido is not None else bool(time_feats.get("es_noche")),
                "doy": int(time_feats.get("doy", 0) or 0),
                "mes": int(time_feats.get("mes", 0) or 0),
                "coordenadas": loc,
                "station_model": station_model,
                "timezone_offset_minutes": time_feats.get("timezone_offset_minutes"),
                "context_time_epoch": indices.get("context_time_epoch") if isinstance(indices, dict) else None,
                "context_timezone_offset_minutes": indices.get("context_timezone_offset_minutes") if isinstance(indices, dict) else None,
            }
            # incorporar información detallada de día/noche/arco solar si existe
            try:
                if dia_info:
                    contexto.update({
                        "fecha": dia_info.get("fecha"),
                        "estacion": dia_info.get("estacion"),
                        "solar_elevation": dia_info.get("solar_elevation"),
                        "arco_solar_deg": dia_info.get("arco_solar_deg"),
                        "es_noche_astronomico": dia_info.get("es_noche_astronomico"),
                    })
            except Exception:
                pass
            try:
                hora_cliente = indices.get("hora_cliente") if isinstance(indices, dict) else None
                if isinstance(hora_cliente, dict):
                    contexto["hora_cliente_iso"] = hora_cliente.get("valor")
                    contexto["hora_cliente_confianza"] = hora_cliente.get("confianza")
                    contexto["hora_cliente_skew_seconds"] = hora_cliente.get("skew_seconds")
            except Exception:
                pass
            pred["contexto"] = contexto
        except Exception:
            pass

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
            estimadores_incomodidad: List[float] = [max(0.0, min(100.0, score))]
            if isinstance(indices, dict):
                for key in ("sensacion_termica_compuesta", "sensacion_calor", "sensacion_frio"):
                    info = indices.get(key)
                    if isinstance(info, dict) and info.get("valor") is not None:
                        try:
                            estimadores_incomodidad.append(float(info.get("valor")))
                        except Exception:
                            continue
            score, incert = self._combine_estimators(estimadores_incomodidad)
            pred["riesgo_incomodidad_termica"] = {
                "valor": round(max(0.0, min(100.0, score)), 2),
                "unidad": "%",
                "fuente": "sensores_propios",
                "explicacion": "Temperatura + viento (con apoyo índices)",
                "modelo": self.model_version,
                "incertidumbre": round(incert, 2),
                "solicitar_feedback": incert >= self.feedback_uncertainty_threshold,
            }

        return pred
