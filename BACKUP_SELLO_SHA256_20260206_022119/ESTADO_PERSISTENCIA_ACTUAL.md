# ANÁLISIS COMPLETO: ¿QUÉ SE GUARDA PARA EL APRENDIZAJE?

**Fecha**: 4 de febrero de 2026

---

## RESUMEN EJECUTIVO

**RESPUESTA CORTA**: No, **NO se guarda absolutamente todo**. Se guardan los **sensores y configuración**, pero **FALTA guardar sistemáticamente**:
- ❌ Histórico de predicciones (qué predijo en cada momento)
- ❌ Probabilidades de predicciones (confianza de cada predicción)
- ❌ Resultados de predicciones comparados (acertó o no)
- ❌ Índices calculados en el tiempo (sensación térmica, punto de rocío, etc. históricos)
- ❌ Alertas generadas (cuándo se generaron y por qué)
- ❌ Feedback del usuario sobre predicciones (si el usuario confirma o contradice)
- ❌ Sensores virtuales históricos (ej: índice UTCI histórico)
- ❌ Decisiones del motor de duelos (cuál fórmula ganó y por qué)

**Sin estos datos el sistema NO puede aprender porque:**
1. No hay comparación predicción vs realidad
2. No hay histórico de aciertos/errores
3. No hay feedback de validación
4. No hay trazabilidad de decisiones

---

## PARTE 1: QUÉ SE ESTÁ GUARDANDO ACTUALMENTE

### ✅ SENSORES (100% completo)

| Archivo | Registros | Contenido | Intervalo |
|---------|-----------|----------|-----------|
| `sensores_historico.json` | **12** | Datos crudos + normalizados | ~7 min |
| `last_sensores.json` | 1 | Último payload EcowittGateway | Continuo |
| `sensor_ewma_state.json` | ✓ | Estado de suavizado EWMA | Continuo |
| `sensor_aliases.json` | ✓ | Mapeo de aliases de sensores | Estático |

**Ejemplo de registro**:
```json
{
  "timestamp": 1770201072.847,
  "sensores": {
    "temperatura": 12.78,      ← NORMALIZADO (original: 54.5°F)
    "humedad": 77.0,           ← NORMALIZADO
    "viento": 4.02,            ← NORMALIZADO (original: 2.5mph)
    "presion": 1010.13,        ← NORMALIZADO
    "radiacion": 0.0
  },
  "timestamps": { ... }
}
```

**Status**: ✅ **COMPLETO** - Se guardan 41+ parámetros normalizados cada ~7 minutos

---

### ✅ CONFIGURACIÓN & ESTADO (100% completo)

| Archivo | Contenido | Status |
|---------|----------|--------|
| `predicciones_config.json` | Config de motores de predicción | ✓ Guardado |
| `indices_config.json` | Config de índices (UTCI, Steadman, etc) | ✓ Guardado |
| `formula_duel_state.json` | Estado actual de duelos | ✓ Guardado |
| `vanguard_state.json` | Estado del sistema de alertas | ✓ Guardado |
| `sensor_aliases.json` | Mapeo de nombres de sensores | ✓ Guardado |

---

### ⚠️ MÉTRICAS Y AUDITORÍA (Parcial)

| Archivo | Registros | Contenido |
|---------|-----------|----------|
| `metrics_history.jsonl` | **1 registro** | Histórico de métricas (append-only) |
| `auditoria.jsonl` | **1 registro** | Log de auditoría (append-only) |
| `metrics_predicciones.json` | 1 objeto | Resumen último de predicciones |

**Problema**: Solo tiene **1 registro cada uno**. No está siendo actualizado continuamente.

---

### ❌ ALERTAS (VACÍO)

```
vanguard_alerts.json → 0 registros
```

¿Qué debería guardar?
- Timestamp de alerta
- Tipo de alerta
- Valor que disparó (ej: velocidad viento > 40 km/h)
- Nivel (rojo/naranja/verde)
- Acciones recomendadas

---

### ❌ DUELOS DE FÓRMULAS (VACÍO)

```
formula_duel_results.json → 0 registros
```

¿Qué debería guardar?
- Timestamp del duelo
- Parámetro comparado (ej: "sensación_térmica")
- Fórmula A vs Fórmula B
- Datos de entrada (temperatura, humedad, etc)
- Resultado A / Resultado B
- Ganador y diferencia
- Motivo de la victoria

---

### ⚠️ FEEDBACK DE PREDICCIONES (Parcial)

```
prediction_feedback_state.json → 23.6 KB con estructura
```

Existe la **estructura** pero está **vacía de datos históricos**. Solo tiene:
```json
{
  "stats": { "total_feedback": 0, "avg_confidence": 0 },
  "pending": [],
  "events": []
}
```

---

### ⚠️ PREDICCIONES (NO SE GUARDAN)

**CRÍTICO**: No hay archivo `predicciones_historico.json` que guarde:
- ❌ Qué predicción se hizo en cada momento
- ❌ Con qué confianza
- ❌ Contra qué valor real después
- ❌ Si fue correcta o no

---

### ⚠️ ÍNDICES (NO SE GUARDAN HISTÓRICOS)

**CRÍTICO**: No hay archivo `indices_historico.json` que guarde:
- ❌ Sensación térmica histórica
- ❌ Punto de rocío histórico
- ❌ Índices derivados históricos
- ❌ Solo la **configuración** se guarda, no los **cálculos**

---

### ⚠️ SENSORES VIRTUALES (NO SE GUARDAN)

**CRÍTICO**: Los sensores virtuales (derivados) no se guardan:
- ❌ UTCI (Índice de Temperatura Térmica Universal)
- ❌ Steadman Apparent Temperature
- ❌ Punto de rocío
- ❌ Humedad relativa derivada
- ❌ Velocidad efectiva del viento ajustada

---

## PARTE 2: QUÉ FALTA GUARDAR PARA QUE EL SISTEMA PUEDA APRENDER

### CRÍTICO (Sin estos, NO HAY aprendizaje)

| ¿Qué? | ¿Dónde? | ¿Frecuencia? | Razón |
|-------|--------|-------------|-------|
| **Predicciones hechas** | `predicciones_historico.json` | Cada predicción | Comparar contra realidad |
| **Confianza de predicción** | Mismo archivo | Cada predicción | Medir calibración |
| **Valores reales después** | Mismo archivo + sensores | Post-predicción | Validar acierto/error |
| **Índices calculados** | `indices_historico.json` | Cada cálculo | Auditoria de fórmulas |
| **Alertas generadas** | `vanguard_alerts_historico.json` | Cada alerta | Análisis de falsas alarmas |
| **Feedback del usuario** | `feedback_predicciones.jsonl` | Cuando usuario da feedback | Supervisión humana |
| **Resultados duelos** | `formula_duel_historico.jsonl` | Cada duelo | Auditar decisiones |

### IMPORTANTE (Sin estos, aprendizaje incompleto)

| ¿Qué? | ¿Dónde? | Razón |
|-------|--------|-------|
| Sensores virtuales (UTCI, rocío) | `virtual_sensors_historico.json` | Validar cálculos de índices |
| Calibraciones aplicadas | `calibration_history.jsonl` | Rastrear ajustes |
| Cambios de configuración | `config_changes.jsonl` | Auditoría de cambios |
| Evolución de fórmulas | `formula_evolution.jsonl` | Ver qué fórmulas mejoran |

---

## PARTE 3: ANÁLISIS CRÍTICO

### PROBLEMA 1: No hay historial de predicciones

**Hoy**:
- Motor de predicción **calcula** predicciones
- Pero **NO las guarda**
- Entonces NO se puede comparar si fue correcto

**Escenario**:
```
Motor predice: "Mañana 15°C"
Realidad: 16°C
¿El motor lo sabe? NO - porque nunca guardó que predijo 15°C
```

### PROBLEMA 2: No hay trazabilidad de alertas

**Hoy**:
- Sistema Vanguard puede generar alertas
- Pero `vanguard_alerts.json` está **vacío**
- No hay registro de cuándo alertó, por qué, si fue correcta

### PROBLEMA 3: No hay validación de fórmulas

**Hoy**:
- Duelos de fórmulas pueden ocurrir
- Pero `formula_duel_results.json` está **vacío**
- No hay trazabilidad: "¿Qué fórmula ganó? ¿Por cuánto?"

### PROBLEMA 4: No hay feedback loop

**Hoy**:
- Motor calcula
- Usuario podría dar feedback "Eso fue incorrecto"
- Pero no hay lugar donde guardar ese feedback
- Entonces el sistema **no puede aprender de los errores**

---

## PARTE 4: PLAN DE IMPLEMENTACIÓN

Para que el sistema pueda aprender fiablemente, se necesitan estos archivos nuevos:

### 1️⃣ Histórico de Predicciones (CRÍTICO)

```python
# core/monitoring/prediction_history.py

class PredictionHistoryRecorder:
    def save_prediction(self, 
        timestamp: float,
        prediccion: Dict,
        confianza: float,
        motor_id: str
    ):
        """Guarda cada predicción hecha"""
        # Genera: data/predicciones_historico.jsonl
        # Formato:
        # {"timestamp": 1234.5, "prediccion": {...}, "confianza": 0.85, "motor": "MotorX"}
```

**Ubicación**: `data/predicciones_historico.jsonl` (append-only)
**Frecuencia**: Cada predicción (~cada 5 minutos)
**Tamaño esperado**: ~10 KB/día

### 2️⃣ Resultados Reales de Predicciones (CRÍTICO)

```python
# Después de X tiempo (ej: 24h), comparar
# Predicción: "Mañana 15°C"
# Realidad: "Fue 16°C"
# Guardar: {"prediccion": 15, "realidad": 16, "error": -1, "acierto": false}
```

**Ubicación**: `data/prediction_validation_historico.jsonl`
**Frecuencia**: Al validar (24h después de predicción)

### 3️⃣ Histórico de Índices (CRÍTICO)

```python
# core/monitoring/indices_history.py

class IndicesHistoryRecorder:
    def save_indices(self, timestamp: float, indices: Dict):
        """Guarda índices calculados"""
        # Genera: data/indices_historico.jsonl
        # Formato:
        # {"timestamp": 1234.5, "utci": 18.5, "rocio": 8.5, "steadman": 22.1}
```

**Ubicación**: `data/indices_historico.jsonl`
**Frecuencia**: Cada cálculo (~cada 5 minutos)

### 4️⃣ Histórico de Alertas (IMPORTANTE)

```python
# Guardar cada alerta generada
# {"timestamp": 1234.5, "tipo": "viento_alto", "nivel": "naranja", 
#  "valor": 42.5, "umbral": 40, "accion": "recomendacion"}
```

**Ubicación**: `data/vanguard_alerts_historico.jsonl`
**Frecuencia**: Cuando se genera alerta

### 5️⃣ Histórico de Duelos (IMPORTANTE)

```python
# core/monitoring/duel_history.py

class DuelHistoryRecorder:
    def save_duel_result(self, 
        parametro: str, 
        formula_a: str, 
        formula_b: str,
        resultado_a: float,
        resultado_b: float,
        ganador: str
    ):
        """Guarda resultado de cada duelo"""
        # Genera: data/formula_duel_historico.jsonl
```

**Ubicación**: `data/formula_duel_historico.jsonl`
**Frecuencia**: Cada duelo ejecutado

### 6️⃣ Feedback de Usuario (IMPORTANTE)

```python
# El usuario dice: "La predicción del motor fue incorrecta"
# Guardar: {"timestamp": 1234.5, "prediccion_id": "xyz", 
#           "feedback": "incorrecto", "razon": "..."}
```

**Ubicación**: `data/user_feedback_historico.jsonl`
**Frecuencia**: Cuando usuario da feedback

---

## PARTE 5: IMPACTO EN EL APRENDIZAJE

### SIN estos datos (HOYENdía)

El sistema:
- ✅ Recopila sensores correctamente
- ❌ NO puede validar si predice bien o mal
- ❌ NO puede mejorar fórmulas basado en errores
- ❌ NO puede detectar cuándo generó falsas alarmas
- ❌ NO puede usar feedback del usuario

**Conclusión**: El aprendizaje es **INCOMPLETO e INFIABLE**.

### CON estos datos (Implementando)

El sistema:
- ✅ Recopila sensores
- ✅ Guarda predicciones
- ✅ Valida contra realidad
- ✅ Rastrea alertas correctas/falsas
- ✅ Mejora fórmulas basado en duelos auditados
- ✅ Integra feedback del usuario

**Conclusión**: El aprendizaje es **COMPLETO y FIABLE**.

---

## PART 6: CÓDIGO ACTUAL RELACIONADO

### Dónde se hacen predicciones (SIN guardar)

**Archivo**: `main_asgi.py` línea 1774
```python
predicciones = pred_engine.predecir()  # ← Se calcula pero NO se guarda histórico
```

### Dónde se procesan índices (SIN guardar)

**Archivo**: `main_asgi.py` línea 1785
```python
system.indices.reforzar_indices(indices, predicciones=predicciones)
# ← Se calculan pero NO se guardan históricos
```

### Dónde está el feedback (VACÍO)

**Archivo**: `main_asgi.py` línea 521-547
```python
@app.post("/feedback_prediccion")
async def feedback_prediccion(payload: dict = Body(...)):
    # ← Existe el endpoint pero NO persiste histórico de feedback
```

---

## CONCLUSIÓN

**Respuesta a tu pregunta: "¿Se guarda absolutamente todo?"**

**NO**. Se guardan:
- ✅ Sensores crudos y normalizados (correcto)
- ✅ Configuración del sistema
- ❌ Predicciones hechas
- ❌ Validación de predicciones
- ❌ Índices históricos
- ❌ Alertas generadas
- ❌ Decisiones de duelos
- ❌ Feedback del usuario

**Sin estos datos, el autoaprendizaje NO PUEDE FUNCIONAR**.

El sistema está **listo para recopilar**, pero **NO está listo para aprender**.

---

## PRÓXIMOS PASOS

### Implementar (en orden de criticidad):

1. **PredictionHistoryRecorder** - Guardar predicciones
2. **IndicesHistoryRecorder** - Guardar índices calculados
3. **PredictionValidationEngine** - Comparar predicción vs realidad
4. **DuelHistoryRecorder** - Guardar resultados de duelos
5. **AlertsHistoryRecorder** - Guardar alertas generadas
6. **FeedbackHistoryRecorder** - Guardar feedback del usuario

Sin estos, el "autoaprendizaje" es solo una ilusión.
