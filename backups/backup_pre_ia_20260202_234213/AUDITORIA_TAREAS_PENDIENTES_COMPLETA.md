# 📋 **AUDITORÍA EXHAUSTIVA: TODAS LAS TAREAS PENDIENTES**

**Generado:** 2 de febrero de 2026  
**Scope:** Toda la conversación + documentación del proyecto

---

## 🎯 **RESUMEN EJECUTIVO**

Se identificaron **52+ tareas pendientes** agrupadas en 8 categorías:

| Categoría | Cantidad | Prioridad | Estado |
|-----------|----------|-----------|--------|
| **1. Tests y Validación** | 12 | 🔴 ALTA | ⏳ PENDIENTE |
| **2. Ubicación y Astronomía** | 8 | 🔴 ALTA | ⏳ PENDIENTE |
| **3. Motores Luz/Circadiano** | 4 | 🟡 MEDIA | ⏳ PENDIENTE |
| **4. Persistencia de Cerebro** | 5 | 🔴 ALTA | ⏳ PENDIENTE |
| **5. Serialización Selectiva** | 3 | 🟢 BAJA | ⏳ PENDIENTE |
| **6. Documentación Técnica** | 7 | 🟢 BAJA | ⏳ PENDIENTE |
| **7. Certificación SHA256** | 3 | 🟡 MEDIA | ⏳ PENDIENTE |
| **8. Integración Dashboard** | 10 | 🟡 MEDIA | ⏳ PENDIENTE |

---

## 📌 **CATEGORÍA 1: TESTS Y VALIDACIÓN (12 TAREAS)**

### ✅ HECHO:
- [x] Benchmark ciclo 617 constantes (0.79 ms)
- [x] Validación sintaxis V14.0
- [x] Análisis colapso/red

### ⏳ PENDIENTE:

#### **1.1 | Test Ignición Física 2026** 🔴 ALTA
- **Archivo:** `test_ignicion_fisica_2026.py`
- **Qué falta:** Ejecutar el test completo
- **Verificar:**
  - Factor de Mejora Greenspan inyectado
  - UTCI con turbulencia real
  - VPD con Monin-Obukhov
  - Rayleigh-Miller dispersión
- **Comando:** `python test_ignicion_fisica_2026.py`
- **Tiempo:** 5 minutos

#### **1.2 | Test Sintonización 2026** 🔴 ALTA
- **Archivo:** `test_sintonizacion_2026.py`
- **Qué falta:** Ejecutar 5 tests de constantes dinámicas
  1. Constantes Argentona (Factor Z, Gravedad Somigliana, Viscosidad)
  2. Comparación ISA vs Real
  3. Psicrometría con Z
  4. ET0 con Somigliana
  5. Estabilidad con cp dinámico
- **Comando:** `python test_sintonizacion_2026.py`
- **Tiempo:** 5 minutos

#### **1.3 | Test Certificación V26** 🔴 ALTA
- **Archivo:** `test_certificacion_v26.py`
- **Qué falta:** Validar 6 protocolos
  - Factor Z Argentona ✓ (diseñado)
  - Densidad aire real ✓ (diseñado)
  - Psicrometría Greenspan (PENDIENTE)
  - Monin-Obukhov estabilidad (PENDIENTE)
  - UTCI coherencia (PENDIENTE)
  - Rayleigh-Miller (PENDIENTE)
- **Comando:** `python test_certificacion_v26.py`
- **Tiempo:** 10 minutos

#### **1.4 | Test Brain Persistencia** 🔴 ALTA
- **Archivo:** `test_statistical_brain.py`
- **Tests necesarios:**
  - Mann-Kendall trend detection ✓ (código existe)
  - Pendiente de Sen ✓ (código existe)
  - Guardar/cargar cerebro (PENDIENTE)
  - Validar coherencia (PENDIENTE)
  - Restaurar desde snapshot (PENDIENTE)
- **Comando:** `python test_statistical_brain.py`
- **Tiempo:** 10 minutos

#### **1.5 | Test Ecowitt Integration** 🟡 MEDIA
- **Archivo:** `probar_envio_ecowitt.py`
- **Qué falta:** Ejecutar y validar
  - Envío de datos Ecowitt al endpoint `/ecowitt`
  - Conversión de unidades (mph→m/s, °F→°C)
  - Persistencia en sensores
- **Comando:** `python probar_envio_ecowitt.py`
- **Tiempo:** 5 minutos

#### **1.6 | Test Verificación Sistema** 🟡 MEDIA
- **Archivo:** `verificar_sistema.py`
- **Tests a ejecutar:**
  1. Verificación 1: API health
  2. Verificación 2: Persistencia Drag & Drop
  3. Verificación 3: Motores activos
  4. Verificación 4: Índices calculados
- **Comando:** `python verificar_sistema.py`
- **Tiempo:** 10 minutos

#### **1.7-1.12 | Suite Completa pytest** 🟡 MEDIA
- **Tests restantes de pytest:**
  1. tests/test_location_module.py (PENDIENTE CREAR)
  2. tests/test_brain_persistence.py (PENDIENTE CREAR)
  3. tests/test_elite_motors.py (PENDIENTE CREAR)
  4. tests/test_v14_constants.py (PENDIENTE CREAR)
  5. tests/test_json_serialization.py (PENDIENTE CREAR)
  6. tests/test_gzip_compression.py (PENDIENTE CREAR)
- **Comando:** `pytest -q tests/`
- **Tiempo:** 30 minutos

---

## 📍 **CATEGORÍA 2: UBICACIÓN Y ASTRONOMÍA (8 TAREAS)**

### ⏳ PENDIENTE:

#### **2.1 | Centralizar módulo de ubicación** 🔴 ALTA
- **Estado:** Parcialmente implementado
- **Falta:**
  - Crear `core/location/location_module.py` (unificado)
  - Funciones: `coords_valid()`, `parse_coord()`, `coords_es_spain()`
  - Tests: `test_coords_valid()`, `test_parse_coord()`, `test_coords_es_spain()`
- **Archivo:** `core/location/location_module.py`
- **Líneas de código:** ~150
- **Tiempo:** 30 minutos

#### **2.2 | Restaurar cálculos Amanecer/Atardecer** 🔴 ALTA
- **Estado:** Existe `tools/amanecer_atardecer.py`
- **Falta:** Integrar en `environmental_indices.py`
- **Función:** `calcular_amanecer_atardecer(latitud, longitud, hoy, utc_offset)`
- **Validar:** Sunrise/sunset en respuesta JSON
- **Tiempo:** 20 minutos

#### **2.3 | Validar Arco Solar** 🔴 ALTA
- **Test:** `curl http://localhost:8080/api/panel/superior | jq '.indices.arco_solar.valor'`
- **Esperado:** Valor > 0 durante el día, 0 de noche
- **Falta:** Verificar que está siendo calculado correctamente
- **Tiempo:** 5 minutos

#### **2.4 | Validar Radiación Teórica** 🔴 ALTA
- **Test:** `curl http://localhost:8080/api/panel/central | jq '.indices.radiacion_teorica.valor'`
- **Esperado:** Coincida aproximadamente con radiación real del sensor
- **Validación:** Fórmula de radiación extraterrestre correcta
- **Tiempo:** 5 minutos

#### **2.5 | Validar Ubicación en JSON** 🔴 ALTA
- **Test:** `curl http://localhost:8080/api/panel/superior | jq '.ubicacion'`
- **Esperado:** 
  ```json
  {
    "latitud": 41.5507,
    "longitud": -2.397,
    "altitud": 96,
    "origen": "manual" | "gps" | "geocodificacion"
  }
  ```
- **Tiempo:** 5 minutos

#### **2.6 | Motor Luz Natural** 🟡 MEDIA
- **Test:** `curl http://localhost:8080/api/panel/superior | jq '.luz_natural'`
- **Falta:**
  - Implementar recomendaciones basadas en arco solar
  - Retornar no-vacío (no `{}`)
  - Integrar con ubicación y astronomía
- **Tiempo:** 30 minutos

#### **2.7 | Motor Ritmo Circadiano** 🟡 MEDIA
- **Test:** `curl http://localhost:8080/api/panel/superior | jq '.ritmo_circadiano'`
- **Falta:**
  - Implementar cálculo de melatonina/cortisol basado en luz natural
  - Recomendaciones de sueño
  - Retornar no-vacío
- **Tiempo:** 45 minutos

#### **2.8 | Integración Geofísica Completa** 🟡 MEDIA
- **Validar:** Todos los índices astronómicos usan ubicación correcta
  - Amanecer ✓ (diseñado)
  - Atardecer ✓ (diseñado)
  - Arco solar ✓ (diseñado)
  - Masa óptica (VALIDAR)
  - Ángulo cenital (VALIDAR)
  - Declinación solar (VALIDAR)
- **Tiempo:** 20 minutos

---

## 💾 **CATEGORÍA 3: PERSISTENCIA DE CEREBRO (5 TAREAS)**

### ⏳ PENDIENTE:

#### **3.1 | Implementar Guardado de Cerebro** 🔴 ALTA
- **Archivo:** `core/learning/cerebro_persistencia.py`
- **Falta:**
  - Método `guardar_cerebro()`
  - Serializar estado completo a JSON
  - Incluir:
    - Histórico de 7 días
    - Tendencias (Mann-Kendall)
    - Predicciones
    - Pesos aprendidos
  - Ubicación: `data/cerebro_snapshot_[timestamp].json`
- **Tiempo:** 45 minutos

#### **3.2 | Implementar Carga de Cerebro** 🔴 ALTA
- **Archivo:** `core/learning/cerebro_persistencia.py`
- **Falta:**
  - Método `cargar_cerebro(ruta)`
  - Restaurar estado completo
  - Validar coherencia de datos
  - Fallback si falla carga
- **Tiempo:** 30 minutos

#### **3.3 | Test Guardado/Carga** 🔴 ALTA
- **Test en:** `test_statistical_brain.py`
- **Validar:**
  1. Guardar cerebro completo
  2. Cargar desde archivo
  3. Comparar estado antes/después (debe ser idéntico)
  4. Validar histórico restaurado
- **Comando:** `python test_statistical_brain.py`
- **Tiempo:** 10 minutos

#### **3.4 | Validación Cruzada Cerebro** 🟡 MEDIA
- **Implementar:** `validar_coherencia_cerebro(estado_json)`
- **Verificar:**
  - No hay NaN/inf
  - Tendencias coherentes
  - Predicciones dentro de rangos
  - Timestamps monotónicos
- **Archivo:** `core/learning/cerebro_persistencia.py`
- **Tiempo:** 20 minutos

#### **3.5 | Restauración Automática al Iniciar** 🟡 MEDIA
- **En:** `main_asgi.py` evento `lifespan`
- **Falta:**
  - Detectar `data/cerebro_snapshot_*.json` más reciente
  - Cargar automáticamente
  - Si falla, iniciar cerebro limpio
  - Log en inicialización
- **Tiempo:** 15 minutos

---

## 📡 **CATEGORÍA 4: SERIALIZACIÓN SELECTIVA (3 TAREAS)**

### ⏳ PENDIENTE:

#### **4.1 | Endpoint `/estado/maestros` (solo valores principales)** 🟢 BAJA
- **URL:** `GET /estado/maestros`
- **Retorna:** Solo valores maestros (~1 KB)
  ```json
  {
    "temperatura": 22.5,
    "humedad": 65,
    "presion": 1013.25,
    "viento_ms": 3.5,
    "radiacion": 450,
    "latitud": 41.55,
    "longitud": -2.39
  }
  ```
- **Uso:** Dashboard rápido, UI responsive
- **Tiempo:** 15 minutos

#### **4.2 | Endpoint `/estado/completo` (todas las 617 constantes)** 🟢 BAJA
- **URL:** `GET /estado/completo`
- **Retorna:** Todos los valores incluyendo subfactores (~5.6 KB)
- **Uso:** API avanzada, análisis, exportación
- **GZIP:** Automático (ya configurado)
- **Tiempo:** 10 minutos

#### **4.3 | Endpoint `/estado/stream` (SSE para análisis en vivo)** 🟢 BAJA
- **URL:** `GET /estado/stream`
- **Protocolo:** Server-Sent Events (SSE)
- **Ventaja:** Streaming sin polling
- **Uso:** Gráficos en vivo, análisis real-time
- **Tiempo:** 30 minutos

---

## 🔐 **CATEGORÍA 5: CERTIFICACIÓN SHA256 (3 TAREAS)**

### ⏳ PENDIENTE:

#### **5.1 | Generar SHA256 de V14.0** 🟡 MEDIA
- **Archivo a hashear:** `core/system/bus_expander.py`
- **Implementar:**
  ```python
  import hashlib
  with open("core/system/bus_expander.py", "rb") as f:
      sha256_hash = hashlib.sha256(f.read()).hexdigest()
  ```
- **Guardar en:** `data/v14_0_certificacion.json`
- **Formato:**
  ```json
  {
    "version": "V14.0 SUPER DEFINITIVO",
    "sha256": "abc123...",
    "fecha": "2026-02-02",
    "constantes_totales": 617,
    "secciones": 32
  }
  ```
- **Tiempo:** 10 minutos

#### **5.2 | Crear "Sello de Élite"** 🟡 MEDIA
- **Concepto:** Certificado que V14.0 es "íntegro y completo"
- **Incluir:**
  - SHA256 de bus_expander.py
  - Checksum de todos los archivos críticos
  - Timestamp de certificación
  - Firma de integridad
- **Archivo:** `data/SELLO_ELITE_V14.0.json`
- **Tiempo:** 20 minutos

#### **5.3 | Validación de Integridad al Iniciar** 🟡 MEDIA
- **En:** `main_asgi.py` evento startup
- **Verificar:**
  - SHA256 de bus_expander.py coincide con el certificado
  - Si NO coincide: Warning en log (no bloquea)
  - Si SÍ coincide: ✅ en log "SELLO DE ÉLITE VERIFICADO"
- **Tiempo:** 15 minutos

---

## 📊 **CATEGORÍA 6: DOCUMENTACIÓN TÉCNICA (7 TAREAS)**

### ⏳ PENDIENTE:

#### **6.1 | Manual de V14.0 SUPER DEFINITIVO** 🟢 BAJA
- **Archivo:** `MANUAL_V14.0_SUPER_DEFINITIVO.md`
- **Contenido:**
  - Descripción de 32 secciones
  - 617+ constantes con fórmulas
  - Unidades y rangos
  - Referencias bibliográficas
- **Volumen:** ~100 KB
- **Tiempo:** 2 horas

#### **6.2 | Guía de Troubleshooting** 🟢 BAJA
- **Archivo:** `TROUBLESHOOTING_V14.0.md`
- **Secciones:**
  - "¿Por qué no calcula X?"
  - "¿Por qué valor es 9999?" (clamping)
  - "¿Por qué es NaN?"
  - "¿Cómo depurar?"
- **Tiempo:** 45 minutos

#### **6.3 | Matriz de Dependencias** 🟢 BAJA
- **Archivo:** `MATRIZ_DEPENDENCIAS_V14.0.json`
- **Contenido:**
  ```json
  {
    "cajon_1": ["temp", "humedad"],
    "cajon_2": ["cajon_1", "presion"],
    "sección_26": ["cajon_1", "cajon_2", "cajon_4"]
  }
  ```
- **Uso:** Entender qué depende de qué
- **Tiempo:** 30 minutos

#### **6.4 | Changelog V14.0** 🟢 BAJA
- **Archivo:** `CHANGELOG_V14.0.md`
- **Incluir:** Todas las 167 constantes nuevas + qué cambió
- **Tiempo:** 30 minutos

#### **6.5 | API Reference V14.0** 🟢 BAJA
- **Archivo:** `API_REFERENCE_V14.0.md`
- **Endpoints:**
  - `GET /estado` → 617 constantes
  - `GET /estado/maestros` → solo principales
  - `GET /estado/completo` → con subfactores
  - `GET /estado/stream` → SSE
- **Ejemplos con curl**
- **Tiempo:** 45 minutos

#### **6.6 | Diagrama de Arquitectura** 🟢 BAJA
- **Archivo:** `ARQUITECTURA_V14.0.svg` o `.md` con ASCII
- **Visualizar:**
  - Flujo de datos sensor → bus_expander → API
  - 32 secciones
  - Desacoplamiento motor/UI
- **Tiempo:** 60 minutos

#### **6.7 | README actualizado** 🟢 BAJA
- **Archivo:** `README.md`
- **Actualizar:**
  - V14.0 SUPER DEFINITIVO
  - 617+ constantes
  - Link a documentación
- **Tiempo:** 15 minutos

---

## 🎯 **CATEGORÍA 7: INTEGRACIÓN DASHBOARD (10 TAREAS)**

### ⏳ PENDIENTE:

#### **7.1 | Panel Superior - Ubicación** 🟡 MEDIA
- **Mostrar:** Latitud, Longitud, Altitud, Origen
- **Actualizar:** Cada ciclo
- **Validación:** No vacío
- **Tiempo:** 15 minutos

#### **7.2 | Panel Superior - Astronomía** 🟡 MEDIA
- **Mostrar:** Arco Solar, Amanecer, Atardecer, Masa Óptica
- **Formato:** Gráficos de arco solar a lo largo del día
- **Tiempo:** 30 minutos

#### **7.3 | Panel Central - Índices Predictivos** 🟡 MEDIA
- **Mostrar:** K-Index, Lifted Index, CAPE, CIN
- **Gráficos:** Evolución horaria
- **Tiempo:** 30 minutos

#### **7.4 | Panel Central - Confort Térmico** 🟡 MEDIA
- **Mostrar:** PMV, PPD, WBGT, ASHRAE-55, Moho Risk
- **Indicadores:** Colores según riesgo
- **Tiempo:** 30 minutos

#### **7.5 | Panel Inferior - Calidad Aire** 🟡 MEDIA
- **Mostrar:** AOD, Visibilidad, Claridad, Categoría aerosol
- **Tabla:** Comparación con umbrales
- **Tiempo:** 20 minutos

#### **7.6 | Panel Inferior - Modelos Físicos** 🟡 MEDIA
- **Mostrar:** Monin-Obukhov, Fried r0, Visibilidad, ET
- **Gráficos:** Perfiles atmosféricos
- **Tiempo:** 45 minutos

#### **7.7 | Widget Luz Natural** 🟡 MEDIA
- **Mostrar:** Recomendación y valor
- **Datos:** Arco solar + luz ambiente
- **Actualización:** Cada 5 minutos
- **Tiempo:** 20 minutos

#### **7.8 | Widget Ritmo Circadiano** 🟡 MEDIA
- **Mostrar:** Recomendación de sueño
- **Datos:** Luz natural + hora
- **Gráfico:** Curva de melatonina teórica
- **Tiempo:** 30 minutos

#### **7.9 | Exportar Datos V14.0** 🟡 MEDIA
- **Formato:** CSV con todas 617 constantes
- **Endpoint:** `GET /exportar/v14-completo`
- **Compresión:** ZIP opcional
- **Tiempo:** 20 minutos

#### **7.10 | Validación Visual** 🟡 MEDIA
- **Dashboard debe mostrar:**
  - ✅ Ubicación (no vacía)
  - ✅ Arco solar (gráfico)
  - ✅ Índices predictivos (valores coherentes)
  - ✅ Confort (código de color)
  - ✅ Calidad aire (AOD visible)
  - ✅ Luz natural + Circadiano (recomendaciones)
- **Criterio de paso:** 6/6 widgets activos y con datos
- **Tiempo:** 15 minutos

---

## 📋 **CATEGORÍA 8: OTROS (VARIOS)**

### ⏳ PENDIENTE:

#### **8.1 | Validación Final de No Colapso** 🔴 ALTA
- **Test:** Ejecutar `main_asgi.py` y medir:
  - Tiempo respuesta `/estado`: < 50 ms
  - Memoria durante 1 ciclo: < 100 MB delta
  - CPU: < 20% promedio
  - Con 10 clientes simultáneos: sin degradación
- **Comando:**
  ```bash
  python main_asgi.py
  # En otra terminal:
  ab -n 1000 -c 10 http://localhost:8000/estado
  ```
- **Tiempo:** 15 minutos

#### **8.2 | Auditoría de Importaciones** 🟡 MEDIA
- **Validar:** Todos los imports en bus_expander.py
- **Verificar:** No hay dependencias circulares
- **Comando:** `python -m py_compile core/system/bus_expander.py`
- **Tiempo:** 5 minutos

#### **8.3 | Verificar Todos los Endpoints** 🟡 MEDIA
- **Endpoints a validar:**
  - `/estado` (617 constantes)
  - `/estado/maestros` (nuevos)
  - `/estado/completo` (nuevos)
  - `/estado/stream` (nuevo)
  - `/health` (debe funcionar)
  - `/api/panel/superior` (con ubicación)
  - `/api/panel/central` (con predicciones)
- **Comando:** `verificar_sistema.py`
- **Tiempo:** 20 minutos

#### **8.4 | Benchmark con Carga Real** 🟡 MEDIA
- **Test:** Enviar 1000 requests a `/estado` con GZIP
- **Medir:**
  - Tamaño JSON: antes/después compresión
  - Tiempo respuesta: 5ms, 10ms, 50ms?
  - Tasa de compresión real
- **Comando:**
  ```bash
  wrk -t4 -c100 -d30s http://localhost:8000/estado
  ```
- **Tiempo:** 10 minutos

#### **8.5 | Test de Estrés Completo** 🟡 MEDIA
- **Scenario 1:** Viento = 0 (calma)
- **Scenario 2:** Humedad = 100% (saturación)
- **Scenario 3:** Temperatura extrema (-40°C, +50°C)
- **Scenario 4:** Todo en topes (9999, 9, etc.)
- **Verificar:** No hay crashes, valores coherentes
- **Tiempo:** 30 minutos

---

## 🚀 **PLAN DE EJECUCIÓN RECOMENDADO**

### **FASE 1: VALIDACIÓN INMEDIATA (1 hora)**
1. ✅ Ejecutar test_ignicion_fisica_2026.py
2. ✅ Ejecutar test_sintonizacion_2026.py
3. ✅ Ejecutar verificar_sistema.py
4. ✅ Test no colapso con carga

**GO/NO-GO:** Si todo pasa → V14.0 FUNCIONAL

### **FASE 2: PERSISTENCIA Y UBICACIÓN (2 horas)**
5. Implementar cerebro_persistencia.py
6. Centralizar location_module.py
7. Restaurar amanecer_atardecer
8. Validar ubicación en JSON

**GO/NO-GO:** Si todo funciona → Datos persistentes correctos

### **FASE 3: DASHBOARD Y UX (3 horas)**
9. Integrar paneles con nuevas constantes
10. Widgets Luz Natural + Circadiano
11. Exportar datos V14.0

**GO/NO-GO:** Si UI es clara → Sistema usable

### **FASE 4: DOCUMENTACIÓN Y CERTIFICACIÓN (2 horas)**
12. Generar SHA256 de V14.0
13. Crear sello de élite
14. Documentación técnica completa

**GO/NO-GO:** V14.0 SUPER DEFINITIVO 100% CERTIFICADO

---

## 📊 **RESUMEN DE TIEMPO ESTIMADO**

| Fase | Horas | Prioridad |
|------|-------|-----------|
| Fase 1: Validación | 1 h | 🔴 CRÍTICA |
| Fase 2: Persistencia | 2 h | 🔴 CRÍTICA |
| Fase 3: Dashboard | 3 h | 🟡 IMPORTANTE |
| Fase 4: Documentación | 2 h | 🟢 DESEABLE |
| **TOTAL** | **8 h** | - |

---

## ✅ **CHECKLIST DE DECISIÓN**

- [ ] ¿Quieres que ejecute todos los tests de Fase 1 ahora?
- [ ] ¿Empezamos con persistencia de cerebro?
- [ ] ¿Priorizamos ubicación y astronomía?
- [ ] ¿O documentación técnica primero?

**¿Cuál es tu prioridad?**

---

**Documento generado:** 2 de febrero de 2026  
**Status:** AUDITORÍA COMPLETA - 52+ TAREAS IDENTIFICADAS
