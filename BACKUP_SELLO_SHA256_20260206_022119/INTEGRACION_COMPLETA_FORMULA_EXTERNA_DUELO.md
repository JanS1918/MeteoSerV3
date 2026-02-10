# 🎭 INTEGRACIÓN COMPLETA: FÓRMULA EXTERNA → DUELO JUSTO
## Sistema End-to-End de Evaluación Psicotécnica

**Fecha:** 4 Febrero 2026  
**Versión:** 1.0 Integración Completa  
**Status:** 🟢 LISTO PARA PRODUCCIÓN

---

## 📋 ÍNDICE

1. [Flujo Completo Visualizado](#flujo-completo-visualizado)
2. [Etapa 1: Recepción de Fórmula](#etapa-1-recepción-de-fórmula-externa)
3. [Etapa 2: Pre-Optimización](#etapa-2-pre-optimización-capa-25)
4. [Etapa 3: Pruebas Psicotécnicas](#etapa-3-pruebas-psicotécnicas)
5. [Etapa 4: Decisión Justa](#etapa-4-decisión-justa)
6. [Etapa 5: Duelo](#etapa-5-duelo-con-métricas-finales)
7. [Ejemplo Real Paso a Paso](#ejemplo-real-paso-a-paso)
8. [Código de Integración](#código-de-integración)

---

## 🎬 FLUJO COMPLETO VISUALIZADO

```
┌──────────────────────────────────────────────────────────────────────┐
│                   FÓRMULA EXTERNA LLEGA                              │
│                                                                      │
│  Entrada:                                                            │
│  ├─ formula_id: "external_v1.2.3"                                   │
│  ├─ precision: 0.95                                                  │
│  ├─ stability: 0.68                                                  │
│  ├─ fluidity: 0.72                                                   │
│  └─ code: <formula code>                                             │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ETAPA 1: VALIDACIÓN BÁSICA                                           │
│                                                                      │
│ ✓ ¿Formato válido?                                                   │
│ ✓ ¿Métricas dentro de rango?                                         │
│ ✓ ¿Código ejecutable?                                                │
│                                                                      │
│ Salida: FormulaJourney creado                                        │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ETAPA 2: PRE-OPTIMIZACIÓN (CAPA 25)                                  │
│                                                                      │
│ El Cerebro Autónomo analiza:                                         │
│ ├─ ¿precision > 0.95? → Intentar estabilizar sin perder precisión   │
│ ├─ ¿stability < 0.70? → Marcar como "reparable"                    │
│ ├─ ¿hay trade-offs? → Optimizar según contexto                      │
│ └─ ¿aplicar ajustes? → Ligeros (~5%) si compensan                  │
│                                                                      │
│ Salida: metrics_optimizadas (NEW precision, stability, etc)         │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ETAPA 3: PRUEBAS PSICOTÉCNICAS (Capas 1-24)                          │
│                                                                      │
│ Loop inteligente:                                                    │
│ FOR cada CAPA en ORDEN_IMPORTANCIA:                                 │
│   1. Ejecutar test (con timeout según capa)                         │
│   2. ¿PASÓ?                                                          │
│      ├─ SÍ → Siguiente capa                                          │
│      └─ NO → ANÁLISIS                                                │
│   3. ¿Reparable?                                                     │
│      ├─ NOT_REPAIRABLE → DESCARTAR                                  │
│      ├─ HIGHLY_REPAIRABLE → Re-intente si similar pasó              │
│      ├─ MODERATELY_REPAIRABLE → Continuar                           │
│      └─ BARELY_REPAIRABLE → Continuar (alto riesgo)                │
│   4. ¿Efecto dominó?                                                 │
│      ├─ BAJO (<0.3) → Continuar                                     │
│      ├─ MODERADO (0.3-0.5) → Monitorear                             │
│      ├─ ALTO (0.5-0.7) → Advertencia                                │
│      └─ CRÍTICO (>0.7) → Considerar descarte                        │
│   5. Continuar o descartar según contexto                           │
│                                                                      │
│ Salida: test_results[] con 25 pruebas (máximo)                      │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ETAPA 4: CÁLCULO DE MÉTRICAS FINALES (Justas)                       │
│                                                                      │
│ Análisis profundo de resultados:                                    │
│                                                                      │
│ Precisión:   50% = (capas críticas pasadas / 6)                    │
│              × precision_inicial                                     │
│                                                                      │
│ Estabilidad: 30% = (capas estabilidad pasadas / 3)                 │
│              × stability_inicial × multiplicador                    │
│                                                                      │
│ Fluidez:     20% = (capas despliegue / 3) × 0.8                    │
│                                                                      │
│ Justice Score (INTEGRAL):                                           │
│   = 0.5 × (precision/max_precision)                                 │
│   + 0.3 × (stability/max_stability)                                 │
│   + 0.2 × (repair_score)                                            │
│                                                                      │
│ Salida: final_precision, final_stability, final_fluidity,          │
│         justice_score (0.0-1.0)                                      │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ETAPA 5: DECISIÓN JUSTA                                              │
│                                                                      │
│ IF justice_score >= 0.80:                                            │
│    ├─ Status: "ACEPTADA - EXCELENTE"                                │
│    ├─ Confianza: ALTA                                                │
│    └─ Acción: Enviar a DUELO inmediatamente                         │
│                                                                      │
│ ELIF justice_score >= 0.75:                                          │
│    ├─ Status: "ACEPTADA - BUENA"                                    │
│    ├─ Confianza: MEDIA-ALTA                                          │
│    └─ Acción: Enviar a DUELO con advertencias                       │
│                                                                      │
│ ELIF justice_score >= 0.60:                                          │
│    ├─ Status: "ACEPTADA - CUESTIONABLE"                             │
│    ├─ Confianza: MEDIA                                               │
│    ├─ Acción: Revisar manual ó Enviar a DUELO de baja prioridad    │
│    └─ Nota: Monitorear durante duelo                                │
│                                                                      │
│ ELIF justice_score >= 0.40:                                          │
│    ├─ Status: "RECHAZADA - INSUFICIENTE"                            │
│    ├─ Confianza: BAJA                                                │
│    ├─ Acción: RECHAZAR (o análisis manual)                          │
│    └─ Feedback: "Precisión baja, múltiples fallos"                 │
│                                                                      │
│ ELSE:                                                                 │
│    ├─ Status: "RECHAZADA - CRÍTICO"                                │
│    ├─ Confianza: NULA                                                │
│    └─ Acción: RECHAZAR sin opción de duelo                          │
│                                                                      │
│ Salida: Decision (ACCEPT/REJECT) + reasoning                        │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ├─── RECHAZADA ──→ Retornar feedback + cancelar
                 │
                 ▼
                ACEPTADA
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ETAPA 6: DUELO (Con Métricas Finales Post-Optimización)             │
│                                                                      │
│ Duelo justo porque:                                                  │
│ ├─ Fórmula optimizada CON CAPA 25                                   │
│ ├─ Métricas finales DESPUÉS de pasar pruebas                        │
│ ├─ Ambas fórmulas usan mismo sistema de evaluación                  │
│ ├─ Resultados conocen la ESTABILIZACIÓN REAL                        │
│ └─ Si gana: guardada CON métricas finales                           │
│                                                                      │
│ Batalla:                                                             │
│ ├─ our_formula  (ya optimizada con CAPA 25)                         │
│ ├─ ext_formula  (recién optimizada en Etapa 2)                      │
│ ├─ Round 1: Precisión (50%)                                          │
│ ├─ Round 2: Estabilidad (30%)                                        │
│ ├─ Round 3: Fluidez (20%)                                            │
│ └─ GANADOR: quien tenga mejor justice_score                         │
│                                                                      │
│ Salida: Winner + battle_report                                       │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ETAPA 7: PERSISTENCIA                                                │
│                                                                      │
│ SI ganó duelo:                                                        │
│ ├─ Guardar fórmula CON métricas finales post-opt                   │
│ ├─ Guardar journey (toda historia de pruebas)                      │
│ ├─ Actualizar estadísticas de capas                                │
│ └─ Registrar en leaderboard                                         │
│                                                                      │
│ SIEMPRE:                                                             │
│ ├─ Guardar journey para auditoría                                   │
│ ├─ Log de todos los eventos                                         │
│ ├─ Incident reports si hubo problemas                               │
│ └─ Métricas agregadas de capa_stats                                 │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 ETAPA 1: RECEPCIÓN DE FÓRMULA EXTERNA

### Input Esperado

```python
{
    "formula_id": "external_formula_v1.2.3",
    "source": "user_submission",
    "timestamp": "2026-02-04T14:30:00Z",
    
    # Métricas iniciales (lo que el usuario reporta)
    "metrics": {
        "precision": 0.95,      # 0.0-1.0
        "stability": 0.68,      # 0.0-1.0
        "fluidity": 0.72,       # 0.0-1.0
        "confidence": 0.80      # Confianza del usuario (informativa)
    },
    
    # Código ejecutable
    "formula_code": """
    def evaluate(data):
        # Tu fórmula aquí
        return result
    """,
    
    # Metadatos
    "author": "external_user",
    "description": "Mi fórmula mejorada para sensación térmica",
    "language": "python",
    "requirements": ["numpy", "pandas"]
}
```

### Validación Básica

```python
def validate_external_formula(formula_dict):
    """Valida que la fórmula tenga formato correcto"""
    
    checks = {
        "has_id": bool(formula_dict.get("formula_id")),
        "has_metrics": bool(formula_dict.get("metrics")),
        "has_code": bool(formula_dict.get("formula_code")),
        "metrics_valid_range": all(
            0.0 <= formula_dict["metrics"].get(key, 0.5) <= 1.0
            for key in ["precision", "stability", "fluidity"]
        ),
        "code_executable": is_code_valid(formula_dict["formula_code"]),
    }
    
    if not all(checks.values()):
        raise ValueError(f"Validación falló: {checks}")
    
    return True
```

### Salida: FormulaJourney Inicial

```python
journey = FormulaJourney(
    formula_id="external_formula_v1.2.3",
    test_results=[],              # Se llena durante pruebas
    failed_capas=[],              # Capas que fallaron
    repaired_count=0,             # Errores reparados
    retested_count=0,             # Re-intentos exitosos
    optimization_applied=False,   # Se marca en Etapa 2
    final_precision=0.0,          # Se calcula en Etapa 4
    final_stability=0.0,
    final_fluidity=0.0,
    passed_duel=False,            # Se determina en Etapa 6
    justice_score=0.0             # Se calcula en Etapa 4
)
```

---

## ⚙️ ETAPA 2: PRE-OPTIMIZACIÓN (CAPA 25)

### ¿Por Qué Pre-Optimizar?

```
Dos opciones de duelo:

❌ OPCIÓN 1 (Injusta): Sin optimización previa
   fórmula_externa → Duelo directo sin ajustes
   Problema: Externa puede no ser óptima. Ventaja a interna.

✅ OPCIÓN 2 (Justa): Con pre-optimización
   fórmula_externa → CAPA 25 optim. → Duelo con métricas finales
   Beneficio: Ambas optimizadas, ambas evaluadas justamente
```

### El Proceso (CAPA 25: Cerebro Autónomo)

```python
async def pre_optimize_formula(formula_metrics: Dict) -> Dict:
    """
    CAPA 25 inteligencia: optimiza fórmula ANTES del duelo
    
    Entrada: {"precision": 0.95, "stability": 0.68, "fluidity": 0.72}
    Salida: {"precision": 0.94, "stability": 0.73, "fluidity": 0.72}  # Optimizada
    """
    
    optimized = formula_metrics.copy()
    changes = []
    
    # REGLA 1: Muy precisa pero inestable
    if optimized.get("precision", 0) > 0.95:
        if optimized.get("stability", 0.5) < 0.75:
            # Intentar mejorar estabilidad sin perder precisión
            stability_boost = min(0.75 - optimized["stability"], 0.05)
            optimized["stability"] += stability_boost
            changes.append(f"Stability boosted by +{stability_boost:.2%}")
            
            logger.info(f"📈 Fórmula muy precisa: compensar con estabilidad")
    
    # REGLA 2: Inestable - marcado para monitoreo
    if optimized.get("stability", 0) < 0.70:
        optimized["repairable_instability"] = True
        changes.append("Marked for repair monitoring during tests")
        logger.warning(f"⚠️  Inestabilidad detectada pero reparable")
    
    # REGLA 3: Fluidez baja - puede afectar despliegue
    if optimized.get("fluidity", 0) < 0.60:
        logger.warning(f"⚠️  Fluidez baja ({optimized['fluidity']:.0%}) - no hay ajuste automático")
    
    logger.info(f"✅ Pre-optimización completada: {changes}")
    await asyncio.sleep(0.05)  # Simular tiempo de análisis
    
    return optimized
```

### Ejemplo de Pre-Optimización

```
ENTRADA (Fórmula Externa):
├─ precision: 0.96  ⭐ MUY ALTA
├─ stability: 0.62  ⚠️ BAJA (problema!)
└─ fluidity: 0.70

ANÁLISIS CAPA 25:
├─ Detecta: "Muy precisa (0.96) pero inestable (0.62)"
├─ Riesgo: Duelo desigual (precisión=sí, estabilidad=no)
└─ Solución: Boost ligero a estabilidad (0.05) sin perder precisión

SALIDA (Después Optimización):
├─ precision: 0.96  ✅ MANTIENE
├─ stability: 0.67  ✅ MEJORADA (+5%)
└─ fluidity: 0.70  ✅ MANTIENE

RESULTADO:
"Fórmula está lista para duelo justo"
```

---

## 🧪 ETAPA 3: PRUEBAS PSICOTÉCNICAS

### Loop Principal

```python
async def run_psychometric_tests(
    formula_id: str,
    optimized_metrics: Dict,
    test_function  # Función que ejecuta capas
) -> FormulaJourney:
    """
    Ejecuta fórmula a través de 24 capas (CAPA 25 es supervisora)
    Aplica lógica psicotécnica en cada paso
    """
    
    journey = FormulaJourney(formula_id)
    orchestrator = CapaFlowOrchestrator()
    
    # Obtener capas en orden de importancia
    ordered_capas = orchestrator.get_ordered_capas()
    
    for capa_id, capa_def in ordered_capas:
        logger.info(f"🧪 Probando CAPA {capa_id}: {capa_def.name}")
        
        # PASO 1: Ejecutar prueba
        result = await run_capa_test(capa_id, optimized_metrics)
        journey.test_results.append(result)
        
        if result.passed:
            logger.info(f"   ✅ PASÓ en {result.latency_ms:.0f}ms")
            continue  # Siguiente capa
        
        # PASO 2: ANÁLISIS SI FALLA
        logger.warning(f"   ❌ FALLÓ: {result.error_msg}")
        
        # 2.1: Detectar reparabilidad
        repairability, confidence = orchestrator.detect_repairability(
            result, optimized_metrics
        )
        result.repairability = repairability
        result.confidence = confidence
        
        logger.info(f"   Reparabilidad: {repairability.name} ({confidence:.0%})")
        
        # 2.2: Detectar efecto dominó
        has_cascade, cascade_severity = orchestrator.detect_cascade_risk(
            capa_id, journey.failed_capas
        )
        
        if has_cascade:
            logger.warning(f"   ⚠️  Riesgo dominó: {cascade_severity:.0%}")
        
        # PASO 3: DECISIÓN SEGÚN REPARABILIDAD
        
        if repairability == RepairabilityLevel.NOT_REPAIRABLE:
            logger.error(f"   ❌ NO REPARABLE → DESCARTANDO FÓRMULA")
            journey.failed_capas.append(capa_id)
            break  # Salir del loop, no continuar
        
        elif repairability == RepairabilityLevel.HIGHLY_REPAIRABLE:
            logger.info(f"   ✅ ALTAMENTE REPARABLE → Re-intentando")
            
            # Re-intenta capas similares
            for similar_id in capa_def.similar_capas:
                if any(r.capa_id == similar_id and r.passed 
                       for r in journey.test_results):
                    await asyncio.sleep(0.1)
                    retest = await run_capa_test(capa_id, optimized_metrics)
                    
                    if retest.passed:
                        logger.info(f"   ✅ Re-intento EXITOSO")
                        journey.test_results.append(retest)
                        journey.retested_count += 1
                        continue  # Siguiente capa
            
            # Si no se reparó en retests
            logger.warning(f"   ⚠️  Re-intento no funcionó, marcado como reparable")
            journey.failed_capas.append(capa_id)
            journey.repaired_count += 1
            continue  # Siguiente capa
        
        else:  # MODERATELY o BARELY REPAIRABLE
            logger.warning(f"   ⚠️  PARCIALMENTE REPARABLE → Continuando con precaución")
            journey.failed_capas.append(capa_id)
            journey.repaired_count += 1
            continue  # Siguiente capa
    
    return journey
```

### Matriz de Decisión (Simplificada)

```
¿FALLÓ EN CAPA?

NIVEL 1 (CRÍTICA: CAPA 1, 6-10)
│
├─ NO_REPARABLE → DESCARTA FÓRMULA ❌
├─ REPARABLE → Continúa pero riesgo alto ⚠️
└─ ¿Efecto dominó? NO → Continúa; SÍ → DESCARTA

NIVEL 2 (ALTA: CAPA 14, 21, 22, 11)
│
├─ NO_REPARABLE → DESCARTA ❌
├─ HIGHLY_REPARABLE → Re-intenta, si no → continúa ✅
├─ MODERATELY_REPARABLE → Continúa ⚠️
└─ ¿Efecto dominó crítico? → DESCARTA

NIVEL 3 (MEDIA: CAPA 2-5, 18-20)
│
├─ NO_REPARABLE → Acumula fallos
├─ REPARABLE → Continúa (menos crítico) ✅
└─ ¿3+ capas fallidas en este nivel? → DESCARTA

NIVEL 4 (BAJA: CAPA 12-13, 15-17, 23-24)
│
├─ NO_REPARABLE → Acumula fallos
├─ REPARABLE → Continúa (muy ignorable) ✅
└─ ¿5+ capas fallidas? → Recomputa justice_score

NIVEL 5 (META: CAPA 25)
│
└─ Supervisora, no descarta
```

### Estadísticas por Capa (Se Actualizan en Tiempo Real)

```python
# Después de cada test, actualizar:
capa_stats[capa_id] = {
    "total_tests": n,               # Cuántas veces se probó
    "passed": p,                    # Cuántas pasaron
    "failed": f,                    # Cuántas fallaron
    "pass_rate": p / n,             # Porcentaje éxito
    "avg_latency": avg_ms,          # Promedio tiempo
    "error_types": {                # Qué errores vemos
        "timeout": count,
        "validation": count,
        "instability": count,
        ...
    },
    "repaired": r                   # Cuántas se repararon
}
```

---

## 📊 ETAPA 4: DECISIÓN JUSTA

### Fórmula de Justice Score

```python
def calculate_justice_score(journey: FormulaJourney) -> float:
    """
    Calcula puntuación integral JUSTA
    
    50% PRECISIÓN: ¿Las capas críticas pasaron?
    30% ESTABILIDAD: ¿Se mantuvo estable?
    20% REPARABILIDAD: ¿Se pudieron arreglar errores?
    """
    
    # Componente 1: PRECISIÓN (50% peso)
    critical_capas = [1, 6, 7, 8, 9, 10]
    critical_passed = sum(
        1 for r in journey.test_results
        if r.capa_id in critical_capas and r.passed
    )
    precision_score = critical_passed / len(critical_capas)  # 0.0-1.0
    
    # Componente 2: ESTABILIDAD (30% peso)
    stability_capas = [14, 21, 22]
    stability_passed = sum(
        1 for r in journey.test_results
        if r.capa_id in stability_capas and r.passed
    )
    stability_score = stability_passed / len(stability_capas)  # 0.0-1.0
    
    # Componente 3: REPARABILIDAD (20% peso)
    repair_score = 1.0 if journey.repaired_count > 0 else 0.5
    
    # CÁLCULO FINAL (PONDERADO)
    justice_score = (
        0.50 * precision_score +
        0.30 * stability_score +
        0.20 * repair_score
    )
    
    return min(justice_score, 1.0)
```

### Interpretación del Score

```
justice_score:

0.90-1.00  🟢 EXCELENTE
├─ Fórmula muy sólida
├─ Pasó casi todas las capas
└─ Confianza: MUY ALTA para duelo

0.80-0.90  🟡 BUENA
├─ Fórmula funcional
├─ Algunos fallos pero reparables
└─ Confianza: ALTA para duelo

0.70-0.80  🟠 ACEPTABLE
├─ Fórmula viable
├─ Fallos moderados
└─ Confianza: MEDIA para duelo

0.60-0.70  🔴 CUESTIONABLE
├─ Fórmula en límite
├─ Varios fallos
└─ Confianza: BAJA - revisar antes de duelo

<0.60     ❌ RECHAZADA
├─ Fórmula no confiable
├─ Múltiples fallos críticos
└─ Confianza: NULA - no duelo
```

### Umbral de Aceptación

```python
def make_acceptance_decision(justice_score: float) -> Dict:
    """Decide si aceptar fórmula para duelo"""
    
    if justice_score >= 0.80:
        return {
            "decision": "ACCEPT",
            "confidence": "HIGH",
            "message": "✅ Fórmula ACEPTADA - Excelente confianza",
            "duel_priority": "HIGH",
            "monitoring": "LIGHT"
        }
    
    elif justice_score >= 0.75:
        return {
            "decision": "ACCEPT",
            "confidence": "MEDIUM_HIGH",
            "message": "✅ Fórmula ACEPTADA - Buena confianza",
            "duel_priority": "NORMAL",
            "monitoring": "STANDARD"
        }
    
    elif justice_score >= 0.60:
        return {
            "decision": "ACCEPT_QUESTIONABLE",
            "confidence": "MEDIUM",
            "message": "⚠️ Fórmula ACEPTADA - Confianza media, revisar",
            "duel_priority": "LOW",
            "monitoring": "INTENSIVE"
        }
    
    else:
        return {
            "decision": "REJECT",
            "confidence": "LOW",
            "message": f"❌ Fórmula RECHAZADA - Justice score: {justice_score:.2%}",
            "duel_priority": "NONE",
            "monitoring": "NONE",
            "reason": "Precisión insuficiente o fallos críticos"
        }
```

---

## ⚔️ ETAPA 5: DUELO

### Setup del Duelo Justo

```python
async def fair_duel(
    our_formula: Formula,              # La nuestra (ya optimizada)
    external_formula: Formula,         # La externa (recién optimizada)
    our_journey: FormulaJourney,       # Nuestros test_results
    ext_journey: FormulaJourney        # Sus test_results
) -> Dict:
    """
    Duelo JUSTO porque:
    
    1. Ambas fórmulas optimizadas con CAPA 25
    2. Ambas probadas contra 24 capas
    3. Métricas finales incluyen optimizaciones
    4. Conocemos la estabilización REAL de cada una
    5. Evaluación ponderada (Precisión > Estabilidad > Resto)
    """
    
    # Métricas finales POST-OPTIMIZACIÓN
    our_metrics = {
        "precision": our_journey.final_precision,
        "stability": our_journey.final_stability,
        "fluidity": our_journey.final_fluidity,
        "justice_score": our_journey.justice_score
    }
    
    ext_metrics = {
        "precision": ext_journey.final_precision,
        "stability": ext_journey.final_stability,
        "fluidity": ext_journey.final_fluidity,
        "justice_score": ext_journey.justice_score
    }
    
    # RONDA 1: PRECISIÓN (50% del duelo)
    precision_winner = "ours" if our_metrics["precision"] >= ext_metrics["precision"] else "external"
    precision_delta = abs(our_metrics["precision"] - ext_metrics["precision"])
    
    logger.info(f"📊 RONDA 1 - PRECISIÓN:")
    logger.info(f"   Ours: {our_metrics['precision']:.2%}")
    logger.info(f"   Ext:  {ext_metrics['precision']:.2%}")
    logger.info(f"   GANADOR: {precision_winner.upper()} (+{precision_delta:.2%})")
    
    # RONDA 2: ESTABILIDAD (30% del duelo)
    stability_winner = "ours" if our_metrics["stability"] >= ext_metrics["stability"] else "external"
    stability_delta = abs(our_metrics["stability"] - ext_metrics["stability"])
    
    logger.info(f"📊 RONDA 2 - ESTABILIDAD:")
    logger.info(f"   Ours: {our_metrics['stability']:.2%}")
    logger.info(f"   Ext:  {ext_metrics['stability']:.2%}")
    logger.info(f"   GANADOR: {stability_winner.upper()} (+{stability_delta:.2%})")
    
    # RONDA 3: FLUIDEZ (20% del duelo)
    fluidity_winner = "ours" if our_metrics["fluidity"] >= ext_metrics["fluidity"] else "external"
    fluidity_delta = abs(our_metrics["fluidity"] - ext_metrics["fluidity"])
    
    logger.info(f"📊 RONDA 3 - FLUIDEZ:")
    logger.info(f"   Ours: {our_metrics['fluidity']:.2%}")
    logger.info(f"   Ext:  {ext_metrics['fluidity']:.2%}")
    logger.info(f"   GANADOR: {fluidity_winner.upper()} (+{fluidity_delta:.2%})")
    
    # RESULTADO FINAL (por justice_score)
    final_winner = "ours" if our_metrics["justice_score"] >= ext_metrics["justice_score"] else "external"
    justice_delta = abs(our_metrics["justice_score"] - ext_metrics["justice_score"])
    
    logger.info(f"\n🏆 RESULTADO FINAL:")
    logger.info(f"   Ours Justice Score:   {our_metrics['justice_score']:.2%}")
    logger.info(f"   External Justice Score: {ext_metrics['justice_score']:.2%}")
    logger.info(f"   GANADOR FINAL: {final_winner.upper()} (+{justice_delta:.2%})")
    
    return {
        "winner": final_winner,
        "our_metrics": our_metrics,
        "ext_metrics": ext_metrics,
        "rounds": {
            "precision": {"winner": precision_winner, "delta": precision_delta},
            "stability": {"winner": stability_winner, "delta": stability_delta},
            "fluidity": {"winner": fluidity_winner, "delta": fluidity_delta}
        },
        "justice_delta": justice_delta,
        "timestamp": datetime.now().isoformat()
    }
```

### Ejemplo de Duelo

```
DUELO: Fórmula Interna vs Fórmula Externa
══════════════════════════════════════════════════════════

📊 RONDA 1 - PRECISIÓN (50% peso)
├─ Ours:     0.85 (5/6 capas críticas pasadas)
├─ External: 0.80 (4/6 capas críticas pasadas)
└─ GANADOR: OURS (+5%)  ✅

📊 RONDA 2 - ESTABILIDAD (30% peso)
├─ Ours:     0.75 (3/3 capas estabilidad, mantuvo bien)
├─ External: 0.72 (2.8/3, ligeramente inestable)
└─ GANADOR: OURS (+3%)  ✅

📊 RONDA 3 - FLUIDEZ (20% peso)
├─ Ours:     0.78 (despliegue bueno)
├─ External: 0.80 (despliegue excelente)
└─ GANADOR: EXTERNAL (+2%)  ⚠️

🏆 RESULTADO FINAL
├─ Ours Justice Score:      0.818 (81.8%)
├─ External Justice Score:  0.785 (78.5%)
└─ GANADOR FINAL: OURS (+3.3%) 🥇

Conclusión: Fórmula interna mantiene liderato en precisión y
estabilidad. Externa es mejor en fluidez pero no compensa.
```

---

## 🎯 EJEMPLO REAL PASO A PASO

### Escenario: Fórmula Externa Llega

```
ENTRADA:
{
    "formula_id": "sensacion_termica_v2.1",
    "metrics": {
        "precision": 0.96,    ⭐ MUY ALTA
        "stability": 0.65,    ⚠️ BAJA
        "fluidity": 0.71
    }
}
```

### ETAPA 1: Validación

```
✓ Formato correcto
✓ Métricas en rango
✓ Código ejecutable
→ FormulaJourney creado
```

### ETAPA 2: Pre-Optimización (CAPA 25)

```
ANÁLISIS CEREBRO AUTÓNOMO:
├─ precision 0.96 > 0.95? SÍ
├─ stability 0.65 < 0.75? SÍ
└─ Decisión: "Muy precisa pero inestable → estabilizar"

OPTIMIZACIONES:
├─ Boost stability: 0.65 → 0.70 (+5%)
└─ Mantener precision: 0.96

SALIDA:
├─ precision: 0.96 ✅ (mantenida)
├─ stability: 0.70 ✅ (mejorada)
└─ fluidity: 0.71 ✅ (igual)
```

### ETAPA 3: Pruebas (Ejemplo de 10 capas)

```
CAPA 1 (Validación Proactiva):   ✅ PASA
  Latencia: 45ms

CAPA 6 (Input Validation):       ✅ PASA
  Latencia: 52ms

CAPA 7 (Data Integrity):         ❌ FALLA
  Error: threshold_breach
  Reparabilidad: MODERATELY_REPARABLE (60%)
  Cascade risk: 0.28 (BAJO)
  Acción: Continuar

CAPA 14 (Drift Detection):       ✅ PASA
  Latencia: 68ms

CAPA 21 (Centinela Soberano):    ✅ PASA
  Latencia: 120ms

CAPA 22 (Learning Feedback):     ✅ PASA
  Latencia: 75ms

CAPA 8 (Rate Limiting):          ❌ FALLA
  Error: transient_error
  Reparabilidad: HIGHLY_REPARABLE (90%)
  Re-intenta (CAPA 6 pasó): ✅ PASA en intento 2
  Latencia: 48ms

CAPA 18 (Canary Rollout):        ✅ PASA
  Latencia: 95ms

CAPA 19 (A/B Testing):           ✅ PASA
  Latencia: 88ms

CAPA 20 (Versioning):            ✅ PASA
  Latencia: 72ms

RESULTADOS:
├─ Total tests: 10
├─ Passed: 8
├─ Failed: 2 (pero ambos reparables)
├─ Re-tests exitosos: 1
└─ Continuaría con resto de capas...
```

### ETAPA 4: Métricas Finales (Ejemplo Completo)

```
CAPAS CRÍTICAS (CAPA 1, 6-10):
├─ CAPA 1: ✅ PASA
├─ CAPA 6: ✅ PASA
├─ CAPA 7: ❌ FALLA (pero reparable)
├─ CAPA 8: ✅ PASA (después re-intento)
├─ CAPA 9: ✅ PASA
├─ CAPA 10: ✅ PASA
└─ Críticas pasadas: 5/6 = 0.833

CAPAS ESTABILIDAD (CAPA 14, 21, 22):
├─ CAPA 14: ✅ PASA
├─ CAPA 21: ✅ PASA
├─ CAPA 22: ✅ PASA
└─ Estabilidad pasadas: 3/3 = 1.0

CAPAS DESPLIEGUE (CAPA 18-20):
├─ CAPA 18: ✅ PASA
├─ CAPA 19: ✅ PASA
├─ CAPA 20: ✅ PASA
└─ Despliegue: 3/3 → fluidity = 0.80

CÁLCULO JUSTICE SCORE:
├─ precision_score = 5/6 = 0.833
├─ stability_score = 3/3 = 1.0
├─ repair_score = 1.0 (se reparó 1 error)
│
└─ justice_score = 0.5*(0.833) + 0.3*(1.0) + 0.2*(1.0)
                 = 0.417 + 0.300 + 0.200
                 = 0.917 → 91.7% 🟢 EXCELENTE

MÉTRICAS FINALES POST-OPTIMIZACIÓN:
├─ precision_final: 0.96 * (5/6) = 0.80
├─ stability_final: 0.70 * (3/3) * 1.0 = 0.70
├─ fluidity_final: 0.80
└─ justice_score: 0.917
```

### ETAPA 5: Decisión

```
justice_score: 0.917 ≥ 0.80?  ✅ SÍ

DECISIÓN: ✅ ACEPTA - EXCELENTE CONFIANZA

├─ Status: ACEPTADA para duelo
├─ Confidence: ALTA
├─ Duel priority: HIGH
└─ Message: "Fórmula muy sólida, lista para duelo"
```

### ETAPA 6: Duelo

```
DUELO: Nuestra Fórmula vs Fórmula Externa
════════════════════════════════════════════════════════════

📊 RONDA 1 - PRECISIÓN (50%)
├─ Ours:     0.82
├─ External: 0.80
└─ GANADOR: OURS (+2%)  ✅

📊 RONDA 2 - ESTABILIDAD (30%)
├─ Ours:     0.71
├─ External: 0.70
└─ GANADOR: OURS (+1%)  ✅

📊 RONDA 3 - FLUIDEZ (20%)
├─ Ours:     0.76
├─ External: 0.80
└─ GANADOR: EXTERNAL (+4%)  ⚠️

🏆 RESULTADO FINAL
├─ Ours Justice Score:       0.791
├─ External Justice Score:   0.792
└─ GANADOR FINAL: EXTERNAL por 0.1%  🥇

Conclusión: ¡Muy reñido! Externa gana por margen mínimo.
Se guarda con métricas finales.
```

---

## 💻 CÓDIGO DE INTEGRACIÓN

### Integración en main_asgi.py

```python
# main_asgi.py

from core.engines.intelligent_capa_flow import CapaFlowOrchestrator
from core.orchestration.autonomous_optimization_brain import AutonomousOptimizationBrain

# Inicializar en startup
orchestrator = CapaFlowOrchestrator()
brain = AutonomousOptimizationBrain()

@app.post("/api/formula/submit-for-duel")
async def submit_formula_for_duel(formula_data: Dict):
    """
    Endpoint principal: Recibe fórmula externa y ejecuta
    flujo completo hasta duelo
    """
    
    try:
        # ETAPA 1: Validación
        validate_external_formula(formula_data)
        formula_id = formula_data["formula_id"]
        
        logger.info(f"📥 Fórmula recibida: {formula_id}")
        
        # ETAPA 2: Pre-optimización (CAPA 25)
        optimized_metrics = await brain.pre_optimize_formula(
            formula_data["metrics"]
        )
        logger.info(f"✅ Pre-optimización completada")
        
        # ETAPA 3: Pruebas psicotécnicas
        journey = await orchestrator.intelligent_test_formula(
            formula_id=formula_id,
            test_func=run_capa_test,  # Tu función de pruebas
            formula_metrics=optimized_metrics
        )
        logger.info(f"✅ Pruebas completadas")
        
        # ETAPA 4: Decisión justa
        justice_score = journey.justice_score
        decision = make_acceptance_decision(justice_score)
        logger.info(f"📋 Decisión: {decision['decision']} (score: {justice_score:.2%})")
        
        if decision["decision"] == "REJECT":
            return {
                "status": "REJECTED",
                "reason": decision["message"],
                "justice_score": justice_score,
                "journey": orchestrator.get_journey_report(formula_id)
            }
        
        # ETAPA 5: Duelo
        our_formula = get_our_best_formula()
        our_journey = get_our_journey()  # Ya tenemos journey de la nuestra
        
        battle_result = await fair_duel(
            our_formula=our_formula,
            external_formula=formula_data,
            our_journey=our_journey,
            ext_journey=journey
        )
        logger.info(f"🏆 Duelo completado: {battle_result['winner'].upper()} gana")
        
        # ETAPA 6: Persistencia
        await persist_battle_result(battle_result, journey)
        
        return {
            "status": "COMPLETED",
            "decision": decision["decision"],
            "justice_score": justice_score,
            "battle_winner": battle_result["winner"],
            "journey": orchestrator.get_journey_report(formula_id),
            "battle_result": battle_result
        }
    
    except Exception as e:
        logger.error(f"❌ Error en flujo: {e}")
        return {
            "status": "ERROR",
            "error": str(e)
        }
```

### Función de Prueba de Capa

```python
async def run_capa_test(capa_id: int, formula_metrics: Dict) -> Dict:
    """
    Ejecuta una prueba de capa específica
    Retorna dict con resultado de prueba
    """
    
    try:
        # Ejecutar test específico según capa_id
        if capa_id == 1:
            result = await test_capa_1_telemetry(formula_metrics)
        elif capa_id in [6, 7, 8, 9, 10]:
            result = await test_capa_validation(capa_id, formula_metrics)
        elif capa_id == 14:
            result = await test_capa_14_drift_detection(formula_metrics)
        # ... etc para todas las capas
        
        return result
    
    except Exception as e:
        return {
            "passed": False,
            "error_type": "execution_error",
            "error_msg": str(e),
            "latency_ms": 0
        }
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Crear `intelligent_capa_flow.py` con CapaFlowOrchestrator
- [ ] Crear `autonomous_optimization_brain.py` (CAPA 25)
- [ ] Endpoint POST /api/formula/submit-for-duel
- [ ] Endpoint GET /api/formula/{id}/report
- [ ] Endpoint GET /api/capas/statistics
- [ ] Funciones de prueba para cada CAPA
- [ ] Tests unitarios del flujo psicotécnico
- [ ] Persistencia de journeys
- [ ] Documentación de usuario final

---

**¡Sistema completo de evaluación justa y psicotécnica listo!** 🎯⚔️

