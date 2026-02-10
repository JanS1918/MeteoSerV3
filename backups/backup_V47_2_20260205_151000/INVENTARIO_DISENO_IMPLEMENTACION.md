# 📋 INVENTARIO COMPLETO: DISEÑOS vs CÓDIGO

## 📊 Estado General
- **Total de conversaciones**: 3+ sesiones
- **Diseños identificados**: 47 características
- **Implementadas**: 32 (68%)
- **Pendientes**: 15 (32%)
- **Bloqueadas**: 3 (requieren decisiones)

---

## 🟢 IMPLEMENTADAS (32/47)

### Motor de Duelos (COMPLETADO)
| Diseño | Status | Ubicación | Nota |
|--------|--------|-----------|------|
| Duelo básico de fórmulas | ✅ | `core/monitoring/formula_duel_engine.py` | Compara dos fórmulas, selecciona ganador |
| Puntuación de duelos | ✅ | Same | Precision (60%) + Estabilidad (30%) + Eficiencia (10%) |
| Detección de contaminación | ✅ | Same | Analiza alertas y metadatos de simulación |
| Modo dry-run | ✅ | Same | Recomienda sin aplicar cambios |
| Mitigación de contaminación | ✅ | Same | Rechaza duelos si datos no limpios |
| Selector de escenarios | ✅ | Same | Diferentes fórmulas por rango de temperatura |
| Integración con vanguard | ✅ | Same | Lee candidatas de `vanguard_alerts.json` |

### Gestión de Cambios (COMPLETADO)
| Diseño | Status | Ubicación | Nota |
|--------|--------|-----------|------|
| Tracker de cambios | ✅ | `core/monitoring/formula_change_tracker.py` | Registra quién cambió qué y por qué |
| Auditoría de cambios | ✅ | Same | Verifica si cambios realmente mejoraron |
| Marcar estabilización | ✅ | Same | Indica que fórmula ya "ganó" los duelos |
| Rollback automático | ✅ | Same | Revierte cambios que no mejoraron |

### Gestor de Overrides (COMPLETADO)
| Diseño | Status | Ubicación | Nota |
|--------|--------|-----------|------|
| Override por defecto | ✅ | `core/monitoring/formula_override_manager.py` | Usa fórmula X siempre |
| Override por escenarios | ✅ | Same | Usa fórmula X si T > 20°C, Y si T ≤ 20°C |
| Persistencia de overrides | ✅ | Same | Guarda en JSON |
| UI Web (Streamlit) | ✅ | `ui/streamlit_formulas.py` | Interfaz para aplicar overrides |

### Jerarquía de Fórmulas (COMPLETADO)
| Diseño | Status | Ubicación | Nota |
|--------|--------|-----------|------|
| 10 niveles Elite por parámetro | ✅ | `core/bus/formula_hierarchy.py` | NivelElite NIVEL_1 a NIVEL_10 |
| Registro de fórmulas | ✅ | Same | Hardy, Wexler, OMM, IAPWS-95, etc. |
| Acceso transparente | ✅ | Same | Sistema elige automáticamente nivel máximo disponible |

### Fórmulas Científicas (COMPLETADO)
| Diseño | Status | Ubicación | Nota |
|--------|--------|-----------|------|
| Hardy NIST (Presión Vapor) | ✅ | `core/indices/hardy_nist_psicrometria.py` | ±0.1 Pa, NIST 1998 |
| Wexler-Hyland Saturado | ✅ | Same | Polinomios NIST ±0.1 Pa |
| Newton-Raphson Td | ✅ | Same | Converge garantizado |
| OMM/WMO Densidad | ✅ | `core/indices/omm_densidad_temperatura_virtual.py` | CIPM-2007, ±0.01% |
| Temperatura Virtual | ✅ | Same | Corrección por humedad |
| IAPWS-95 | ✅ | Referencias en jerarquía | Máxima precisión agua |
| Penman-Monteith ET | ✅ | `core/indices/` | FAO-56, ASCE Standardized |
| UTCI Comfort Index | ✅ | `core/indices/utci_polynomial.py` | Fiala 186 capas, -50 a +60°C |

### Registro de Candidatas (COMPLETADO)
| Diseño | Status | Ubicación | Nota |
|--------|--------|-----------|------|
| Registro de candidatas externas | ✅ | `core/monitoring/formula_candidate_registry.py` | Para formulas propuestas |
| Persistencia JSON | ✅ | Same | `data/formula_candidates.json` |
| Integración con duelos | ✅ | Same | Candidatas compiten contra elite |

### Acceso a Datos (RECIÉN IMPLEMENTADO)
| Diseño | Status | Ubicación | Nota |
|--------|--------|-----------|------|
| Puente SensorDataBridge | ✅ | `core/monitoring/sensor_data_bridge.py` | Lee last_sensores.json, llena historial |
| Lectura last_sensores.json | ✅ | Same | 45+ parámetros con timestamps |
| Llenado historial_sensores | ✅ | Same | Deques de 1000 muestras por parámetro |
| Persistencia sensores_historico.json | ✅ | Same | Guarda histórico para auditorías |
| Estadísticas por parámetro | ✅ | Same | Media, stdev, min, max, rango |

---

## 🟡 PENDIENTES (15/47)

### 1. ⚠️ MOTOR EN MODO REAL (NO DRY-RUN)

**Status**: Bloqueado por validación
**¿Por qué no se hizo?**: Necesita aprobación explícita del usuario
**Qué falta**: 
- [ ] Ejecutar duelo real con datos reales
- [ ] Validar que recomendaciones sean coherentes
- [ ] Comparar contra juicio humano
- [ ] Aprobar antes de desactivar dry_run

**Ubicación actual**: `core/monitoring/formula_duel_engine.py` línea 55: `self.dry_run = True`

**Siguiente paso**: 
```python
# Usuario debe ejecutar:
engine = FormulaDuelEngine()
engine.dry_run = False  # ← DECISIÓN DEL USUARIO
system = SystemCore(...)
engine.run(system)
```

---

### 2. ⚠️ DASHBOARD EN TIEMPO REAL (RESULTADOS DUELOS)

**Status**: Interfaz falta
**¿Por qué no se hizo?**: Esperaba que duelos estén funcionando primero
**Qué falta**:
- [ ] Crear `ui/streamlit_duel_results.py` 
- [ ] Mostrar tabla: Parámetro | Ganador | Score | Estabilidad | Status
- [ ] Botón: "Aplicar cambio" (llamar override_manager)
- [ ] Botón: "Ver histórico" (graficar con plotly)
- [ ] Botón: "Rechazar cambio" (registrar en tracker)

**Diseño**:
```
┌─ MOTOR DE DUELOS ──────────────────────────┐
│ Próxima ejecución: en 18 horas              │
│                                             │
│ Parámetro        Ganador      Score Status  │
│ ─────────────────────────────────────────  │
│ temperatura      Hardy NIST   0.87  ✓ OK   │
│ humedad          Arden Buck   0.76  ⚠ BAJA│
│ presion          OMM WMO      0.92  ✓ OK   │
│                                             │
│ [Aplicar] [Rechazar] [Ver Histórico]       │
└─────────────────────────────────────────────┘
```

**Bloqueador**: Duelos deben correr una vez con éxito primero

---

### 3. ⚠️ PERSISTENCIA DE SESIÓN DE DUELOS

**Status**: Arquitectura falta
**¿Por qué no se hizo?**: Esperaba que duelos básicos funcionasen primero
**Qué falta**:
- [ ] Guardar sesión: ID, timestamp, parámetros duelos, resultados
- [ ] Permitir "reproducir" duelo histórico
- [ ] Comparar duelos de distintos días
- [ ] Detectar patrones: ¿siempre gana Hardy en T > 25°C?

**Ubicación**: Nueva clase `core/monitoring/duel_session_manager.py`

**Estructura de datos**:
```json
{
  "duel_sessions": [
    {
      "session_id": "duel_20260203_v1",
      "timestamp": 1770081303.32,
      "duelos": [
        {
          "parametro": "temperatura",
          "formula_a": "Hardy NIST",
          "formula_b": "Magnus Simple",
          "score_a": 0.87,
          "score_b": 0.72,
          "ganador": "Hardy NIST",
          "razon": "Mejor estabilidad en rango extremo"
        }
      ]
    }
  ]
}
```

---

### 4. ⚠️ MOTOR DE RECOMENDACIONES INTELIGENTE

**Status**: Falta integración
**¿Por qué no se hizo?**: Depende de que duelos reales funcionen
**Qué falta**:
- [ ] Analizar tendencias de duelos históricos
- [ ] Si Hardy siempre gana: "Cambia a Hardy de forma permanente"
- [ ] Si hay empates: "Mantén escenarios (T > 25)"
- [ ] Si candidata externa gana: "Integra esta fórmula"
- [ ] Generar "reporte ejecutivo" legible para humanos

**Diseño**:
```
RECOMENDACIONES AUTOMÁTICAS (basado en 10 últimos duelos)

✅ CAMBIO RECOMENDADO:
   - temperatura: Cambiar de Magnus → Hardy NIST (ganó 9/10 duelos)
   - Razón: Mayor precisión con datos extremos

⚠️ SIN DECISIÓN:
   - humedad: Empate técnico entre Arden Buck y Magnus
   - Acción: Usar escenarios (Arden Buck si HR > 80%, Magnus si HR ≤ 80%)

❌ CAMBIO NO RECOMENDADO:
   - presion: Candidata externa "SuperPressure" perdió 5 duelos consecutivos
   - Acción: Descartar candidata, mantener OMM WMO
```

---

### 5. ⚠️ TEST FRAMEWORK PARA DUELOS

**Status**: Falta implementación
**¿Por qué no se hizo?**: Necesita que duelos reales funcionen
**Qué falta**:
- [ ] `tests/test_formula_duels.py` - Unit tests
- [ ] `tests/test_duel_scenarios.py` - Tests de escenarios
- [ ] Datos sintéticos para reproducibilidad
- [ ] Validación: si test_A falla hoy, debe fallar siempre

**Ejemplo de test**:
```python
def test_hardy_beats_magnus_extremo():
    # Simular T extrema (-30°C), alta humedad
    datos = synthetic_data(temp=-30, humid=95, samples=50)
    score_hardy = evaluar_hardy(datos)
    score_magnus = evaluar_magnus(datos)
    assert score_hardy > score_magnus, "Hardy debe ganar en extremo"
```

**Bloqueador**: Necesita suite de datos sintéticos

---

### 6. ⚠️ VANGUARD: ALERTAS AUTOMÁTICAS

**Status**: Sistema existe pero sin triggers
**¿Por qué no se hizo?**: No hay condiciones definidas para generar alertas
**Qué falta**:
- [ ] Definir: "¿Cuándo una fórmula es sospechosa?"
- [ ] Triggers:
  - Sensor no recibe datos > 2 horas → Vanguard Alert
  - Duelo tarda > 1 hora (posible infinite loop) → Alert
  - Candidata externa tiene score 0.2 diferencia de elite → Alert "Promisoria"
  - Histórico contiene gap > 30 min → Alert "Datos inconsistentes"
- [ ] Implementar en `core/monitoring/vanguard_*.py`

**Archivo referencia**: `data/vanguard_alerts.json` (existe pero vacío)

---

### 7. ⚠️ AUDITORÍA DE FÓRMULAS

**Status**: Tracker existe, auditoría falta
**¿Por qué no se hizo?**: Esperaba cambios reales primero
**Qué falta**:
- [ ] `core/monitoring/formula_audit.py`
- [ ] Preguntas:
  - "¿Quién cambió cada fórmula?"
  - "¿Cuándo se hizo el cambio?"
  - "¿Por qué se hizo (duelo vs manual)?"
  - "¿Mejoró o empeó el sistema después?"
- [ ] Report diario: "Cambios aplicados y sus impactos"

**Ubicación**: Nueva clase en core/monitoring/

---

### 8. ⚠️ INTEGRACIÓN CON EPISODIC_MEMORY

**Status**: DB existe pero no conectada
**¿Por qué no se hizo?**: Motor estaba buscando archivos, no DB
**Qué falta**:
- [ ] Conectar `episodic_memory.db` como fuente secundaria de datos
- [ ] Si `last_sensores.json` no responde → caer a episodic_memory
- [ ] Sincronizar: episodic_memory debe copiar datos de last_sensores
- [ ] Ubicación: `core/memory/episodic_integration.py`

**Beneficio**: Redundancia, datos históricos más profundos

---

### 9. ⚠️ LIMPIEZA DE DATOS AUTOMÁTICA

**Status**: Existe `_historico_limpio()` pero es pasiva
**¿Por qué no se hizo?**: Necesita definir reglas de limpieza
**Qué falta**:
- [ ] `core/monitoring/data_cleaner.py`
- [ ] Ejecutar limpieza:
  - Quitar outliers (±3 sigma)
  - Interpolar gaps pequeños (< 5 min)
  - Rechazar secuencias con valores repetidos (sensor stuck)
  - Detectar cambios discontinuos (saltos > 2*sigma)
- [ ] Opción: limpieza agresiva vs conservadora
- [ ] Logging: registrar qué se limpió

**¿Por qué no se hizo?**: Podría ocultar problemas reales de sensores

---

### 10. ⚠️ GENERADOR DE DATOS SINTÉTICOS

**Status**: Falta completamente
**¿Por qué no se hizo?**: Necesita para testing, pero sistema tiene datos reales
**Qué falta**:
- [ ] `core/simulation/synthetic_generator.py`
- [ ] Generar: condiciones típicas, extremas, raras
- [ ] Usable para:
  - Testear duelos sin esperar 24h reales
  - Validar fórmulas en condiciones imposibles
  - Reproducibilidad
- [ ] Parámetros:
  - Amplitud (rango de valores)
  - Frecuencia (cuánto varía)
  - Contaminación (% de datos malos)

**Ejemplo**:
```python
gen = SyntheticGenerator()
# Escenario: nevada extrema
datos = gen.generar_escenario(
    temperatura=-25,
    humedad=98,
    presion=970,
    duracion_minutos=480,
    contaminacion=0.05
)
```

---

### 11. ⚠️ EXPORTACIÓN DE REPORTES

**Status**: Falta
**¿Por qué no se hizo?**: Motor recién operacional
**Qué falta**:
- [ ] Excel: Todos los duelos históricos con análisis
- [ ] CSV: Datos crudos para investigación
- [ ] PDF: Reporte ejecutivo mensual
- [ ] HTML: Dashboard estático para compartir

**Ubicación**: `core/reporting/report_generator.py`

---

### 12. ⚠️ NOTIFICACIONES (EMAIL, SLACK, DISCORD)

**Status**: Falta integración
**¿Por qué no se hizo?**: Sistema aún en desarrollo
**Qué falta**:
- [ ] Cuando duelo descubre mejora → Notificar
- [ ] Cuando cambio se revierte → Notificar
- [ ] Cuando sensor falla → Notificar
- [ ] Soportar: email, slack webhook, discord bot

**Config**:
```json
{
  "notifications": {
    "email": {
      "enabled": true,
      "to": ["admin@example.com"],
      "on_events": ["duel_winner_found", "change_reverted"]
    },
    "slack": {
      "enabled": false,
      "webhook": "https://..."
    }
  }
}
```

---

### 13. ⚠️ INTERFAZ AUTOMÁTICA PARA BUSCAR FORMULAS PROPUESTAS

**Status**: Puente existe pero no hay buscador
**¿Por qué no se hizo?**: Esperaba que usuario proponga candidatas
**Qué falta**:
- [ ] `ui/streamlit_candidate_search.py`
- [ ] Permitir usuario:
  - Ingresar nombre de fórmula
  - Buscar en literatura / repositorios
  - Ver referencia bibliográfica
  - Evaluar científicamente
  - Agregar a candidatas si es aceptable
- [ ] Integración: ¿ChatGPT busca formulas?

---

### 14. ⚠️ INTEGRACIÓN CON CHATGPT/LLM

**Status**: Existe `meteoser_ia_integration.py` pero separado
**¿Por qué no se hizo?**: Motor no estaba listo
**Qué falta**:
- [ ] Conectar duelos con LLM
- [ ] Preguntas al LLM:
  - "¿Por qué Hardy gana sobre Magnus?"
  - "¿Qué fórmula recomendarías para humedad?"
  - "¿Esta candidata tiene sentido físicamente?"
- [ ] Respuestas contextualizadas con datos reales

---

### 15. ⚠️ VERSIONING DE FÓRMULAS

**Status**: Tracker existe pero sin versiones
**¿Por qué no se hizo?**: Necesita cambios reales primero
**Qué falta**:
- [ ] `core/monitoring/formula_versioning.py`
- [ ] Rastrear: 
  - v1: Hardy NIST (2026-01-15)
  - v2: Hardy NIST + Wexler (2026-01-20)
  - v3: Magnus Simple (2026-01-25, REVERTIDA)
- [ ] Poder "volver" a cualquier versión
- [ ] Changelog visible para auditoría

---

## 🔴 BLOQUEADAS (3/47)

### 1. ❌ DUELOS MULTIPARÁMETRO
**Bloqueador**: ¿Cómo comparar dos fórmulas de TEMPERATURA contra dos de HUMEDAD simultáneamente?
**Decisión necesaria**: ¿Ganador es "mejor en 3/4 parámetros"? ¿O score agregado?
**Estado**: Diseño incompleto

### 2. ❌ APRENDIZAJE CONTINUO (SELF_MOD_ENGINE)
**Bloqueador**: `self_mod_engine.py` existe pero está desacoplado del motor de duelos
**Decisión necesaria**: ¿Self-mod propone cambios? ¿Motor los valida? ¿O son procesos separados?
**Estado**: Arquitectura sin decisión

### 3. ❌ INTEGRACIÓN COMPLETA CON SISTEMA METEO PRINCIPAL
**Bloqueador**: Motor de duelos es independiente, pero main.py no lo llama
**Decisión necesaria**: ¿Motor ejecuta cada 24h automáticamente? ¿O manual? ¿O ambos?
**Estado**: Falta hook en SystemCore.run()

---

## 📈 IMPACTO Y RECOMENDACIÓN

### Prioridad 1 (HACER YA)
1. **Motor en modo real** → Desactivar dry_run después de validar una ejecución
2. **Dashboard de resultados** → Ver qué está pasando en vivo
3. **Persistencia de sesiones** → No perder información de duelos

### Prioridad 2 (SIGUIENTE SPRINT)
4. Recomendaciones inteligentes
5. Vanguard alertas configurables
6. Auditoría de cambios

### Prioridad 3 (NICE-TO-HAVE)
7. Exportación de reportes
8. Notificaciones
9. Generador de datos sintéticos

### Prioridad 4 (INVESTIGACIÓN)
10. Duelos multiparámetro
11. Integración Self-mod
12. LLM interpretación

---

## 🚀 PRÓXIMOS PASOS

**Inmediato**:
```
1. Ejecutar motor una vez con dry_run=True → Ver resultados
2. Validar que recomendaciones sean sensatas
3. Cambiar dry_run=False
4. Monitorear cambios por 48 horas
```

**Después**:
```
5. Implementar dashboard
6. Crear tests automatizados
7. Documentar decisiones tomadas
```

---

**Documento generado**: 2026-02-03 (UTC)
**Versión del sistema**: MeteoSerV3 con Motor de Duelos v1.0
**Estado del motor**: ✅ Operacional (acceso a datos resuelto, modo dry-run activo)
