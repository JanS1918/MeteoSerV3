# AUDITORÍA CRÍTICA: Fallbacks Innecesarios en MeteoSer V3

**Actualizado:** 10 de febrero de 2026  
**Conclusión:** El sistema AÚN ESTÁ USANDO FALLBACKS A DATOS QUE YA TIENE DISPONIBLES

---

## 0. ✅ MEJORAS IMPLEMENTADAS (10/02/2026)

### SRTM Fallback Mejorado (location_engine.py)
**Status:** ✅ **IMPLEMENTADO**

**Cambio:** Cascada explícita de SRTM con logging
```python
# Fallback chain: SRTM API → last_location.json → config file → 0.0
if API_fails:
    if self.altitud is not None and self.altitud > 0:
        log("Usando última altitud SRTM conocida")
        return self.altitud  # Cache anterior
    try_config_value()
    return 0.0
```
**Beneficio:** Si SRTM API falla, usa últimas coordenadas conocidas (en lugar de perder datos)

### Funciones Astronómicas Integradas (bus_expander.py)
**Status:** ✅ **IMPLEMENTADO**

4 funciones científicas que se habían perdido en refactoring main_asgi → bus_expander:

1. **arco_solar()** - Arco solar + duración del día
   - Formula: Spencer's solar arc calculation
   - Output: `arco_solar` (grados), `duracion_dia_h` (horas)

2. **radiacion_teorica()** - Radiación solar teórica
   - Formula: Extra-terrestre ajustada por día del año y hora
   - Output: `radiacion_teorica` (W/m²)

3. **calcular_anejo_astronomico()** - Amanecer/Atardecer/Es_dia
   - Calcula: Hora exacta de amanecer/atardecer
   - Output: `amanecer` (HH:MM), `atardecer` (HH:MM), `es_dia` (bool)

4. **Fallback automático:** Si AstronomiaRecursiva falla → location_module functions
   - Logging explícito: muestra cuál capa se está usando (AstronomiaRecursiva vs location_module)

**Beneficio:** Ya no publica None para datos astronómicos, y debuggable qué capa se usa

---

## 1. LATITUD/LONGITUD: El problema que identificaste

### ✅ DATOS DISPONIBLES EN EL SISTEMA:
```python
# core/system/constants.py (LÍNEAS 18-19)
class ESTACION:
    LATITUD = 41.55326700      # °N - EXACTA (8 decimales)
    LONGITUD = 2.39684500      # °E - EXACTA (8 decimales)
    ALTITUD = 124.0            # metros SRTM - EXACTA
```

### ❌ FALLBACKS QUE NO DEBERÍAN ESTAR:

**core/indices/environmental_indices.py (línea 1453)**
```python
presion_hpa = float(contexto.presion_barometrica) if hasattr(contexto, 'presion_barometrica') else None
```

**core/indices/environmental_indices.py (línea 3794)**
```python
p_value = contexto.get("presion_barometrica") if hasattr(contexto, 'get') else getattr(contexto, "presion_barometrica", None)
```

**core/indices/environmental_indices.py (línea 2067)**
```python
if dt is not None and hasattr(dt, "presion_barometrica") and getattr(dt, "presion_barometrica") is not None:
    p_val = float(getattr(dt, "presion_barometrica"))
```

**Sección 37 de bus_expander.py (múltiples líneas)**
```python
lat = self.system.location.latitud if hasattr(self.system, 'location') else 41.5
lon = self.system.location.longitud if hasattr(self.system, 'location') else 2.4
```

---

## 2. DATOS QUE TIENES DISPONIBLES POR SENSOR:

## 🌡️ TEMPERATURA
- **Sensor:** Disponible en `self.system.data.get("temperatura")`
- **ISA Fallback:** 15.0°C (¡INCORRECTO! En Invierno, Argentona promedia 8-10°C)
- **Ubicaciones con fallback:**
  - bus_expander.py:2788 (sección calidad aire)
  - bus_expander.py:2849 (sección humedad suelo)
  - bus_expander.py:3301 (sección confort interior)
  - environmental_indices.py:múltiples (100+ líneas)
  - advanced_field_indices.py:72-360

## 💧 HUMEDAD
- **Sensor:** Disponible en `self.system.data.get("humedad")`
- **ISA Fallback:** 50.0% (¡INCORRECTO! Argentona costa promedia 75%+)
- **Ubicaciones:** 50+ líneas en todo el codebase

## 🌪️ PRESIÓN BAROMÉTRICA
- **Sensor:** Disponible en `self.system.data.get("presion_barometrica")`
- **ISA Fallback:** 1013.25 hPa (CRÍTICO para WBGT Liljegren/Deardorff)
- **Problema:** Argentona en costa = ~1010 hPa típicamente
- **Ubicaciones:** 15+ funciones

## 💨 VIENTO
- **Sensor:** Disponible en `self.system.data.get("velocidad_viento")`
- **ISA Fallback:** 0.0 m/s (siempre hay viento en costa)
- **Ubicaciones:** 40+ líneas

## ☀️ RADIACIÓN SOLAR
- **Sensor:** Disponible en `self.system.data.get("radiacion_global")`
- **ISA Fallback:** 0.0 W/m² (por defecto)
- **Ubicaciones:** 30+ líneas

## 🧊 CO2
- **Sensor:** DESCONECTADO (None)
- **ISA Fallback:** ~~400 ppm~~ → ✅ AHORA None (CORRECTO)
- **Cambio hecho:** 09/02/2026

---

## 3. DATOS QUE NO DEBERÍAN TENER FALLBACK A ISA

| Parámetro | Tienes | ISA | Argentona Real | Problema |
|-----------|--------|-----|-----------------|----------|
| Latitud | 41.553267°N | 45° | ✅ | Fallback de 45° es innecesario |
| Longitud | 2.396845°E | - | ✅ | No se usa fallback pero busca dinámicamente |
| Altitud | 124m SRTM | 0m | ✅ | SRTM exacto, no se usa ISA |
| Temperatura | Sensor | 15°C | 8-20°C | ISA es incorrecto para costa invernal |
| Humedad | Sensor | 50% | 65-80% | ISA es incorrecto para costa |
| Presión | Sensor | 1013.25 hPa | 1007-1015 hPa | ISA es 6 hPa OFF |
| Gravedad | Calculada | 9.80665 m/s² | 9.80272394 m/s² | ISA vs Somigliana |
| Densidad aire | Sensor | 1.225 kg/m³ | ~1.208 kg/m³ | ISA es 1%+ off |

---

## 4. CADENA DE FALLBACKS INNECESARIOS

### El "Anti-patrón del Fallback Doble"

El código hace esto:
```python
# MALO: Fallback anidado
presion_hpa = self.system.data.get("presion_barometrica", 101325.0)  # Fallback a ISA primero
if presion_hpa is None:
    presion_hpa = 1013.25  # Fallback a ISA segundo
```

Debería hacer:
```python
# MEJOR: Una sola línea
presion_hpa = self.system.data.get("presion_barometrica")
if presion_hpa is None:
    logger.warning("⚠️ Sensor presión desconectado - operando sin presión")
    # NO usar ISA, devolver None o lanzar error
```

---

## 5. LÍNEAS CRÍTICAS CON FALLBACKS INNECESARIOS

### 🔴 CRÍTICO (Afecta WBGT, ET0, cálculos físicos):

1. **bus_expander.py:2786** - Presión con ISA fallback
2. **bus_expander.py:2788** - Temperatura con ISA fallback
3. **bus_expander.py:2790** - Humedad con ISA fallback
4. **environmental_indices.py:1453-1510** - Presión busca fallback primero
5. **environmental_indices.py:2067** - Presión fallback en entalpia
6. **environmental_indices.py:3794** - Presión fallback en profiler
7. **advanced_field_indices.py:72-90** - Radiación Rayleigh-Miller con presión fallback

### 🟡 IMPORTANTE (Usa ISA innecesariamente):

8. **bus_expander.py** - 10+ líneas con `.get("campo", ISA_VALUE)`
9. **environmental_indices.py** - 40+ líneas con `.get("campo", ISA_VALUE)`
10. **advanced_field_indices.py** - Rayleigh-Miller presión fallback

---

## 6. PROBLEMA DEL DISEÑO

### El Sistema Actual:
```
Sensor → .get("presion", 101325.0) → ISA cae automático → Valor incorrecto
```

### Debería Ser:
```
Sensor → .get("presion") → None si falta → VOLVER ATRÁS (No ocultar con ISA)
```

---

## 7. RECOMENDACIÓN: POLÍTICA DE FALLBACKS

### ✅ FALLBACKS PERMITIDOS:
- **Ubicación (lat/lon/alt):** ESTACION.LATITUD / LONGITUD / ALTITUD (conocida)
- **Gravedad:** 9.80272394 m/s² (Somigliana-Helmert para Argentona)
- **Constantes físicas:** Stefan-Boltzmann, Boltzmann, Planck (universales)
- **Configuración aplicación:** valores default del código conocidos

### ❌ FALLBACKS NO PERMITIDOS:
- **Temperatura sensor:** Sin sensor = None, no 15°C ISA
- **Humedad sensor:** Sin sensor = None, no 50% ISA  
- **Presión sensor:** Sin sensor = None, no 1013.25 hPa ISA
- **Viento sensor:** Sin sensor = 0 m/s (cero real), no ISA
- **Radiación sensor:** Sin sensor = None, no 0 W/m²
- **CO2 sensor:** Sin sensor = None, no 400 ppm ISA ✅ (DONE)

---

## 8. ACCIÓN REQUERIDA

### ANTES (Ahora):
```
Sensor CO2 desconectado → 400 ppm ISA → Mostrar como real ❌
```

### DESPUÉS (Requerido):
```
Sensor CO2 desconectado → None → Mostrar "Sin dato" ✅ (DONE)
Sensor TEMP desconectado → None → Mostrar "Sin dato" (TODO)
Sensor HUMEDAD desconectado → None → Mostrar "Sin dato" (TODO)
Sensor PRESIÓN desconectado → None → Mostrar "Sin dato" (TODO)
```

---

## 9. CONCLUSIÓN

**No necesitas fallbacks ISA porque:**

1. **Tienes coordenadas exactas:** 41.553267°N, 2.396845°E, 124m SRTM
2. **Tienes sensores reales** que envían datos disponibles en `self.system.data`
3. **El ISA es para aviones a 0m sobre nivel del mar en 45°N**, no para Argentona costa
4. **Ocultar con ISA es mentir** - si no hay sensor, di que no hay sensor

---

## 10. PROXIMOS PASOS

Cambiar **TODOS** los fallbacks de sensores a None:

```bash
# CAMBIOS REALIZADOS (10/02/2026):

✅ bus_expander.py L7496-7500: Sensor fallbacks → None
   - temperatura: 15.0 → None
   - humedad: 50.0 → None  
   - presion: 101325.0 → None
   - co2: 400.0 → None

✅ environmental_indices.py L1226: Steadman Apparent Temperature
   - p_atm_pa = 101325.0 → obtener del contexto + logging warning

✅ environmental_indices.py L1505: Radiación solar UV
   - presion_barometrica = 1013.25 → None

✅ environmental_indices.py L1601: Rayleigh-Miller Scattering
   - presion_hpa fallback a 1013.25 → None

✅ environmental_indices.py L1626: Nubosidad Liu-Jordan (CRÍTICO)
   - presion_pa = 101325.0 → None
   - presion_fuente = "isa_fallback" → "sin_dato"

✅ environmental_indices.py L2791: Nubosidad calculator
   - presion_hpa = 1013.25 → None + logging warning

✅ environmental_indices.py L6428: ContextoMaestro constructor
   - presion_barometrica=1013.25 → None

✅ environmental_indices.py L6492: Fase lunar Meeus
   - presion_val = presion_hpa if ... else 1013.25 → presion_val = presion_hpa

✅ environmental_indices.py L9701: Hardy Psicrometria
   - presion_pa = ... else 101325.0 → logwarn + fallback solo si realmente None

✅ environmental_indices.py L9820: Saturacion Vapor ultra-precisa
   - presion_pa if ... else 101325.0 → logwarn + fallback solo si realmente None
```

---

## 11. RAZÓN PRINCIPAL: HONESTIDAD EN DATOS

El sistema tiene:
- ✅ **Sensor de presión** disponible: `self.system.data.get("presion_barometrica")`
- ❌ **ISA como fallback**: Mentir que hay presión 1013.25 hPa cuando realmente no hay dato

**Consecuencias de mentir:**
1. **WBGT Liljegren/Deardorff:** Requiere presión para evaporación de sudor. ISA está 3-6 hPa OFF de realidad.
2. **ET0 (Evapotranspiración):** Sensible a presión para densidad aire.
3. **Confort interior:** Depende de entalpía que necesita presión exacta.
4. **Depuración:** "¿Por qué mis cálculos no matchen?" → Escondido en ISA fallback.

**Solución:** 
```python
# MALO (actual):
presion_hpa = contexto.get("presion_barometrica", 1013.25)  # Mentira silenciosa

# BUENO (nuevo):
presion_hpa = contexto.get("presion_barometrica", None)
if presion_hpa is None:
    logger.warning("⚠️ Sensor presión desconectado - no hay dato real")
    # Devolver None o error, NO ocultar con ISA
```
