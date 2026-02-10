# 🔍 HALLAZGOS PROFUNDOS - ANÁLISIS CONTEXTUALIZADO DE CAPAS DE SEGURIDAD
**Fecha:** 4 de febrero 2026 | **Búsqueda:** Contextualizada en 1000+ archivos del proyecto

---

## 📊 RESUMEN EJECUTIVO

### Situación Real vs Planeada
| Métrica | Valor |
|---------|-------|
| **Capas planeadas** | 24 |
| **Capas realmente implementadas** | 13 |
| **Capas parcialmente implementadas** | 3 |
| **Capas completamente pendientes** | 8 |
| **Módulos de soporte descubiertos** | 15+ (nuevos, NO documentados antes) |
| **Sistemas de detección activos** | 6 |
| **Umbrales/thresholds configurados** | 40+ |

---

## ✅ CAPAS COMPLETAMENTE IMPLEMENTADAS (13)

### 1️⃣ **LOCKDOWN gate**
- **Archivo:** `core/monitoring/formula_security_gates.py`
- **Clase:** `FormulaSecurityGates`
- **Estado:** ✅ **IMPLEMENTADO**
- **Funcionamiento:** Bloquea emergencia manual de fórmulas
- **Refinamiento V37.2:** Activable por watchdog si ≥1 error físico o timeout > 30s

### 2️⃣ **Whitelist de parámetros sagrados**
- **Archivo:** `core/security/whitelist_enforcer.py`
- **Clase:** `WhitelistEnforcer`
- **Estado:** ✅ **IMPLEMENTADO**
- **Protege:** 50+ parámetros críticos (no modificables)
- **Descubrimiento:** También existe `core/bus/whitelist_sagrados_v30.py` con 11 umbrales de emergencia:
  - `riesgo_helada: 0.7`
  - `riesgo_tormenta: 0.7`
  - `riesgo_inundacion: 0.7`
  - `riesgo_incendio: 0.7`
  - `alerta_frio_extremo: 0.8`
  - `alerta_calor_extremo: 0.8`
  - Más 5 umbrales adicionales

### 3️⃣ **SpecValidationEngine**
- **Archivo:** `core/monitoring/spec_validation_engine.py`
- **Estado:** ✅ **IMPLEMENTADO**
- **Ciclo:** 6 horas
- **Validaciones:** Especificación completa, firma, canónico

### 4️⃣ **Firma + Canónico**
- **Archivo:** `core/monitoring/spec_validation_engine.py`
- **Estado:** ✅ **IMPLEMENTADO**
- **Refinamiento V37.2:** Detección de duplicados en 6h

### 5️⃣ **Dominio meteorológico**
- **Archivo:** `core/security/meteorological_domain_validator.py`
- **Clase:** `MeteorologicalDomainValidator`
- **Estado:** ✅ **IMPLEMENTADO**
- **Validaciones:** Rango físico, coherencia cross-variable

### 6️⃣ **Especificación completa**
- **Archivo:** `core/security/specification_completeness_validator.py`
- **Clase:** `SpecificationCompletenessValidator`
- **Estado:** ✅ **IMPLEMENTADO**
- **Rechazo si:** Incomplitud > umbral

### 7️⃣ **Precisión mínima**
- **Archivo:** `core/security/precision_validator.py`
- **Clase:** `PrecisionValidator`
- **Estado:** ✅ **IMPLEMENTADO**
- **Mapeo:** Parámetro → precisión requerida
- **Ejemplo:** Temperatura ±0.5°C, Presión ±1.5 hPa

### 8️⃣ **Juez termodinámico**
- **Archivo:** `core/monitoring/thermodynamic_judge.py`
- **Clase:** `ThermodynamicJudge`
- **Estado:** ✅ **IMPLEMENTADO**
- **Validaciones:** Límites físicos (0-100% humedad, presión válida)

### 9️⃣ **Optimización pre-duelo (EWMA)**
- **Archivo:** `core/monitoring/formula_optimizer.py`
- **Estado:** ✅ **IMPLEMENTADO**
- **Parámetro EWMA:** α = 0.1
- **Clipping:** ±1.5σ

### 🔟 **Duelo multi-etapa (1000 escenarios)**
- **Archivo:** `core/monitoring/formula_duel_engine.py`
- **Clase:** `FormulaDuelEngine`
- **Estado:** ✅ **IMPLEMENTADO**
- **Escenarios:** 1000 + 20% ruido sintético
- **Métodos:** 
  - `_duelo_parametro()`
  - `_guardar_resultado_duelo()`
- **Refinamiento V37.2:** Trade-off 60/30/10 (precisión/estabilidad/fluidez)

### 1️⃣1️⃣ **Comparador autoridad científica**
- **Archivo:** `core/monitoring/formula_comparator.py`
- **Clase:** `FormulaComparator`
- **Estado:** ✅ **IMPLEMENTADO**
- **Ranking:** Exhaustivo, rechaza fuentes externas

### 1️⃣2️⃣ **Watchdog + rollback + circuit breaker**
- **Archivo:** `core/monitoring/auto_change_watchdog.py`
- **Clase:** `AutoChangeWatchdog`
- **Estado:** ✅ **IMPLEMENTADO**
- **Heartbeat:** 30s
- **Timeout:** 35s
- **Rollback:** < 5s
- **Circuit breaker:** Freeze 12h si ≥2 rollbacks en 6h
- **Métodos clave:**
  - `evaluate()` → Revierte si degradación > umbral
  - `validate_spec_compliance()` → Validación proactiva
  - `_record_rollback_event()` → Registro de circuit breaker

### 1️⃣3️⃣ **Guardián 617 + SHA256**
- **Archivo:** `main_asgi.py` (L1368-L1490), `formula_security_lockdown.py`
- **Estado:** ⚠️ **PARCIALMENTE IMPLEMENTADO**
- **Implementado:**
  - Health endpoint público (sin credenciales)
  - SHA256 parcial en core/
  - Auditoría forense auto-activa
- **Falta:**
  - SHA256 completo en bus/ + security/
  - Verificación de integridad forense en anomalía

---

## ⚠️ CAPAS PARCIALMENTE IMPLEMENTADAS (3)

### 🔄 **Calibración de probabilidades (Capa 22 - Debate)**
- **Archivo:** `core/learning/learning_feedback.py` (proyecto, NO existe en codebase)
- **Soporte existente:** `core/calibration/auto_calibrator.py`, `core/engines/auto_improvement_engine.py`
- **Implementado:**
  - ✅ Ajuste de umbrales dinámico (método `ajustar_umbrales()`)
  - ✅ Historial de eventos
  - ✅ Ratio de aceptación calculado
  - ✅ Clipping: 10.0 ≤ umbral ≤ 90.0
- **Falta:** Entidad centralizada que combine feedback + probabilidades

### 🔄 **Bias/offset de sensores (Capa 23 - Debate)**
- **Archivo:** `core/calibration/bias_detector.py`
- **Clase:** `DetectorBias`
- **Estado:** ⚠️ **IMPLEMENTADO PERO NO INTEGRADO**
- **3 métodos de detección:**
  1. **Offset constante** → Si |diferencia| > 0.5 y σ < 2×|diferencia|
  2. **Regresión lineal** → Si pendiente ≠ 1 o intercepto ≠ 0 (ej: 0.05, 0.3)
  3. **Deriva temporal** → Si cambio/día > umbral
- **Métodos:**
  - `detectar_offset()` → Retorna (hay_bias, offset_valor, descripción)
  - `detectar_bias_regresion()` → (hay_bias, {pendiente, intercepto, r2, mae}, desc)
  - `detectar_deriva_temporal()` → (hay_deriva, tasa_por_día, desc)
  - `generar_reporte()` → Análisis completo
- **Publicación al Bus:** Falta integración
  - Debería publicar: `sensor_temperatura_bias_offset_c`, `sensor_temperatura_necesita_calibracion_bool`

### 🔄 **Filtro visual de alertas (Capa 24 - Debate)**
- **Archivo:** `core/ui/alert_filter_system.py` (NO existe)
- **Soporte existente:** `core/bus/whitelist_sagrados_v30.py` (CentinelaV30)
- **Implementado:**
  - ✅ Centinela con umbrales (11 parámetros)
  - ✅ Método `evaluar_parametro()` → Boolean
  - ✅ Alertas activas con timestamp y severidad
  - ✅ Logging de alertas críticas
  - ✅ Comparación: valor ≥ umbral → CRÍTICA; ≥ 0.9 → ALTA
- **Falta:** UI visual integrada que filtre alertas en dashboard

---

## ❌ CAPAS PENDIENTES (8)

### 🚧 **Capa 12: Gate de cascada A→B→C (Profundidad 1)**
- **Archivo requerido:** `core/monitoring/cascade_depth_gate.py`
- **Propósito:** Si fórmula necesita A→B→C (>1 nivel), rechazar
- **Refinamiento V37.2:** Depth mapper. >1 nivel → rechazo automático
- **Descubierto:** Existe `core/validation/sensor_validator_cascada.py` pero NO implementa gate
- **Estado:** ❌ **NO IMPLEMENTADO**

### 🚧 **Capa 13: Auditoría Bus integration**
- **Archivo requerido:** `core/bus/bus_integration_auditor.py`
- **Propósito:** Validar trazabilidad de subfactores (3 publicados → 1 en Bus → ALERT)
- **Refinamiento V37.2:** Subfactor traceability 100%
- **Estado:** ❌ **NO IMPLEMENTADO**
- **Nota:** Bus existe (`core/bus/`), pero NO auditor de subfactores

### 🚧 **Capa 14: Gate de estabilidad temporal (drift)**
- **Archivo requerido:** `core/monitoring/drift_detection_gate.py`
- **Propósito:** Bloquear si p95 latency > 1s O variancia > 5%
- **Descubierto:** CUSUM drift detection existe en `core/engines/statistical_brain.py`:
  ```python
  def cusum_drift_detection(value, state, threshold=5.0, slack=0.5)
  ```
  Pero NO integrado como gate de rechazo
- **Estado:** ❌ **NO IMPLEMENTADO COMO GATE**

### 🚧 **Capa 15: Presupuesto fluidez/eficiencia**
- **Archivo requerido:** `core/monitoring/resource_budget_gate.py`
- **Propósito:** CPU < 10%, RAM < 500MB, latency p95 < 1s
- **Refinamiento V37.2:** Medir en Canary. Si falla → rollback
- **Estado:** ❌ **NO IMPLEMENTADO**
- **Soporte parcial:** `core/system/observability_engine.py` REGISTRA métricas pero NO bloquea

### 🚧 **Capa 16: Anomaly detector de ganadores**
- **Archivo requerido:** `core/monitoring/anomaly_detector_winners.py`
- **Propósito:** Detectar si mejora es "demasiado perfecta" (overfitting signal)
- **Refinamiento V37.2:** Si mejora > 20% pero estabilidad degrada > 10% → RECHAZO
- **Descubierto:** `core/validation/anomaly_detector.py` existe pero es para SENSORES, no GANADORES
- **Estado:** ❌ **NO IMPLEMENTADO**

### 🚧 **Capa 17: Sandbox de ejecución**
- **Archivo requerido:** `core/monitoring/execution_sandbox.py`
- **Propósito:** Limita CPU/RAM/tiempo antes del duelo real (early termination)
- **Refinamiento V37.2:** Timeout 30s, CPU cap 50%, RAM 200MB. Si excede → rechazo sin duelo
- **Descubierto:** `self_mod_engine.py` tiene `sandbox=True/False` pero NO es execution sandbox
- **Estado:** ❌ **NO IMPLEMENTADO**

### 🚧 **Capa 18: Canary rollout (5%-10%-50%-100%)**
- **Archivo requerido:** `core/deployment/canary_rollout_manager.py`
- **Propósito:** Gradual deployment con monitoreo de regresión entre fases
- **Refinamiento V37.2:** Cada fase ≥ 2h. Si degradación > 1% → rollback automático
- **Estado:** ❌ **NO IMPLEMENTADO**
- **Soporte parcial:** Estructura de deployment existe, pero NO canary phases

### 🚧 **Capa 21: Centinela externo independiente**
- **Archivo requerido:** `watchdog_soberano.py` (PROCESO SEPARADO, no hilo)
- **Propósito:** Proceso completamente separado, monitorea heartbeat, obliga rollback
- **Refinamiento V37.2:** Daemon independiente. Socket TCP heartbeat 30s. Si falla → mata main + restaura snapshot
- **Estado:** ❌ **NO IMPLEMENTADO**
- **Crítico:** No puede ser hilo, debe ser PROCESO EXTERNO

---

## 🔬 DESCUBRIMIENTOS NUEVOS (Módulos no documentados antes)

### 1. **Detección de Anomalías Avanzada**
- **Archivo:** `core/validation/anomaly_detector.py`
- **Clase:** `AnomalyDetector`
- **Capacidades:**
  - Z-score (desviaciones estándar desde media)
  - Outlier detection (|z| > 3.0)
  - Incoherencia cross-variable
  - Configuración dinámica de thresholds
  - Publicación al Bus con metadata
- **Estado:** ✅ **ACTIVO**

### 2. **Detección CUSUM de Deriva (CUSUM Drift)**
- **Archivo:** `core/engines/statistical_brain.py` (línea 258)
- **Función:** `cusum_drift_detection(value, state, threshold=5.0, slack=0.5)`
- **Capacidades:**
  - Suma acumulativa de desviaciones
  - Detección robusta de cambios sistemáticos
  - State tracking temporal
- **Estado:** ✅ **IMPLEMENTADO pero NO integrado como gate**

### 3. **Auditoría de Cambios Centralizada**
- **Archivo:** `core/logging/audit_trail.py`
- **Capacidades:**
  - JSON-lines logging
  - Detección de anomalías registrada
  - Activación de fallback registrada
  - Histórico de eventos
- **Estado:** ✅ **ACTIVO**

### 4. **Motor de Mejora Automática**
- **Archivo:** `core/engines/auto_improvement_engine.py` Y `core/engines/autoimprovement_engine.py` (duplicado)
- **Capacidades:**
  - Ajuste de pesos de índices
  - Ajuste dinámico de umbrales (±2.0 por ratio)
  - Clipping: 10.0 ≤ umbral ≤ 90.0
  - Historial de eventos
- **Estado:** ✅ **ACTIVO**

### 5. **Orquestador Acorazado**
- **Archivo:** `core/system/acorazado_orchestrator.py`
- **Pipeline:** Anomalía → Auditoría → Fallback → Confianza → Observabilidad → Feature Store
- **Estado:** ✅ **IMPLEMENTADO**

### 6. **Motor de Observabilidad**
- **Archivo:** `core/system/observability_engine.py`
- **Métricas:**
  - Anomalies detected
  - Measurements processed
  - Check alert thresholds
- **Estado:** ✅ **ACTIVO**

### 7. **Health Check Engine**
- **Archivo:** `tools/health_check_engine.py`
- **Chequeos:**
  - Logs accesibles
  - Backups recientes
  - Detector funcionando
  - Reporte semanal
- **Estado:** ✅ **IMPLEMENTADO**

### 8. **Metadata Middleware (Bus)**
- **Archivo:** `core/bus/metadata_middleware.py`
- **Enriquecimiento:** Añade metadatos de detección a mediciones
- **Estado:** ✅ **IMPLEMENTADO**

### 9. **Memoria Episódica (SQL)**
- **Archivo:** `core/learning/episodic_memory_sqlite.py`
- **Memorización:** Episodios de anomalía con contexto
- **Estado:** ✅ **ACTIVO**

### 10. **Asistente IA**
- **Archivo:** `core/ia/assistant.py`
- **Funciones:**
  - `explain_anomaly()` → Explicación legible
  - `suggest_maintenance()` → Sugerencias basadas en histórico (>50% anomalía → fallo sensor)
- **Estado:** ✅ **IMPLEMENTADO**

### 11. **Monitor Bus Realtime**
- **Archivo:** `core/bus/monitor_bus.py`
- **Clase:** `MonitorBusRealtime`
- **Estado:** ✅ **IMPLEMENTADO**

### 12. **Sensor Anomaly Detector (específico)**
- **Archivo:** `core/validation/sensor_anomaly_detector.py`
- **Clase:** `SensorAnomalyDetector`
- **Estado:** ✅ **ACTIVO**

### 13. **Validador de Cascada**
- **Archivo:** `core/validation/sensor_validator_cascada.py`
- **Nota:** Existe pero NO implementa capa 12 (Gate cascade depth)
- **Estado:** ⚠️ **EXISTE pero SUB-UTILIZADO**

### 14. **Constantes y Topes Físicos (1000+)**
- **Archivo:** `core/system/bus_expander.py` (4600+ líneas)
- **Publicados:** 1000+ subfactores en Bus
- **Umbrales:**
  - `limite_estabilidad: 9`
  - `limite_energia: 1999 W/m²`
  - `limite_viento: 99 km/h`
  - `limite_cape: 4999 J/kg`
  - `limite_humedad_max: 100%`
  - `limite_humedad_min: 0%`
  - Más 30+ thresholds
- **Estado:** ✅ **COMPLETAMENTE IMPLEMENTADO**

### 15. **Calibración Avanzada (3 niveles)**
- **Archivos:**
  - `core/calibration/auto_calibrator.py` → AutoCalibrador (básico)
  - `core/calibration/bias_detector.py` → DetectorBias (avanzado)
  - `core/calibration/regression_calibrator.py` → CalibradorRegresion (ML)
- **Orquestador:** `OrquestadorCalibracion` integra los 3
- **Estado:** ✅ **IMPLEMENTADO**

---

## 📋 TABLA COMPARATIVA: PLANEADO vs REAL

| Capa | Nombre | Planeado | Real | Diferencia |
|------|--------|----------|------|-----------|
| 1 | LOCKDOWN | ✅ | ✅ | - |
| 2 | Whitelist 50 params | ✅ | ✅ + 11 más en v30 | +11 |
| 3 | SpecValidationEngine | ✅ | ✅ | - |
| 4 | Firma + Canónico | ✅ | ✅ | - |
| 5 | Dominio meteorológico | ✅ | ✅ | - |
| 6 | Especificación completa | ✅ | ✅ | - |
| 7 | Precisión mínima | ✅ | ✅ | - |
| 8 | Juez termodinámico | ✅ | ✅ | - |
| 9 | Optimización pre-duelo | ✅ | ✅ (α=0.1) | - |
| 10 | Duelo 1000 escenarios | ✅ | ✅ | - |
| 11 | Comparador científico | ✅ | ✅ | - |
| 12 | Cascade depth gate | ❌ | ❌ | **FALTA** |
| 13 | Bus integration audit | ❌ | ❌ | **FALTA** |
| 14 | Drift detection gate | ❌ | ⚠️ (existe CUSUM) | **Parcial** |
| 15 | Resource budget gate | ❌ | ❌ | **FALTA** |
| 16 | Anomaly detector winners | ❌ | ❌ (existe para sensores) | **FALTA** |
| 17 | Sandbox execution | ❌ | ❌ | **FALTA** |
| 18 | Canary rollout | ❌ | ❌ | **FALTA** |
| 19 | Watchdog + rollback | ✅ | ✅ (30s/35s/<5s) | - |
| 20 | Guardián 617 SHA256 | ⚠️ | ⚠️ | Parcial |
| 21 | Centinela externo | ❌ | ❌ | **FALTA** |
| 22 | Calibración prob | ⚠️ | ⚠️ (soporte existe) | Parcial |
| 23 | Bias sensores | ⚠️ | ⚠️ (DetectorBias) | Parcial |
| 24 | Filtro visual alertas | ❌ | ⚠️ (CentinelaV30) | Parcial |

---

## 🎯 ANÁLISIS POR CATEGORÍA

### 🛡️ Capas de PROTECCIÓN (1-11): 11/11 ✅
Todas implementadas. Sistema base FUERTE.

### 🚪 Capas de PUERTAS (12-18): 0/7 ❌
**CRÍTICAS FALTANTES:**
- Cascade depth (profundidad 1)
- Resource budget
- Anomaly winners
- Sandbox
- Canary phases

### 📊 Capas de MONITOREO (19-20): 1.5/2 ⚠️
- Watchdog ✅
- SHA256 ⚠️ (parcial)

### 🔒 Capas de VIGILANCIA EXTERNA (21): 0/1 ❌
- Centinela soberano COMPLETAMENTE FALTA

### 🧠 Capas de APRENDIZAJE (22-24): 1.5/3 ⚠️
- Calibración prob: soporte existe, falta orquestación
- Bias sensores: implementado pero NO integrado
- Filtro alertas: soporte existe (CentinelaV30) pero NO UI

---

## 📊 UMBRALES CONFIGURADOS (40+ descobertos)

### Watchdog/Rollback
- Heartbeat: 30s
- Timeout: 35s
- Rollback time: <5s
- Max rollbacks en 6h: 2
- Freeze duration: 12h
- Precision: 0.03 (3% max degradation)
- Stability: 0.05 (5%)
- Efficiency: 0.08 (8%)
- Score: 0.02 (2%)

### Whitelist (CentinelaV30)
- `riesgo_helada: 0.7`
- `riesgo_tormenta: 0.7`
- `riesgo_inundacion: 0.7`
- `riesgo_incendio: 0.7`
- `alerta_helada: 0.7`
- `alerta_tormenta: 0.7`
- `alerta_frio_extremo: 0.8`
- `alerta_calor_extremo: 0.8`
- `temperatura_anomalia: 0.75`
- `presion_anomalia: 0.75`
- `viento_anomalia: 0.75`

### Bias Detection
- Offset umbral: ±0.5
- Regresión pendiente: ≠1 por >0.05
- Regresión intercepto: ≠0 por >0.3
- Deriva temporal: cambio/día > umbral

### EWMA Optimization
- Alpha: 0.1
- Clipping: ±1.5σ

### Auto-Improvement
- Umbral mínimo: 10.0
- Umbral máximo: 90.0
- Ratio bajo (<0.2): +2.0
- Ratio alto (>0.8): -2.0

### Anomaly Detection
- Z-score outlier: |z| > 3.0
- Desviación patrón temp: 2 × σ
- Desviación patrón presión: 10 hPa

### Resource Constraints (planeados, NO implementados)
- CPU: <10%
- RAM: <500MB
- Latency p95: <1s
- Canary phase: ≥2h cada una

### Cascade Depth
- Máximo nivel permitido: 1 (si >1 → rechazo)

---

## 🔮 IMPACTO DE HALLAZGOS

### 🎉 POSITIVO (+++)
1. **Detección de anomalías REAL Y FUNCIONANDO** (no solo planeada)
   - 6 sistemas diferentes
   - Z-score, CUSUM, offset, regresión, deriva, cross-variable
   
2. **Calibración avanzada CASI LISTA**
   - BiasDetector con 3 métodos
   - Orquestador integrado
   - Falta solo publicación al Bus

3. **1000+ subfactores meteorológicos**
   - 40+ umbrales físicos
   - Bus completamente expandido

4. **Auditoría y logging COMPRENSIVO**
   - JSON-lines
   - Episódica
   - Forensic auto-activation

### ⚠️ PREOCUPANTE (++)
1. **8 puertas de seguridad DISEÑADAS pero NO IMPLEMENTADAS**
   - Cascade depth, resource budget, anomaly winners, sandbox, canary
   - Estas son las más críticas para deploy seguro

2. **Centinela soberano COMPLETAMENTE FALTA**
   - Proceso externo NO existe
   - Watchdog solo interno

3. **Integraciones FRAGMENTADAS**
   - BiasDetector existe pero NO publica al Bus
   - CentinelaV30 existe pero NO tiene UI
   - CUSUM existe pero NO es gate

### 🚨 CRÍTICO (!)
1. **Canary phases NO EXISTEN**
   - Deploy sin monitoreo gradual
   - Rollout 0% → 100% (riesgo alto)

2. **Sandbox execution NO EXISTE**
   - Sin timeout/CPU/RAM limits pre-duelo
   - Early termination SIN protección

3. **Cascade depth NO VALIDADO**
   - Profundidad 1 constraint NO es obligatorio
   - Puede haber A→B→C que rompe diseño

---

## 📋 IMPLEMENTACIÓN INMEDIATA (Prioridad)

### 🔴 P0 - BLOQUEANTES (deben ser 1eras)
1. **Capa 21: Centinela soberano** (watchdog_soberano.py)
   - Proceso EXTERNO separado
   - Socket TCP heartbeat 30s
   - Kill main + restore si timeout

2. **Capa 12: Cascade depth gate** (core/monitoring/cascade_depth_gate.py)
   - Validator DAG depth
   - Rechaza >1 nivel
   - Integración en duelo pre-validación

### 🟠 P1 - CRÍTICOS (siguientes)
3. **Capa 18: Canary rollout** (core/deployment/canary_rollout_manager.py)
   - 5% → 10% → 50% → 100% fases
   - ≥2h cada una
   - Rollback si deg > 1%

4. **Capa 17: Sandbox execution** (core/monitoring/execution_sandbox.py)
   - Timeout 30s
   - CPU 50%
   - RAM 200MB
   - Pre-duelo

5. **Integración BiasDetector** (core/calibration/bias_detector.py → Bus)
   - Publicar: `sensor_*_bias_offset`, `sensor_*_necesita_calibracion`

### 🟡 P2 - IMPORTANTES (después)
6. **Capa 15: Resource budget gate** (core/monitoring/resource_budget_gate.py)
   - Medir en canary
   - CPU < 10%, RAM < 500MB, latency p95 < 1s

7. **Capa 16: Anomaly detector winners** (core/monitoring/anomaly_detector_winners.py)
   - Detectar overfitting
   - Si mejora > 20% pero estabilidad < 10% → rechazo

8. **Capa 13: Bus integration auditor** (core/bus/bus_integration_auditor.py)
   - 100% trazabilidad subfactores

---

## ✨ CONCLUSIÓN

**Estructura base (capas 1-11): EXCELENTE ✅**
- 11/11 completamente implementadas
- Watchdog robusto (30s/35s/<5s)
- 1000 escenarios duelo
- Validadores completos
- Detección de anomalías real

**Puertas de seguridad (capas 12-18): CRÍTICA FALTA ❌**
- 0/7 implementadas
- Sin cascade depth validation
- Sin resource budgeting
- Sin canary phases
- Sin sandbox pre-duelo

**Vigilancia externa (capa 21): NO EXISTE ❌**
- Centinela soberano completamente falta

**Sistemas de soporte (descubrimientos): ROBUSTOS ✅**
- 15+ módulos activos no documentados
- Calibración avanzada lista
- Auditoría completa
- 1000+ subfactores

**Recomendación:** Implementar P0 + P1 ANTES de producción.

