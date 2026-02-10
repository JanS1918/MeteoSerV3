# 📋 CAPAS QUE NO IMPLEMENTAMOS - ENUMERACIÓN CLARA

**Fecha:** 4 de febrero 2026 | **Total no implementadas:** 8 capas

---

## ❌ LISTA EXHAUSTIVA: CAPAS COMPLETAMENTE FALTANTES

### 1. **CAPA 12: Gate de cascada A→B→C (Profundidad 1)**

**¿Qué es?**
- Validador que rechaza fórmulas que necesitan más de 1 nivel de dependencia
- Si fórmula requiere A→B→C para calcularse → **RECHAZO AUTOMÁTICO**

**¿Por qué falta?**
- Archivo `core/monitoring/cascade_depth_gate.py` NO EXISTE
- Validador no está integrado en pipeline de duelo

**¿Qué hace falta?**
- [ ] Crear `core/monitoring/cascade_depth_gate.py`
- [ ] Clase `CascadeDepthGate` con método `validate_depth(formula_ast)`
- [ ] Integrar en `automated_duel_engine.py` como pre-validación
- [ ] Rechazar si profundidad > 1

**Impacto:** CRÍTICO - Sin esto, fórmulas complejas pueden degradar sistema

**Tiempo estimado:** 2-3 horas

---

### 2. **CAPA 13: Auditoría Bus integration (trazabilidad subfactores)**

**¿Qué es?**
- Monitor que valida: Si fórmula DECLARA 3 subfactores → 3 deben estar en Bus
- Si publica A, B, C pero solo B llega al Bus → ALERT

**¿Por qué falta?**
- Archivo `core/bus/bus_integration_auditor.py` NO EXISTE
- Sistema Bus existe pero sin auditoría de trazabilidad

**¿Qué hace falta?**
- [ ] Crear `core/bus/bus_integration_auditor.py`
- [ ] Clase `BusIntegrationAuditor`
- [ ] Método `audit_subfactor_completeness(formula_name, declared_subfactors, published_subfactors)`
- [ ] Registrar discrepancias en logs

**Impacto:** MEDIO-ALTO - Previene "agujeros" en Bus

**Tiempo estimado:** 1.5-2 horas

---

### 3. **CAPA 14: Gate de estabilidad temporal (drift detection como gate)**

**¿Qué es?**
- Rechaza fórmulas si su salida presenta drift temporal > umbral
- Valida: p95 latency < 1s Y variancia < 5%

**¿Por qué falta?**
- Existe CUSUM en `core/engines/statistical_brain.py` (función `cusum_drift_detection`)
- **PERO NO está integrado como gate que RECHAZA**
- Solo calcula, no valida

**¿Qué hace falta?**
- [ ] Crear `core/monitoring/drift_detection_gate.py`
- [ ] Clase `DriftDetectionGate`
- [ ] Integrar CUSUM como método de detección
- [ ] Método `validate_drift(formula_outputs, threshold_variance=0.05, threshold_latency_p95=1.0)`
- [ ] Rechazo automático si excede

**Impacto:** ALTO - Detecta fórmulas que se degradan en tiempo real

**Tiempo estimado:** 2 horas

---

### 4. **CAPA 15: Presupuesto fluidez/eficiencia (resource budget gate)**

**¿Qué es?**
- Bloquea fórmulas que usan demasiados recursos
- Validaciones: CPU < 10%, RAM < 500MB, latency p95 < 1s

**¿Por qué falta?**
- Archivo `core/monitoring/resource_budget_gate.py` NO EXISTE
- Sistema observabilidad REGISTRA métricas pero NO las BLOQUEA

**¿Qué hace falta?**
- [ ] Crear `core/monitoring/resource_budget_gate.py`
- [ ] Clase `ResourceBudgetGate`
- [ ] Método `validate_resource_consumption(formula_name, cpu_pct, ram_mb, latency_p95_s)`
- [ ] Rechazo si: CPU ≥ 10 OR RAM ≥ 500 OR latency ≥ 1

**Impacto:** MEDIO - Previene que fórmulas "hambrientas" saturen sistema

**Tiempo estimado:** 1.5 horas

---

### 5. **CAPA 16: Anomaly detector de ganadores (overfitting detection)**

**¿Qué es?**
- Detecta si una "mejora" es "demasiado perfecta" (señal de overfitting)
- Si mejora > 20% pero estabilidad degrada > 10% → RECHAZO sospechoso

**¿Por qué falta?**
- Archivo `core/monitoring/anomaly_detector_winners.py` NO EXISTE
- Existe `core/validation/anomaly_detector.py` pero es para SENSORES, no fórmulas

**¿Qué hace falta?**
- [ ] Crear `core/monitoring/anomaly_detector_winners.py`
- [ ] Clase `AnomalyDetectorWinners`
- [ ] Método `detect_overfitting_signal(improvement_pct, stability_delta_pct, precision_delta_pct)`
- [ ] Lógica: Si mejora > 20% Y estabilidad < -10% → flag sospechoso → rechazo

**Impacto:** ALTO - Evita que IA acepte "trampas" matemáticas

**Tiempo estimado:** 2 horas

---

### 6. **CAPA 17: Sandbox de ejecución (execution sandbox)**

**¿Qué es?**
- Ejecuta fórmula en entorno aislado CON LÍMITES antes del duelo real
- Timeout: 30s, CPU cap: 50%, RAM: 200MB
- Si excede → rechazo sin duelo

**¿Por qué falta?**
- Archivo `core/monitoring/execution_sandbox.py` NO EXISTE
- Existe `self_mod_engine.py` con `sandbox=True/False` pero es PREVIEW, no execution sandbox

**¿Qué hace falta?**
- [ ] Crear `core/monitoring/execution_sandbox.py`
- [ ] Clase `ExecutionSandbox`
- [ ] Método `execute_with_limits(formula_func, inputs, timeout_s=30, cpu_limit_pct=50, ram_limit_mb=200)`
- [ ] Usar `resource.setrlimit()` + `signal.alarm()`
- [ ] Rechazo si timeout o límites excedidos

**Impacto:** CRÍTICO - Sin esto, fórmula maligna puede colgar sistema

**Tiempo estimado:** 2.5-3 horas

---

### 7. **CAPA 18: Canary rollout (gradual deployment con fases)**

**¿Qué es?**
- Deploya fórmula en fases: 5% → 10% → 50% → 100%
- Cada fase dura ≥ 2h
- Si regresión > 1% en cualquier fase → rollback automático

**¿Por qué falta?**
- Archivo `core/deployment/canary_rollout_manager.py` NO EXISTE
- Estructura deployment existe pero sin canary phases

**¿Qué hace falta?**
- [ ] Crear `core/deployment/canary_rollout_manager.py`
- [ ] Clase `CanaryRolloutManager`
- [ ] Método `execute_canary_deployment(formula_name, phases=[5, 10, 50, 100])`
- [ ] Cada fase: espera 2h → mide regresión
- [ ] Si regresión > 1% → rollback automático
- [ ] Logging de cada fase

**Impacto:** CRÍTICO - Es ÚNICO mecanismo para deploy seguro

**Tiempo estimado:** 3-4 horas

---

### 8. **CAPA 21: Centinela externo independiente (watchdog soberano)**

**¿Qué es?**
- **PROCESO SEPARADO** (no hilo, no dentro de main app)
- Monitorea heartbeat de main app vía socket TCP (cada 30s)
- Si timeout (35s) → **MATA proceso main + restaura último snapshot**

**¿Por qué falta?**
- Archivo `watchdog_soberano.py` NO EXISTE
- Existe `auto_change_watchdog.py` pero es INTERNO, no soberano

**¿Por qué es diferente?**
- Watchdog internal (capa 19): puede estar corrupto/comprometido
- Watchdog soberano (capa 21): **EXTERNO, independiente, no killeable por main**
- Es la última defensa contra corrupción total

**¿Qué hace falta?**
- [ ] Crear `watchdog_soberano.py` en raíz (NO en core/)
- [ ] Clase `WatchdogSoberano`
- [ ] Método `heartbeat_monitor()` con socket TCP listen en puerto 9617
- [ ] Hilo: espera signal main cada 30s
- [ ] Si 35s sin signal → `os.kill(main_pid, SIGKILL)` + restore snapshot
- [ ] Método `restore_from_snapshot()` para rollback
- [ ] **INICIAR como proceso EXTERNO en arranque**

**Impacto:** CRÍTICO-MÁXIMO - Es defensa final contra IA "rogue"

**Tiempo estimado:** 3-4 horas

---

## 📊 RESUMEN: CAPAS QUE NO HACEMOS

| # | Nombre | Archivo | Status | P | Horas |
|---|--------|---------|--------|---|-------|
| 12 | Cascade depth | `core/monitoring/cascade_depth_gate.py` | ❌ | 🔴 | 2-3 |
| 13 | Bus auditor | `core/bus/bus_integration_auditor.py` | ❌ | 🟡 | 1.5-2 |
| 14 | Drift gate | `core/monitoring/drift_detection_gate.py` | ❌ | 🟠 | 2 |
| 15 | Resource budget | `core/monitoring/resource_budget_gate.py` | ❌ | 🟡 | 1.5 |
| 16 | Anomaly winners | `core/monitoring/anomaly_detector_winners.py` | ❌ | 🟠 | 2 |
| 17 | Sandbox exec | `core/monitoring/execution_sandbox.py` | ❌ | 🔴 | 2.5-3 |
| 18 | Canary rollout | `core/deployment/canary_rollout_manager.py` | ❌ | 🔴 | 3-4 |
| 21 | Centinela soberano | `watchdog_soberano.py` | ❌ | 🔴 | 3-4 |

**Total horas estimadas:** 18-22 horas de desarrollo

**Prioridad orden recomendado:** 21 → 12 → 18 → 17 → 16 → 14 → 15 → 13

---

## 🔴 CRÍTICOS ABSOLUTOS (ANTES DE PRODUCCIÓN)

### Tú decides prioridad, pero estos 3 son **IMPRESCINDIBLES**:

1. **Centinela soberano (Capa 21)** 
   - Sin esto: IA puede corromperse y no hay quien la detenga
   - Prototipo mínimo: 3h

2. **Canary rollout (Capa 18)**
   - Sin esto: deploys van 0% → 100% de golpe (riesgo catastrófico)
   - Prototipo mínimo: 3h

3. **Cascade depth (Capa 12)**
   - Sin esto: fórmulas pueden ser A→B→C→D→... (cadenas infinitas)
   - Prototipo mínimo: 2h

**Los otros 5 son importantes pero más "robustez" que "prevención de desastre".**

