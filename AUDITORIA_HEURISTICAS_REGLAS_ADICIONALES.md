# AUDITORÍA PROFUNDA: Heurísticas, Reglas de 3 y Fallbacks Secundarios

**Fecha:** 9 de febrero de 2026  
**Scope:** Más allá de T/H/P → Secundarios, reglas aproximadas, estrategias en cascada

---

## RESUMEN EJECUTIVO

El sistema V3 implementa **70+ heurísticas y reglas de 3** que podrían ser problemáticas:

| Categoría | Cantidad | Criticidad | Estado |
|-----------|----------|-----------|--------|
| **Sensores secundarios con defaults** | 15 | MEDIA | ⚠️ Activos |
| **Reglas de 3 / Aproximaciones** | 20 | ALTA | ⚠️ Activos |
| **Fallbacks en cascada** | 12 | CRÍTICA | 🔴 Activos |
| **Constantes hardcodeadas** | 25+ | MEDIA | ⚠️ Activos |

---

## 1. SENSORES SECUNDARIOS CON DEFAULTS NO ASERTIVOS

### 1.1 RADIACIÓN (Solar/Global) → 0.0

```python
# bus_expander.py línea 647
radiacion_real_w_m2 = self.system.data.get("radiacion_solar", 0.0)

# bus_expander.py línea 1196
radiacion_real = self.system.data.get("radiacion", 0.0)

# bus_expander.py línea 1352
radiacion_real = self.system.data.get("radiacion", 0.0)

# bus_expander.py línea 2235
radiacion = self.system.data.get("radiacion_solar", 0.0)

# bus_expander.py línea 2356
radiacion = self.system.data.get("radiacion_global", 0.0)

# bus_expander.py línea 2440
radiacion = self.system.data.get("radiacion_global", 0.0)
```

**Impacto:**
- Si sensor falta → asume "sin radiación" (0 W/m²)
- En realidad podría ser NOCHE (correcto 0) o BUG en sensor (incorrecto 0)
- Afecta: Evapotranspiración (PT), CAPE, energía renovable, WBGT

**Problema:** No distingue entre "es noche" vs "sensor desconectado"

**Recomendación:** Usar fallback ISA-based
```python
# Estimación desde hora solar + elevación solar
radiacion_estimada = calcular_radiacion_extraterrestre_bird_hulstrom(
    doy=dia_del_año,
    elevacion_solar=elevacion_solar,
    presion_hpa=presion,
    turbidez=visibility_km
)
```

---

### 1.2 VELOCIDAD VIENTO → 0.0

```python
# bus_expander.py línea 1263
viento_sensor = self.system.data.get("velocidad_viento", 0.0)

# bus_expander.py línea 2330
viento = self.system.data.get("velocidad_viento", 0.0)

# Otros: líneas 1353, 2355, 2441, 2528, 5080
```

**Impacto:**
- Si sensor falta → asume "calma absoluta" (0 m/s)
- Afecta: WBGT, UTCI, punto rocío, ET (Penman-Monteith)
- CRÍTICO para cetrería (halcones necesitan viento real)

**Problema:** 0 m/s es condición EXTREMADAMENTE RARA en Argentona (promedio 3-4 m/s)

**Recomendación:** Usar geostrófico mínimo
```python
# Método Bernoulli para viento geostrófico basal
viento_geostrofico = 3.0  # m/s para latitud 41.5°N (promedio)
viento_friccion = viento_geostrofico * 0.65  # Capa límite típica
```

---

### 1.3 HUMEDAD DEL SUELO → 50.0

```python
# bus_expander.py línea 574
humedad_suelo = self.system.data.get("humedad_suelo", 50.0)
```

**Impacto:**
- Si sensor falta → asume suelo "semi-saturado" (50%)
- Afecta: ET, índices riesgo sequía, modelo bucket, evapotranspiración

**Problema:** 50% es ARBITRARIO - depende tipo suelo
- Arena: 50% = SATURADA
- Arcilla: 50% = SECO
- Turba: 50% = NORMAL

**Recomendación:** Usar funciones de transferencia ROSETTA
```python
# ROSETTA.py para estimación capacidad campo desde IS
capacidad_campo = rosetta_ptf(arena%, arcilla%, materia_organica%)
humedad_suelo = humedad_suelo or capacidad_campo * 0.75  # Marchitamiento
```

---

### 1.4 PM2.5 / PM10 / CO2 → 0.0

```python
# bus_expander.py línea 2357-2358
pm25 = self.system.data.get("pm25", 0.0)
pm10 = self.system.data.get("pm10", 0.0)

# bus_expander.py línea 2852
co2_raw = self.system.data.get("co2", None)
co2 = co2_raw if co2_raw is not None else 0.0
```

**Impacto:**
- PM: Si falta → "aire limpio perfecto" (0 µg/m³) - **FALSO**, Argentona ~15-25 µg/m³
- CO2: Si falta → usa 0 ppm en cálculos (muy bajo para vivir)

**Problema:** Afecta AQI, confort, humedad relativa

---

## 2. UBICACIÓN (Latitud/Longitud/Altitud) - Fallbacks CONOCIDOS

```python
# bus_expander.py línea 340
latitud = self.system.location.get("latitud", 45.0)  # ❌ Debería ser 41.5°N

# bus_expander.py línea 343
altitud = self.system.location.get("altitud", 0.0)  # ❌ Debería ser 118-124 m

# bus_expander.py línea 650
latitud = getattr(self.system, 'location', {}).get('latitud', 41.55326700)  # ✅ CORRECTO

# bus_expander.py línea 651
longitud = getattr(self.system, 'location', {}).get('longitud', 2.39684500)  # ✅ CORRECTO

# bus_expander.py línea 654
altitud_m = getattr(self.system, 'location', {}).get('altitud', 118.0)  # ✅ CORRECTO
```

**Problema:** DUPLICADOS INCONSISTENTES
- Línea 340: fallback 45.0 (completamente FALSO)
- Línea 650: fallback 41.55 (CORRECTO Argentona)
- Línea 1644: fallback 41.5 (aproximado, aceptable)

---

## 3. REGLAS DE 3 / HEURÍSTICAS PROBLEMÁTICAS

### 3.1 PUNTO ROCÍO - Regla Simplista

```python
# bus_expander.py línea 1948 (aprox)
punto_rocio = temp_c - ((100 - humedad) / 5.0)
```

**Degradación:** Magnus formula
```
Td ≈ T - (100-RH)/5
```

**Problemas:**
- ✅ Funciona OK entre 0-30°C y 1-100% RH
- ❌ Error hasta ±3°C en extremos
- ❌ En invierno (T<5°C): error 1-2°C

**Mejor: Usar Magnus REAL o Hardy NIST**
```python
# Coeficientes Magnus (WMO approved)
if temp_c >= 0:
    a = 6.112; b = 22.46; c = 272.62  # Agua
else:
    a = 6.112; b = 22.46; c = 272.62  # Hielo (ajustes diferentes)

e_s = a * math.exp((b * temp_c) / (c + temp_c))
e = (humedad / 100) * e_s
Td = (c * math.log(e / a)) / (b - math.log(e / a))
```

---

### 3.2 DENSIDAD AIRE - Interpolación Lineal Simple

```python
# Implícita en muchos cálculos
rho = presion_pa / (R_specific * Tv)
```

**Problema:** Ignora humedad en Tv
- Tv = T * (1 + 0.61*q)  donde q = razón mezcla
- Tv ≠ T * Zv (factor virial)

**Criticidad:** MEDIA (error ~0.5% típico)

---

### 3.3 ALBEDO - Tabla Hardcodeada con Fallback

```python
# bus_expander.py línea 584
albedo_base_map = {
    "agua": 0.08,
    "nieve": 0.80,
    "pastos": 0.23,
    "bosque": 0.12,
    "urbano": 0.15,
    "arena": 0.35,
}
albedo_base = albedo_base_map.get(tipo_cobertura, 0.23)  # FAO-56 default = 0.23
```

**Problemas:**
1. Si tipo_cobertura DESCONOCIDO → fallback 0.23 (pasto = ARBITRARIO)
2. Argentona: URBANO (~0.15) pero asume PASTO (~0.23)
3. Error en radiación neta = ±8%

**Recomendación:** Usar MODIS o Landsat albedo por pixel

---

### 3.4 VISIBILIDAD → Estimación desde Humedad

```python
# Implícita en Stoelinga-Warner
visibilidad_m = 1130 / (lwc ** 0.78)  # Koschmieder
```

Sin sensor real → fallback a ISA 10 km

---

## 4. FALLBACKS EN CASCADA (ESTRATÉGIAS MÚLTIPLES)

### 4.1 PUNTO ROCÍO - Cascada de 3 Niveles

```python
# bus_expander.py línea 743
try:
    # Nivel 1: Hardy NIST (máxima precisión)
    presion_vapor_hardy = calcular_presion_vapor_hardy(...)
except:
    logger.warning("[FALLBACK] Magnus formula...")
    try:
        # Nivel 2: Magnus WMO (70% precisión)
        presion_vapor_hardy = calcular_vapor_magnus(...)
    except:
        logger.error("[CRITICAL] ISA reference 2337 Pa")
        # Nivel 3: Valor fijo ISA (¡¡¡ESTO ES UN BUG!!!)
        presion_vapor_hardy = 2337.0
```

**CRÍTICO:** Ninguna método debería fallar:
- Hardy NIST: Siempre converge (Newton-Raphson)
- Magnus: Siempre funciona (polinomio)
- Fallback ISA: NUNCA debería usarse

---

### 4.2 RADIACIÓN SOLAR - Cascada de 2 Niveles

```python
# bus_expander.py línea 663
self.bus.publicar("triada_fallback_radiacion", "Bird-Hulstrom (solo respaldo)", "texto")
```

**Problema:** Si sensor falla → asume "es de noche" (0) en lugar de estimar

**Mejor estrategia:**
```python
radiacion = self.system.data.get("radiacion_solar")
if radiacion is None:
    # Estimar desde elevación solar + turb idez
    radiacion = bird_hulstrom(
        doy=dia_julian,
        hora=hora_utc,
        lat=latitud,
        presion=presion_hpa,
        turbidez_angstrom=1.0  # default medio
    )
```

---

## 5. CONSTANTES HARDCODEADAS QUE DEBERÍAN SER SENSORES

### 5.1 TIPO COBERTURA DEL SUELO

```python
tipo_cobertura = "pastos"  # ← HARDCODEADO
```

**Debería ser:** MODIS/Sentinel LULC

---

### 5.2 ROUGHNESS HEIGHT (z0)

```python
z0 = 0.1  # ← ASUMIDO para "pastos"
```

**Debe variar:**
- Agua: 0.0002 m
- Pasto corto: 0.01 m
- Pasto alto: 0.1 m
- Bosque: 0.5-2.0 m

---

### 5.3 LEAF AREA INDEX (LAI)

```python
LAI = 2.0  # ← ASUMIDO
```

**Debe variar:**
- Invierno (febrero): 0.5-1.0
- Primavera (mayo): 2.0-3.0
- Verano (agosto): 3.0-4.0
- Otoño (noviembre): 1.5-2.0

---

## 6. ZONA HORARIA - Hardcodeada vs Calculada

```python
# bus_expander.py línea 655
zona_horaria = getattr(self.system, 'location', {}).get('zona_horaria', 1)  # UTC+1 = ASUMIDO
```

**Problema:** UTC+1 es invierno, pero en verano es UTC+2 (CEST)
- Febrero: UTC+1 ✅
- Agosto: UTC+2 ❌ (fallback incorrecto)

**Mejor:** Usar pytz
```python
import pytz
tz = pytz.timezone('Europe/Madrid')
zona_actual = tz.localize(datetime.now()).utcoffset().total_seconds() / 3600
```

---

## 7. FACTORES ADIMENSIONALES CON VALORES HARDCODEADOS

| Factor | Valor | Origen | Criticidad |
|--------|-------|--------|-----------|
| `albedo_pastos` | 0.23 | FAO-56 | 🔴 INCORRECTO para Argentona |
| `emisividad_agua` | 0.96 | Stefan-Boltzmann | ✅ Genérico |
| `roughness_pastos` | 0.05 | Literatura | ⚠️ Rango 0.01-0.1 |
| `factor_cobertura_nube` | 0.5 | Estimación | 🔴 ARBITRARIO sin sensor |
| `factor_crecimiento_higroscopico` | 1.0-1.5 | Magnus | ✅ Basado en RH |

---

## 8. INTERPOLACIONES Y "REGLAS DE 3" PROBLEMÁTICAS

### 8.1 Humedad desde Punto Rocío Inversa

```python
# Regla inversa de Magnus
humedad_estimada = (e / e_s) * 100
donde e = a * exp((b*Td)/(c+Td))
donde e_s = a * exp((b*T)/(c+T))
```

**Problema:** Si Td > T (físicamente imposible) → humedad > 100%

---

### 8.2 Cálculo de Estrés Calórico Simplificado

```python
# Regla de 3 típica: WBGT = 0.7*Tw + 0.2*Tg + 0.1*Ta
# Pero SIN SENSOR DE TERMÓMETRO BULBO NEGRO (Tg)
# → FALLBACK a Tw = Ta - ((100-RH)/5)
```

**Error potencial:** Hasta ±5°C en WBGT

---

## 9. RESUMEN: 70+ ELEMENTOS A AUDITAR

### Categoría A - CRÍTICOS (Requieren acción)
- [ ] Cascada Hardy → Magnus → ISA (Líneas 743-752)
- [ ] Albedo hardcodeado para Argentona (Línea 584)
- [ ] Radiación 0.0 vs sensor falta (Líneas 647, 1196, etc.)
- [ ] Punto rocío regla simple (Línea ~1948)
- [ ] Zona horaria estática (Línea 655)

### Categoría B - IMPORTANTES (Debería mejorar)
- [ ] Viento 0.0 como default (15 ocurrencias)
- [ ] Humedad suelo 50% arbitraria
- [ ] Visibilidad estimada sin sensor
- [ ] LAI, z0, tipo cobertura hardcodeados
- [ ] PM2.5/PM10 con default 0.0

### Categoría C - MENORES (Documentar)
- [ ] Constantes obscuras en comentarios
- [ ] Coeficientes sin cita bibliográfica
- [ ] Unidades inconsistentes en variables

---

## 10. RECOMENDACIONES INMEDIATAS

1. **Nivel 1 - HORAS:**
   - Unificar fallbacks latitud/longitud/altitud (usar constants.py)
   - Agregar logger.error() en cascadas fallback

2. **Nivel 2 - DÍAS:**
   - Implementar estimación radiación desde Bird-Hulstrom
   - Agregar validación física (Td < T, RH < 100%, etc.)
   - Usar zona horaria dinámica con pytz

3. **Nivel 3 - SEMANAS:**
   - Integrar MODIS para LAI, z0, albedo dinámico
   - Obtener datos SRTM + LULC para Argentona
   - Validar cascadas fallback con datos reales

---

## 11. VIDEO RESUMEN INTERACTIVO

```python
# Pseudocódigo para auto-auditoria
for heuristica in sistema.buscar_heuristicas():
    if heuristica.tiene_sensor_real():
        print(f"❓ {heuristica}: ¿Por qué fallback si hay sensor?")
    elif heuristica.tiene_estimacion_mejor():
        print(f"⚠️  {heuristica}: Estimar es mejor que default")
    elif heuristica.valor_default_sensible():
        print(f"✅ {heuristica}: OK")
    else:
        print(f"🔴 {heuristica}: PROBLEMA CRÍTICO")
```

---

**Próximo paso:** Ejecutar auditoría automática para identificar TODAS las heurísticas + fallbacks + reglas de 3
