# 🎯 PLAN DE ACCIÓN - RESTAURACIÓN INMEDIATA V2.6

**Objetivo**: Recuperar la "máquina excelsa" en **2.5 horas**  
**Estrategia**: Agregar código perdido SIN tocar lo funcional  
**Riesgo**: BAJO (solo adiciones, no sobrescrituras)  

---

## 📋 TAREAS PREVIAS COMPLETADAS

✅ **Verificadas como INTACTAS:**
- [x] 6 Motores Elite (EliteMotorsV25.py - 387 líneas)
- [x] Bus de Estado Global (bus_estado_global.py - 373 líneas)
- [x] Formulas Ultra-Precisas (Ciddor 2002, Loschmidt, King, Ekman)
- [x] Sensor Pipeline Ecowitt (reparado - 128 líneas nuevo endpoint)
- [x] SystemManager inicializado cargando datos reales

✅ **Verificados como RECUPERABLES:**
- [x] `tools/arco_solar.py` - EXISTE y funcional
- [x] `tools/amanecer_atardecer.py` - EXISTE y funcional
- [x] Código geocodificación en `backup/ojo_20260202_102049:main_asgi.py`
- [x] Código radiación teórica en backup

---

## 🚀 TAREAS DE RECUPERACIÓN

### **TAREA 1: Restaurar Geocodificación** (35 min)

**Archivo**: `main_asgi.py`  
**Ubicación**: Después de inicializar SystemManager, antes de endpoints

**Agregar este código**:

```python
# ========================================
# GEOCODIFICACIÓN Y UBICACIÓN
# ========================================

def _coords_valid(lat, lon):
    """Valida que lat/lon sean números dentro de rango"""
    try:
        return lat is not None and lon is not None and -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180
    except Exception:
        return False

def _coords_es_spain(lat, lon):
    """Valida que coordenadas estén en territorio español"""
    try:
        lat = float(lat)
        lon = float(lon)
        return 35 <= lat <= 44.5 and -10 <= lon <= 4.5
    except Exception:
        return False

def _parse_coord(val):
    """Parsea coordenadas en formato decimal o cardinal"""
    if val is None:
        return None
    s = str(val).strip().lower().replace(',', '.')
    sign = 1
    if s.endswith(('n', 's', 'e', 'o', 'w')):
        suffix = s[-1]
        s = s[:-1].strip()
        if suffix in ('s', 'o', 'w'):
            sign = -1.0
    try:
        return float(s) * sign
    except Exception:
        return None

# Función helper para obtener ubicación (NUEVA)
def _obtener_ubicacion(system_manager):
    """
    Lógica jerarquizada de obtención de ubicación:
    1. CONFIG_PATH (manual)
    2. Sensores WH65 (si tiene GPS)
    3. LocationEngine (estimación)
    4. Fallback Argentona
    """
    latitud = None
    longitud = None
    origen_ubicacion = "estimada"
    
    # Paso 1: Intenta leer de config
    CONFIG_PATH = Path(__file__).parent / "meteoser_configuracion.txt"
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if "latitud" in line.lower():
                    val = line.split(":")[-1].strip()
                    latitud = _parse_coord(val)
                if "longitud" in line.lower():
                    val = line.split(":")[-1].strip()
                    longitud = _parse_coord(val)
        if latitud is not None and longitud is not None:
            system_manager.set_manual_coordinates(latitud, longitud)
            origen_ubicacion = "manual"
            return latitud, longitud, origen_ubicacion
    except Exception:
        pass
    
    # Paso 2: Intenta leer de sensores
    if system_manager.system:
        lat_sensor = system_manager.system.sensores.get("latitud") or system_manager.system.sensores.get("lat")
        lon_sensor = system_manager.system.sensores.get("longitud") or system_manager.system.sensores.get("lon")
        if lat_sensor is not None and lon_sensor is not None:
            latitud = _parse_coord(lat_sensor)
            longitud = _parse_coord(lon_sensor)
            if latitud is not None and longitud is not None:
                origen_ubicacion = "sensor"
                return latitud, longitud, origen_ubicacion
    
    # Paso 3: LocationEngine (estimación de radiación)
    if latitud is None or longitud is None:
        try:
            coords = system_manager.obtener_coordenadas()
            if coords:
                latitud = coords.get("lat")
                longitud = coords.get("lon")
                origen_ubicacion = coords.get("origen", "estimada")
        except Exception:
            pass
    
    # Paso 4: Validación y fallback
    if not _coords_valid(latitud, longitud) or (origen_ubicacion != "manual" and not _coords_es_spain(latitud, longitud)):
        latitud = 41.5507  # Argentona fallback
        longitud = -2.397
        origen_ubicacion = "desconocida"
    
    return latitud, longitud, origen_ubicacion

# INTEGRACIÓN: Obtener ubicación al iniciar
latitud, longitud, origen_ubicacion = _obtener_ubicacion(system_manager)

# INYECCIÓN: Guardar en system
if system_manager and system_manager.system:
    try:
        system_manager.system.ubicacion = {
            "lat": latitud,
            "lon": longitud,
            "origen": origen_ubicacion,
        }
    except Exception:
        pass
```

**Verificación**:
```bash
curl http://localhost:8080/api/panel/superior | jq '.ubicacion'
# Debería devolver: {"lat": 41.5507, "lon": -2.397, "origen": "desconocida"} o valores reales si están configurados
```

---

### **TAREA 2: Restaurar Arco Solar** (25 min)

**Archivo**: `main_asgi.py`  
**Ubicación**: Después de geocodificación, en función que calcula índices

**Agregar imports**:

```python
from tools.arco_solar import arco_solar as calc_arco_solar
```

**Agregar en la sección de cálculo de índices** (después de obtener ubicación):

```python
# Cálculo del arco solar (brújula táctica)
try:
    hoy = datetime.datetime.now().timetuple().tm_yday
    arco = calc_arco_solar(latitud, hoy)
    indices["arco_solar"] = {
        "valor": round(arco, 2),
        "unidad": "grados",
        "desc": "Recorrido angular del sol hoy"
    }
except Exception:
    indices["arco_solar"] = {"valor": 0, "error": True}
```

**Verificación**:
```bash
curl http://localhost:8080/api/panel/central | jq '.indices.arco_solar'
# Debería devolver: {"valor": ~165.4, "unidad": "grados"} (valor típico España)
```

---

### **TAREA 3: Restaurar Radiación Teórica** (25 min)

**Archivo**: `main_asgi.py`  
**Ubicación**: Después de arco solar

**Agregar función**:

```python
def _radiacion_teorica(lat_deg, day, hora_decimal):
    """Radiación solar teórica máxima (Spencer 1971)"""
    import math
    lat_rad = math.radians(lat_deg)
    
    # Declinación solar
    delta = 0.409 * math.sin(2 * math.pi * (day - 81) / 368)
    
    # Ángulo horario
    omega = math.radians((hora_decimal - 12.0) * 15.0)
    
    # Altitud solar
    sin_alt = (math.sin(lat_rad) * math.sin(delta) + 
               math.cos(lat_rad) * math.cos(delta) * math.cos(omega))
    
    if sin_alt <= 0:
        return 0
    
    # Radiación extraterrestre
    gsc = 1361.0  # W/m² constante solar
    dr = 1 + 0.033 * math.cos(2 * math.pi * day / 365.0)
    
    return gsc * dr * sin_alt
```

**Agregar en cálculo de índices**:

```python
# Radiación solar teórica
try:
    hoy = datetime.datetime.now().timetuple().tm_yday
    hora_decimal = datetime.datetime.now().hour + datetime.datetime.now().minute / 60.0
    rad_teorica = _radiacion_teorica(latitud, hoy, hora_decimal)
    indices["radiacion_teorica"] = {
        "valor": round(rad_teorica, 1),
        "unidad": "W/m²",
        "desc": "Radiación máxima posible (cielo despejado)"
    }
except Exception:
    indices["radiacion_teorica"] = {"valor": 0, "error": True}
```

**Verificación**:
```bash
curl http://localhost:8080/api/panel/central | jq '.indices.radiacion_teorica'
# Debería devolver: {"valor": ~500.0} al mediodía, 0 de noche
```

---

### **TAREA 4: Restaurar Amanecer/Atardecer** (20 min)

**Archivo**: `main_asgi.py`  
**Ubicación**: Después de radiación teórica

**Agregar imports**:

```python
from tools.amanecer_atardecer import calcular_amanecer_atardecer
```

**Agregar en cálculo de índices**:

```python
# Amanecer y atardecer astronómicos
try:
    from zoneinfo import ZoneInfo
    ahora = datetime.datetime.now(ZoneInfo("Europe/Madrid"))
    utc_offset = int(ahora.utcoffset().total_seconds() / 3600)
except Exception:
    try:
        utc_offset = int(datetime.datetime.now().astimezone().utcoffset().total_seconds() / 3600)
    except Exception:
        utc_offset = 1

try:
    horas_sol = calcular_amanecer_atardecer(latitud, longitud, hoy, utc_offset)
    indices["amanecer"] = horas_sol.get("amanecer", "--:--")
    indices["atardecer"] = horas_sol.get("atardecer", "--:--")
except Exception:
    indices["amanecer"] = "--:--"
    indices["atardecer"] = "--:--"
```

**Verificación**:
```bash
curl http://localhost:8080/api/panel/central | jq '.indices | {amanecer, atardecer}'
# Debería devolver: {"amanecer": "07:43", "atardecer": "17:32"} (típico febrero España)
```

---

### **TAREA 5: Agregar Índices Astronómicos** (15 min)

**Archivo**: `main_asgi.py`  
**Ubicación**: Después de amanecer/atardecer

```python
# Índices astronómicos (calidad de cielo)
try:
    calidad_cielo = indices.get("calidad_cielo", 50)  # Default 50%
    ventana_observacion = 6  # horas de ventana nocturna
    
    if calidad_cielo and ventana_observacion:
        cielo_n = max(0, min(1.0, float(calidad_cielo) / 100.0))
        horas_n = max(0, min(1.0, float(ventana_observacion) / 6.0))
        indice_cielo = (0.7 * cielo_n + 0.3 * horas_n) * 100
        
        indices["indice_cielo_astronomico"] = {
            "valor": round(indice_cielo, 1),
            "unidad": "%",
            "desc": "Calidad para observación astronómica"
        }
except Exception:
    pass
```

---

### **TAREA 6: Inyectar Ubicación en Respuestas API** (10 min)

**Archivo**: `main_asgi.py`  
**Función**: Modificar endpoint `/api/panel/superior` o `/api/panel/central`

**Asegurarse que devuelva**:

```python
response = {
    "ubicacion": {
        "lat": latitud,
        "lon": longitud,
        "origen": origen_ubicacion
    },
    "indices": indices,
    # ... resto
}
```

---

### **TAREA 7: Testing Integral** (30 min)

**Test 1: Ubicación**
```bash
curl http://localhost:8080/api/panel/superior | jq '.ubicacion'
# ✅ Debe tener lat, lon, origen
```

**Test 2: Arco Solar**
```bash
curl http://localhost:8080/api/panel/central | jq '.indices.arco_solar.valor'
# ✅ Debe ser > 0 durante el día, 0 de noche
```

**Test 3: Radiación**
```bash
curl http://localhost:8080/api/panel/central | jq '.indices.radiacion_teorica.valor'
# ✅ Debe coincidir aprox con radiación real del sensor
```

**Test 4: Amanecer/Atardecer**
```bash
curl http://localhost:8080/api/panel/central | jq '.indices | {amanecer, atardecer}'
# ✅ Debe ser ~7:30-18:00 (rango España febrero)
```

**Test 5: Verificar Vector #26 recibe ubicación**
```bash
python3 -c "
from core.indices.bus_estado_global import BusEstadoGlobal
from core.system.system_manager import SystemManager
sm = SystemManager()
sm.iniciar()
print('ubicacion:', sm.system.ubicacion)
"
# ✅ Debe mostrar {"lat": ..., "lon": ..., "origen": ...}
```

---

### **TAREA 8: Validación de Impacto en Motores** (30 min)

**Verificar MasasDeAire recibe Θe**:
```bash
curl http://localhost:8080/api/panel/central | jq '.indices | {theta_e, angulo_solar}'
```

**Verificar CapaLimite tiene espesor**:
```bash
curl http://localhost:8080/api/panel/central | jq '.indices.espesor_capa_limite'
```

**Verificar Opacidad (Vector #26) calcula brújula**:
```bash
curl http://localhost:8080/api/panel/central | jq '.indices.brujula_tactica'
```

---

## ⏱️ CRONOGRAMA TOTAL

| Tarea | Duración | Acumulado |
|-------|----------|-----------|
| 1. Geocodificación | 35 min | 35 min |
| 2. Arco Solar | 25 min | 60 min |
| 3. Radiación Teórica | 25 min | 85 min |
| 4. Amanecer/Atardecer | 20 min | 105 min |
| 5. Índices Astronómicos | 15 min | 120 min |
| 6. Inyección en API | 10 min | 130 min |
| 7. Testing | 30 min | 160 min |
| 8. Validación Motores | 30 min | 190 min |
| **TOTAL** | - | **~3.2 horas** |

---

## ✅ CHECKLIST FINAL

- [ ] main_asgi.py tiene función `_obtener_ubicacion()`
- [ ] main_asgi.py tiene función `_radiacion_teorica()`
- [ ] main_asgi.py importa `arco_solar` y `calcular_amanecer_atardecer`
- [ ] `system.ubicacion` está poblado
- [ ] `/api/panel/superior` devuelve ubicación
- [ ] `/api/panel/central` devuelve arco_solar, radiacion_teorica, amanecer, atardecer
- [ ] Vector #26 reconoce ubicación
- [ ] Motor MasasDeAire calcula Θe
- [ ] Dashboard muestra coordenadas correctas
- [ ] 6 motores operan "con visión"

---

## 🎯 RESULTADO ESPERADO

```
Sistema: EXCELSO RESTAURADO
├─ ✅ 6 Motores Elite: OPERATIVOS
├─ ✅ Bus de Estado Global: FUNCIONAL
├─ ✅ Formulas Ultra-Precisas: ACTIVAS
├─ ✅ Sensor Pipeline Ecowitt: EN VIVO
├─ ✅ Geocodificación: RESTAURADA
├─ ✅ Arco Solar: CALCULADO
├─ ✅ Radiación Teórica: VALIDANDO
├─ ✅ Amanecer/Atardecer: SINCRONIZADO
├─ ✅ Vector #26 (Brújula): OPERATIVA
└─ ✅ Dashboard: COMPLETO
```

---

**Próximo paso**: Ejecutar TAREA 1 y reportar resultado del test.

