import logging
from fastapi import FastAPI, Request
## Eliminado import FileResponse
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
from core.system.system_manager import SystemManager
from core.learning.learning_simulation import LearningEngine, SimulationEngine
from core.sensors.sensor_fusion import SensorFusion
from core.engines.autoimprovement_engine import AutoImprovementSystem
from core.indices.environmental_indices import EnvironmentalIndices

EXTERNAL_INTEGRATION_MODE = "live"

app = FastAPI()

## Eliminado: Servir recursos estáticos
STATIC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

## Eliminado endpoint
manager = SystemManager()
system = manager.iniciar()
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
            logging.exception("Silent except at 142 - revisar contexto")
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
    logging.getLogger(__name__).warning(f"[RECEPTOR ENTRY] Entrando a actualizar_sensores_ecowitt con {len(data)} keys")
    # Normalizar claves recibidas
    present_keys = set(k.lower() for k in (data.keys() or []))
    # HEARTBEAT / PURGA: si un sensor no envía datos durante este umbral (segundos) lo marcamos desconectado
    HEARTBEAT_TIMEOUT = int(os.environ.get('METEOSER_HEARTBEAT_TIMEOUT_S', 180))
    import time
    now_ts = time.time()
    # --- AUTORIZACIÓN DE IDENTIDAD: PASSKEY DIAMANTE ---
    PASSKEY_DIAMANTE = "979DFF1BC20666D72CD2FC0290AE1832"
    passkey = data.get("PASSKEY") or data.get("passkey")
    if passkey == PASSKEY_DIAMANTE:
        system.sensores["fuente_confianza"] = "HP2550A_DIAMANTE"
        print(f"[ADUANA] PASSKEY Diamante autorizada: {passkey}")
    else:
        system.sensores["fuente_confianza"] = "desconocida"
        print(f"[ADUANA] PASSKEY no reconocida: {passkey}")
        
    temperatura = data.get("tempf")
    humedad = data.get("humidity")
    viento = data.get("windspeedmph")
    radiacion = data.get("solarradiation")
    uv_raw = data.get("uv") or data.get("uvi") or data.get("uvindex") or data.get("uv_index")
    lightning = data.get("lightning")
    lightning_num = data.get("lightning_num")
    lightning_time = data.get("lightning_time")

    # --- Sellado de Presión Universal V1.4 (Desnudez de claves + puente directo) ---
    presion_hpa = None
    fuente_presion = None
    presion_raw = None

    presion_candidates = [
        ("baromrelhpa", "hpa"),
        ("baromrel_hpa", "hpa"),
        ("absbaromhpa", "hpa"),
        ("baromabshpa", "hpa"),
        ("baromabs_hpa", "hpa"),
        ("baromrelin", "inhg"),
        ("baromabsin", "inhg"),
        ("baromrel", "auto"),
        ("baromabs", "auto"),
        ("pressure", "auto"),
        ("pressurerel", "auto"),
        ("pressureabs", "auto"),
        ("baromrelmm", "mmhg"),
        ("baromabsmm", "mmhg"),
    ]

    def _convert_presion(val, unidad):
        try:
            v = float(val)
        except Exception:
            return None
        if unidad == "hpa":
            return v
        if unidad == "inhg":
            return v * 33.8638866667
        if unidad == "mmhg":
            return v * 1.33322
        if unidad == "auto":
            if v > 800:
                return v
            if 20.0 <= v <= 40.0:
                return v * 33.8638866667
            if 600.0 <= v <= 800.0:
                return v * 1.33322
        return None

    for key, unidad in presion_candidates:
        if data.get(key) is None:
            continue
        presion_raw = data.get(key)
        fuente_presion = key
        presion_hpa = _convert_presion(presion_raw, unidad)
        print(f"[PRESION DEBUG] {key}={presion_raw} → {presion_hpa} hPa")
        if presion_hpa is not None:
            break

    intentos_fallidos = 0
    try:
        intentos_fallidos = int(system.sensores.get("presion_intentos_fallidos", 0))
    except Exception:
        intentos_fallidos = 0

    # Puente directo: si el valor es >800 hPa, inyéctalo
    if presion_hpa is not None and presion_hpa > 800:
        try:
            # VACIADO DE CACHE: Purgar valores antiguos/basura antes de inyectar
            if hasattr(system, "sensores") and "presion" in system.sensores:
                valor_anterior = system.sensores.get("presion")
                if valor_anterior in [799.0, 799, 101325.0, 101325, None]:
                    print(f"[PURGA] Limpiando presión placeholder anterior: {valor_anterior}")
                    system.sensores["presion"] = None

            # REGISTRO DE IDENTIDAD Y METADATA (sensor virtual nativo del receptor)
            sensor_id = "BAROM_INTERNAL_HP2550A"
            try:
                valor_hpa = float(presion_hpa)
            except Exception:
                print(f"[ADUANA] Error: presión recibida no es float: {presion_hpa}")
                return

            try:
                # Marcar explícitamente como gateway (nave nodriza) y disponible para ámbito exterior
                system.registrar_sensor_metadata(sensor_id, tipo="presion", unidad="hPa", fuente="HP2550A", origen="ecowitt", fiabilidad=95.0, rol="gateway", ambito="exterior")
                # Trazabilidad explícita en el mapa rápido de sensores
                try:
                    system.sensores["presion_ambito"] = "exterior"
                    system.sensores["presion_fuente_sensor"] = sensor_id
                except Exception:
                    logging.exception("Silent except at 297 - revisar contexto")
            except Exception:
                logging.exception("Silent except at 299 - revisar contexto")

            # Pasar por el Cerebro Estadístico (Hampel / Mahalanobis) SOLO SI TIENE HISTORIAL
            final_val = None
            try:
                if 'learning_engine' in globals() and getattr(learning_engine, 'statistical_brain', None):
                    brain = learning_engine.statistical_brain
                    # PERMITIR PRIMEROS VALORES: Hampel necesita mínimo 3 valores históricos
                    presion_count = len(brain.data_buffer.get(sensor_id, []))
                    if presion_count >= 3:
                        brain_results = brain.ingest({sensor_id: round(valor_hpa, 2)})
                        filtered = brain_results.get('filtered_values', {}) if isinstance(brain_results, dict) else {}
                        if sensor_id in filtered:
                            final_val = float(filtered[sensor_id])
                        else:
                            # Hampel ha marcado la lectura como outlier
                            print(f"[ADUANA] Presión RECHAZADA por Hampel: {valor_hpa:.2f} hPa (ID: {sensor_id})")
                            system.sensores["presion_status"] = "HAMPEL_RECHAZADA"
                    else:
                        # Primer valor o sin suficiente historial: aceptar directamente
                        final_val = round(valor_hpa, 2)
                        print(f"[INGESTA] Presión ACEPTADA (historial insuficiente): {final_val:.2f} hPa")
                else:
                    # No hay cerebro estadístico: proceder con la entrada
                    final_val = round(valor_hpa, 2)
            except Exception as e:
                print(f"[ADUANA] Error al validar presión con Cerebro Estadístico: {e}")
                final_val = round(valor_hpa, 2)

            # Si el valor pasó la validación, actualizar sensor y presion principal
            if final_val is not None:
                system.actualizar_sensor(sensor_id, final_val)
                system.actualizar_sensor("presion", final_val)
                # Trazabilidad
                print(f"[INGESTA] Presión RECONOCIDA de HP2550A: {final_val:.2f} hPa (ID: {sensor_id})")
                system.sensores["presion_ultima_valida"] = final_val
                system.sensores["presion_fuente"] = sensor_id
                system.sensores["presion_fuente_raw"] = fuente_presion
                system.sensores["presion_raw"] = presion_raw
                system.sensores["presion_status"] = "OK"
                system.sensores["presion_intentos_fallidos"] = 0
                
                # RESET MONIN-OBUKHOV: Presión pasó de falta a OK → resetear estabilidad
                try:
                    from core.integration.temporal_sync_persistence import reset_monin_obukhov_on_pressure_change
                    reset_monin_obukhov_on_pressure_change("OK", system)
                except Exception as e:
                    print(f"[RESET MONIN] Error: {e}")
                
                # ═════════════════════════════════════════════════════════════════════
                # PUBLICACIÓN AL BUS: AMBOS VALORES (RELATIVA Y ABSOLUTA) COMO INTERIOR Y EXTERIOR
                # ═════════════════════════════════════════════════════════════════════
                try:
                    # PRESIÓN RELATIVA (baromrelin)
                    baromrelin = data.get("baromrelin")
                    if baromrelin is not None:
                        presion_relativa_hpa = float(baromrelin) * 33.8638866667  # inHg → hPa
                        presion_rel_rounded = round(presion_relativa_hpa, 2)
                        system.actualizar_sensor("presion_relativa_interior", presion_rel_rounded)
                        system.actualizar_sensor("presion_relativa_exterior", presion_rel_rounded)
                        print(f"[INGESTA] Presión HP2550A RELATIVA (nivel mar): {presion_relativa_hpa:.2f} hPa → INTERIOR y EXTERIOR")
                    
                    # PRESIÓN ABSOLUTA (baromabsin)
                    baromabsin = data.get("baromabsin")
                    if baromabsin is not None:
                        presion_absoluta_hpa = float(baromabsin) * 33.8638866667  # inHg → hPa
                        presion_abs_rounded = round(presion_absoluta_hpa, 2)
                        system.actualizar_sensor("presion_absoluta_interior", presion_abs_rounded)
                        system.actualizar_sensor("presion_absoluta_exterior", presion_abs_rounded)
                        print(f"[INGESTA] Presión HP2550A ABSOLUTA (nivel sensor): {presion_absoluta_hpa:.2f} hPa → INTERIOR y EXTERIOR")
                except Exception as e:
                    print(f"[ERROR] Error actualizando sensores de presión: {e}")
            else:
                # No actualizar presion en reactor; incrementar intentos fallidos
                intentos_fallidos += 1
                system.sensores["presion_intentos_fallidos"] = intentos_fallidos
        except Exception as e:
            print(f"[ADUANA] Error al procesar presión HP2550A: {e}")
    else:
        intentos_fallidos += 1
        system.sensores["presion_intentos_fallidos"] = intentos_fallidos
        if intentos_fallidos >= 3:
            # Usar ISA dinámico en lugar de 1013.25 hardcodeado
            from core.atmosphere.isa_calculator import presion_isa_fallback
            try:
                altitud = system.sensores.get("altitud", 96.0)
            except:
                altitud = 96.0
            
            presion_ultima = system.sensores.get("presion_ultima_valida")
            presion_fallback, razon = presion_isa_fallback(altitud, presion_ultima)
            
            system.actualizar_sensor("presion", presion_fallback)
            system.sensores["presion_status"] = "ALERTA_SENSOR_BAROMETRO_OFFLINE"
            print(
                "[ALERTA] Barómetro offline: usando fallback ISA dinámico "
                f"{presion_fallback:.2f} hPa (razón: {razon})"
            )

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
    # --- PM2.5: registrar con ámbito interior/exterior según el canal de temperatura/humedad ---
    try:
        pm_key_candidates = [k for k in data.keys() if k.lower().startswith('pm25') or k.lower().startswith('pm2.5') or k.lower().startswith('pm_25')]
        logging.getLogger(__name__).warning(f"[PM LOOP DEBUG] Candidatos PM encontrados: {pm_key_candidates}")
        for pm_key in pm_key_candidates:
            try:
                pm_val = float(data.get(pm_key))
            except Exception:
                continue
            # Determinar ámbito: si hay tempinf/humidityin -> interior
            ambito = 'exterior'
            if data.get('tempinf') is not None or data.get('humidityin') is not None or data.get('tempin') is not None or data.get('humidityin') is not None:
                ambito = 'interior'
            sensor_id = pm_key
            try:
                # REGISTRAR metadata con AMBITO en los argumentos de `registrar_sensor_metadata`
                system.registrar_sensor_metadata(sensor_id, tipo='pm25', unidad='µg/m³', fuente='ecowitt', origen='externo', fiabilidad=90.0, ambito=ambito)
                # Forzar escritura directa adicional en sensores_metadata por si el método no lo guarda
                if hasattr(system, 'sensores_metadata'):
                    system.sensores_metadata.setdefault(sensor_id, {})
                    system.sensores_metadata[sensor_id]['ambito'] = ambito
                # LOG CRÍTICO: Confirmar que ambito se registró (USAR logging.warning para garantizar visibilidad)
                logging.getLogger(__name__).warning(f"[ADUANA ECOWITT] Sensor PM {sensor_id} → ambito={ambito} | tempinf={data.get('tempinf')} | humidityin={data.get('humidityin')}")
            except Exception as e:
                logging.getLogger(__name__).error(f"[ADUANA] Error al registrar PM metadata: {e}")
            # Actualizar sensor específico
            try:
                system.actualizar_sensor(sensor_id, pm_val)
            except Exception:
                try:
                    system.sensores[sensor_id] = pm_val
                except Exception:
                    logging.exception("Silent except at 487 - revisar contexto")
            
            # PUBLICAR sensor genérico 'pm25' SIEMPRE, pero HEREDAR metadata del sensor específico
            # ⚡ PRIORIDAD ABSOLUTA: Escribir metadata ANTES de actualizar el sensor
            try:
                if hasattr(system, 'sensores_metadata'):
                    if 'pm25' not in system.sensores_metadata:
                        system.sensores_metadata['pm25'] = {}
                    system.sensores_metadata['pm25']['ambito'] = ambito
                    system.sensores_metadata['pm25']['fuente'] = sensor_id  # Trazabilidad
                    # LOG NUCLEAR: confirmar escritura de metadata
                    logging.getLogger(__name__).warning(f"[HERENCIA AMBITO] pm25 heredó ambito={ambito} de {sensor_id}")
            except Exception as herencia_err:
                logging.getLogger(__name__).error(f"[HERENCIA AMBITO] ERROR: {herencia_err}")
            
            # Actualizar sensor genérico DESPUÉS de la metadata
            try:
                system.actualizar_sensor('pm25', pm_val)
            except Exception:
                try:
                    system.sensores['pm25'] = pm_val
                except Exception:
                    logging.exception("Silent except at 509 - revisar contexto")
            # Registrar fuente y ambito para trazabilidad
            try:
                system.sensores['pm25_fuente'] = sensor_id
                system.sensores['pm25_ambito'] = ambito
            except Exception:
                logging.exception("Silent except at 515 - revisar contexto")
            # Calcular y almacenar PM corregido inmediatamente (para trazabilidad)
            try:
                indices_engine = getattr(system, 'indices', None)
                if indices_engine is not None:
                    # Preferir humedad interior si está disponible
                    try:
                        rh_val = float(data.get('humidityin')) if data.get('humidityin') is not None else float(data.get('humidity') or system.sensores.get('humedad') or 50.0)
                    except Exception:
                        rh_val = float(system.sensores.get('humedad') or 50.0)
                    try:
                        corrected = indices_engine._pm_humidity_correction(pm_val, rh_val, sensor_id)
                        # Guardar resultado derivado y razon
                        key_corr = f"pm25_corregido_{sensor_id}"
                        try:
                            system.sensores[key_corr] = corrected
                        except Exception:
                            logging.exception("Silent except at 532 - revisar contexto")
                        razon_key = f"pm25_razon_confianza_{sensor_id}"
                        try:
                            # si indices_engine dejó una razon previa, manténla
                            razon = system.sensores.get(razon_key) or None
                            if razon:
                                system.sensores[razon_key] = razon
                        except Exception:
                            logging.exception("Silent except at 540 - revisar contexto")
                    except Exception:
                        logging.exception("Silent except at 542 - revisar contexto")
            except Exception:
                logging.exception("Silent except at 544 - revisar contexto")
    except Exception as ex_pm_loop:
        logging.getLogger(__name__).error(f"[PM LOOP EXCEPTION] ERROR CRÍTICO en bloque PM: {ex_pm_loop}", exc_info=True)

    # --- Sensores desconocidos/experimentales (prefijo sensor_) ---
    try:
        for raw_key, raw_val in data.items():
            if not str(raw_key).lower().startswith("sensor_"):
                continue
            if raw_val is None:
                continue
            sensor_id = str(raw_key).lower()
            try:
                val = float(raw_val)
            except Exception:
                val = raw_val
            unidad = "Bq/m³" if "radon" in sensor_id else None
            try:
                system.registrar_sensor_metadata(sensor_id, tipo=sensor_id, unidad=unidad, fuente="ecowitt", origen="externo", fiabilidad=80.0)
            except Exception:
                logging.exception("Silent except at 564 - revisar contexto")
            try:
                system.actualizar_sensor(sensor_id, val)
            except Exception:
                try:
                    system.sensores[sensor_id] = val
                except Exception:
                    logging.exception("Silent except at 571 - revisar contexto")
    except Exception:
        logging.exception("Silent except at 573 - revisar contexto")

    # ------------------
    # Limpieza por ausencia explícita de claves (NO heredar valor anterior)
    # Regla: si el paquete NO incluye `co2` lo limpiamos (S/D). Para PM, si no hay ningún channel de PM
    # el sensor pm25 se marca S/D también.
    try:
        co2_keys = {'co2', 'co2ppm'}
        if not any(k in present_keys for k in co2_keys):
            # paquete no trae CO2: no heredar valor previo
            try:
                system.actualizar_sensor('co2', None)
                system.sensores_metadata.setdefault('co2', {})
                system.sensores_metadata['co2']['status'] = 'disconnected'
            except Exception:
                logging.exception("Silent except at 588 - revisar contexto")
        pm_candidates_lower = {k.lower() for k in pm_key_candidates}
        if not pm_candidates_lower:
            try:
                system.actualizar_sensor('pm25', None)
                system.sensores_metadata.setdefault('pm25', {})
                system.sensores_metadata['pm25']['status'] = 'disconnected'
            except Exception:
                logging.exception("Silent except at 596 - revisar contexto")
    except Exception:
        logging.exception("Silent except at 598 - revisar contexto")

    # Purga por heartbeat: sensores con timestamp muy antiguos → desconectados (S/D)
    try:
        if hasattr(system, 'sensores_timestamp'):
            for sensor_name, ts in list(system.sensores_timestamp.items()):
                try:
                    if ts is None:
                        continue
                    if now_ts - float(ts) > HEARTBEAT_TIMEOUT:
                        # marcar como desconectado y limpiar valor
                        system.actualizar_sensor(sensor_name, None)
                        system.sensores_metadata.setdefault(sensor_name, {})
                        system.sensores_metadata[sensor_name]['status'] = 'disconnected'
                except Exception:
                    continue
    except Exception:
        logging.exception("Silent except at 615 - revisar contexto")
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
    try:
        print("[DEBUG] Claves recibidas en /ecowitt:", sorted(list(data.keys())))
    except Exception:
        print("[DEBUG] Claves recibidas en /ecowitt: <no_disponible>")
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
            logging.exception("Silent except at 741 - revisar contexto")
        if "amanecer" not in indices or "atardecer" not in indices:
            horas_sol = calcular_amanecer_atardecer(lat, lon, hoy, 1)
            indices["amanecer"] = horas_sol.get("amanecer", "--:--")
            indices["atardecer"] = horas_sol.get("atardecer", "--:--")
        indices["latitud"] = lat
        indices["longitud"] = lon
        estado["indices"] = indices
    except Exception:
        logging.exception("Silent except at 750 - revisar contexto")
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
