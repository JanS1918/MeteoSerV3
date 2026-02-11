# ÍNDICE TÉCNICO - PATRÓN BUS-FIRST IMPLEMENTADO
**Fecha:** 11 de febrero de 2026  
**Propósito:** Referencia rápida de módulos, líneas y funciones del patrón bus-first

---

## 🗂️ Estructura de Directorios Relevantes

```
MeteoSerV3/
├── core/
│   ├── indices/
│   │   ├── astronomia_recursiva.py          🟢 Publicador: AstronomiaRecursiva
│   │   ├── environmental_indices.py         🟢 Consumidor: Bus-first implementado
│   │   ├── contexto_solar.py                🟢 Consumidor: Bus-first implementado (NUEVO)
│   │   └── radiacion_hibrida.py             🟢 Consumidor: Bus-first implementado
│   ├── system/
│   │   ├── bus_expander.py                  🔴 PUBLICADOR CENTRAL
│   │   ├── bus.py                           🟢 Interfaz desdel bus
│   │   └── system_manager.py                🟢 Gestor del sistema
│   ├── integration/
│   │   └── ecowitt_receiver.py              🟢 Consumidor: Bus-first implementado
│   ├── context/
│   │   └── contexto_maestro_global.py       🟢 Consumidor: Bus-first implementado
│   ├── location/
│   │   └── location_module.py               🟢 Fallback: location_module functions
│   └── arcos_solares.py                     🟢 Consumidor: Bus-first implementado (NUEVO)
├── app/
│   └── ui/
│       └── router.py                        🟢 Consumidor: Bus-first implementado
├── routers/
│   └── fusion_endpoints.py                  🟢 Consumidor: Bus-first implementado (NUEVO)
├── main_asgi.py                             🟢 Consumidor: Bus-first implementado
└── DOCUMENTACIÓN NUEVA:
    ├── GUIA_PATRON_BUS_FIRST_ASTRONOMIA.md   📖 Guía técnica completa
    ├── PLAN_DESPLIEGUE_BUS_FIRST.md          📋 Plan de despliegue
    ├── AUDITORIA_FINAL_BUS_FIRST.md          📊 Detalles técnicos
    └── RESUMEN_EJECUTIVO_BUS_FIRST.md        📈 Resumen ejecutivo
```

---

## 🔅 Publicador Central: BusExpander

### Archivo
**`core/system/bus_expander.py`**

### Función Principal
```python
async def _publish_astronomia(self)
```
**Líneas:** 1973-2170  
**Frecuencia:** Cada ciclo del sistema  
**Responsable de publicar:**
- `elevacion_solar_deg` ← **DATOS SOLARES PRIMARIOS**
- `azimut_solar_deg`
- `distancia_tierra_sol_AU`
- Subfactores (refracción, delta-T, etc.)

### Métodos Auxiliares
- `_require_sensor()` - Línea 315
- `_validate_physics()` - Línea 332

### Lógica de Publicación
1. Obtiene datos de sensores en tiempo real
2. Valida rangos físicos
3. Crea instancia de `AstronomiaRecursiva`
4. Llama `calcular_posicion_solar_nrel_spa()`
5. Publica resultados en bus con timestamp

---

## 🟢 Consumidores (Bus-First Pattern)

### 1. app/ui/router.py
**Líneas con bus-first:** 80, 397, 782, 846, 1654, 2549, 2667  
**Patrón:** Lee `elevacion_solar_deg` del bus en múltiples endpoints  
**Fallback:** Calcula localmente si no está disponible

**Ubicaciones específicas:**
```python
# Línea 80: Lectura de elevación solar
bus = obtener_bus()
if bus:
    elevacion = bus.leer("elevacion_solar_deg")

# Línea 397: En endpoint de contexto temporal
# Línea 782: En endpoint de radiación
# etc.
```

### 2. routers/fusion_endpoints.py
**Líneas con bus-first:** 385-408 ⭐ MODIFICADO HOY  
**Patrón:** Bus-first para detección de anomalías de sensores  
**Función:** `get_dashboard_data()` (línea 316)

**Cambio aplicado:**
```python
# Línea 385-408: Bus-first con fallback
try:
    bus = obtener_bus()
    if bus:
        elevacion_solar_bus = bus.leer("elevacion_solar_deg")
        if elevacion_solar_bus is not None:
            elevacion_solar = float(elevacion_solar_bus)
        else:
            # Fallback a cálculo local (línea 393-401)
            from core.indices.radiacion_hibrida import PiranometroHibrido
            pir = PiranometroHibrido()
            pos_solar = pir.calcular_posicion_solar(dt_now.now())
            elevacion_solar = pos_solar.get("elevacion_deg", 0)
except Exception as e:
    logger.debug(f"Error: {e}")
```

### 3. core/indices/contexto_solar.py
**Líneas con bus-first:** 118-143 ⭐ MODIFICADO HOY  
**Patrón:** Bus-first para contexto temporal solar  
**Clase:** `ContextoSolar`  
**Función:** `calcular_contexto()`

**Cambio aplicado:**
```python
# Línea 118-143: Bus-first pattern implementado
elevacion = None
azimut = None
try:
    from core.system.bus import obtener_bus
    bus = obtener_bus()
    if bus:
        elevacion_bus = bus.leer("elevacion_solar_deg")
        azimut_bus = bus.leer("azimut_solar_deg")
        if elevacion_bus is not None and azimut_bus is not None:
            elevacion = float(elevacion_bus)
            azimut = float(azimut_bus)
except:
    pass

# Fallback: Línea 136-143
if elevacion is None or azimut is None:
    if self.astro:
        try:
            pos_solar = self.astro.calcular_posicion_solar_nrel_spa(...)
            elevacion = pos_solar.get("elevacion_aparente_deg", 0.0)
            azimut = pos_solar.get("azimut_deg", 0.0)
        except Exception as e:
            logger.warning(f"Error: {e}")
            elevacion, azimut = self._calcular_solar_fallback(fecha_hora)
```

### 4. core/arcos_solares.py
**Líneas con bus-first:** 199-227 ⭐ MODIFICADO HOY  
**Patrón:** Bus-first en función utilitaria  
**Función:** `calcular_posicion_sol()` (línea 160)

**Cambio aplicado:**
```python
# Línea 199-227: Bus-first + fallback
elevacion_solar = None
azimut_solar = None

# ⚛️ BUS-FIRST: Intentar obtener del bus
try:
    from core.system.bus import obtener_bus
    bus = obtener_bus()
    if bus:
        elevacion_solar_bus = bus.leer("elevacion_solar_deg")
        azimut_solar_bus = bus.leer("azimut_solar_deg")
        if elevacion_solar_bus is not None and azimut_solar_bus is not None:
            elevacion_solar = float(elevacion_solar_bus)
            azimut_solar = float(azimut_solar_bus)
except:
    pass

# Fallback: calcular localmente
if elevacion_solar is None or azimut_solar is None:
    try:
        from core.indices.astronomia_recursiva import AstronomiaRecursiva
        astro = AstronomiaRecursiva(lat, lon, altitud_val)
        # ... cálculo local
    except:
        elevacion_solar = None
        azimut_solar = None
```

### 5. core/indices/environmental_indices.py
**Líneas con bus-first:** 3455-3490  
**Patrón:** Bus-first para índices ambientales  
**Función:** `_calcular_nubosidad_estimada()`

**Implementación:**
```python
# Línea 3455: Comentario indicando patrón
# Preferir elevación solar SPA NREL desde bus

# Línea 3460-3490: Lógica bus-first
elevacion_solar_deg = None
try:
    if bus:
        elevacion_solar_deg = bus.leer("elevacion_solar_deg")
except:
    pass

if elevacion_solar_deg is None:
    try:
        from core.indices.astronomia_recursiva import AstronomiaRecursiva
        astro = AstronomiaRecursiva(lat, lon, alt)
        resultado = astro.calcular_posicion_solar_nrel_spa(...)
        elevacion_solar_deg = resultado.get("elevacion_aparente_deg")
    except:
        pass
```

### 6. core/indices/radiacion_hibrida.py
**Líneas con bus-first:** 175-230  
**Patrón:** Bus-first en clase `PiranometroHibrido`  
**Método:** `calcular_posicion_solar()`

### 7. core/integration/ecowitt_receiver.py
**Patrón:** Bus-first implementado  
**Función:** Integra datos de sensores Ecowitt con contexto astronómico

### 8. core/context/contexto_maestro_global.py
**Patrón:** Bus-first implementado  
**Función:** `actualizar_astronomia()`

### 9. main_asgi.py
**Patrón:** Bus-first implementado  
**Uso:** Contexto astronómico en inicio del sistema

---

## 📚 Clase de Cálculo: AstronomiaRecursiva

### Archivo
**`core/indices/astronomia_recursiva.py`**

### Método Principal
```python
def calcular_posicion_solar_nrel_spa(
    self,
    fecha_utc: datetime,
    presion_hpa: float,
    temperatura_c: float,
    humedad_fraccion: float
) -> Dict[str, float]
```
**Línea:** 51  
**Retorna:** Dict con elevación, azimuth, refracción, etc.

### Inputs Requeridos
- `fecha_utc`: Momento UTC
- `presion_hpa`: Presión barométrica (hPa)
- `temperatura_c`: Temperatura aire (°C)
- `humedad_fraccion`: Humedad (0-1)

### Outputs
- `elevacion_aparente_deg`: Elevación con refracción
- `elevation_true_deg`: Elevación verdadera
- `azimut_deg`: Azimuth desde norte
- `refraccion_arcmin`: Refracción (arcmin)
- `distancia_tierra_sol_AU`: Distancia AU
- `julian_day_ephemeris`: JDE para cálculos
- `delta_t_segundos`: Delta-T

---

## 🔗 Flujo de Datos (Diagrama ASCII)

```
┌─────────────────────────────────────────┐
│         PUBLICADOR CENTRAL              │
│    BusExpander._publish_astronomia()    │
│              (Línea 1973)               │
└─────────────────┬───────────────────────┘
                  │
                  ├─► Sensores en tiempo real
                  ├─► AstronomiaRecursiva.calcular_posicion_solar_nrel_spa()
                  └─► Publicar en bus:
                      - elevacion_solar_deg
                      - azimut_solar_deg
                      - etc.
                      │
        ┌─────────────┼─────────────────────┐
        │             │                     │
    ┌───▼───┐     ┌──▼──┐            ┌─────▼──────┐
    │app/   │     │core/│            │routers/    │
    │router │     │indices/          │fusion_     │
    │       │     │                  │endpoints   │
    └───────┘     │contexto_solar.py │            │
                  │(Línea 118)       └────────────┘
                  │
                  │ ⚛️  BUS-FIRST PATTERN:
                  │
                  ├─► 1. Intentar leer del bus ✅
                  │      └─► Si éxito, usar datos
                  │
                  ├─► 2. Fallback: Calcular localmente
                  │      └─► AstronomiaRecursiva()
                  │
                  └─► 3. Último recurso: Valor por defecto
                         └─► elevacion = 45.0 (mediodía)
```

---

## 📊 Checklist de Implementación

### Bus-First Checklist para Nuevos Módulos

```python
# ✅ PASO 1: Import y obtención del bus
try:
    from core.system.bus import obtener_bus
    bus = obtener_bus()
except:
    bus = None

# ✅ PASO 2: Intentar leer del bus
elevacion_solar = None
if bus:
    try:
        elevacion_solar = bus.leer("elevacion_solar_deg")
    except:
        pass

# ✅ PASO 3: Validar que no es None
if elevacion_solar is None:
    # PASO 4: Fallback local
    try:
        from core.indices.astronomia_recursiva import AstronomiaRecursiva
        astro = AstronomiaRecursiva(lat, lon, alt)
        resultado = astro.calcular_posicion_solar_nrel_spa(...)
        elevacion_solar = resultado.get("elevacion_aparente_deg")
    except:
        # PASO 5: Último recurso
        elevacion_solar = 45.0

# ✅ PASO 6: Log/Debug de fuente
logger.debug(f"Elevación solar: {elevacion_solar}° (fuente: {'bus' if obtuvo_de_bus else 'local'})")
```

---

## 🔍 Búsqueda Rápida de Código

| Qué busco | Dónde | Referencia |
|-----------|-------|-----------|
| Publicación de datos solares | `bus_expander.py` | Línea 1973 |
| Lectura en router | `app/ui/router.py` | Línea 80 |
| Contexto temporal | `contexto_solar.py` | Línea 118 |
| Cálculo local (fallback) | `astronomia_recursiva.py` | Línea 51 |
| Patrón bus-first | `GUIA_PATRON_BUS_FIRST_ASTRONOMIA.md` | Completo |
| Plan de despliegue | `PLAN_DESPLIEGUE_BUS_FIRST.md` | Completo |

---

## 🧪 Tests Relacionados

**Ubicación:** `tests/`  
**Comando:** `python -m pytest tests/ -q`  
**Resultado:** ✅ 166 passed, 3 skipped

Tests que validan patrón:
- Tests de integration (módulos principales)
- Tests de astronómicos
- Tests de contexto temporal

---

## 🔗 Links Internos

- [Guía Técnica Completa](GUIA_PATRON_BUS_FIRST_ASTRONOMIA.md)
- [Plan de Despliegue](PLAN_DESPLIEGUE_BUS_FIRST.md)
- [Auditoría Técnica](AUDITORIA_FINAL_BUS_FIRST.md)
- [Resumen Ejecutivo](RESUMEN_EJECUTIVO_BUS_FIRST.md)

---

**Última actualización:** 2026-02-11 15:50 UTC

