# 🔄 Sistema Automático de Descubrimiento y Duelo de Fórmulas

## Visión General

El MeteoSerV3 ahora tiene un **sistema de mejora automática continua** que:

1. **Busca** fórmulas externas mejores en librerías científicas (scipy, scikit-learn, statsmodels)
2. **Valida** cada candidata contra criterios rigurosos
3. **Duelo**: Compara candidata externa vs. interna actual con datos reales
4. **Integra**: Si externa gana, se integra automáticamente en FORMULA_HIERARCHY
5. **Registra**: Todo queda auditable con logs y histórico

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│  FormulaOptimizationOrchestrator                            │
│  (Director: orquesta todo el flujo)                         │
└─────────────────────────────────────────────────────────────┘
              │
              ├─→ ExternalFormulaDiscoverer
              │   (🔍 Busca candidatas externas)
              │   Inputs: parametro, inputs_disponibles
              │   Outputs: candidatas_validas[]
              │
              ├─→ AutomatedDuelEngine
              │   (⚔️ Duelos auténticos)
              │   Inputs: fn_interna, fn_externa, datos_prueba
              │   Outputs: ganadora, score, margen
              │
              └─→ ExternalFormulaIntegrator
                  (🔧 Integración de ganadora)
                  Inputs: candidata ganadora
                  Outputs: wrapper registrado + integrado
```

---

## Flujo Detallado

### 1️⃣ DESCUBRIMIENTO (ExternalFormulaDiscoverer)

**Objetivo**: Encontrar fórmulas externas candidatas para cada parámetro.

**Estrategia**: Mapeo manual de parámetros → funciones de librerías científicas.

Ejemplos:
- `sensacion_termica` → `scipy.optimize.curve_fit`, `scipy.stats.norm`, `sklearn.ensemble.GradientBoostingRegressor`
- `humedad_relativa` → `scipy.special.erf`, `sklearn.preprocessing.StandardScaler`, `statsmodels.tsa.seasonal.seasonal_decompose`
- `punto_rocio` → `scipy.interpolate.interp1d`, `sklearn.pipeline.Pipeline`, `statsmodels.formula.api.ols`

**Validación de candidata**:
1. ¿La función existe en la librería?
2. ¿Se puede importar sin errores?
3. ¿Es ejecutable?
4. Calcular score de ejecutabilidad (0-100)

**Salida**: Lista de candidatas válidas con score de validación.

```python
from core.monitoring.external_formula_discoverer import ExternalFormulaDiscoverer

discoverer = ExternalFormulaDiscoverer()
candidatas, resultado = discoverer.discover_for_parameter(
    parametro="sensacion_termica",
    inputs_disponibles=["temperatura", "velocidad_viento", "humedad_relativa"]
)

for cand in candidatas:
    print(f"✅ {cand.nombre} (score: {cand.score_validacion:.2f})")
```

---

### 2️⃣ DUELO AUTOMATIZADO (AutomatedDuelEngine)

**Objetivo**: Comparar candidata externa vs. interna actual con datos reales.

**Métricas**: 
- `precision_mae`: Mean Absolute Error
- `precision_rmse`: Root Mean Squared Error
- `precision_r2`: Coeficiente de determinación (0-1)
- `robustez_score`: % de ejecuciones sin error
- `estabilidad_score`: Consistencia de outputs
- `tiempo_ejecucion`: Velocidad

**Score Final** (ponderado):
```
score = R² * 40% + (1 - MAE) * 25% + Robustez * 20% + Estabilidad * 15%
```

**Ganadora**: 
- Externa gana si: `score_externa > score_interna + 5.0`
- Si scores cercanos (diff < 5): conservar interna (principio de cautela)

```python
from core.monitoring.automated_duel_engine import AutomatedDuelEngine

duel_engine = AutomatedDuelEngine()

resultado = duel_engine.duelo(
    parametro="sensacion_termica",
    interna=formula_interna_actual,
    interna_id="sensacion_termica_v1",
    externa=formula_externa_candidata,
    externa_id="scipy_sensacion_termica_0",
    externa_nombre="scipy.special.erf",
    datos_prueba=[
        {"temperatura": 25, "velocidad_viento": 10, ...},
        {"temperatura": 30, "velocidad_viento": 15, ...},
        ...
    ],
    valores_esperados=[18.5, 22.3, ...]  # ground-truth opcional
)

print(f"Ganadora: {resultado.ganadora}")
print(f"Score ganadora: {resultado.score_ganadora:.2f}")
print(f"Margen: {resultado.margen_victoria:.2f}")
```

---

### 3️⃣ INTEGRACIÓN (ExternalFormulaIntegrator)

**Objetivo**: Si externa gana, integrarla en el sistema.

**Proceso**:
1. Generar **wrapper** compatible con FORMULA_HIERARCHY
2. Guardar wrapper en `core/monitoring/external_wrappers/`
3. Validar que sea importable
4. Registrar integración en `data/integrated_external_formulas.json`

**Wrapper generado automáticamente**:
```python
# external_sensacion_termica_scipy_sensacion_termica_0.py
def external_sensacion_termica_scipy_sensacion_termica_0(temperatura, velocidad_viento, ...):
    """Wrapper de ganadora externa integrada."""
    from scipy.special import erf
    
    resultado = erf(temperatura / 30.0) * 30.0
    
    return {
        "valor": float(resultado),
        "metadata": {
            "fuente": "externa",
            "wrapper": "external_sensacion_termica_...",
            "parametro": "sensacion_termica"
        }
    }
```

```python
from core.monitoring.external_formula_integrator import ExternalFormulaIntegrator

integrator = ExternalFormulaIntegrator()

success = integrator.integrar_ganadora(
    parametro="sensacion_termica",
    externa_id="scipy_sensacion_termica_0",
    externa_nombre="scipy.special.erf",
    externa_ref="scipy.special.erf",
    inputs_requeridos=["temperatura"],
    score_duelo=85.5,
    metadata={"margen_victoria": 12.3}
)

if success:
    info = integrator.obtener_info_integrada("sensacion_termica")
    print(f"✅ Integrada: {info['wrapper_id']}")
```

---

### 4️⃣ ORQUESTACIÓN (FormulaOptimizationOrchestrator)

**Objetivo**: Ejecutar el flujo completo en ciclos periódicos.

**Ciclo**:
```
1. Para cada parámetro en lista de prioridad:
   a. Descubrir candidatas externas
   b. Validar
   c. Para cada candidata válida:
      i. Ejecutar duelo
      ii. Si externa gana y score > umbral:
          - Integrar ganadora
   d. Registrar resultado

2. Guardar estadísticas del ciclo
3. Repetir después de intervalo configurado
```

**Configuración** (`data/optimization_config.json`):
```json
{
  "enabled": true,
  "intervalo_minutos": 60,
  "parametros_prioridad": [
    "sensacion_termica",
    "humedad_relativa",
    "punto_rocio",
    "indice_calor",
    "radiacion_solar"
  ],
  "minimo_score_ganadora_externa": 75.0,
  "minimo_margen_victoria": 5.0,
  "max_candidatas_por_parametro": 5
}
```

```python
from core.monitoring.formula_optimization_orchestrator import FormulaOptimizationOrchestrator

orchestrator = FormulaOptimizationOrchestrator()

# Ejecutar un ciclo
ciclo = orchestrator.ejecutar_ciclo(
    parametros=["sensacion_termica", "humedad_relativa"],
    datos_prueba=None  # Genera dummy data
)

print(f"Ciclo #{ciclo.ciclo_num}:")
print(f"  Candidatas descubiertas: {ciclo.candidatas_descubiertas}")
print(f"  Duelos ejecutados: {ciclo.duelos_ejecutados}")
print(f"  Ganadoras integradas: {ciclo.integraciones_exitosas}")

# Estadísticas
stats = orchestrator.obtener_estadisticas()
print(f"Total integraciones: {stats['ganadoras_integradas']}")
```

---

## Archivos de Persistencia

| Archivo | Propósito |
|---------|-----------|
| `data/external_candidates.json` | Candidatas descubiertas |
| `data/discovery_results.json` | Histórico de descubrimientos |
| `data/duel_results.json` | Resultados de todos los duelos |
| `data/integrated_external_formulas.json` | Fórmulas externas integradas |
| `data/formula_integration_log.json` | Log de integraciones |
| `data/optimization_cycles.json` | Histórico de ciclos |
| `data/optimization_config.json` | Configuración del sistema |
| `core/monitoring/external_wrappers/` | Wrappers de ganadoras externas |

---

## Ejemplo Completo

```python
#!/usr/bin/env python3
from core.monitoring.formula_optimization_orchestrator import FormulaOptimizationOrchestrator

# 1. Inicializar orquestador
orchestrator = FormulaOptimizationOrchestrator()

# 2. Ejecutar ciclo
ciclo = orchestrator.ejecutar_ciclo()

# 3. Ver resultados
for detalle in ciclo.detalles:
    print(f"Parámetro: {detalle['parametro']}")
    print(f"Status: {detalle['status']}")
    if detalle['status'] == 'integrada':
        print(f"✅ Ganadora integrada: {detalle['candidata']}")
    elif detalle['status'] == 'perdio_duelo':
        print(f"❌ Perdió duelo: {detalle['candidata']}")
```

**Salida esperada**:
```
🔄 CICLO DE OPTIMIZACIÓN #1
   📋 Procesando: sensacion_termica
   🔍 Descubiertas 5 candidatas para sensacion_termica
   ✅ scipy.special.erf validada (score: 92.0)
   ✅ sklearn.ensemble.GradientBoostingRegressor validada (score: 88.5)
   ⚔️ DUELO: sensacion_termica
      Interna: sensacion_termica_v1
      Externa: scipy.special.erf
   🏆 GANADORA: EXTERNAL (score: 87.3 vs 72.1)
   🔧 Integrando ganadora...
   ✅ Ganadora integrada exitosamente
   
   📋 Procesando: humedad_relativa
   ...

✅ CICLO #1 COMPLETADO
   Parámetros procesados: 5
   Candidatas descubiertas: 23
   Duelos ejecutados: 12
   Ganadoras integradas: 3
```

---

## Características Clave

✅ **Totalmente automático**: Sin intervención manual requerida  
✅ **Auditable**: Todo queda registrado con timestamps y detalles  
✅ **Seguro**: Conservar interna si scores muy cercanos (cautela)  
✅ **Escalable**: Puede añadirse más librerías y candidatas  
✅ **Configurable**: Umbrales, parámetros, intervalo de ejecución  
✅ **Recuperable**: Histórico completo de ciclos y duelos  
✅ **Integrado**: Wrappers se registran automáticamente en el sistema  

---

## Próximos Pasos (Roadmap)

1. ✅ **Motor de descubrimiento**: Implementado
2. ✅ **Validador de candidatas**: Implementado
3. ✅ **Motor de duelo**: Implementado
4. ✅ **Integrador**: Implementado
5. ✅ **Orquestador**: Implementado
6. ⏳ **Scheduler automático**: Ejecutar periódicamente (en background)
7. ⏳ **Dashboard**: Visualizar ciclos y resultados en tiempo real
8. ⏳ **Feedback loop**: Mejorar candidatas basado en resultados

---

## Conclusión

MeteoSerV3 ahora es un **"Acorazado de Hierro"** que:
- 🔍 **Busca** activamente mejores fórmulas
- ✅ **Valida** cada candidata rigurosa y auditablemente
- ⚔️ **Compite** en duelos justos
- 🏆 **Integra** ganadoras automáticamente
- 📊 **Registra** todo para trazabilidad

**El sistema mejora continuamente sin intervención manual.**
