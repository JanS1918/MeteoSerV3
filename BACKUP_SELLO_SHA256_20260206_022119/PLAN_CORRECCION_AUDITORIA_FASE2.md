# 🚨 PLAN DE CORRECCIONES - AUDITORÍA FASE 2

## PRIORIDADES CRÍTICAS

### PRIORIDAD 1 - CORDONES SANITARIOS 🔴
**Reparar TODA la cadena de gravedad que está quebrada**

#### Acción 1.1: Centralizar gravedad en todos los módulos
```
Archivos a modificar: 6
Líneas a cambiar: 12 (9 con gravity, 3 con pressure)
Patrón: Cambiar g = 9.81 o g = 9.80665 por lectura de Bus
```

Tabla de cambios:

| Archivo | Línea | Actual | Nuevo | Motivo |
|---------|-------|--------|-------|--------|
| core/atmosphere/isa_calculator.py | 47 | `g = 9.81` | `g = self.bus.leer("gravedad_dinamica") or 9.80272394` | ISA dinámica |
| core/indices/atmospheric_profiler.py | 140 | `g = 9.81` | `g = self.bus.leer("gravedad_dinamica") or 9.80272394` | Richardson |
| core/indices/atmospheric_profiler.py | 195 | `g = 9.81` | `g = self.bus.leer("gravedad_dinamica") or 9.80272394` | Gradiente |
| core/indices/advanced_predictive_indices.py | 417 | `g = 9.81` | `g = self.bus.leer("gravedad_dinamica") or 9.80272394` | Índice 1 |
| core/indices/advanced_predictive_indices.py | 870 | `g = 9.81` | `g = self.bus.leer("gravedad_dinamica") or 9.80272394` | Índice 2 |
| core/indices/advanced_predictive_indices.py | 1038 | `g = 9.81` | `g = self.bus.leer("gravedad_dinamica") or 9.80272394` | Índice 3 |
| core/indices/advanced_physics_models.py | 477 | `9.81` en CAPE | `self.bus.leer("gravedad_dinamica") or 9.80272394` | CAPE crítico |
| core/indices/advanced_physics_models.py | 483 | `9.81` en CAPE | `self.bus.leer("gravedad_dinamica") or 9.80272394` | CAPE crítico |
| core/indices/environmental_indices.py | 1448 | `g = 9.80665` | `g = self.bus.leer("gravedad_dinamica") or 9.80272394` | Humedad |
| core/indices/physics_numba.py | 35 | `G = 9.80665` | `# REVISAR: Numba no permite runtime` | Numba issue |

#### Acción 1.2: Reparar Numba Global
**Problema**: `physics_numba.py` línea 35 tiene `G = 9.80665` como constante de compilación
```python
# ACTUAL:
G = 9.80665  # m/s² (esto se compila en bytecode)

# OPCIÓN A - Remover numba y usar valor dinámico:
# Remover @njit decorador, cambiar a lectura de Bus

# OPCIÓN B - Crear wrapper que no use numba para gravedad
def obtener_gravedad():
    return bus.leer("gravedad_dinamica") or 9.80272394

# OPCIÓN C - Aceptar gravedad como parámetro en funciones numba
@njit
def calcular_algo(x, y, g):  # ← g como parámetro
    return ...
```

### PRIORIDAD 2 - COORDENADAS FALLBACK 🟡
**Unificar 4 fallbacks diferentes a 1 solo**

#### Acción 2.1: Identificar TODAS las coordenadas fallback
```
Encontradas 4 versiones diferentes:
1. main_asgi.py: 41.5507°N, -2.397°E (NOTA: lon negativa, debe ser positiva)
2. ecowitt_receiver.py: 41.5507°N, -2.397°E (igual a 1)
3. advanced_physics_models.py: 41.5513°N (solo latitud)
4. bus_expander.py: 41.55°N (truncada)
```

#### Acción 2.2: Crear constante global para fallback
**Archivo**: Crear o editar `core/config/CONSTANTES_ESTACION.py`
```python
# ARGENTONA - COORDENADAS SELLADAS (8 decimales)
ESTACION_COORDENADAS = {
    'latitud': 41.55326700,      # 8 decimales
    'longitud': 2.39684500,      # 8 decimales (POSITIVO para Este)
    'altitud': 118.0,             # metros
    'nombre': 'Argentona, Catalunya'
}

FALLBACK_COORDENADAS = ESTACION_COORDENADAS  # Siempre usar esto

# GRAVEDAD SELLADA
ESTACION_GRAVEDAD = 9.80272394   # Somigliana-Helmert (Argentona)
```

#### Acción 2.3: Reemplazar todos los fallback
```
main_asgi.py línea 1831-1832:
   OLD: latitud = 41.5507; longitud = -2.397
   NEW: lat, lon = FALLBACK_COORDENADAS['latitud'], FALLBACK_COORDENADAS['longitud']

ecowitt_receiver.py línea 830-831:
   OLD: lat = indices.get("latitud", 41.5507)
   NEW: lat = indices.get("latitud", FALLBACK_COORDENADAS['latitud'])

advanced_physics_models.py línea 270:
   OLD: latitud = 41.5513
   NEW: latitud = FALLBACK_COORDENADAS['latitud']

bus_expander.py línea 560:
   OLD: lat = self.system.location.get("latitud", 41.55)
   NEW: lat = self.system.location.get("latitud", FALLBACK_COORDENADAS['latitud'])
```

### PRIORIDAD 3 - PRESIÓN NIVEL MAR INCONSISTENTE 🟡
**Unificar 3 cálculos diferentes de presión nivel mar**

#### Acción 3.1: Revisar línea 4691 de bus_expander.py
```python
# ¿Por qué se hardcodea 1013.25?
# ¿Debería usar fórmula barométrica como línea 543?
# ¿O es un valor de fallback para caso de error?
```

#### Acción 3.2: Estandarizar
**Si línea 4691 es un fallback**, cambiar a:
```python
# OLD:
self.bus.publicar("presion_nivel_mar", 1013.25, "hPa")

# NEW:
presion_mar = presion_estacion * exp(gravedad * altitud / (R_especifico * T_media))
self.bus.publicar("presion_nivel_mar", presion_mar / 100.0, "hPa")
```

---

## ESTRATEGIA DE IMPLEMENTACIÓN

### Fase A - Preparación
1. ✅ Crear `CONSTANTES_ESTACION.py` con valores sellados
2. ✅ Crear script de validación para verificar cambios
3. ✅ Hacer backup de archivos originales

### Fase B - Implementación Módulo por Módulo
**Orden de precedencia** (módulos fundacionales primero):
1. `isa_calculator.py` (usado por muchos)
2. `atmospheric_profiler.py` (estabilidad)
3. `environmental_indices.py` (humedad)
4. `advanced_physics_models.py` (CAPE crítico)
5. `advanced_predictive_indices.py` (3 ubicaciones)
6. `physics_numba.py` (ESPECIAL - revisar arquitectura)

### Fase C - Fallback de Coordenadas
1. Crear `CONSTANTES_ESTACION.py`
2. Reemplazar en 4 ubicaciones
3. Verificar que todos usen mismos valores

### Fase D - Presión Nivel Mar
1. Revisar lógica de línea 4691
2. Unificar si es posible
3. Documentar si hay motivo para 3 versiones

### Fase E - Validación y Testing
1. Script de verificación de gravedad en cada módulo
2. Comparación de CAPE antes/después
3. Comparación de presión nivel mar antes/después
4. Validación de coordenadas a 8 decimales en UI

---

## IMPACTO ESTIMADO

### Módulos Afectados
- ✅ ISA Calculator → Todas las atmósferas
- ✅ Atmospheric Profiler → Estabilidad
- ✅ Environmental Indices → Humedad, punto rocío
- ✅ Advanced Physics → CAPE (weather prediction)
- ✅ Predictive Indices → 3+ índices
- ⚠️  Physics Numba → Requiere revisar JIT

### Cálculos que van a cambiar
- UTCI (sensación térmica) → Pequeña mejora
- CAPE → Cambio significativo (~2-3% más preciso)
- Presión nivel mar → Variación según altitud
- Richardson Number → Mejora en estabilidad
- Punto rocío → Pequeña mejora

### Riesgo de Regresión
- BAJO: Solo cambia valor de gravedad
- Las fórmulas matemáticas no cambian
- Fallbacks más consistentes (menos divergencia)

---

## CHECKLIST FINAL

### Pre-Cambios
- [ ] Backup completo de codebase
- [ ] Crear CONSTANTES_ESTACION.py
- [ ] Crear script de validación
- [ ] Documentar valores esperados vs actuales

### Cambios Implementados
- [ ] isa_calculator.py línea 47
- [ ] atmospheric_profiler.py líneas 140, 195
- [ ] advanced_predictive_indices.py líneas 417, 870, 1038
- [ ] advanced_physics_models.py líneas 477, 483
- [ ] environmental_indices.py línea 1448
- [ ] physics_numba.py línea 35 (ESPECIAL)
- [ ] main_asgi.py líneas 1831-1832
- [ ] ecowitt_receiver.py líneas 830-831
- [ ] advanced_physics_models.py línea 270
- [ ] bus_expander.py línea 560
- [ ] bus_expander.py línea 4691 (revisar)

### Post-Cambios
- [ ] Ejecutar script de validación
- [ ] Comparar CAPE antes/después
- [ ] Verificar coordenadas a 8 decimales
- [ ] Prueba de presión nivel mar
- [ ] Logs de gravedad en todos los módulos

---

## COMANDANTE: ¿AUTORIZAS IMPLEMENTACIÓN FASE A?
