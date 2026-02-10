# 🔗 MAPEO DE DEPENDENCIAS - Dónde Se Usaban las Funciones Perdidas

## RESUMEN RÁPIDO

| Función Perdida | Motor Afectado | Criticidad | Estado |
|---|---|---|---|
| `arco_solar()` | Luz Natural, Ritmo Circadiano, Confort | 🔴 CRÍTICA | ❌ Inoperante |
| `amanecer/atardecer_hibrido` | Luz Natural, Ritmo Circadiano | 🔴 CRÍTICA | ❌ Inoperante |
| `radiacion_teorica()` | Radiación UV, Ambiental, Confort | 🟠 MEDIA | ⚠️ Degradado |
| `nubosidad_estimada` | Ambiental, Radiación | 🟠 MEDIA | ⚠️ Degradado |
| `ubicacion (lat/lon)` | TODOS los 6 motores | 🔴 CRÍTICA | ❌ Inoperante |
| `es_dia_astronomico` | Luz Natural, Nocturno | 🔴 CRÍTICA | ❌ Inoperante |
| `ventana_observacion_nocturna` | Motor Nocturno | 🟠 MEDIA | ❌ No se calcula |

---

## 🔴 MOTOR LUZ NATURAL (`core/motors/luz_natural_motor.py`)

### DEPENDENCIAS DEL BACKUP
```python
def analizar(self, contexto):
    indices = contexto["indices"]
    
    # L1: amanecer / atardecer híbrido
    amanecer = indices.get("amanecer")           # "06:15" ← PERDIDO
    atardecer = indices.get("atardecer")         # "19:45" ← PERDIDO
    
    # L2: Datos astronómicos
    es_dia_astronomico = indices.get("es_dia_astronomico")    # True/False ← PERDIDO
    es_dia_sensor = indices.get("es_dia_sensor")              # True/False ← PERDIDO
    
    # L3: Radiación teórica para validar
    radiacion_teorica = indices.get("radiacion_teorica")     # W/m² ← PERDIDO
    radiacion_real = sensores.get("radiacion")               # W/m² (funciona)
    
    # AHORA: Sin estos datos, el motor NO PUEDE:
    # - Determinar si es día/noche
    # - Validar si sensor de radiación está roto
    # - Estimar luz natural disponible
    # - Sugerir persianas/cortinas
    
    return {}  # ← RETORNA VACÍO
```

### ESTADO ACTUAL
```
❌ COMPLETAMENTE INOPERANTE
   - No tiene acceso a "amanecer", "atardecer"
   - No puede calcular luminancia
   - No puede recomendar apertura de persianas
```

### SÍNTOMAS DE FALLO
- No recomienda abrir cortinas al amanecer
- No detecta anomalías en sensor de radiación
- No ajusta iluminación artificial a hora solar

---

## 🔴 MOTOR RITMO CIRCADIANO (`core/motors/ritmo_circadiano_motor.py`)

### DEPENDENCIAS DEL BACKUP
```python
def analizar(self, contexto):
    indices = contexto["indices"]
    
    # L1: Horas de luz (función del arco solar)
    duracion_dia = indices.get("duracion_dia_h")  # 11.5 horas ← PERDIDO
    duracion_noche = indices.get("duracion_noche_h")  # 12.5 horas ← PERDIDO
    
    # L2: Horarios híbridos
    amanecer = indices.get("amanecer")     # "06:15" ← PERDIDO
    atardecer = indices.get("atardecer")   # "19:45" ← PERDIDO
    
    # L3: Ubicación (varía arco solar por latitud)
    latitud = indices.get("latitud")       # 41.5507 ← PERDIDO
    origen = indices.get("origen_ubicacion")  # "manual"/"sensor"/"estimada" ← PERDIDO
    
    # AHORA: Sin estos datos, el motor:
    # - NO PUEDE calcular fase circadiana
    # - NO PUEDE recomendar siestas
    # - NO PUEDE ajustar alertness por hora del día
    # - NO PUEDE detectar desincronización
    
    return {}  # ← RETORNA VACÍO
```

### ESTADO ACTUAL
```
❌ COMPLETAMENTE INOPERANTE
   - No sabe horario de amanecer
   - No puede calcular "horas desde amanecer"
   - No puede recomendar hora de sueño
```

### SÍNTOMAS DE FALLO
- Recomienda siesta a medianoche
- No detecta jet lag
- No ajusta alertness a ciclo solar real

---

## 🔴 MOTOR NOCTURNO (`core/motors/nocturno_motor.py`)

### DEPENDENCIAS DEL BACKUP
```python
def analizar(self, contexto):
    indices = contexto["indices"]
    
    # L1: Duración de noche
    duracion_noche = indices.get("duracion_noche_h")  # 12.5 ← PERDIDO
    
    # L2: Índices de cielo astronómico
    ventana_obs = indices.get("ventana_observacion_nocturna")  # 4.2 horas ← PERDIDO
    indice_cielo = indices.get("indice_cielo_astronomico")     # 75.3 ← PERDIDO
    indice_cielo_nivel = indices.get("indice_cielo_astronomico_nivel")  # "bueno" ← PERDIDO
    
    # L3: Ubicación
    latitud = indices.get("latitud")  # 41.5507 ← PERDIDO
    
    # AHORA: Sin estos datos, el motor:
    # - NO PUEDE calcular "buena noche para observar"
    # - NO PUEDE recomendar hora de observación
    # - NO PUEDE estimar contaminación lumínica
    
    return {}  # ← RETORNA VACÍO
```

### ESTADO ACTUAL
```
❌ COMPLETAMENTE INOPERANTE
   - No calcula ventana de observación
   - No estima calidad del cielo
   - No recomienda hora para astronomía
```

### SÍNTOMAS DE FALLO
- No sugiere "buena noche para telescopio"
- No detecta mejoras en contaminación lumínica
- No recomienda horario de observación

---

## 🟠 MOTOR AMBIENTAL (`core/motors/ambiental_motor.py`)

### DEPENDENCIAS DEL BACKUP
```python
def analizar(self, contexto):
    indices = contexto["indices"]
    
    # L1: Radiación teórica (con ubicación)
    radiacion_teorica = indices.get("radiacion_teorica")  # W/m² ← PERDIDO
    radiacion_real = sensores.get("radiacion")            # W/m² (funciona)
    
    # L2: Nubosidad estimada (derivada de radiación)
    nubosidad_est = indices.get("nubosidad_estimada")  # 0-100% ← PERDIDO
    
    # L3: Ubicación
    latitud = indices.get("latitud")  # Para ajustar umbrales de comodidad
    
    # AHORA: Puede funcionar PARCIALMENTE
    # - Usa nubosidad DE SENSORES si existe
    # - Pero NO PUEDE estimar si falta sensor
    
    # RECOMENDACIÓN: "Nublado" 
    # PERO: ¿Es realmente nublado o falla el sensor? NO LO SABE
```

### ESTADO ACTUAL
```
⚠️ DEGRADADO
   - Funciona con sensores directos
   - NO PUEDE estimar nubosidad sin radiación
   - NO PUEDE validar anomalías
```

### SÍNTOMAS DE FALLO
- Si falta sensor radiación: nubosidad = null
- No detecta "sensor roto" (radiación = 0 con sol)
- No ajusta recomendaciones por latitud

---

## 🟠 MOTOR CONFORT (`core/motors/confort_motor.py`)

### DEPENDENCIAS DEL BACKUP
```python
def analizar(self, contexto):
    indices = contexto["indices"]
    
    # L1: Arco solar (adapta umbrales por latitud)
    arco_solar = indices.get("arco_solar")      # 172.5° ← PERDIDO
    duracion_dia = indices.get("duracion_dia_h")  # 11.5 ← PERDIDO
    
    # L2: Ubicación (latitud cambia física del confort)
    latitud = indices.get("latitud")  # 41.5507 ← PERDIDO
    
    # L3: Horario solar
    amanecer = indices.get("amanecer")  # "06:15" ← PERDIDO
    atardecer = indices.get("atardecer")  # "19:45" ← PERDIDO
    
    # AHORA: Usa umbrales GENÉRICOS sin contexto local
    # Problema: España Mediterránea != Galicia
    #           Verano != Invierno (en duración del día)
    
    # SIN ARCO SOLAR: No adapta recomendación de:
    # - Temperatura ideal
    # - Humedad ideal
    # - Necesidad de apertura de ventanas
```

### ESTADO ACTUAL
```
⚠️ DEGRADADO
   - Funciona pero con recomendaciones genéricas
   - NO PUEDE personalizar por latitud
   - NO PUEDE adaptar por estación
```

### SÍNTOMAS DE FALLO
- En invierno (6h luz): Recomienda abrir ventana como en verano (16h luz)
- No ajusta temperatura ideal por duración del día
- Recomienda lo mismo para Madrid (40.4°N) y Sevilla (37.4°N)

---

## 🟠 MOTOR RADIACIÓN/UV

### DEPENDENCIAS DEL BACKUP
```python
def analizar(self, contexto):
    indices = contexto["indices"]
    
    # L1: Radiación teórica (para validar sensor)
    radiacion_teorica = indices.get("radiacion_teorica")  # W/m² ← PERDIDO
    radiacion_real = sensores.get("radiacion")            # W/m² (funciona)
    
    # L2: Ubicación
    latitud = indices.get("latitud")  # Afecta ángulo de incidencia UV
    
    # AHORA: NO PUEDE:
    # - Detectar "radiación imposible" (real > teórica × 1.1)
    # - Validar sensor UV roto
    # - Estimar si nubes oscurecen pero no detectable por sensor
    
    if radiacion_real > radiacion_teorica:
        alert("⚠️ RADIACIÓN ANÓMALA: Posible error de sensor")  ← NO SE HACE
```

### ESTADO ACTUAL
```
⚠️ DEGRADADO
   - Funciona con sensores directos
   - NO PUEDE validar anomalías radiación
   - NO PUEDE detectar falla de sensor UV
```

### SÍNTOMAS DE FALLO
- Sensor UV roto: reporta UV=0 a mediodía → NO SE DETECTA
- Radiación real > teórica × 2 → NO SE ALERTA
- No ajusta recomendaciones SPF por latitud

---

## MATRIZ DE IMPACTO

```
┌──────────────────────┬───────────────┬────────────────┬─────────────────┐
│ Motor                │ Criticidad    │ Estado Actual  │ Síntoma         │
├──────────────────────┼───────────────┼────────────────┼─────────────────┤
│ Luz Natural          │ 🔴 CRÍTICA    │ ❌ Muerto      │ Sin recomend.   │
│ Ritmo Circadiano     │ 🔴 CRÍTICA    │ ❌ Muerto      │ Sin recomend.   │
│ Motor Nocturno       │ 🟠 ALTA       │ ❌ Muerto      │ Sin astronomía  │
│ Ambiental            │ 🟠 MEDIA      │ ⚠️ Degradado   │ Nubosidad null  │
│ Confort              │ 🟠 MEDIA      │ ⚠️ Degradado   │ Genérico        │
│ Radiación/UV         │ 🟠 MEDIA      │ ⚠️ Degradado   │ Sin validación  │
└──────────────────────┴───────────────┴────────────────┴─────────────────┘
```

---

## LÍNEAS EN BACKUP QUE HABRÍA QUE ANALIZAR

```
L282:    from tools.arco_solar import arco_solar
L1559:   from tools.amanecer_atardecer import calcular_amanecer_atardecer
L1471:   # Leer latitud/longitud manuales si existen
L1487:   def _coords_valid(lat, lon):
L1495:   def _parse_coord(val):
L1508:   def _coords_es_spain(lat, lon):
L1545:   hoy = datetime.datetime.now().timetuple().tm_yday
L1547:   arco = arco_solar(latitud, hoy)
L1548:   def _radiacion_teorica(lat_deg, day, hora_decimal):
L1583:   indices["arco_solar"] = {"valor": round(arco, 2), "estimado": estimado_arco}
L1584:   indices["duracion_dia_h"] = {"valor": round(arco / 15.0, 2), "estimado": estimado_arco}
L1587:   indices["radiacion_teorica"] = {"valor": round(rad_teorica, 1), "estimado": True}
L1614:   horas_sol = calcular_amanecer_atardecer(latitud, longitud, hoy, utc_offset)
L1728:   indices["latitud"] = latitud
L1729:   indices["longitud"] = longitud
L1730:   indices["origen_ubicacion"] = origen_ubicacion
```

---

## RECOMENDACIÓN DE RESTAURACIÓN

### PASO 1: Verificar si funciones ya existen
```bash
grep -r "_radiacion_teorica" core/
grep -r "radiacion_teorica" core/
grep -r "_coords_valid" core/
grep -r "arco_solar" core/
```

### PASO 2: Si NO existen, crear archivo de "módulo de ubicación"
```python
# core/location/location_module.py

def coords_valid(lat, lon):
    """Validar coordenadas"""
    ...

def parse_coord(val):
    """Parsear múltiples formatos"""
    ...

def detect_location(system, config_path):
    """Detectar ubicación jerárquicamente"""
    ...

def calcular_radiacion_teorica(lat, lon, dia, hora):
    """Calcular radiación teórica"""
    ...

def calcular_duracion_noche(lat, dia):
    """Calcular horas de noche"""
    ...
```

### PASO 3: Integrar en `app/ui/router.py`
```python
# En _estado_impl() o nuevo endpoint GET /api/ubicacion_contexto

from core.location.location_module import *

ubicacion = detect_location(system, CONFIG_PATH)
indices["latitud"] = ubicacion["lat"]
indices["longitud"] = ubicacion["lon"]
indices["origen_ubicacion"] = ubicacion["origen"]

# ... resto de cálculos
```

### PASO 4: Validar en respuesta
```bash
curl http://localhost:8080/api/panel/superior | jq '.indices.latitud'
# Debe devolver: 41.5507 (o lo que haya configurado)
```

---

*Generado: 2 Feb 2026*
*Referencia: backup/ojo_20260202_102049 → main_asgi.py (líneas 1471-1730)*
