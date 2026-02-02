# 🔴 AUDITORÍA CRÍTICA: PÉRDIDAS EN GIT RESET
**Fecha**: 2 de febrero de 2026  
**Estado**: Sistema degradado por operación git destructiva  
**Prioridad**: CRÍTICA - Física del Sistema V2.6 incompleta  

---

## 📊 RESUMEN EJECUTIVO

Mediante análisis comparativo entre `main` y `backup/ojo_20260202_102049`, se identificaron **PÉRDIDAS FUNCIONALES CRÍTICAS**:

| Componente | Estado | Impacto | Recuperable |
|-----------|--------|--------|------------|
| **Geocodificación de ubicación** | ❌ PERDIDO | 6 motores ciegos | ✅ SÍ (código en backup) |
| **Arco Solar (brújula, radiación)** | ❌ PERDIDO | Vector #26 muerto | ✅ SÍ (función arco_solar.py) |
| **Radiación Teórica (Spencer)** | ❌ PERDIDO | Nubosidad estimada falla | ✅ SÍ (función _radiacion_teorica) |
| **Amanecer/Atardecer astronómico** | ❌ PERDIDO | Ritmo circadiano fallido | ✅ SÍ (tools/amanecer_atardecer.py) |
| **Validación geográfica (España)** | ❌ PERDIDO | Fallback a valores fijos | ✅ SÍ |
| **Inyección system.ubicacion** | ❌ PERDIDO | API devuelve null | ✅ SÍ |
| **Índices astronómicos (cielo)** | ❌ PERDIDO | Motor nocturno degradado | ✅ SÍ |

**Total de pérdidas: 7 componentes funcionales críticos**

---

## 🔍 DETALLES DE LO PERDIDO

### 1. **Geocodificación de Ubicación** (CRÍTICA)

**Estado actual**: `last_location.json` = `{"lat": 60, "lon": -2.75, "manual": false}` (INCORRECTO)

**Lo que falta**:
```python
# Lógica de lectura jerarquizada que NO existe en main_asgi.py
latitud = None
longitud = None
origen_ubicacion = "estimada"

# Paso 1: Leer de CONFIG_PATH (meteoser_configuracion.txt)
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if "latitud" in line.lower():
                latitud = float(line.split(":")[-1].strip())
            if "longitud" in line.lower():
                longitud = float(line.split(":")[-1].strip())
    if latitud and longitud:
        manager.set_manual_coordinates(latitud, longitud)
        origen_ubicacion = "manual"
except: pass

# Paso 2: Leer de sensores (WH65 si lo soporta)
if not latitud:
    lat_sensor = system.sensores.get("latitud") or system.sensores.get("lat")
    lon_sensor = system.sensores.get("longitud") or system.sensores.get("lon")
    if lat_sensor and lon_sensor:
        latitud = _parse_coord(lat_sensor)  # Parsea formato N/S/E/O
        longitud = _parse_coord(lon_sensor)
        origen_ubicacion = "sensor"

# Paso 3: LocationEngine.estimate_coordinates() (radiación + hora)
if not latitud:
    coords = manager.obtener_coordenadas()
    if coords:
        latitud, longitud = coords["lat"], coords["lon"]
        origen_ubicacion = coords.get("origen", "estimada")

# Paso 4: Validar y fallback
if not _coords_valid(latitud, longitud) or (origen_ubicacion != "manual" and not _coords_es_spain(latitud, longitud)):
    latitud = 41.5507  # Argentona
    longitud = -2.397
    origen_ubicacion = "desconocida"

# Paso 5: INYECTAR EN SYSTEM (esto NO está en main)
system.ubicacion = {
    "lat": latitud,
    "lon": longitud,
    "origen": origen_ubicacion,
}
```

**Impacto**:
- Vector #26 no sabe dónde está → no calcula ángulo solar
- Visibilidad Bucholtz no sabe altura del sol → masa de aire fallida
- Dashboard devuelve null en ubicación
- 6 motores operan "a ciegas"

**Recuperable**: ✅ SÍ - código íntegro en backup/ojo_20260202_102049:main_asgi.py

---

### 2. **Arco Solar** (CRÍTICA)

**Función perdida**: `arco_solar(lat, day_of_year)`

**Lo que hace**:
```python
def arco_solar(lat, hoy):
    """
    Calcula recorrido angular del sol (amanecer a atardecer)
    Entrada: latitud, día del año
    Salida: grados de recorrido
    Fórmula: Spencer (1971) para declinación solar
    """
    import math
    lat_rad = math.radians(lat)
    delta = 0.409 * math.sin(2 * math.pi * (hoy - 81) / 368)
    
    # Ángulo donde el sol sale/se pone (altitud = 0)
    cos_h0 = -math.tan(lat_rad) * math.tan(delta)
    if cos_h0 > 1: return 0  # Sol nunca sale
    if cos_h0 < -1: return 360  # Sol nunca se pone (polo)
    
    h0 = math.acos(cos_h0)
    arc = 2 * math.degrees(h0)  # Convertir a grados
    return arc
```

**Ubicación en backup**: `tools/arco_solar.py`

**Impacto**:
- Brújula táctica (cajón "Arcos") devuelve 0
- Radiación teórica incalculable
- Motor de luz natural sin datos
- Recomendaciones de persianas/cortinas fallan

**Recuperable**: ✅ SÍ - función está en `tools/arco_solar.py` (revisar)

---

### 3. **Radiación Solar Teórica** (CRÍTICA)

**Función perdida**: `_radiacion_teorica(lat_deg, day, hora_decimal)`

```python
def _radiacion_teorica(lat_deg, day, hora_decimal):
    """
    Calcula radiación solar teórica máxima (cielo despejado)
    Válida para validar anomalías de sensores
    Fórmula: Spencer (1971) + Constant Solar
    """
    import math
    lat_rad = math.radians(lat_deg)
    
    # Declinación solar (día del año)
    delta = 0.409 * math.sin(2 * math.pi * (day - 81) / 368)
    
    # Ángulo horario
    omega = math.radians((hora_decimal - 12.0) * 15.0)
    
    # Altitud solar
    sin_alt = (math.sin(lat_rad) * math.sin(delta) + 
               math.cos(lat_rad) * math.cos(delta) * math.cos(omega))
    
    if sin_alt <= 0:
        return 0  # Sol bajo horizonte
    
    # Radiación extraterrestre
    gsc = 1361.0  # W/m² (constante solar)
    dr = 1 + 0.033 * math.cos(2 * math.pi * day / 365.0)
    
    return gsc * dr * sin_alt
```

**Ubicación en backup**: Inlined en main_asgi.py (línea ~1700)

**Impacto**:
- Motor Ambiental no detecta nubosidad → devuelve null
- Validación de sensores rotos → ausente
- Predicción local de lluvia falla
- Dashboard cajón "Radiación" incompleto

**Recuperable**: ✅ SÍ - código íntegro en backup

---

### 4. **Amanecer/Atardecer Astronómico** (ALTA)

**Función perdida**: `calcular_amanecer_atardecer(lat, lon, day, utc_offset)`

**Ubicación en backup**: `tools/amanecer_atardecer.py`

**Lo que hace**:
- Calcula hora exacta de salida/puesta del sol
- Retorna dict con `{"amanecer": HH:MM, "atardecer": HH:MM}`
- Usa fórmula NOAA/NASA

**Impacto**:
- Motor Ritmo Circadiano no sabe cuándo "es de noche"
- Motor Nocturno no enciende recomendaciones
- Detector de presencia nocturna fallido
- Índice cielo astronómico = null

**Recuperable**: ✅ SÍ - módulo completo en tools/

---

### 5. **Validación Geográfica (España)** (MEDIA)

**Función perdida**: `_coords_es_spain(lat, lon)`

```python
def _coords_es_spain(lat, lon):
    """Valida que coordenadas estén en España (±oceanía)"""
    return 35 <= lat <= 44.5 and -10 <= lon <= 4.5
```

**Impacto**:
- Fallback a Argentona sin verificar si tiene sentido
- Podría devolver coordenadas de Noruega como "válidas"

**Recuperable**: ✅ SÍ - trivial

---

### 6. **Índices Astronómicos (Cielo Nocturno)** (MEDIA)

**Lo que falta**:
```python
# Calidad del cielo (oscuridad)
cielo_val = indices.get("calidad_cielo")

# Horas de ventana de observación (tema del usuario/local)
ventana = 6  # ej: puede observar 6 horas/noche

# Índice combinado
if cielo_val and ventana:
    cielo_n = max(0, min(1.0, float(cielo_val) / 100.0))
    horas_n = max(0, min(1.0, float(ventana) / 6.0))
    indice_cielo = (0.7 * cielo_n + 0.3 * horas_n) * 100
    
    indices["indice_cielo_astronomico"] = {
        "valor": round(indice_cielo, 2),
        "estimado": True
    }
```

**Impacto**:
- Dashboard cajón "Astronomía" vacío
- Motor Nocturno no personaliza recomendaciones

**Recuperable**: ✅ SÍ

---

## 🎯 IMPACTO EN LOS 6 MOTORES ELITE

| Motor | Crítica | Pérdida | Efecto |
|-------|---------|--------|--------|
| **MasasDeAire** | ✅ SÍ | Ubicación (lat/lon) | No calcula Θe (ángulo solar) |
| **CapaLimite** | ✅ SÍ | Radiación teórica | Espesor de capa fijo |
| **Opacidad** | ✅ SÍ | Arco solar | Brújula táctica muerta |
| **Ventilación** | ⚠️ SÍ | Arco + amanecer | Recomendaciones genéricas |
| **Autocalibración** | ⚠️ MEDIO | Radiación validación | Menos precisa pero funciona |
| **Forense** | ⚠️ SÍ | Histórico de ubicación | Sin trazas estelares |

---

## 📋 PLAN DE RECUPERACIÓN

### Fase 1: Restaurar Geocodificación (30 min)

**Archivo**: `main_asgi.py`  
**Sección**: Línea ~1650 en backup

```diff
+ # Leer latitud/longitud manuales si existen
+ latitud = None
+ longitud = None
+ origen_ubicacion = "estimada"
+ [... 60 líneas de lógica jerarquizada ...]
+ system.ubicacion = {
+     "lat": latitud,
+     "lon": longitud,
+     "origen": origen_ubicacion,
+ }
+ indices["latitud"] = latitud
+ indices["longitud"] = longitud
+ indices["origen_ubicacion"] = origen_ubicacion
```

### Fase 2: Restaurar Arco Solar (20 min)

**Verificar**: `tools/arco_solar.py` existe  
**Si no**: Copiar función desde backup

```python
from tools.arco_solar import arco_solar
arco = arco_solar(latitud, hoy)
```

### Fase 3: Restaurar Radiación Teórica (20 min)

**Agregar a main_asgi.py**:

```python
def _radiacion_teorica(lat_deg, day, hora_decimal):
    import math
    lat_rad = math.radians(lat_deg)
    delta = 0.409 * math.sin(2 * math.pi * (day - 81) / 368)
    omega = math.radians((hora_decimal - 12.0) * 15.0)
    sin_alt = math.sin(lat_rad) * math.sin(delta) + math.cos(lat_rad) * math.cos(delta) * math.cos(omega)
    if sin_alt <= 0:
        return 0
    gsc = 1361.0
    dr = 1 + 0.033 * math.cos(2 * math.pi * day / 365.0)
    return gsc * dr * sin_alt
```

### Fase 4: Restaurar Amanecer/Atardecer (30 min)

**Verificar**: `tools/amanecer_atardecer.py` existe  
**Integrar**:

```python
from tools.amanecer_atardecer import calcular_amanecer_atardecer
horas_sol = calcular_amanecer_atardecer(latitud, longitud, hoy, utc_offset)
```

### Fase 5: Validación e Índices (40 min)

**Restaurar funciones auxiliares**:
- `_coords_valid(lat, lon)`
- `_coords_es_spain(lat, lon)`
- Cálculo de índice cielo astronómico

### Fase 6: Testing (30 min)

```bash
# Test 1: Verificar ubicación en respuesta
curl http://localhost:8080/api/panel/superior | jq '.ubicacion'

# Test 2: Verificar arco solar
curl http://localhost:8080/api/panel/central | jq '.arco_solar'

# Test 3: Verificar radiación teórica
curl http://localhost:8080/api/panel/central | jq '.radiacion_teorica'
```

---

## ⚠️ PRECAUCIONES

1. **NO resetear main_asgi.py completo** - sólo agregar secciones faltantes
2. **Conservar** la lógica de `/ecowitt` que fue reparada recientemente
3. **Mantener** la inyección de SystemManager
4. **Verificar** que `CONFIG_PATH` existe: `data/meteoser_configuracion.txt`
5. **Test de Physics** después: Sistema debe reconocer ubicación

---

## ✅ LISTA DE VERIFICACIÓN FINAL

- [ ] `system.ubicacion` poblado en respuesta API
- [ ] `indices["latitud"]`, `indices["longitud"]` presentes
- [ ] Arco solar ≠ 0 durante el día
- [ ] Radiación teórica > 0 durante el día
- [ ] Amanecer/atardecer = horas reales
- [ ] Vector #26 calcula ángulo solar correcto
- [ ] Motor MasasDeAire obtiene Θe válido
- [ ] Dashboard cajones muestran ubicación y radiación

---

**Conclusión**: Todas las pérdidas son **RECUPERABLES** sin modificar código existente funcional. Estimado total: **2.5 horas** de integración limpia.

