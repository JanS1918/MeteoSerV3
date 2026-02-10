# 🔧 GUÍA DE RECODIFICACIÓN - Funciones Perdidas

## Ubicación en Backup
- Archivo: `main_asgi.py`
- Rama: `backup/ojo_20260202_102049`
- Líneas: 1471-1730
- Función principal: `_estado_impl()`

---

## FUNCIÓN 1: `_coords_valid(lat, lon)` 
**Propósito:** Validar que coordenadas sean válidas

### Pseudocódigo
```
FUNCIÓN validar_coords(lat, lon):
  SI lat es None O lon es None:
    RETORNA False
  
  INTENTA:
    lat_num ← float(lat)
    lon_num ← float(lon)
    
    SI -90 <= lat_num <= 90:
      SI -180 <= lon_num <= 180:
        RETORNA True
    
    RETORNA False
  
  EXCEPTO Error de conversión:
    RETORNA False
```

### Casos de uso
```python
# Válida (España):
_coords_valid(41.5507, -2.397)  # → True

# Inválida (fuera de rango):
_coords_valid(91, 0)             # → False (lat > 90)
_coords_valid(0, 200)            # → False (lon > 180)

# Inválida (no convertible):
_coords_valid("abc", 0)          # → False
_coords_valid(None, 41)          # → False
```

---

## FUNCIÓN 2: `_parse_coord(val)`
**Propósito:** Convertir múltiples formatos de coordenadas

### Pseudocódigo
```
FUNCIÓN parsear_coord(val):
  SI val es None:
    RETORNA None
  
  texto ← CONVERTIR_A_STRING(val).strip().lower()
  texto ← REEMPLAZAR_COMAS_POR_PUNTOS(texto)
  
  signo ← 1
  SI texto termina con ('n', 's', 'e', 'o', 'w'):
    sufijo ← último_carácter(texto)
    texto ← texto[:-1].strip()
    
    SI sufijo en ('s', 'o', 'w'):  // Sur, Oeste, West
      signo ← -1.0
  
  INTENTA:
    número ← float(texto)
    RETORNA número * signo
  
  EXCEPTO Error de conversión:
    RETORNA None
```

### Casos de uso
```python
# Formatos normales:
_parse_coord(41.5507)           # → 41.5507
_parse_coord("-2.397")          # → -2.397
_parse_coord("41,5507")         # → 41.5507 (coma → punto)

# Formatos con sufijo:
_parse_coord("41.5507N")        # → 41.5507 (Norte positivo)
_parse_coord("2.397W")          # → -2.397 (Oeste negativo)
_parse_coord("41.5507S")        # → -41.5507 (Sur negativo)
_parse_coord("2.397E")          # → 2.397 (Este positivo)

# Inválidos:
_parse_coord(None)              # → None
_parse_coord("abc")             # → None
_parse_coord("")                # → None
```

---

## FUNCIÓN 3: `_coords_es_spain(lat, lon)`
**Propósito:** Verificar que coordenadas sean de España

### Pseudocódigo
```
FUNCIÓN es_españa(lat, lon):
  INTENTA:
    lat_num ← float(lat)
    lon_num ← float(lon)
    
    // Bounding box de España peninsular + islas
    SI 35 <= lat_num <= 44.5:
      SI -10 <= lon_num <= 4.5:
        RETORNA True
    
    RETORNA False
  
  EXCEPTO Error:
    RETORNA False
```

### Rango válido
```
Latitud:  35°N a 44.5°N  (norte Canarias a norte Galicia)
Longitud: -10°W a 4.5°E  (oeste Canarias a este Barcelona)
```

### Casos de uso
```python
_coords_es_spain(41.5507, -2.397)   # → True  (Argentona)
_coords_es_spain(36.7372, -3.5881)  # → True  (Granada)
_coords_es_spain(40.4168, -3.7038)  # → True  (Madrid)
_coords_es_spain(43.2627, -2.9253)  # → True  (Bilbao)

_coords_es_spain(51, 0)             # → False (Reino Unido)
_coords_es_spain(34, -2)            # → False (Marruecos/sur límite)
_coords_es_spain(50, 10)            # → False (Francia/este límite)
```

---

## FUNCIÓN 4: Detección Jerárquica de Ubicación
**Propósito:** Buscar coordenadas en orden de confianza

### Pseudocódigo
```
FUNCIÓN detectar_ubicacion():
  latitud ← None
  longitud ← None
  origen ← "estimada"
  
  // NIVEL 1: Archivo de configuración manual
  INTENTA:
    ABRIR_ARCHIVO("data/meteoser_configuracion.txt"):
      POR_CADA línea:
        SI "latitud" en línea.lower():
          latitud ← float(línea.split(":")[-1].strip())
        
        SI "longitud" en línea.lower():
          longitud ← float(línea.split(":")[-1].strip())
    
    SI latitud ≠ None Y longitud ≠ None:
      manager.set_manual_coordinates(latitud, longitud)
      origen ← "manual"
      RETORNA (latitud, longitud, origen)
  
  EXCEPTO Error:
    pass
  
  // NIVEL 2: Sensores del sistema
  INTENTA:
    lat_sensor ← system.sensores.get("latitud") O system.sensores.get("lat")
    lon_sensor ← system.sensores.get("longitud") O system.sensores.get("lon")
    
    SI lat_sensor ≠ None Y lon_sensor ≠ None:
      latitud ← parsear_coord(lat_sensor)
      longitud ← parsear_coord(lon_sensor)
      origen ← "sensor"
      RETORNA (latitud, longitud, origen)
  
  EXCEPTO Error:
    pass
  
  // NIVEL 3: Manager (geocodificación previa)
  INTENTA:
    coords ← manager.obtener_coordenadas()
    SI coords:
      latitud ← coords.get("lat")
      longitud ← coords.get("lon")
      origen ← coords.get("origen", "estimada")
      RETORNA (latitud, longitud, origen)
  
  EXCEPTO Error:
    pass
  
  // NIVEL 4: Fallback (Argentona, Barcelona)
  SI NO validar_coords(latitud, longitud):
    latitud ← 41.5507
    longitud ← -2.397
    origen ← "desconocida"
  
  O SI origen ≠ "manual" Y NO es_españa(latitud, longitud):
    latitud ← 41.5507
    longitud ← -2.397
    origen ← "desconocida"
  
  RETORNA (latitud, longitud, origen)
```

### Resultado
```python
lat, lon, origen = detectar_ubicacion()

# Posibles orígenes:
# "manual"      → Archivo de configuración
# "sensor"      → Sensores del sistema
# "estimada"    → Manager (geocodificación previa)
# "desconocida" → Fallback (Argentona)
```

---

## FUNCIÓN 5: Cálculo de Arco Solar
**Propósito:** Calcular arco solar en grados para una latitud y día

### Pseudocódigo
```
FUNCIÓN arco_solar(latitud, dia_año):
  // Esta función es EXTERNA en tools/arco_solar.py
  // Se importa: from tools.arco_solar import arco_solar
  
  // Retorna el número de grados de arco que recorre el sol
  // desde salida hasta puesta
```

### Uso
```python
import datetime
from tools.arco_solar import arco_solar

hoy_numero = datetime.datetime.now().timetuple().tm_yday  # 1-365
lat = 41.5507

arco = arco_solar(lat, hoy_numero)  # ≈ 172.5 (grados)

duracion_horas = arco / 15.0        # ≈ 11.5 (horas)

# Añadir a índices:
indices["arco_solar"] = {"valor": round(arco, 2), "estimado": origen != "manual"}
indices["duracion_dia_h"] = {"valor": round(duracion_horas, 2), "estimado": origen != "manual"}
```

---

## FUNCIÓN 6: Radiación Solar Teórica
**Propósito:** Calcular radiación solar extraterrestre en W/m²

### Pseudocódigo
```
FUNCIÓN radiacion_teorica(lat_grados, dia_año, hora_decimal):
  IMPORTAR math
  
  lat_radianes ← math.radians(lat_grados)
  
  // Declinación solar (ángulo entre el plano ecuatorial y el sol)
  declinacion ← 0.409 * sin(2π * (dia_año - 81) / 368)
  
  // Ángulo horario (cuántos grados está el sol de la meridiana)
  omega ← math.radians((hora_decimal - 12.0) * 15.0)
  
  // Seno de la altitud solar
  sin_altitud ← sin(lat_radianes) * sin(declinacion) + 
                cos(lat_radianes) * cos(declinacion) * cos(omega)
  
  // Si el sol está bajo el horizonte, radiación = 0
  SI sin_altitud <= 0:
    RETORNA 0
  
  // Constante solar extraterrestre
  GSC ← 1361.0  // W/m²
  
  // Factor de distancia Tierra-Sol (varía ±3.3% durante el año)
  distancia_relativa ← 1 + 0.033 * cos(2π * dia_año / 365.0)
  
  // Radiación = Constante × Distancia × sin(altitud)
  RETORNA GSC * distancia_relativa * sin_altitud
```

### Uso
```python
import datetime
import math

lat = 41.5507  # Argentona
hoy = datetime.datetime.now().timetuple().tm_yday  # 1-365
ahora = datetime.datetime.now()
hora_decimal = ahora.hour + ahora.minute / 60.0 + ahora.second / 3600.0  # 12.5 = 12:30

rad_teorica = radiacion_teorica(lat, hoy, hora_decimal)  # ≈ 600 W/m² (mediodía)

# Añadir a índices:
indices["radiacion_teorica"] = {"valor": round(rad_teorica, 1), "estimado": True}

// Estimar nubosidad si falta sensor
SI "radiacion" en sensores Y radiacion_teorica > 0:
  rad_real = float(sensores.get("radiacion"))
  nubosidad = max(0, min(100, (1.0 - (rad_real / rad_teorica)) * 100))
  indices["nubosidad_estimada"] = {"valor": round(nubosidad, 2), "estimado": True}
```

### Casos ejemplos
```
Día: 2 Feb (día 33 del año)
Latitud: 41.5507 (Argentona)

Hora: 06:00 (amanecer)
  → radiacion ≈ 50 W/m²

Hora: 12:00 (mediodía)
  → radiacion ≈ 700 W/m²

Hora: 18:00 (atardecer)
  → radiacion ≈ 100 W/m²

Hora: 22:00 (noche)
  → radiacion ≈ 0 W/m²
```

---

## FUNCIÓN 7: Cálculo de Amanecer/Atardecer
**Propósito:** Calcular horas de salida y puesta del sol

### Pseudocódigo
```
FUNCIÓN calcular_amanecer_atardecer(lat, lon, dia_año, offset_utc):
  // Esta función es EXTERNA en tools/amanecer_atardecer.py
  // Se importa: from tools.amanecer_atardecer import calcular_amanecer_atardecer
  
  // Entrada:
  //   lat: latitud en grados (-90 a 90)
  //   lon: longitud en grados (-180 a 180)
  //   dia_año: 1-365
  //   offset_utc: diferencia horaria (1 para España en invierno, 2 en verano)
  
  // Retorna diccionario:
  // {
  //   "amanecer": "06:15",
  //   "atardecer": "19:45",
  //   "duracion": 13.5  (horas)
  // }
```

### Uso
```python
import datetime
from tools.amanecer_atardecer import calcular_amanecer_atardecer
from zoneinfo import ZoneInfo

lat = 41.5507
lon = -2.397
hoy = datetime.datetime.now().timetuple().tm_yday

// Obtener offset UTC
ahora = datetime.datetime.now(ZoneInfo("Europe/Madrid"))
utc_offset = int(ahora.utcoffset().total_seconds() / 3600)  # 1 o 2

horas_sol = calcular_amanecer_atardecer(lat, lon, hoy, utc_offset)

amanecer = horas_sol.get("amanecer")  # "06:15"
atardecer = horas_sol.get("atardecer")  # "19:45"
duracion = horas_sol.get("duracion")  # 13.5

indices["amanecer_astronomico"] = amanecer
indices["atardecer_astronomico"] = atardecer
```

---

## FUNCIÓN 8: Lógica Híbrida Día/Noche
**Propósito:** Sincronizar astronomía con sensores

### Pseudocódigo
```
FUNCIÓN deterginar_dia_hibrido(horas_sol, sensores, indices, umbral_ventana=90):
  amanecer_astro ← horas_sol.get("amanecer")      // "06:15"
  atardecer_astro ← horas_sol.get("atardecer")    // "19:45"
  
  ahora ← datetime.datetime.now()
  ahora_minutos ← ahora.hour * 60 + ahora.minute
  
  // Conversiones
  amanecer_min ← hhmm_a_minutos(amanecer_astro)   // 375
  atardecer_min ← hhmm_a_minutos(atardecer_astro) // 1185
  
  // Determinar si es día según sensores
  radiacion ← sensores.get("radiacion", 0)
  uv ← sensores.get("uv", 0)
  
  es_dia_sensor ← (radiacion >= 50) O (uv > 0.1)
  
  // Determinar si es día según astronomía
  SI amanecer_min ≤ atardecer_min:  // Día normal
    es_dia_astronomico ← amanecer_min ≤ ahora_minutos ≤ atardecer_min
  OTRO:                              // Caso especial (zonas polares)
    es_dia_astronomico ← ahora_minutos >= amanecer_min O ahora_minutos ≤ atardecer_min
  
  // Ajuste híbrido
  amanecer_hibrido ← amanecer_astro
  atardecer_hibrido ← atardecer_astro
  
  SI es_dia_astronomico ES False Y es_dia_sensor:  // Sensor dice día, astro dice noche
    SI abs(ahora_minutos - amanecer_min) ≤ umbral_ventana:  // 90 minutos
      amanecer_hibrido ← minutos_a_hhmm(ahora_minutos)      // Usa hora actual
  
  SI es_dia_astronomico ES True Y NO es_dia_sensor:  // Astro dice día, sensor dice noche
    SI abs(ahora_minutos - atardecer_min) ≤ umbral_ventana:
      atardecer_hibrido ← minutos_a_hhmm(ahora_minutos)
  
  // Calcular desviaciones
  amanecer_h_min ← hhmm_a_minutos(amanecer_hibrido)
  atardecer_h_min ← hhmm_a_minutos(atardecer_hibrido)
  
  desvio_amanecer ← abs(amanecer_h_min - amanecer_min)
  desvio_atardecer ← abs(atardecer_h_min - atardecer_min)
  
  // Detectar inconsistencias
  inconsistencia_sensor ← (es_dia_astronomico ≠ None) Y (es_dia_astronomico ≠ es_dia_sensor)
  inconsistencia_hibrida ← (desvio_amanecer >= 30) O (desvio_atardecer >= 30)
  
  RETORNA {
    "amanecer": amanecer_hibrido,
    "atardecer": atardecer_hibrido,
    "amanecer_astronomico": amanecer_astro,
    "atardecer_astronomico": atardecer_astro,
    "es_dia_sensor": es_dia_sensor,
    "es_dia_astronomico": es_dia_astronomico,
    "desvio_amanecer_min": desvio_amanecer,
    "desvio_atardecer_min": desvio_atardecer,
    "inconsistencia_luz": inconsistencia_sensor O inconsistencia_hibrida,
    "inconsistencia_sensor": inconsistencia_sensor,
    "inconsistencia_hibrida": inconsistencia_hibrida,
  }
```

### Caso de uso
```python
resultado = determinar_dia_hibrido(
    horas_sol,      # {"amanecer": "06:15", "atardecer": "19:45"}
    sensores,       # {"radiacion": 600, "uv": 5}
    indices
)

indices.update(resultado)
# Ahora contiene todos los índices de luz/día
```

---

## FUNCIÓN 9: Índices de Cielo Nocturno
**Propósito:** Calcular calidad del cielo nocturno

### Pseudocódigo
```
FUNCIÓN calcular_indices_cielo_nocturno(indices, duracion_noche):
  // Usar funciones del módulo environmental_indices
  IMPORTAR _calcular_ventana_observacion_nocturna
  IMPORTAR _clasificar_indice_cielo
  
  cielo_observable ← indices.get("cielo_observable_nocturno")
  cielo_valor ← cielo_observable.get("valor") SI cielo_observable ES dict SINO cielo_observable
  
  // Calcular ventana de observación
  ventana ← _calcular_ventana_observacion_nocturna(cielo_valor, duracion_noche)
  
  SI ventana ≠ None:
    indices["ventana_observacion_nocturna"] = {
      "valor": round(ventana, 2),
      "estimado": True,
      "explicacion": "Horas útiles según cielo observable y duración de noche"
    }
  
  // Calcular índice compuesto
  SI cielo_valor ≠ None Y ventana ≠ None:
    cielo_normalizado ← max(0, min(1.0, cielo_valor / 100.0))
    ventana_normalizado ← max(0, min(1.0, ventana / 6.0))
    
    indice_cielo ← (0.7 * cielo_normalizado + 0.3 * ventana_normalizado) * 100
    
    indices["indice_cielo_astronomico"] = {
      "valor": round(indice_cielo, 2),
      "estimado": True,
      "explicacion": "Índice de cielo astronómico (cielo observable + ventana)"
    }
    
    indices["indice_cielo_astronomico_nivel"] = _clasificar_indice_cielo(indice_cielo)
```

---

## FUNCIONES AUXILIARES

### `_hhmm_a_minutos(hhmm: str) -> int`
```python
def hhmm_a_minutos(hhmm):
    """Convierte "06:15" a 375 minutos"""
    try:
        if not hhmm or ":" not in hhmm:
            return None
        h, m = hhmm.split(":")[:2]
        return int(h) * 60 + int(m)
    except:
        return None
```

### `_minutos_a_hhmm(total_min: int) -> str`
```python
def minutos_a_hhmm(total_min):
    """Convierte 375 minutos a "06:15" """
    try:
        total_min = total_min % (24 * 60)
        h = total_min // 60
        m = total_min % 60
        return f"{h:02d}:{m:02d}"
    except:
        return "--:--"
```

---

## INTEGRACIÓN EN CONTEXTO

### Orden de ejecución en `_estado_impl()`:
```
1. Cargar sensores persistidos
2. Inicializar EnvironmentalIndices
3. Obtener snapshot meteo
4. DETECTAR UBICACIÓN ← Función 4
5. CALCULAR ARCO SOLAR ← Función 5
6. CALCULAR RADIACIÓN TEÓRICA ← Función 6
7. CALCULAR AMANECER/ATARDECER ← Función 7
8. APLICAR LÓGICA HÍBRIDA DÍA/NOCHE ← Función 8
9. CALCULAR ÍNDICES DE CIELO ← Función 9
10. Añadir ubicación a indices
11. Ejecutar 40+ motores (CON contexto completo)
12. Retornar respuesta JSON
```

---

## FLUJO DE DATOS

```
CONFIG.txt / Sensores / Manager
        ↓
    detectar_ubicacion()
        ↓
    (lat, lon, origen)
        ↓
    ┌───────────────────────────────────────┐
    │ arco_solar()                          │
    │ radiacion_teorica()                   │
    │ calcular_amanecer_atardecer()         │
    │ determinar_dia_hibrido()              │
    │ calcular_indices_cielo_nocturno()    │
    └───────────────────────────────────────┘
        ↓
    indices = {
        "latitud": 41.5507,
        "longitud": -2.397,
        "origen_ubicacion": "manual",
        "arco_solar": 172.5,
        "duracion_dia_h": 11.5,
        "radiacion_teorica": 650,
        "nubosidad_estimada": 30,
        "amanecer": "06:15",
        "atardecer": "19:45",
        "es_dia_astronomico": True,
        "es_dia_sensor": True,
        "duracion_noche_h": 12.5,
        "ventana_observacion_nocturna": 4.2,
        "indice_cielo_astronomico": 75.3,
        ...
    }
        ↓
    contexto = {
        "sensores": {...},
        "indices": {...}  ← Completo con ubicación
    }
        ↓
    MotorLuzNatural().analizar(contexto)
    MotorRitmoCircadiano().analizar(contexto)
    MotorNocturno().analizar(contexto)
    ... (40+ motores más)
```

---

*Generado: 2 Feb 2026*
*Referencia: ANALISIS_PERDIDA_UBICACION_V26.md*
