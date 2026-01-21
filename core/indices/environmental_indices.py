from typing import Dict

# ------------------------------------------------------------
# ALERTA DE FRÍO EXTREMO
# ------------------------------------------------------------
def indice_alerta_polvo(pm25: float, viento: float) -> float:
    """
    Calcula un índice de alerta por polvo/suciedad en el aire basado en PM2.5 y viento.
    Devuelve un valor entre 0 y 100 (mayor = más riesgo).
    """
    # Fórmula simple: riesgo crece con PM2.5 y viento
    riesgo: float = pm25 * (1 + 0.1 * viento)
    # Normalización básica
    if riesgo > 100:
        riesgo = 100
    if riesgo < 0:
        riesgo = 0
    return riesgo

def indice_alerta_frio_extremo(temp: float, viento: float, humedad: float) -> float:
    """
    Índice de alerta de frío extremo basado en:
    - Temperatura baja
    - Viento alto
    - Humedad baja
    Devuelve un valor 0-100 (mayor = más riesgo de frío extremo).
    """
    score = 0.0
    if temp < 5:
        score += min(40, (5 - temp) * 4)
    if viento > 10:
        score += min(30, (viento - 10) * 2)
    if humedad < 40:
        score += min(30, (40 - humedad) * 0.5)
    return max(0.0, min(100.0, score))
# ------------------------------------------------------------
# ALERTA DE CALOR EXTREMO
# ------------------------------------------------------------
def indice_alerta_calor_extremo(temp: float, uv: float, humedad: float) -> float:
    """
    Índice de alerta de calor extremo basado en:
    - Temperatura alta
    - UV alto
    - Humedad alta
    Devuelve un valor 0-100 (mayor = más riesgo de calor extremo).
    """
    score = 0.0
    if temp > 32:
        score += min(40, (temp - 32) * 2)
    if uv > 7:
        score += min(30, (uv - 7) * 5)
    if humedad > 60:
        score += min(30, (humedad - 60) * 0.5)
    return max(0.0, min(100.0, score))


# ------------------------------------------------------------
# ÍNDICES AVANZADOS DE SENSACIÓN TÉRMICA Y AIRE
# ------------------------------------------------------------

def indice_heat_index_c(temp_c: float, humedad: float) -> float:
    # NOAA Heat Index (en °C)
    t_f: float = temp_c * 9 / 5 + 32
    rh: float = humedad
    hi_f: float = (-42.379 + 2.04901523 * t_f + 10.14333127 * rh - 0.22475541 * t_f * rh
            - 0.00683783 * t_f * t_f - 0.05481717 * rh * rh
            + 0.00122874 * t_f * t_f * rh + 0.00085282 * t_f * rh * rh
            - 0.00000199 * t_f * t_f * rh * rh)
    hi_c: float = (hi_f - 32) * 5 / 9
    return hi_c


def indice_wind_chill_c(temp_c: float, viento_kmh: float) -> float:
    # Sensación térmica por viento (°C) válida para T<=10C y viento>4.8 km/h
    v: float = max(viento_kmh, 0.0)
    if temp_c > 10 or v < 4.8:
        return temp_c
    return 13.12 + 0.6215 * temp_c - 11.37 * (v ** 0.16) + 0.3965 * temp_c * (v ** 0.16)


def indice_bulbo_humedo_c(temp_c: float, humedad: float) -> float:
    # Aproximación Stull (2011)
    rh: float = max(1.0, min(100.0, humedad))
    return (temp_c * math.atan(0.151977 * (rh + 8.313659) ** 0.5)
            + math.atan(temp_c + rh)
            - math.atan(rh - 1.676331)
            + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
            - 4.686035)


def indice_humidex(temp_c: float, humedad: float) -> float:
    # Humidex basado en punto de rocío estimado
    a, b = 17.27, 237.7
    alpha: float = ((a * temp_c) / (b + temp_c)) + math.log(max(1e-6, humedad) / 100.0)
    dp: float = (b * alpha) / (a - alpha)
    e: float = 6.11 * math.exp(5417.7530 * (1 / 273.16 - 1 / (273.15 + dp)))
    return temp_c + 0.5555 * (e - 10.0)


def indice_humedad_absoluta_gm3(temp_c: float, humedad: float) -> float:
    # g/m3
    es: float = 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))
    e: float = es * (humedad / 100.0)
    return 2.1674 * e / (273.15 + temp_c) * 100.0


def indice_vpd_kpa(temp_c: float, humedad: float) -> float:
    # Déficit de presión de vapor (kPa)
    es: float = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea: float = es * (humedad / 100.0)
    return max(0.0, es - ea)


def indice_entalpia_kjkg(temp_c: float, humedad: float, presion_kpa: float = 101.325) -> float:
    # Entalpía del aire húmedo (kJ/kg)
    es: float = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea: float = es * (humedad / 100.0)
    w: float = 0.62198 * ea / max(0.1, (presion_kpa - ea))
    return 1.006 * temp_c + w * (2501 + 1.86 * temp_c)


def indice_wbgt(temp_c: float, humedad: float, radiacion: float = 0.0, viento_kmh: float = 0.0) -> float:
    # WBGT aproximado con bulbo húmedo y globo estimado
    tw: float = indice_bulbo_humedo_c(temp_c, humedad)
    tg: float = temp_c + (radiacion / 1000.0) * 12.0 - (viento_kmh * 0.5)
    tg: float = max(temp_c - 5, min(temp_c + 20, tg))
    return 0.7 * tw + 0.2 * tg + 0.1 * temp_c


def indice_pmv_ppd_simple(temp_c: float, humedad: float, viento_kmh: float = 0.0) -> Dict[str, float]:
    # Aproximación simple basada en temperatura/HR/viento
    v: float = viento_kmh / 3.6
    pmv: float = (temp_c - 24) / 4 + (humedad - 50) / 100 - v * 0.2
    pmv: float = max(-3.0, min(3.0, pmv))
    ppd: float = 100.0 - 95.0 * math.exp(-0.03353 * pmv ** 4 - 0.2179 * pmv ** 2)
    return {"pmv": round(pmv, 2), "ppd": round(ppd, 1)}


def indice_aqi_pm25(pm25: float) -> float:
    # AQI US EPA para PM2.5 (µg/m³)
    breakpoints: list[tuple[float, float, int, int]] = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 350.4, 301, 400),
        (350.5, 500.4, 401, 500),
    ]
    c: float = max(0.0, pm25)
    for (cl, ch, il, ih) in breakpoints:
        if cl <= c <= ch:
            return (ih - il) / (ch - cl) * (c - cl) + il
    return 500.0


def _media_ponderada(valores: list, pesos: list) -> float:
    total_w = 0.0
    total = 0.0
    for v, w in zip(valores, pesos):
        if v is None:
            continue
        total_w += w
        total += v * w
    if total_w <= 0:
        return None
    return total / total_w


def _clamp_range(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min(value, max_value), min_value)


def _calcular_nubosidad_estimada(temp: float | None, dew: float | None, rh: float | None, viento: float | None,
                                 rad_real: float | None, rad_teorica: float | None, temp_esperada_nocturna: float | None,
                                 es_dia: bool) -> float | None:
    if temp is None or dew is None or rh is None or viento is None:
        return None
    delta_t = max(min(temp - dew, 10.0), 0.0)
    sat_factor = (10.0 - delta_t) / 10.0
    rh_factor = max(min(rh, 100.0), 0.0) / 100.0
    viento_clamp = max(min(viento, 5.0), 0.0)
    viento_factor = 1.0 - (viento_clamp / 5.0)
    manta_factor = 0.0
    if not es_dia and temp_esperada_nocturna is not None:
        delta_n = max(min(temp - temp_esperada_nocturna, 5.0), -5.0)
        manta_factor = delta_n / 5.0 if delta_n >= 0 else 0.0
    nub_atmos = (
        0.4 * sat_factor +
        0.3 * rh_factor +
        0.2 * viento_factor +
        0.1 * manta_factor
    ) * 100.0
    nub_atmos = _clamp_range(nub_atmos)
    if es_dia and rad_teorica and rad_teorica > 0:
        ratio = 0.0 if rad_real is None else rad_real / rad_teorica
        ratio = max(min(ratio, 1.2), 0.0)
        nub_radiacion = _clamp_range((1.0 - ratio) * 120.0)
        nub_final = 0.7 * nub_radiacion + 0.3 * nub_atmos
    else:
        nub_final = nub_atmos
    return _clamp_range(nub_final)


def _calcular_transparencia_atmosferica(rh: float | None, temp: float | None, dew: float | None,
                                        nub: float | None, rad_real: float | None, rad_teorica: float | None,
                                        es_dia: bool) -> float | None:
    if rh is None or temp is None or dew is None or nub is None:
        return None
    delta_t = max(min(temp - dew, 15.0), 0.0)
    sequedad = delta_t / 15.0
    rh_factor = 1.0 - (max(min(rh, 100.0), 0.0) / 100.0)
    nub_factor = 1.0 - (max(min(nub, 100.0), 0.0) / 100.0)
    if es_dia and rad_teorica and rad_teorica > 0:
        ratio = 0.0 if rad_real is None else rad_real / rad_teorica
        ratio = max(min(ratio, 1.2), 0.0)
        rad_factor = min(ratio, 1.0)
    else:
        rad_factor = 1.0
    transparencia = (
        0.35 * sequedad +
        0.35 * rh_factor +
        0.20 * nub_factor +
        0.10 * rad_factor
    ) * 100.0
    return _clamp_range(transparencia)


def _calcular_riesgo_empaniamiento_optica(temp: float | None, dew: float | None, rh: float | None,
                                         viento: float | None) -> float | None:
    if temp is None or dew is None or rh is None or viento is None:
        return None
    delta_t = max(min(temp - dew, 5.0), 0.0)
    roc_factor = (5.0 - delta_t) / 5.0
    rh_factor = max(min(rh, 100.0), 0.0) / 100.0
    viento_clamp = max(min(viento, 4.0), 0.0)
    viento_factor = 1.0 - (viento_clamp / 4.0)
    riesgo = (
        0.5 * roc_factor +
        0.3 * rh_factor +
        0.2 * viento_factor
    ) * 100.0
    return _clamp_range(riesgo)


def _calcular_seeing_termico_basico(var_t_5min: float | None, viento: float | None) -> float | None:
    if var_t_5min is None or viento is None:
        return None
    var_t = max(min(var_t_5min, 3.0), 0.0)
    viento_clamp = max(min(viento, 8.0), 0.0)
    var_factor = var_t / 3.0
    viento_factor = viento_clamp / 8.0
    seeing_malo = (
        0.6 * var_factor +
        0.4 * viento_factor
    ) * 100.0
    return _clamp_range(seeing_malo)


def _calcular_cielo_observable_nocturno(nub: float | None, transp: float | None, niebla: float | None,
                                      emp: float | None, seeing: float | None, fase_lunar: float | None) -> float | None:
    if nub is None or transp is None or niebla is None or emp is None or seeing is None:
        return None
    nub_n = nub / 100.0
    transp_n = transp / 100.0
    niebla_n = niebla / 100.0
    emp_n = emp / 100.0
    seeing_n = seeing / 100.0
    fase_n = (fase_lunar or 0.0) / 100.0
    calidad_base = 0.5 * (1.0 - nub_n) + 0.5 * transp_n
    penal_niebla = 0.4 * niebla_n
    penal_emp = 0.2 * emp_n
    penal_seeing = 0.2 * seeing_n
    if fase_lunar is None:
        penal_luna = 0.0
    elif fase_lunar <= 20:
        penal_luna = 0.0
    elif fase_lunar <= 50:
        penal_luna = 0.1 * fase_n
    elif fase_lunar <= 80:
        penal_luna = 0.25 * fase_n
    else:
        penal_luna = 0.4 * fase_n
    calidad = calidad_base - (penal_niebla + penal_emp + penal_seeing + penal_luna)
    return _clamp_range(calidad * 100.0)


def _calcular_ventana_observacion_nocturna(cielo: float | None, duracion_noche: float | None) -> float | None:
    if cielo is None or duracion_noche is None:
        return None
    horas = duracion_noche * (cielo / 100.0)
    return max(0.0, min(horas, 12.0))


def _clasificar_indice_cielo(valor: float | None) -> str:
    if valor is None:
        return "sin datos"
    if valor >= 75:
        return "buena"
    if valor >= 45:
        return "regular"
    return "mala"


from datetime import datetime
from typing import Dict, Any
import math

# ------------------------------------------------------------
# ALERTA DE TORMENTA
# ------------------------------------------------------------
def indice_alerta_tormenta(uv: float, radiacion: float, presion: float, tendencia_presion: float, rayos: float) -> float:
    """
    Índice de alerta de tormenta basado en:
    - UV bajo
    - Radiación baja
    - Presión baja o descendente
    - Rayos detectados
    Devuelve un valor 0-100 (mayor = más riesgo de tormenta).
    """
    score = 0.0
    # UV bajo y radiación baja suelen indicar nubosidad densa
    if uv < 2:
        score += 20
    if radiacion < 100:
        score += 20
    # Presión baja o tendencia descendente
    if presion < 1005:
        score += 20
    if tendencia_presion < 0:
        score += min(20, abs(tendencia_presion) * 5)
    # Rayos detectados
    if rayos > 0:
        score += min(20, rayos * 2)
    return max(0.0, min(100.0, score))

# ============================================================
# MÓDULO B — ÍNDICES METEOROLÓGICOS AVANZADOS
# ============================================================
#
# Este módulo contiene todos los índices, fórmulas y previsiones avanzadas de MeteoSer.
# Cada función está documentada con su propósito, fórmula y ejemplos de uso.
# Los índices combinan sensores reales, estimaciones físicas y lógica creativa para maximizar la robustez y utilidad.


EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales
# Permite valores derivados fiables (estimados) cuando faltan sensores directos
REAL_ONLY_SENSORS = False


from typing import Dict, Any
import math
import time
import os
from core.indices.cetreria.cetreria_indices import calcular_cetreria


class EnvironmentalIndices:
    def indice_sonometro(self):
        """
        Devuelve el valor del sensor de ruido (decibelios) como índice.
        """
        ruido = self._get_sensor("ruido")
        if ruido["valor"] is None:
            return {"valor": None, "estimado": True, "explicacion": "Sin datos de sonómetro"}
        return {
            "valor": round(float(ruido["valor"]), 2),
            "estimado": ruido["estimado"],
            "explicacion": "Nivel de ruido ambiente (dB)"
        }

    def indice_sismografo(self):
        """
        Índice simple de sismógrafo: devuelve el último valor conocido o marcado como no disponible.
        """
        try:
            sismo = self._get_sensor("sismografo")
        except Exception:
            sismo = {"valor": None, "estimado": True}
        if sismo.get("valor") is None:
            return {"valor": None, "estimado": True, "explicacion": "Sin datos de sismógrafo"}
        return {"valor": round(float(sismo["valor"]), 2), "estimado": sismo.get("estimado", False), "explicacion": "Actividad sísmica relativa"}

    def radiacion_teorica(self):
        """
        Calcula la radiación solar teórica en superficie horizontal (W/m2) según la hora y latitud.
        Devuelve un dict con valor, estimado y explicación.
        """
        import math
        from datetime import datetime
        # Constante solar (W/m2)
        S = 1367
        # Obtener latitud
        lat, lon = self._get_location() if hasattr(self, '_get_location') else (None, None)
        if lat is None:
            return {"valor": None, "estimado": True, "explicacion": "Falta latitud"}
        # Día del año
        now: datetime = datetime.utcnow()
        n: int = now.timetuple().tm_yday
        # Hora decimal UTC
        hora_decimal: float = now.hour + now.minute / 60 + now.second / 3600
        # Decl. solar
        decl: float = 23.45 * math.sin(math.radians(360 * (284 + n) / 365))
        # Ángulo horario
        omega: float = math.radians((hora_decimal - 12.0) * 15.0)
        # Elevación solar
        lat_rad: float = math.radians(lat)
        decl_rad: float = math.radians(decl)
        elev: float = math.asin(math.sin(lat_rad) * math.sin(decl_rad) + math.cos(lat_rad) * math.cos(decl_rad) * math.cos(omega))
        if elev <= 0:
            return {"valor": 0.0, "estimado": True, "explicacion": "Sol bajo el horizonte"}
        # Atmósfera clara, sin nubes
        rad: float = S * math.sin(elev)
        return {"valor": round(rad, 2), "estimado": True, "explicacion": "Modelo teórico sin nubes"}

    def _get_location(self):
        """
        Devuelve (lat, lon) si el sistema tiene método obtener_coordenadas, si no (None, None).
        """
        if hasattr(self.system, "obtener_coordenadas"):
            coords = self.system.obtener_coordenadas()
            if coords and isinstance(coords, (list, tuple)) and len(coords) == 2:
                return coords[0], coords[1]
            if isinstance(coords, dict) and "lat" in coords and "lon" in coords:
                return coords["lat"], coords["lon"]
        return None, None

    def __init__(self, system_core) -> None:
        self.system = system_core
        try:
            self._min_confidence = float(os.environ.get("METEOSER_MIN_CONFIDENCE", "0.4"))
        except Exception:
            self._min_confidence = 0.4
        try:
            self._lag_seconds = max(0, int(os.environ.get("METEOSER_LAG_SECONDS", "10")))
        except Exception:
            self._lag_seconds = 10
        env_lag_indices = os.environ.get("METEOSER_LAG_INDICES")
        default_lag_indices = {
            "variabilidad_viento_30m",
            "riesgo_niebla",
            "nubosidad_estimada",
            "transparencia_atmosferica",
            "seeing_termico",
            "cielo_observable_nocturno",
        }
        if env_lag_indices is None:
            self._lag_indices = default_lag_indices
        else:
            try:
                self._lag_indices = {s.strip() for s in env_lag_indices.split(',') if s.strip()}
            except Exception:
                self._lag_indices = default_lag_indices
        self._lag_buffer: dict[str, list[tuple[float, float]]] = {}
        self._lag_last: dict[str, dict] = {}
        try:
            self._min_confidence = float(os.environ.get("METEOSER_MIN_CONFIDENCE", "0.4"))
        except Exception:
            self._min_confidence = 0.4
        try:
            self._lag_seconds = max(0, int(os.environ.get("METEOSER_LAG_SECONDS", "10")))
        except Exception:
            self._lag_seconds = 10
        env_lag_indices = os.environ.get("METEOSER_LAG_INDICES")
        default_lag_indices = {
            "variabilidad_viento_30m",
            "riesgo_niebla",
            "nubosidad_estimada",
            "transparencia_atmosferica",
            "seeing_termico",
            "cielo_observable_nocturno",
        }
        if env_lag_indices is None:
            self._lag_indices = default_lag_indices
        else:
            try:
                self._lag_indices = {s.strip() for s in env_lag_indices.split(',') if s.strip()}
            except Exception:
                self._lag_indices = default_lag_indices
        self._lag_buffer: dict[str, list[tuple[float, float]]] = {}
        self._lag_last: dict[str, dict] = {}
        try:
            self._min_confidence = float(os.environ.get("METEOSER_MIN_CONFIDENCE", "0.4"))
        except Exception:
            self._min_confidence = 0.4
        # Lag / buffering settings para índices ruidosos
        try:
            self._lag_seconds = max(0, int(os.environ.get("METEOSER_LAG_SECONDS", "10")))
        except Exception:
            self._lag_seconds = 10
        env_lag_indices = os.environ.get("METEOSER_LAG_INDICES")
        default_lag_indices = {
            "variabilidad_viento_30m",
            "riesgo_niebla",
            "nubosidad_estimada",
            "transparencia_atmosferica",
            "seeing_termico",
            "cielo_observable_nocturno",
        }
        if env_lag_indices is None:
            self._lag_indices = default_lag_indices
        else:
            try:
                # permitir lista separada por comas
                self._lag_indices = {s.strip() for s in env_lag_indices.split(',') if s.strip()}
            except Exception:
                self._lag_indices = default_lag_indices
        self._lag_buffer: dict[str, list[tuple[float, float]]] = {}
        self._lag_last: dict[str, dict] = {}

    def _sensor_confidence(self, nombre: str) -> float | None:
        try:
            meta = getattr(self.system, "sensores_metadata", {}).get(nombre, {})
        except Exception:
            meta = {}
        if not meta:
            return None
        try:
            val = float(meta.get("fiabilidad"))
        except Exception:
            return None
        if val > 1.5:
            val = val / 100.0
        return max(0.0, min(1.0, val))

    def _apply_lag(self, indices: Dict[str, Any]) -> Dict[str, Any]:
        if not self._lag_indices or self._lag_seconds <= 0:
            return indices
        now = time.time()
        for nombre in self._lag_indices:
            entry = indices.get(nombre)
            if not isinstance(entry, dict):
                continue
            raw = entry.get("valor")
            if raw is None:
                continue
            try:
                raw_val = float(raw)
            except Exception:
                continue
            buffer = self._lag_buffer.get(nombre)
            if buffer is None:
                buffer = []
            buffer.append((now, raw_val))
            if len(buffer) > 200:
                buffer = buffer[-200:]
            cutoff = now - max(self._lag_seconds * 5, 300)
            buffer = [item for item in buffer if item[0] >= cutoff]
            self._lag_buffer[nombre] = buffer
            target_time = now - self._lag_seconds
            lag_val = None
            lag_ts = None
            for ts, val in reversed(buffer):
                if ts <= target_time:
                    lag_val = val
                    lag_ts = ts
                    break
            if lag_val is None and nombre in self._lag_last:
                lag_val = self._lag_last[nombre].get("valor")
                lag_ts = self._lag_last[nombre].get("ts")
            if lag_val is not None:
                self._lag_last[nombre] = {"valor": lag_val, "ts": lag_ts or now}
            entry["valor_crudo"] = raw_val
            entry["valor"] = lag_val
            entry["lagged"] = True
            entry["lag_s"] = self._lag_seconds
            entry["ts_crudo"] = now
            entry["ts_lag"] = lag_ts
        return indices

    def calcular_indices(self):
        sismos = self._get_sensor("sismografo")
        try:
            from .external_earthquake_validation import validar_sismo_externo
        except ImportError:
            validar_sismo_externo = None
        lat, lon = self._get_location()
        sismo_externo_confirma = False
        explicacion_sismo_externa: str = ""
        if validar_sismo_externo and lat is not None and lon is not None:
            try:
                sismo_externo_confirma: bool = validar_sismo_externo(lat=lat, lon=lon)
            except Exception as e:
                sismo_externo_confirma = False
                explicacion_sismo_externa = f"Error validación externa: {e}"
        elif not validar_sismo_externo:
            explicacion_sismo_externa = "No disponible módulo validación externa sismos"
        else:
            explicacion_sismo_externa = "No disponible lat/lon para validación externa sismos"
        # Aquí iría el cálculo y retorno de los índices, por ejemplo:
        indices = {}
        # Ejemplo: indices["sismo"] = sismos
        return indices

    def nubosidad_estimada(self):
        temp = self._get_sensor("temperatura")
        humedad = self._get_sensor("humedad")
        viento = self._get_sensor("viento", fallback=0)
        uv = self._get_sensor("uv", fallback=0)
        rad_real = self._get_sensor("radiacion", fallback=0)
        rad_teor = self.radiacion_teorica()

        temp_val = float(temp["valor"]) if temp["valor"] is not None else None
        humedad_val = float(humedad["valor"]) if humedad["valor"] is not None else None
        viento_val = float(viento["valor"]) if viento["valor"] is not None else 0.0
        uv_val = float(uv["valor"]) if uv["valor"] is not None else 0.0
        rad_val = float(rad_real["valor"]) if rad_real["valor"] is not None else None
        rad_teor_val = float(rad_teor["valor"]) if rad_teor["valor"] is not None else None

        # Punto de rocío
        dew = None
        if temp_val is not None and humedad_val is not None:
            try:
                a, b = 17.27, 237.7
                alpha = ((a * temp_val) / (b + temp_val)) + math.log(max(1e-6, humedad_val) / 100.0)
                dew = (b * alpha) / (a - alpha)
            except Exception:
                dew = None

        es_dia = False
        if rad_val is not None and rad_val >= 50:
            es_dia = True
        if uv_val > 0.1:
            es_dia = True

        temp_esperada_nocturna = None
        if not es_dia:
            temp_esperada_nocturna = self._mean_history("temperatura", window_s=21600)

        nub = _calcular_nubosidad_estimada(
            temp_val,
            dew,
            humedad_val,
            viento_val,
            rad_val,
            rad_teor_val,
            temp_esperada_nocturna,
            es_dia,
        )
        if nub is None:
            if es_dia and rad_teor_val and rad_teor_val > 0 and rad_val is not None:
                try:
                    nub = _clamp_range((1.0 - (rad_val / rad_teor_val)) * 100.0)
                except Exception:
                    nub = 50.0
            else:
                nub = 50.0
        explicacion = "Nubosidad día/noche (radiación + atmósfera)" if es_dia else "Nubosidad nocturna (atmósfera)"
        return {
            "valor": round(float(nub), 2),
            "estimado": True,
            "explicacion": explicacion
        }

    def fase_lunar(self):
        try:
            import datetime
            # Epoch: new moon 2000-01-06 18:14 UTC
            epoch = datetime.datetime(2000, 1, 6, 18, 14)
            now = datetime.datetime.utcnow()
            days = (now - epoch).total_seconds() / 86400.0
            synodic = 29.53058867
            phase = days % synodic
            # 0=new, 0.5=full
            illum = 0.5 * (1 - math.cos(2 * math.pi * phase / synodic))
            return {
                "valor": round(illum * 100.0, 2),
                "estimado": True,
                "explicacion": "Fase lunar estimada (iluminación %)"
            }
        except Exception:
            return {"valor": None, "estimado": True, "explicacion": "Fase lunar no disponible"}
    def riesgo_niebla(self):
        """
        Índice de riesgo de niebla: alta humedad, baja temperatura, poca radiación y poco viento.
        Devuelve 0-100.
        """
        temp = self._get_sensor("temperatura")
        humedad = self._get_sensor("humedad")
        radiacion = self._get_sensor("radiacion", fallback=0)
        viento = self._get_sensor("viento", fallback=0)
        try:
            t = float(temp["valor"])
            h = float(humedad["valor"])
            r = float(radiacion["valor"])
            v = float(viento["valor"])
        except Exception:
            return {"valor": None, "estimado": True, "explicacion": "Faltan sensores para niebla"}
        score = 0.0
        if h > 90:
            score += (h - 90) * 2
        if t < 8:
            score += (8 - t) * 4
        if r < 50:
            score += (50 - r) * 0.5
        if v < 2:
            score += (2 - v) * 5
        return {"valor": min(100, round(score, 2)), "estimado": temp["estimado"] or humedad["estimado"], "explicacion": f"HR={h}%, T={t}C, Rad={r}W/m2, V={v}m/s"}

    def evapotranspiracion(self):
        """
        Evapotranspiración de referencia (FAO Penman-Monteith simplificado, mm/día).
        Usa temperatura, humedad, radiación y viento si están disponibles.
        """
        temp = self._get_sensor("temperatura")
        humedad = self._get_sensor("humedad")
        radiacion = self._get_sensor("radiacion", fallback=None)
        viento = self._get_sensor("viento", fallback=0)
        try:
            t = float(temp["valor"])
            h = float(humedad["valor"])
            if radiacion["valor"] is None:
                rad_teor = self.radiacion_teorica()
                r: float | None = float(rad_teor["valor"]) if rad_teor["valor"] is not None else None
                rad_estimado = True
            else:
                r = float(radiacion["valor"])
                rad_estimado = radiacion["estimado"]
            v = float(viento["valor"])
        except Exception:
            return {"valor": None, "estimado": True, "explicacion": "Faltan sensores para ET"}
        if r is None:
            return {"valor": None, "estimado": True, "explicacion": "Falta radiación para ET"}
        # Fórmula FAO PM simplificada (no incluye presión ni todos los factores)
        # ETo = 0.408*Delta*(Rn-G) + gamma*(900/(T+273))*u2*(es-ea) / (Delta+gamma*(1+0.34*u2))
        # Simplificamos: Rn=radiación neta (W/m2), u2=viento (m/s), T=ºC, HR=%, es-ea=deficit presión vapor
        es: float = 0.6108 * math.exp((17.27 * t) / (t + 237.3))
        ea: float = es * (h / 100.0)
        delta: float = 4098 * es / ((t + 237.3) ** 2)
        gamma: float = 0.665e-3 * 101.3  # kPa/ºC, presión estándar
        rn: float = r * 0.0864 / 2.45  # MJ/m2/día a mm/día (aprox)
        eto: float = (0.408 * delta * rn + gamma * (900 / (t + 273)) * v * (es - ea)) / (delta + gamma * (1 + 0.34 * v))
        return {"valor": round(max(0, eto), 2), "estimado": temp["estimado"] or humedad["estimado"] or rad_estimado, "explicacion": f"T={t}C, HR={h}%, Rad={r}W/m2, V={v}m/s"}

    """
    Motor unificado de índices meteorológicos y ambientales.
    Calcula valores derivados SOLO a partir de sensores reales disponibles.
    Si falta un sensor, estima usando física/histórico y marca como 'estimado'.
    Devuelve todos los índices relevantes con trazabilidad de fuente y estimación.
    """

    def __init__(self, system_core) -> None:
        self.system = system_core

    def _get_sensor(self, nombre, fallback=None):
        v = self.system.obtener_sensor(nombre)
        if v is not None:
            conf = self._sensor_confidence(nombre)
            estimado = False if conf is None else conf < getattr(self, "_min_confidence", 0.4)
            return {"valor": v, "estimado": estimado, "fuente": nombre, "confianza_sensor": conf}
        if fallback is not None and not REAL_ONLY_SENSORS:
            return {"valor": fallback, "estimado": True, "fuente": f"estimado_{nombre}", "confianza_sensor": None}
        return {"valor": None, "estimado": True, "fuente": f"no_disponible_{nombre}", "confianza_sensor": None}

    def _get_sensor_any(self, nombres: list[str], fallback=None):
        for nombre in nombres:
            v = self.system.obtener_sensor(nombre)
            if v is not None:
                conf = self._sensor_confidence(nombre)
                estimado = False if conf is None else conf < getattr(self, "_min_confidence", 0.4)
                return {"valor": v, "estimado": estimado, "fuente": nombre, "confianza_sensor": conf}
        if fallback is not None and not REAL_ONLY_SENSORS:
            base = nombres[0] if nombres else "sensor"
            return {"valor": fallback, "estimado": True, "fuente": f"estimado_{base}", "confianza_sensor": None}
        base = nombres[0] if nombres else "sensor"
        return {"valor": None, "estimado": True, "fuente": f"no_disponible_{base}", "confianza_sensor": None}

    def _rain_accumulated(self, nombres: list[str], window_s: int) -> tuple[float | None, bool]:
        estimado = True
        for nombre in nombres:
            try:
                historial = self.system.obtener_historial_sensor(nombre)
            except Exception:
                historial = None
            if not historial or len(historial) < 2:
                continue
            estimado = False
            import time as _time
            now: float = _time.time()
            samples = [(t, v) for t, v in historial if (now - t) <= window_s]
            if len(samples) < 2:
                samples = historial[-50:]
            total = 0.0
            prev = None
            for _, v in samples:
                if v is None:
                    continue
                try:
                    v = float(v)
                except Exception:
                    continue
                if prev is None:
                    prev = v
                    continue
                delta = v - prev
                if delta >= 0:
                    total += delta
                else:
                    total += max(0.0, v)
                prev = v
            return total, estimado
        return None, True

    def _confianza(self, estimado: bool, fiable: bool = True) -> str:
        if not estimado:
            return "real"
        return "derivado_fiable" if fiable else "estimado"

    def _tokenizar_nombre(self, nombre: str) -> set:
        if nombre is None:
            return set()
        s = str(nombre).lower()
        for ch in ("_", "-", "/", ".", ",", ":"):
            s = s.replace(ch, " ")
        tokens = {t for t in s.split() if t}
        stop = {"indice", "índice", "riesgo", "alerta", "prediccion", "predicción", "compuesto", "compuesta", "estimado", "estimada"}
        return {t for t in tokens if t not in stop}

    def _relacionados(self, nombre_a: str, nombre_b: str) -> bool:
        ta = self._tokenizar_nombre(nombre_a)
        tb = self._tokenizar_nombre(nombre_b)
        if not ta or not tb:
            return False
        return len(ta & tb) > 0

    def _confianza_score_base(self, conf: str | None) -> float:
        if not conf:
            return 0.45
        conf = str(conf).lower()
        if conf == "real":
            return 0.75
        if conf == "derivado_fiable":
            return 0.55
        if conf == "estimado":
            return 0.35
        return 0.45

    def reforzar_indices(self, indices: Dict[str, Any], predicciones: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if not isinstance(indices, dict) or not indices:
            return indices
        try:
            from core.indices.index_catalog import INDEX_CATALOG
        except Exception:
            INDEX_CATALOG = {}

        sensores = getattr(self.system, "sensores", {}) or {}
        sensores_derivados = getattr(self.system, "sensores_derivados", {}) or {}
        formulas = getattr(self.system, "formulas", {}) or {}

        for nombre, info in list(indices.items()):
            if not isinstance(info, dict):
                continue
            meta = INDEX_CATALOG.get(nombre, {}) if isinstance(INDEX_CATALOG, dict) else {}
            sensores_esperados = meta.get("sensores") or []

            refuerzos = []
            sensores_presentes = 0
            for sensor in sensores_esperados:
                if sensor in sensores:
                    sensores_presentes += 1
                    refuerzos.append({"tipo": "sensor", "nombre": sensor, "estado": "real"})
                elif sensor in sensores_derivados:
                    sensores_presentes += 1
                    refuerzos.append({"tipo": "sensor", "nombre": sensor, "estado": "derivado"})
                elif sensor in indices:
                    sensores_presentes += 1
                    refuerzos.append({"tipo": "indice", "nombre": sensor, "estado": "derivado"})

            formula_refuerzos = 0
            if isinstance(formulas, dict) and formulas:
                for nombre_formula, cfg in formulas.items():
                    if nombre_formula not in indices:
                        continue
                    entradas = cfg.get("entradas") or []
                    if set(entradas) & set(sensores_esperados) or self._relacionados(nombre_formula, nombre):
                        formula_refuerzos += 1
                        refuerzos.append({"tipo": "formula", "nombre": nombre_formula, "estado": "apoyo"})

            pred_refuerzos = 0
            if isinstance(predicciones, dict) and predicciones:
                for nombre_pred in predicciones.keys():
                    if self._relacionados(nombre_pred, nombre):
                        pred_refuerzos += 1
                        refuerzos.append({"tipo": "prediccion", "nombre": nombre_pred, "estado": "apoyo"})

            ratio = 0.0
            if sensores_esperados:
                ratio = sensores_presentes / max(1, len(sensores_esperados))

            base = self._confianza_score_base(info.get("confianza"))
            score = min(100.0, max(0.0, base * 100.0 + ratio * 30.0 + formula_refuerzos * 4.0 + pred_refuerzos * 7.0))

            info["refuerzos"] = refuerzos
            info["confianza_detalle"] = {
                "sensores_esperados": len(sensores_esperados),
                "sensores_presentes": sensores_presentes,
                "formulas_apoyo": formula_refuerzos,
                "predicciones_apoyo": pred_refuerzos,
                "ratio_apoyo": round(ratio, 3),
            }
            info["confianza_score"] = round(score, 2)
        return indices

    def _trend(self, nombre, window_s: int = 3600):
        try:
            historial = self.system.obtener_historial_sensor(nombre)
        except Exception:
            historial = None
        if not historial or len(historial) < 2:
            return None
        import time as _time
        now: float = _time.time()
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

    def _hours_over_threshold(self, nombre, threshold, window_s: int = 86400) -> float:
        try:
            historial = self.system.obtener_historial_sensor(nombre)
        except Exception:
            historial = None
        if not historial or len(historial) < 2:
            return 0.0
        import time as _time
        now: float = _time.time()
        samples = [(t, v) for t, v in historial if (now - t) <= window_s]
        if len(samples) < 2:
            samples = historial[-50:]
        if len(samples) < 2:
            return 0.0
        total_s = 0.0
        for (t0, v0), (t1, v1) in zip(samples, samples[1:]):
            if v0 is not None and v0 >= threshold:
                total_s += max(0.0, t1 - t0)
        return round(total_s / 3600.0, 2)

    def _hours_under_threshold(self, nombre, threshold, window_s: int = 86400) -> float:
        try:
            historial = self.system.obtener_historial_sensor(nombre)
        except Exception:
            historial = None
        if not historial or len(historial) < 2:
            return 0.0
        import time as _time
        now: float = _time.time()
        samples = [(t, v) for t, v in historial if (now - t) <= window_s]
        if len(samples) < 2:
            samples = historial[-50:]
        if len(samples) < 2:
            return 0.0
        total_s = 0.0
        for (t0, v0), (t1, v1) in zip(samples, samples[1:]):
            if v0 is not None and v0 <= threshold:
                total_s += max(0.0, t1 - t0)
        return round(total_s / 3600.0, 2)

    def _mean_history(self, nombre, window_s: int = 86400) -> None | float:
        try:
            historial = self.system.obtener_historial_sensor(nombre)
        except Exception:
            historial = None
        if not historial:
            return None
        import time as _time
        now: float = _time.time()
        samples = [v for t, v in historial if (now - t) <= window_s and v is not None]
        if not samples:
            return None
        return sum(samples) / len(samples)

    def _std_history(self, nombre, window_s: int = 1800) -> None | float:
        try:
            historial = self.system.obtener_historial_sensor(nombre)
        except Exception:
            historial = None
        if not historial:
            return None
        import time as _time
        now: float = _time.time()
        samples = [v for t, v in historial if (now - t) <= window_s and v is not None]
        if len(samples) < 2:
            return None
        mean = sum(samples) / len(samples)
        var = sum((v - mean) ** 2 for v in samples) / max(1, (len(samples) - 1))
        return var ** 0.5

    def sensacion_termica(self):
        temp = self._get_sensor("temperatura")
        viento = self._get_sensor("viento", fallback=0)
        if temp["valor"] is None:
            return {"valor": None, "estimado": True, "explicacion": "Sin sensor de temperatura"}
        try:
            t_val = float(temp["valor"])
        except (TypeError, ValueError):
            return {"valor": None, "estimado": True, "explicacion": "Valor de temperatura no numérico"}
        try:
            v_val = float(viento["valor"])
        except (TypeError, ValueError):
            v_val = 0.0
        st: float = t_val - (v_val * 0.7)
        return {
            "valor": round(st, 2),
            "estimado": temp["estimado"] or viento["estimado"],
            "explicacion": f"{'Estimado' if temp['estimado'] or viento['estimado'] else 'Directo'}: T={t_val}C, V={v_val}m/s"
        }

    def indice_uv(self):
        uv = self._get_sensor("uv")
        try:
            uv_val = float(uv["valor"])
            # Mostrar siempre el valor, aunque sea 0
            if uv_val == 0:
                rad = self._get_sensor("radiacion")
                try:
                    rad_val = float(rad["valor"])
                    if rad_val > 10:
                        uv_val_est: float = min(12, rad_val / 25)
                        return {
                            "valor": round(uv_val_est, 2),
                            "estimado": True,
                            "explicacion": "UV estimado por radiación solar (sensor UV=0, radiación>10). Apoyo entre sensores."
                        }
                except (TypeError, ValueError):
                    pass
            # Siempre mostrar el valor, aunque sea 0
            return {"valor": uv_val, "estimado": uv["estimado"], "explicacion": "Sensor UV directo" if not uv["estimado"] else "Estimado por ausencia de sensor UV"}
        except (TypeError, ValueError):
            pass
        # Estimación física básica si no hay sensor UV
        rad = self._get_sensor("radiacion")
        try:
            rad_val = float(rad["valor"])
            if rad_val > 10:
                uv_val: float = min(12, rad_val / 25)
                return {
                    "valor": round(uv_val, 2),
                    "estimado": True,
                    "explicacion": "UV estimado por radiación solar. Apoyo entre sensores."
                }
            # Si hay radiación pero no suficiente, mostrar 0
            return {
                "valor": 0,
                "estimado": True,
                "explicacion": "UV estimado: radiación baja o sensor UV=0"
            }
        except (TypeError, ValueError):
            pass
        # Si no hay radiación ni UV, mostrar 0
        return {"valor": 0, "estimado": True, "explicacion": "Sin sensor UV ni radiación"}

    def riesgo_lluvia(self):
        humedad = self._get_sensor("humedad")
        lluvia = self._get_sensor("lluvia", fallback=0)
        if humedad["valor"] is None:
            return {"valor": None, "estimado": True, "explicacion": "Sin sensor de humedad"}
        try:
            h_val = float(humedad["valor"])
        except (TypeError, ValueError):
            return {"valor": None, "estimado": True, "explicacion": "Valor de humedad no numérico"}
        try:
            l_val = float(lluvia["valor"])
        except (TypeError, ValueError):
            l_val = 0.0
        riesgo: float = (h_val * 0.6) + (l_val * 0.4)
        return {
            "valor": min(100, round(riesgo, 2)),
            "estimado": humedad["estimado"] or lluvia["estimado"],
            "explicacion": f"{'Estimado' if humedad['estimado'] or lluvia['estimado'] else 'Directo'}: HR={h_val}%, Lluvia={l_val}mm"
        }

    def punto_rocio(self):
        temp = self._get_sensor("temperatura")
        rh = self._get_sensor("humedad")
        if temp["valor"] is None or rh["valor"] is None:
            return {"valor": None, "estimado": True, "explicacion": "Faltan sensores para punto de rocío"}
        try:
            t_val = float(temp["valor"])
            rh_val = float(rh["valor"])
        except (TypeError, ValueError):
            return {"valor": None, "estimado": True, "explicacion": "Valores no numéricos para punto de rocío"}
        a, b = 17.27, 237.7
        try:
            alpha: float = ((a * t_val) / (b + t_val)) + math.log(rh_val / 100.0)
            dp: float = (b * alpha) / (a - alpha)
        except Exception:
            return {"valor": None, "estimado": True, "explicacion": "Error en cálculo de punto de rocío"}
        return {
            "valor": round(dp, 2),
            "estimado": temp["estimado"] or rh["estimado"],
            "explicacion": f"{'Estimado' if temp['estimado'] or rh['estimado'] else 'Directo'}: T={t_val}C, HR={rh_val}%"
        }

    def obtener_todos(self) -> Dict[str, Any]:
        """
        Devuelve todos los índices avanzados, creativos y clásicos, con explicación y nivel de confianza.
        """
        indices = {}
        # Sensores base
        temp = self._get_sensor("temperatura")
        viento = self._get_sensor("viento", fallback=0)
        humedad = self._get_sensor("humedad")
        lluvia = self._get_sensor("lluvia", fallback=0)
        tempint = self._get_sensor("temperatura_interior")
        humedadint = self._get_sensor("humedad_interior")
        co2 = self._get_sensor("co2")
        pm25 = self._get_sensor("pm25")
        ruido = self._get_sensor("ruido")
        luz = self._get_sensor("luz")
        radiacion = self._get_sensor("radiacion", fallback=0)
        suelo = self._get_sensor("wh51")
        rayos = self._get_sensor("rayos")
        lightning_num = self._get_sensor("lightning_num")
        lightning_time = self._get_sensor("lightning_time")

        # --- Validación externa de rayos ---
        try:
            from .external_lightning_validation import validar_rayo_externo
        except ImportError:
            validar_rayo_externo = None
        lat, lon = self._get_location()
        externo_confirma = False
        explicacion_externa: str = ""
        if validar_rayo_externo and lat is not None and lon is not None:
            try:
                externo_confirma = validar_rayo_externo(lat=lat, lon=lon)
            except Exception as e:
                externo_confirma = False
                explicacion_externa: str = f"Error validación externa: {e}"
        elif not validar_rayo_externo:
            explicacion_externa = "No disponible módulo validación externa"
        else:
            explicacion_externa = "No disponible lat/lon para validación externa"
        # Índice de niebla
        niebla = self.riesgo_niebla()
        # Siempre incluir el índice de niebla, aunque sea 0 o None
        if niebla["valor"] is None:
            niebla["valor"] = 0
            niebla["explicacion"] = niebla.get("explicacion", "Sin datos suficientes para niebla")
        niebla["confianza"] = self._confianza(niebla.get("estimado", True), fiable=True)
        indices["riesgo_niebla"] = niebla
        # Índice de evapotranspiración
        et = self.evapotranspiracion()
        if et["valor"] is not None:
            et["confianza"] = self._confianza(et["estimado"], fiable=True)
            indices["evapotranspiracion"] = et
        # Radiación teórica y nubosidad estimada
        rad_teor = self.radiacion_teorica()
        if rad_teor["valor"] is not None:
            rad_teor["confianza"] = self._confianza(rad_teor["estimado"], fiable=True)
            indices["radiacion_teorica"] = rad_teor
        nub = self.nubosidad_estimada()
        if nub["valor"] is not None:
            nub["confianza"] = self._confianza(nub["estimado"], fiable=True)
            indices["nubosidad_estimada"] = nub

        # --- Astronomía local: transparencia, empañamiento, seeing, fase lunar, cielo observable ---
        dew_val = None
        try:
            if temp["valor"] is not None and humedad["valor"] is not None:
                a, b = 17.27, 237.7
                t_val = float(temp["valor"])
                h_val = float(humedad["valor"])
                alpha = ((a * t_val) / (b + t_val)) + math.log(max(1e-6, h_val) / 100.0)
                dew_val = (b * alpha) / (a - alpha)
        except Exception:
            dew_val = None

        rad_teor_val = rad_teor.get("valor") if isinstance(rad_teor, dict) else None
        rad_real_val = radiacion.get("valor") if isinstance(radiacion, dict) else None
        uv_sensor = self._get_sensor("uv", fallback=0)
        es_dia = False
        try:
            if rad_real_val is not None and float(rad_real_val) >= 50:
                es_dia = True
            if uv_sensor.get("valor") is not None and float(uv_sensor["valor"]) > 0.1:
                es_dia = True
        except Exception:
            es_dia = False

        nub_val = nub.get("valor") if isinstance(nub, dict) else None
        transp = _calcular_transparencia_atmosferica(
            float(humedad["valor"]) if humedad["valor"] is not None else None,
            float(temp["valor"]) if temp["valor"] is not None else None,
            dew_val,
            nub_val,
            float(rad_real_val) if rad_real_val is not None else None,
            float(rad_teor_val) if rad_teor_val is not None else None,
            es_dia,
        )
        if transp is not None:
            indices["transparencia_atmosferica"] = {
                "valor": round(transp, 2),
                "estimado": True,
                "confianza": "derivado_fiable",
                "explicacion": "Transparencia atmosférica (sequedad + nubosidad + radiación)"
            }

        emp = _calcular_riesgo_empaniamiento_optica(
            float(temp["valor"]) if temp["valor"] is not None else None,
            dew_val,
            float(humedad["valor"]) if humedad["valor"] is not None else None,
            float(viento["valor"]) if viento["valor"] is not None else None,
        )
        if emp is not None:
            indices["riesgo_empaniamiento_optica"] = {
                "valor": round(emp, 2),
                "estimado": True,
                "confianza": "derivado_fiable",
                "explicacion": "Riesgo de empañamiento óptico por rocío/HR/viento"
            }

        trend_t = self._trend("temperatura", window_s=600)
        var_t_5min = abs(trend_t) / 12.0 if trend_t is not None else 0.0
        seeing = _calcular_seeing_termico_basico(var_t_5min, float(viento["valor"]) if viento["valor"] is not None else 0.0)
        if seeing is not None:
            indices["seeing_termico_basico"] = {
                "valor": round(seeing, 2),
                "estimado": True,
                "confianza": "derivado_fiable",
                "explicacion": "Seeing térmico básico (variación T + viento)"
            }

        fase = self.fase_lunar()
        if fase.get("valor") is not None:
            fase["confianza"] = self._confianza(fase.get("estimado", True), fiable=True)
            indices["fase_lunar"] = fase

        cielo = _calcular_cielo_observable_nocturno(
            nub_val,
            transp,
            niebla.get("valor") if isinstance(niebla, dict) else None,
            emp,
            seeing,
            fase.get("valor") if isinstance(fase, dict) else None,
        )
        if cielo is not None:
            indices["cielo_observable_nocturno"] = {
                "valor": round(cielo, 2),
                "estimado": True,
                "confianza": "derivado_fiable",
                "explicacion": "Cielo observable nocturno (nubosidad + transparencia + riesgos + luna)"
            }
        # Humedad de suelo (WH51)
        if suelo["valor"] is not None:
            indices["humedad_suelo"] = {
                "valor": suelo["valor"],
                "estimado": suelo["estimado"],
                "confianza": self._confianza(suelo["estimado"], fiable=True),
                "explicacion": "Sensor WH51"
            }
            trend_suelo = self._trend("wh51")
            if trend_suelo is not None:
                indices["tendencia_humedad_suelo"] = {
                    "valor": round(trend_suelo, 3),
                    "estimado": True,
                    "confianza": "derivado_fiable",
                    "explicacion": "Tendencia humedad suelo (%/h) desde histórico real"
                }
            # Índice de sequía del suelo (0-100)
            try:
                suelo_val = float(suelo["valor"])
                base: float = max(0.0, min(100.0, 100.0 - suelo_val))
                ajuste_trend = 0.0
                if trend_suelo is not None and trend_suelo < 0:
                    ajuste_trend: float = min(20.0, abs(trend_suelo) * 10.0)
                ajuste_et = 0.0
                if et.get("valor") is not None:
                    ajuste_et: float = min(20.0, float(et["valor"]) * 2.0)
                sequia: float = max(0.0, min(100.0, base + ajuste_trend + ajuste_et))
                indices["indice_sequia_suelo"] = {
                    "valor": round(sequia, 2),
                    "estimado": True,
                    "confianza": "derivado_fiable",
                    "explicacion": "Sequía por humedad suelo + tendencia + ET"
                }
            except Exception:
                pass
        # Rayos (contador y fecha) con validación externa
        explicacion_rayos: str = ""
        rayo_valido = False
        validado_por = []
        # Solo validamos rayos detectados por el sensor interno
        if rayos["valor"] is not None and rayos["valor"] > 0:
            # 1. Validación por fuente externa
            if externo_confirma:
                rayo_valido = True
                validado_por.append("fuente externa")
            # 2. Validación por lluvia real o prevista +/-1h
            # Buscar lluvia real o prevista en la ventana de 1h antes/después del último rayo
            lluvia_detectada = False
            try:
                import datetime
                ahora = datetime.datetime.now()
                # Obtener fecha/hora del último rayo
                rayo_time = None
                if lightning_time["valor"] is not None:
                    # Se asume formato timestamp o string ISO
                    try:
                        if isinstance(lightning_time["valor"], (int, float)):
                            rayo_time = datetime.datetime.fromtimestamp(float(lightning_time["valor"]))
                        else:
                            rayo_time = datetime.datetime.fromisoformat(str(lightning_time["valor"]))
                    except Exception:
                        rayo_time = None
                if rayo_time:
                    # Buscar lluvia real +/-1h
                    lluvia_val = lluvia["valor"] if "valor" in lluvia else None
                    if lluvia_val is not None and float(lluvia_val) > 0:
                        lluvia_detectada = True
                    # Buscar lluvia prevista +/-1h (si hay predicción disponible)
                    # Se asume que el sistema puede tener un método obtener_prediccion_lluvia(hora)
                    if hasattr(self.system, "obtener_prediccion_lluvia"):
                        for delta_h in range(-1,2):
                            hora_pred = rayo_time + datetime.timedelta(hours=delta_h)
                            try:
                                pred_lluvia = self.system.obtener_prediccion_lluvia(hora_pred)
                                if pred_lluvia and float(pred_lluvia) > 0:
                                    lluvia_detectada = True
                                    break
                            except Exception:
                                continue
            except Exception:
                pass
            if lluvia_detectada:
                rayo_valido = True
                validado_por.append("lluvia real o prevista +/-1h")
            # 3. Si no hay validación, no se cuenta el rayo
            if rayo_valido:
                explicacion_rayos: str = f"Detectado por sensor interno y validado por: {', '.join(validado_por)}. "
            else:
                explicacion_rayos = "Detectado por sensor interno pero no validado por fuente externa ni por lluvia real o prevista +/-1h. "
            if explicacion_externa:
                explicacion_rayos += f"[{explicacion_externa}]"
            indices["contador_rayos"] = {
                "valor": rayos["valor"] if rayo_valido else 0,
                "estimado": rayos["estimado"] or not rayo_valido,
                "explicacion": explicacion_rayos.strip()
            }
        else:
            indices["contador_rayos"] = {
                "valor": 0,
                "estimado": True,
                "explicacion": "No se detectaron rayos por sensores internos. " + (f"[{explicacion_externa}]" if explicacion_externa else "")
            }
        if lightning_time["valor"] is not None:
            indices["ultimo_rayo"] = {"valor": lightning_time["valor"], "estimado": lightning_time["estimado"], "explicacion": "Fecha/hora del último rayo"}

        # Fórmulas personalizadas
        formulas: Any | Dict[Any, Any] = getattr(self.system, "formulas", {}) or {}
        if isinstance(formulas, dict) and formulas:
            for nombre, cfg in formulas.items():
                try:
                    expr = cfg.get("expresion")
                    entradas = cfg.get("entradas") or []
                    env = {"math": math}
                    missing = False
                    for key in entradas:
                        val = self.system.obtener_sensor(key)
                        if val is None:
                            missing = True
                            break
                        env[key] = float(val)
                    if missing or not expr:
                        continue
                    valor = eval(expr, {"__builtins__": {}}, env)
                    indices[nombre] = {
                        "valor": round(float(valor), 3),
                        "estimado": False,
                        "confianza": "real",
                        "explicacion": cfg.get("descripcion", "Fórmula personalizada")
                    }
                except Exception:
                    continue
        st = self.sensacion_termica()
        if st["valor"] is not None:
            indices["sensacion_termica"] = st

        pr = self.punto_rocio()
        if pr["valor"] is not None:
            pr["confianza"] = self._confianza(pr["estimado"], fiable=True)
            indices["punto_rocio"] = pr

        # --- Cetrería local ---
        try:
            temp_val = float(temp["valor"]) if temp["valor"] is not None else None
            hum_val = float(humedad["valor"]) if humedad["valor"] is not None else None
            viento_val = float(viento["valor"]) if viento["valor"] is not None else None
            rad_val = float(radiacion["valor"]) if radiacion["valor"] is not None else None

            rachas = self._get_sensor_any(["rachas", "racha", "viento_racha", "wind_gust", "gust"], fallback=viento_val)
            rachas_val = float(rachas["valor"]) if rachas["valor"] is not None else None

            dew_val = None
            dew_est = True
            if isinstance(pr, dict) and pr.get("valor") is not None:
                dew_val = float(pr.get("valor"))
                dew_est = pr.get("estimado", True)
            elif temp_val is not None and hum_val is not None:
                try:
                    a, b = 17.27, 237.7
                    alpha = ((a * temp_val) / (b + temp_val)) + math.log(max(1e-6, hum_val) / 100.0)
                    dew_val = (b * alpha) / (a - alpha)
                    dew_est = True
                except Exception:
                    dew_val = None
                    dew_est = True

            nub_info = indices.get("nubosidad_estimada")
            nub_val = nub_info.get("valor") if isinstance(nub_info, dict) else nub_info
            nub_est = nub_info.get("estimado", True) if isinstance(nub_info, dict) else True

            trend_5m = self._trend("temperatura", window_s=300)
            var_t_5min = abs(trend_5m) / 12.0 if trend_5m is not None else 0.0
            trend_30m = self._trend("temperatura", window_s=1800)
            viento_std_30m = self._std_history("viento", window_s=1800)

            lluvia_1h_val = None
            lluvia_1h_est = True
            lluvia_1h = self._get_sensor_any(["lluvia_1h", "rain_1h", "lluvia_h", "rain_hour"])
            if lluvia_1h["valor"] is not None:
                lluvia_1h_val = float(lluvia_1h["valor"])
                lluvia_1h_est = lluvia_1h["estimado"]
            else:
                lluvia_1h_val, lluvia_1h_est = self._rain_accumulated(["lluvia", "rain", "rainfall"], 3600)

            lluvia_24h_val = None
            lluvia_24h_est = True
            lluvia_24h = self._get_sensor_any(["lluvia_24h", "rain_24h", "lluvia_dia", "rain_day"])
            if lluvia_24h["valor"] is not None:
                lluvia_24h_val = float(lluvia_24h["valor"])
                lluvia_24h_est = lluvia_24h["estimado"]
            else:
                lluvia_24h_val, lluvia_24h_est = self._rain_accumulated(["lluvia", "rain", "rainfall"], 86400)

            lluvia_rate_val = None
            lluvia_rate_est = True
            lluvia_rate = self._get_sensor_any(["lluvia_rate", "rain_rate", "rainrate", "rain_rate_h"])
            if lluvia_rate["valor"] is not None:
                lluvia_rate_val = float(lluvia_rate["valor"])
                lluvia_rate_est = lluvia_rate["estimado"]

            pm25_val = None
            pm25_est = True
            pm25 = self._get_sensor_any(["pm25", "pm2_5", "pm2.5", "pm_25"])
            if pm25["valor"] is not None:
                pm25_val = float(pm25["valor"])
                pm25_est = pm25["estimado"]

            hum_suelo_val = None
            hum_suelo_est = True
            hum_suelo = self._get_sensor_any(["humedad_suelo", "soil_moisture", "soil", "wh51"])
            if hum_suelo["valor"] is not None:
                hum_suelo_val = float(hum_suelo["valor"])
                hum_suelo_est = hum_suelo["estimado"]

            uv_val = None
            uv_est = True
            uv = self._get_sensor_any(["uv", "uv_index", "indice_uv"])
            if uv["valor"] is not None:
                uv_val = float(uv["valor"])
                uv_est = uv["estimado"]

            st_val = st.get("valor") if isinstance(st, dict) else None
            if viento_std_30m is not None:
                indices["variabilidad_viento_30m"] = {
                    "valor": round(float(viento_std_30m), 3),
                    "estimado": True,
                    "confianza": self._confianza(True, fiable=True),
                    "explicacion": "Desviación estándar del viento (últimos 30 min)",
                }
            estimado_cetreria = any([
                temp["estimado"], humedad["estimado"], viento["estimado"], radiacion["estimado"],
                rachas["estimado"], nub_est, dew_est, lluvia_1h_est, lluvia_24h_est,
                lluvia_rate_est, pm25_est, hum_suelo_est, uv_est
            ])

            cetreria = calcular_cetreria({
                "viento_medio": viento_val,
                "rachas": rachas_val,
                "temperatura": temp_val,
                "punto_rocio": dew_val,
                "humedad": hum_val,
                "nubosidad_estimada": nub_val,
                "radiacion": rad_val,
                "var_t_5min": var_t_5min,
                "lluvia_24h": lluvia_24h_val,
                "lluvia_1h": lluvia_1h_val,
                "lluvia_rate": lluvia_rate_val,
                "pm25": pm25_val,
                "humedad_suelo": hum_suelo_val,
                "temp_tendencia_30m": trend_30m,
                "uv": uv_val,
                "viento_std_30m": viento_std_30m,
                "sensacion_termica": st_val,
            })

            def _push_cet(nombre, valor, explicacion):
                if valor is None:
                    return
                indices[nombre] = {
                    "valor": round(float(valor), 2),
                    "estimado": estimado_cetreria,
                    "confianza": self._confianza(estimado_cetreria, fiable=True),
                    "explicacion": explicacion,
                }

            _push_cet("viento_cetreria", cetreria.get("viento_cetreria"), "Viento apto para cetrería")
            _push_cet("visibilidad_terreno", cetreria.get("visibilidad_terreno"), "Visibilidad sobre terreno")
            _push_cet("termales_probabilidad", cetreria.get("termales_probabilidad"), "Probabilidad de térmicas")
            _push_cet("barro_campo", cetreria.get("barro_campo"), "Barro en campo (lluvia y secado)")
            _push_cet("confort_ave", cetreria.get("confort_ave"), "Confort térmico del ave")
            _push_cet("indice_viento_cetreria", cetreria.get("indice_viento_cetreria"), "Índice viento cetrería")
            _push_cet("indice_visibilidad_cetreria", cetreria.get("indice_visibilidad_cetreria"), "Índice visibilidad cetrería")
            _push_cet("indice_termales", cetreria.get("indice_termales"), "Índice de térmicas")
            _push_cet("indice_seguridad_vuelo", cetreria.get("indice_seguridad_vuelo"), "Índice seguridad de vuelo")
            _push_cet("indice_cetreria", cetreria.get("indice_cetreria"), "Índice final de cetrería")
        except Exception:
            pass

        # Índices avanzados de sensación térmica y aire
        try:
            if temp["valor"] is not None and humedad["valor"] is not None:
                t = float(temp["valor"])
                h = float(humedad["valor"])
                v = float(viento["valor"] or 0.0)
                r = float(radiacion["valor"] or 0.0)
                estimado = temp["estimado"] or humedad["estimado"] or viento["estimado"] or radiacion["estimado"]

                hi: float = indice_heat_index_c(t, h)
                indices["sensacion_calor"] = {
                    "valor": round(hi, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "Heat Index (NOAA)"
                }
                wc: float = indice_wind_chill_c(t, v)
                indices["sensacion_frio"] = {
                    "valor": round(wc, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "Wind Chill (frío por viento)"
                }
                wb: float = indice_bulbo_humedo_c(t, h)
                indices["bulbo_humedo"] = {
                    "valor": round(wb, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "Bulbo húmedo (aprox.)"
                }
                hdx: float = indice_humidex(t, h)
                indices["humidex"] = {
                    "valor": round(hdx, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "Humidex (sensación de calor)"
                }
                wbgt: float = indice_wbgt(t, h, r, v)
                indices["wbgt"] = {
                    "valor": round(wbgt, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "WBGT aproximado"
                }
                abs_h: float = indice_humedad_absoluta_gm3(t, h)
                indices["humedad_absoluta"] = {
                    "valor": round(abs_h, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "Humedad absoluta (g/m3)"
                }
                vpd: float = indice_vpd_kpa(t, h)
                indices["vpd"] = {
                    "valor": round(vpd, 3),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "Déficit de presión de vapor (kPa)"
                }
                ent: float = indice_entalpia_kjkg(t, h)
                indices["entalpia_aire"] = {
                    "valor": round(ent, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "Entalpía aire húmedo (kJ/kg)"
                }
                pmv_ppd: Dict[str, float] = indice_pmv_ppd_simple(t, h, v)
                indices["pmv"] = {
                    "valor": pmv_ppd["pmv"],
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "PMV (aprox.)"
                }
                indices["ppd"] = {
                    "valor": pmv_ppd["ppd"],
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "PPD (aprox.)"
                }
        except Exception:
            pass

        if pm25["valor"] is not None:
            try:
                aqi: float = indice_aqi_pm25(float(pm25["valor"]))
                indices["aqi_pm25"] = {
                    "valor": round(aqi, 1),
                    "estimado": pm25["estimado"],
                    "confianza": self._confianza(pm25["estimado"], fiable=True),
                    "explicacion": "AQI US EPA (PM2.5)"
                }
            except Exception:
                pass

        # Índices compuestos (fusión de fórmulas)
        try:
            t_ext: float | None = float(temp["valor"]) if temp["valor"] is not None else None
            modo = "templado"
            if t_ext is not None and t_ext >= 20:
                modo = "calor"
                vals = [
                    indices.get("sensacion_calor", {}).get("valor"),
                    indices.get("humidex", {}).get("valor"),
                    indices.get("wbgt", {}).get("valor"),
                ]
                pesos: list[float] = [0.4, 0.3, 0.3]
            elif t_ext is not None and t_ext <= 10:
                modo = "frio"
                vals = [
                    indices.get("sensacion_frio", {}).get("valor"),
                    t_ext,
                ]
                pesos: list[float] = [0.7, 0.3]
            else:
                vals = [
                    indices.get("sensacion_calor", {}).get("valor"),
                    indices.get("sensacion_frio", {}).get("valor"),
                    t_ext,
                ]
                pesos: list[float] = [0.3, 0.3, 0.4]
            comp: float = _media_ponderada(vals, pesos)
            if comp is not None:
                estimado: bool = any([
                    indices.get("sensacion_calor", {}).get("estimado"),
                    indices.get("sensacion_frio", {}).get("estimado"),
                    indices.get("humidex", {}).get("estimado"),
                    indices.get("wbgt", {}).get("estimado"),
                ])
                indices["sensacion_termica_compuesta"] = {
                    "valor": round(comp, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": f"Fusión {modo}: heat index/humidex/wbgt/wind chill"
                }
        except Exception:
            pass

        try:
            aqi = indices.get("aqi_pm25", {}).get("valor")
            aire_cargado = indices.get("aire_cargado", {}).get("valor")
            aire_enrarecido = indices.get("aire_enrarecido", {}).get("valor")
            aqi_norm = None
            if aqi is not None:
                aqi_norm: float = min(100.0, max(0.0, float(aqi) / 5.0))
            vals = [aqi_norm, aire_cargado, aire_enrarecido]
            pesos: list[float] = [0.4, 0.35, 0.25]
            comp: float = _media_ponderada(vals, pesos)
            if comp is not None:
                estimado: bool = any([
                    indices.get("aqi_pm25", {}).get("estimado"),
                    indices.get("aire_cargado", {}).get("estimado"),
                    indices.get("aire_enrarecido", {}).get("estimado"),
                ])
                indices["calidad_aire_compuesta"] = {
                    "valor": round(comp, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "Fusión AQI+CO2+PM2.5"
                }
        except Exception:
            pass

        try:
            vent = indices.get("ventilacion_ideal", {}).get("valor")
            aire_cargado = indices.get("aire_cargado", {}).get("valor")
            aire_enrarecido = indices.get("aire_enrarecido", {}).get("valor")
            vals = [vent, aire_cargado, aire_enrarecido]
            pesos: list[float] = [0.5, 0.3, 0.2]
            comp: float = _media_ponderada(vals, pesos)
            if comp is not None:
                estimado: bool = any([
                    indices.get("ventilacion_ideal", {}).get("estimado"),
                    indices.get("aire_cargado", {}).get("estimado"),
                    indices.get("aire_enrarecido", {}).get("estimado"),
                ])
                indices["ventilacion_compuesta"] = {
                    "valor": round(comp, 2),
                    "estimado": estimado,
                    "confianza": self._confianza(estimado, fiable=True),
                    "explicacion": "Fusión ventilación ideal + aire cargado/enrarecido"
                }
        except Exception:
            pass
        uv = self.indice_uv()
        # SIEMPRE incluir el índice UV, aunque sea 0 o None
        if isinstance(uv, dict) and "confianza" not in uv:
            uv["confianza"] = self._confianza(uv.get("estimado", True), fiable=True)
        indices["indice_uv"] = uv
        rl = self.riesgo_lluvia()
        if rl["valor"] is not None:
            rl["confianza"] = self._confianza(rl["estimado"], fiable=True)
            indices["riesgo_lluvia"] = rl

        # Tendencias base (si hay histórico real)
        trend_t = self._trend("temperatura")
        if trend_t is not None:
            indices["tendencia_temperatura"] = {
                "valor": round(trend_t, 3),
                "estimado": True,
                "confianza": "derivado_fiable",
                "explicacion": "Tendencia T_ext (C/h) desde histórico real"
            }
        trend_h = self._trend("humedad")
        if trend_h is not None:
            indices["tendencia_humedad"] = {
                "valor": round(trend_h, 3),
                "estimado": True,
                "confianza": "derivado_fiable",
                "explicacion": "Tendencia HR_ext (%/h) desde histórico real"
            }
        trend_p = self._trend("presion")
        if trend_p is not None:
            indices["tendencia_presion"] = {
                "valor": round(trend_p, 3),
                "estimado": True,
                "confianza": "derivado_fiable",
                "explicacion": "Tendencia presión (hPa/h) desde histórico real"
            }

        # Estabilidad térmica (si hay tendencia)
        if trend_t is not None:
            try:
                estabilidad: float = max(0.0, 100.0 - min(100.0, abs(trend_t) * 20.0))
                indices["estabilidad_termica"] = {
                    "valor": round(estabilidad, 2),
                    "estimado": True,
                    "confianza": "derivado_fiable",
                    "explicacion": "Estabilidad térmica basada en tendencia de T_ext"
                }
            except Exception:
                pass

        # ------------------------------------------------------------
        # FUSIONES MULTIFÓRMULA (complementar estimaciones)
        # ------------------------------------------------------------
        try:
            # Nubosidad: base por radiación vs teórica + alt por HR + presión
            if indices.get("nubosidad_estimada") is not None:
                nub_base = indices.get("nubosidad_estimada", {}).get("valor")
                trend_p_val = indices.get("tendencia_presion", {}).get("valor") or 0.0
                alt_nub = None
                if humedad["valor"] is not None:
                    h = float(humedad["valor"])
                    alt_nub: float = _clamp_0_100((h - 60) * 1.8 + max(0.0, -float(trend_p_val)) * 25.0)
                comp: float = _media_ponderada([nub_base, alt_nub], [0.7, 0.3])
                if comp is not None:
                    indices["nubosidad_estimada"]["base"] = nub_base
                    indices["nubosidad_estimada"]["fusion"] = round(comp, 2)
                    indices["nubosidad_estimada"]["valor"] = round(comp, 2)
                    indices["nubosidad_estimada"]["explicacion"] = "Fusión radiación+HR+tendencia presión"
        except Exception:
            pass

        try:
            # Riesgo lluvia: HR/lluvia + micro-lluvias + tormenta + presión/nubosidad
            rl = indices.get("riesgo_lluvia", {}).get("valor")
            rm = indices.get("riesgo_micro_lluvias", {}).get("valor")
            at = indices.get("alerta_tormenta", {}).get("valor")
            nub = indices.get("nubosidad_estimada", {}).get("valor")
            trend_p_val = indices.get("tendencia_presion", {}).get("valor") or 0.0
            alt = None
            if humedad["valor"] is not None:
                h = float(humedad["valor"])
                alt: float = _clamp_0_100((h - 60) * 1.4 + max(0.0, -float(trend_p_val)) * 20.0 + (float(nub or 0.0) * 0.3))
            comp: float = _media_ponderada([rl, rm, at, alt], [0.4, 0.2, 0.2, 0.2])
            if comp is not None and "riesgo_lluvia" in indices:
                indices["riesgo_lluvia"]["base"] = rl
                indices["riesgo_lluvia"]["fusion"] = round(comp, 2)
                indices["riesgo_lluvia"]["valor"] = round(comp, 2)
                indices["riesgo_lluvia"]["explicacion"] = "Fusión HR/lluvia + micro + tormenta + presión"
        except Exception:
            pass

        try:
            # Micro-lluvias: base + alt por HR + nubosidad + presión
            rm = indices.get("riesgo_micro_lluvias", {}).get("valor")
            nub = indices.get("nubosidad_estimada", {}).get("valor")
            trend_p_val = indices.get("tendencia_presion", {}).get("valor") or 0.0
            alt = None
            if humedad["valor"] is not None:
                h = float(humedad["valor"])
                alt: float = _clamp_0_100((h - 70) * 1.8 + max(0.0, -float(trend_p_val)) * 15.0 + (float(nub or 0.0) * 0.25))
            comp: float = _media_ponderada([rm, alt], [0.6, 0.4])
            if comp is not None and "riesgo_micro_lluvias" in indices:
                indices["riesgo_micro_lluvias"]["base"] = rm
                indices["riesgo_micro_lluvias"]["fusion"] = round(comp, 2)
                indices["riesgo_micro_lluvias"]["valor"] = round(comp, 2)
                indices["riesgo_micro_lluvias"]["explicacion"] = "Fusión HR + presión + nubosidad"
        except Exception:
            pass

        try:
            # Riesgo helada: base + alt por T_ext + punto rocío + radiación nocturna
            rh = indices.get("riesgo_helada_local", {}).get("valor")
            alt = None
            if temp["valor"] is not None and pr.get("valor") is not None:
                t_ext = float(temp["valor"])
                dp = float(pr["valor"])
                rad_val = self._get_sensor("radiacion", fallback=0)["valor"]
                rad_noc: float = 0.8 if rad_val is not None and float(rad_val) < 20 else 0.1
                alt: float = _clamp_0_100((2 - t_ext) * 10 + (0 - dp) * 4 + rad_noc * 25)
            comp: float = _media_ponderada([rh, alt], [0.7, 0.3])
            if comp is not None and "riesgo_helada_local" in indices:
                indices["riesgo_helada_local"]["base"] = rh
                indices["riesgo_helada_local"]["fusion"] = round(comp, 2)
                indices["riesgo_helada_local"]["valor"] = round(comp, 2)
                indices["riesgo_helada_local"]["explicacion"] = "Fusión helada: punto rocío + T_ext + radiación"
        except Exception:
            pass

        try:
            # Aire cargado: base + alt por CO2 directo
            if "aire_cargado" in indices and co2["valor"] is not None:
                base = indices["aire_cargado"]["valor"]
                alt: float = _clamp_0_100((float(co2["valor"]) - 800) * 0.05)
                comp: float = _media_ponderada([base, alt], [0.7, 0.3])
                if comp is not None:
                    indices["aire_cargado"]["base"] = base
                    indices["aire_cargado"]["fusion"] = round(comp, 2)
                    indices["aire_cargado"]["valor"] = round(comp, 2)
                    indices["aire_cargado"]["explicacion"] = "Fusión CO2 + tiempo sin ventilar"
        except Exception:
            pass

        try:
            # Aire enrarecido: base + alt por PM2.5 directo
            if "aire_enrarecido" in indices and pm25["valor"] is not None:
                base = indices["aire_enrarecido"]["valor"]
                alt: float = _clamp_0_100((float(pm25["valor"]) - 10) * 2)
                comp: float = _media_ponderada([base, alt], [0.7, 0.3])
                if comp is not None:
                    indices["aire_enrarecido"]["base"] = base
                    indices["aire_enrarecido"]["fusion"] = round(comp, 2)
                    indices["aire_enrarecido"]["valor"] = round(comp, 2)
                    indices["aire_enrarecido"]["explicacion"] = "Fusión CO2+PM2.5"
        except Exception:
            pass

        try:
            # Bochorno real: base + alt por heat index interior
            if "bochorno_real" in indices and tempint["valor"] is not None and humedadint["valor"] is not None:
                t_i = float(tempint["valor"])
                h_i = float(humedadint["valor"])
                hi_i: float = indice_heat_index_c(t_i, h_i)
                alt: float = _clamp_0_100((hi_i - 26) * 4)
                base = indices["bochorno_real"]["valor"]
                comp: float = _media_ponderada([base, alt], [0.6, 0.4])
                if comp is not None:
                    indices["bochorno_real"]["base"] = base
                    indices["bochorno_real"]["fusion"] = round(comp, 2)
                    indices["bochorno_real"]["valor"] = round(comp, 2)
                    indices["bochorno_real"]["explicacion"] = "Fusión bochorno + heat index interior"
        except Exception:
            pass

        try:
            # Aire pegajoso: base + alt por humidex interior
            if "aire_pegajoso" in indices and tempint["valor"] is not None and humedadint["valor"] is not None:
                t_i = float(tempint["valor"])
                h_i = float(humedadint["valor"])
                hdx_i: float = indice_humidex(t_i, h_i)
                alt: float = _clamp_0_100((hdx_i - 28) * 4)
                base = indices["aire_pegajoso"]["valor"]
                comp: float = _media_ponderada([base, alt], [0.6, 0.4])
                if comp is not None:
                    indices["aire_pegajoso"]["base"] = base
                    indices["aire_pegajoso"]["fusion"] = round(comp, 2)
                    indices["aire_pegajoso"]["valor"] = round(comp, 2)
                    indices["aire_pegajoso"]["explicacion"] = "Fusión HR/OT + humidex interior"
        except Exception:
            pass

        try:
            # Frío incómodo: base + alt por wind chill interior
            if "frio_incomodo" in indices and tempint["valor"] is not None:
                t_i = float(tempint["valor"])
                v = float(viento["valor"] or 0.0)
                wc: float = indice_wind_chill_c(t_i, v)
                alt: float = _clamp_0_100((15 - wc) * 5)
                base = indices["frio_incomodo"]["valor"]
                comp: float = _media_ponderada([base, alt], [0.6, 0.4])
                if comp is not None:
                    indices["frio_incomodo"]["base"] = base
                    indices["frio_incomodo"]["fusion"] = round(comp, 2)
                    indices["frio_incomodo"]["valor"] = round(comp, 2)
                    indices["frio_incomodo"]["explicacion"] = "Fusión frío + wind chill"
        except Exception:
            pass

        try:
            # Deshidratación: base + alt por VPD interior
            if "deshidratacion_ambiental" in indices and tempint["valor"] is not None and humedadint["valor"] is not None:
                t_i = float(tempint["valor"])
                h_i = float(humedadint["valor"])
                vpd_i: float = indice_vpd_kpa(t_i, h_i)
                alt: float = _clamp_0_100(vpd_i * 40)
                base = indices["deshidratacion_ambiental"]["valor"]
                comp: float = _media_ponderada([base, alt], [0.6, 0.4])
                if comp is not None:
                    indices["deshidratacion_ambiental"]["base"] = base
                    indices["deshidratacion_ambiental"]["fusion"] = round(comp, 2)
                    indices["deshidratacion_ambiental"]["valor"] = round(comp, 2)
                    indices["deshidratacion_ambiental"]["explicacion"] = "Fusión HR baja + VPD"
        except Exception:
            pass

        try:
            # Moho: base + alt por proximidad del punto de rocío interior
            if "riesgo_moho" in indices and tempint["valor"] is not None and humedadint["valor"] is not None:
                t_i = float(tempint["valor"])
                h_i = float(humedadint["valor"])
                a, b = 17.27, 237.7
                alpha = ((a * t_i) / (b + t_i)) + math.log(h_i / 100.0)
                dp_i = (b * alpha) / (a - alpha)
                delta: float = max(0.0, t_i - dp_i)
                alt: float = _clamp_0_100((2.0 - delta) * 40)
                base = indices["riesgo_moho"]["valor"]
                comp: float = _media_ponderada([base, alt], [0.6, 0.4])
                if comp is not None:
                    indices["riesgo_moho"]["base"] = base
                    indices["riesgo_moho"]["fusion"] = round(comp, 2)
                    indices["riesgo_moho"]["valor"] = round(comp, 2)
                    indices["riesgo_moho"]["explicacion"] = "Fusión HR/tiempo + punto rocío interior"
        except Exception:
            pass

        try:
            # Condensación ventanas: base + alt por ΔT vs punto de rocío interior
            if "riesgo_condensacion_ventanas" in indices and tempint["valor"] is not None and humedadint["valor"] is not None:
                t_i = float(tempint["valor"])
                h_i = float(humedadint["valor"])
                a, b = 17.27, 237.7
                alpha = ((a * t_i) / (b + t_i)) + math.log(h_i / 100.0)
                dp_i = (b * alpha) / (a - alpha)
                alt: float = _clamp_0_100((dp_i - (t_i - 4)) * 12)
                base = indices["riesgo_condensacion_ventanas"]["valor"]
                comp: float = _media_ponderada([base, alt], [0.6, 0.4])
                if comp is not None:
                    indices["riesgo_condensacion_ventanas"]["base"] = base
                    indices["riesgo_condensacion_ventanas"]["fusion"] = round(comp, 2)
                    indices["riesgo_condensacion_ventanas"]["valor"] = round(comp, 2)
                    indices["riesgo_condensacion_ventanas"]["explicacion"] = "Fusión condensación + punto rocío interior"
        except Exception:
            pass

        try:
            # Olor a cerrado: base + alt por CO2 + tiempo sin ventilar
            if "riesgo_olor_cerrado" in indices and humedadint["valor"] is not None and co2["valor"] is not None:
                tiempo_sin_ventilar_h = self._hours_over_threshold("co2", 800)
                alt: float = _clamp_0_100((float(co2["valor"]) - 800) * 0.03 + tiempo_sin_ventilar_h * 5)
                base = indices["riesgo_olor_cerrado"]["valor"]
                comp: float = _media_ponderada([base, alt], [0.6, 0.4])
                if comp is not None:
                    indices["riesgo_olor_cerrado"]["base"] = base
                    indices["riesgo_olor_cerrado"]["fusion"] = round(comp, 2)
                    indices["riesgo_olor_cerrado"]["valor"] = round(comp, 2)
                    indices["riesgo_olor_cerrado"]["explicacion"] = "Fusión HR+tiempo + CO2"
        except Exception:
            pass

        try:
            # Estabilidad térmica: base + tendencia interior
            if "estabilidad_termica" in indices:
                trend_ti = self._trend("temperatura_interior")
                alt = None
                if trend_ti is not None:
                    alt: float = max(0.0, 100.0 - min(100.0, abs(trend_ti) * 20.0))
                base = indices["estabilidad_termica"]["valor"]
                comp: float = _media_ponderada([base, alt], [0.6, 0.4])
                if comp is not None:
                    indices["estabilidad_termica"]["base"] = base
                    indices["estabilidad_termica"]["fusion"] = round(comp, 2)
                    indices["estabilidad_termica"]["valor"] = round(comp, 2)
                    indices["estabilidad_termica"]["explicacion"] = "Fusión estabilidad exterior+interior"
        except Exception:
            pass

        # Riesgo de moho (interior)
        if humedadint["valor"] is not None and tempint["valor"] is not None:
            try:
                tiempo_hr_alta_h = self._hours_over_threshold("humedad_interior", 60)
                valor: float = indice_riesgo_moho(
                    float(humedadint["valor"]),
                    float(tiempo_hr_alta_h),
                    float(tempint["valor"])
                )
                indices["riesgo_moho"] = {
                    "valor": round(valor, 2),
                    "estimado": humedadint["estimado"] or tempint["estimado"],
                    "explicacion": "Moho: HR_int + tiempo HR alta + T_int"
                }
            except Exception:
                pass

        # Confort interior (si hay datos suficientes)
        if tempint["valor"] is not None and humedadint["valor"] is not None and co2["valor"] is not None:
            try:
                confort: float = indice_confort_general(float(tempint["valor"]), float(humedadint["valor"]), float(co2["valor"]))
                indices["confort_general"] = {
                    "valor": round(confort, 2),
                    "estimado": tempint["estimado"] or humedadint["estimado"] or co2["estimado"],
                    "explicacion": "Confort: T_int, HR_int, CO2"
                }
                bochorno: float = indice_bochorno_real(float(tempint["valor"]), float(humedadint["valor"]))
                indices["bochorno_real"] = {
                    "valor": round(bochorno, 2),
                    "estimado": tempint["estimado"] or humedadint["estimado"],
                    "explicacion": "Bochorno: T_int, HR_int"
                }
                aire_seco: float = indice_aire_seco(float(humedadint["valor"]))
                indices["aire_seco"] = {
                    "valor": round(aire_seco, 2),
                    "estimado": humedadint["estimado"],
                    "explicacion": "Aire seco: HR_int"
                }
                aire_pegajoso: float = indice_aire_pegajoso(float(humedadint["valor"]), float(tempint["valor"]))
                indices["aire_pegajoso"] = {
                    "valor": round(aire_pegajoso, 2),
                    "estimado": humedadint["estimado"] or tempint["estimado"],
                    "explicacion": "Aire pegajoso: HR_int, T_int"
                }
                frio_incomodo: float = indice_frio_incomodo(float(tempint["valor"]))
                indices["frio_incomodo"] = {
                    "valor": round(frio_incomodo, 2),
                    "estimado": tempint["estimado"],
                    "explicacion": "Frío incómodo: T_int"
                }
            except Exception:
                pass

        # Aire cargado / enrarecido / ventilación ideal
        if co2["valor"] is not None:
            try:
                tiempo_sin_ventilar_h = self._hours_over_threshold("co2", 800)
                aire_cargado: float = indice_aire_cargado(float(co2["valor"]), float(tiempo_sin_ventilar_h))
                indices["aire_cargado"] = {
                    "valor": round(aire_cargado, 2),
                    "estimado": co2["estimado"],
                    "explicacion": "Aire cargado: CO2 + tiempo sin ventilar"
                }
                if pm25["valor"] is not None:
                    aire_enrarecido: float = indice_aire_enrarecido(float(co2["valor"]), float(pm25["valor"]))
                    indices["aire_enrarecido"] = {
                        "valor": round(aire_enrarecido, 2),
                        "estimado": co2["estimado"] or pm25["estimado"],
                        "explicacion": "Aire enrarecido: CO2 + PM2.5"
                    }
                if tempint["valor"] is not None and humedadint["valor"] is not None:
                    vent_ideal: float = indice_ventilacion_ideal(float(co2["valor"]), float(humedadint["valor"]), float(tempint["valor"]))
                    indices["ventilacion_ideal"] = {
                        "valor": round(vent_ideal, 2),
                        "estimado": co2["estimado"] or humedadint["estimado"] or tempint["estimado"],
                        "explicacion": "Ventilación ideal: CO2, HR_int, T_int"
                    }
            except Exception:
                pass

        # Deshidratación ambiental
        if humedadint["valor"] is not None:
            try:
                tiempo_baja_hr = self._hours_under_threshold("humedad_interior", 40)
                deshid: float = indice_deshidratacion_ambiental(float(humedadint["valor"]), float(tiempo_baja_hr))
                indices["deshidratacion_ambiental"] = {
                    "valor": round(deshid, 2),
                    "estimado": humedadint["estimado"],
                    "explicacion": "Deshidratación: HR baja sostenida"
                }
            except Exception:
                pass

        # Confort nocturno
        if tempint["valor"] is not None and ruido["valor"] is not None and luz["valor"] is not None:
            try:
                confort_noct: float = indice_confort_nocturno(float(tempint["valor"]), float(ruido["valor"]), float(luz["valor"]))
                indices["confort_nocturno"] = {
                    "valor": round(confort_noct, 2),
                    "estimado": tempint["estimado"] or ruido["estimado"] or luz["estimado"],
                    "explicacion": "Confort nocturno: T_int, ruido, luz"
                }
            except Exception:
                pass

        # Aire pegajoso exterior (si hay datos)
        if temp["valor"] is not None and humedad["valor"] is not None:
            try:
                aire_pegajoso_ext: float = indice_aire_pegajoso(float(humedad["valor"]), float(temp["valor"]))
                indices["aire_pegajoso_exterior"] = {
                    "valor": round(aire_pegajoso_ext, 2),
                    "estimado": temp["estimado"] or humedad["estimado"],
                    "explicacion": "Aire pegajoso exterior: HR_ext, T_ext"
                }
            except Exception:
                pass

        # Riesgo de olor a cerrado
        if humedadint["valor"] is not None:
            try:
                tiempo_sin_ventilar_h = self._hours_over_threshold("co2", 800)
                valor: float = indice_riesgo_olor_cerrado(float(humedadint["valor"]), float(tiempo_sin_ventilar_h))
                indices["riesgo_olor_cerrado"] = {
                    "valor": round(valor, 2),
                    "estimado": humedadint["estimado"],
                    "explicacion": "Olor a cerrado: HR_int + tiempo CO2 alto"
                }
            except Exception:
                pass

        # Salud del edificio
        try:
            humedad_media = self._mean_history("humedad_interior")
            if humedad_media is not None:
                tiempo_hr_alta_h = self._hours_over_threshold("humedad_interior", 60)
                valor: float = indice_salud_edificio(float(humedad_media), float(tiempo_hr_alta_h), 0)
                indices["salud_edificio"] = {
                    "valor": round(valor, 2),
                    "estimado": False,
                    "explicacion": "Salud edificio: HR media + tiempo HR alta"
                }
        except Exception:
            pass

        # Riesgo de condensación en ventanas (interior vs exterior)
        if tempint["valor"] is not None and humedadint["valor"] is not None and temp["valor"] is not None:
            try:
                valor: float = indice_riesgo_condensacion_ventanas(
                    float(tempint["valor"]),
                    float(humedadint["valor"]),
                    float(temp["valor"])
                )
                indices["riesgo_condensacion_ventanas"] = {
                    "valor": round(valor, 2),
                    "estimado": tempint["estimado"] or humedadint["estimado"] or temp["estimado"],
                    "explicacion": "Condensación: T_int, HR_int, T_ext"
                }
            except Exception:
                pass

        # Riesgo de helada local (si hay datos suficientes)
        if pr["valor"] is not None and temp["valor"] is not None and viento["valor"] is not None:
            try:
                radiacion_val = self._get_sensor("radiacion", fallback=0)["valor"]
                radiacion_nocturna: float = 0.8 if radiacion_val is not None and float(radiacion_val) < 20 else 0.1
                valor: float = indice_riesgo_helada_local(
                    float(pr["valor"]),
                    float(temp["valor"]),
                    float(radiacion_nocturna),
                    float(viento["valor"])
                )
                indices["riesgo_helada_local"] = {
                    "valor": round(valor, 2),
                    "estimado": pr["estimado"] or temp["estimado"] or viento["estimado"],
                    "explicacion": "Helada: punto de rocío, T_ext, radiación nocturna, viento"
                }
            except Exception:
                pass

        # Riesgo de micro-lluvias (si hay tendencia real)
        if humedad["valor"] is not None:
            try:
                hr_ext = float(humedad["valor"])
                cambio_viento = self._trend("viento") or 0.0
                presion_tendencia = self._trend("presion")
                if presion_tendencia is None:
                    presion_tendencia = self._get_sensor("tendencia_presion")["valor"]
                if presion_tendencia is None:
                    presion_tendencia = 0.0
                irll_base: float = max(0.0, hr_ext - 70.0)
                valor: float = indice_riesgo_micro_lluvias(hr_ext, irll_base, float(cambio_viento), float(presion_tendencia))
                indices["riesgo_micro_lluvias"] = {
                    "valor": round(valor, 2),
                    "estimado": humedad["estimado"],
                    "explicacion": "Micro-lluvias: HR, cambio viento, tendencia presión"
                }
            except Exception:
                pass

        # Rachas peligrosas (exterior)
        if viento["valor"] is not None:
            try:
                v_ext = float(viento["valor"])
                riesgo_rachas: float = max(0.0, min(100.0, (v_ext - 20) * 4))
                indices["riesgo_rachas_peligrosas"] = {
                    "valor": round(riesgo_rachas, 2),
                    "estimado": viento["estimado"],
                    "explicacion": "Rachas peligrosas: viento exterior"
                }
            except Exception:
                pass

        # Viento incómodo para dormir (exterior)
        if viento["valor"] is not None:
            try:
                v_ext = float(viento["valor"])
                riesgo: float = max(0.0, min(100.0, (v_ext - 10) * 5))
                indices["viento_incomodo_dormir"] = {
                    "valor": round(riesgo, 2),
                    "estimado": viento["estimado"],
                    "explicacion": "Viento incómodo para dormir: viento exterior"
                }
            except Exception:
                pass

        # Visibilidad local (baja si niebla alta)
        try:
            niebla_val = indices.get("riesgo_niebla", {}).get("valor", 0)
            vis: float = max(0.0, min(100.0, 100.0 - float(niebla_val)))
            indices["visibilidad_local"] = {
                "valor": round(vis, 2),
                "estimado": True,
                "confianza": "derivado_fiable",
                "explicacion": "Visibilidad local inversa a riesgo de niebla"
            }
        except Exception:
            pass

        # Estrés térmico exterior (simple)
        if temp["valor"] is not None and humedad["valor"] is not None:
            try:
                t_ext = float(temp["valor"])
                h_ext = float(humedad["valor"])
                stress: float = max(0.0, min(100.0, (t_ext - 26) * 4 + (h_ext - 60) * 0.6))
                indices["estres_termico_exterior"] = {
                    "valor": round(stress, 2),
                    "estimado": temp["estimado"] or humedad["estimado"],
                    "explicacion": "Estrés térmico: T_ext y HR_ext"
                }
            except Exception:
                pass

        # Inversión térmica local (si hay interior/exterior)
        if temp["valor"] is not None and tempint["valor"] is not None:
            try:
                delta: float = float(tempint["valor"]) - float(temp["valor"])
                inversion: float = max(0.0, min(100.0, (delta - 2) * 10))
                indices["inversion_termica"] = {
                    "valor": round(inversion, 2),
                    "estimado": temp["estimado"] or tempint["estimado"],
                    "explicacion": "Inversión térmica: T_int - T_ext"
                }
            except Exception:
                pass

        # Micro-ráfagas (cambio brusco viento)
        if viento["valor"] is not None:
            try:
                cambio_v = self._trend("viento") or 0.0
                micro_rafaga: float = max(0.0, min(100.0, abs(cambio_v) * 10))
                indices["micro_rafagas"] = {
                    "valor": round(micro_rafaga, 2),
                    "estimado": True,
                    "confianza": "derivado_fiable",
                    "explicacion": "Micro-ráfagas: cambio rápido de viento"
                }
            except Exception:
                pass

        # Niebla de advección (HR alta + viento)
        if humedad["valor"] is not None and viento["valor"] is not None:
            try:
                hr = float(humedad["valor"])
                v_ext = float(viento["valor"])
                adv: float = max(0.0, min(100.0, (hr - 85) * 2 + (v_ext - 5) * 3))
                indices["niebla_adveccion"] = {
                    "valor": round(adv, 2),
                    "estimado": humedad["estimado"] or viento["estimado"],
                    "explicacion": "Niebla advección: HR alta + viento"
                }
            except Exception:
                pass
        # Índices interiores derivados (si hay sensores suficientes)
        try:
            contexto = {
                "ot": tempint["valor"],
                "humedad_interior": humedadint["valor"],
                "co2": co2["valor"],
                "pm25": pm25["valor"],
                "ruido": ruido["valor"],
                "luz": luz["valor"],
                "tiempo_sin_ventilar_h": self._get_sensor("tiempo_sin_ventilar_h", fallback=0)["valor"],
                "tiempo_hr_baja_h": self._get_sensor("tiempo_hr_baja_h", fallback=0)["valor"],
            }
            indices_interior: Dict[str, Any] = evaluar_indices_ambientales(contexto)
            estimado_interior: bool = any([
                tempint["estimado"],
                humedadint["estimado"],
                co2["estimado"],
                pm25["estimado"],
                ruido["estimado"],
                luz["estimado"],
            ])
            for nombre, valor in indices_interior.items():
                indices[nombre] = {
                    "valor": round(float(valor), 2),
                    "estimado": estimado_interior,
                    "explicacion": "Índice interior derivado de sensores"
                }
        except Exception:
            pass

        # Índices avanzados y creativos
        try:
            # ...existing code...
            # ALERTAS Y PREVISIONES INÉDITAS
            # Alerta de tormenta
            uv_val = uv["valor"] if uv["valor"] is not None else 0.0
            radiacion_val = self._get_sensor("radiacion")["valor"] or 0.0
            presion_val = self._get_sensor("presion")["valor"] or 1013.0
            tendencia_presion_val = self._get_sensor("tendencia_presion")["valor"] or 0.0
            rayos_val = self._get_sensor("rayos")["valor"] or 0.0
            alerta_tormenta: float = indice_alerta_tormenta(float(uv_val), float(radiacion_val), float(presion_val), float(tendencia_presion_val), float(rayos_val))
            indices["alerta_tormenta"] = {"valor": round(alerta_tormenta,2), "estimado": False, "explicacion": "Alerta de tormenta: UV, radiación, presión, tendencia y rayos"}
            # Alerta de calor extremo
            temp_val = temp["valor"] if temp["valor"] is not None else 0.0
            humedad_val = humedad["valor"] if humedad["valor"] is not None else 0.0
            alerta_calor: float = indice_alerta_calor_extremo(float(temp_val), float(uv_val), float(humedad_val))
            indices["alerta_calor_extremo"] = {"valor": round(alerta_calor,2), "estimado": False, "explicacion": "Alerta de calor extremo: T, UV, HR"}
            # Alerta de frío extremo
            viento_val = viento["valor"] if viento["valor"] is not None else 0.0
            alerta_frio: float = indice_alerta_frio_extremo(float(temp_val), float(viento_val), float(humedad_val))
            indices["alerta_frio_extremo"] = {"valor": round(alerta_frio,2), "estimado": False, "explicacion": "Alerta de frío extremo: T, viento, HR"}
            # Alerta de polvo/suciedad
            pm25_val = pm25["valor"] if pm25["valor"] is not None else 0.0
            alerta_polvo: float = indice_alerta_polvo(float(pm25_val), float(viento_val))
            indices["alerta_polvo"] = {"valor": round(alerta_polvo,2), "estimado": False, "explicacion": "Alerta de polvo/suciedad: PM2.5 y viento"}
        except Exception as e:
            indices["error_indices_avanzados"] = {"valor": None, "estimado": True, "explicacion": f"Error en índices avanzados: {e}"}
        # Sonógrafo y sismógrafo siempre presentes
        indices["sonometro"] = self.indice_sonometro()
        indices["sismografo"] = self.indice_sismografo()
        try:
            self.reforzar_indices(indices)
        except Exception:
            pass
        return self._apply_lag(indices)
"""
Módulo unificado de índices ambientales MeteoSer.

Incluye:
- Confort humano
- Diagnóstico del edificio
- Meteorología local avanzada
- Índices derivados (IETF, IRCA, IREA, IRCA-HUMANO, IRHL, IRLL, etc.)

Todos los índices devuelven un valor 0–100.
"""

from typing import Dict, Any
import math


def _clamp_0_100(value: float) -> float:
    return max(0.0, min(100.0, value))


# ------------------------------------------------------------
# CONFORT HUMANO
# ------------------------------------------------------------

def indice_confort_general(ot: float, humedad: float, co2: float) -> float:
    """
    Índice de confort general basado en:
    - OT (temperatura operativa, °C)
    - Humedad relativa (%)
    - CO2 (ppm)
    Fórmula: penaliza desviaciones de OT, HR y CO2 respecto a valores ideales.
    Ejemplo: indice_confort_general(22, 50, 600) -> 100.0
    """
    score = 100.0

    # OT ideal 20–24
    if ot < 18:
        score -= (18 - ot) * 4
    elif ot > 26:
        score -= (ot - 26) * 4

    # HR ideal 40–60
    if humedad < 40:
        score -= (40 - humedad) * 0.8
    elif humedad > 60:
        score -= (humedad - 60) * 0.8

    # CO2 ideal < 800 ppm
    if co2 > 800:
        score -= (co2 - 800) * 0.02

    return _clamp_0_100(score)


def indice_bochorno_real(ot: float, humedad: float) -> float:
    """
    Bochorno real: sensación de calor pegajoso.
    - ot: temperatura operativa (°C)
    - humedad: humedad relativa (%)
    Sube si ot > 24 y humedad > 60.
    Ejemplo: indice_bochorno_real(28, 70) -> valor alto
    """
    score = 0.0
    if ot > 24 and humedad > 60:
        score += (ot - 24) * 5
        score += (humedad - 60) * 0.8
    return _clamp_0_100(score)


def indice_aire_seco(humedad: float) -> float:
    """
    Aire seco: riesgo de deshidratación ambiental.
    - humedad: humedad relativa (%)
    Sube si HR < 40.
    Ejemplo: indice_aire_seco(30) -> 20.0
    """
    if humedad >= 40:
        return 0.0
    return _clamp_0_100((40 - humedad) * 2)


def indice_aire_pegajoso(humedad: float, ot: float) -> float:
    """
    Aire pegajoso: humedad alta + temperatura moderada/alta.
    - humedad: humedad relativa (%)
    - ot: temperatura operativa (°C)
    Sube si HR > 60 y ot > 24.
    """
    if humedad < 60:
        return 0.0
    base: float = (humedad - 60) * 1.2
    if ot > 24:
        base += (ot - 24) * 3
    return _clamp_0_100(base)


def indice_confort_nocturno(ot: float, ruido: float, luz: float) -> float:
    """
    Confort nocturno: combina temperatura, ruido y luz para valorar el descanso.
    - ot: temperatura operativa (°C)
    - ruido: nivel relativo (0-100)
    - luz: nivel relativo (0-100)
    """
    score = 100.0

    # OT ideal noche 18–23
    if ot < 18:
        score -= (18 - ot) * 4
    elif ot > 23:
        score -= (ot - 23) * 4

    # Ruido (0–100 relativo)
    score -= ruido * 0.5

    # Luz (0–100 relativo)
    score -= luz * 0.4

    return _clamp_0_100(score)


def indice_frio_incomodo(ot: float) -> float:
    """
    Frío incómodo por OT baja.
    - ot: temperatura operativa (°C)
    Sube si ot < 20.
    """
    if ot >= 20:
        return 0.0
    return _clamp_0_100((20 - ot) * 6)


def indice_aire_cargado(co2: float, tiempo_sin_ventilar_h: float) -> float:
    """
    Aire cargado: CO2 alto + tiempo sin ventilación.
    - co2: ppm
    - tiempo_sin_ventilar_h: horas
    """
    base = 0.0
    if co2 > 800:
        base += (co2 - 800) * 0.03
    base += tiempo_sin_ventilar_h * 3
    return _clamp_0_100(base)


def indice_deshidratacion_ambiental(humedad: float, tiempo_h: float) -> float:
    """
    Deshidratación ambiental: HR baja mantenida.
    - humedad: humedad relativa (%)
    - tiempo_h: horas con HR baja
    """
    if humedad >= 40:
        return 0.0
    base: float = (40 - humedad) * 1.5 + tiempo_h * 2
    return _clamp_0_100(base)


def indice_aire_enrarecido(co2: float, pm25: float) -> float:
    """
    Aire enrarecido: mezcla de CO2 y PM2.5.
    - co2: ppm
    - pm25: µg/m³
    """
    score = 0.0
    if co2 > 800:
        score += (co2 - 800) * 0.03
    if pm25 > 10:
        score += (pm25 - 10) * 2
    return _clamp_0_100(score)


def indice_ventilacion_ideal(co2: float, humedad: float, ot: float) -> float:
    """
    Ventilación ideal: cuánto conviene ventilar AHORA.
    - co2: ppm
    - humedad: %
    - ot: °C
    """
    score = 0.0
    if co2 > 800:
        score += (co2 - 800) * 0.04
    if humedad > 60 or humedad < 40:
        score += abs(humedad - 50) * 1.0
    if ot > 26 or ot < 18:
        score += abs(ot - 22) * 3
    return _clamp_0_100(score)


# ------------------------------------------------------------
# DIAGNÓSTICO DEL EDIFICIO
# ------------------------------------------------------------

def indice_salud_edificio(humedad_media: float,
                          tiempo_hr_alta_h: float,
                          condensacion_eventos: int) -> float:
    """
    Salud del edificio: inverso de humedad crónica + condensación.
    - humedad_media: %
    - tiempo_hr_alta_h: horas con HR alta
    - condensacion_eventos: nº eventos
    """
    riesgo = 0.0
    if humedad_media > 60:
        riesgo += (humedad_media - 60) * 1.5
    riesgo += tiempo_hr_alta_h * 2
    riesgo += condensacion_eventos * 5
    return _clamp_0_100(100.0 - _clamp_0_100(riesgo))


def indice_riesgo_moho(humedad: float, tiempo_hr_alta_h: float,
                       temperatura: float) -> float:
    """
    Riesgo de moho: HR alta + tiempo + T moderada.
    - humedad: %
    - tiempo_hr_alta_h: horas
    - temperatura: °C
    """
    if humedad < 60:
        return 0.0
    base: float = (humedad - 60) * 1.5 + tiempo_hr_alta_h * 3
    if 15 <= temperatura <= 25:
        base *= 1.2
    return _clamp_0_100(base)


def indice_riesgo_condensacion_ventanas(t_int: float,
                                        hr_int: float,
                                        t_ext: float) -> float:
    """
    Condensación en ventanas: punto de rocío interior vs T de vidrio (aprox T_ext).
    - t_int: temperatura interior (°C)
    - hr_int: humedad interior (%)
    - t_ext: temperatura exterior (°C)
    """
    # Cálculo simple de punto de rocío
    a, b = 17.27, 237.7
    alpha: float = ((a * t_int) / (b + t_int)) + math.log(hr_int / 100.0)
    dew_point: float = (b * alpha) / (a - alpha)

    delta: float = dew_point - t_ext
    if delta <= 0:
        return 0.0
    return _clamp_0_100(delta * 10)


def indice_riesgo_olor_cerrado(humedad: float,
                               tiempo_sin_ventilar_h: float) -> float:
    """
    Olor a cerrado: HR + tiempo sin ventilación.
    - humedad: %
    - tiempo_sin_ventilar_h: horas
    """
    base = 0.0
    if humedad > 60:
        base += (humedad - 60) * 1.2
    base += tiempo_sin_ventilar_h * 2
    return _clamp_0_100(base)


# ------------------------------------------------------------
# METEOROLOGÍA LOCAL AVANZADA
# ------------------------------------------------------------

def indice_riesgo_helada_local(punto_rocio: float,
                               t_ext: float,
                               radiacion_nocturna: float,
                               viento: float) -> float:
    """
    IRHL: riesgo de helada local.
    - punto_rocio: °C
    - t_ext: temperatura exterior (°C)
    - radiacion_nocturna: 0-1
    - viento: m/s
    """
    base = 0.0
    if t_ext <= 2:
        base += (2 - t_ext) * 10
    if punto_rocio < 0:
        base += abs(punto_rocio) * 4
    if radiacion_nocturna > 0.5:
        base += radiacion_nocturna * 20
    if viento < 2:
        base += 10  # calma favorece helada
    return _clamp_0_100(base)


def indice_riesgo_micro_lluvias(hr_ext: float,
                                irll_base: float,
                                cambio_viento: float,
                                presion_tendencia: float) -> float:
    """
    IRLL: riesgo de micro-lluvias (sprinkles).
    - hr_ext: humedad exterior (%)
    - irll_base: base empírica
    - cambio_viento: m/s
    - presion_tendencia: hPa/h
    """
    base: float = irll_base
    if hr_ext > 80:
        base += (hr_ext - 80) * 1.5
    base += abs(cambio_viento) * 2
    base -= presion_tendencia * 5  # si sube presión, baja riesgo
    return _clamp_0_100(base)


# ------------------------------------------------------------
# ÍNDICES DERIVADOS AVANZADOS
# ------------------------------------------------------------

def indice_estabilidad_termica_futura(estabilidad_actual: float,
                                      ireav: float,
                                      delta_t_in_out: float,
                                      viento_ext: float) -> float:
    """
    IETF: predice si la vivienda mantendrá su temperatura.
    - estabilidad_actual: %
    - ireav: índice de pérdidas
    - delta_t_in_out: diferencia T int-ext (°C)
    - viento_ext: m/s
    """
    score: float = estabilidad_actual * 0.5
    score += (100.0 - ireav) * 0.3  # si hay pocas pérdidas, más estabilidad
    score -= abs(delta_t_in_out) * 2
    if viento_ext > 20:
        score -= (viento_ext - 20) * 1.5
    return _clamp_0_100(score)


def indice_condensacion_oculta_armarios(irsh: float,
                                        irin: float,
                                        ersf: float,
                                        historial_nocturno: float) -> float:
    """
    IRCA: riesgo de condensación oculta en armarios.
    """
    try:
        irsh = float(irsh) if irsh is not None else 0.0
    except Exception:
        irsh = 0.0
    try:
        irin = float(irin) if irin is not None else 0.0
    except Exception:
        irin = 0.0
    try:
        ersf = float(ersf) if ersf is not None else 0.0
    except Exception:
        ersf = 0.0
    try:
        historial_nocturno = float(historial_nocturno) if historial_nocturno is not None else 0.0
    except Exception:
        historial_nocturno = 0.0
    base: float = irsh * 0.4 + irin * 0.3 + ersf * 0.2 + historial_nocturno * 0.1
    return _clamp_0_100(base)


def indice_renovacion_efectiva_aire(co2: float,
                                    pm25: float,
                                    irin: float,
                                    irae: float,
                                    actividad_humana: float) -> float:
    """
    IREA: cuánto se ha renovado realmente el aire.
    0 = nada, 100 = renovación excelente.
    """
    score = 100.0
    if co2 > 800:
        score -= (co2 - 800) * 0.03
    if pm25 > 10:
        score -= (pm25 - 10) * 1.5
    score += (irae - 50) * 0.5
    score += (irin - 50) * 0.3
    score -= actividad_humana * 0.4
    return _clamp_0_100(score)


def indice_ritmo_circadiano_ambiental(ot: float,
                                      luz: float,
                                      ruido: float,
                                      estabilidad_termica: float,
                                      irin: float) -> float:
    """
    IRCA-HUMANO: si el ambiente favorece sueño o vigilia.
    0 = muy activador, 100 = muy propicio para dormir.
    """
    # Fallbacks seguros
    try:
        ot = float(ot)
    except Exception:
        ot = 22.0
    try:
        luz = float(luz)
    except Exception:
        luz = 50.0
    try:
        ruido = float(ruido)
    except Exception:
        ruido = 30.0
    try:
        estabilidad_termica = float(estabilidad_termica)
    except Exception:
        estabilidad_termica = 50.0
    try:
        irin = float(irin)
    except Exception:
        irin = 50.0

    score = 0.0

    # OT ligeramente fresca favorece sueño
    if 18 <= ot <= 23:
        score += 30
    elif ot < 18:
        score -= (18 - ot) * 2
    else:
        score -= (ot - 23) * 2

    # Luz baja favorece sueño
    score += (100 - luz) * 0.4

    # Ruido bajo favorece sueño
    score += (100 - ruido) * 0.3

    # Estabilidad térmica y IRIN
    score += estabilidad_termica * 0.2
    score += (100 - irin) * 0.1  # menos intrusión, más descanso

    return _clamp_0_100(score)


# ------------------------------------------------------------
# ENVOLVENTE PRINCIPAL PARA CONTEXTO
# ------------------------------------------------------------

def evaluar_indices_ambientales(contexto: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evalúa un conjunto de índices clave a partir de un contexto MeteoSer.
    El contexto es un diccionario con claves como:
    - ot, humedad_interior, co2, pm25, ruido, luz, etc.
    """
    ot: Any | None = contexto.get("ot")
    hr: Any | None = contexto.get("humedad_interior")
    co2: Any | None = contexto.get("co2")
    pm25 = contexto.get("pm25", 5.0)
    ruido = contexto.get("ruido", 20.0)
    luz = contexto.get("luz", 30.0)

    resultados: Dict[str, Any] = {}

    if ot is not None and hr is not None and co2 is not None:
        resultados["confort_general"] = indice_confort_general(ot, hr, co2)
        resultados["bochorno_real"] = indice_bochorno_real(ot, hr)
        resultados["aire_seco"] = indice_aire_seco(hr)
        resultados["aire_pegajoso"] = indice_aire_pegajoso(hr, ot)
        resultados["confort_nocturno"] = indice_confort_nocturno(ot, ruido, luz)
        resultados["frio_incomodo"] = indice_frio_incomodo(ot)
        resultados["aire_cargado"] = indice_aire_cargado(co2, contexto.get("tiempo_sin_ventilar_h", 0.0))
        resultados["deshidratacion_ambiental"] = indice_deshidratacion_ambiental(
            hr, contexto.get("tiempo_hr_baja_h", 0.0)
        )
        resultados["aire_enrarecido"] = indice_aire_enrarecido(co2, pm25)
        resultados["ventilacion_ideal"] = indice_ventilacion_ideal(co2, hr, ot)

    # Aquí se pueden ir añadiendo más índices a medida que se integren
    return resultados
