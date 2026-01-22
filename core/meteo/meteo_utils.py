import math
import datetime
from core.meteo.meteo_model import SensorRaw, SensorNormalized, DerivedMetric, MeteoSnapshot
from core.indices.environmental_indices import (
    indice_heat_index_c,
    indice_wind_chill_c,
    indice_humidex,
    indice_wbgt,
)

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
        # Magnus-Tetens
        a, b = 17.27, 237.7
        alpha = ((a * temp.value) / (b + temp.value)) + math.log(rh.value / 100.0)
        dp = (b * alpha) / (a - alpha)
        derived["punto_rocio"] = DerivedMetric(name="punto_rocio", value=dp, unit="C", ts=ts)
    if temp:
        # Recolectar inputs
        t_val = temp.value if temp and temp.value is not None else None
        rh_val = rh.value if rh and rh.value is not None else None
        viento_val = None
        if snapshot.sensors.get("viento") and snapshot.sensors.get("viento").value is not None:
            viento_val = float(snapshot.sensors.get("viento").value)
        rad_val = snapshot.sensors.get("radiacion") and snapshot.sensors.get("radiacion").value
        uv_val = snapshot.sensors.get("uv") and snapshot.sensors.get("uv").value

        candidates = {}
        try:
            # Wind chill (convertir m/s a km/h)
            if t_val is not None and viento_val is not None:
                wc = indice_wind_chill_c(float(t_val), float(viento_val) * 3.6)
                candidates['wind_chill'] = {
                    'value': float(wc), 'depends_on': ['temperatura', 'viento'],
                    'explicacion': f'Wind-chill: T={t_val}C, V={viento_val}m/s'
                }
            # Heat index
            if t_val is not None and rh_val is not None:
                hi = indice_heat_index_c(float(t_val), float(rh_val))
                candidates['heat_index'] = {
                    'value': float(hi), 'depends_on': ['temperatura', 'humedad'],
                    'explicacion': f'Heat-index (NOAA): T={t_val}C, RH={rh_val}%'
                }
            # Humidex
            if t_val is not None and rh_val is not None:
                hdx = indice_humidex(float(t_val), float(rh_val))
                candidates['humidex'] = {
                    'value': float(hdx), 'depends_on': ['temperatura', 'humedad'],
                    'explicacion': f'Humidex: T={t_val}C, RH={rh_val}%'
                }
            # WBGT (si hay humedad, radiación opcional)
            if t_val is not None and rh_val is not None:
                v_kmh = float(viento_val) * 3.6 if viento_val is not None else 0.0
                rad_n = float(rad_val) if rad_val is not None else 0.0
                wb = indice_wbgt(float(t_val), float(rh_val), rad_n, v_kmh)
                candidates['wbgt'] = {
                    'value': float(wb), 'depends_on': ['temperatura', 'humedad', 'radiacion'],
                    'explicacion': f'WBGT aprox: T={t_val}C, RH={rh_val}%, Rad={rad_n}'
                }
        except Exception:
            pass

        # Selección por prioridad dinámica según temperatura
        selected = None
        eps = 0.15
        try:
            if t_val is None:
                raise Exception('temperatura no disponible')
            t_num = float(t_val)
            if t_num <= 10:
                order = ['wind_chill', 'wbgt', 'heat_index', 'humidex']
            elif t_num >= 25:
                order = ['wbgt', 'heat_index', 'humidex', 'wind_chill']
            else:
                order = ['heat_index', 'humidex', 'wbgt', 'wind_chill']
            # Elegir la primera que varíe respecto a T más allá de eps
            for key in order:
                c = candidates.get(key)
                if not c:
                    continue
                if abs(c['value'] - t_num) > eps:
                    selected = (key, c)
                    break
            # Si ninguna varía, elegir la más precisa disponible por orden
            if selected is None:
                for key in order:
                    c = candidates.get(key)
                    if c:
                        selected = (key, c)
                        break
        except Exception:
            selected = None

        # Construir DerivedMetric
        if selected is not None:
            key, info = selected
            dm = DerivedMetric(name='sensacion_termica', value=round(info['value'], 2), unit='C', ts=ts)
            dm.quality = 'ok'
            dm.depends_on = info.get('depends_on', [])
            dm.metodo = key
            dm.explicacion = info.get('explicacion', '')
            derived['sensacion_termica'] = dm
        else:
            dm = DerivedMetric(name='sensacion_termica', value=round(float(t_val) if t_val is not None else None, 2), unit='C', ts=ts)
            dm.quality = 'sospechoso'
            dm.depends_on = ['temperatura']
            dm.metodo = 'temperatura_directa'
            dm.explicacion = 'Ninguna fórmula disponible o ninguna varía respecto a la temperatura: revisar sensores.'
            derived['sensacion_termica'] = dm
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
