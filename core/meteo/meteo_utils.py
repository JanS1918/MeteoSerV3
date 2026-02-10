import math
from core.meteo.meteo_model import SensorRaw, SensorNormalized, DerivedMetric, MeteoSnapshot
from core.indices.environmental_indices import _dew_point

def f_to_c(temp_f: float) -> float:
    return (temp_f - 32.0) * 5.0 / 9.0

def normalize_sensor(name: str, raw: SensorRaw) -> SensorNormalized:
    v = raw.value
    unit = raw.unit
    if name.startswith("tempf") or name.startswith("tempinf"):
        v = f_to_c(v)
        unit = "C"
    elif name.startswith("temperatura"):
        if unit and unit.upper() == "F":
            v = f_to_c(v)
            unit = "C"
        elif unit and unit.upper() == "C":
            unit = "C"
        else:
            return SensorNormalized(value=v, unit=unit, ts=raw.ts, source=raw.source, quality="sospechoso")
    elif name.startswith("humedad"):
        unit = "%"
    elif "viento" in name:
        if unit and unit.lower() in ["km/h", "kmh", "kph"]:
            v = v / 3.6
        elif unit and unit.lower() in ["mph"]:
            v = v * 0.44704
        unit = "m/s"
    elif "lluvia" in name:
        unit = "mm"
    elif "presion" in name:
        if unit and unit.lower() in ["inhg"]:
            v = v * 33.8639
        unit = "hpa"
    elif name == "co2":
        unit = "ppm"
    return SensorNormalized(value=v, unit=unit, ts=raw.ts, source=raw.source, quality="ok")

def compute_derived(snapshot: MeteoSnapshot) -> dict:
    # Ejemplo: punto de rocío y sensación térmica
    derived = {}
    temp = snapshot.sensors.get("temperatura")
    rh = snapshot.sensors.get("humedad")
    viento = snapshot.sensors.get("viento")
    radiacion = snapshot.sensors.get("radiacion")
    ts = snapshot.ts
    if temp and rh:
        try:
            dp = _dew_point(float(temp.value), float(rh.value))
        except Exception:
            dp = None
        if dp is not None:
            derived["punto_rocio"] = DerivedMetric(name="punto_rocio", value=dp, unit="C", ts=ts)
    if temp and rh and viento:
        # Sensación térmica simple
        st = temp.value - (viento.value * 0.7)
        derived["sensacion_termica"] = DerivedMetric(name="sensacion_termica", value=st, unit="C", ts=ts)
    if radiacion and (snapshot.sensors.get("uv") is None):
        if radiacion.value is not None:
            uv_est = min(12.0, max(0.0, radiacion.value / 25.0))
            derived["uv_derivado"] = DerivedMetric(
                name="uv_derivado",
                value=uv_est,
                unit="",
                ts=ts,
                quality="derivado_fiable",
                depends_on=["radiacion"],
            )
    return derived
