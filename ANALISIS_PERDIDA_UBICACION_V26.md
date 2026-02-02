# 🔍 ANÁLISIS DE PÉRDIDA: Ubicación, Arco Solar y Astronomía en main_asgi.py

## ⚠️ RESUMEN EJECUTIVO
En la rama backup `ojo_20260202_102049`, el archivo `main_asgi.py` contenía **una sección CRÍTICA de 250+ líneas** que:
1. Extrae/valida/gestiona ubicación (lat/lon)
2. Calcula arco solar, amanecer/atardecer, radiación teórica
3. Genera índices astronómicos y de cielo nocturno
4. Integra todo en la respuesta JSON de `/api/panel/superior`

**Versión actual (main_asgi.py):** Solo 198 líneas. Redujo 94% de funcionalidad.

---

## 📊 FUNCIONES PERDIDAS

### 1. **`_coords_valid(lat, lon)` - Validación de Coordenadas**
```python
def _coords_valid(lat, lon):
    try:
        return lat is not None and lon is not None and -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180
    except Exception:
        return False
```
- **Propósito:** Validar que latitud/longitud sean valores numéricos y dentro de rangos terrestres
- **Dónde se llamaba:** En la cadena de detección de ubicación (línea ~1495)
- **Importancia:** CRÍTICA para evitar inyecciones de datos inválidos al motor de radiación

---

### 2. **`_parse_coord(val)` - Parseador Geocodificación**
```python
def _parse_coord(val):
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
```
- **Propósito:** Convertir coordenadas en múltiples formatos:
  - `41.5507N` → `41.5507`
  - `-2.397W` → `2.397` (con signo negativo)
  - `41,5507` (con coma) → `41.5507` (normaliza separador decimal)
- **Dónde se llamaba:** Extracción desde `system.sensores.get("latitud")`
- **Importancia:** CRÍTICA para aceptar entrada de múltiples formatos geocodificadores

---

### 3. **`_coords_es_spain(lat, lon)` - Validación España**
```python
def _coords_es_spain(lat, lon):
    try:
        lat = float(lat)
        lon = float(lon)
        return 35 <= lat <= 44.5 and -10 <= lon <= 4.5
    except Exception:
        return False
```
- **Propósito:** Verificar que las coordenadas sean coherentes con España (fallback)
- **Lógica:** Si no son manuales, rechaza si están fuera de los límites españoles
- **Fallback:** Si coordenadas inválidas, asigna Argentona (41.5507, -2.397)
- **Importancia:** MEDIA - Protección contra anomalías geográficas

---

### 4. **Lógica de Detección Jerárquica de Ubicación**
**Flujo en el backup (líneas 1471-1539):**

```
1. Intenta leer latitud/longitud del CONFIG_PATH (meteoser_configuracion.txt)
   └─ Llama: manager.set_manual_coordinates(latitud, longitud)
   └─ origen_ubicacion = "manual" ✓

2. Si falla (1), intenta desde sensores del sistema
   └─ Busca: system.sensores.get("latitud") o system.sensores.get("lat")
   └─ Intenta: system.sensores.get("longitud") o system.sensores.get("lon")
   └─ Aplica: _parse_coord() a cada uno
   └─ origen_ubicacion = "sensor" ✓

3. Si falla (2), consulta manager.obtener_coordenadas()
   └─ Esto trae coordenadas previamente geocodificadas/estimadas
   └─ origen_ubicacion = coords.get("origen", "estimada") ✓

4. Si TODO falla, usa FALLBACK
   └─ latitud = 41.5507 (Argentona)
   └─ longitud = -2.397
   └─ origen_ubicacion = "desconocida"
```

**En el código actual:** Esta lógica COMPLETA desapareció.

---

### 5. **Cálculo de Arco Solar y Duración del Día**
```python
# Línea 1545-1547 del backup
hoy = datetime.datetime.now().timetuple().tm_yday
arco = arco_solar(latitud, hoy)

# Línea 1583 - Se añadía al índice
indices["arco_solar"] = {"valor": round(arco, 2), "estimado": estimado_arco}
indices["duracion_dia_h"] = {"valor": round(arco / 15.0, 2), "estimado": estimado_arco}
```
- **Función externa:** `from tools.arco_solar import arco_solar`
- **Entrada:** Latitud, día del año (1-365)
- **Salida:** Arco solar en grados
- **Cálculo:** `duracion_hora = arco / 15.0` (conversión grados a horas)
- **Marcador:** `"estimado": True/False` (si origen es manual, estimado=False)
- **Importancia:** CRÍTICA para todos los 6 motores (luz natural, ritmo circadiano, etc.)

---

### 6. **Función `_radiacion_teorica(lat_deg, day, hora_decimal)`**
```python
def _radiacion_teorica(lat_deg, day, hora_decimal):
    import math
    lat_rad = math.radians(lat_deg)
    # Declinación solar
    delta = 0.409 * math.sin(2 * math.pi * (day - 81) / 368)
    # Ángulo horario
    omega = math.radians((hora_decimal - 12.0) * 15.0)
    # Altitud solar
    sin_alt = math.sin(lat_rad) * math.sin(delta) + math.cos(lat_rad) * math.cos(delta) * math.cos(omega)
    if sin_alt <= 0:
        return 0
    # Constante solar + factor de distancia Tierra-Sol
    gsc = 1361.0  # W/m² (constante solar extraterrestre)
    dr = 1 + 0.033 * math.cos(2 * math.pi * day / 365.0)  # Distancia relativa
    return gsc * dr * sin_alt
```
- **Entrada:** Latitud en grados, día del año, hora decimal (12.5 = 12:30)
- **Salida:** Radiación teórica en W/m²
- **Algoritmo:** Ecuación de radiación solar de Spencer (simplificada)
- **Uso:** Estimar nubosidad si falta sensor de radiación
- **Importancia:** CRÍTICA para:
  - Motor de radiación UV
  - Detección de anomalías (nubosidad)
  - Brújula táctica (si falta radiación real)

---

### 7. **Cálculo de Amanecer/Atardecer Híbrido**
```python
# Línea 1559 del backup
from tools.amanecer_atardecer import calcular_amanecer_atardecer

# Línea 1571
horas_sol = calcular_amanecer_atardecer(latitud, longitud, hoy, utc_offset)

# Línea 1614-1671: Lógica híbrida
amanecer_astro = horas_sol.get("amanecer")      # "06:15"
atardecer_astro = horas_sol.get("atardecer")    # "19:45"

# Comparación con sensor
es_dia_sensor = (radiacion >= 50 or uv > 0.1)
es_dia_astronomico = (amanecer_min <= ahora_min <= atardecer_min)

# Ajuste híbrido si hay discrepancia
if es_dia_astronomico is False and es_dia_sensor:
    if abs(ahora_min - amanecer_min) <= 90:  # ventana_min
        amanecer_hibrido = _min_to_hhmm(ahora_min)  # Usa hora actual

indices["amanecer"] = amanecer_hibrido
indices["atardecer"] = atardecer_hibrido
indices["amanecer_astronomico"] = amanecer_astro
indices["atardecer_astronomico"] = atardecer_astro
```
- **Propósito:** Sincronizar astronomía con sensores para detectar anomalías
- **Indices generados:**
  - `amanecer`, `atardecer` (mejor estimación)
  - `amanecer_astronomico`, `atardecer_astronomico` (teórico)
  - `es_dia_sensor`, `es_dia_astronomico`
  - `desvio_amanecer_min`, `desvio_atardecer_min` (diferencia)
  - `inconsistencia_luz` (bandera de error)
- **Importancia:** CRÍTICA para:
  - Motor de luz natural
  - Motor de ritmo circadiano
  - Detección de fallas de sensores

---

### 8. **Índices Astronómicos Compuestos**
```python
# Líneas 1693-1726 del backup
from core.indices.environmental_indices import (
    _calcular_ventana_observacion_nocturna,
    _clasificar_indice_cielo
)

duracion_noche = 24.0 - duracion_dia
indices["duracion_noche_h"] = {"valor": round(duracion_noche, 2), "estimado": True}

ventana = _calcular_ventana_observacion_nocturna(cielo_observable, duracion_noche)
indices["ventana_observacion_nocturna"] = {
    "valor": round(ventana, 2),
    "estimado": True,
    "explicacion": "Horas útiles según cielo observable y duración de noche"
}

indice_cielo = (0.7 * (cielo / 100) + 0.3 * (ventana / 6.0)) * 100
indices["indice_cielo_astronomico"] = {
    "valor": round(indice_cielo, 2),
    "estimado": True,
    "explicacion": "Índice de cielo astronómico (cielo observable + ventana)"
}
indices["indice_cielo_astronomico_nivel"] = _clasificar_indice_cielo(indice_cielo)
```
- **Índices generados:**
  - `duracion_noche_h`
  - `ventana_observacion_nocturna`
  - `indice_cielo_astronomico`
  - `indice_cielo_astronomico_nivel`
- **Importancia:** CRÍTICA para:
  - Motor nocturno
  - Motor de astronomía
  - Ritmo circadiano nocturno

---

### 9. **Integración de Ubicación en Respuesta JSON**
```python
# Línea 1728-1730 del backup
indices["latitud"] = latitud
indices["longitud"] = longitud
indices["origen_ubicacion"] = origen_ubicacion

# Luego incluido en return gigante (línea 1892+)
return {
    "sensores": sensores,
    "indices": indices,  # ← Incluye ubicación
    "ambiental": ambiental,
    "confort": confort,
    # ... 40+ motores más
}
```
- **Propósito:** Exponer ubicación para:
  - Debug/auditoría
  - UI (mostrar donde está instalado)
  - Recalcular dinámicamente si cambia
- **Importancia:** MEDIA/BAJA (informativa pero no operativa)

---

### 10. **Funciones Auxiliares Perdidas**
```python
# Línea 1735-1747
def _hhmm_to_min(hhmm: str):
    """Convierte "06:15" a 375 minutos"""
    if not hhmm or ":" not in hhmm:
        return None
    h, m = hhmm.split(":")[:2]
    return int(h) * 60 + int(m)

def _min_to_hhmm(total_min: int):
    """Convierte 375 minutos a "06:15" """
    total_min = total_min % (24 * 60)
    h = total_min // 60
    m = total_min % 60
    return f"{h:02d}:{m:02d}"
```
- **Propósito:** Conversión de horarios para comparación y ajuste
- **Importancia:** MEDIA - Helpers de cálculo

---

## 🔌 INTEGRACIONES PERDIDAS CON LOS 6 MOTORES

### **Motor Ambiental** (`ambiental_motor.py`)
- ❌ **Perdió:** `radiacion_teorica`, `nubosidad_estimada`
- ❌ **Efecto:** No puede estimar nubosidad si falta sensor radiación
- ⚠️ **Riesgo:** Anomalía del ambiente no detectada

### **Motor Confort** (`confort_motor.py`)
- ❌ **Perdió:** `arco_solar`, `duracion_dia_h`, ubicación base
- ❌ **Efecto:** No puede ajustar umbrales de confort por latitud
- ⚠️ **Riesgo:** Recomendaciones no personalizadas por zona

### **Motor Luz Natural** (`luz_natural_motor.py`)
- ❌ **Perdió:** `amanecer`, `atardecer`, `es_dia_astronomico`, `es_dia_sensor`
- ❌ **Efecto:** Motor completamente inoperante
- 🔴 **RIESGO CRÍTICO:** No detecta día/noche correctamente

### **Motor Ritmo Circadiano** (`ritmo_circadiano_motor.py`)
- ❌ **Perdió:** `amanecer_hibrido`, `atardecer_hibrido`, `duracion_dia_h`
- ❌ **Efecto:** No ajusta ritmo de descanso a horario solar real
- 🔴 **RIESGO CRÍTICO:** Recomendaciones de sueño desincronizadas

### **Motor Nocturno** (`nocturno_motor.py`)
- ❌ **Perdió:** `duracion_noche_h`, `ventana_observacion_nocturna`, `indice_cielo_astronomico`
- ❌ **Efecto:** No calcula calidad de observación nocturna
- ⚠️ **RIESGO CRÍTICO:** Astronomía/observación completamente ciega

### **Motor de Radiación/UV**
- ❌ **Perdió:** `radiacion_teorica`, `latitud`, `longitud`
- ❌ **Efecto:** No puede validar mediciones de UV ni estimar si radiación es anómala
- ⚠️ **RIESGO CRÍTICO:** UV indetectable en anomalías

---

## 📋 IMPORTANCIA PARA VECTOR #26

### **Física Correcta (Rayleigh-Bucholtz)**
```
ANTES (Backup):
┌─ Ubicación (lat/lon) ─┐
│                       ├─→ Arco Solar
│                       │
└─ Sensor radiación ◄────┼─→ Radiación Teórica
                        │
                        └─→ Nubosidad Estimada
                           ↓
                        Índices Correctos

AHORA (Main_asgi.py):
┌─ Ubicación (PERDIDA)
│
└─ Sensor radiación (SIN CONTEXTO)
   ↓
   Índices INCOMPLETOS
```

### **Físicas Afectadas**
1. **Ecuación de Radiación:** Necesita `lat_deg` + `day` + `hora_decimal`
   - Sin ubicación = **SIN VALIDACIÓN DE ANOMALÍAS**

2. **Cielo Nocturno:** Necesita `duracion_noche` + `cielo_observable`
   - Sin duración = **NO CALCULA VENTANA DE OBSERVACIÓN**

3. **Ritmo Circadiano:** Necesita amanecer/atardecer REAL
   - Sin horario solar = **DESINCRONIZACIÓN**

---

## 🛠️ CÓMO RESTAURARLO

### **Opción A: Restaurar desde backup** (RECOMENDADO)
```bash
git show backup/ojo_20260202_102049:main_asgi.py > main_asgi_v26_con_ubicacion.py
# Extraer sección de ubicación (líneas 1471-1730)
# Integrar en nuevo main_asgi.py moderno
```

### **Opción B: Recodificar secciones críticas**
1. Instanciar `SystemManager` con ubicación
2. Añadir endpoint `GET /api/ubicacion` que devuelva `{lat, lon, origen}`
3. Modificar `/api/panel/superior` para inyectar ubicación en contexto
4. Re-calcular índices astronómicos antes de devolver respuesta

### **Opción C: Usar módulo `app/ui/router.py`**
- Revisar si `app/ui/router.py` ya maneja ubicación
- Si no, trasladar lógica de backup allá

---

## 📦 ARCHIVOS DE APOYO NECESARIOS

```
✓ tools/arco_solar.py           [EXISTE] - Importa en backup L282
✓ tools/amanecer_atardecer.py   [EXISTE] - Importa en backup L1559
✓ core/indices/environmental_indices.py
  ├─ _calcular_ventana_observacion_nocturna()  [CHECK]
  └─ _clasificar_indice_cielo()                [CHECK]
? core/system/system_manager.py
  ├─ set_manual_coordinates(lat, lon)  [CHECK]
  └─ obtener_coordenadas()             [CHECK]
```

---

## 🎯 CONCLUSIÓN

**La sección de ubicación/astronomía NO ERA OPCIONAL:**
- Fue eliminada en una refactorización que modernizó `main_asgi.py`
- Pero **nunca fue trasladada** a `app/ui/router.py`
- Resultado: **6 motores operan sin datos críticos**

**Próximos pasos:**
1. ✅ Inventariar exactamente dónde se movió (o si se perdió)
2. ✅ Restaurar cálculos astronómicos
3. ✅ Integrar ubicación en contexto de análisis
4. ✅ Validar física Vector #26 (Rayleigh + Bucholtz)

---

*Generado: 2 Feb 2026*
*Rama analizada: backup/ojo_20260202_102049*
*Estado: CRÍTICO - 6 motores sin datos de ubicación*
