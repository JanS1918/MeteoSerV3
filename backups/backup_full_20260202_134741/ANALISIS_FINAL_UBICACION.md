# ✅ ANÁLISIS FINAL - Ubicación y Astronomía en MeteoSerV3

## 📊 SITUACIÓN RESUMIDA

### ¿Qué pasó?
En la refactorización `main_asgi.py` → `app/ui/router.py + core/arcos_solares.py`:

| Componente | Estado | Ubicación |
|---|---|---|
| **Cálculo de arco solar** | ✅ Migrado | `core/arcos_solares.py` (L1-89) |
| **Amanecer/atardecer teórico** | ✅ Migrado | `core/arcos_solares.py` L1-89 |
| **Fase lunar** | ✅ Migrado | `core/arcos_solares.py` L92-140 |
| **Radiación solar teórica** | ❌ **FALTA** | - |
| **Lógica híbrida día/noche** | ❌ **FALTA** | - |
| **Índices de cielo nocturno** | ❌ **FALTA** | - |
| **Detección jerárquica ubicación** | ⚠️ Incompleta | `app/ui/router.py` L726-728 |
| **Integración en contexto** | ✅ Presente | `app/ui/router.py` L358-360 |

---

## 🔴 LO QUE REALMENTE FALTA

### CRÍTICA: Radiación Solar Teórica
```python
# FALTA EN: core/arcos_solares.py

def radiacion_teorica(lat_deg: float, dia_año: int, hora_decimal: float) -> float:
    """Calcular radiación solar extraterrestre en W/m²"""
    # Ecuación de Spencer (del backup)
    # Necesaria para:
    # - Validar anomalías de radiación
    # - Estimar nubosidad si falta sensor
    # - Física de Vector #26 (Rayleigh-Bucholtz)
```

**Impacto:** Motor Radiación/UV no valida sensor

### CRÍTICA: Lógica Híbrida Día/Noche
```python
# FALTA EN: app/ui/viewmodel.py o core/arcos_solares.py

def determinar_dia_hibrido(horas_sol, sensores, indices):
    """Sincronizar astronomía con sensores reales"""
    # Comparar amanecer astronómico vs radiación sensor
    # Si desvío > 90min: marcar inconsistencia
    # Necesaria para:
    # - Motor Luz Natural (detectar anomalías)
    # - Validar si sensor está roto
    # - Genera alertas de error
```

**Impacto:** Motor Luz Natural no funciona correctamente

### MEDIA: Índices de Cielo Nocturno
```python
# FALTA EN: app/ui/viewmodel.py L117-124

# En obtener_arcos_solares(), añadir:
datos_cielo = {
    'duracion_noche': duracion_noche,
    'ventana_observacion_nocturna': calcular_ventana(...),
    'indice_cielo_astronomico': 75.3,
    'indice_cielo_astronomico_nivel': 'bueno'
}
```

**Impacto:** Motor Nocturno devuelve datos genéricos

---

## 📋 CHECKLIST MÍNIMO DE COMPLETACIÓN

### Paso 1: Añadir `radiacion_teorica()` (30 min)
```bash
# Añadir a: core/arcos_solares.py
# Copiar pseudocódigo de: PSEUDOCODIGO_RESTAURACION_UBICACION.md
# Tests: 3 casos simples
```

### Paso 2: Añadir lógica híbrida (1 hora)
```bash
# Añadir a: core/arcos_solares.py
# Función: determinar_dia_hibrido(horas_sol, sensores)
# Retorna: indices con inconsistencia_luz, desvio_*
```

### Paso 3: Integrar en `app/ui/viewmodel.py` (30 min)
```bash
# En obtener_arcos_solares():
#   - Llamar determinar_dia_hibrido()
#   - Añadir radiacion_teorica a respuesta
#   - Calcular ventana_observacion_nocturna
```

### Paso 4: Inyectar en contexto de motores (15 min)
```bash
# En app/ui/router.py L774-777:
# contexto['ubicacion']['radiacion_teorica'] = ...
# contexto['indices']['inconsistencia_luz'] = ...
```

### Paso 5: Tests (30 min)
```bash
# tests/test_radiacion.py
# tests/test_hibrido_dia_noche.py
```

---

## 🎯 ESTADO DE MOTORES

| Motor | Necesita | Status | Acción |
|---|---|---|---|
| **Luz Natural** | Radiación teórica + Híbrido | 🔴 ROTO | Urgente |
| **Ritmo Circadiano** | Amanecer/atardecer (✅) | ⚠️ PARCIAL | Verificar |
| **Motor Nocturno** | Índices cielo | 🟠 DEGRADADO | Añadir índices |
| **Ambiental** | Radiación teórica | ⚠️ PARCIAL | Si radiación |
| **Confort** | Ubicación (✅) | ✅ OK | - |
| **Radiación/UV** | Radiación teórica | 🟠 DEGRADADO | Urgente |

---

## 🚀 IMPLEMENTACIÓN RECOMENDADA

### Opción A: Quick Fix (1-2 horas)
```python
# core/arcos_solares.py - Añadir al final

def radiacion_teorica(lat_deg, dia, hora):
    """Radiación solar teórica (Spencer simplificado)"""
    # Pseudocódigo: 20 líneas
    
def determinar_dia_hibrido(horas_sol, radiacion, uv):
    """Lógica híbrido día/noche"""
    # Pseudocódigo: 40 líneas
```

**Resultado:** 3 motores restaurados a funcional

### Opción B: Completo (3-4 horas)
```python
# core/arcos_solares.py - COMO ARRIBA

# core/astronomy_advanced.py - NUEVO MÓDULO
# - calcular_ventana_observacion_nocturna()
# - clasificar_indice_cielo()
# - integracion completa

# Tests completos
```

**Resultado:** 6 motores funcionan perfectamente

---

## 📝 REFERENCIAS

### Documentos Generados:
1. **RESUMEN_UBICACION_ASTRONOMIA_PERDIDAS.md** - Visión general (¿qué pasó?)
2. **PSEUDOCODIGO_RESTAURACION_UBICACION.md** - Cómo codificar (pseudocódigo)
3. **MAPEO_DEPENDENCIAS_MOTORES.md** - Dónde se usa (impacto por motor)
4. **CHECKLIST_RESTAURACION_UBICACION.md** - Plan completo (todos los pasos)
5. **ACTUALIZACION_HALLAZGOS_UBICACION.md** - Búsquedas en codebase
6. **ANALISIS_FINAL_UBICACION.md** - Este documento (resumen ejecutivo)

### Código a Copiar:
- Backup: `git show backup/ojo_20260202_102049:main_asgi.py | head -1730`
- Líneas específicas: 1548 (radiación), 1650 (híbrido), 1693 (cielo)

---

## ⏱️ ESTIMADO FINAL

| Tarea | Tiempo | Prioridad |
|---|---|---|
| Radiación teórica | 30 min | 🔴 CRÍTICA |
| Lógica híbrida | 1 h | 🔴 CRÍTICA |
| Integración en viewmodel | 30 min | 🔴 CRÍTICA |
| Tests | 30 min | 🟠 MEDIA |
| Documentación | 30 min | 🟠 MEDIA |
| **TOTAL** | **3 horas** | - |

---

## ✅ PRÓXIMO PASO

Ejecutar:
```bash
cd c:\Users\kioko\Desktop\MeteoSerV3
# Abrir: PSEUDOCODIGO_RESTAURACION_UBICACION.md → Función 5 & 6 & 8
# Crear: core/arcos_solares.py + funciones
# Integrar: app/ui/viewmodel.py
# Tests: pytest tests/test_radiacion.py -v
```

---

*Generado: 2 Feb 2026*
*Estado: LISTO PARA ACCIÓN INMEDIATA*
*Estimado: 3 horas de trabajo*
