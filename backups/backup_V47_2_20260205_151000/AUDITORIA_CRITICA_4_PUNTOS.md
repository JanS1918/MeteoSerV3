# 🛡️ AUDITORÍA CRÍTICA V14.1 - ANÁLISIS DE 4 PUNTOS

**Fecha:** 2 Febrero 2026  
**Estado:** INCOMPLETO - PROBLEMAS GRAVES IDENTIFICADOS

---

## 📋 VERIFICACIÓN DE 4 PUNTOS CRÍTICOS

### ❌ PUNTO 1: ¿DÓNDE SE CARGA SRTM EN system.location?

**Búsqueda:** `core/location/location_engine.py`  
**Resultado:** **NO EXISTE ALTITUD**

```python
class LocationEngine:
    def __init__(self, base_dir: Optional[Path] = None):
        self.lat = None
        self.lon = None
        self.manual = False
        # ↑ NO HAY self.altitud
```

**Método get_coordinates():**
```python
def get_coordinates(self, system) -> Optional[Dict[str, float]]:
    return {"lat": self.lat, "lon": self.lon, "origen": "manual"}
    # ↑ Solo lat/lon - SIN altitud
```

**CRÍTICO EN bus_expander.py línea 186:**
```python
altitud = self.system.location.get("altitud", 0.0)  # ← ESTO VA A FALLAR
```
- `system.location` es un **LocationEngine OBJECT**, no un dict
- LocationEngine NO tiene método `.get()`
- Resultado: `AttributeError` - El código colapsará

---

### ❌ PUNTO 2: ¿QUIÉN ACTUALIZA last_data_update_time?

**Búsqueda en codebase:**
- `grep last_data_update_time` → Solo 1 match en main_asgi.py línea 1110
- `grep last_update` → SIN RESULTADOS
- `grep sensor_update_time` → SIN RESULTADOS

**Ubicación en /health:**
```python
last_data_update = getattr(system, 'last_data_update_time', time.time())
# ↑ GETATTR CON DEFAULT = Siempre usa time.time() ahora
```

**CRÍTICO:** 
- Variable NO EXISTE en system_core.py
- Nunca se actualiza en `actualizar_sensor()`
- Watchdog 64s **NUNCA ACTIVARÁ** porque siempre devuelve "hace 0 segundos"

---

### ❌ PUNTO 3: ¿EL CÓDIGO LEE METEOSER_SRTM_FORCE?

**Búsqueda:** `grep METEOSER_SRTM_FORCE`  
**Resultado:** **SIN MATCHES EN TODO EL CÓDIGO**

- Script la configura: ✅ `$env:METEOSER_SRTM_FORCE='1'`
- Código la LEE: ❌ **NUNCA**
- Consumidor: ❌ **NO EXISTE**

**Variable muere sin ser leída.**

---

### ❓ PUNTO 4: ¿CUÁNTAS DE 617 CONSTANTES SON NO-NULL?

**Búsqueda:** `core/system/bus_expander.py`

**Lo que se publica:**
- Sección 1-9: ~150 constantes
- Sección 10-18: ~160 constantes  
- Sección 19-25: ~140 constantes (PROMISE pero incompleto)
- **Total teórico:** 450+

**Problema:**
```python
bus_keys = list(system.bus.datos.keys())  # ← Solo LLAVES
# No valida que sean != 0, != None, != default
```

**Riesgo:** Muchas constantes publicadas con valor 0.0 o None (especialmente si SRTM falla)

---

## 🔴 RESUMEN CRÍTICO

| Punto | Estado | Riesgo | Severidad |
|-------|--------|--------|-----------|
| 1. SRTM Carga | ❌ NO EXISTE | AttributeError en line 186 | **CRÍTICO** |
| 2. Watchdog Update | ❌ NO IMPLEMENTADO | Nunca activará alertas | **CRÍTICO** |
| 3. SRTM_FORCE Consumo | ❌ NO SE LEE | Variable inerte | **CRÍTICO** |
| 4. 617 Constantes Válidas | ❓ SIN VALIDAR | Muchas zeros falsos | **MEDIO** |

---

## 🔧 QUÉ NECESITA ARREGLARSE (ORDEN TÁCTICA)

### FASE 1: SRTM LOADING (CRÍTICO)
```
1. Extender LocationEngine con método get_altitude_srtm()
2. Llenar system.location.altitud desde datos SRTM reales
3. Hacerlo callable como dict en bus_expander
```

### FASE 2: WATCHDOG TIMESTAMP (CRÍTICO)
```
1. Agregar system.last_data_update_time = time.time()
2. Actualizar en actualizar_sensor()
3. Implementar callback en sensores reales
```

### FASE 3: ENV VAR CONSUMPTION
```
1. Leer os.getenv("METEOSER_SRTM_FORCE")
2. Ejecutar lógica si '1'
3. Forzar altitud SRTM en inicialización
```

### FASE 4: VALIDACIÓN DE 617
```
1. Contar solo valores != 0 y != None
2. Distinguir entre "publicadas" vs "válidas"
3. Report en /health diferenciado
```

---

## 📊 ESTADO FINAL

**Ignición Blindada V14.1:**
- ✅ Estructura conceptual: CORRECTA
- ✅ Guardián 617 endpoints: IMPLEMENTADO
- ✅ SHA256 check: FUNCIONA
- ❌ **SRTM flujo real: ROTURA CRÍTICA**
- ❌ **Watchdog actualización: NO FUNCIONA**
- ❌ **Variables de env: NO CONSUMIDAS**

**Veredicto:** Sistema inicia pero `/health` reportará:
```json
{
  "status": "CRITICAL",
  "SRTM_ALTITUD": 0.0,
  "WATCHDOG": "tiempo_sin_actualizar: 99999s",
  "BUS_GUARDIAN": "constantes_faltantes: [muchas]"
}
```

---

## ⚡ SIGUIENTE PASO

**¿PROCEDO A REPARAR LOS 3 CRÍTICOS?**
- Extender LocationEngine + SRTM
- Agregar last_data_update_time y actualizarlo
- Implementar consumidor de METEOSER_SRTM_FORCE
