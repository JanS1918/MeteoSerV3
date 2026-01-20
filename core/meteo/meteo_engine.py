from core.meteo.meteo_model import (
    MeteoSnapshot,
    SensorRaw,
    DerivedMetric,
    normalize_sensor,
    compute_derived,
)
import time


def get_full_meteo_snapshot(system) -> dict:
    """
    Construye un snapshot meteorológico completo a partir de los sensores actuales del sistema.
    """
    sensores = system.sensores.copy()
    ts = time.time()
    # Convertir sensores a SensorRaw (asumiendo que todos son en unidades internas)
    sensores_raw = {}
    for nombre, valor in sensores.items():
        if valor is None:
            continue
        meta = system.obtener_sensor_metadata(nombre) or {}
        # Asumimos unidad por tipo
        if "temp" in nombre:
            unit = "C"
        elif "humedad" in nombre:
            unit = "%"
        elif "viento" in nombre:
            unit = "m/s"
        elif "lluvia" in nombre:
            unit = "mm"
        elif "presion" in nombre:
            unit = "hpa"
        elif nombre == "co2":
            unit = "ppm"
        else:
            unit = ""
        if meta.get("unidad"):
            unit = meta.get("unidad")
        try:
            valor_num = float(valor)
        except Exception:
            continue
        sensores_raw[nombre] = SensorRaw(
            value=valor_num, unit=unit, ts=ts, source=meta.get("fuente") or "sistema"
        )
    # Normalizar
    sensores_norm = {k: normalize_sensor(k, v) for k, v in sensores_raw.items()}
    # Snapshot
    snapshot = MeteoSnapshot(ts=ts, sensors=sensores_norm)
    # Métricas derivadas
    derived = compute_derived(snapshot)
    # Tendencia de presión (hPa/h) si hay histórico real
    historial_presion = system.obtener_historial_sensor("presion")
    if historial_presion and len(historial_presion) >= 2:
        try:
            t0, v0 = historial_presion[0]
            t1, v1 = historial_presion[-1]
            dt_h = (t1 - t0) / 3600.0
            if dt_h > 0:
                tendencia = (v1 - v0) / dt_h
                derived["tendencia_presion"] = DerivedMetric(
                    name="tendencia_presion",
                    value=tendencia,
                    unit="hPa/h",
                    ts=ts,
                    quality="derivado_fiable",
                    depends_on=["presion"],
                )
        except Exception:
            pass
    snapshot.derived = derived
    # Actualizar sensores derivados en sistema
    for nombre, metrica in snapshot.derived.items():
        metadata = {
            "tipo": nombre,
            "unidad": metrica.unit,
            "fuente": "derivado",
            "origen": "interno",
            "fiabilidad": 85.0 if metrica.quality != "sospechoso" else 60.0,
            "calidad": metrica.quality,
            "depends_on": metrica.depends_on,
        }
        system.actualizar_sensor_derivado(nombre, metrica.value, metadata)

        # Auto-mejora: comparar derivados con sensores reales si existen
        try:
            if nombre == "uv_derivado":
                real = system.obtener_sensor("uv")
                if real is not None:
                    system.auto_improvement_engine.registrar_error(
                        "uv_derivado", float(real), float(metrica.value)
                    )
        except Exception:
            pass
    # Serializar a dict
    return {
        "ts": snapshot.ts,
        "sensores": {k: vars(v) for k, v in snapshot.sensors.items()},
        "derivadas": {k: vars(v) for k, v in snapshot.derived.items()},
    }
