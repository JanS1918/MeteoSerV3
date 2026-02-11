# 🔍 AUDITORIA DE VALORES HARDCODEADOS - BUSQUEDA DE CHAPUZAS

## ESTADO ACTUAL: Busqueda de valores fijos que deberían ser dinámicos

---

## 1. VALORES GEOGRAFICOS (ARGENTONA HARDCODEADA)

### ❌ PROBLEMA CRÍTICO

Los parámetros de ubicación están hardcodeados en múltiples lugares con valores fijos de Argentona:

```
Latitud:  41.5513° (FIJA)
Longitud: 2.3998° (FIJA)
Altitud suelo: 96.0 m (FIJA)
Altitud total: 109.0 m (FIJA)
Altura sensor: 13.0 m (FIJA)
```

### 📍 UBICACIONES CON VALORES FIJOS

#### 1. core/context/contexto_maestro_global.py
```python
# Línea 13-14: HARDCODEADOS EN INIT
def __init__(self, elevation_ground=96.0, elevation_total=109.0, 
             lat=41.5513, lon=2.3998, sensor_height_above_ground=13.0,...):

# Línea 62-68: HARDCODEADOS EN SINGLETON
cls._instance = ContextoMaestro(
    elevation_ground=96.0,      # ❌ FIJO
    elevation_total=109.0,      # ❌ FIJO
    lat=41.5513,                # ❌ FIJO
    lon=2.3998,                 # ❌ FIJO
    sensor_height_above_ground=13.0  # ❌ FIJO
)
```

#### 2. main_asgi.py
```python
# Línea 1779: HARDCODEADO EN CALCULO RADIACION
latitud = 41.5507  # ❌ FIJO (casi igual a 41.5513)
```

#### 3. core/integration/ecowitt_receiver.py
```python
# Línea 711: HARDCODEADO EN CALCULO
lat = indices.get("latitud", 41.5507)  # ❌ FIJO DEFAULT
```

#### 4. tools/arco_solar.py
```python
# Línea 38: HARDCODEADO EN HERRAMIENTA
lat = 41.55  # ❌ FIJO
```

### 🎯 DEBERÍA SER DINAMICO PORQUE:
- Sistema diseñado para ser portable (no solo Argentona)
- Cada ubicación tiene parámetros únicos:
  - Altitud afecta presión atmosférica (ISA)
  - Latitud afecta gravedad (Somigliana-Helmert)
  - Latitud afecta radiación solar
  - Rugosidad (z0) depende del terreno local
- Usuarios en otras ubicaciones recibirían datos incorrectos

---

## 2. RUGOSIDAD DEL TERRENO (z0) - FIJA

### ❌ PROBLEMA

```python
# core/context/contexto_maestro_global.py línea 31-32
self.z0_calle = 0.5      # ❌ Urbano típico (FIJO)
self.z0_terraza = 0.03   # ❌ Liso típico (FIJO)
```

### 🎯 DEBERÍA SER DINAMICO PORQUE:
- z0 depende del terreno específico:
  - Campo abierto: 0.001-0.01 m
  - Cultivos: 0.05-0.1 m  
  - Bosque: 0.3-2.0 m
  - Zona urbana: 0.5-1.5 m
  - Ciudad densa: 1-3 m
- Afecta drásticamente perfil de viento
- Monin-Obukhov requiere z0 exacto

### 📍 UBICACIONES

**core/context/contexto_maestro_global.py** líneas 31-32:
```python
self.z0_calle = 0.5      # ❌ SUPUESTO urbano "típico"
self.z0_terraza = 0.03   # ❌ SUPUESTO terraza "lisa"
```

---

## 3. PRESION ATMOSFERICA DE RESPALDO - FIJA

### ❌ PROBLEMA

ISA (International Standard Atmosphere) usado como fallback en múltiples lugares:

```
1013.25 hPa - PRESIÓN ESTÁNDAR A NIVEL DEL MAR
```

### 📍 UBICACIONES

#### 1. core/integration/ecowitt_receiver.py (línea 388)
```python
presion_fallback = 1013.25  # ❌ ISA FIJA
# Debería ser: ISA ajustada a altitud local
```

#### 2. data/indices_config.json
```json
"isa_defaults": {
    "presion": 1013.25,           # ❌ FIJA
    "presion_atmosferica": 1013.25,
    "pressure": 1013.25
}
```

#### 3. core/context/fallback_universal.py (línea 15)
```python
PRESION_ISA = 1013.25  # ❌ FIJA (nivel del mar)
```

### 🎯 DEBERIA SER DINAMICO PORQUE:
- 1013.25 hPa solo es válido a nivel del mar
- En Argentona (96 m): ≈ 1011.3 hPa (diferencia: -2 hPa)
- En 2000 m: ≈ 795 hPa (diferencia: -218 hPa)
- Usar ISA nivel mar en altura alta induce ERRORES GRANDES

**Fórmula ISA correcta:**
```
P(h) = 1013.25 × (1 - 0.0065×h/288.15)^5.255
```

Donde h = altitud en metros

---

## 4. CONSTANTE SOLAR - FIJA

### ❌ PROBLEMA

```python
# Múltiples ubicaciones
S0 = 1367  # W/m² - CONSTANTE SOLAR
```

### 📍 UBICACIONES

#### 1. core/indices/environmental_indices.py (línea 2157)
```python
S = 1367  # W/m² ❌ FIJA
```

#### 2. core/system/bus_expander.py (líneas 552, 706)
```python
S0 = 1367  # W/m² ❌ FIJA
```

### 🎯 VERIFICACION: ¿DEBERIA SER DINAMICA?

**NO** - La constante solar es **física universal**:
- Valor medio en órbita terrestre: 1367 W/m²
- Varía ±3% por ciclo solar (11 años)
- Pero para meteorología local: constante física legítima

**VEREDICTO**: ✅ OK (constante física, no chapuza)

---

## 5. PARÁMETROS DE SUELO - FIJOS

### ❌ PROBLEMA

```python
# core/context/contexto_maestro_global.py línea 24-27
self.estado_suelo = {
    "humedad": 0.25,      # ❌ FIJA 25% (suelo medio)
    "temperatura": 15.0,  # ❌ FIJA 15°C
    "conductividad": 0.8  # ❌ FIJA 0.8 W/mK
}
```

### 🎯 DEBERÍA SER DINAMICO PORQUE:
- Humedad suelo varía 0.05-0.40 según precipitación
- Temperatura suelo cambia con estación/hora
- Conductividad varía con tipo suelo:
  - Arena: 0.2-0.4 W/mK
  - Limo: 0.8-1.2 W/mK
  - Arcilla: 1.2-1.5 W/mK
- Afecta radiación neta, evapotranspiración

---

## 6. ELEVACION SOLAR - FIJA

### ❌ PROBLEMA

```python
# core/context/contexto_maestro_global.py línea 20
self.elevacion_solar = elevacion_solar if elevacion_solar is not None else 45.0
# ❌ DEFAULT A 45° (mediodía aproximado)
```

### 🎯 DEBERIA SER DINAMICO PORQUE:
- Cambia cada hora según hora solar local
- En invierno: max ~30°
- En verano: max ~70°+
- Afecta radiación solar, UVI, visibilidad
- Función `actualizar_astronomia()` existe pero no se llama

---

## 7. FACTOR SMOOTHING (EWMA) - FIJO

### ❌ PROBLEMA

```python
# main_asgi.py línea 289
SENSOR_SMOOTHING_ALPHA = 0.5  # ❌ FIJO
```

### 🎯 DEBERÍA SER DINAMICO PORQUE:
- Depende de frecuencia de datos:
  - Datos cada 1 minuto: α ≈ 0.03
  - Datos cada 5 minutos: α ≈ 0.15
  - Datos cada 10 minutos: α ≈ 0.25
- Valor 0.5 es agresivo (12 m período)
- Debería ser configurable por sensor

---

## 8. COEFICIENTES FISICOS - REVISAR VALIDEZ

### ✅ VERIFICACION: Estos son constantes FISICAS UNIVERSALES

| Constante | Valor | Ubicación | Validez |
|-----------|-------|-----------|---------|
| R_d | 287.05 J/(kg·K) | advanced_physics_models.py | ✅ Constante universal |
| R_v | 461.5 J/(kg·K) | advanced_physics_models.py | ✅ Constante universal |
| ε (epsilon) | 0.62198 | advanced_physics_models.py | ✅ Relación Mv/Md |
| g | 9.81 m/s² | Múltiples | ⚠️ Mejora con Somigliana |
| σ | 5.67e-8 W/(m²·K⁴) | advanced_physics_models.py | ✅ Stefan-Boltzmann |
| Magnus 1-3 | 6.112, 17.67, 243.5 | advanced_physics_models.py | ✅ Coeficientes empíricos |

**Nota**: g(41.55°N) = 9.8037 m/s² (implementado en Somigliana-Helmert) ✅

---

## RESUMEN DE CHAPUZAS DETECTADAS

| Severidad | Parámetro | Estado | Acción Requerida |
|-----------|-----------|--------|-----------------|
| 🔴 CRÍTICA | Ubicación geográfica (lat/lon/alt) | HARDCODEADO | Leer de config |
| 🔴 CRÍTICA | Rugosidad terreno (z0) | HARDCODEADO | Leer de config |
| 🟡 ALTA | Presión ISA fallback | HARDCODEADO | Calcular con altitud |
| 🟡 ALTA | Estado suelo (humedad/temp) | HARDCODEADO | Sensor o config |
| 🟠 MEDIA | Elevación solar | FIJA EN CONFIG | Calcular dinámicamente |
| 🟠 MEDIA | EWMA alpha | HARDCODEADO | Parametrizable |
| ✅ OK | Constante solar | FIJA CORRECTAMENTE | Mantener |
| ✅ OK | Constantes físicas | FIJAS CORRECTAMENTE | Mantener |

---

## RECOMENDACIONES

### 1️⃣ INMEDIATA (Bloquea Producción)
```
[ ] Crear config_estacion.json con parámetros de ubicación
[ ] Leer ubicación de config al inicio
[ ] Pasar ubicación a ContextoMaestro via singleton
```

### 2️⃣ ALTA PRIORIDAD  
```
[ ] Calcular ISA de fallback en función de altitud
[ ] Permitir configurar z0_calle y z0_terraza
[ ] Pasar estado_suelo a sensores reales si disponibles
```

### 3️⃣ MEJORA CONTINUA
```
[ ] Calcular elevación solar dinámicamente cada vez que se llama
[ ] Hacer EWMA alpha configurable por sensor
```

### 4️⃣ VALIDACIÓN
```
[ ] Tests comparan resultados con ubicación real vs ISA
[ ] Verificar UTCI con otros datos de Argentona
[ ] Sensibilidad: cambiar lat → cambiar resultados
```

---

## EJEMPLO: IMPACTO DE CHAPUZAS

### Escenario 1: Sistema en Barcelona (60 m)
```
Argentona (96 m) values:
  ISA fallback: 1013.25 hPa ❌
  
Barcelona (60 m) real:
  ISA esperada: ~1013.6 hPa
  ERROR: -0.35 hPa (menor, pero visible)
```

### Escenario 2: Sistema en La Paz, Bolivia (3640 m)
```
Argentona values (hardcodeadas):
  ISA fallback: 1013.25 hPa ❌
  Lat: 41.55° (Argentona) ❌
  z0: 0.5 m urbano (incorrecto) ❌
  
La Paz real:
  ISA esperada: ~650 hPa
  ERROR: +363.25 hPa (CATASTRÓFICO)
  Lat: -16.5° (diferente gravedad, radiación)
  z0: 1.5 m (ciudad andina)
  
RESULTADO: Todos los cálculos INVALIDOS
```

---

## CONCLUSIÓN

**Sistema NO es portable actualmente.**  
**Todos los valores geográficos están hardcodeados.**  
**Debería usarse sistema de configuración dinámico.**

**Status**: REQUIERE LIMPIEZA ANTES DE PRODUCCIÓN MULTI-SITIO

