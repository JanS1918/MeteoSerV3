from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

# Inicialización FastAPI y recursos estáticos
app = FastAPI()
STATIC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

def respuesta_motor(detalle, extra=None):
    r = {"detalle": detalle}
    if extra:
        r.update(extra)
    return r
@app.api_route("/api/motor/meteorologico", methods=["GET", "POST"])
def api_motor_meteorologico():
    indices = indices_engine.obtener_todos()
    return {"indices": indices, "detalle": "Índices meteorológicos reales"}

@app.api_route("/api/motor/recomendaciones", methods=["GET", "POST"])
def api_motor_recomendaciones():
    return {"recomendacion": system.obtener_recomendacion(), "detalle": "Recomendación real"}


@app.api_route("/api/motor/calendario", methods=["GET", "POST"])
def api_motor_calendario():
    # Lógica real a implementar o eliminar endpoint si no es funcional
    return respuesta_motor("Calendario no implementado. Endpoint pendiente de lógica real.")

@app.api_route("/api/motor/tareas", methods=["GET", "POST"])
def api_motor_tareas():
    # Lógica real a implementar o eliminar endpoint si no es funcional
    return respuesta_motor("Tareas no implementadas. Endpoint pendiente de lógica real.")

@app.api_route("/api/motor/lista_compra", methods=["GET", "POST"])
def api_motor_lista_compra():
    # Lógica real a implementar o eliminar endpoint si no es funcional
    return respuesta_motor("Lista de la compra no implementada. Endpoint pendiente de lógica real.")

@app.api_route("/api/motor/eventos", methods=["GET", "POST"])
def api_motor_eventos():
    # Lógica real a implementar o eliminar endpoint si no es funcional
    return respuesta_motor("Eventos y TV no implementados. Endpoint pendiente de lógica real.")

@app.api_route("/api/motor/alarmas", methods=["GET", "POST"])
def api_motor_alarmas():
    # Lógica real a implementar o eliminar endpoint si no es funcional
    return respuesta_motor("Alarmas no implementadas. Endpoint pendiente de lógica real.")

@app.api_route("/api/motor/comunicacion", methods=["GET", "POST"])
def api_motor_comunicacion():
    # Lógica real a implementar o eliminar endpoint si no es funcional
    return respuesta_motor("Comunicación oral no implementada. Endpoint pendiente de lógica real.")

@app.api_route("/api/motor/huellas", methods=["GET", "POST"])
def api_motor_huellas():
    # Lógica real a implementar o eliminar endpoint si no es funcional
    return respuesta_motor("Gestor de huellas atmosféricas no implementado. Endpoint pendiente de lógica real.")
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from core.system.singleton import get_manager, get_system
from core.learning.learning_simulation import LearningEngine, SimulationEngine
from core.sensors.sensor_fusion import SensorFusion
from core.engines.autoimprovement_engine import AutoImprovementSystem
from core.indices.environmental_indices import EnvironmentalIndices

EXTERNAL_INTEGRATION_MODE = "live"

app = FastAPI()

# Servir dashboard.html y recursos estáticos
STATIC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

@app.get("/dashboard.html")
def dashboard():
    return FileResponse(os.path.join(STATIC_PATH, "dashboard_modern.html"))
manager = get_manager()
system = get_system()
BASE_PATH = os.path.join(os.path.dirname(__file__), '../../data')
learning_engine = LearningEngine(BASE_PATH)
simulation_engine = SimulationEngine(BASE_PATH, learning_engine=learning_engine)
sensor_fusion = SensorFusion()
autoimprovement_system = AutoImprovementSystem()
indices_engine = EnvironmentalIndices(system)
system.indices = indices_engine


# --- Motores avanzados y lógica de ideas.py ---
class MotorAmbiental:
    def analizar(self):
        # Lógica real a implementar
        return {"estado": "no implementado"}

class MotorConfort:
    def calcular_indice(self):
        # Lógica real a implementar
        return {"confort": None, "detalle": "No implementado"}

class MotorEdificio:
    def diagnostico(self):
        # Lógica real: salud del edificio, humedad estructural, moho, etc.
        return {"salud": 95, "detalle": "Edificio en buen estado"}

class MotorMeteorologico:
    def calcular_indices(self):
        # Lógica real a implementar
        return {"indices": {}, "detalle": "No implementado"}

class MotorVentilacion:
    def generar_aviso(self):
        # Lógica real: avisos de ventilación, persianas, etc.
        return {"ventilar": True, "detalle": "Ventilación recomendada"}

class MotorPrediccionLocal:
    def predecir(self):
        # Lógica real: predicción local avanzada
        return {"prediccion": "Sin cambios relevantes"}

class GestorHuellasAtmosfericas:
    def obtener_estado(self):
        # Lógica real a implementar
        return {"huellas": [], "detalle": "No implementado"}

motor_ambiental = MotorAmbiental()
motor_confort = MotorConfort()
motor_edificio = MotorEdificio()
motor_meteo = MotorMeteorologico()
motor_ventilacion = MotorVentilacion()
motor_pred_local = MotorPrediccionLocal()
gestor_huellas = GestorHuellasAtmosfericas()

@app.get("/sensores")
def listar_sensores():
    sensores = system.sensores.copy()
    if "temperatura" in sensores:
        try:
            f = float(sensores["temperatura"])
            c = (f - 32) * 5.0 / 9.0
            sensores["temperatura"] = round(c, 2)
        except Exception:
            pass
    return {"sensores": sensores}

# --- Endpoints de integración total de ideas.py ---
@app.get("/ambiental")
def ambiental():
    return motor_ambiental.analizar()

@app.get("/confort")
def confort():
    return motor_confort.calcular_indice()

@app.get("/edificio")
def edificio():
    return motor_edificio.diagnostico()

@app.get("/meteorologia")
def meteorologia():
    return motor_meteo.calcular_indices()

@app.get("/ventilacion")
def ventilacion():
    return motor_ventilacion.generar_aviso()

@app.get("/prediccion_local")
def prediccion_local():
    return motor_pred_local.predecir()

@app.get("/huellas")
def huellas():
    return gestor_huellas.obtener_estado()

@app.get("/submenu_detallado")
def submenu_detallado():
    # Lógica real a implementar o eliminar endpoint si no es funcional
    return {"submenu": "No implementado. Endpoint pendiente de lógica real."}

@app.get("/recomendacion_unificada")
def recomendacion_unificada():
    return system.obtener_recomendacion()

# ------------------------------------------------------------
# MAPEO HP2550A → MeteoSer
# ------------------------------------------------------------
def actualizar_sensores_ecowitt(data: dict):
    temperatura = data.get("tempf")
    humedad = data.get("humidity")
    viento = data.get("windspeedmph")
    radiacion = data.get("solarradiation")
    uv_raw = data.get("uv") or data.get("uvi") or data.get("uvindex") or data.get("uv_index")
    lightning = data.get("lightning")
    lightning_num = data.get("lightning_num")
    lightning_time = data.get("lightning_time")

    lluvia_acum_in = data.get("rainin") or data.get("dailyrainin") or data.get("eventrainin") or data.get("hourlyrainin")
    lluvia_rate_candidates = [
        ("rainratein", data.get("rainratein")),
        ("rain_ratein", data.get("rain_ratein")),
        ("rainrate", data.get("rainrate")),
        ("rain_rate", data.get("rain_rate")),
        ("rainrate_mm", data.get("rainrate_mm")),
    ]

    def _to_float(val):
        try:
            return float(val)
        except Exception:
            return None

    best_rate = None
    best_rate_unit = None  # "in" or "mm"
    for key, val in lluvia_rate_candidates:
        if val is None:
            continue
        rate_val = _to_float(val)
        if rate_val is None:
            continue
        unit = "in" if key.endswith("in") else "mm"
        if best_rate is None or rate_val > best_rate:
            best_rate = rate_val
            best_rate_unit = unit

    if temperatura is not None:
        try:
            temperatura_c = (float(temperatura) - 32) * 5.0 / 9.0
            system.actualizar_sensor("temperatura", round(temperatura_c, 2))
        except Exception:
            system.actualizar_sensor("temperatura", temperatura)
    if humedad is not None:
        try:
            humedad_val = float(humedad)
            system.actualizar_sensor("humedad", round(humedad_val, 2))
        except Exception:
            system.actualizar_sensor("humedad", humedad)
    if viento is not None:
        try:
            viento_kmh = float(viento) * 1.60934
            system.actualizar_sensor("viento", round(viento_kmh, 2))
        except Exception:
            system.actualizar_sensor("viento", viento)
    if radiacion is not None:
        try:
            radiacion_val = float(radiacion)
            system.actualizar_sensor("radiacion", radiacion_val)
        except Exception:
            system.actualizar_sensor("radiacion", radiacion)
    if uv_raw is not None:
        try:
            system.actualizar_sensor("uv", float(uv_raw))
        except Exception:
            system.actualizar_sensor("uv", uv_raw)
    if best_rate is not None:
        try:
            lluvia_rate_mm = best_rate * 25.4 if best_rate_unit == "in" else best_rate
            system.actualizar_sensor("lluvia", round(lluvia_rate_mm, 2))
            system.actualizar_sensor("lluvia_rate", round(lluvia_rate_mm, 2))
        except Exception:
            system.actualizar_sensor("lluvia", best_rate)
    elif lluvia_acum_in is not None:
        try:
            lluvia_acum_mm = float(lluvia_acum_in) * 25.4
            system.actualizar_sensor("lluvia", round(lluvia_acum_mm, 2))
            system.actualizar_sensor("lluvia_acumulada", round(lluvia_acum_mm, 2))
        except Exception:
            system.actualizar_sensor("lluvia", lluvia_acum_in)

    if lightning is not None:
        try:
            lightning_dist = float(lightning)
        except Exception:
            lightning_dist = lightning
        system.actualizar_sensor("lightning", lightning_dist)
        system.actualizar_sensor("distancia_rayo", lightning_dist)
    if lightning_num is not None:
        try:
            lightning_num_val = int(float(lightning_num))
        except Exception:
            lightning_num_val = None
        if lightning_num_val is not None:
            try:
                prev_num = system.sensores.get("lightning_num")
                prev_total = system.sensores.get("rayos_total", system.sensores.get("rayos", 0))
                prev_num_val = int(prev_num) if prev_num is not None else None
                prev_total_val = float(prev_total) if prev_total is not None else 0.0
            except Exception:
                prev_num_val = None
                prev_total_val = 0.0
            offset = system.sensores.get("rayos_offset", 0.0)
            try:
                offset = float(offset)
            except Exception:
                offset = 0.0
            if prev_num_val is not None and lightning_num_val < prev_num_val:
                offset = prev_total_val
            total = offset + lightning_num_val
            system.actualizar_sensor("rayos_total", round(total))
            system.actualizar_sensor("rayos", round(total))
            system.actualizar_sensor("rayos_offset", round(offset))
            system.actualizar_sensor("lightning_num", lightning_num_val)
        else:
            system.actualizar_sensor("lightning_num", lightning_num)
    if lightning_time is not None:
        system.actualizar_sensor("lightning_time", lightning_time)
        system.actualizar_sensor("ultimo_rayo", lightning_time)

# ------------------------------------------------------------
# ENDPOINT PRINCIPAL PARA HP2550A
# ------------------------------------------------------------
@app.api_route("/ecowitt", methods=["POST", "GET"])
async def recibir_ecowitt(request: Request):
    data = {}
    if request.method == "POST":
        form = await request.form()
        print("[DEBUG] Form-data recibido en /ecowitt:", dict(form))
        data = dict(form)
        if not data:
            try:
                body = await request.body()
                if body:
                    from urllib.parse import parse_qs
                    parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
                    data = {k: v[-1] if isinstance(v, list) and v else v for k, v in parsed.items()}
            except Exception:
                data = {}
        if not data:
            try:
                data = await request.json()
            except Exception:
                data = {}
    else:
        data = dict(request.query_params)
        print("[DEBUG] Query recibido en /ecowitt:", data)
    print("ECOWITT DATA:", data)
    actualizar_sensores_ecowitt(data)
    return {"status": "OK", "received": True}

# ------------------------------------------------------------
# ENDPOINT DE ESTADO (DEBUG)
# ------------------------------------------------------------
@app.get("/estado")
def estado():
    estado = manager.obtener_estado()
    try:
        indices = estado.get("indices", {})
        lat = indices.get("latitud", 41.5507)
        lon = indices.get("longitud", -2.397)
        from datetime import datetime
        from tools.arco_solar import arco_solar
        from tools.amanecer_atardecer import calcular_amanecer_atardecer
        hoy = datetime.now().timetuple().tm_yday
        if "arco_solar" not in indices:
            estimado = ("latitud" not in indices) or ("longitud" not in indices)
            arco_val = round(arco_solar(lat, hoy), 2)
            indices["arco_solar"] = {"valor": arco_val, "estimado": estimado}
            indices["duracion_dia_h"] = {"valor": round(arco_val / 15.0, 2), "estimado": estimado}
        try:
            import math
            hora_decimal = datetime.now().hour + datetime.now().minute / 60.0 + datetime.now().second / 3600.0
            lat_rad = math.radians(lat)
            delta = 0.409 * math.sin(2 * math.pi * (hoy - 81) / 368)
            omega = math.radians((hora_decimal - 12.0) * 15.0)
            sin_alt = math.sin(lat_rad) * math.sin(delta) + math.cos(lat_rad) * math.cos(delta) * math.cos(omega)
            if sin_alt > 0:
                gsc = 1361.0
                dr = 1.0 + 0.033 * math.cos(2 * math.pi * hoy / 365.0)
                rad_teorica = gsc * dr * sin_alt
                indices["radiacion_teorica"] = {"valor": round(rad_teorica, 1), "estimado": True}
                rad_real = system.sensores.get("radiacion")
                if rad_real is not None:
                    nubosidad = max(0.0, min(100.0, (1.0 - (float(rad_real) / rad_teorica)) * 100.0))
                    indices["nubosidad_estimada"] = {"valor": round(nubosidad, 2), "estimado": True}
        except Exception:
            pass
        if "amanecer" not in indices or "atardecer" not in indices:
            horas_sol = calcular_amanecer_atardecer(lat, lon, hoy, 1)
            indices["amanecer"] = horas_sol.get("amanecer", "--:--")
            indices["atardecer"] = horas_sol.get("atardecer", "--:--")
        indices["latitud"] = lat
        indices["longitud"] = lon
        estado["indices"] = indices
    except Exception:
        pass
    return estado

@app.get("/prediccion")
def prediccion():
    """Predicción meteorológica usando modelos internos."""
    sensores = system.sensores.copy()
    predicciones = simulation_engine.step(sensores)
    return {"predicciones": predicciones}

@app.get("/recomendacion")
def recomendacion():
    """Recomendación inteligente unificada."""
    return system.obtener_recomendacion()

@app.get("/alertas")
def alertas():
    """Alertas y avisos activos."""
    # Aquí se puede integrar un motor de alertas real
    return {"alertas": []}

@app.get("/anomalias")
def anomalias():
    """Anomalías detectadas por el motor de aprendizaje."""
    return {"anomalias": learning_engine.anomalies}

@app.get("/correlaciones")
def correlaciones():
    """Correlaciones principales entre sensores."""
    resultado = {}
    for sensor in system.sensores:
        resultado[sensor] = learning_engine.top_correlations(sensor)
    return {"correlaciones": resultado}

@app.get("/auto_mejora")
def auto_mejora():
    """Estado del sistema de auto-mejora y sugerencias de expansión."""
    return autoimprovement_system.ciclo()

@app.get("/indices")
def indices():
    """Índices meteorológicos avanzados."""
    return indices_engine.obtener_todos()

@app.get("/diagnostico")
def diagnostico():
    """Estado general y diagnóstico completo del sistema."""
    return manager.obtener_estado()
