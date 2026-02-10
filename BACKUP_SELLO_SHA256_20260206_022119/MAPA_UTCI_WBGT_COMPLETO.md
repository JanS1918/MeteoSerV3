# 🗺️ MAPA COMPLETO: UTCI Y WBGT EN EL SISTEMA

Fecha: 5 FEB 2026  
Comandante: Análisis exhaustivo de dónde está cada fórmula y cómo circula por el Bus

---

## 📌 PARTE 1: ¿QUÉ VERSIÓN DE UTCI TENEMOS?

### **La Versión PRINCIPAL: Diamond_Refined_v1 (Fiala 2012)**

**Ubicación del código:**
- [core/indices/environmental_indices.py](core/indices/environmental_indices.py#L1150) línea 1150+
- Función: `indice_utci()`
- Status: ✅ ACTIVA EN PRODUCCIÓN

**Fórmula base:**
- Modelo termorregulatorio de 64 nodos (Fiala et al. 2012)
- 45 científicos, 23 países
- ISO 14505-2 certified
- Precisión: ±0.1°C

**Con qué se FUSIONA:**
```
indice_utci() 
  ↓ (internamente)
  ├─ Radiación (Gueymard REST2 + SRTM + Ocaso Topográfico)
  ├─ Viento (Gryning capa límite, 2 contextos: calle vs terraza)
  ├─ Humedad (Real si HP2550A, estimada si falla)
  ├─ Presión (IAPWS Elite si disponible, fallback Hardy)
  └─ UTCI v2 (Blazejczyk 2013) INTERNAMENTE si:
     - RH > 85% (alta humedad)
     - T > 35°C (calor extremo)
     - T < -10°C (frío extremo)
```

### **La Versión SECUNDARIA: UTCI v2 Blazejczyk (2013) - OCULTA**

**Ubicación del código:**
- [core/indices/utci_v2_blazejczyk.py](core/indices/utci_v2_blazejczyk.py) línea 35+
- Función: `utci_v2_blazejczyk()`
- Status: ✅ **OCULTA en FORMULA_HIERARCHY (hasta hace 24h)**
- Status: ✅ **AHORA REGISTRADA como BÁSICO (20 Jan 2026)**

**Fórmula base:**
- Blazejczyk et al. (2013) - mejoras para extremos térmicos
- Precisión: ±0.2°C
- Rango: -40°C a +50°C

**Dónde se CARGA:**
```
En indice_utci() internamente:
Si (RH > 85% OR T > 35°C OR T < -10°C):
    utci_calle_v2 = utci_v2_blazejczyk(...)  # contexto CALLE
    utci_sensor_v2 = utci_v2_blazejczyk(...)  # contexto TERRAZA
    
    Si condición se cumple:
        utci_calle = utci_calle_v2  # Reemplaza v1
        utci_sensor = utci_sensor_v2  # Reemplaza v1
        metodo_utci = "Diamond_Refined_v1 + Blazejczyk v2 (2013)"
```

**Retorna ahora:**
```python
{
    "calle": float,          # UTCI contexto CALLE
    "sensor": float,         # UTCI contexto TERRAZA
    "calle_v2": float,       # Versión v2 si se usó
    "sensor_v2": float,      # Versión v2 si se usó
    "delta_v2_calle": float, # Diferencia v2 vs v1 CALLE
    "delta_v2_sensor": float,# Diferencia v2 vs v1 TERRAZA
    "tmrt": float,           # Temperatura radiante media calculada
    "wind_calle": float,     # Viento corregido contexto CALLE
    "wind_sensor": float,    # Viento corregido contexto TERRAZA
    "motor": str,            # Método usado ("Diamond_Refined_v1" o "...+ Blazejczyk v2")
    "presion_fuente": str,   # De dónde vino presión
    "presion_pa": float,     # Presión en Pa
}
```

---

## 🛣️ DÓNDE SE UTILIZA UTCI

### **1. EN EL CÓDIGO PRODUCTOR (EnvironmentalIndices)**

**Archivo:** [core/indices/environmental_indices.py](core/indices/environmental_indices.py#L4809)  
**Línea:** 4809+  
**Función:** `EnvironmentalIndices.sensacion_termica()`

```python
# Llama a indice_utci() y publica en BUS
utci_result = indice_utci(t_val, h_val, v_ms, rad_val, contexto)

# Extrae componentes
utci_calle = utci_result["calle"]
utci_sensor = utci_result["sensor"]
tmrt = utci_result["tmrt"]

# PUBLICA EN BUS
self._bus.publicar("sensacion_termica", utci_result["calle"], "indice_utci")
```

### **2. EN EL BUS (bus_expander.py)**

**Archivo:** [core/system/bus_expander.py](core/system/bus_expander.py#L2667)  
**Línea:** 2667-2710

```python
# PUBLICA: indice_utci() en contexto BusExpander
try:
    from core.indices.environmental_indices import indice_utci
    utci_result = indice_utci(temp_c, humedad, viento / 3.6, radiacion, contexto)
    
    if isinstance(utci_result, dict):
        utci_val = utci_result.get("calle")
    else:
        utci_val = utci_result
    
    self.bus.publicar("utci", utci_val, "°C")
    self.bus.publicar("utci_categoria_estrés", "...", "string")
    
except Exception as e:
    self.bus.publicar("utci", None, "°C")
```

**TAMBIÉN PUBLICA subfactores:**

[core/system/bus_expander.py](core/system/bus_expander.py#L5627) línea 5627+

```python
# Constantes UTCI (para análisis)
self.bus.publicar("utci_polynomial", utci, "°C")
self.bus.publicar("utci_temp_min", -50, "°C")
self.bus.publicar("utci_temp_max", 60, "°C")
self.bus.publicar("utci_viento_min", 0.1, "m/s")
self.bus.publicar("utci_viento_max", 17, "m/s")
self.bus.publicar("utci_vp_min", 0, "hPa")
self.bus.publicar("utci_vp_max", 54, "hPa")
self.bus.publicar("utci_delta_radiante_min", -50, "K")
self.bus.publicar("utci_delta_radiante_max", 120, "K")

# Thresholds UTCI de estrés
self.bus.publicar("utci_estres_frio_extremo", -40, "°C")
self.bus.publicar("utci_estres_frio_muy_fuerte", -27, "°C")
self.bus.publicar("utci_estres_frio_fuerte", -13, "°C")
self.bus.publicar("utci_estres_frio_moderado", 0, "°C")
self.bus.publicar("utci_sin_estres_termico", 9, "°C")
self.bus.publicar("utci_estres_calor_moderado", 26, "°C")
self.bus.publicar("utci_estres_calor_fuerte", 32, "°C")
self.bus.publicar("utci_estres_calor_muy_fuerte", 38, "°C")
self.bus.publicar("utci_estres_calor_extremo", 46, "°C")
```

### **3. EN LA UI (Tablet/Dashboard)**

**Archivo:** [app/ui/router.py](app/ui/router.py#L177)  
**Línea:** 177+

```python
# MUESTRA EN INTERFAZ
valores_termo.append(ValorSistema(
    nombre='UTCI Calle (Fiala)',
    tipo='índice',
    valor=valor_uc,  # valor del bus
    unidad='°C',
    fiabilidad=fiab_uc,
    icono='🛣️',
    prioridad=92,
    sensores=['temperatura', 'humedad', 'viento', 'radiacion'],
    dependencias=['UTCI']
))

valores_termo.append(ValorSistema(
    nombre='UTCI Sensor (Fiala)',
    tipo='índice',
    valor=valor_us,
    unidad='°C',
    fiabilidad=fiab_us,
    icono='🏠',
    prioridad=91,
    sensores=['temperatura', 'humedad', 'viento', 'radiacion'],
    dependencias=['UTCI']
))
```

### **4. EN ENDPOINTS REST (main_asgi.py)**

**Archivo:** [main_asgi.py](main_asgi.py#L2360)  
**Línea:** 2360+

```json
{
    "sensacion_termica_ext": {
        "heat_index": [valor del bus],
        "humidex": [valor del bus o fallback],
        "compuesta": [valor calculado]
    }
}
```

### **5. EN GUARDIAN DUELO (Comparador de Fórmulas)**

**Archivo:** [core/bus/formula_hierarchy.py](core/bus/formula_hierarchy.py#L70)  
**Status:** ✅ REGISTRADA como ELITE

```python
"sensacion_termica": {
    NivelElite.ELITE: Fórmula(
        nombre_tecnico="indice_utci",
        nombre_legible="Universal Thermal Climate Index (ISO 14505-2)",
        módulo="core.indices.environmental_indices",
        referencia="Fiala et al. (2012) ISO 14505-2",
        precisión="±0.1°C",
        ...
    ),
}
```

Guardian entiende: "Para sensacion_termica, ELITE es indice_utci"

### **6. DÓNDE NO SE UTILIZA (Vacíos actuales)**

❌ **No hay endpoint específico `/api/utci`** - Se consume como `sensacion_termica`  
❌ **No hay tabla histórica UTCI propia** - Se mezcla con otros índices  
❌ **No se compara activamente contra UTCI v2** - v2 solo se usa internamente si extremos  
❌ **No se envía a API extern**as como alerting - Queda en bus interno  

---

## 💦 DÓNDE SE UTILIZA WBGT

### **1. EN EL CÓDIGO PRODUCTOR (OCULTO HASTA HOY)**

**Ubicación del código:**
- [core/indices/environmental_indices.py](core/indices/environmental_indices.py#L1663) línea 1663+
- Función: `indice_wbgt()`
- Status: ✅ **OCULTA en FORMULA_HIERARCHY (hasta hace 24h)**
- Status: ✅ **AHORA REGISTRADA como PROFESIONAL**

**Fórmula:**
```python
def indice_wbgt(temp_c, humedad, radiacion=0, viento_kmh=0, ...):
    """
    WBGT con bulbo húmedo unificado (Stull).
    - Usa modelo Liljegren-Carhart (2008)
    - Calcula Tw (bulbo húmedo) sin psicrómetro
    - Calcula Tg (globo negro) sin sensor físico
    - Fórmula: WBGT = 0.7·Tw + 0.2·Tg + 0.1·Ta
    """
    tw = indice_bulbo_humedo_c(temp_c, humedad, dt)
    Tg = temp_c + 0.1 * radiacion / 100  # Aproximación 
    wbgt = 0.7 * tw + 0.2 * Tg + 0.1 * temp_c
    return wbgt
```

**Status en sistema:**
- ✅ Importable: `from core.indices.environmental_indices import indice_wbgt`
- ✅ Llama a funciones internas reales
- ❌ **NUNCA se publica en el BUS actualmente** (es el problema)
- ❌ **NO se usa en sensacion_termica()** (solo UTCI)
- ✅ Ahora se puede llamar MANUALMENTE en tests

### **2. EN FÓRMULAS EXTERNAS (NUEVO - v47.5)**

**Ubicación:** [core/indices/formulas_externas_v47_5.py](core/indices/formulas_externas_v47_5.py#L99)  
**Línea:** 99+

```python
def wbgt_yaglou_osha(
    temperatura_globo_negro,
    temperatura_bulbo_humedo,
    temperatura_bulbo_seco,
    **kwargs
) -> Optional[float]:
    """WBGT - Wet Bulb Globe Temperature"""
    T_bh = temperatura_bulbo_humedo
    T_bg = temperatura_globo_negro
    T_bs = temperatura_bulbo_seco
    WBGT = 0.7 * T_bh + 0.2 * T_bg + 0.1 * T_bs
    return round(WBGT, 1)
```

**Status:** 📋 Candidata EXTERNA registrada (no integrada aún)

### **3. EN BUS_EXPANDER (HISTORIAS PASADAS - COMENTADO)**

**Archivo:** [core/system/bus_expander_V13_BACKUP_20260202_180608.py](core/system/bus_expander_V13_BACKUP_20260202_180608.py#L1469)

```python
# INTENTO ANTERIOR (COMENTADO):
try:
    from core.indices.liljegren_wbgt import calcular_wbgt_liljegren
    resultado_wbgt = calcular_wbgt_liljegren(temp_c, humedad, radiacion, viento)
    wbgt = resultado_wbgt.get("wbgt", temp_c)
    self.bus.publicar("wbgt", wbgt, "°C")
except:
    self.bus.publicar("wbgt", temp_c, "°C")
```

**Status actual:** ⚠️ Archivo de BACKUP (no se ejecuta)

### **4. EN FORMULA_HIERARCHY (REGISTRADA HOY)**

**Archivo:** [core/bus/formula_hierarchy.py](core/bus/formula_hierarchy.py#L94)  
**Status:** ✅ REGISTRADA como PROFESIONAL

```python
"sensacion_termica": {
    ...
    NivelElite.PROFESIONAL: Fórmula(
        nivel=NivelElite.PROFESIONAL,
        nombre_tecnico="indice_wbgt",
        nombre_legible="Wet Bulb Globe Temperature (OSHA)",
        módulo="core.indices.environmental_indices",
        referencia="Yaglou & Minard (1957) - NOAA/US Military",
        precisión="±1°C",
        rango_validez=(-10, 55),
        requisitos_datos=["temperatura", "humedad", "radiacion", "viento"],
        notas="Estándar OSHA para ambientes ocupacionales [PREVIAMENTE OCULTA - AUTOREPARADA]"
    ),
}
```

**Implicación:** Guardian DUELO ahora sabe que existe, pero...

### **5. DÓNDE WBGT NO SE UTILIZA (Problemas)**

❌ **No se publica en el BUS automáticamente** - Solo en código de tests  
❌ **No aparece en sensacion_termica()** - Esa función solo devuelve UTCI  
❌ **No hay endpoint `/api/wbgt`**  
❌ **No aparece en UI/tablet**  
❌ **No se registra en históricos**  
❌ **No se alimenta a alertas de riesgo ocupacional**  

**Consecuencia:** Guardian lo VE en FORMULA_HIERARCHY, pero no puede USARLO porque no hay datos publicados en el BUS.

---

## 🔄 TABLA COMPARATIVA: UTCI vs WBGT

| Aspecto | UTCI | WBGT |
|--------|------|------|
| **Versión** | Diamond_Refined_v1 (Fiala 2012) + v2 (Blazejczyk 2013) internamente | Liljegren-Carhart (2008) / Yaglou-Minard (1957) |
| **Código existe** | ✅ Sí, línea 1150+ | ✅ Sí, línea 1663+ |
| **Registrado en FORMULA_HIERARCHY** | ✅ Sí, ELITE | ✅ Sí, PROFESIONAL (NUEVO) |
| **Se publica en BUS** | ✅ SÍ, como "utci" y "sensacion_termica" | ❌ NO (nunca publicado) |
| **Aparece en UI/Tablet** | ✅ SÍ, dos campos (Calle + Sensor) | ❌ NO |
| **Guardian lo ve** | ✅ SÍ, para duelos | ✅ SÍ, pero sin datos |
| **Tipo de dato** | Confort general (sensación térmica) | Seguridad ocupacional (estrés calor) |
| **Consumidor principal** | Usuarios generales, control climático | Alertas OSHA, deportistas, militares |
| **Precisión** | ±0.1°C | ±1°C |
| **Rango validez** | -50 a +60°C | -10 a +55°C |

---

## 🛠️ QUIN SE FUSIONAN Y CON QUÉ

### **UTCI se fusiona con:**

1. **Radiación (Gueymard REST2 + SRTM)**
   - Ocaso topográfico del Maresme
   - Cálculo: `tmrt = calcular_radiacion_extraterrestre_rest2(...)`
   
2. **Viento (Capa límite Gryning)**
   - 2 contextos: CALLE (h=13m) y TERRAZA (h=2m)
   - Cálculo: `v_calle = viento_logaritmico(v_sensor, h_sensor=13.0, ...)`

3. **Humedad (Real + Estimada)**
   - Real: `HP2550A` si funciona
   - Estimada: `_estimar_humedad_inteligente()` si falla

4. **Presión (IAPWS Elite + Fallback Hardy)**
   - Elite: `presion_iapws_elite_eos(T, rho)`
   - Fallback: `presion_hardy_barometrica(...)`

5. **Contexto local (Argentona)**
   - Lat/Lon/Alt del sistema
   - Zona 0 (z0_calle, z0_terraza)

### **WBGT se fusionaría con:** (si se habilitara)

1. **Bulbo Húmedo (Cálculo Stull)**
   - `tw = indice_bulbo_humedo_c(temp_c, humedad, dt)`

2. **Globo Negro Virtual (ISO 7726)**
   - `Tg = temp_c + 0.1 * radiacion / 100`

3. **Componentes separados**
   - 0.7 × Tw (evaporación de sudor)
   - 0.2 × Tg (radiación térmica)
   - 0.1 × Ta (convección aire)

---

## 📊 FLUJO ACTUAL DE DATOS

### **UTCI: ACTIVO**
```
Sensores (HP2550A, Vaisala, etc)
  ↓
core/indices/environmental_indices.py::indice_utci()
  ├─ Fiala 2012 (v1) siempre
  ├─ + Blazejczyk 2013 (v2) si extremos
  └─ + Radiación Gueymard + Viento Gryning + Humedad estimada
  ↓
EnvironmentalIndices.sensacion_termica()
  ↓
bus_expander._publish_confort_avanzado()
  ↓
BUS: "utci" + "sensacion_termica" + 15 subfactores
  ↓
UI/Tablet + Endpoints REST + Históricos
```

### **WBGT: BLOQUEADO**
```
Sensores
  ↓
core/indices/environmental_indices.py::indice_wbgt() ← EXISTE
  ↓
??? (No se llama desde ningún lado) ← PROBLEMA
  ↓
BUS: VACÍO (nunca publicado)
  ↓
UI/Tablet/Endpoints: NO DISPONIBLE ← CIEGO
```

---

## 🚨 DIAGNÓSTICO FINAL

### **UTCI: Operativo**
- ✅ Código: Sí
- ✅ Publicación: Sí  
- ✅ Visualización: Sí
- ✅ Duelos: Sí
- ✅ **Conclusión: FUNCIONANDO NORMALMENTE**

### **WBGT: Semi-Funcional**
- ✅ Código: Sí
- ✅ Registro: Sí (NUEVO)
- ❌ Publicación: No
- ❌ Visualización: No
- ❌ Duelos: Sí pero sin datos
- ⚠️ **Conclusión: REGISTRADA PERO DESCONECTADA DEL BUS**

### **UTCI v2: Semi-Funcional**
- ✅ Código: Sí
- ✅ Uso interno: Sí (si extremos)
- ✅ Registro: Sí (NUEVO)
- ⚠️ **Conclusión: USADA INTERNAMENTE EN v1, NO COMO OPCIÓN INDEPENDIENTE**

---

## 📋 ACCIONES RECOMENDADAS

**Prioritarias:**
1. Habilitar publicación de WBGT en BUS desde `sensacion_termica()` o crear endpoint separado
2. Crear UI para mostrar WBGT (ocupacional, alertas OSHA)
3. Documentar cuándo se elige v2 vs v1 en UTCI (mostrar en "motor")

**Secundarias:**
4. Considerar exponer UTCI v2 como opción independiente en Guardian (no solo interna)
5. Mejorar WBGT con feedback de datos reales (validación vs sensaciones reportadas)
6. Crear dashboard de "Seguridad Térmica" para alertas ocupacionales

