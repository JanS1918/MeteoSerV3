# 📊 TABLA DE REFERENCIA RÁPIDA

## 1. Archivos Clave

| Archivo | Propósito | Acción |
|---------|-----------|--------|
| `core/monitoring/sensor_data_bridge.py` | Puente datos | Producción (automático) |
| `core/monitoring/formula_duel_engine.py` | Motor duelos | Ejecutar / monitorear |
| `data/last_sensores.json` | Datos en vivo | Leer (automático) |
| `data/sensores_historico.json` | Histórico persistido | Leer (se crea automático) |
| `data/formula_duel_results.json` | Resultados duelos | Leer / analizar |
| `data/formula_duel_state.json` | Estado motor | Leer (metadata) |

---

## 2. Documentación Entregada

| Documento | Tipo | Leer si... | Tiempo |
|-----------|------|-----------|--------|
| `GUIA_RAPIDA_MOTOR_OPERACIONAL.md` | Acción | Quieres ejecutar ahora | 3 min |
| `RESUMEN_SESION_2026_02_03.md` | Contexto | Quieres entender qué pasó | 5 min |
| `RESUMEN_MOTOR_DUELOS_OPERACIONAL.md` | Técnico | Necesitas detalles técnicos | 10 min |
| `INVENTARIO_DISENO_IMPLEMENTACION.md` | Exhaustivo | Quieres ver TODO planificado | 20 min |
| `ANTES_DESPUES_VISUAL.md` | Visual | Prefieres diagramas | 5 min |

---

## 3. Pruebas Disponibles

| Script | Qué hace | Usar para | Tiempo |
|--------|----------|-----------|--------|
| `run_duel_test.py` | End-to-end rápido | Validación inicial | 30 seg |
| `test_sensor_bridge.py` | Solo puente | Debuguear datos | 5 seg |
| `test_motor_duelos_real.py` | Motor completo | Validación profunda | 1-2 min |

---

## 4. Parámetros del Motor

| Parámetro | Valor Actual | Rango | Efecto |
|-----------|--------------|-------|--------|
| `dry_run` | `True` | True/False | Aplica cambios o solo recomienda |
| `peso_precision` | 0.6 | 0-1 | Importancia de precisión |
| `peso_estabilidad` | 0.3 | 0-1 | Importancia de estabilidad |
| `peso_eficiencia` | 0.1 | 0-1 | Importancia de velocidad |
| `max_parametros_por_run` | 4 | 1-50 | Cuántos duelos por ejecución |
| `sample_size` | 100 | 30-1000 | Muestras para análisis |
| `audit_days` | 7 | 1-90 | Días para auditar cambios |

---

## 5. Fórmulas Implementadas (Jerarquía)

| Parámetro | ELITE | ESTÁNDAR | PROFESIONAL |
|-----------|-------|----------|-------------|
| `punto_rocio` | Hardy NIST | Wexler Newton-Raphson | IAPWS-95 |
| `presion_vapor` | Hardy Enhancement | IAPWS-95 | Goff-Gratch |
| `sensacion_termica` | UTCI | Steadman | Heat Index |
| `evapotranspiracion` | ASCE Penman-Monteith | FAO-56 Penman | Hargreaves |
| `densidad_aire` | OMM WMO CIPM-2007 | Ideal Gas | Density Approx |
| `presion_relativa` | (ELITE) | IAPWS-95 | Hypsometric |

---

## 6. Carga de Datos (Estado Actual)

| Fuente | Parámetros | Estado | Frecuencia |
|--------|-----------|--------|-----------|
| `last_sensores.json` | 45 | ✅ Activo | En vivo |
| `system.historial_sensores` | 45 | ✅ Lleno (deques) | Cada run() |
| `sensores_historico.json` | 45 | ✅ Persistido | Cada 5 seg |
| `episodic_memory.db` | Variable | ⚠️ Desconectado | - |

---

## 7. Decisiones Necesarias del Usuario

| Pregunta | Opción A | Opción B | Efecto |
|----------|----------|----------|--------|
| ¿Duelos reales? | `dry_run=False` | `dry_run=True` (mantener) | Aplica o no cambios |
| ¿Frecuencia? | 24 horas | On-demand manual | Automático vs manual |
| ¿Dashboard? | Crear Streamlit | No crear | Interfaz visual |
| ¿Integración main? | Llamar motor cada run | Independiente | Acoplamiento |

---

## 8. Próximas Características (Prioridad)

| Prioridad | Característica | Tamaño | Bloqueador |
|-----------|---|--------|-----------|
| 1️⃣ | Motor en modo real | S | Decisión usuario |
| 2️⃣ | Dashboard de resultados | M | Motor funcional |
| 3️⃣ | Persistencia de sesiones | S | Tests previos |
| 4️⃣ | Recomendaciones inteligentes | M | Histórico de duelos |
| 5️⃣ | Vanguard alertas | S | Config alertas |

---

## 9. Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| "ModuleNotFoundError" | Path incorrecto | `cd MeteoSerV3` antes de ejecutar |
| "No results" | Pocos parámetros en jerarquía | Normal, solo hay 6 parámetros |
| "Histórico vacío" | Primer run sin datos | Ejecutar 2 veces |
| "sensores_historico.json not found" | Primer ejecución | OK, se crea automáticamente |

---

## 10. Comando Rápido para TODO

```bash
# 1. Ir a carpeta
cd C:\Users\kioko\Desktop\MeteoSerV3

# 2. Ejecutar test
python run_duel_test.py

# 3. Ver resultados
type data\formula_duel_results.json

# 4. Si OK, leer este documento
more INVENTARIO_DISENO_IMPLEMENTACION.md
```

---

## 11. Indicadores de Salud

| Indicador | Verde ✅ | Amarillo ⚠️ | Rojo ❌ |
|-----------|--------|----------|--------|
| Datos cargados | >30 params | 10-30 params | <10 params |
| Duelos ejecutados | >0 resultados | Resultados vacíos | Error |
| Score motor | >0.70 promedio | 0.50-0.70 | <0.50 |
| Tiempo ejecución | <5 min | 5-15 min | >15 min |

---

## 12. URLs de Referencia (Si quieres profundizar)

| Tema | Fuente | Link (en internet) |
|------|--------|---------------------|
| Hardy NIST | Wikipedia | "Dew point" |
| IAPWS-95 | Official | www.iapws.org |
| OMM/WMO | Organización | wmo.int |
| Penman-Monteith | FAO | fao.org/evapotranspiration |
| UTCI | ISO 14505-2 | Standard meteorología |

---

## 13. Confirmación de Implementación

| Componente | Implementado | Probado | Documentado |
|-----------|---------|---------|---------|
| SensorDataBridge | ✅ | ✅ | ✅ |
| Integración motor | ✅ | ✅ | ✅ |
| Tests | ✅ | ✅ | ✅ |
| Documentación | ✅ | - | ✅ |
| Dashboard | ❌ | - | ❌ |
| Recomendaciones | ✅ (diseño) | ❌ | ❌ |

---

## 14. Respuestas a Preguntas Originales (TABLA)

| Pregunta Original | Respuesta | Evidencia | Acción |
|------------------|-----------|-----------|--------|
| ¿Fórmulas mejoran sistema? | NO (son inferiores) | Análisis científico + literatura | Mantener actuales |
| ¿Tenemos datos? | SÍ (45 params, activos) | last_sensores.json verificado | Usar Bridge |
| ¿Motor accede a datos? | SÍ (SensorDataBridge) | Prueba pasada: 38 params cargados | Ejecutar test |

---

## 15. Checklist de Implementación

- [x] Analizar preguntas del usuario
- [x] Investigar fórmulas propuestas
- [x] Verificar disponibilidad de datos
- [x] Diseñar SensorDataBridge
- [x] Implementar SensorDataBridge
- [x] Integrar con FormulaDuelEngine
- [x] Crear tests
- [x] Documentar exhaustivamente
- [ ] Usuario ejecuta test
- [ ] Usuario valida resultados
- [ ] Usuario activa modo real
- [ ] Motor en producción continua

---

**Última actualización**: 2026-02-03  
**Estado**: ✅ OPERACIONAL  
**Bloqueadores**: 0  
**Pendiente**: Ejecución de usuario  
