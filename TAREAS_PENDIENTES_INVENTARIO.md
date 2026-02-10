# 📋 TAREAS PENDIENTES - INVENTARIO COMPLETO

**Fecha**: 2 de febrero de 2026  
**Origen**: Exploración exhaustiva del sistema durante restauración V2.6  
**Estado**: NO INICIAR - Solo documentación de hallazgos

---

## 🔴 TAREA 1: Conversión Masiva al Bus (CRÍTICO)

**Prioridad**: MÁXIMA  
**Progreso actual**: 16% (4 de 25 predicciones)  
**Archivo**: `scripts/conversion_masiva_bus.py`

**Pendiente**:
- 21 métodos de predicción sin convertir al patrón consumir-publicar
- Variables críticas esperando:
  - `evapotranspiracion_penman_monteith`
  - `indice_utci`
  - `tendencia_barometrica` (13 consumidores)
  - `helada_radiativa` (4 consumidores)

**Impacto**: Bloquea auditoría dinámica, eficiencia al 70% no alcanzada

---

## 🟠 TAREA 2: Conectar Botones de UI

**Prioridad**: ALTA  
**Archivo**: `app/static/panel_2026.js` (líneas 667, 672, 682, 687)

**Botones con "Funcionalidad pendiente"**:
- 📰 Noticias
- 🤖 Asistente
- ⚙️ Configuración
- 💬 Feedback

**Backend existe**: `core/feedback_manager.py` (116 líneas implementadas)  
**Falta**: Conectar frontend con endpoints API

---

## 🟡 TAREA 3: Completar Statistical Brain

**Prioridad**: MEDIA  
**Archivo**: `core/engines/statistical_brain.py` línea 442

**Pendiente**:
- Implementar cálculo completo de Kullback-Leibler
- Divergencia KL para comparar distribuciones

**Funciones ya implementadas**: Mann-Kendall, Sen, Granger Causality

---

## 🟡 TAREA 4: Omnipotencia V1.5 - Detección Real

**Prioridad**: MEDIA  
**Archivo**: `core/omnipotence/omnipotence_simple.py`

**Implementado**:
- ✅ Endpoints básicos (`/admin/omnipotence/*`)
- ✅ Estructura de datos

**Pendiente**:
- ❌ Escaneo real de USB
- ❌ Detección automática Bluetooth
- ❌ Asimilación de drivers
- ❌ Instalación automática de hardware

---

## 🟡 TAREA 5: Integrar Cetrería en Dashboard

**Prioridad**: MEDIA  
**Archivos**:
- `core/indices/cetreria/cetreria_indices.py` (177 líneas)
- `tools/calibrar_cetreria.py`
- `data/cetreria_calibracion.json`

**Estado**: Código completo (100%), integración 0%  
**Pendiente**: Agregar a endpoints principales y dashboard

---

## 🟢 TAREA 6: Implementar Ideas Master

**Prioridad**: BAJA (documentación conceptual)  
**Archivo**: `ideas.py` (1953 líneas)

**Conceptos documentados, NO implementados**:
- Huella Atmosférica Personal (PAS) - Identificación de personas
- Temperatura Operativa Real (OT) - Cálculo completo
- Diagnóstico del Edificio - 15 índices (moho, oxidación, condensación)
- Detección de luz artificial
- Motor conversacional

**Nota**: Son ideas para futuro desarrollo, no bugs

---

## 🔵 TAREA 7: Automatizar Tests

**Prioridad**: MEJORA  
**Documento**: `PERSISTENCIA_Y_SALUD_INTERIOR_v1.4.md` línea 451

**Pendiente**:
- Configurar CI/CD
- Automatizar tests existentes (manuales actualmente)

**Tests existentes**:
- `test_boot.py`
- `test_statistical_brain.py`
- `test_visibilidad_factor_z.py`
- `test_ignicion_fisica_2026.py`

---

## 🔵 TAREA 8: Arreglar Deprecation Warnings

**Prioridad**: MANTENIMIENTO  
**Archivo log**: `uvicorn.log`

**3 tipos de warnings**:

1. `datetime.utcnow()` → `datetime.now(timezone.UTC)`
   - Ubicación: `main_asgi.py` línea 1077

2. `datetime.utcfromtimestamp()` → `datetime.fromtimestamp(UTC)`
   - Ubicación: `core/indices/environmental_indices.py` línea 965

3. FastAPI `on_event` → `lifespan handlers`
   - Ubicación: `main_asgi.py` (decoradores startup/shutdown)

---

## 🔵 TAREA 9: Implementar Bloques Funcionales

**Prioridad**: EXPERIMENTAL  
**Archivo**: `core/ideas_master_blocks.py` (185 líneas)

**Estado**: Solo esqueletos (return strings)  
**Clases creadas**: BloqueA-G (Sensores, Reglas, IA, Watchdog, Hardening, Conversacional, Cluster)

---

## 📊 RESUMEN

| Tarea | Prioridad | Completitud | Bloquea |
|-------|-----------|-------------|---------|
| Conversión Bus | 🔴 CRÍTICA | 16% | Auditoría dinámica |
| Botones UI | 🟠 ALTA | 0% | Experiencia usuario |
| Statistical Brain | 🟡 MEDIA | 90% | - |
| Omnipotencia | 🟡 MEDIA | 30% | - |
| Cetrería | 🟡 MEDIA | 100% código | - |
| Ideas Master | 🟢 BAJA | 0% | - |
| Tests CI/CD | 🔵 MEJORA | - | - |
| Deprecations | 🔵 MANT | - | - |
| Bloques Func | 🔵 EXPER | 5% | - |

---

**IMPORTANTE**: NO INICIAR estas tareas sin confirmación explícita.  
Este documento es solo un inventario de hallazgos durante la restauración V2.6.
