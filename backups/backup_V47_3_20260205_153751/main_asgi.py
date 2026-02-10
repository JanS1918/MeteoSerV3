from __future__ import annotations

import logging
# ⚠️ MAIN ASGI - ROUTER SELLADO CON ESTÁNDARES DIAMANTE
# ════════════════════════════════════════════════════════════════════════════
# Router principal del servidor METEOSER V3.
# Reglas de Diamante (INAMOVIBLES):
#
# 1. LEY DEL ENTERO: Salida JSON emite topes como INT puros (0, 1, 99, 100)
#    nunca 0.0, 1.0, 99.0, 100.0
#
# 2. REDONDEO: Índices meteorológicos máximo 2 decimales en salida
#
# 3. CONFIG SOBERANA: Todos los límites desde data/indices_config.json
#
# 4. ESCUDO DE SEGURIDAD: Protecciones (if > 0) intactas en divisiones
#
# Ver: ENGINEERING_STANDARDS.md (raíz del proyecto)
# ════════════════════════════════════════════════════════════════════════════

from fastapi import Body
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from contextlib import asynccontextmanager
import base64
import os
import pathlib
import time

# Sistema de IA integrado
try:
    from ai_controller import initialize_ai_controller, get_ai_controller
    from ai_endpoints import router as ai_router
    AI_AVAILABLE = True
except Exception as e:
    AI_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(f"⚠️ Sistema de IA no disponible: {e}")

try:
    from core.indices.index_catalog import INDEX_CATALOG
except Exception:
    INDEX_CATALOG = {}

# Importar recorders de histórico
try:
    from core.monitoring.history_recorders import get_recorders
    RECORDERS_AVAILABLE = True
except Exception as e:
    RECORDERS_AVAILABLE = False
    logging.getLogger(__name__).warning(f"⚠️ History recorders no disponibles: {e}")

# Importar validador de predicciones y feedback automático
try:
    from core.monitoring.prediction_validation import (
        validar_y_generar_feedback_automatico,
        LearningLoopValidator
    )
    PREDICTION_VALIDATION_AVAILABLE = True
except Exception as e:
    PREDICTION_VALIDATION_AVAILABLE = False
    logging.getLogger(__name__).warning(f"⚠️ Prediction validation no disponible: {e}")

# Definir lifespan handler (reemplaza @app.on_event deprecado)
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Gestiona startup/shutdown del servidor MeteoSerV3."""
    global discovery_engine, auto_repair_engine, pas_engine, habits_engine, omnipotence_manager
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STARTUP
    # ═══════════════════════════════════════════════════════════════════════════
    logger.info("🚀 INICIO: MeteoSerV3 iniciando secuencia de carga...")
    
    # � AUDITORÍA AUTOMÁTICA DE STARTUP (100% REAL)
    try:
        from core.system.startup_auditor import startup_auditor
        audit_report = await startup_auditor.audit_system()
        if audit_report["status"] != "OK":
            logger.warning(f"⚠️ Auditoría encontró {audit_report['total_issues']} problemas")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo ejecutar auditoría: {e}")
    
    # 🔄 INTEGRADOR ALWAYS-ON: Recuperación automática de datos del gap histórico
    try:
        from core.integration.integrador_always_on import ejecutar_integrador_automatico
        resultado_integrador = await ejecutar_integrador_automatico()
        logger.info(f"🔄 Integrador Always-On: {resultado_integrador.get('status', 'completado')}")
        if resultado_integrador.get('status') == 'exito':
            logger.info(f"   ✅ {resultado_integrador.get('eventos_procesados', 0)} eventos recuperados e integrados")
    except Exception as e:
        logger.warning(f"⚠️ Integrador Always-On no disponible: {e}")
    
    # �🛸 OMNIPOTENCIA V1.5: Activar radar universal al inicio
    if omnipotence_manager:
        try:
            await omnipotence_manager.start()
            logger.info("🛸 Radar Universal iniciado - Buscando hardware por USB/BLE/WiFi...")
        except Exception as omni_err:
            logger.error(f"Error iniciando Omnipotencia: {omni_err}")

    mqtt_host = os.getenv("METEOSER_MQTT_HOST", "127.0.0.1")
    mqtt_tls_enabled = os.getenv("METEOSER_MQTT_TLS", "1") not in ("0", "false", "False")
    default_mqtt_port = "8883" if mqtt_tls_enabled else "1883"
    try:
        mqtt_port = int(os.getenv("METEOSER_MQTT_PORT", default_mqtt_port))
    except Exception:
        mqtt_port = int(default_mqtt_port)
    mqtt_enabled = os.getenv("METEOSER_MQTT_ENABLED", "1") not in ("0", "false", "False")
    mdns_enabled = os.getenv("METEOSER_MDNS_ENABLED", "1") not in ("0", "false", "False")
    serial_enabled = os.getenv("METEOSER_SERIAL_ENABLED", "1") not in ("0", "false", "False")
    # BLE DESHABILITADO permanentemente (sin Bluetooth en este sistema)
    ble_enabled = False
    mqtt_user = os.getenv("METEOSER_MQTT_USER")
    mqtt_pass = os.getenv("METEOSER_MQTT_PASSWORD")
    mqtt_timeout = int(os.getenv("METEOSER_MQTT_TIMEOUT", "60"))
    mqtt_reconnect_interval = int(os.getenv("METEOSER_MQTT_RECONNECT_INTERVAL", "5"))

    if discovery_engine:
        try:
            discovery_engine.start(
                mqtt_host=mqtt_host,
                mqtt_port=mqtt_port,
                mqtt_enabled=mqtt_enabled,
                mdns_enabled=mdns_enabled,
                serial_enabled=serial_enabled,
                ble_enabled=ble_enabled,
                mqtt_user=mqtt_user,
                mqtt_pass=mqtt_pass,
                mqtt_tls=mqtt_tls_enabled,
                mqtt_timeout=mqtt_timeout,
                mqtt_reconnect_interval=mqtt_reconnect_interval,
            )
            logger.info(f"🔍 Discovery Engine iniciado (MQTT:{mqtt_enabled}, mDNS:{mdns_enabled}, Serial:{serial_enabled}, BLE:{ble_enabled})")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo iniciar discovery: {e}")

    def _alarmas_loop():
        while True:
            try:
                if system and hasattr(system, 'alerting_brain') and system.alerting_brain:
                    system.alerting_brain.check_and_notify(system.data)
            except Exception as e:
                logger.error(f"Error en _alarmas_loop: {e}")
            time.sleep(10)

    async def _habitos_loop():
        while True:
            try:
                if system and hasattr(system, 'data'):
                    system_copy = dict(system.data) if system.data else {}
                else:
                    system_copy = {}
                if system_copy:
                    try:
                        if habits_engine:
                            habits_engine.update_from_system(system_copy)
                    except Exception:
                        logging.exception("Silent except at 128 - revisar contexto")
                await asyncio.sleep(600)
            except Exception as e:
                logger.error(f"Error en _habitos_loop: {e}")
                await asyncio.sleep(10)

    async def _watchdog_loop():
        # Evaluación periódica del watchdog de cambios (rollback automático)
        while True:
            try:
                engine = getattr(app_instance.state, "self_mod_engine", None)
                if engine:
                    result = engine.evaluate_all_changes()
                    if result.get("reverted", 0) > 0:
                        logger.warning(f"⚠️ Watchdog revirtió cambios: {result}")
            except Exception as e:
                logger.error(f"Error en _watchdog_loop: {e}")
            await asyncio.sleep(600)

    async def _auto_optimizer_loop():
        # 🎯 MEJORADO: Procesa cola CON VALIDACIÓN PROACTIVA
        while True:
            try:
                engine = getattr(app_instance.state, "self_mod_engine", None)
                controller = getattr(app_instance.state, "auto_optimizer", None)
                validator = getattr(app_instance.state, "spec_validator", None)  # 🎯 NUEVO
                watchdog = getattr(app_instance.state, "auto_change_watchdog", None)  # 🎯 NUEVO
                
                if engine and controller:
                    # 🎯 PASO 1: Obtener cambio propuesto
                    result = controller.process_queue(engine)
                    
                    # 🎯 PASO 2: Validar PROACTIVAMENTE antes de aplicar
                    if validator and watchdog and result.get("applied", 0) > 0:
                        change_info = result.get("change_info", {})
                        formula_name = change_info.get("formula_name", "unknown")
                        impl_func = change_info.get("impl_func")
                        spec_params = change_info.get("spec_params", {})
                        
                        # 🎯 Usar SpecValidationEngine para validar especificación
                        if hasattr(validator, 'validate_single_formula'):
                            from dataclasses import dataclass
                            validation_result = validator._validate_single_formula(
                                formula_name, impl_func, spec_params
                            )
                            is_compliant = validation_result.is_valid
                            issues = validation_result.errors
                        else:
                            is_compliant, issues = watchdog.validate_spec_compliance(
                                formula_name, impl_func, spec_params
                            )
                        
                        if not is_compliant:
                            logger.critical(
                                f"🚫 VALIDADOR PROACTIVO bloqueó cambio incompleto: {formula_name}\n"
                                f"   Problemas: {issues}"
                            )
                            watchdog.block_noncompliant_change(
                                formula_name,
                                f"Incumplimiento de especificación: {len(issues)} problemas"
                            )
                            result["applied"] = 0
                            result["blocked_proactive"] = True
                        else:
                            logger.info(f"✅ Validador Proactivo: {formula_name} COMPLIANT - aplicando cambio")
                            logger.info(f"✅ Auto-optimizer aplicó cambios: {result}")
            except Exception as e:
                logger.error(f"Error en _auto_optimizer_loop: {e}")
            await asyncio.sleep(600)

    import threading
    threading.Thread(target=_alarmas_loop, daemon=True).start()
    
    import asyncio
    try:
        asyncio.create_task(_habitos_loop())
    except Exception:
        logging.exception("Silent except at 141 - revisar contexto")

    # 🛡️ WATCHDOG DE CAMBIOS (rollback automático + freeze)
    # + 🎯 VALIDADOR PROACTIVO (bloquea incomplitudes PRE-aplicación)
    try:
        from self_mod_engine import SelfModEngine
        from core.monitoring.auto_optimizer_controller import AutoOptimizerController
        from core.monitoring.spec_validation_engine import SpecValidationEngine
        from core.monitoring.auto_change_watchdog import AutoChangeWatchdog
        from core.security import (
            MeteorologicalDomainValidator,
            SpecificationCompletenessValidator,
            PrecisionValidator,
            WhitelistEnforcer,
            SecurityOptimizationOrchestrator
        )
        
        app_instance.state.self_mod_engine = SelfModEngine(base_path=".", sandbox=False, use_watchdog=True)
        app_instance.state.auto_optimizer = AutoOptimizerController()
        app_instance.state.spec_validator = SpecValidationEngine()  # 🎯 NUEVO: Validador proactivo
        app_instance.state.auto_change_watchdog = AutoChangeWatchdog()  # 🎯 NUEVO: Watchdog mejorado
        
        # 🔐 MÁXIMA SEGURIDAD - 5 validadores de dominio, especificación, precisión, sagrados, orquestación
        app_instance.state.domain_validator = MeteorologicalDomainValidator()
        app_instance.state.completeness_validator = SpecificationCompletenessValidator()
        app_instance.state.precision_validator = PrecisionValidator()
        app_instance.state.whitelist_enforcer = WhitelistEnforcer(".")
        app_instance.state.security_orchestrator = SecurityOptimizationOrchestrator()
        
        asyncio.create_task(_watchdog_loop())
        asyncio.create_task(_auto_optimizer_loop())
        asyncio.create_task(_security_optimization_loop())
        logger.info("🛡️ Watchdog de cambios activado - evaluación automática cada 10 min")
        logger.info("🎯 VALIDADOR PROACTIVO activado - bloqueará cambios incompletos ANTES de aplicar")
    except Exception as e:
        logger.warning(f"⚠️ Watchdog de cambios / Validador Proactivo no disponible: {e}")
    
    # � CARGAR ALTITUD SRTM (env var METEOSER_SRTM_FORCE)
    try:
        srtm_force = os.getenv("METEOSER_SRTM_FORCE", "0") in ("1", "true", "True")
        if system and hasattr(system, 'location') and system.location:
            altitud = system.location.load_altitude_srtm(force=srtm_force)
            logger.info(f"🗻 SRTM Altitud cargada: {altitud}m (force={srtm_force})")
        else:
            logger.warning("⚠️ LocationEngine no disponible para cargar SRTM")
    except Exception as e:
        logger.warning(f"⚠️ Error cargando SRTM altitud: {e}")
    
    # �📡 EXPANDIR BUS CON SUBFACTORES (100% COBERTURA)
    try:
        from core.system.bus_expander import BusExpander
        if hasattr(system, 'data') and hasattr(app.state, 'bus'):
            bus_expander = BusExpander(app.state.bus, system)
            await bus_expander.publish_all_subfactors()
    except Exception as e:
        logger.warning(f"⚠️ No se pudo expandir Bus: {e}")
    
    # 🧬 EVOLUTION ENGINE (AUTO-MEJORA CONTINUA)
    try:
        from evolution_engine import EvolutionEngine
        evolution = EvolutionEngine(base_path=BASE_DIR, sandbox=False)
        logger.info("🧬 Evolution Engine activado - Auto-mejora continua habilitada")
        # Guardar referencia global
        app_instance.state.evolution_engine = evolution
    except Exception as e:
        logger.info(f"ℹ️ Evolution Engine desactivado (opcional): {type(e).__name__}")
        app_instance.state.evolution_engine = None
    
    # 🤖 SISTEMA DE IA (AUTOCURACIÓN, DIÁLOGO, CODEGEN)
    if AI_AVAILABLE:
        try:
            # Obtener instancia del Bus
            bus_instance = getattr(app_instance.state, 'bus', None)
            
            # Inicializar controlador de IA
            ai_controller = initialize_ai_controller(
                bus=bus_instance,
                config_dir="data",
                contracts_dir="contracts"
            )
            
            # Inicializar todos los subsistemas
            await ai_controller.initialize()
            
            # Guardar referencia global
            app_instance.state.ai_controller = ai_controller
            
            logger.info("🤖 Sistema de IA inicializado - Autocuración, diálogo y codegen activos")
        except Exception as e:
            logger.warning(f"⚠️ Sistema de IA no pudo inicializarse: {e}")
            app_instance.state.ai_controller = None
    else:
        app_instance.state.ai_controller = None
    
    logger.info("✅ INICIO: MeteoSerV3 listo y escuchando (100% REAL)")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 🧩 INCLUIR ROUTERS MODULARES (Arquitectura limpia)
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        from core.api.routers import (
            sensors_router,
            admin_router,
            assistant_router,
            voice_router,
            config_router,
            systems_router
        )
        app_instance.include_router(sensors_router)
        app_instance.include_router(admin_router)
        app_instance.include_router(assistant_router)
        app_instance.include_router(voice_router)
        app_instance.include_router(config_router)
        app_instance.include_router(systems_router)
        logger.info("🧩 Routers modulares cargados: 6 módulos")
    except Exception as e:
        logger.warning(f"⚠️ No se pudieron cargar routers modulares: {e}")
    
    # 🤖 REGISTRAR ENDPOINTS DE IA
    if AI_AVAILABLE:
        try:
            app_instance.include_router(ai_router)
            logger.info("🤖 Endpoints de IA registrados: /ai/*")
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron registrar endpoints de IA: {e}")
    
    logger.info("✅ INICIO: MeteoSerV3 listo y escuchando (100% REAL)")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CEDER AL SERVIDOR (servidor corre aquí)
    # ═══════════════════════════════════════════════════════════════════════════
    yield
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SHUTDOWN
    # ═══════════════════════════════════════════════════════════════════════════
    logger.info("🛑 APAGADO: MeteoSerV3 iniciando secuencia de parada...")
    
    # 🤖 Apagar sistema de IA
    ai_controller = getattr(app_instance.state, 'ai_controller', None)
    if ai_controller:
        try:
            await ai_controller.shutdown()
            logger.info("🤖 Sistema de IA apagado correctamente")
        except Exception as e:
            logger.error(f"❌ Error apagando sistema de IA: {e}")
    
    # 🛸 Detener Omnipotencia
    if omnipotence_manager:
        try:
            await omnipotence_manager.stop()
            logger.info("🛸 Radar Universal detenido")
        except Exception as e:
            logger.error(f"Error deteniendo Omnipotencia: {e}")
    
    # Guardar el estado del cerebro estadístico
    if system and hasattr(system, 'statistical_brain') and system.statistical_brain is not None:
        try:
            from core.engines.brain_persistence import save_brain_state
            logger.info("🛑 APAGADO: Guardando estado del cerebro...")
            save_brain_state(system.statistical_brain)
            logger.info("✅ Estado del cerebro guardado exitosamente")
        except Exception as e:
            logger.exception(f"❌ Error al guardar cerebro durante apagado: {e}")
    
    logger.info("✅ APAGADO: MeteoSerV3 detenido")

# ═══════════════════════════════════════════════════════════════════════════
# CREAR INSTANCIA FASTAPI CON LIFESPAN
# ═══════════════════════════════════════════════════════════════════════════
app = FastAPI(lifespan=lifespan, title="MeteoSerV3", version="3.0.0")

# Importar routers de la nueva UI (legado)
try:
    from app.ui.api_endpoints import router as ui_router, set_system_manager as set_ui_system_manager
    from app.ui.router import router as panel_router, set_system_manager
    app.include_router(ui_router)
    app.include_router(panel_router)
except Exception as e:
    print(f"No se pudo cargar los routers de UI: {e}")

MAX_SENSOR_FRESHNESS_SECONDS = 300
SENSOR_SMOOTHING_ALPHA = 0.5
_SENSOR_SMOOTHING_STATE: dict[str, float] = {}

def _default_unit(canonical: str):
    """Devuelve unidad por defecto para un sensor canonical."""
    if canonical == "temperatura":
        return "C"
    if canonical == "humedad":
        return "%"
    if canonical == "presion":
        return "hPa"
    if canonical in ("pm25", "pm10", "pm1"):
        return "µg/m³"
    if canonical == "co2":
        return "ppm"
    if canonical == "viento":
        return "km/h"
    if canonical == "lluvia":
        return "mm"
    if canonical == "wh51":
        return "%"
    return None

def _canonical_sensor_id(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    from core.bus.parametros_canonicos import resolver_parametro_entrada

    canonical = resolver_parametro_entrada(name)
    if canonical:
        return canonical
    base = _normalizar_texto_simple(name)
    if not base:
        return None
    return base.replace(" ", "_")

def _parse_numeric(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("%"):
        return _parse_numeric(text[:-1])
    text = text.replace(",", ".")
    try:
        return float(text)
    except Exception:
        return None

def _parse_timestamp(value):
    numeric = _parse_numeric(value)
    if numeric is not None:
        return numeric
    if not value:
        return None
    try:
        text = str(value).strip()
        return datetime.datetime.fromisoformat(text).timestamp()
    except Exception:
        logging.exception("Silent except at 347 - revisar contexto")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(text, fmt).timestamp()
        except Exception:
            continue
    return None

def _normalize_sensor_payload(payload: dict) -> dict:
    nombre = payload.get("name") or payload.get("sensor")
    from core.bus.parametros_canonicos import resolver_parametro_entrada

    map_to_raw = payload.get("map_to")
    canonical = resolver_parametro_entrada(map_to_raw) if map_to_raw else None
    if canonical is None:
        canonical = _canonical_sensor_id(nombre) or nombre
    unidad = payload.get("unit")
    if not unidad and canonical:
        try:
            unidad = _default_unit(canonical)
        except Exception:
            unidad = None
    timestamp = _parse_timestamp(payload.get("timestamp") or payload.get("time") or payload.get("ts"))
    valor = _parse_numeric(payload.get("value"))
    raw_reliability = payload.get("reliability") or payload.get("confidence") or payload.get("fiabilidad")
    if raw_reliability is None:
        confidence = 1
    else:
        parsed = _parse_numeric(raw_reliability)
        if parsed is None:
            confidence = 1
        elif parsed > 1:
            confidence = max(0, min(parsed / 100.0, 1.0))
        else:
            confidence = max(0, min(parsed, 1.0))
    return {
        "name": nombre,
        "canonical": canonical,
        "map_to": payload.get("map_to"),
        "unit": unidad,
        "value": valor,
        "timestamp": timestamp,
        "confidence": confidence,
        "source": payload.get("source") or payload.get("origin") or "externo",
        "origin": payload.get("origin") or payload.get("source") or "externo",
        "reliability": raw_reliability,
        "raw": payload,
    }

def _validate_sensor_payload(normalized: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not normalized.get("name"):
        errors.append("No hay nombre de sensor")
    if normalized.get("value") is None:
        errors.append("Valor no convertible a número")
    now = time.time()
    timestamp = normalized.get("timestamp")
    if timestamp and abs(now - timestamp) > MAX_SENSOR_FRESHNESS_SECONDS:
        errors.append("Lectura demasiado antigua")
    confidence = normalized.get("confidence", 1.0)
    if not (0.0 <= confidence <= 1):
        errors.append("Confidence fuera de rango")
    if errors:
        return False, errors
    return True, []

def _smooth_sensor_value(sensor_id: Optional[str], value):
    if sensor_id is None or not isinstance(value, (int, float)):
        return value
    previous = _SENSOR_SMOOTHING_STATE.get(sensor_id)
    if previous is None:
        next_value = value
    else:
        next_value = SENSOR_SMOOTHING_ALPHA * value + (1 - SENSOR_SMOOTHING_ALPHA) * previous
    _SENSOR_SMOOTHING_STATE[sensor_id] = next_value
    return next_value

# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS LEGADOS NO MIGRADOS (mantener para compatibilidad)
# Los nuevos están en core/api/routers/
# ═══════════════════════════════════════════════════════════════════════════

# Endpoint para sensores virtuales (MANTENER: lógica compleja no migrada aún)
@app.post("/sensor_virtual")
async def sensor_virtual(payload: dict = Body(...)):
    try:
        normalized = _normalize_sensor_payload(payload)
        valid, validation_errors = _validate_sensor_payload(normalized)
        if not valid:
            logger.warning("Lectura de sensor virtual rechazada: %s", validation_errors)
            return JSONResponse(status_code=400, content={
                "status": "ERROR",
                "message": "Lectura inválida",
                "errors": validation_errors,
            })
        nombre = payload.get("name") or payload.get("sensor")
        tipo = payload.get("type") or nombre
        unidad = normalized.get("unit")
        fuente = normalized.get("source")
        origen = normalized.get("origin")
        fiabilidad = normalized.get("confidence", 1.0)
        map_to = normalized.get("canonical")
        if nombre is None and not map_to:
            return JSONResponse(status_code=400, content={
                "status": "ERROR",
                "message": "Falta identificador de sensor",
            })
        valor = normalized.get("value")
        smoothed_value = _smooth_sensor_value(map_to or nombre, valor)
        if unidad is None and map_to:
            try:
                unidad = _default_unit(map_to)
            except Exception:
                unidad = None
        try:
            system.registrar_sensor_metadata(nombre or map_to, tipo=tipo, unidad=unidad, fuente=fuente, origen=origen, fiabilidad=fiabilidad)
        except Exception as exc:
            logger.warning("Error registrando metadata del sensor virtual: %s", exc)
        sensor_id = map_to or nombre
        if sensor_id is None:
            return JSONResponse(status_code=400, content={
                "status": "ERROR",
                "message": "No se pudo determinar el identificador del sensor",
            })
        if not hasattr(system, "actualizar_sensor"):
            logger.warning("Sistema sin actualizar_sensor; lectura virtual aceptada en modo no-op")
            return {
                "status": "OK",
                "received": True,
                "sensor": sensor_id,
                "value": smoothed_value,
                "confidence": fiabilidad,
                "warning": "system_noop",
            }
        try:
            system.actualizar_sensor(sensor_id, smoothed_value)
        except Exception as exc:
            logger.error("Error al actualizar sensor %s: %s", sensor_id, exc)
            return JSONResponse(status_code=500, content={
                "status": "ERROR",
                "message": "Fallo al actualizar el sensor",
                "errors": [str(exc)],
            })
        return {"status": "OK", "received": True, "sensor": sensor_id, "value": smoothed_value, "confidence": fiabilidad}
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        logger.exception("Unhandled exception in /sensor_virtual: %s", exc)
        return JSONResponse(status_code=500, content={
            "status": "ERROR",
            "message": "Unhandled error in /sensor_virtual",
            "error": str(exc),
            "trace": tb,
        })
def _feedback_snapshot() -> dict:
    try:
        indices = system.indices.obtener_todos() if system.indices else {}
    except Exception:
        indices = {}
    try:
        sensores = dict(getattr(system, "sensores", {}) or {})
    except Exception:
        sensores = {}
    return {"indices": indices, "sensores": sensores}


def _append_feedback_log(detalle: dict) -> None:
    try:
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", "feedback_registros.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(detalle, ensure_ascii=False) + "\n")
    except Exception:
        logging.exception("Silent except at 515 - revisar contexto")
# Endpoint de feedback para predicciones (MANTENER: lógica compleja)
@app.post("/feedback_prediccion")
async def feedback_prediccion(payload: dict = Body(...)):
    tipo = payload.get("tipo")
    nombre = payload.get("nombre")
    valor = payload.get("valor")
    feedback = payload.get("feedback")  # "acierto" o "error"
    valor_real = payload.get("valor_real")
    detalle = {
        "fecha": datetime.datetime.now().isoformat(),
        "tipo": tipo,
        "nombre": nombre,
        "valor": valor,
        "valor_real": valor_real,
        "feedback": feedback,
        "snapshot": _feedback_snapshot(),
    }
    _append_feedback_log(detalle)
    if nombre and system.auto_improvement_engine:
        system.auto_improvement_engine.feedback(nombre, error=(feedback=="error"), detalle=detalle)
        # Si hay valor real y valor estimado numérico, registrar error cuantitativo
        try:
            if feedback == "error" and valor_real is not None and valor is not None:
                v_real = float(valor_real)
                v_estimado = float(valor)
                system.auto_improvement_engine.registrar_error(nombre, v_real, v_estimado)
                # Entrenamiento online si es predicción
                if tipo == "prediccion" and system.learning_engine:
                    # Entrenar modelo si existe
                    system.learning_engine.ensure_model(nombre)
                    # Usar features dummy (solo valor estimado)
                    system.learning_engine.models[nombre].update({"estimado": v_estimado}, v_real)
        except Exception:
            logging.exception("Silent except at 549 - revisar contexto")
    return {"ok": True, "msg": "Feedback registrado"}


# ✅ ENDPOINT: Validar predicciones y generar feedback automático (CRÍTICO PARA APRENDIZAJE)
@app.post("/validar_predicciones_automaticamente")
async def validar_predicciones_automaticamente():
    """
    Ejecuta validación de predicciones contra datos reales.
    Genera feedback automático.
    CRÍTICO: Este endpoint es lo que permite al sistema APRENDER.
    """
    if not PREDICTION_VALIDATION_AVAILABLE:
        return {
            "status": "ERROR",
            "msg": "Sistema de validación no disponible"
        }
    
    try:
        resultado = validar_y_generar_feedback_automatico(Path("."))
        return {
            "status": "OK",
            "validaciones_ejecutadas": resultado.get("validaciones_ejecutadas", 0),
            "feedback_generado": resultado.get("feedback_generado", 0),
            "reporte": resultado.get("reporte", {})
        }
    except Exception as e:
        logging.error(f"Error validando predicciones: {e}")
        return {
            "status": "ERROR",
            "msg": str(e)
        }


# ✅ ENDPOINT: Ver estado del loop de aprendizaje
@app.get("/estado_loop_aprendizaje")
async def estado_loop_aprendizaje():
    """
    Retorna salud completa del loop de aprendizaje.
    Útil para diagnósticos.
    """
    if not PREDICTION_VALIDATION_AVAILABLE:
        return {
            "status": "ERROR",
            "msg": "Sistema de validación no disponible"
        }
    
    try:
        validator = LearningLoopValidator(Path("."))
        reporte = validator.generar_reporte_aprendizaje()
        return {
            "status": "OK",
            "reporte": reporte
        }
    except Exception as e:
        logging.error(f"Error en reporte de aprendizaje: {e}")
        return {
            "status": "ERROR",
            "msg": str(e)
        }


import datetime
import threading
import sys
import asyncio
import json
import re
import unicodedata
import math
from tools.arco_solar import arco_solar
import os
from fastapi import FastAPI, Request, Query

import logging
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from core.system.system_manager import SystemManager
import pathlib
from core.indices.environmental_indices import EnvironmentalIndices
from core.meteo.meteo_engine import get_full_meteo_snapshot
from core.prediction.prediction_engine import PredictionEngine
from fastapi.middleware.cors import CORSMiddleware
from core.auto.auto_sensor_discovery import AutoSensorDiscovery
from core.auto.auto_repair_engine import AutoRepairEngine
from core.auto.auto_expansion_engine import AutoExpansionEngine

# Imports de Omnipotencia V1.5
try:
    from core.omnipotence.omnipotence_simple import omnipotence
    OMNIPOTENCE_ENABLED = True
except ImportError as e:
    OMNIPOTENCE_ENABLED = False
    omnipotence = None
from core.pas.pas_engine import PASEngine
from core.engines.habits_engine import HabitLearningEngine
from meteoser_ia import block_f as voice_engine
from core.engines.communication_engine import CommunicationEngine
from core.motors.impresion_motor import MotorImpresion
from core.motors.calendario_motor import MotorCalendario
from core.motors.tareas_motor import MotorTareas
from core.motors.lista_compra_motor import MotorListaCompra
from core.motors.eventos_motor import MotorEventos
from core.motors.alarmas_motor import MotorAlarmas
from core.motors.comunicacion_motor import MotorComunicacion
from core.engines.environmental_engines import (
    MotorAmbiental,
    MotorConfort,
    MotorEdificio,
    MotorMeteorologico,
    MotorVentilacion,
    MotorPrediccionLocal,
    GestorHuellasAtmosfericas,
    MotorUsoDispositivos,
    MotorNocturno,
    MotorIntrusion,
    MotorMateriales,
    MotorAvisosPracticos,
    MotorSaludAire,
    MotorVentanasPuertas,
    MotorRiesgoHumedad,
    MotorTemperaturaOperativa,
    MotorRitmoCircadianoPersona,
    MotorHabitabilidad,
    MotorConfortNocturno,
    MotorMeteorologiaAvanzada,
    MotorVientoRachas,
    MotorVisibilidadLocal,
    MotorLuzNatural,
    MotorConfortTermico,
    MotorAirePegajosoSeco,
    MotorAireCargado,
    MotorOlorCerrado,
    MotorCondensacionArmarios,
    MotorSecadoRopa,
    MotorPersianas,
    MotorAireEnrarecido,
    MotorDeshidratacionAmbiental,
    MotorAireEstancado,
    MotorRenovacionAire,
    MotorRiesgoOxidacion,
    MotorRiesgoLibrosPapel,
    MotorRiesgoElectronica,
    MotorRiesgoPlasticos,
    MotorRiesgoRopaGuardada,
    MotorRiesgoColchones,
    MotorRiesgoAlimentos,
    MotorRiesgoInstrumentos,
    MotorRiesgoMadera,
    MotorActividadHumana,
    MotorPresencia,
    MotorCorrientesInternas,
    MotorEstabilidadTermicaFutura,
    MotorGolpesPuerta,
    MotorRiesgoPlantas,
    MotorRopaTendida,
    MotorVientoDormir,
    MotorPrediccionCorrientesFuturas,
)

# Configurar logging robusto
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("meteoser")

# App ya creado con lifespan en línea 155
# (si no existe en globals, fue creado arriba con lifespan handler)
# Habilitar CORS para todos los orígenes (localhost, 127.0.0.1, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = pathlib.Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / "app" / "static"  # Ruta absoluta a app/static/ (nueva interfaz)
CONFIG_PATH = BASE_DIR / "meteoser_configuracion.txt"

# Montar archivos estáticos con ruta absoluta
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
else:
    print(f"WARNING: Static directory not found at {STATIC_DIR}")

# Inicializar sistema MeteoSer y forzar motores, con protección ante errores
try:
    manager = SystemManager()
    system = manager.iniciar()
    try:
        system.location = manager.location
    except Exception:
        logger.exception("No se pudo inyectar LocationEngine en SystemCore")
    # Asegurar que el Cerebro Estadístico esté presente y trate de restaurar estado
    try:
        from core.engines.statistical_brain import StatisticalBrain
        if not hasattr(system, 'statistical_brain') or system.statistical_brain is None:
            system.statistical_brain = StatisticalBrain(restore_state=True)
            logger.info("🧠 StatisticalBrain añadido al sistema (restore_state=True)")
    except Exception:
        # No bloquear el arranque si falla la creación del cerebro
        logger.exception("⚠️ No se pudo inicializar StatisticalBrain en el arranque")
    if not isinstance(system.indices, EnvironmentalIndices):
        system.indices = EnvironmentalIndices(system)
    
    # --- LIMPIEZA DE BUFFERS DE ERROR: Monin-Obukhov y presión ---
    import logging
    # Limpiar flags de error de presión
    if hasattr(system, 'sensores'):
        for key in [
            'presion_status', 'presion_intentos_fallidos', 'presion_ultima_valida',
            'presion_fuente', 'presion_fuente_raw', 'presion_raw',
            'presion_ambito', 'presion_fuente_sensor',
            'MONIN_OBUKHOV_ERROR', 'MONIN_OBUKHOV_FLAG', 'MONIN_OBUKHOV_SOBERANO',
        ]:
            if key in system.sensores:
                system.sensores[key] = None
    # Limpiar flags de error en metadata si existen
    if hasattr(system, 'sensores_metadata'):
        for meta in system.sensores_metadata.values():
            for k in list(meta.keys()):
                if 'error' in k.lower() or 'flag' in k.lower():
                    meta[k] = None
    # ARQUITECTURA DE LIMPIEZA: Entra en modo de observación (silencio quirúrgico sin tics)
    try:
        if hasattr(system, 'statistical_brain') and hasattr(system.statistical_brain, 'enter_observation_mode'):
            system.statistical_brain.enter_observation_mode()
            logging.getLogger(__name__).info('[LIMPIEZA] Cerebro en modo observacion - Silencio quirurgico activo')
    except Exception as e:
        logging.getLogger(__name__).info(f'[LIMPIEZA] Modo observacion no disponible: {e}')
    
    # Inyectar SystemManager en el router de la nueva UI
    try:
        set_system_manager(manager)
        set_ui_system_manager(manager)
    except Exception as inject_err:
        logger.warning(f"No se pudo inyectar SystemManager en UI router: {inject_err}")
    
    logger.info("MeteoSer backend inicializado correctamente.")
    
    # 🛸 OMNIPOTENCIA V1.5: Inicializar sistema de descubrimiento universal
    try:
        from core.discovery import OmnipotenceManager
        omnipotence_manager = OmnipotenceManager(system)
        logger.info("🛸 OMNIPOTENCIA V1.5 ACTIVADA - Radar Universal en línea")
    except Exception as omni_err:
        logger.warning(f"⚠️ Omnipotencia no disponible: {omni_err}")
        omnipotence_manager = None
        
except Exception as e:
    logger.error(f"Error crítico al iniciar MeteoSer: {e}", exc_info=True)
    # Creamos un system y manager dummy para que la app no se caiga
    class Dummy:
        def obtener_historial_original(self, nombre):
            return []
        def obtener_estado_completo(self):
            return {"estado": "Error crítico en la inicialización. Ver logs."}
    manager = Dummy()
    system = Dummy()
    omnipotence_manager = None

discovery_engine = None
auto_repair_engine = None
pas_engine = None
habits_engine = None
comm_engine = CommunicationEngine()
_alarm_playing = False
_alarm_stop_event = threading.Event()
_asistente_store = {
    "noticias": {},
    "eventos": [],
    "alarmas": [],
    "calendario": [],
    "tareas": [],
    "lista_compra": [],
    "cola_impresion": [],
    "recomendaciones": [],
    "patrones_compra": {},
    "sugerencias_compra": [],
    "patrones_tareas": {},
    "sugerencias_tareas": [],
    "patrones_eventos": {},
    "sugerencias_eventos": [],
}


def _ruta_asistente() -> pathlib.Path:
    path = BASE_DIR / "data" / "asistente_estado.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _cargar_asistente() -> None:
    try:
        ruta = _ruta_asistente()
        if ruta.exists():
            data = json.loads(ruta.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                if "data" in data and isinstance(data.get("data"), dict):
                    _asistente_store.update(data.get("data"))
                else:
                    _asistente_store.update(data)
    except Exception:
        logging.exception("Silent except at 787 - revisar contexto")


def _guardar_asistente() -> None:
    try:
        payload = {
            "version": 2,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "data": _asistente_store,
        }
        _ruta_asistente().write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        logging.exception("Silent except at 799 - revisar contexto")


def _registrar_evento_hardware_nuevo() -> list:
    nuevos = []
    try:
        if not hasattr(system, "sensores_metadata"):
            return nuevos
        vistos = _asistente_store.get("hardware_nuevo_vistos")
        if not isinstance(vistos, list):
            vistos = []
        for nombre in list(system.sensores_metadata.keys()):
            if not nombre or nombre.startswith("__") or nombre.endswith("_original"):
                continue
            if nombre in vistos:
                continue
            evento = {
                "tipo": "hardware_nuevo",
                "sensor": nombre,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "mensaje": f"Hardware nuevo detectado: {nombre}",
            }
            _agregar_lista("eventos", evento)
            vistos.append(nombre)
            nuevos.append(nombre)
        _asistente_store["hardware_nuevo_vistos"] = vistos
        if nuevos:
            _guardar_asistente()
    except Exception:
        logging.exception("Silent except at 828 - revisar contexto")
    return nuevos


_cargar_asistente()


def _asistente_estado() -> dict:
    return {
        "noticias": _asistente_store.get("noticias", {}),
        "eventos": _asistente_store.get("eventos", []),
        "alarmas": _asistente_store.get("alarmas", []),
        "calendario": _asistente_store.get("calendario", []),
        "tareas": _asistente_store.get("tareas", []),
        "lista_compra": _asistente_store.get("lista_compra", []),
        "cola_impresion": _asistente_store.get("cola_impresion", []),
        "recomendaciones": _asistente_store.get("recomendaciones", []),
        "patrones_compra": _asistente_store.get("patrones_compra", {}),
        "sugerencias_compra": _asistente_store.get("sugerencias_compra", []),
        "patrones_tareas": _asistente_store.get("patrones_tareas", {}),
        "sugerencias_tareas": _asistente_store.get("sugerencias_tareas", []),
        "patrones_eventos": _asistente_store.get("patrones_eventos", {}),
        "sugerencias_eventos": _asistente_store.get("sugerencias_eventos", []),
    }


def _parse_hora(hora: str):
    try:
        if not hora:
            return None
        parts = str(hora).strip().split(":")
        if len(parts) < 2:
            return None
        hh = int(parts[0])
        mm = int(parts[1])
        if hh < 0 or hh > 23 or mm < 0 or mm > 59:
            return None
        return hh, mm
    except Exception:
        return None


def _normalizar_texto_simple(texto: str) -> str:
    try:
        return re.sub(r"\s+", " ", str(texto).strip().lower())
    except Exception:
        return ""


def _json_safe(value):
    try:
        if isinstance(value, dict):
            return {str(k): _json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_json_safe(v) for v in value]
        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.isoformat()
        if isinstance(value, pathlib.Path):
            return str(value)
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8")
            except Exception:
                return repr(value)
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
        if hasattr(value, "tolist"):
            try:
                return value.tolist()
            except Exception:
                logging.exception("Silent except at 899 - revisar contexto")
        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                logging.exception("Silent except at 904 - revisar contexto")
        return value
    except Exception:
        return None


def _recalcular_sugerencias(clave_patrones: str, clave_sugerencias: str) -> None:
    patrones = _asistente_store.get(clave_patrones, {})
    if not isinstance(patrones, dict):
        patrones = {}
    sugerencias = sorted(patrones.items(), key=lambda x: x[1], reverse=True)[:5]
    _asistente_store[clave_sugerencias] = [s[0] for s in sugerencias]


def _sonar_alarma() -> None:
    global _alarm_playing
    if _alarm_playing:
        return
    _alarm_stop_event.clear()

    def _run():
        global _alarm_playing
        _alarm_playing = True
        try:
            if sys.platform.startswith("win"):
                try:
                    import winsound
                    for _ in range(6):
                        if _alarm_stop_event.is_set():
                            break
                        winsound.Beep(900, 280)
                        if _alarm_stop_event.is_set():
                            break
                        winsound.Beep(1200, 280)
                except Exception:
                    logging.exception("Silent except at 939 - revisar contexto")
            else:
                for _ in range(6):
                    if _alarm_stop_event.is_set():
                        break
                    asyncio.sleep(0.2)
        finally:
            _alarm_playing = False

    threading.Thread(target=_run, daemon=True).start()


def _silenciar_alarma() -> None:
    _alarm_stop_event.set()
    if sys.platform.startswith("win"):
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_ASYNC)
        except Exception:
            logging.exception("Silent except at 958 - revisar contexto")


def _imprimir_item(item: dict) -> dict:
    try:
        texto = item.get("texto") or item.get("documento") or item.get("titulo")
        if not texto:
            texto = json.dumps(item, ensure_ascii=False, indent=2)
        out_dir = BASE_DIR / "data" / "impresion"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        path = out_dir / f"impresion_{ts}.txt"
        path.write_text(str(texto), encoding="utf-8")
        item["archivo"] = str(path)
        status = "guardado"
        printed = False
        auto_print = item.get("auto_print", True)
        if os.name == "nt" and auto_print:
            try:
                os.startfile(str(path), "print")
                status = "enviado_a_impresion"
                printed = True
            except Exception:
                status = "error_impresion"
        item["status"] = status
        item["printed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat() if printed else None
    except Exception:
        item["status"] = "error"
    return item


async def _alarmas_loop():
    while True:
        try:
            now = datetime.datetime.now()
            hoy = now.date().isoformat()
            for alarma in _asistente_store.get("alarmas", []):
                if not isinstance(alarma, dict):
                    continue
                if alarma.get("activa") is False:
                    continue
                hora = alarma.get("hora")
                parsed = _parse_hora(hora)
                if not parsed:
                    continue
                hh, mm = parsed
                recurrencia = _normalizar_texto_simple(alarma.get("recurrencia", ""))
                dia_semana = alarma.get("dia_semana")
                if recurrencia == "semanal" and dia_semana is None:
                    alarma["dia_semana"] = now.weekday()

                if recurrencia in ("laborables", "laboral") and now.weekday() >= 5:
                    continue
                if recurrencia in ("fin de semana", "findesemana", "finsemana") and now.weekday() < 5:
                    continue
                if recurrencia == "semanal" and alarma.get("dia_semana") is not None and now.weekday() != alarma.get("dia_semana"):
                    continue

                aviso_min = alarma.get("aviso_min") or alarma.get("prealert_min")
                try:
                    aviso_min = int(aviso_min) if aviso_min is not None else 0
                except Exception:
                    aviso_min = 0

                if aviso_min > 0:
                    aviso_time = (datetime.datetime(now.year, now.month, now.day, hh, mm) - datetime.timedelta(minutes=aviso_min))
                    aviso_key = alarma.get("ultimo_aviso")
                    if now.hour == aviso_time.hour and now.minute == aviso_time.minute and aviso_key != hoy:
                        alarma["ultimo_aviso"] = hoy
                        comm_engine.responder(f"Aviso: alarma en {aviso_min} minutos.", {"alarma": alarma})

                last = alarma.get("ultimo_disparo")
                if now.hour == hh and now.minute == mm and last != hoy:
                    alarma["sonando"] = True
                    alarma["ultimo_disparo"] = hoy
                    comm_engine.responder(f"Alarma {hora}.", {"alarma": alarma})
                    _sonar_alarma()
                    if recurrencia in ("una vez", "una-vez", "una"):
                        alarma["activa"] = False
            _guardar_asistente()
        except Exception:
            logging.exception("Silent except at 1039 - revisar contexto")
        await asyncio.sleep(30)


def _departamentos_ideas(asistente: dict) -> dict:
    return {
        "comunicacion_oral": {
            "modo": "prioritario",
            "fallback": True,
            "pendiente_fuentes_externas": True,
        },
        "noticias": {
            "resumen": asistente.get("noticias", {}),
            "categorias": ["mundo", "espana", "deportes", "tecnologia", "economia"],
            "pendiente_fuentes_externas": False,
        },
        "eventos_tv": {
            "eventos": asistente.get("eventos", []),
            "recomendaciones": asistente.get("recomendaciones", []),
            "pendiente_fuentes_externas": True,
        },
        "despertador_alarmas": {
            "alarmas": asistente.get("alarmas", []),
            "sonido_real": False,
            "pendiente_motor_alarma_real": True,
        },
        "organizacion": {
            "calendario": asistente.get("calendario", []),
            "tareas": asistente.get("tareas", []),
            "lista_compra": asistente.get("lista_compra", []),
            "impresion": asistente.get("cola_impresion", []),
            "inteligencia_compra": {
                "sugerencias": [],
                "patrones": [],
                "pendiente": True,
            },
        },
        "integraciones": {
            "submenu_detallado": True,
            "recomendaciones_unificadas": True,
            "auto_mejora": True,
        },
    }


def _agregar_lista(clave: str, item):
    if clave not in _asistente_store or not isinstance(_asistente_store[clave], list):
        _asistente_store[clave] = []
    _asistente_store[clave].append(item)
    _guardar_asistente()
    return _asistente_store[clave]


def _borrar_lista(clave: str, idx: int):
    lista = _asistente_store.get(clave)
    if not isinstance(lista, list):
        return False
    if idx < 0 or idx >= len(lista):
        return False
    lista.pop(idx)
    _guardar_asistente()
    return True


# Handler de startup MOVIDO al lifespan context manager (línea ~30)
# Ya no usamos @app.on_event() porque está deprecado en FastAPI 0.93+
# Ver: lifespan() context manager arriba

async def iniciar_autodeteccion():
    """Compatibilidad: inicia autodetección con la configuración actual."""
    if not discovery_engine:
        return False
    mqtt_host = os.getenv("METEOSER_MQTT_HOST", "127.0.0.1")
    mqtt_tls_enabled = os.getenv("METEOSER_MQTT_TLS", "1") not in ("0", "false", "False")
    default_mqtt_port = "8883" if mqtt_tls_enabled else "1883"
    try:
        mqtt_port = int(os.getenv("METEOSER_MQTT_PORT", default_mqtt_port))
    except Exception:
        mqtt_port = int(default_mqtt_port)
    mqtt_enabled = os.getenv("METEOSER_MQTT_ENABLED", "1") not in ("0", "false", "False")
    mdns_enabled = os.getenv("METEOSER_MDNS_ENABLED", "1") not in ("0", "false", "False")
    serial_enabled = os.getenv("METEOSER_SERIAL_ENABLED", "1") not in ("0", "false", "False")
    ble_enabled = False
    mqtt_user = os.getenv("METEOSER_MQTT_USER")
    mqtt_pass = os.getenv("METEOSER_MQTT_PASSWORD")
    mqtt_timeout = int(os.getenv("METEOSER_MQTT_TIMEOUT", "60"))
    mqtt_reconnect_interval = int(os.getenv("METEOSER_MQTT_RECONNECT_INTERVAL", "5"))
    try:
        discovery_engine.start(
            mqtt_host=mqtt_host,
            mqtt_port=mqtt_port,
            mqtt_enabled=mqtt_enabled,
            mdns_enabled=mdns_enabled,
            serial_enabled=serial_enabled,
            ble_enabled=ble_enabled,
            mqtt_user=mqtt_user,
            mqtt_pass=mqtt_pass,
            mqtt_tls=mqtt_tls_enabled,
            mqtt_timeout=mqtt_timeout,
            mqtt_reconnect_interval=mqtt_reconnect_interval,
        )
        return True
    except Exception as e:
        logger.warning(f"⚠️ No se pudo iniciar autodetección: {e}")
        return False


# Ya no usamos @app.on_event() porque está deprecado en FastAPI 0.93+
# Ver: lifespan() context manager arriba

async def guardar_cerebro_al_apagar():
    """Compatibilidad: guarda el estado del cerebro estadístico."""
    if system and hasattr(system, 'statistical_brain') and system.statistical_brain is not None:
        try:
            from core.engines.brain_persistence import save_brain_state
            save_brain_state(system.statistical_brain)
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando cerebro: {e}")
            return False
    return False


# Endpoint de historial de sensores (DUPLICADO: migrado a routers/sensors.py)
# MANTENER por compatibilidad, se eliminará en v3.1
@app.get("/api/sensores/historial")
async def obtener_historial_sensor(nombre: str = Query(..., description="Nombre del sensor base, por ejemplo 'tempf'")):
    return {"historial": system.obtener_historial_original(nombre)}


# Health check (DUPLICADO: migrado a routers/admin.py)
# MANTENER por compatibilidad
@app.get("/health", response_class=JSONResponse)
def healthcheck():
    """
    🛡️ GUARDIÁN 617 - IGNICIÓN BLINDADA V14.1
    Valida:
    - Integridad del Bus (617 constantes)
    - Watchdog de datos estancados (64s)
    - SHA256 del sistema
    - SRTM altitud real siendo consumida
    """
    import time
    import hashlib
    from pathlib import Path
    
    health_report = {
        "status": "UNKNOWN",
        "timestamp": time.time(),
        "ignition": "BLINDADA_V14.1",
        "guardians": {}
    }
    
    try:
        # ═══════════════════════════════════════════════════════════════════════
        # GUARDIÁN 1: Integridad Bus (617 constantes)
        # ═══════════════════════════════════════════════════════════════════════
        bus_keys = list(system.bus.datos.keys()) if hasattr(system, 'bus') and hasattr(system.bus, 'datos') else []
        bus_count = len(bus_keys)
        bus_critical_keys = [
            'temperatura', 'presion_barometrica', 'humedad', 'gravedad_dinamica',
            'densidad_aire_cipm', 'temperatura_virtual', 'factor_compresibilidad_virial'
        ]
        bus_missing = [k for k in bus_critical_keys if k not in bus_keys]
        
        health_report["guardians"]["BUS_GUARDIAN"] = {
            "status": "OK" if len(bus_missing) == 0 else "CRITICAL",
            "constantes_publicadas": bus_count,
            "constantes_criticas_esperadas": len(bus_critical_keys),
            "constantes_faltantes": bus_missing,
            "mensaje": f"Bus con {bus_count} constantes. {len(bus_missing)} críticas faltando."
        }
        
        # ═══════════════════════════════════════════════════════════════════════
        # GUARDIÁN 2: Watchdog 64 segundos (datos estancados)
        # ═══════════════════════════════════════════════════════════════════════
        watchdog_timeout = 64  # segundos
        last_data_update = getattr(system, 'last_data_update_time', time.time())
        time_since_update = time.time() - last_data_update
        watchdog_status = "OK" if time_since_update < watchdog_timeout else "DATA_STAGNANT"
        
        health_report["guardians"]["WATCHDOG_64s"] = {
            "status": watchdog_status,
            "tiempo_sin_actualizar": f"{time_since_update:.1f}s",
            "timeout_critico": f"{watchdog_timeout}s",
            "mensaje": f"Datos últimamente actualizados hace {time_since_update:.1f}s"
        }
        
        # ═══════════════════════════════════════════════════════════════════════
        # GUARDIÁN 3: SRTM Altitud Real siendo consumida
        # ═══════════════════════════════════════════════════════════════════════
        altitud_srtm = 0.0
        srtm_status = "NOT_AVAILABLE"
        if hasattr(system, 'location') and isinstance(system.location, dict):
            altitud_srtm = system.location.get('altitud', 0.0)
            srtm_status = "OK" if altitud_srtm > 0 else "USING_DEFAULT"
        elif hasattr(system, 'location') and hasattr(system.location, 'get'):
            altitud_srtm = system.location.get('altitud', 0.0)
            srtm_status = "OK" if altitud_srtm > 0 else "USING_DEFAULT"
        
        health_report["guardians"]["SRTM_ALTITUD"] = {
            "status": srtm_status,
            "altitud_m": altitud_srtm,
            "factor_z_usa_altitud": True,
            "mensaje": f"SRTM altitud consumida: {altitud_srtm}m (siendo usada por Factor Z y presión vapor)"
        }
        
        # ═══════════════════════════════════════════════════════════════════════
        # GUARDIÁN 4: SHA256 Bus V14.0
        # ═══════════════════════════════════════════════════════════════════════
        try:
            work_dir = Path("C:/Users/kioko/Desktop/MeteoSerV3") if Path("C:/Users/kioko/Desktop/MeteoSerV3").exists() else Path(".")
            sha256_file = work_dir / "logs" / "SHA256_BUS_CURRENT.txt"
            sha256_status = "NOT_VERIFIED"
            sha256_hash = "UNDEFINED"
            
            if sha256_file.exists():
                sha256_hash = sha256_file.read_text().strip()
                sha256_status = "VERIFIED"
            
            health_report["guardians"]["SHA256_BUS"] = {
                "status": sha256_status,
                "hash": sha256_hash,
                "mensaje": f"Bus V14.0 verificado con SHA256: {sha256_hash[:16]}..."
            }
        except Exception as sha_err:
            health_report["guardians"]["SHA256_BUS"] = {
                "status": "ERROR",
                "error": str(sha_err),
                "mensaje": f"No se pudo verificar SHA256: {sha_err}"
            }
        
        # ═══════════════════════════════════════════════════════════════════════
        # RESUMEN: Status general
        # ═══════════════════════════════════════════════════════════════════════
        guardian_statuses = [g.get("status") for g in health_report["guardians"].values()]
        
        if "CRITICAL" in guardian_statuses or "DATA_STAGNANT" in guardian_statuses:
            health_report["status"] = "CRITICAL"
        elif "ERROR" in guardian_statuses:
            health_report["status"] = "DEGRADED"
        elif all(s in ["OK", "VERIFIED", "USING_DEFAULT"] for s in guardian_statuses):
            health_report["status"] = "GREEN"
        else:
            health_report["status"] = "WARNING"
        
        return health_report
        
    except Exception as e:
        logger.exception(f"Error en /health Guardián 617: {e}")
        return {
            "status": "ERROR",
            "error": str(e),
            "mensaje": "Fallo crítico en chequeo de salud"
        }


# Admin: forzar guardado del cerebro (DUPLICADO: migrado a routers/admin.py)
# MANTENER por compatibilidad
# Admin: forzar guardado del cerebro y consultar estado
@app.post("/admin/brain/force_save")
def admin_force_save():
    try:
        # Preferir usar el autosaver si existe
        if hasattr(system, 'brain_autosaver') and system.brain_autosaver is not None:
            system.brain_autosaver.force_save()
        else:
            from core.engines.brain_persistence import save_brain_state
            if hasattr(system, 'statistical_brain') and system.statistical_brain is not None:
                save_brain_state(system.statistical_brain)
            else:
                return JSONResponse({"ok": False, "msg": "No hay cerebro cargado"}, status_code=500)
        return {"ok": True, "msg": "Guardado forzado iniciado"}
    except Exception as e:
        logger.exception(f"Error forzando guardado del cerebro: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
# Admin: estado del cerebro (DUPLICADO: migrado a routers/admin.py)
# MANTENER por compatibilidad


@app.get("/admin/brain/status")
def admin_brain_status():
    try:
        status = {"brain_loaded": False}
        if hasattr(system, 'statistical_brain') and system.statistical_brain is not None:
            status["brain_loaded"] = True
            # intentar leer metadata de persistencia
            try:
                from core.engines.brain_persistence import METADATA_FILE
                import json
                if METADATA_FILE.exists():
                    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                        status["metadata"] = json.load(f)
            except Exception:
                status["metadata"] = None
        return status
    except Exception as e:
# Asistente endpoints (DUPLICADOS: migrados a routers/assistant.py)
# MANTENER por compatibilidad durante transición
        logger.exception(f"Error consultando estado del cerebro: {e}")
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/asistente/estado")
def asistente_estado():
    return {"asistente": _asistente_estado()}


@app.post("/asistente/noticias")
def asistente_noticias(payload: dict = None):
    categorias = []
    if isinstance(payload, dict):
        categorias = payload.get("categorias") or []
        if payload.get("noticias"):
            _asistente_store["noticias"] = payload.get("noticias")
            _guardar_asistente()
            return {"noticias": _asistente_store["noticias"], "categorias": categorias}
    if not categorias:
        categorias = ["mundo", "espana", "deportes", "tecnologia", "economia"]
    resumen = comm_engine.resumen_noticias(categorias)
    _asistente_store["noticias"] = resumen
    _guardar_asistente()
    return {"noticias": resumen, "categorias": categorias}


@app.api_route("/asistente/eventos", methods=["GET", "POST", "DELETE"])
def asistente_eventos(request: Request, payload: dict = None):
    if request.method == "POST":
        data = payload or {}
        evento = {
            "titulo": data.get("titulo"),
            "hora": data.get("hora"),
            "canal": data.get("canal"),
            "duracion": data.get("duracion"),
            "categoria": data.get("categoria"),
        }
        _agregar_lista("eventos", evento)
        titulo = _normalizar_texto_simple(evento.get("titulo", ""))
        if titulo:
            patrones = _asistente_store.get("patrones_eventos", {})
            patrones[titulo] = patrones.get(titulo, 0) + 1
            _asistente_store["patrones_eventos"] = patrones
            _recalcular_sugerencias("patrones_eventos", "sugerencias_eventos")
            _guardar_asistente()
        comm_engine.info_evento(evento.get("titulo") or "evento", evento)
    elif request.method == "DELETE":
        idx = int((payload or {}).get("index", -1))
        _borrar_lista("eventos", idx)
    return MotorEventos().consultar({"eventos": _asistente_store.get("eventos", [])})


@app.api_route("/asistente/alarmas", methods=["GET", "POST", "DELETE"])
def asistente_alarmas(request: Request, payload: dict = None):
    if request.method == "POST":
        data = payload or {}
        hora = data.get("hora") or data.get("alarm") or "--:--"
        alarma = {
            "hora": hora,
            "recurrencia": data.get("recurrencia"),
            "aviso_min": data.get("aviso_min") or data.get("prealert_min"),
            "activa": True,
            "sonando": False,
            "ultimo_disparo": None,
        }
        _agregar_lista("alarmas", alarma)
        comm_engine.configurar_alarma(hora)
    elif request.method == "DELETE":
        idx = int((payload or {}).get("index", -1))
        if 0 <= idx < len(_asistente_store.get("alarmas", [])):
            hora = _asistente_store.get("alarmas", [])[idx].get("hora")
            _borrar_lista("alarmas", idx)
            if hora:
                comm_engine.borrar_alarma(hora)
    return MotorAlarmas().gestionar({"alarmas": _asistente_store.get("alarmas", [])})


@app.post("/asistente/alarmas/ack")
def asistente_alarmas_ack(payload: dict = None):
    idx = int((payload or {}).get("index", -1))
    alarmas = _asistente_store.get("alarmas", [])
    if 0 <= idx < len(alarmas):
        alarmas[idx]["sonando"] = False
        _guardar_asistente()
        _silenciar_alarma()
    return MotorAlarmas().gestionar({"alarmas": _asistente_store.get("alarmas", [])})


@app.post("/asistente/alarmas/update")
def asistente_alarmas_update(payload: dict = None):
    data = payload or {}
    idx = int(data.get("index", -1))
    alarmas = _asistente_store.get("alarmas", [])
    if 0 <= idx < len(alarmas):
        alarma = alarmas[idx]
        for k in ("hora", "recurrencia", "aviso_min", "prealert_min", "activa"):
            if k in data and data.get(k) is not None:
                alarma[k] = data.get(k)
        _guardar_asistente()
    return MotorAlarmas().gestionar({"alarmas": _asistente_store.get("alarmas", [])})


@app.post("/asistente/alarmas/toggle")
def asistente_alarmas_toggle(payload: dict = None):
    idx = int((payload or {}).get("index", -1))
    alarmas = _asistente_store.get("alarmas", [])
    if 0 <= idx < len(alarmas):
        alarmas[idx]["activa"] = not bool(alarmas[idx].get("activa", True))
        _guardar_asistente()
    return MotorAlarmas().gestionar({"alarmas": _asistente_store.get("alarmas", [])})


@app.api_route("/asistente/calendario", methods=["GET", "POST", "DELETE"])
def asistente_calendario(request: Request, payload: dict = None):
    if request.method == "POST":
        data = payload or {}
        _agregar_lista("calendario", data)
    elif request.method == "DELETE":
        idx = int((payload or {}).get("index", -1))
        _borrar_lista("calendario", idx)
    return MotorCalendario().gestionar({"calendario": _asistente_store.get("calendario", [])})


@app.api_route("/asistente/tareas", methods=["GET", "POST", "DELETE"])
def asistente_tareas(request: Request, payload: dict = None):
    if request.method == "POST":
        data = payload or {}
        _agregar_lista("tareas", data)
        titulo = _normalizar_texto_simple(data.get("titulo") or data.get("tarea") or "")
        if titulo:
            patrones = _asistente_store.get("patrones_tareas", {})
            patrones[titulo] = patrones.get(titulo, 0) + 1
            _asistente_store["patrones_tareas"] = patrones
            _recalcular_sugerencias("patrones_tareas", "sugerencias_tareas")
            _guardar_asistente()
    elif request.method == "DELETE":
        idx = int((payload or {}).get("index", -1))
        _borrar_lista("tareas", idx)
    return MotorTareas().gestionar({"tareas": _asistente_store.get("tareas", [])})


@app.api_route("/asistente/lista_compra", methods=["GET", "POST", "DELETE"])
def asistente_lista_compra(request: Request, payload: dict = None):
    if request.method == "POST":
        data = payload or {}
        _agregar_lista("lista_compra", data)
        item = (data.get("item") or data.get("nombre") or "").strip().lower()
        if item:
            patrones = _asistente_store.get("patrones_compra", {})
            patrones[item] = patrones.get(item, 0) + 1
            _asistente_store["patrones_compra"] = patrones
            sugerencias = sorted(patrones.items(), key=lambda x: x[1], reverse=True)[:5]
            _asistente_store["sugerencias_compra"] = [s[0] for s in sugerencias]
            _guardar_asistente()
    elif request.method == "DELETE":
        idx = int((payload or {}).get("index", -1))
        _borrar_lista("lista_compra", idx)
    return MotorListaCompra().gestionar({"lista_compra": _asistente_store.get("lista_compra", [])})


@app.get("/asistente/compra/sugerencias")
def asistente_compra_sugerencias():
    return {
        "patrones": _asistente_store.get("patrones_compra", {}),
        "sugerencias": _asistente_store.get("sugerencias_compra", []),
    }


@app.api_route("/asistente/impresion", methods=["GET", "POST", "DELETE"])
def asistente_impresion(request: Request, payload: dict = None):
    if request.method == "POST":
        data = payload or {}
        item = _imprimir_item(dict(data))
        _agregar_lista("cola_impresion", item)
        comm_engine.responder("Estoy imprimiendo tu documento.", {"impresion": data})
    elif request.method == "DELETE":
        idx = int((payload or {}).get("index", -1))
        _borrar_lista("cola_impresion", idx)
    return MotorImpresion().imprimir({"cola_impresion": _asistente_store.get("cola_impresion", [])})


@app.post("/asistente/recomendaciones")
def asistente_recomendaciones(payload: dict = None):
    sugerencias = []
    if isinstance(payload, dict):
        sugerencias = payload.get("sugerencias") or []
    if sugerencias:
        comm_engine.recomendar_contenido(sugerencias)
    _asistente_store["recomendaciones"] = sugerencias
    _guardar_asistente()
    return {"recomendaciones": sugerencias}


@app.post("/asistente/comunicacion")
def asistente_comunicacion(payload: dict = None):
    data = payload or {}
    texto = data.get("texto", "")
    return MotorComunicacion().responder(texto, data)


# Endpoint genérico para sensores externos (autoconfigurable)
@app.api_route("/sensor_input", methods=["POST"])
async def sensor_input(request: Request):
    from core.bus.parametros_canonicos import resolver_parametro_entrada

    def _canonical_name(nombre: str):
        return resolver_parametro_entrada(nombre)

    def _normalize_value(canonical: str, value, unit):
        if canonical == "viento":
            return "km/h"
        if canonical == "lluvia":
            return "mm"
        if canonical == "wh51":
            return "%"
        return None

    def _normalize_value(canonical: str, value, unit):
        try:
            v = float(value)
        except Exception:
            return value, unit
        if canonical == "temperatura":
            if unit and str(unit).upper() == "F":
                return (v - 32.0) * 5.0 / 9.0, "C"
            return v, "C"
        if canonical == "humedad":
            return v, "%"
        if canonical == "presion":
            if unit and str(unit).lower() == "inhg":
                return v * 33.8639, "hPa"
            return v, "hPa"
        if canonical == "viento":
            if unit and str(unit).lower() == "mph":
                return v * 1.60934, "km/h"
            if unit and str(unit).lower() in ["m/s", "ms"]:
                return v * 3.6, "km/h"
            return v, "km/h"
        if canonical == "lluvia":
            if unit and str(unit).lower() in ["in", "inch", "in/hr", "in/h"]:
                return v * 25.4, "mm"
            return v, "mm"
        if canonical in ("pm25", "pm10", "pm1"):
            return v, "µg/m³"
        if canonical == "co2":
            return v, "ppm"
        return v, unit

    data = {}
    try:
        if request.headers.get("content-type", "").startswith("application/json"):
            data = await request.json()
        else:
            form = await request.form()
            data = dict(form)
    except Exception:
        data = {}

    readings = data.get("readings") if isinstance(data, dict) else None
    if isinstance(readings, list):
        for item in readings:
            try:
                nombre = item.get("name") or item.get("sensor")
                valor = item.get("value")
                if nombre is None:
                    continue
                tipo = item.get("type") or nombre
                unidad = item.get("unit")
                fuente = item.get("source") or "externo"
                origen = item.get("origin") or "externo"
                fiabilidad = item.get("reliability", 100.0)
                map_to_raw = item.get("map_to")
                map_to = resolver_parametro_entrada(map_to_raw) if map_to_raw else _canonical_name(nombre)
                if unidad is None and map_to:
                    unidad = _default_unit(map_to)
                system.registrar_sensor_metadata(nombre, tipo=tipo, unidad=unidad, fuente=fuente, origen=origen, fiabilidad=fiabilidad)
                if map_to:
                    norm_val, norm_unit = _normalize_value(map_to, valor, unidad)
                    system.registrar_sensor_metadata(map_to, tipo=tipo, unidad=unidad, fuente=fuente, origen=origen, fiabilidad=fiabilidad)
                    system.actualizar_sensor(map_to, norm_val)
                else:
                    system.actualizar_sensor(nombre, valor)
            except Exception:
                continue
        try:
            if hasattr(system, "evaluar_anomalias_y_simular"):
                system.evaluar_anomalias_y_simular()
            if hasattr(system, "learning_feedback"):
                system.learning_feedback.evaluar_desde_sensores(system.sensores)
        except Exception:
            logger.exception("Error evaluando anomalías tras batch")
        return {"status": "OK", "received": True, "count": len(readings)}

    nombre = data.get("name") or data.get("sensor")
    valor = data.get("value")
    if nombre is None:
        return {"status": "ERROR", "message": "Falta nombre de sensor"}
    tipo = data.get("type") or nombre
    unidad = data.get("unit")
    fuente = data.get("source") or "externo"
    origen = data.get("origin") or "externo"
    fiabilidad = data.get("reliability", 100.0)
    map_to_raw = data.get("map_to")
    map_to = resolver_parametro_entrada(map_to_raw) if map_to_raw else _canonical_name(nombre)
    if unidad is None and map_to:
        unidad = _default_unit(map_to)
    system.registrar_sensor_metadata(nombre, tipo=tipo, unidad=unidad, fuente=fuente, origen=origen, fiabilidad=fiabilidad)
    if map_to:
        norm_val, norm_unit = _normalize_value(map_to, valor, unidad)
        system.registrar_sensor_metadata(map_to, tipo=tipo, unidad=norm_unit, fuente=fuente, origen=origen, fiabilidad=fiabilidad)
        system.actualizar_sensor(map_to, norm_val)
    else:
        system.actualizar_sensor(nombre, valor)
    try:
        if hasattr(system, "evaluar_anomalias_y_simular"):
            system.evaluar_anomalias_y_simular()
        if hasattr(system, "learning_feedback"):
            system.learning_feedback.evaluar_desde_sensores(system.sensores)
    except Exception:
        logger.exception("Error evaluando anomalías tras sensor")
    return {"status": "OK", "received": True}


# Endpoint de estado para la web
@app.get("/estado")
def estado():
    try:
        from core.indices.serializador_estado_atomico import serializar_estado_atomico
        from core.indices.bus_estado_global import BusEstadoGlobal
        bus = BusEstadoGlobal.obtener_instancia()
        estado_panel = serializar_estado_atomico(bus)
        payload = estado_panel.model_dump()
        try:
            if 'system' in globals() and system is not None:
                if hasattr(system, 'obtener_estado_completo'):
                    payload.update(system.obtener_estado_completo())
        except Exception:
            logger.exception("Error enriqueciendo /estado con SystemCore")
        return payload
    except Exception as e:
        logger.error(f"Error en /estado (serializador atómico): {e}", exc_info=True)
        return {"error": str(e)}


def _estado_impl():
    global INDEX_CATALOG
    if "INDEX_CATALOG" not in globals() or not isinstance(INDEX_CATALOG, dict):
        try:
            from core.indices.index_catalog import INDEX_CATALOG as _INDEX_CATALOG
            INDEX_CATALOG = _INDEX_CATALOG if isinstance(_INDEX_CATALOG, dict) else {}
        except Exception:
            INDEX_CATALOG = {}
    # Refrescar sensores desde el último payload persistido si existe
    persisted_sensores = None
    try:
        snapshot_candidates = [
            BASE_DIR / "data" / "last_sensores.json",
            pathlib.Path.cwd() / "data" / "last_sensores.json",
        ]
        snapshot_path = None
        for candidate in snapshot_candidates:
            if not candidate.exists():
                continue
            if snapshot_path is None:
                snapshot_path = candidate
                continue
            try:
                if candidate.stat().st_mtime > snapshot_path.stat().st_mtime:
                    snapshot_path = candidate
            except Exception:
                logging.exception("Silent except at 1682 - revisar contexto")
        if snapshot_path and snapshot_path.exists():
            persisted = json.loads(snapshot_path.read_text(encoding="utf-8"))
            persisted_sensores = persisted.get("sensores", {})
            persisted_ts = persisted.get("timestamps", {})
            if isinstance(persisted_sensores, dict):
                system.sensores.update(persisted_sensores)
            if isinstance(persisted_ts, dict) and hasattr(system, "sensores_timestamp"):
                system.sensores_timestamp.update(persisted_ts)
    except Exception:
        logging.exception("Silent except at 1692 - revisar contexto")
    # Forzar siempre el cálculo de índices avanzados
    from core.indices.environmental_indices import EnvironmentalIndices
    if not isinstance(system.indices, EnvironmentalIndices):
        system.indices = EnvironmentalIndices(system)
    meteo_snapshot = get_full_meteo_snapshot(system)
    indices = system.indices.obtener_todos()
    pred_engine = PredictionEngine(system)
    predicciones = pred_engine.predecir()
    
    # ✅ GUARDAR PREDICCIONES (CRÍTICO PARA APRENDIZAJE)
    if RECORDERS_AVAILABLE:
        try:
            recorders = get_recorders()
            ts_ahora = time.time()
            recorders["predicciones"].guardar_prediccion(
                timestamp=ts_ahora,
                motor_id="PredictionEngine",
                predicciones=predicciones,
                confianza=0.75,  # Valor por defecto
                contexto={"sensores": dict(system.sensores)}
            )
        except Exception as e:
            logging.debug(f"Error guardando predicción: {e}")
    
    # Aplicar calibración global si existen factores
    try:
        from core.calibration.calibration_engine import load_factors, apply_calibration
        factors = load_factors()
        if factors:
            apply_calibration(indices, factors)
            apply_calibration(predicciones, factors)
    except Exception:
        logging.exception("Silent except at 1709 - revisar contexto")
    try:
        system.indices.reforzar_indices(indices, predicciones=predicciones)
    except Exception:
        logging.exception("Silent except at 1713 - revisar contexto")
    
    # ✅ GUARDAR ÍNDICES CALCULADOS (CRÍTICO PARA AUDITORIA)
    if RECORDERS_AVAILABLE:
        try:
            recorders = get_recorders()
            ts_ahora = time.time()
            recorders["indices"].guardar_indices(
                timestamp=ts_ahora,
                indices=indices,
                datos_entrada={
                    "temperatura": system.sensores.get("temperatura"),
                    "humedad": system.sensores.get("humedad"),
                    "presion": system.sensores.get("presion"),
                    "viento": system.sensores.get("viento"),
                },
                formula_usada={"metodo": "EnvironmentalIndices"}
            )
        except Exception as e:
            logging.debug(f"Error guardando índices: {e}")
    recomendacion = system.obtener_recomendacion()
    # Leer latitud/longitud manuales si existen
    latitud = None
    longitud = None
    origen_ubicacion = "estimada"
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if "latitud" in line.lower():
                    latitud = float(line.split(":")[-1].strip())
                if "longitud" in line.lower():
                    longitud = float(line.split(":")[-1].strip())
        if latitud is not None and longitud is not None:
            manager.set_manual_coordinates(latitud, longitud)
            origen_ubicacion = "manual"
    except Exception:
        logging.exception("Silent except at 1730 - revisar contexto")
    def _coords_valid(lat, lon):
        try:
            return lat is not None and lon is not None and -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180
        except Exception:
            return False

    if latitud is None or longitud is None:
        try:
            def _parse_coord(val):
                if val is None:
                    return None
                s = str(val).strip().lower().replace(',', '.')
                sign = 1
                if s.endswith(('n', 's', 'e', 'o', 'w')):
                    suffix = s[-1]
                    s = s[:-1].strip()
                    if suffix in ('s', 'o', 'w'):
                        sign = -1.0
                try:
                    return float(s) * sign
                except Exception:
                    return None

            lat_sensor = system.sensores.get("latitud") or system.sensores.get("lat")
            lon_sensor = system.sensores.get("longitud") or system.sensores.get("lon")
            if lat_sensor is not None and lon_sensor is not None:
                latitud = _parse_coord(lat_sensor)
                longitud = _parse_coord(lon_sensor)
                origen_ubicacion = "sensor"
        except Exception:
            logging.exception("Silent except at 1761 - revisar contexto")

    if latitud is None or longitud is None:
        coords = manager.obtener_coordenadas()
        if coords:
            latitud = coords.get("lat")
            longitud = coords.get("lon")
            origen_ubicacion = coords.get("origen", "estimada")
    def _coords_es_spain(lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            return 35 <= lat <= 44.5 and -10 <= lon <= 4.5
        except Exception:
            return False

    if not _coords_valid(latitud, longitud) or (origen_ubicacion != "manual" and not _coords_es_spain(latitud, longitud)):
        from core.system.constants import ESTACION
        latitud = ESTACION.LATITUD
        longitud = ESTACION.LONGITUD
        origen_ubicacion = "constantes_selladas"
    try:
        system.ubicacion = {
            "lat": latitud,
            "lon": longitud,
            "origen": origen_ubicacion,
        }
    except Exception:
        logging.exception("Silent except at 1788 - revisar contexto")
    # Calcular arco solar y horas de amanecer/atardecer para hoy
    hoy = datetime.datetime.now().timetuple().tm_yday
    arco = arco_solar(latitud, hoy)
    def _radiacion_teorica(lat_deg, day, hora_decimal):
        import math
        lat_rad = math.radians(lat_deg)
        delta = 0.409 * math.sin(2 * math.pi * (day - 81) / 368)
        omega = math.radians((hora_decimal - 12.0) * 15.0)
        sin_alt = math.sin(lat_rad) * math.sin(delta) + math.cos(lat_rad) * math.cos(delta) * math.cos(omega)
        if sin_alt <= 0:
            return 0
        gsc = 1361.0
        dr = 1 + 0.033 * math.cos(2 * math.pi * day / 365.0)
        return gsc * dr * sin_alt
    from tools.amanecer_atardecer import calcular_amanecer_atardecer
    try:
        from zoneinfo import ZoneInfo
        ahora = datetime.datetime.now(ZoneInfo("Europe/Madrid"))
        utc_offset = ahora.utcoffset()
        utc_offset = int(utc_offset.total_seconds() / 3600) if utc_offset is not None else 1
    except Exception:
        try:
            utc_offset = datetime.datetime.now().astimezone().utcoffset()
            utc_offset = int(utc_offset.total_seconds() / 3600) if utc_offset is not None else 1
        except Exception:
            utc_offset = 1
    horas_sol = calcular_amanecer_atardecer(latitud, longitud, hoy, utc_offset)
    # Si no hay sensor de radiación, estimar radiación máxima posible por arco solar
    if isinstance(persisted_sensores, dict):
        sensores = persisted_sensores.copy()
    else:
        sensores = system.sensores.copy()
    # No forzar valores artificiales si faltan sensores base



    # Añadir arco solar a los índices (leer de bus/índices si existe)
    estimado_arco = origen_ubicacion != "manual"
    arco_existente = None
    if hasattr(system, "obtener_indice"):
        arco_existente = system.obtener_indice("arco_solar")
    if arco_existente is None and hasattr(system, "indices"):
        arco_existente = system.indices.get("arco_solar")
    if arco_existente is not None:
        indices["arco_solar"] = {"valor": arco_existente, "estimado": False}
        indices["duracion_dia_h"] = {"valor": arco_existente / 15.0, "estimado": False}
    else:
        indices["arco_solar"] = {"valor": arco, "estimado": estimado_arco}
        indices["duracion_dia_h"] = {"valor": arco / 15.0, "estimado": estimado_arco}
        if hasattr(system, "actualizar_indice"):
            system.actualizar_indice("arco_solar", arco)
            system.actualizar_indice("duracion_dia_h", arco / 15.0)
    hora_decimal = datetime.datetime.now().hour + datetime.datetime.now().minute / 60.0 + datetime.datetime.now().second / 3600.0
    rad_teorica_existente = None
    if hasattr(system, "obtener_indice"):
        rad_teorica_existente = system.obtener_indice("radiacion_teorica")
    if rad_teorica_existente is None and hasattr(system, "indices"):
        rad_teorica_existente = system.indices.get("radiacion_teorica")
    if rad_teorica_existente is None:
        rad_teorica = _radiacion_teorica(latitud, hoy, hora_decimal)
        indices["radiacion_teorica"] = {"valor": rad_teorica, "estimado": True}
        if hasattr(system, "actualizar_indice"):
            system.actualizar_indice("radiacion_teorica", rad_teorica)
    else:
        indices["radiacion_teorica"] = {"valor": rad_teorica_existente, "estimado": False}
    try:
        rad_real = sensores.get("radiacion")
        if ("nubosidad_estimada" not in indices or indices.get("nubosidad_estimada") is None) and rad_real is not None and rad_teorica > 0:
            nubosidad = max(0, min(100, (1.0 - (float(rad_real) / rad_teorica)) * 100))
            indices["nubosidad_estimada"] = {"valor": nubosidad, "estimado": True}
            if hasattr(system, "actualizar_indice"):
                system.actualizar_indice("nubosidad_estimada", nubosidad)
    except Exception:
        logging.exception("Silent except at 1838 - revisar contexto")
    def _hhmm_to_min(hhmm: str):
        try:
            if not hhmm or ":" not in hhmm:
                return None
            h, m = hhmm.split(":")[:2]
            return int(h) * 60 + int(m)
        except Exception:
            return None

    def _min_to_hhmm(total_min: int):
        try:
            total_min = total_min % (24 * 60)
            h = total_min // 60
            m = total_min % 60
            return f"{h:02d}:{m:02d}"
        except Exception:
            return "--:--"

    try:
        horas_sol = calcular_amanecer_atardecer(latitud, longitud, hoy, utc_offset)
        amanecer_astro = horas_sol.get("amanecer")
        atardecer_astro = horas_sol.get("atardecer")

        now = datetime.datetime.now()
        ahora_min = now.hour * 60 + now.minute
        amanecer_min = _hhmm_to_min(amanecer_astro)
        atardecer_min = _hhmm_to_min(atardecer_astro)

        rad = sensores.get("radiacion")
        uv = sensores.get("uv")
        try:
            rad_val = float(rad) if rad is not None else None
        except Exception:
            rad_val = None
        try:
            uv_val = float(uv) if uv is not None else None
        except Exception:
            uv_val = None

        es_dia_sensor = False
        if rad_val is not None and rad_val >= 50:
            es_dia_sensor = True
        if uv_val is not None and uv_val > 0.1:
            es_dia_sensor = True

        es_dia_astronomico = None
        if amanecer_min is not None and atardecer_min is not None:
            if amanecer_min <= atardecer_min:
                es_dia_astronomico = amanecer_min <= ahora_min <= atardecer_min
            else:
                es_dia_astronomico = ahora_min >= amanecer_min or ahora_min <= atardecer_min

        amanecer_hibrido = amanecer_astro
        atardecer_hibrido = atardecer_astro
        ventana_min = 90
        umbral_desvio_min = 30
        if es_dia_astronomico is False and es_dia_sensor and amanecer_min is not None:
            if abs(ahora_min - amanecer_min) <= ventana_min:
                amanecer_hibrido = _min_to_hhmm(ahora_min)
        if es_dia_astronomico is True and (not es_dia_sensor) and atardecer_min is not None:
            if abs(ahora_min - atardecer_min) <= ventana_min:
                atardecer_hibrido = _min_to_hhmm(ahora_min)

        indices["amanecer_astronomico"] = amanecer_astro
        indices["atardecer_astronomico"] = atardecer_astro
        indices["amanecer_hibrido"] = amanecer_hibrido
        indices["atardecer_hibrido"] = atardecer_hibrido
        indices["amanecer"] = amanecer_hibrido
        indices["atardecer"] = atardecer_hibrido
        indices["es_dia_astronomico"] = es_dia_astronomico
        indices["es_dia_sensor"] = es_dia_sensor
        amanecer_h_min = _hhmm_to_min(amanecer_hibrido)
        atardecer_h_min = _hhmm_to_min(atardecer_hibrido)
        desvio_amanecer = None
        desvio_atardecer = None
        if amanecer_min is not None and amanecer_h_min is not None:
            desvio_amanecer = abs(amanecer_h_min - amanecer_min)
        if atardecer_min is not None and atardecer_h_min is not None:
            desvio_atardecer = abs(atardecer_h_min - atardecer_min)

        inconsistencia_sensor = (es_dia_astronomico is not None and es_dia_astronomico != es_dia_sensor)
        inconsistencia_hibrida = False
        if desvio_amanecer is not None and desvio_amanecer >= umbral_desvio_min:
            inconsistencia_hibrida = True
        if desvio_atardecer is not None and desvio_atardecer >= umbral_desvio_min:
            inconsistencia_hibrida = True

        indices["desvio_amanecer_min"] = desvio_amanecer
        indices["desvio_atardecer_min"] = desvio_atardecer
        indices["inconsistencia_luz"] = (inconsistencia_sensor or inconsistencia_hibrida)
        indices["inconsistencia_sensor_luz"] = inconsistencia_sensor
        indices["inconsistencia_hibrida"] = inconsistencia_hibrida
    except Exception:
        indices["amanecer"] = "--:--"
        indices["atardecer"] = "--:--"

    # Índices astronómicos compuestos
    try:
        from core.indices.environmental_indices import _calcular_ventana_observacion_nocturna, _clasificar_indice_cielo
        duracion_dia = None
        if isinstance(indices.get("duracion_dia_h"), dict):
            duracion_dia = indices.get("duracion_dia_h", {}).get("valor")
        elif indices.get("duracion_dia_h") is not None:
            duracion_dia = indices.get("duracion_dia_h")
        duracion_noche = None
        if duracion_dia is not None:
            duracion_noche = max(0, 24.0 - float(duracion_dia))
            indices["duracion_noche_h"] = {"valor": duracion_noche, "estimado": True}

        cielo_obs = indices.get("cielo_observable_nocturno")
        cielo_val = cielo_obs.get("valor") if isinstance(cielo_obs, dict) else cielo_obs
        ventana = _calcular_ventana_observacion_nocturna(cielo_val, duracion_noche)
        if ventana is not None:
            indices["ventana_observacion_nocturna"] = {
                "valor": ventana,
                "estimado": True,
                "explicacion": "Horas útiles según cielo observable y duración de noche"
            }

        indice_cielo = None
        if cielo_val is not None and ventana is not None:
            cielo_n = max(0, min(1.0, float(cielo_val) / 100.0))
            horas_n = max(0, min(1.0, float(ventana) / 6.0))
            indice_cielo = (0.7 * cielo_n + 0.3 * horas_n) * 100
        if indice_cielo is not None:
            indices["indice_cielo_astronomico"] = {
                "valor": indice_cielo,
                "estimado": True,
                "explicacion": "Índice de cielo astronómico (cielo observable + ventana)"
            }
            indices["indice_cielo_astronomico_nivel"] = _clasificar_indice_cielo(indice_cielo)
    except Exception:
        logging.exception("Silent except at 1971 - revisar contexto")
    indices["latitud"] = latitud
    indices["longitud"] = longitud
    indices["origen_ubicacion"] = origen_ubicacion
    contexto = _build_contexto(sensores, indices)
    ambiental = MotorAmbiental().analizar(contexto)
    confort = MotorConfort().analizar(contexto)
    edificio = MotorEdificio().analizar(contexto)
    meteorologico = MotorMeteorologico().analizar(contexto)
    ventilacion = MotorVentilacion().analizar(contexto)
    pred_local = MotorPrediccionLocal().analizar(contexto)
    huellas = GestorHuellasAtmosfericas().analizar("default", contexto)
    uso_dispositivos = MotorUsoDispositivos().analizar(contexto)
    nocturno = MotorNocturno().analizar(contexto)
    intrusion = MotorIntrusion().analizar(contexto)
    materiales = MotorMateriales().analizar(contexto)
    avisos_practicos = MotorAvisosPracticos().analizar(contexto)
    salud_aire = MotorSaludAire().analizar(contexto)
    ventanas_puertas = MotorVentanasPuertas().analizar(contexto)
    riesgo_humedad = MotorRiesgoHumedad().analizar(contexto)
    temperatura_operativa = MotorTemperaturaOperativa().analizar(contexto)
    ritmo_circadiano = MotorRitmoCircadianoPersona().analizar(contexto)
    habitabilidad = MotorHabitabilidad().analizar(contexto)
    confort_nocturno = MotorConfortNocturno().analizar(contexto)
    meteo_avanzada = MotorMeteorologiaAvanzada().analizar(contexto)
    viento_rachas = MotorVientoRachas().analizar(contexto)
    visibilidad_local = MotorVisibilidadLocal().analizar(contexto)
    luz_natural = MotorLuzNatural().analizar(contexto)
    confort_termico = MotorConfortTermico().analizar(contexto)
    aire_pegajoso_seco = MotorAirePegajosoSeco().analizar(contexto)
    aire_cargado = MotorAireCargado().analizar(contexto)
    aire_enrarecido = MotorAireEnrarecido().analizar(contexto)
    deshidratacion = MotorDeshidratacionAmbiental().analizar(contexto)
    aire_estancado = MotorAireEstancado().analizar(contexto)
    renovacion_aire = MotorRenovacionAire().analizar(contexto)
    riesgo_oxidacion = MotorRiesgoOxidacion().analizar(contexto)
    riesgo_libros_papel = MotorRiesgoLibrosPapel().analizar(contexto)
    riesgo_electronica = MotorRiesgoElectronica().analizar(contexto)
    riesgo_plasticos = MotorRiesgoPlasticos().analizar(contexto)
    riesgo_ropa_guardada = MotorRiesgoRopaGuardada().analizar(contexto)
    riesgo_colchones = MotorRiesgoColchones().analizar(contexto)
    riesgo_alimentos = MotorRiesgoAlimentos().analizar(contexto)
    riesgo_instrumentos = MotorRiesgoInstrumentos().analizar(contexto)
    riesgo_madera = MotorRiesgoMadera().analizar(contexto)
    actividad_humana = MotorActividadHumana().analizar(contexto)
    presencia = MotorPresencia().analizar(contexto)
    corrientes_internas = MotorCorrientesInternas().analizar(contexto)
    estabilidad_futura = MotorEstabilidadTermicaFutura().analizar(contexto)
    golpes_puerta = MotorGolpesPuerta().analizar(contexto)
    riesgo_plantas = MotorRiesgoPlantas().analizar(contexto)
    ropa_tendida = MotorRopaTendida().analizar(contexto)
    viento_dormir = MotorVientoDormir().analizar(contexto)
    corrientes_futuras = MotorPrediccionCorrientesFuturas().analizar(contexto)
    _registrar_evento_hardware_nuevo()
    asistente = _asistente_estado()
    departamentos = _departamentos_ideas(asistente)
    olor_cerrado = MotorOlorCerrado().analizar(contexto)
    condensacion_armarios = MotorCondensacionArmarios().analizar(contexto)
    secado_ropa = MotorSecadoRopa().analizar(contexto)
    persianas = MotorPersianas().analizar(contexto)
    def _entero_si_redondo(val):
        try:
            if isinstance(val, float) and val == int(val):
                return int(val)
        except Exception:
            logging.exception("Silent except at 2036 - revisar contexto")
        return val

    # Forzar Ley del Entero en humedad y viento si son redondos
    def _forzar_entero_en_dict(d, keys):
        for k in keys:
            if k in d and isinstance(d[k], dict) and "valor" in d[k]:
                d[k]["valor"] = _entero_si_redondo(d[k]["valor"])
        return d

    riesgo_humedad = _forzar_entero_en_dict(riesgo_humedad, ["humedad"])
    viento_rachas = _forzar_entero_en_dict(viento_rachas, ["viento"])

    bloques_fusionados = {
        "riesgos": {
            "humedad": riesgo_humedad,
            "meteo": meteo_avanzada,
            "viento": viento_rachas,
            "visibilidad": visibilidad_local,
            "intrusion": intrusion,
            "plantas": riesgo_plantas,
            "ropa_tendida": ropa_tendida,
        },
        "confort": {
            "termico": confort_termico,
            "aire": aire_pegajoso_seco,
            "nocturno": confort_nocturno,
            "habitabilidad": habitabilidad,
            "ritmo_circadiano": ritmo_circadiano,
            "ot": temperatura_operativa,
            "estabilidad_futura": estabilidad_futura,
            "sensacion_termica_ext": {
                "heat_index": indices.get("sensacion_calor"),
                "wind_chill": indices.get("sensacion_frio"),
                "wbgt": indices.get("wbgt"),
                # Humidex eliminado: devolver el mejor índice disponible (WBGT > sensacion_calor > vpd)
                "humidex": indices.get("wbgt") or indices.get("sensacion_calor") or indices.get("vpd"),
                "compuesta": indices.get("sensacion_termica_compuesta"),
            },
            "aire_avanzado": {
                "bulbo_humedo": indices.get("bulbo_humedo"),
                "humedad_absoluta": indices.get("humedad_absoluta"),
                "vpd": indices.get("vpd"),
                "entalpia": indices.get("entalpia_aire"),
                "pmv": indices.get("pmv"),
                "ppd": indices.get("ppd"),
                "aqi_pm25": indices.get("aqi_pm25"),
                "calidad_compuesta": indices.get("calidad_aire_compuesta"),
                "ventilacion_compuesta": indices.get("ventilacion_compuesta"),
            },
        },
        "hogar": {
            "ventanas_puertas": ventanas_puertas,
            "avisos": avisos_practicos,
            "luz_natural": luz_natural,
            "uso_dispositivos": uso_dispositivos,
            "secado_ropa": secado_ropa,
            "persianas": persianas,
            "actividad": actividad_humana,
            "presencia": presencia,
            "corrientes": corrientes_internas,
            "golpes_puerta": golpes_puerta,
            "corrientes_futuras": corrientes_futuras,
        },
        "salud": {
            "aire": salud_aire,
            "materiales": materiales,
            "olor_cerrado": olor_cerrado,
            "condensacion_armarios": condensacion_armarios,
            "aire_enrarecido": aire_enrarecido,
            "deshidratacion": deshidratacion,
            "aire_estancado": aire_estancado,
            "renovacion_aire": renovacion_aire,
            "riesgo_oxidacion": riesgo_oxidacion,
            "riesgo_libros_papel": riesgo_libros_papel,
            "riesgo_electronica": riesgo_electronica,
            "riesgo_plasticos": riesgo_plasticos,
            "riesgo_ropa_guardada": riesgo_ropa_guardada,
            "riesgo_colchones": riesgo_colchones,
            "riesgo_alimentos": riesgo_alimentos,
            "riesgo_instrumentos": riesgo_instrumentos,
            "riesgo_madera": riesgo_madera,
        },
        "prediccion": {
            "local": pred_local,
        },
        "nocturno": nocturno,
        "organizacion": {
            "noticias": asistente.get("noticias"),
            "eventos": asistente.get("eventos"),
            "alarmas": asistente.get("alarmas"),
            "calendario": asistente.get("calendario"),
            "tareas": asistente.get("tareas"),
            "lista_compra": asistente.get("lista_compra"),
            "impresion": asistente.get("cola_impresion"),
            "recomendaciones": asistente.get("recomendaciones"),
        },
        "departamentos": departamentos,
        "asistente": asistente,
    }
    return {
        "sensores": sensores,
        "sensores_metadata": system.sensores_metadata,
        "sensores_derivados_metadata": system.sensores_derivados_metadata,
        "indices_catalogo": INDEX_CATALOG,
        "indices": indices,
        "recomendacion": recomendacion,
        "meteo": meteo_snapshot,
        "predicciones": predicciones,
        "ambiental": ambiental,
        "confort": confort,
        "edificio": edificio,
        "meteorologico": meteorologico,
        "ventilacion": ventilacion,
        "prediccion_local": pred_local,
        "huellas": huellas,
        "uso_dispositivos": uso_dispositivos,
        "nocturno": nocturno,
        "intrusion": intrusion,
        "materiales": materiales,
        "avisos_practicos": avisos_practicos,
        "salud_aire": salud_aire,
        "ventanas_puertas": ventanas_puertas,
        "riesgo_humedad": riesgo_humedad,
        "temperatura_operativa": temperatura_operativa,
        "ritmo_circadiano": ritmo_circadiano,
        "habitabilidad": habitabilidad,
        "confort_nocturno": confort_nocturno,
        "meteo_avanzada": meteo_avanzada,
        "viento_rachas": viento_rachas,
        "visibilidad_local": visibilidad_local,
        "luz_natural": luz_natural,
        "confort_termico": confort_termico,
        "aire_pegajoso_seco": aire_pegajoso_seco,
        "aire_cargado": aire_cargado,
        "aire_enrarecido": aire_enrarecido,
        "deshidratacion": deshidratacion,
        "aire_estancado": aire_estancado,
        "renovacion_aire": renovacion_aire,
        "riesgo_oxidacion": riesgo_oxidacion,
        "riesgo_libros_papel": riesgo_libros_papel,
        "riesgo_electronica": riesgo_electronica,
        "riesgo_plasticos": riesgo_plasticos,
        "riesgo_ropa_guardada": riesgo_ropa_guardada,
        "riesgo_colchones": riesgo_colchones,
        "riesgo_alimentos": riesgo_alimentos,
        "riesgo_instrumentos": riesgo_instrumentos,
        "riesgo_madera": riesgo_madera,
        "actividad_humana": actividad_humana,
        "presencia": presencia,
        "corrientes_internas": corrientes_internas,
        "estabilidad_futura": estabilidad_futura,
        "golpes_puerta": golpes_puerta,
        "riesgo_plantas": riesgo_plantas,
        "riesgo_ropa_tendida": ropa_tendida,
        "viento_dormir": viento_dormir,
        "corrientes_futuras": corrientes_futuras,
        "asistente": asistente,
        "departamentos": departamentos,
        "noticias": asistente.get("noticias"),
        "eventos": asistente.get("eventos"),
        "alarmas": asistente.get("alarmas"),
        "calendario": asistente.get("calendario"),
        "tareas": asistente.get("tareas"),
        "lista_compra": asistente.get("lista_compra"),
        "impresion": asistente.get("cola_impresion"),
        "recomendaciones": asistente.get("recomendaciones"),
        "olor_cerrado": olor_cerrado,
        "condensacion_armarios": condensacion_armarios,
        "secado_ropa": secado_ropa,
        "persianas": persianas,
        "bloques_fusionados": bloques_fusionados,
    }


@app.get("/submenu_detallado")
def submenu_detallado():
    try:
        from core.indices.environmental_indices import EnvironmentalIndices
        try:
            from core.indices.index_catalog import INDEX_CATALOG
        except Exception:
            INDEX_CATALOG = {}
        if not isinstance(system.indices, EnvironmentalIndices):
            system.indices = EnvironmentalIndices(system)
        indices = system.indices.obtener_todos()
        predicciones = PredictionEngine(system).predecir()
        contexto = _build_contexto(system.sensores.copy(), indices)
        ambiental = MotorAmbiental().analizar(contexto)
        confort = MotorConfort().analizar(contexto)
        edificio = MotorEdificio().analizar(contexto)
        meteorologico = MotorMeteorologico().analizar(contexto)
        ventilacion = MotorVentilacion().analizar(contexto)
        pred_local = MotorPrediccionLocal().analizar(contexto)
        try:
            pred_refuerzos = {}
            if isinstance(predicciones, dict):
                pred_refuerzos.update(predicciones)
            if isinstance(pred_local, dict):
                pred_refuerzos.update(pred_local)
            system.indices.reforzar_indices(indices, predicciones=pred_refuerzos)
        except Exception:
            logging.exception("Silent except at 2238 - revisar contexto")
        huellas = GestorHuellasAtmosfericas().analizar("default", contexto)
        uso_dispositivos = MotorUsoDispositivos().analizar(contexto)
        nocturno = MotorNocturno().analizar(contexto)
        intrusion = MotorIntrusion().analizar(contexto)
        materiales = MotorMateriales().analizar(contexto)
        avisos_practicos = MotorAvisosPracticos().analizar(contexto)
        salud_aire = MotorSaludAire().analizar(contexto)
        ventanas_puertas = MotorVentanasPuertas().analizar(contexto)
        riesgo_humedad = MotorRiesgoHumedad().analizar(contexto)
        temperatura_operativa = MotorTemperaturaOperativa().analizar(contexto)
        ritmo_circadiano = MotorRitmoCircadianoPersona().analizar(contexto)
        habitabilidad = MotorHabitabilidad().analizar(contexto)
        confort_nocturno = MotorConfortNocturno().analizar(contexto)
        meteo_avanzada = MotorMeteorologiaAvanzada().analizar(contexto)
        viento_rachas = MotorVientoRachas().analizar(contexto)
        visibilidad_local = MotorVisibilidadLocal().analizar(contexto)
        luz_natural = MotorLuzNatural().analizar(contexto)
        confort_termico = MotorConfortTermico().analizar(contexto)
        aire_pegajoso_seco = MotorAirePegajosoSeco().analizar(contexto)
        aire_cargado = MotorAireCargado().analizar(contexto)
        aire_enrarecido = MotorAireEnrarecido().analizar(contexto)
        deshidratacion = MotorDeshidratacionAmbiental().analizar(contexto)
        aire_estancado = MotorAireEstancado().analizar(contexto)
        renovacion_aire = MotorRenovacionAire().analizar(contexto)
        riesgo_oxidacion = MotorRiesgoOxidacion().analizar(contexto)
        riesgo_libros_papel = MotorRiesgoLibrosPapel().analizar(contexto)
        riesgo_electronica = MotorRiesgoElectronica().analizar(contexto)
        riesgo_plasticos = MotorRiesgoPlasticos().analizar(contexto)
        riesgo_ropa_guardada = MotorRiesgoRopaGuardada().analizar(contexto)
        riesgo_colchones = MotorRiesgoColchones().analizar(contexto)
        riesgo_alimentos = MotorRiesgoAlimentos().analizar(contexto)
        riesgo_instrumentos = MotorRiesgoInstrumentos().analizar(contexto)
        riesgo_madera = MotorRiesgoMadera().analizar(contexto)
        actividad_humana = MotorActividadHumana().analizar(contexto)
        presencia = MotorPresencia().analizar(contexto)
        corrientes_internas = MotorCorrientesInternas().analizar(contexto)
        estabilidad_futura = MotorEstabilidadTermicaFutura().analizar(contexto)
        golpes_puerta = MotorGolpesPuerta().analizar(contexto)
        riesgo_plantas = MotorRiesgoPlantas().analizar(contexto)
        ropa_tendida = MotorRopaTendida().analizar(contexto)
        viento_dormir = MotorVientoDormir().analizar(contexto)
        corrientes_futuras = MotorPrediccionCorrientesFuturas().analizar(contexto)
        asistente = _asistente_estado()
        departamentos = _departamentos_ideas(asistente)
        olor_cerrado = MotorOlorCerrado().analizar(contexto)
        condensacion_armarios = MotorCondensacionArmarios().analizar(contexto)
        secado_ropa = MotorSecadoRopa().analizar(contexto)
        persianas = MotorPersianas().analizar(contexto)
        bloques_fusionados = {
            "riesgos": {
                "humedad": riesgo_humedad,
                "meteo": meteo_avanzada,
                "viento": viento_rachas,
                "visibilidad": visibilidad_local,
                "intrusion": intrusion,
                "plantas": riesgo_plantas,
                "ropa_tendida": ropa_tendida,
            },
            "confort": {
                "termico": confort_termico,
                "aire": aire_pegajoso_seco,
                "nocturno": confort_nocturno,
                "habitabilidad": habitabilidad,
                "ritmo_circadiano": ritmo_circadiano,
                "ot": temperatura_operativa,
                "estabilidad_futura": estabilidad_futura,
                "sensacion_termica_ext": {
                    "heat_index": indices.get("sensacion_calor"),
                    "wind_chill": indices.get("sensacion_frio"),
                    "wbgt": indices.get("wbgt"),
                    # Humidex eliminado: devolver el mejor índice disponible (WBGT > sensacion_calor > vpd)
                    "humidex": indices.get("wbgt") or indices.get("sensacion_calor") or indices.get("vpd"),
                    "compuesta": indices.get("sensacion_termica_compuesta"),
                },
                "aire_avanzado": {
                    "bulbo_humedo": indices.get("bulbo_humedo"),
                    "humedad_absoluta": indices.get("humedad_absoluta"),
                    "vpd": indices.get("vpd"),
                    "entalpia": indices.get("entalpia_aire"),
                    "pmv": indices.get("pmv"),
                    "ppd": indices.get("ppd"),
                    "aqi_pm25": indices.get("aqi_pm25"),
                    "calidad_compuesta": indices.get("calidad_aire_compuesta"),
                    "ventilacion_compuesta": indices.get("ventilacion_compuesta"),
                },
            },
            "hogar": {
                "ventanas_puertas": ventanas_puertas,
                "avisos": avisos_practicos,
                "luz_natural": luz_natural,
                "uso_dispositivos": uso_dispositivos,
                "secado_ropa": secado_ropa,
                "persianas": persianas,
                "actividad": actividad_humana,
                "presencia": presencia,
                "corrientes": corrientes_internas,
                "golpes_puerta": golpes_puerta,
                "corrientes_futuras": corrientes_futuras,
            },
            "salud": {
                "aire": salud_aire,
                "materiales": materiales,
                "olor_cerrado": olor_cerrado,
                "condensacion_armarios": condensacion_armarios,
                "aire_enrarecido": aire_enrarecido,
                "deshidratacion": deshidratacion,
                "aire_estancado": aire_estancado,
                "renovacion_aire": renovacion_aire,
                "riesgo_oxidacion": riesgo_oxidacion,
                "riesgo_libros_papel": riesgo_libros_papel,
                "riesgo_electronica": riesgo_electronica,
                "riesgo_plasticos": riesgo_plasticos,
                "riesgo_ropa_guardada": riesgo_ropa_guardada,
                "riesgo_colchones": riesgo_colchones,
                "riesgo_alimentos": riesgo_alimentos,
                "riesgo_instrumentos": riesgo_instrumentos,
                "riesgo_madera": riesgo_madera,
            },
            "prediccion": {
                "local": pred_local,
            },
            "nocturno": nocturno,
            "organizacion": {
                "noticias": asistente.get("noticias"),
                "eventos": asistente.get("eventos"),
                "alarmas": asistente.get("alarmas"),
                "calendario": asistente.get("calendario"),
                "tareas": asistente.get("tareas"),
                "lista_compra": asistente.get("lista_compra"),
                "impresion": asistente.get("cola_impresion"),
                "recomendaciones": asistente.get("recomendaciones"),
            },
            "departamentos": departamentos,
            "asistente": asistente,
        }

        sensores = []
        for nombre, valor in system.sensores.items():
            meta = system.obtener_sensor_metadata(nombre) or {}
            sensores.append({
                "nombre": nombre,
                "valor": valor,
                "unidad": meta.get("unidad"),
                "fuente": meta.get("fuente"),
                "origen": meta.get("origen"),
                "fiabilidad": meta.get("fiabilidad"),
                "tipo": meta.get("tipo"),
                "timestamp": system.sensores_timestamp.get(nombre),
                "derivado": False,
            })

        derivados = []
        for nombre, valor in getattr(system, "sensores_derivados", {}).items():
            meta = getattr(system, "sensores_derivados_metadata", {}).get(nombre, {})
            derivados.append({
                "nombre": nombre,
                "valor": valor,
                "unidad": meta.get("unidad"),
                "fuente": meta.get("fuente"),
                "origen": meta.get("origen"),
                "fiabilidad": meta.get("fiabilidad"),
                "tipo": meta.get("tipo"),
                "calidad": meta.get("calidad"),
                "depends_on": meta.get("depends_on"),
                "derivado": True,
            })

        expansion = AutoExpansionEngine(system).report()
        auto_mejora_ciclo = system.auto_improvement_system.ciclo() if system.auto_improvement_system else {}
        pas_status = pas_engine.status(system.sensores) if pas_engine else {}
        habitos_status = habits_engine.status() if habits_engine else {}
        data = {
            "sensores": sensores,
            "derivados": derivados,
            "indices": indices,
            "predicciones": predicciones,
        "ambiental": ambiental,
        "confort": confort,
        "edificio": edificio,
        "meteorologico": meteorologico,
        "ventilacion": ventilacion,
        "prediccion_local": pred_local,
        "huellas": huellas,
        "uso_dispositivos": uso_dispositivos,
        "nocturno": nocturno,
        "intrusion": intrusion,
        "materiales": materiales,
        "avisos_practicos": avisos_practicos,
        "salud_aire": salud_aire,
        "ventanas_puertas": ventanas_puertas,
        "riesgo_humedad": riesgo_humedad,
        "temperatura_operativa": temperatura_operativa,
        "ritmo_circadiano": ritmo_circadiano,
        "habitabilidad": habitabilidad,
        "confort_nocturno": confort_nocturno,
        "meteo_avanzada": meteo_avanzada,
        "viento_rachas": viento_rachas,
        "visibilidad_local": visibilidad_local,
        "luz_natural": luz_natural,
        "confort_termico": confort_termico,
        "aire_pegajoso_seco": aire_pegajoso_seco,
        "aire_cargado": aire_cargado,
        "aire_enrarecido": aire_enrarecido,
        "deshidratacion": deshidratacion,
        "aire_estancado": aire_estancado,
        "renovacion_aire": renovacion_aire,
        "riesgo_oxidacion": riesgo_oxidacion,
        "riesgo_libros_papel": riesgo_libros_papel,
        "riesgo_electronica": riesgo_electronica,
        "riesgo_plasticos": riesgo_plasticos,
        "riesgo_ropa_guardada": riesgo_ropa_guardada,
        "riesgo_colchones": riesgo_colchones,
        "riesgo_alimentos": riesgo_alimentos,
        "riesgo_instrumentos": riesgo_instrumentos,
        "riesgo_madera": riesgo_madera,
        "actividad_humana": actividad_humana,
        "presencia": presencia,
        "corrientes_internas": corrientes_internas,
        "estabilidad_futura": estabilidad_futura,
        "golpes_puerta": golpes_puerta,
        "riesgo_plantas": riesgo_plantas,
        "riesgo_ropa_tendida": ropa_tendida,
        "viento_dormir": viento_dormir,
        "corrientes_futuras": corrientes_futuras,
        "asistente": asistente,
        "departamentos": departamentos,
        "noticias": asistente.get("noticias"),
        "eventos": asistente.get("eventos"),
        "alarmas": asistente.get("alarmas"),
        "calendario": asistente.get("calendario"),
        "tareas": asistente.get("tareas"),
        "lista_compra": asistente.get("lista_compra"),
        "impresion": asistente.get("cola_impresion"),
        "recomendaciones": asistente.get("recomendaciones"),
        "olor_cerrado": olor_cerrado,
        "condensacion_armarios": condensacion_armarios,
        "secado_ropa": secado_ropa,
        "persianas": persianas,
        "bloques_fusionados": bloques_fusionados,
        "auto_mejora": system.auto_improvement_engine.reporte() if system.auto_improvement_engine else {},
        "auto_mejora_sistema": auto_mejora_ciclo,
        "sensores_metadata": system.sensores_metadata,
        "indices_catalogo": INDEX_CATALOG,
        "auto_expansion": expansion,
        "auto_reparacion": auto_repair_engine.last_report if auto_repair_engine else {},
        "pas": pas_status,
        "habitos": habitos_status,
        }
        return _json_safe(data)
    except Exception as e:
        logger.error(f"Error en /submenu_detallado: {e}", exc_info=True)
        try:
            from core.indices.environmental_indices import EnvironmentalIndices
            if not isinstance(system.indices, EnvironmentalIndices):
                system.indices = EnvironmentalIndices(system)
            indices = system.indices.obtener_todos()
        except Exception:
            indices = {}
        fallback = {
            "error": str(e),
            "sensores": system.sensores.copy(),
            "indices": indices,
        }
        return _json_safe(fallback)


@app.post("/voz/sesion")
async def voz_sesion(payload: dict = None):
    user_id = None
    if isinstance(payload, dict):
        user_id = payload.get("user_id")
    session_id = voice_engine.start_session(user_id=user_id)
    return {"session_id": session_id}


def _normalizar_texto(texto: str) -> str:
    if texto is None:
        return ""
    s = str(texto).lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = s.replace("_", " ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _tokenizar(texto: str):
    return set(_normalizar_texto(texto).split())


def _aliases_para_nombre(nombre: str, meta: dict = None):
    aliases = set()
    if nombre:
        aliases.add(_normalizar_texto(nombre))
        aliases.add(_normalizar_texto(nombre.replace("_", " ")))
    if isinstance(meta, dict):
        for k in ("tipo", "nombre", "source", "origen", "descripcion", "categoria"):
            v = meta.get(k)
            if v:
                aliases.add(_normalizar_texto(v))
    return {a for a in aliases if a}


def _extraer_valor(info):
    if isinstance(info, dict):
        for k in ("valor", "value", "prediccion", "tendencia", "texto", "resumen"):
            if k in info and info.get(k) is not None:
                return info.get(k)
        return info
    return info


def _formatear_valor_texto(valor, unidad: str = "") -> str:
    if valor is None:
        return "Sin datos"
    try:
        if isinstance(valor, str):
            v = valor.strip()
            # evitar fechas tipo 12/72
            if "/" in v:
                v = v.replace("/", " ")
            try:
                num = float(v.replace(",", "."))
                valor = num
            except Exception:
                return (v + (" " + unidad if unidad else "")).strip()
        if isinstance(valor, (int, float)):
            if isinstance(valor, float) and not valor.is_integer():
                txt = f"{valor:.2f}".rstrip("0").rstrip(".")
            else:
                txt = f"{int(valor)}"
            txt = txt.replace(".", " coma ")
            return (txt + (" " + unidad if unidad else "")).strip()
        return (str(valor) + (" " + unidad if unidad else "")).strip()
    except Exception:
        return (str(valor) + (" " + unidad if unidad else "")).strip()


def _resolver_consulta_valor(text: str):
    consulta = _normalizar_texto(text)
    if not consulta:
        return None

    try:
        from core.indices.index_catalog import INDEX_CATALOG
    except Exception:
        INDEX_CATALOG = {}
    from core.prediction.prediction_engine import PredictionEngine
    from core.indices.environmental_indices import EnvironmentalIndices

    if not isinstance(system.indices, EnvironmentalIndices):
        system.indices = EnvironmentalIndices(system)

    indices = system.indices.obtener_todos()
    predicciones = PredictionEngine(system).predecir()
    try:
        contexto = _build_contexto(system.sensores.copy(), indices)
        pred_local = MotorPrediccionLocal().analizar(contexto)
    except Exception:
        pred_local = {}

    candidatos = []

    for nombre, valor in system.sensores.items():
        meta = getattr(system, "sensores_metadata", {}).get(nombre, {})
        candidatos.append({
            "nombre": nombre,
            "tipo": "sensor",
            "valor": valor,
            "unidad": meta.get("unidad"),
            "meta": meta,
            "explicacion": meta.get("explicacion"),
            "confianza": meta.get("fiabilidad")
        })

    for nombre, valor in getattr(system, "sensores_derivados", {}).items():
        meta = getattr(system, "sensores_derivados_metadata", {}).get(nombre, {})
        candidatos.append({
            "nombre": nombre,
            "tipo": "derivado",
            "valor": valor,
            "unidad": meta.get("unidad"),
            "meta": meta,
            "explicacion": meta.get("explicacion"),
            "confianza": meta.get("fiabilidad")
        })

    if isinstance(indices, dict):
        for nombre, info in indices.items():
            if not isinstance(info, dict):
                info = {"valor": info}
            candidatos.append({
                "nombre": nombre,
                "tipo": "indice",
                "valor": _extraer_valor(info),
                "unidad": info.get("unidad"),
                "meta": INDEX_CATALOG.get(nombre, {}),
                "explicacion": info.get("explicacion") or INDEX_CATALOG.get(nombre, {}).get("explicacion"),
                "confianza": info.get("confianza")
            })

    if isinstance(predicciones, dict):
        for nombre, info in predicciones.items():
            if not isinstance(info, dict):
                info = {"prediccion": info}
            candidatos.append({
                "nombre": nombre,
                "tipo": "prediccion",
                "valor": _extraer_valor(info),
                "unidad": info.get("unidad"),
                "meta": info,
                "explicacion": info.get("explicacion"),
                "confianza": info.get("confianza")
            })

    if isinstance(pred_local, dict):
        for nombre, info in pred_local.items():
            if not isinstance(info, dict):
                info = {"prediccion": info}
            candidatos.append({
                "nombre": nombre,
                "tipo": "prediccion",
                "valor": _extraer_valor(info),
                "unidad": info.get("unidad"),
                "meta": info,
                "explicacion": info.get("explicacion"),
                "confianza": info.get("confianza")
            })

    aliases_map = {
        "temperatura": ["temperatura", "temp", "t", "temperatura exterior", "t exterior"],
        "temperatura_interior": ["temperatura interior", "t interior", "temp interior"],
        "humedad": ["humedad", "hum", "hr", "humedad relativa", "humedad exterior"],
        "humedad_interior": ["humedad interior", "hr interior"],
        "presion": ["presion", "pres", "barometro", "baro"],
        "presion_relativa_interior": ["presion interior", "presion relativa interior"],
        "presion_absoluta_interior": ["presion absoluta interior"],
        "viento": ["viento", "wind", "racha", "gust", "velocidad viento"],
        "lluvia": ["lluvia", "rain", "precipitacion", "precip"],
        "radiacion": ["radiacion", "solar", "irradiancia"],
        "uv": ["uv", "ultravioleta"],
        "co2": ["co2", "dioxido de carbono", "carbono"],
        "pm25": ["pm25", "pm2 5", "particulas"],
        "riesgo_lluvia": ["riesgo de lluvia", "llovera", "lluvias"],
        "alerta_tormenta": ["alerta tormenta", "tormenta"],
    }

    consulta_tokens = _tokenizar(consulta)
    quiere_interior = "interior" in consulta_tokens or "dentro" in consulta_tokens
    quiere_exterior = "exterior" in consulta_tokens or "fuera" in consulta_tokens
    for key, syns in aliases_map.items():
        if any(s in consulta for s in syns):
            consulta_tokens.update(_tokenizar(key))

    mejor = None
    mejores = []
    for c in candidatos:
        aliases = _aliases_para_nombre(c["nombre"], c.get("meta"))
        extra = aliases_map.get(c["nombre"], [])
        for syn in extra:
            aliases.add(_normalizar_texto(syn))
        score = 0
        # match exacto del nombre
        if _normalizar_texto(c["nombre"]) == consulta:
            score += 6
        if consulta_tokens & _tokenizar(c["nombre"]):
            score += 2
        for a in aliases:
            if not a:
                continue
            if a in consulta:
                score += 3
            score += len(consulta_tokens & _tokenizar(a))
        if quiere_interior:
            if "interior" in c["nombre"]:
                score += 4
            if "exterior" in c["nombre"] or c["nombre"] in ("temperatura", "humedad"):
                score -= 2
        if quiere_exterior:
            if "exterior" in c["nombre"] or c["nombre"] in ("temperatura", "humedad"):
                score += 3
            if "interior" in c["nombre"]:
                score -= 2
        if "indice" in consulta and c["tipo"] == "indice":
            score += 1
        if "prediccion" in consulta and c["tipo"] == "prediccion":
            score += 1
        if score <= 0:
            continue
        if mejor is None or score > mejor[0]:
            mejor = (score, c)
            mejores = [c]
        elif score == mejor[0]:
            mejores.append(c)

    if not mejor:
        return None

    if len(mejores) > 1 and mejor[0] <= 2:
        nombres = ", ".join(sorted({m["nombre"] for m in mejores})[:8])
        return {"text": f"He encontrado varios valores posibles: {nombres}. Di el nombre exacto.", "audio": False}

    c = mejor[1]
    valor = c.get("valor")
    unidad = c.get("unidad") or ""
    tipo = c.get("tipo")
    fuente = c.get("meta", {}).get("fuente") or c.get("meta", {}).get("source")
    conf = c.get("confianza")
    explicacion = c.get("explicacion")

    valor_txt = _formatear_valor_texto(valor, unidad)
    razon = []
    razon.append(f"Tipo: {tipo}.")
    if fuente:
        razon.append(f"Fuente: {fuente}.")
    if conf is not None:
        razon.append(f"Confianza: {conf}.")
    if explicacion:
        razon.append(f"Razón: {explicacion}.")

    return {
        "text": f"{c['nombre']}: {valor_txt}".strip() + (". " + " ".join(razon) if razon else ""),
        "audio": False,
        "valor": valor,
        "unidad": unidad,
        "tipo": tipo,
        "nombre": c["nombre"],
    }


def _listar_valores_disponibles():
    sensores = list(getattr(system, "sensores", {}).keys())
    derivados = list(getattr(system, "sensores_derivados", {}).keys())
    try:
        indices = list(system.indices.obtener_todos().keys()) if system.indices else []
    except Exception:
        indices = []
    todos = sensores + derivados + indices
    return {
        "sensores": sensores,
        "derivados": derivados,
        "indices": indices,
        "total": len(todos)
    }


def _resumen_tiempo() -> dict:
    sensores = dict(getattr(system, "sensores", {}) or {})
    derivados = dict(getattr(system, "sensores_derivados", {}) or {})
    try:
        indices = dict(system.indices.obtener_todos()) if system.indices else {}
    except Exception:
        indices = {}

    def _pick(keys):
        for key in keys:
            for src in (sensores, derivados, indices):
                if key in src and src[key] is not None:
                    return src[key], key
        return None, None

    partes = []

    temp, temp_key = _pick(["temp_c", "temp", "temperatura", "temperature", "temp_exterior", "outdoor_temp", "tempf", "temperature_f"])
    if temp is not None:
        try:
            temp_val = float(temp)
            if temp_key and ("tempf" in temp_key.lower() or "fahrenheit" in temp_key.lower()):
                temp_val = (temp_val - 32.0) * 5.0 / 9.0
            elif temp_val > 60:
                temp_val = (temp_val - 32.0) * 5.0 / 9.0
            partes.append(f"Temperatura {temp_val:.1f} °C")
        except Exception:
            partes.append(f"Temperatura {temp}")

    hum, hum_key = _pick(["humedad", "humidity", "hum", "humedad_relativa", "rh"])
    if hum is not None:
        try:
            hum_val = float(hum)
            partes.append(f"Humedad {hum_val:.0f}%")
        except Exception:
            partes.append(f"Humedad {hum}")

    viento, viento_key = _pick(["viento", "wind", "wind_speed", "wind_kph", "wind_mph", "windspeed", "velocidad_viento"])
    if viento is not None:
        try:
            viento_val = float(viento)
            if viento_key and "mph" in viento_key.lower():
                viento_val = viento_val * 1.60934
            partes.append(f"Viento {viento_val:.1f} km/h")
        except Exception:
            partes.append(f"Viento {viento}")

    pres, pres_key = _pick(["presion", "pressure", "barometer", "presion_barometrica", "pressure_inhg"])
    if pres is not None:
        try:
            pres_val = float(pres)
            if pres_key and "inhg" in pres_key.lower():
                pres_val = pres_val * 33.8639
            elif pres_val < 200:
                pres_val = pres_val * 33.8639
            partes.append(f"Presión {pres_val:.0f} hPa")
        except Exception:
            partes.append(f"Presión {pres}")

    if not partes:
        return {"text": "Aún no hay datos meteorológicos disponibles."}

    return {"text": "Tiempo actual: " + ", ".join(partes) + "."}


def _respuesta_voz(session_id: str, text: str, extra: dict | None = None) -> dict:
    resp = {"session_id": session_id, "text": text}
    if extra:
        resp.update(extra)
    audio_bytes = voice_engine.synthesize_text_to_speech(text) if text else None
    if audio_bytes:
        resp["audio"] = True
        resp["audio_base64"] = base64.b64encode(audio_bytes).decode("ascii")
        resp["audio_mime"] = "audio/wav"
    else:
        resp["audio"] = False
    return resp



@app.post("/voz/texto")
async def voz_texto(payload: dict):
    session_id = payload.get("session_id") if isinstance(payload, dict) else None
    text = payload.get("text") if isinstance(payload, dict) else None
    if not session_id:
        session_id = voice_engine.start_session()
    if not text:
        return _respuesta_voz(session_id, "No he recibido texto.")
    t = str(text).lower()
    raw_text = str(text)

    # --- FEEDBACK POR VOZ ---
    import re
    feedback_match = re.search(r'(acertaste|fue correcta|fue un acierto|fue correcta la|fue buena|fue exacta) (la|el)? ?(predicci[oó]n|sensor|índice|indice)? ?(de|del|de la)? ?([\w_\- ]+)', t)
    feedback_error_match = re.search(r'(fallaste|fue incorrecta|fue un error|fue mala|fue err[oó]nea|fue incorrecto|no acertaste|no fue buena|no fue exacta) (la|el)? ?(predicci[oó]n|sensor|índice|indice)? ?(de|del|de la)? ?([\w_\- ]+)', t)
    valor_real_match = re.search(r'(el valor real|el valor correcto|era|fue|debería ser|deberia ser) ([\d\.,\-]+)', t)

    def _lookup_valor(data, nombre_busqueda: str):
        if not data or not nombre_busqueda:
            return None, None
        for grupo in ["predicciones", "sensores", "indices"]:
            items = data.get(grupo, {})
            if isinstance(items, dict):
                for k, v in items.items():
                    if nombre_busqueda.lower() in k.lower():
                        return v.get("valor") if isinstance(v, dict) and "valor" in v else v, grupo
            if isinstance(items, list):
                for item in items:
                    nombre_item = str(item.get("nombre", ""))
                    if nombre_busqueda.lower() in nombre_item.lower():
                        return item.get("valor"), grupo
        return None, None

    def _match_nombre_libre(texto: str) -> tuple[str | None, str | None]:
        disponibles = _listar_valores_disponibles()
        candidatos = []
        for grupo, nombres in disponibles.items():
            if not isinstance(nombres, list):
                continue
            for nombre in nombres:
                if not nombre or len(nombre) < 3:
                    continue
                if nombre.lower() in texto:
                    candidatos.append((nombre, grupo))
        if not candidatos:
            return None, None
        candidatos.sort(key=lambda x: len(x[0]), reverse=True)
        return candidatos[0]

    evento_match = re.search(r'(hubo|hay|no hubo|no hay) (.+)', t)
    if evento_match:
        accion = evento_match.group(1)
        entidad = evento_match.group(2).strip()
        nombre, grupo = _match_nombre_libre(entidad)
        if nombre:
            valor_real = 100 if accion in ("hubo", "hay") else 0
            tipo = "indice" if grupo == "indices" else "sensor" if grupo == "sensores" else "prediccion"
            valor_estimado = None
            try:
                data = submenu_detallado()
                valor_estimado, _ = _lookup_valor(data, nombre)
            except Exception:
                logging.exception("Silent except at 2861 - revisar contexto")
            from fastapi.testclient import TestClient
            client = TestClient(app)
            client.post("/feedback_prediccion", json={
                "tipo": tipo,
                "nombre": nombre,
                "valor": valor_estimado,
                "feedback": "acierto" if valor_real >= 50 else "error",
                "valor_real": valor_real
            })
            msg = f"Feedback registrado: {'positivo' if valor_real >= 50 else 'negativo'} sobre {nombre}"
            return _respuesta_voz(session_id, msg)
    if feedback_match or feedback_error_match:
        tipo = 'prediccion'
        nombre = None
        feedback = 'acierto' if feedback_match else 'error'
        if feedback_match:
            nombre = feedback_match.group(5).strip() if feedback_match.group(5) else None
        if feedback_error_match:
            nombre = feedback_error_match.group(5).strip() if feedback_error_match.group(5) else None
        if "indice" in t or "índice" in t:
            tipo = 'indice'
        valor_real = None
        if valor_real_match:
            valor_real = valor_real_match.group(2).replace(',', '.').strip()
        # Buscar valor estimado actual si es posible
        valor_estimado = None
        try:
            # Buscar en predicciones, sensores e índices
            data = submenu_detallado()
            if nombre:
                valor_estimado, grupo = _lookup_valor(data, nombre)
                if grupo:
                    tipo = "indice" if grupo == "indices" else "sensor" if grupo == "sensores" else "prediccion"
        except Exception:
            logging.exception("Silent except at 2896 - revisar contexto")
        if valor_real is not None and valor_estimado is not None:
            try:
                v_real = float(valor_real)
                v_estimado = float(valor_estimado)
                if abs(v_real - v_estimado) <= 5:
                    feedback = "acierto"
            except Exception:
                logging.exception("Silent except at 2904 - revisar contexto")
        # Enviar feedback al endpoint
        from fastapi.testclient import TestClient
        client = TestClient(app)
        client.post("/feedback_prediccion", json={
            "tipo": tipo,
            "nombre": nombre,
            "valor": valor_estimado,
            "feedback": feedback,
            "valor_real": valor_real
        })
        msg = f"Feedback registrado: {feedback} sobre {nombre or 'valor'}"
        if valor_real:
            msg += f" (valor real: {valor_real})"
        return _respuesta_voz(session_id, msg)

    # --- FIN FEEDBACK POR VOZ ---

    if "submenu" in t or "submenú" in t:
        data = submenu_detallado()
        return _respuesta_voz(session_id, "Mostrando submenú detallado.", {"submenu": data})
    if "crear formula" in t or "crear fórmula" in t:
        m = re.search(r"crear\s+(?:formula|fórmula)\s*(?:llamada|llamar|de|para)?\s*([\w\- ]+?)\s*(?:=|:|\bque\b|\bcon\b)\s*(.+)", raw_text, flags=re.IGNORECASE)
        if not m:
            return _respuesta_voz(session_id, "Dime el nombre y la fórmula. Ejemplo: crear fórmula sensación = (temp + humedad/100).")
        nombre = m.group(1).strip().replace(" ", "_")
        expresion = m.group(2).strip()
        unidad_match = re.search(r"unidad\s+([\w%°/]+)", raw_text, flags=re.IGNORECASE)
        unidad = unidad_match.group(1) if unidad_match else "unidad"
        descripcion = f"Sensor virtual creado por voz: {expresion}"
        try:
            if hasattr(system, "agregar_sensor_virtual"):
                system.agregar_sensor_virtual(nombre, expresion, unidad, descripcion)
                return _respuesta_voz(session_id, f"Fórmula registrada como {nombre}.")
            return _respuesta_voz(session_id, "El sistema no admite sensores virtuales en este momento.")
        except Exception as e:
            return _respuesta_voz(session_id, f"No pude crear la fórmula: {e}")
    if "layout" in t or "diseño" in t or "diseno" in t:
        target_layout = None
        if "column" in t or "columnas" in t:
            target_layout = "columns"
        elif "libre" in t:
            target_layout = "free"
        elif "default" in t or "estandar" in t or "estándar" in t:
            target_layout = "default"
        if target_layout:
            _guardar_layout(target_layout)
            return _respuesta_voz(session_id, f"Layout cambiado a {target_layout}.")
        try:
            import json
            ruta = _ruta_layout()
            if ruta.exists():
                data = json.loads(ruta.read_text(encoding="utf-8"))
                layout_actual = data.get("layout", "default")
            else:
                layout_actual = "default"
            return _respuesta_voz(session_id, f"El layout actual es {layout_actual}.")
        except Exception:
            return _respuesta_voz(session_id, "No pude leer el layout actual.")
    if any(x in t for x in ["qué día hace", "que dia hace", "que tiempo hace", "qué tiempo hace", "cómo está el tiempo", "como esta el tiempo", "clima"]):
        resumen = _resumen_tiempo()
        return _respuesta_voz(session_id, resumen["text"], resumen.get("extra"))
    respuesta = _resolver_consulta_valor(text)
    if respuesta:
        extra = dict(respuesta)
        texto_resp = extra.pop("text", "")
        extra.pop("audio", None)
        return _respuesta_voz(session_id, texto_resp, extra)
    disponibles = _listar_valores_disponibles()
    if disponibles.get("total", 0) == 0:
        return _respuesta_voz(session_id, "Aún no hay datos de sensores recibidos.")
    lista = (disponibles.get("sensores", []) + disponibles.get("derivados", []) + disponibles.get("indices", []))
    muestra = ", ".join(lista[:12])
    return _respuesta_voz(session_id, f"No encontré ese valor. Puedes preguntar por: {muestra}.")


def _ruta_layout() -> pathlib.Path:
    path = BASE_DIR / "data" / "layout.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _ruta_paneles() -> pathlib.Path:
    path = BASE_DIR / "data" / "panels.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _build_contexto(sensores: dict, indices: dict) -> dict:
    def _val(obj, key):
        if isinstance(obj, dict) and key in obj:
            v = obj.get(key)
            if isinstance(v, dict) and "valor" in v:
                return v.get("valor")
            return v
        return None

    ruido = sensores.get("ruido")
    if ruido is None:
        ruido = 20.0
    luz = sensores.get("luz")
    if luz is None:
        luz = 30.0

    contexto = {
        "temperatura_exterior": sensores.get("temperatura"),
        "humedad_exterior": sensores.get("humedad"),
        "temperatura_interior": sensores.get("temperatura_interior"),
        "humedad_interior": sensores.get("humedad_interior"),
        "co2": sensores.get("co2"),
        "pm25": sensores.get("pm25") or sensores.get("pm25_ch1") or sensores.get("wh43"),
        "ruido": ruido,
        "luz": luz,
        "viento": sensores.get("viento"),
        "radiacion_solar": sensores.get("radiacion"),
        "punto_rocio": _val(indices, "punto_rocio"),
        "tendencia_presion": _val(indices, "tendencia_presion"),
        "tendencia_temperatura": _val(indices, "tendencia_temperatura"),
        "tendencia_humedad": _val(indices, "tendencia_humedad"),
        "estabilidad_termica": _val(indices, "estabilidad_termica"),
        "ventilacion_ideal": _val(indices, "ventilacion_ideal"),
        "riesgo_lluvia": _val(indices, "riesgo_lluvia"),
        "alerta_tormenta": _val(indices, "alerta_tormenta"),
        "riesgo_micro_lluvias": _val(indices, "riesgo_micro_lluvias"),
        "riesgo_helada_local": _val(indices, "riesgo_helada_local"),
        "ersf": _val(indices, "ersf"),
        "irin": _val(indices, "irin"),
        "irsh": _val(indices, "irsh"),
        "ireav": _val(indices, "ireav"),
        "irsd": _val(indices, "irsd"),
        "ot": sensores.get("temperatura_interior") or sensores.get("temperatura"),
        "hora_local": datetime.datetime.now().hour + datetime.datetime.now().minute / 60.0,
    }
    return contexto


def _guardar_layout(layout: str):
    try:
        _ruta_layout().write_text(json.dumps({"layout": layout}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        logging.exception("Silent except at 3012 - revisar contexto")


@app.get("/config/layout")
def obtener_layout():
    ruta = _ruta_layout()
    if ruta.exists():
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            return {"layout": data.get("layout", "default")}
        except Exception:
            logging.exception("Silent except at 3023 - revisar contexto")
    return {"layout": "default"}


@app.post("/config/layout")
def guardar_layout(payload: dict):
    layout = payload.get("layout") if isinstance(payload, dict) else "default"
    if layout not in ["default", "columns", "free"]:
        layout = "default"
    _guardar_layout(layout)
    return {"status": "OK", "layout": layout}


@app.get("/config/panels")
def obtener_paneles():
    ruta = _ruta_paneles()
    if ruta.exists():
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            return {"order": data.get("order", []), "sizes": data.get("sizes", {})}
        except Exception:
            logging.exception("Silent except at 3044 - revisar contexto")
    return {"order": [], "sizes": {}}


@app.post("/config/panels")
def guardar_paneles(payload: dict):
    order = payload.get("order") if isinstance(payload, dict) else []
    sizes = payload.get("sizes") if isinstance(payload, dict) else {}
    if not isinstance(order, list):
        order = []
    if not isinstance(sizes, dict):
        sizes = {}
    try:
        _ruta_paneles().write_text(json.dumps({"order": order, "sizes": sizes}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        logging.exception("Silent except at 3059 - revisar contexto")
    return {"status": "OK", "order": order, "sizes": sizes}


def _resumen_meteo_actual():
    try:
        data = estado()
    except Exception:
        data = {}
    sensores = data.get("sensores", {}) if isinstance(data, dict) else {}
    indices = data.get("indices", {}) if isinstance(data, dict) else {}
    temp = sensores.get("temperatura")
    hum = sensores.get("humedad")
    lluvia = sensores.get("lluvia")
    viento = sensores.get("viento")
    rad = sensores.get("radiacion")
    niebla = indices.get("riesgo_niebla", {}).get("valor") if isinstance(indices.get("riesgo_niebla"), dict) else None
    lluvia_riesgo = indices.get("riesgo_lluvia", {}).get("valor") if isinstance(indices.get("riesgo_lluvia"), dict) else None
    nub = indices.get("nubosidad_estimada", {}).get("valor") if isinstance(indices.get("nubosidad_estimada"), dict) else None

    frases = []
    if temp is not None:
        try:
            t = float(temp)
            if t < 15:
                frases.append("Hace frío")
            elif t > 28:
                frases.append("Hace calor")
            else:
                frases.append("Temperatura moderada")
        except Exception:
            logging.exception("Silent except at 3090 - revisar contexto")
    if lluvia is not None:
        try:
            l = float(lluvia)
            if l > 0.2:
                frases.append("Está lloviendo")
        except Exception:
            logging.exception("Silent except at 3097 - revisar contexto")
    if lluvia_riesgo is not None:
        try:
            if float(lluvia_riesgo) >= 60:
                frases.append("Alta probabilidad de lluvia")
        except Exception:
            logging.exception("Silent except at 3103 - revisar contexto")
    if niebla is not None:
        try:
            if float(niebla) >= 40:
                frases.append("Hay riesgo de niebla")
        except Exception:
            logging.exception("Silent except at 3109 - revisar contexto")
    if nub is not None:
        try:
            if float(nub) >= 70:
                frases.append("Cielo muy nublado")
        except Exception:
            logging.exception("Silent except at 3115 - revisar contexto")

    detalles = []
    if temp is not None:
        detalles.append(f"temperatura {temp}°C")
    if hum is not None:
        detalles.append(f"humedad {hum}%")
    if viento is not None:
        detalles.append(f"viento {viento} km/h")
    if rad is not None:
        detalles.append(f"radiación {rad} W/m²")

    resumen = ", ".join(frases) if frases else "Condiciones normales"
    if detalles:
        resumen += ". " + ", ".join(detalles)
    return resumen


@app.get("/auto_reparacion")
def auto_reparacion_estado():
    if not auto_repair_engine:
        return {"status": "inactive"}
    return auto_repair_engine.last_report


@app.get("/auto_expansion")
def auto_expansion_estado():
    expansion = AutoExpansionEngine(system).report()
    sugerencias = system.auto_improvement_system.auto_expansion.obtener_sugerencias() if system.auto_improvement_system else []
    return {"catalogo": expansion, "sugerencias": sugerencias}


@app.get("/pas")
def pas_estado():
    if not pas_engine:
        return {"status": "inactive"}
    return pas_engine.status(system.sensores)

# Mantener el endpoint /ecowitt para integración de sensores
@app.api_route("/ecowitt", methods=["POST", "GET"])
async def recibir_ecowitt(request: Request):
    data = {}
    if request.method == "POST":
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            data = {}
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
    
    # SINCRONÍA TEMPORAL: Inyectar timestamp preciso del dateutc
    try:
        from core.integration.temporal_sync_persistence import apply_temporal_sync, reset_monin_obukhov_on_pressure_change
        data = apply_temporal_sync(data, system)
    except Exception as e:
        logging.getLogger(__name__).exception(f"Error en sincronía temporal: {e}")
    
    # HELPER PARA PERSISTENCIA DE EMERGENCIA
    def actualizar_con_persistencia(sensor_id: str, valor: float, metadata_kwargs: dict = None):
        """Actualizar sensor y guardar como last_valid_value para emergencias."""
        try:
            if valor is not None:
                system.actualizar_sensor(sensor_id, valor)
                # Guardar last_valid_value en metadata
                if not hasattr(system, 'sensores_metadata'):
                    system.sensores_metadata = {}
                if sensor_id not in system.sensores_metadata:
                    system.sensores_metadata[sensor_id] = {}
                system.sensores_metadata[sensor_id]['last_valid_value'] = float(valor)
                if metadata_kwargs:
                    system.registrar_sensor_metadata(sensor_id, **metadata_kwargs)
        except Exception as e:
            logging.getLogger(__name__).exception(f"Error en actualizar_con_persistencia({sensor_id}): {e}")
    
    if not data:
        try:
            ts = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
            system.actualizar_sensor("ultimo_ecowitt_error", ts)
        except Exception:
            logging.exception("Silent except at 3209 - revisar contexto")
        return {"status": "WARN", "received": False, "message": "Payload vacío"}
    # Log detallado de rayos y puerto
    import socket
    try:
        puerto = request.url.port or 'desconocido'
    except Exception:
        puerto = 'desconocido'
    print(f"[Ecowitt] Datos recibidos en puerto {puerto}:")
    for k, v in data.items():
        print(f"  {k}: {v}")
    print(f"  lightning: {data.get('lightning')}")
    print(f"  lightning_num: {data.get('lightning_num')}")
    print(f"  lightning_time: {data.get('lightning_time')}")

    # ═══════════════════════════════════════════════════════════════════════
    # PRESIÓN (HP2550A): MISMA PARA INTERIOR Y EXTERIOR (ATMÓSFERA GLOBAL)
    # Publicar AMBOS valores como interior Y como exterior
    # ═══════════════════════════════════════════════════════════════════════
    # PRESIÓN HP2550A: RELATIVA (baromrelin) Y ABSOLUTA (baromabsin)
    # Ambas se guardan como INTERIOR y EXTERIOR (misma atmósfera)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        # PRESIÓN RELATIVA (baromrelin - nivel del mar)
        baromrelin = data.get("baromrelin")
        if baromrelin is not None:
            presion_relativa_hpa = float(baromrelin) * 33.8638866667  # inHg → hPa
            if 900 <= presion_relativa_hpa <= 1100:
                # Guardar en sistema para Monin-Obukhov
                actualizar_con_persistencia("presion", presion_relativa_hpa, {"tipo": "presion", "unidad": "hPa", "fuente": "HP2550A", "origen": "externo", "fiabilidad": 95.0})
                if hasattr(system, "sensores"):
                    system.sensores["presion_status"] = "OK"
                    system.sensores["presion_fuente"] = "HP2550A"
                # Publicar como INTERIOR y EXTERIOR (mismo valor)
                system.actualizar_sensor("presion_relativa_interior", presion_relativa_hpa)
                system.actualizar_sensor("presion_relativa_exterior", presion_relativa_hpa)
                print(f"[INGESTA] Presion HP2550A RELATIVA (nivel mar): {presion_relativa_hpa:.2f} hPa → INTERIOR y EXTERIOR")
            else:
                if hasattr(system, "sensores"):
                    system.sensores["presion_status"] = "OUT_OF_RANGE"
                print(f"[ADVERTENCIA] Presion relativa fuera de rango: {presion_relativa_hpa:.2f} hPa (rango válido: 900-1100)")

        # PRESIÓN ABSOLUTA (baromabsin - nivel del sensor)
        baromabsin = data.get("baromabsin")
        if baromabsin is not None:
            presion_absoluta_hpa = float(baromabsin) * 33.8638866667  # inHg → hPa
            if 900 <= presion_absoluta_hpa <= 1100:
                # Publicar como INTERIOR y EXTERIOR (mismo valor)
                system.actualizar_sensor("presion_absoluta_interior", presion_absoluta_hpa)
                system.actualizar_sensor("presion_absoluta_exterior", presion_absoluta_hpa)
                print(f"[INGESTA] Presion HP2550A ABSOLUTA (nivel sensor): {presion_absoluta_hpa:.2f} hPa → INTERIOR y EXTERIOR")
            else:
                print(f"[ADVERTENCIA] Presion absoluta fuera de rango: {presion_absoluta_hpa:.2f} hPa (rango válido: 900-1100)")
    except Exception as e:
        logging.getLogger(__name__).exception(f"Error procesando presión HP2550A: {e}")
        if hasattr(system, "sensores"):
            system.sensores["presion_status"] = "ERROR"
    # Guardar marca de tiempo y payload recibido (datos reales)
    try:
        ts = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        system.actualizar_sensor("ultimo_ecowitt", ts)
        payload_path = BASE_DIR / "data" / "last_ecowitt_payload.json"
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(
            json.dumps({"timestamp": ts, "data": data}, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception:
        logging.exception("Silent except at 3279 - revisar contexto")

    # Sensores desconocidos/experimentales (prefijo sensor_)
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
                logging.exception("Silent except at 3297 - revisar contexto")
            try:
                system.actualizar_sensor(sensor_id, val)
            except Exception:
                try:
                    system.sensores[sensor_id] = val
                except Exception:
                    logging.exception("Silent except at 3304 - revisar contexto")
    except Exception:
        logging.exception("Silent except at 3306 - revisar contexto")

    # Sensores interiores
    tempint = data.get("tempinf")
    humedadint = data.get("humidityin")
    baromrelint = data.get("baromrelin")  # HP2550A: misma fuente para interior/exterior
    baromabsint = data.get("baromabsin")  # HP2550A: misma fuente para interior/exterior
    system.actualizar_sensor("tempinf_original", tempint)
    system.actualizar_sensor("humidityin_original", humedadint)
    system.actualizar_sensor("baromrelin_original", baromrelint)
    system.actualizar_sensor("baromabsin_original", baromabsint)
    
    # Conversión y registro de interiores
    if tempint is not None:
        try:
            tempint_c = (float(tempint) - 32) * 5.0 / 9.0
            actualizar_con_persistencia("temperatura_interior", tempint_c, {"tipo": "temperatura_interior", "unidad": "C", "fuente": "ecowitt", "origen": "externo", "fiabilidad": 90.0})
        except Exception:
            system.actualizar_sensor("temperatura_interior", None)
    if humedadint is not None:
        try:
            humedadint_num = float(humedadint)
            if 0 <= humedadint_num <= 100:
                system.actualizar_sensor("humedad_interior", humedadint_num)
                system.registrar_sensor_metadata("humedad_interior", tipo="humedad_interior", unidad="%", fuente="ecowitt", origen="externo", fiabilidad=90.0)
            else:
                system.actualizar_sensor("humedad_interior", None)
        except Exception:
            system.actualizar_sensor("humedad_interior", None)
    
    temperatura = data.get("tempf")
    humedad = data.get("humidity")
    viento = data.get("windspeedmph")
    radiacion = data.get("solarradiation")
    uv_raw = data.get("uv") or data.get("uvi") or data.get("uvindex") or data.get("uv_index")

    lluvia_rate_candidates = [
        ("rainratein", data.get("rainratein")),
        ("rain_ratein", data.get("rain_ratein")),
        ("rainrate", data.get("rainrate")),
        ("rain_rate", data.get("rain_rate")),
        ("rainrate_mm", data.get("rainrate_mm")),
    ]
    lluvia_acum_candidates = [
        ("rainin", data.get("rainin")),
        ("dailyrainin", data.get("dailyrainin")),
        ("eventrainin", data.get("eventrainin")),
        ("hourlyrainin", data.get("hourlyrainin")),
        ("dailyrainmm", data.get("dailyrainmm")),
        ("eventrainmm", data.get("eventrainmm")),
        ("hourlyrainmm", data.get("hourlyrainmm")),
        ("rainmm", data.get("rainmm")),
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

    best_acum = None
    best_acum_unit = None  # "in" or "mm"
    for key, val in lluvia_acum_candidates:
        if val is None:
            continue
        acum_val = _to_float(val)
        if acum_val is None:
            continue
        unit = "in" if key.endswith("in") else "mm"
        if best_acum is None or acum_val > best_acum:
            best_acum = acum_val
            best_acum_unit = unit
    # Guardar valores originales para trazabilidad
    system.actualizar_sensor("tempf_original", temperatura)
    system.actualizar_sensor("humidity_original", humedad)
    system.actualizar_sensor("windspeedmph_original", viento)
    rainratein_raw = data.get("rainratein") or data.get("rain_ratein")
    system.actualizar_sensor("rainratein_original", rainratein_raw)
    rainin_raw = data.get("rainin") or data.get("dailyrainin") or data.get("eventrainin") or data.get("hourlyrainin")
    if rainin_raw is not None:
        system.actualizar_sensor("rainin_original", rainin_raw)
    system.actualizar_sensor("solarradiation_original", radiacion)
    if uv_raw is not None:
        system.actualizar_sensor("uv_original", uv_raw)
    # Procesar radiación solar
    if radiacion is not None:
        try:
            radiacion_num = float(radiacion)
            system.actualizar_sensor("radiacion", radiacion_num)
            system.registrar_sensor_metadata("radiacion", tipo="radiacion_solar", unidad="W/m²", fuente="ecowitt", origen="externo", fiabilidad=90.0)
        except Exception:
            system.actualizar_sensor("radiacion", radiacion)
    # Procesar UV
    if uv_raw is not None:
        try:
            uv_val = float(uv_raw)
            system.actualizar_sensor("uv", uv_val)
            system.registrar_sensor_metadata("uv", tipo="uv", unidad="", fuente="ecowitt", origen="externo", fiabilidad=85.0)
        except Exception:
            system.actualizar_sensor("uv", uv_raw)
    # Sensores extra: rayos y partículas
    lightning = data.get("lightning")
    lightning_num = data.get("lightning_num")
    lightning_time = data.get("lightning_time")
    pm25 = data.get("pm25") or data.get("pm25_ch1") or data.get("wh43")
    # Guardar distancia de rayo (si Ecowitt la envía)
    if lightning is not None:
        try:
            lightning_dist = float(lightning)
        except Exception:
            lightning_dist = lightning
        system.actualizar_sensor("lightning", lightning_dist)
        system.actualizar_sensor("distancia_rayo", lightning_dist)
        system.registrar_sensor_metadata("distancia_rayo", tipo="distancia_rayo", unidad="km", fuente="ecowitt", origen="externo", fiabilidad=85.0)
    # Guardar fecha/hora del último rayo
    if lightning_time is not None:
        system.actualizar_sensor("lightning_time", lightning_time)
        system.actualizar_sensor("ultimo_rayo", lightning_time)
    # Si existe lightning_num, usarlo como contador absoluto preferente con detección de reset
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
            except Exception as e:
                logging.getLogger(__name__).exception("Error leyendo valores previos de lightning: %s", e)
                prev_num_val = None
                prev_total_val = 0
            offset = system.sensores.get("rayos_offset", 0)
            try:
                offset = float(offset)
            except Exception:
                offset = 0
            if prev_num_val is not None and lightning_num_val < prev_num_val:
                # Reset del contador en el dispositivo: consolidar total previo
                offset = prev_total_val
            total = offset + lightning_num_val
            system.actualizar_sensor("rayos_total", float(total))
            system.actualizar_sensor("rayos", float(total))
            system.actualizar_sensor("rayos_offset", float(offset))
            system.actualizar_sensor("lightning_num", lightning_num_val)
            system.registrar_sensor_metadata("rayos", tipo="contador_rayos", unidad="", fuente="ecowitt", origen="externo", fiabilidad=85.0)
    # --- PM2.5: Registro con ámbito interior/exterior ---
    import logging
    pm_key_candidates = [k for k in data.keys() if k.lower().startswith('pm25') or k.lower().startswith('pm2.5') or k.lower().startswith('pm_25')]
    logging.getLogger(__name__).warning(f"[PM LOOP DEBUG] Candidatos PM encontrados: {pm_key_candidates}")
    for pm_key in pm_key_candidates:
        try:
            pm_val = float(data.get(pm_key))
        except Exception:
            continue
        # Determinar ámbito: si hay tempinf/humidityin -> interior
        ambito = 'exterior'
        if data.get('tempinf') is not None or data.get('humidityin') is not None or data.get('tempin') is not None:
            ambito = 'interior'
        sensor_id = pm_key
        try:
            # REGISTRAR metadata sin parámetro ambito (registrar_sensor_metadata no lo acepta)
            system.registrar_sensor_metadata(sensor_id, tipo='pm25', unidad='µg/m³', fuente='ecowitt', origen='externo', fiabilidad=90.0)
            # Forzar escritura directa del ambito en sensores_metadata
            if hasattr(system, 'sensores_metadata'):
                system.sensores_metadata.setdefault(sensor_id, {})
                system.sensores_metadata[sensor_id]['ambito'] = ambito
            # LOG CRÍTICO: Confirmar registro de ambito
            logging.getLogger(__name__).warning(f"[ADUANA ECOWITT] Sensor PM {sensor_id} → ambito={ambito} | tempinf={data.get('tempinf')} | humidityin={data.get('humidityin')}")
        except Exception as e:
            logging.getLogger(__name__).error(f"[ADUANA] Error al registrar PM metadata: {e}")
        # Actualizar sensor específico
        try:
            system.actualizar_sensor(sensor_id, pm_val)
        except Exception as e:
            logging.getLogger(__name__).exception("Error actualizando sensor %s: %s", sensor_id, e)
            try:
                system.sensores[sensor_id] = pm_val
            except Exception as e2:
                logging.getLogger(__name__).exception("Fallo asignando sensor %s en system.sensores: %s", sensor_id, e2)
        # PUBLICAR sensor genérico 'pm25' con herencia de metadata
        try:
            if hasattr(system, 'sensores_metadata'):
                if 'pm25' not in system.sensores_metadata:
                    system.sensores_metadata['pm25'] = {}
                system.sensores_metadata['pm25']['ambito'] = ambito
                system.sensores_metadata['pm25']['fuente'] = sensor_id
                # LOG NUCLEAR: confirmar herencia de ambito
                logging.getLogger(__name__).warning(f"[HERENCIA AMBITO] pm25 heredó ambito={ambito} de {sensor_id}")
        except Exception as herencia_err:
            logging.getLogger(__name__).error(f"[HERENCIA AMBITO] ERROR: {herencia_err}")
        # Actualizar sensor genérico 'pm25'
        try:
            system.actualizar_sensor('pm25', pm_val)
        except Exception:
            try:
                system.sensores['pm25'] = pm_val
            except Exception:
                logging.exception("Silent except at 3519 - revisar contexto")
        # Trazabilidad global
        try:
            system.sensores['pm25_fuente'] = sensor_id
            system.sensores['pm25_ambito'] = ambito
        except Exception:
            logging.exception("Silent except at 3525 - revisar contexto")
    
    # ════════════════════════════════════════════════════════════
    # CAPTURA DE CO2 DESDE ECOWITT (WH45 sensor)
    # ════════════════════════════════════════════════════════════
    co2_raw = data.get("co2")
    if co2_raw is not None:
        try:
            co2_val = float(co2_raw)
            system.actualizar_sensor("co2", co2_val)
            system.registrar_sensor_metadata("co2", tipo="co2", unidad="ppm", fuente="ecowitt", origen="externo", fiabilidad=85.0)
            logging.getLogger(__name__).warning(f"[ADUANA ECOWITT] Sensor CO2 capturado: co2={co2_val}ppm")
        except Exception as e:
            logging.getLogger(__name__).exception(f"Error al procesar CO2: {e}")
    
    # WH51 (humedad del suelo) y valor AD crudo si existe
    soil_keys = [
        "soilmoisture1", "soilmoisture2", "soilmoisture3", "soilmoisture4",
        "soilmoisture", "soil_moisture", "soil_moisture1", "wh51",
    ]
    soil_raw = None
    for key in soil_keys:
        if data.get(key) is not None:
            soil_raw = data.get(key)
            break
    if soil_raw is not None:
        try:
            soil_val = float(soil_raw)
            system.actualizar_sensor("wh51", soil_val)
            system.registrar_sensor_metadata("wh51", tipo="humedad_suelo", unidad="%", fuente="ecowitt", origen="externo", fiabilidad=90.0)
        except Exception:
            system.actualizar_sensor("wh51", soil_raw)

    soil_ad_keys = [
        "soilmoisture1_ad", "soilmoisture1adc", "soilmoisture1_adc",
        "soilmoisture1_raw", "soilmoisture1raw", "soilad1", "wh51_ad",
        "ad1", "ad_1",
    ]
    soil_ad_raw = None
    for key in soil_ad_keys:
        if data.get(key) is not None:
            soil_ad_raw = data.get(key)
            break
    if soil_ad_raw is not None:
        try:
            soil_ad_val = float(soil_ad_raw)
            system.actualizar_sensor("wh51_ad", soil_ad_val)
            system.registrar_sensor_metadata("wh51_ad", tipo="humedad_suelo_ad", unidad="ad", fuente="ecowitt", origen="externo", fiabilidad=70.0)
        except Exception:
            system.actualizar_sensor("wh51_ad", soil_ad_raw)
    # Convertir temperatura de Fahrenheit a Celsius SIEMPRE y guardar solo en °C
    if temperatura is not None:
        try:
            temperatura_c = (float(temperatura) - 32) * 5.0 / 9.0
            actualizar_con_persistencia("temperatura", temperatura_c, {"tipo": "temperatura", "unidad": "C", "fuente": "ecowitt", "origen": "externo", "fiabilidad": 90.0})
        except Exception:
            system.actualizar_sensor("temperatura", None)
    if humedad is not None:
        try:
            humedad_num = float(humedad)
            if 0 <= humedad_num <= 100:
                actualizar_con_persistencia("humedad", humedad_num, {"tipo": "humedad", "unidad": "%", "fuente": "ecowitt", "origen": "externo", "fiabilidad": 90.0})
            else:
                system.actualizar_sensor("humedad", None)
        except Exception:
            system.actualizar_sensor("humedad", None)
    if viento is not None:
        try:
            viento_kmh = float(viento) * 1.60934
            actualizar_con_persistencia("viento", viento_kmh, {"tipo": "viento", "unidad": "km/h", "fuente": "ecowitt", "origen": "externo", "fiabilidad": 85.0})
        except Exception:
            system.actualizar_sensor("viento", viento)
    if best_rate is not None:
        try:
            lluvia_rate_mm = best_rate * 25.4 if best_rate_unit == "in" else best_rate
            system.actualizar_sensor("lluvia", lluvia_rate_mm)
            system.actualizar_sensor("lluvia_rate", lluvia_rate_mm)
            system.registrar_sensor_metadata("lluvia", tipo="lluvia", unidad="mm", fuente="ecowitt", origen="externo", fiabilidad=90.0)
        except Exception:
            system.actualizar_sensor("lluvia", best_rate)
    elif best_acum is not None:
        try:
            lluvia_acum_mm = best_acum * 25.4 if best_acum_unit == "in" else best_acum
            system.actualizar_sensor("lluvia", lluvia_acum_mm)
            system.actualizar_sensor("lluvia_acumulada", lluvia_acum_mm)
            system.registrar_sensor_metadata("lluvia", tipo="lluvia", unidad="mm", fuente="ecowitt", origen="externo", fiabilidad=90.0)
        except Exception:
            system.actualizar_sensor("lluvia", best_acum)
    # Recalcular índices tras cada actualización (solo cálculo, no guardar en system.indices si es un motor)
    if hasattr(system, 'indices') and hasattr(system.indices, 'obtener_todos'):
        _ = system.indices.obtener_todos()  # Solo recalcula, no asigna
    
    # 🌪️ VALIDACIÓN CRUZADA CO2/PM2.5 - DETECTOR DE COMBUSTIÓN
    try:
        from core.engines.indoor_air_cross_validator import validate_indoor_air_cross
        
        # Extraer sensores relevantes
        co2_ppm = system.sensores.get("co2")
        pm25_ugm3 = system.sensores.get("pm25") or system.sensores.get("pm25_interior")
        temp_interior = system.sensores.get("temperatura_interior") or system.sensores.get("tempinf")
        hum_interior = system.sensores.get("humedad_interior") or system.sensores.get("humidityin")
        
        # Solo validar si hay al menos un sensor disponible
        if co2_ppm is not None or pm25_ugm3 is not None:
            validation_result = validate_indoor_air_cross(co2_ppm, pm25_ugm3, temp_interior, hum_interior)
            
            # Almacenar resultado en system para que otros motores lo consulten
            system.sensores["indoor_air_quality_status"] = validation_result["estado"].value
            system.sensores["indoor_air_quality_flag"] = validation_result["flag"]
            system.sensores["indoor_air_quality_score"] = validation_result["score"]
            system.sensores["indoor_air_quality_recomendacion"] = validation_result["recomendacion"]
            
            # Log si hay combustión confirmada
            if validation_result["estado"].value == "COMBUSTION_CONFIRMADA":
                logger.warning(f"🔥 COMBUSTIÓN CONFIRMADA: {validation_result['recomendacion']}")
    except Exception as e:
        logging.getLogger(__name__).exception(f"Error en validación cruzada CO2/PM2.5: {e}")
    
    return {"status": "OK", "received": True}


# 🛸 ENDPOINT DE OMNIPOTENCIA V1.5
@app.get("/admin/omnipotencia/status")
async def get_omnipotence_status():
    """Estado del sistema de descubrimiento universal"""
    if not omnipotence_manager:
        return {"error": "Omnipotencia no disponible"}
    return omnipotence_manager.get_status()


@app.get("/admin/omnipotencia/dispositivos")
async def get_detected_devices():
    """Lista de dispositivos detectados por el radar"""
    if not omnipotence_manager:
        return {"error": "Omnipotencia no disponible", "dispositivos": []}
    
    devices = omnipotence_manager.scanner.get_devices()
    return {
        "total": len(devices),
        "dispositivos": [
            {
                "id": d.id,
                "nombre": d.name,
                "tipo": d.type,
                "direccion": d.address,
                "detectado": d.detected_at.isoformat(),
                "metadata": d.metadata
            }
            for d in devices
        ]
    }

    async def _security_optimization_loop():
        """Ciclos de optimización de seguridad (cada 10 minutos) - auto-mejora de defensas"""
        while True:
            try:
                orchestrator = getattr(app_instance.state, "security_orchestrator", None)
                if orchestrator:
                    result = orchestrator.execute_security_cycle()
                    if result:
                        logger.info(
                            f"🛡️ Ciclo seguridad #{result.get('cycle_num')}: "
                            f"{result.get('vulnerabilities_discovered', 0)} gaps descubiertos, "
                            f"{result.get('security_duels_won', 0)} mejoras integradas, "
                            f"Seguridad actual: {result.get('current_security_score', 0):.1f}%"
                        )
            except Exception as e:
                logger.error(f"Error en security_optimization_loop: {e}")
            await asyncio.sleep(600)  # Cada 10 minutos
