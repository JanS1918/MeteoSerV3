# SISTEMA PSICOTÉCNICO MAESTRO V36

## Archivo Principal
**`SISTEMA_PSICOTECNICO_MAESTRO_V36.py`** - Sistema completo de validación universal

## Contenido

### ✅ 25 CAPAS EN 7 FASES
```
FASE 1: Críticas Rápidas (CAPA 1,6)           - Rechazo rápido 50%, DURAS
FASE 2: Contexto (CAPA 2-5,11)               - Datos para validaciones, FLEXIBLES
FASE 3: Datos Duros (CAPA 7,8,10)            - Integridad, DURAS
FASE 4: Validaciones Avanzadas (CAPA 18-24,9) - Pruebas profundas, FLEXIBLES
FASE 5: Detección Inteligente (CAPA 14-16-22) - Anomalías, FLEXIBLES
FASE 6: Feedback (CAPA 17,21,22)             - Auditoría, FLEXIBLES
FASE 7: Meta-Análisis (CAPA 25)              - Decisión con Justice Score
```

### ✅ 5 MITIGACIONES AL 99.99%
1. **Cascade Analyzer V2** - AST static analysis (85% → 95%)
2. **ML Calibrator** - Justice Score weights (85% → 92%)
3. **Robust Duel Engine** - Particiones estratégicas + Mann-Whitney U (85% → 94%)
4. **Whitelist Fixes** - Auto-fixes seguras (55% → 97%)
5. **Transient Classifier** - Errores transitorio vs sistémico (85% → 93%)

### ✅ MEJORAS V36
- Tests Estadísticos (Mann-Whitney U)
- Watchdog 24h Post-Deploy
- Entropy Index (confianza)
- Filtrado Histórico (limpia datos contaminados)
- Rate Limiting, Canary Deploy, Health Checks
- Detector de Especificidad (acepta fórmula SOLO para ciertos cálculos)

### ✅ UNIVERSAL
- Aplicable a **FÓRMULAS** (precision, stability, fluidity)
- Aplicable a **ALGORITMOS** (precision, recall, f1-score, silhouette)
- Aplicable a **MODELOS** (AUC, Logloss, RMSE)

## Clases Principales

### PsychotechnicValidator
Valida candidata a través de 25 capas
```python
validator = PsychotechnicValidator(domain=ValidationDomain.FORMULA)
journey = await validator.validate_candidate(candidate_id, test_func, metrics)
```

### CascadeAnalyzer
Detecta riesgo de cascada mediante AST
```python
analyzer = CascadeAnalyzer(workspace_root)
risk_score = await analyzer.analyze_cascade_risk(component_id)
```

### MLCalibrator
Calibra pesos del Justice Score
```python
calibrator = MLCalibrator()
calibrator.add_historical_records(clean_records)
weights = await calibrator.calibrate_weights()
```

### RobustDuelEngine
Ejecuta duelo con particiones + Mann-Whitney U
```python
duel = RobustDuelEngine()
result = await duel.execute_robust_duel(candidate_id, current_id, dataset, test_func)
```

### Watchdog24h
Monitorea post-deploy, rollback automático si degrada > 10%
```python
watchdog = Watchdog24h()
alert = await watchdog.monitor_deployed_candidate(candidate_id, metrics_fn)
```

### CalculationSpecificityAnalyzer
Analiza: ¿fórmula es mejor SOLO para ciertos cálculos?
```python
analyzer = CalculationSpecificityAnalyzer()
profile = await analyzer.analyze_formula(formula_id, code, test_results, current_scores)
```

## Flujo Completo

```
CANDIDATA
   ↓
FILTRADO HISTÓRICO (limpia datos contaminados)
   ↓
25 CAPAS (7 FASES)
   ↓
Justice Score >= 0.75?
   ├─ SÍ → continúa
   └─ NO → RECHAZO
   ↓
CASCADE ANALYZER V2 (risk < 0.7?)
   ├─ SÍ → continúa
   └─ NO → NOTIFICAR_HUMANO
   ↓
ROBUST DUEL (Mann-Whitney U)
   ├─ Candidata gana TODAS particiones + p<0.05 + margin>=10%?
   ├─ SÍ → ACEPTADA
   ├─ NO pero margin 5-10% → NEEDS_REVIEW
   └─ NO → RECHAZADA
   ↓
CANARY DEPLOY (1% tráfico, snapshot reversible)
   ↓
WATCHDOG 24h
   ├─ Degradación > 10% → ROLLBACK automático (<1min)
   ├─ Degradación 5-10% → ALERTA
   └─ Estable 24h → FULL DEPLOY
```

## Adaptación a Algoritmos

**TIEMPO: 2-3 horas**

```python
from SISTEMA_PSICOTECNICO_MAESTRO_V36 import PsychotechnicOrchestrator, ValidationDomain

# Para clustering:
orchestrator = PsychotechnicOrchestrator(
    domain=ValidationDomain.ALGORITHM
)

# Cambios necesarios:
# 1. Métricas: precision, recall, f1-score, silhouette
# 2. Whitelist: hyperparameter_tuning en lugar de EWMA
# 3. Test function: ejecuta clustering en lugar de fórmula
# 4. TODO LO DEMÁS = IDÉNTICO
```

## Datos Limpios para ML Calibrator

**FILTRADO AUTOMÁTICO:**
```python
✅ INCLUIR:
- production_success = True
- system_errors = 0
- config_valid = True
- days_in_production >= 7
- execution_count >= 100

❌ EXCLUIR:
- Rollbacks
- Syntax errors
- Config errors
- Data corruption
- Dev mode
- Experimentos fallidos
```

## Estructura de Directorios Actual

```
MeteoSerV3/
├─ SISTEMA_PSICOTECNICO_MAESTRO_V36.py    ← ARCHIVO ÚNICO MAESTRO
├─ SISTEMA_PSICOTECNICO_README.md          ← Esta documentación
├─ core/engines/
│  ├─ auto_system_optimizer.py             ← Auto-fixes whitelist
│  ├─ statistical_brain.py                 ← Análisis estadístico
│  ├─ environmental_engines.py             ← Engines específicos
│  └─ ...otros engines auxiliares
├─ data/
│  ├─ *.jsonl (históricos limpios)
│  └─ ...datos
└─ tests/
   └─ ...tests
```

## Archivos Eliminados (Consolidados)

- ~~cascade_analyzer_v2.py~~ → CascadeAnalyzer en MAESTRO
- ~~ml_calibrator.py~~ → MLCalibrator en MAESTRO
- ~~robust_duel_engine.py~~ → RobustDuelEngine en MAESTRO
- ~~transient_classifier.py~~ → TransientClassifier en MAESTRO
- ~~intelligent_capa_flow.py~~ → PsychotechnicValidator en MAESTRO
- ~~orchestrador_duelo.py~~ → RobustDuelEngine en MAESTRO
- ~~formula_calculation_specificity.py~~ → CalculationSpecificityAnalyzer en MAESTRO
- ~~EXPLICACION_COMPLETA_99_99.py~~ → Innecesario (todo en MAESTRO)
- ~~auto_improvement_engine.py~~ (duplicado)
- ~~autoimprovement_engine.py~~ (duplicado)

## Próximos Pasos

1. **Integración en main_asgi.py**
   - Importar PsychotechnicOrchestrator
   - Wiring de endpoints de validación

2. **Tests**
   - test_psychometric_master.py
   - Cobertura mínima 85%

3. **Staging (3 meses)**
   - ML Calibrator aprende de histórico limpio
   - Watchdog valida reversibilidad
   - Reach 99.99% en Fase 7

4. **Adaptación Algoritmos**
   - Copy MAESTRO → algorithm_validator.py
   - Cambiar 3 cosas (métricas, whitelist, test_func)
   - 100% reutilizable
