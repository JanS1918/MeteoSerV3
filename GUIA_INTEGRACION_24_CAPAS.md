# 🔧 GUÍA DE INTEGRACIÓN - 24 CAPAS EN PIPELINE

## 1. INICIALIZACIÓN EN main_asgi.py

```python
# Agregar al startup de FastAPI
from core.monitoring.cascade_depth_gate import CascadeDepthGate
from core.monitoring.drift_detection_gate import DriftDetectionGate
from core.monitoring.resource_budget_gate import ResourceBudgetGate
from core.monitoring.anomaly_detector_winners import AnomalyDetectorWinners
from core.monitoring.execution_sandbox import ExecutionSandbox
from core.deployment.canary_rollout_manager import CanaryRolloutManager
from core.bus.bus_integration_auditor import BusIntegrationAuditor
from core.calibration.bias_sensor_bus_publisher import BiasSensorBusPublisher
from core.ui.alert_filter_system import AlertFilterSystem, AlertSeverity, AlertCategory

# En lifespan startup:
@app.on_event("startup")
async def startup():
    # Inicializar nuevas capas
    app.cascade_depth_gate = CascadeDepthGate()
    app.drift_detection_gate = DriftDetectionGate()
    app.resource_budget_gate = ResourceBudgetGate()
    app.anomaly_detector = AnomalyDetectorWinners()
    app.sandbox = ExecutionSandbox()
    app.canary_manager = CanaryRolloutManager()
    app.bus_auditor = BusIntegrationAuditor()
    app.bias_publisher = BiasSensorBusPublisher(mqtt_client=app.mqtt)
    app.alert_system = AlertFilterSystem()
    
    # Iniciar watchdog en proceso separado
    import subprocess
    app.watchdog_process = subprocess.Popen([
        'python', 'watchdog_soberano.py',
        '--port', '9617',
        '--app-pid', str(os.getpid())
    ])
    logger.info("✅ Watchdog iniciado como proceso separado (PID: {})".format(app.watchdog_process.pid))
```

---

## 2. PRE-DUELO VALIDATION PIPELINE

En `automated_duel_engine.py` agregar:

```python
async def validate_formula_for_duelo(formula_name: str, formula_code: str) -> Tuple[bool, str]:
    """Pipeline completo de validación pre-duelo (CAPAS 12-17)"""
    
    # CAPA 12: Cascade Depth Gate
    cascade_result = app.cascade_depth_gate.analyze(formula_name)
    if not cascade_result.passed:
        return False, f"❌ CAPA 12: {cascade_result.reason}"
    
    # CAPA 14: Drift Detection
    drift_result = app.drift_detection_gate.analyze(formula_name)
    if not drift_result.passed:
        return False, f"❌ CAPA 14: {drift_result.reason}"
    
    # CAPA 15: Resource Budget
    resource_result = app.resource_budget_gate.analyze(formula_name)
    if not resource_result.passed:
        return False, f"❌ CAPA 15: {resource_result.reason}"
    
    # CAPA 17: Execution Sandbox
    sandbox_result = app.sandbox.execute_with_limits(
        formula_name,
        eval_formula,  # función a ejecutar
        formula_code, sample_data
    )
    if not sandbox_result.executed:
        return False, f"❌ CAPA 17: {sandbox_result.violation or sandbox_result.error}"
    
    # CAPA 16: Anomaly Detector (si hay mejora previa)
    if previous_improvement_pct > 0:
        anomaly_result = app.anomaly_detector.analyze_improvement(
            formula_name, improvement_pct=previous_improvement_pct,
            stability_delta=stability_delta, precision_delta=precision_delta
        )
        if anomaly_result.detected_overfitting:
            return False, f"❌ CAPA 16: {anomaly_result.reason}"
    
    # CAPA 13: Bus Integration Audit
    bus_audit = app.bus_auditor.audit_formula(formula_name, published_subfactors)
    if not bus_audit.audit_passed:
        return False, f"❌ CAPA 13: {bus_audit.reason}"
    
    # ✅ Todas las capas pasaron
    return True, f"✅ Todas las validaciones pasaron (CAPAS 12-17)"
```

---

## 3. POST-DUELO CANARY DEPLOYMENT

En `post_duelo_handler.py`:

```python
async def start_canary_deployment(formula_name: str, winning_formula_id: str):
    """Inicia despliegue gradual (CAPA 18)"""
    
    deployment_id = app.canary_manager.start_canary_deployment(
        formula_name, winning_formula_id
    )
    logger.info(f"✅ Canary iniciado: {deployment_id} (fase 1: 5%)")
    
    # Monitorear por 2h mínimo
    while True:
        await asyncio.sleep(120)  # Cada 2 minutos
        
        # Recolectar métricas
        phase_metrics = collect_canary_metrics()
        
        # CAPA 14: Validar drift
        drift_ok = app.drift_detection_gate.analyze(formula_name).passed
        
        # CAPA 15: Validar recursos
        resource_ok = app.resource_budget_gate.analyze(formula_name).passed
        
        if not (drift_ok and resource_ok):
            logger.error("❌ Canary degradación detectada, iniciando rollback")
            app.canary_manager.rollback(deployment_id, "Degradación en CAPA 14/15")
            return False
        
        # Avanzar fase si 2h han pasado
        if check_time_for_phase_advance():
            success = app.canary_manager.advance_phase(
                deployment_id, current_phase, phase_metrics
            )
            if success:
                logger.info(f"✅ Fase avanzada a {current_phase}")
            else:
                logger.error(f"❌ Rollback en fase {current_phase}")
                return False
```

---

## 4. WATCHDOG HEARTBEAT LOOP

En `main_asgi.py` o `asyncio` background task:

```python
async def send_watchdog_heartbeat():
    """Envía heartbeat TCP al centinela soberano cada 30s"""
    import socket
    
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', 9617))
            sock.send(b"HEARTBEAT")
            sock.close()
            logger.debug("💓 Heartbeat enviado a watchdog")
        except Exception as e:
            logger.error(f"❌ Error heartbeat: {e}")
        
        await asyncio.sleep(30)

# En startup:
@app.on_event("startup")
async def startup():
    asyncio.create_task(send_watchdog_heartbeat())
```

---

## 5. BUS MQTT INTEGRATION (CAPAS 13, 23)

En `bus_publisher.py`:

```python
async def publish_calibration_data(sensor_name: str, bias_offset: float, confidence: float):
    """Publica sesgo de sensor al Bus (CAPA 23)"""
    
    app.bias_publisher.register_bias(sensor_name, bias_offset, confidence, time.time())
    success = app.bias_publisher.publish_to_bus(sensor_name)
    
    if success:
        logger.info(f"✅ Bias {sensor_name} publicado: {bias_offset:+.2f}°C")
    else:
        logger.error(f"❌ Error publicando bias {sensor_name}")

async def audit_bus_subfactors(formula_name: str):
    """Audita subfactores en Bus (CAPA 13)"""
    
    declared = get_declared_subfactors(formula_name)
    published = get_published_subfactors_from_bus(formula_name)
    
    audit_result = app.bus_auditor.audit_formula(formula_name, published)
    
    if not audit_result.audit_passed:
        app.alert_system.add_alert(
            AlertSeverity.HIGH,
            AlertCategory.BUS,
            f"Subfactores faltantes: {audit_result.missing_from_bus}"
        )
```

---

## 6. UI ALERT SYSTEM (CAPA 24)

En `dashboard_api.py`:

```python
@app.get("/api/alerts")
async def get_alerts(severity_filter: str = "CRITICAL"):
    """Retorna alertas filtradas para UI"""
    
    # Configurar filtro
    min_severity = AlertSeverity[severity_filter]
    app.alert_system.set_filter(severity_min=min_severity)
    
    # Obtener alertas filtradas
    alerts = app.alert_system.get_filtered_alerts(acknowledged=False)
    
    return {
        "summary": app.alert_system.get_dashboard_summary(),
        "alerts": [
            {
                "id": a.alert_id,
                "severity": a.severity.value,
                "category": a.category.value,
                "message": a.message,
                "timestamp": a.timestamp
            }
            for a in alerts
        ]
    }

@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Marca alerta como reconocida"""
    success = app.alert_system.acknowledge_alert(alert_id)
    return {"acknowledged": success}
```

---

## 7. LOGGING & MONITORING

Todas las capas registran en `app.logger`:

```python
# CAPA 12 - Cascade
app.logger.warning(f"⚠️ CAPA 12: Cascade {formula_name} profundidad={depth}")

# CAPA 14 - Drift
app.logger.info(f"✅ CAPA 14: Drift check {formula_name} latency_p95={latency_p95:.2f}s")

# CAPA 18 - Canary
app.logger.info(f"🚀 CAPA 18: Canary phase {phase} - {phase_pct}% tráfico")

# CAPA 21 - Watchdog
app.logger.critical(f"⚠️ CAPA 21: Watchdog timeout 35s, ejecutando SIGKILL")
```

---

## 8. TESTING COVERAGE

```bash
# Test cada capa individualmente
pytest tests/test_capa_12_cascade.py
pytest tests/test_capa_13_audit.py
pytest tests/test_capa_14_drift.py
pytest tests/test_capa_15_resource.py
pytest tests/test_capa_16_anomaly.py
pytest tests/test_capa_17_sandbox.py
pytest tests/test_capa_18_canary.py
pytest tests/test_capa_21_watchdog.py
pytest tests/test_capa_23_bias.py
pytest tests/test_capa_24_alerts.py

# Test pipeline completo
pytest tests/test_full_pipeline.py -v

# Test watchdog recovery
pytest tests/test_watchdog_recovery.py
```

---

## 9. CONFIGURACIÓN POR AMBIENTE

### Development
```yaml
watchdog_timeout: 35s
canary_phase_duration: 10m  # Menor para testing
cascade_max_depth: 1
drift_window: 100  # Menor
```

### Production
```yaml
watchdog_timeout: 35s
canary_phase_duration: 2h  # Enforced
cascade_max_depth: 1
drift_window: 1000  # Completo
drift_latency_p95: 1.0s
resource_cpu_threshold: 10%
resource_ram_threshold: 500MB
```

---

## 10. CHECKLIST DE INTEGRACIÓN

- [ ] Importar todas las 24 capas en main_asgi.py
- [ ] Inicializar watchdog como proceso separado
- [ ] Conectar pre-duelo validation pipeline (CAPAS 12-17)
- [ ] Conectar post-duelo canary deployment (CAPA 18)
- [ ] Conectar heartbeat task al loop asyncio
- [ ] Conectar audit_formula a Bus (CAPA 13)
- [ ] Conectar publish_bias a Bus (CAPA 23)
- [ ] Conectar alert_system a dashboard (CAPA 24)
- [ ] Configurar thresholds por ambiente
- [ ] Implementar test suite completo
- [ ] Validar recovery < 5s para CAPA 21
- [ ] Validar SLA 2h mínima por fase (CAPA 18)
- [ ] Deploy a staging
- [ ] Deploy a producción con monitoreo

---

**Status:** 🎯 Todas las 24 capas listas para integración
