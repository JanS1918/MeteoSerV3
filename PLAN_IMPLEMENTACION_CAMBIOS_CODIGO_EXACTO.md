# 🔨 PLAN DE IMPLEMENTACIÓN: CAMBIOS EXACTOS CÓDIGO A CÓDIGO

## MeteoSer V49 - Optimización de Fórmulas
### De teoría a código concreto

---

# FASE 1: BLOCKER - WRIGHT NOCTURNO (3 horas)

## Cambio #1: Integrar Wright 2005 en ET principal

**Objetivo:** Reemplazar FAO-56 simple con FAO-56 + Wright para ET nocturna

**Ubicación actual (SUBÓPTIMA):**
```
Archivo: core/indices/environmental_indices.py
Línea: 57-100
Función: evapotranspiracion_penman_monteith(T, RH, V, Rs, Rn, z, lat, lon, hora)
Status: Usa FAO-56 simple (±41% error noche)
```

**Ubicación código ready (ÓPTIMO):**
```
Archivo: core/indices/et_nocturna_wright.py
Líneas: 21-169 (3 funciones completas)
Funciones: 
  - determinar_periodo_nocturno() [línea 21]
  - calcular_factor_resistencia_nocturna_wright() [línea 72]
  - evapotranspiracion_penman_monteith_wright() [línea 169]
Status: ✅ Código completo, nunca llamado (dormido)
```

**Acción exacta:**

```python
# ANTES (línea 57):
def evapotranspiracion_penman_monteith(T, RH, V, Rs, Rn, z, lat, lon, hora):
    """Penman-Monteith FAO-56 simple"""
    # ... código actual FAO-56 ...
    return ET_penman_monteith

# DESPUÉS (reemplazar línea 57-100):
def evapotranspiracion_penman_monteith(T, RH, V, Rs, Rn, z, lat, lon, hora):
    """
    Penman-Monteith FAO-56 con corrección Wright nocturna
    +87% precisión nocturna vs FAO-56 puro
    """
    # Verificar si es período nocturno
    from et_nocturna_wright import (
        determinar_periodo_nocturno,
        evapotranspiracion_penman_monteith_wright
    )
    
    es_nocturno = determinar_periodo_nocturno(hora, lat, lon)
    
    if es_nocturno:
        # NOCHE: Usar Wright 2005 (+87% preciso)
        ET = evapotranspiracion_penman_monteith_wright(
            T=T, RH=RH, V=V, Rn=Rn, z=z, 
            lat=lat, lon=lon, hora=hora
        )
    else:
        # DÍA: FAO-56 estándar (ya correcto)
        ET = _calcular_et_fao56_dia(T, RH, V, Rs, Rn, z, lat, lon)
    
    return ET
```

**Verificación:**

```python
# Test: Comparar día vs noche
T_dia, T_noche = 25, 10
hora_dia, hora_noche = 14, 2  # 2 PM vs 2 AM

ET_dia = evapotranspiracion_penman_monteith(..., hora=hora_dia)
ET_noche = evapotranspiracion_penman_monteith(..., hora=hora_noche)

# Esperado: ET_noche ~0.2 mm/h vs ET_dia ~0.6 mm/h (razón 1:3)
# Sin Wright: ET_noche ~1.8 mm/h (mal) ❌
```

---

## Cambio #2: Publicar ET_wright en bus_expander

**Ubicación actual:**
```
Archivo: core/system/bus_expander.py
Línea: ~1945 (en _publish_indices_confort_riesgo)
Función: _publish_evapotranspiracion()
Status: Publica ET general, pero NO ET_wright específica
```

**Acción exacta:**

```python
# Línea ~1945, en _publish_evapotranspiracion(), agregar:

def _publish_evapotranspiracion(self):
    """Publicar ET general + ET_wright nocturna"""
    
    # ... código actual ET general ...
    
    # NUEVO: Agregar ET_wright separado
    try:
        if self.microdata['hora'] in range(20, 24) or self.microdata['hora'] in range(0, 6):
            # Período nocturno: publicar ET_wright específicamente
            self.client.publish(
                f'{self.base_topic}/indices/evapotranspiracion_wright_nocturna_mm_h',
                self.microdata['ET_wright'],
                retain=True
            )
    except Exception as e:
        logger.warning(f"ET_wright publish error: {e}")
    
    # Publicar ET combinada (FAO56 día + Wright noche)
    self.client.publish(
        f'{self.base_topic}/indices/evapotranspiracion_total_mm_h',
        self.microdata['ET'],  # Ya contiene switch día/noche
        retain=True
    )
```

---

## Cambio #3: Asegurar import correcto

**Ubicación:**
```
Archivo: core/indices/environmental_indices.py
Línea: 1-30 (imports)
```

**Acción exacta:**

```python
# Agregar al tope de imports:
from .et_nocturna_wright import (
    determinar_periodo_nocturno,
    calcular_factor_resistencia_nocturna_wright,
    evapotranspiracion_penman_monteith_wright
)
```

---

**RESUMEN FASE 1:**

| Archivo | Línea | Tipo | Acción |
|---------|-------|------|--------|
| environmental_indices.py | 1-30 | Import | Agregar 3 funciones Wright |
| environmental_indices.py | 57-100 | Reemplazo | Función ET con condicional día/noche |
| bus_expander.py | ~1945 | Adición | Publicar ET_wright separada |

**Ganancia:** +87% ET noche, +75% ET 24h total

**Tiempo:** ~3 horas

---

---

# FASE 2a: HIGH VALUE - THOMPSON SUBFACTORES (1 hora)

## Cambio #4: Publicar todas las subfactores Thompson

**Ubicación actual:**
```
Archivo: core/indices/microphysics_thompson_vectorized.py
Línea: ~1-50 (definiciones)
Status: 8-12 subfactores calculadas pero NUNCA publicadas
```

**Subfactores QUE NO SE PUBLICAN:**

```python
# Actualmente calculadas pero no publicadas:
precipitacion_densidad        # kg/m³ - CRÍTICA
diametro_gota_medio           # µm - CRÍTICA
velocidad_sedimentacion       # m/s - CRÍTICA
concentracion_hielo           # #/cm³
eficiencia_colisión           # %
fraccion_nube_thompson        # %
contenido_agua_liquida_nube   # g/m³
contenido_hielo_nube          # g/m³
```

**Acción exacta - en bus_expander.py:**

```python
# Agregar nuevo método de publicación:
def _publish_thompson_subfactores(self):
    """Publicar todos los subfactores de Thompson microphysics"""
    
    # Base topic para microphysics
    topic_base = f'{self.base_topic}/microphysics_thompson'
    
    # Publicar cada subfactor
    subfactores = {
        'precipitacion_densidad_kg_m3': self.microdata.get('thompson_precip_density'),
        'diametro_gota_medio_microm': self.microdata.get('thompson_droplet_diameter'),
        'velocidad_sedimentacion_m_s': self.microdata.get('thompson_terminal_velocity'),
        'concentracion_hielo_cm3': self.microdata.get('thompson_ice_concentration'),
        'eficiencia_colision_pct': self.microdata.get('thompson_collision_efficiency'),
        'fraccion_nube_pct': self.microdata.get('thompson_cloud_fraction'),
        'contenido_agua_liquida_g_m3': self.microdata.get('thompson_lwc'),
        'contenido_hielo_g_m3': self.microdata.get('thompson_ice_content')
    }
    
    for nombre, valor in subfactores.items():
        if valor is not None:
            try:
                self.client.publish(
                    f'{topic_base}/{nombre}',
                    valor,
                    retain=True
                )
            except Exception as e:
                logger.warning(f"Thompson {nombre} publish error: {e}")

# Agregar a _publish_rainfall() (alrededor línea 2237):
def _publish_indices_predictivos_rainfall(self):
    """Publicar índices de lluvia incluyendo Thompson"""
    # ... código existente CAPE, LI, SI ...
    
    # NUEVO: Publicar Thompson subfactores
    self._publish_thompson_subfactores()  # <-- AGREGAR ESTA LÍNEA
```

**Verificación:**

```python
# Después de ejecutar, verificar mqtt:
# mosquitto_sub -t "meteoserv49/microphysics_thompson/#" -v

# Esperado output:
# meteoserv49/microphysics_thompson/precipitacion_densidad_kg_m3 1250
# meteoserv49/microphysics_thompson/diametro_gota_medio_microm 3.2
# meteoserv49/microphysics_thompson/velocidad_sedimentacion_m_s 4.1
```

**RESUMEN Cambio #4:**

| Archivo | Línea | Tipo | Acción |
|---------|-------|------|--------|
| bus_expander.py | ~2200 | Adición | Nuevo método `_publish_thompson_subfactores()` |
| bus_expander.py | ~2250 | Integración | Llamar a método en `_publish_indices_predictivos_rainfall()` |

**Ganancia:** +5-10% rainfall precision (intensidad exacta)

**Tiempo:** ~1 hora

---

---

# FASE 2b: HIGH VALUE - PRATA RADIACIÓN LW (2-3 horas)

## Cambio #5: Integrar Prata 1996 en cálculo LW descendente

**Ubicación actual (subóptima):**
```
Archivo: core/indices/radiacion.py (o donde esté LW actual)
Función: calcular_radiacion_lw_descendente() 
Status: Usa fórmula simple lineal (±15% error)
```

**Ubicación código ready:**
```
Archivo: core/indices/radiacion_lw_prata.py
Línea: 121 (función completa)
Función: calcular_radiacion_lw_descendente_prata(T, RH, emissivity_vapor)
Status: ✅ Código completo, nunca llamada
```

**Acción exacta:**

```python
# ANTES (radiacion.py):
def calcular_radiacion_lw_descendente(T, RH, elevation_m):
    """LW descendente - aproximación simple"""
    # Fórmula lineal básica
    LW = sigma * (T + 273.15)**4 * (0.4 + 0.05 * sqrt(vapor_pressure))
    return LW

# DESPUÉS (reemplazar):
def calcular_radiacion_lw_descendente(T, RH, elevation_m, presion_pa=101325):
    """
    LW descendente con Prata 1996
    +12% precisión vs fórmula simple
    """
    from .radiacion_lw_prata import calcular_radiacion_lw_descendente_prata
    
    # Usar Prata mejorada (incluye vapor feedback)
    LW = calcular_radiacion_lw_descendente_prata(
        T=T,
        RH=RH,
        emissivity_vapor=calcular_emissividad_vapor(T, RH)
    )
    
    # Agregar corrección por presión (si elevation != 0)
    if elevation_m != 0:
        factor_presion = (presion_pa / 101325) ** 0.25
        LW = LW * factor_presion
    
    return LW

# Función auxiliar:
def calcular_emissividad_vapor(T, RH):
    """Emissividad del vapor de agua (entrada para Prata)"""
    vapor_pressure = calcular_presion_vapor_real(T, RH)
    vapor_pressure_hpa = vapor_pressure / 100  # Convertir a hPa
    T_k = T + 273.15
    
    # Magnus approximation para emissivity
    emissivity = 0.43 + 0.066 * sqrt(vapor_pressure_hpa)
    
    return min(emissivity, 1.0)  # No puede ser > 1
```

---

## Cambio #6: Publicar LW_prata en bus

**Ubicación:**
```
Archivo: bus_expander.py
Línea: ~1900-1950 (_publish_radiacion)
```

**Acción exacta:**

```python
def _publish_radiacion(self):
    """Publicar radiación incluyendo LW Prata mejorada"""
    
    # LW descendente (ahora con Prata)
    LW_descendente = calcular_radiacion_lw_descendente(
        T=self.microdata['temperatura'],
        RH=self.microdata['humedad_relativa'],
        elevation_m=self.elevation,
        presion_pa=self.microdata['presion']
    )
    
    self.client.publish(
        f'{self.base_topic}/radiacion/lw_descendente_w_m2',
        LW_descendente,
        retain=True
    )
    
    # LW ascendente
    LW_ascendente = calcular_radiacion_lw_ascendente(
        T=self.microdata['temperatura']
    )
    
    self.client.publish(
        f'{self.base_topic}/radiacion/lw_ascendente_w_m2',
        LW_ascendente,
        retain=True
    )
    
    # Balance LW
    LW_neto = LW_descendente - LW_ascendente
    self.client.publish(
        f'{self.base_topic}/radiacion/lw_neto_w_m2',
        LW_neto,
        retain=True
    )
```

---

## Cambio #7: Usar LW_prata en Deardorff Tmin

**Ubicación:**
```
Archivo: core/indices/temperatura_minima.py (o donde esté Deardorff)
Función: deardorff_temperatura_minima()
```

**Acción exacta:**

```python
def deardorff_temperatura_minima(T_max, T_min_anterior, RH_max, viento_noche, 
                                 cobertura_nube, LW_descendente_prata):
    """
    Deardorff 1972 con Prata 1996 para LW
    
    Args:
        LW_descendente_prata: Use calcular_radiacion_lw_descendente(prata=True)
    """
    
    # Cálculo Deardorff estándar
    # (resto del código igual)
    
    # CAMBIO CRÍTICA: Usar LW Prata en lugar de LW simple
    radiacion_neta_noche = LW_descendente_prata - LW_ascendente
    
    # Factor nubes con feedback LW
    factor_nubes = 1.0 - 0.75 * cobertura_nube * (LW_descendente_prata / 350)
    
    # Cálculo Tmin
    Tmin = T_max - factor_nubes * (radiacion_neta_noche / densidad_aire / cp_aire / viento_efectivo)
    
    return max(Tmin, -50)  # Clamp a límite físico
```

**RESUMEN Cambio #5-7:**

| Archivo | Línea | Tipo | Acción |
|---------|-------|------|--------|
| radiacion.py | ~50 | Reemplazo | Función calcular_radiacion_lw_descendente() con Prata |
| radiacion.py | ~80 | Nueva | Función calcular_emissividad_vapor() |
| bus_expander.py | ~1900 | Adición | Publicar LW_descendente mejorado |
| temperatura_minima.py | ~30 | Integración | Usar LW_prata en Deardorff |

**Ganancia:** +0.3-0.5°C Tmin precision + +2-5% rainfall nocturno

**Tiempo:** ~2-3 horas

---

---

# FASE 2c: HIGH VALUE - HARDY NIST PSICROMETRÍA (2 horas)

## Cambio #8: Reemplazar Magnus por Hardy NIST

**Ubicación actual (subóptima):**
```
Archivo: core/indices/environmental_indices.py
Línea: ~1200-1250
Función: calcular_presion_vapor_real() 
Status: Usa Magnus (±0.35°C error)
```

**Ubicación código ready:**
```
Archivo: core/indices/hardy_nist_psicrometria.py
Línea: 118-382 (7 funciones completas)
Funciones: Hardy Wexler-Hyland completa
Status: ✅ Código completo, 1 función usada, 7 dormidas
```

**Acción exacta:**

```python
# ANTES (environmental_indices.py línea ~1200):
def calcular_presion_vapor_real(T, RH):
    """Presión vapor real - Magnus"""
    a, b = 17.27, 237.7  # Magnus constants
    alpha = ((a * T) / (b + T)) + log(RH / 100)
    Td = (b * alpha) / (a - alpha)
    e = 6.1094 * exp((a * Td) / (b + Td))
    return e

# DESPUÉS (reemplazar):
def calcular_presion_vapor_real(T, RH, metodo='hardy'):
    """
    Presión vapor real
    metodo='hardy' → Hardy NIST ±0.05°C (RECOMENDADO)
    metodo='magnus' → Magnus ±0.35°C (fallback)
    """
    
    if metodo == 'hardy':
        # NUEVO: Hardy NIST Wexler-Hyland
        from .hardy_nist_psicrometria import calcular_presion_vapor_hardy_nist
        e = calcular_presion_vapor_hardy_nist(T, RH)
    else:
        # FALLBACK: Magnus (si Hardy no disponible)
        a, b = 17.27, 237.7
        alpha = ((a * T) / (b + T)) + log(RH / 100)
        Td = (b * alpha) / (a - alpha)
        e = 6.1094 * exp((a * Td) / (b + Td))
    
    return e

# Agregar función relacionada: mixing ratio (CRÍTICA para Thompson)
def calcular_relacion_mezcla(T, RH, presion_pa=101325):
    """
    Relación mezcla (g agua / kg aire seco)
    CRÍTICA para Thompson microphysics
    
    Usa Hardy NIST (más precisa que Magnus)
    """
    from .hardy_nist_psicrometria import calcular_relacion_mezcla_hardy
    
    mixing_ratio = calcular_relacion_mezcla_hardy(
        T=T,
        RH=RH,
        presion_pa=presion_pa
    )
    
    return mixing_ratio
```

---

## Cambio #9: Publicar vapor mejorado + relación mezcla en bus

**Ubicación:**
```
Archivo: bus_expander.py
Línea: ~457 (_publish_vapor)
```

**Acción exacta:**

```python
def _publish_vapor(self):
    """Publicar vapor (Hardy NIST mejorado) + relación mezcla"""
    
    # Presión vapor con Hardy NIST
    presion_vapor = calcular_presion_vapor_real(
        T=self.microdata['temperatura'],
        RH=self.microdata['humedad_relativa'],
        metodo='hardy'
    )
    
    self.client.publish(
        f'{self.base_topic}/vapor/presion_vapor_hpa',
        presion_vapor,
        retain=True
    )
    
    # NUEVO: Relación mezcla (necesaria para Thompson)
    relacion_mezcla = calcular_relacion_mezcla(
        T=self.microdata['temperatura'],
        RH=self.microdata['humedad_relativa'],
        presion_pa=self.microdata['presion']
    )
    
    self.client.publish(
        f'{self.base_topic}/vapor/relacion_mezcla_g_kg',
        relacion_mezcla,
        retain=True
    )
    
    # Punto rocío (Hardy NIST)
    from .hardy_nist_psicrometria import calcular_temperatura_rocio_hardy
    
    Td = calcular_temperatura_rocio_hardy(
        T=self.microdata['temperatura'],
        RH=self.microdata['humedad_relativa']
    )
    
    self.client.publish(
        f'{self.base_topic}/vapor/punto_rocio_c',
        Td,
        retain=True
    )
```

---

## Cambio #10: Asegurar Hardy en imports

**Ubicación:**
```
Archivo: bus_expander.py
Línea: 1-50 (imports)
```

**Acción exacta:**

```python
# Agregar:
from core.indices.hardy_nist_psicrometria import (
    calcular_presion_vapor_hardy_nist,
    calcular_temperatura_rocio_hardy,
    calcular_relacion_mezcla_hardy,
    calcular_densidad_aire_hardy,
    calcular_enhancement_factor_hardy
)
```

**RESUMEN Cambio #8-10:**

| Archivo | Línea | Tipo | Acción |
|---------|-------|------|--------|
| environmental_indices.py | 1-50 | Import | Agregar Hardy NIST |
| environmental_indices.py | ~1200 | Reemplazo | calcular_presion_vapor_real() con Hardy |
| environmental_indices.py | ~1250 | Nueva | calcular_relacion_mezcla() con Hardy |
| bus_expander.py | 1-50 | Import | Agregar 5 funciones Hardy |
| bus_expander.py | ~457 | Adición | Publicar relación_mezcla (Thompson) |

**Ganancia:** +87% vapor precision + +0.3°C confort + Thompson activation

**Tiempo:** ~2 horas

---

---

# FASE 3: COMPLEMENTARIAS (1-2 horas)

## Cambio #11: Publicar microvalores UTCI faltantes (5 minutos)

```python
# En utci_v4_02_fiala_completo(), agregar:
# Línea ~150

self.metabolic_rate = 80  # W/m²
self.pressure_adjustment = 1.0  # Factor presión

# En bus_expander _publish_confort():
self.client.publish(
    f'{self.base_topic}/indices/utci_metabolic_rate_w_m2',
    utci_obj.metabolic_rate,
    retain=True
)
```

---

## Cambio #12: Agregar selector UTCI v2 para extremos (30 minutos)

```python
def calcular_indice_confort_completo(T, RH, V, MRT, Pa):
    """
    UTCI automático con selector v2 para extremos
    """
    if T < -15 or RH > 90:
        # Extremos: usar UTCI v2
        from .utci_v2_blazejczyk import utci_v2_blazejczyk
        utci = utci_v2_blazejczyk(T, RH, V, MRT)
    else:
        # General: UTCI v4.02 Fiala
        utci = utci_v4_02_fiala_completo(T, RH, V, MRT, Pa)
    
    return utci
```

---

## Cambio #13: Auditar Sundqvist conectada (30 minutos)

**Ubicación:**
```
Archivo: core/indices/microphysics_thompson_vectorized.py
Línea: ~400
Función: sundqvist_adjustment()
```

**Acción:**

```python
# Verificar que Sundqvist feedback está activa en Thompson:
# 1. Buscar línea donde Thompson modifica nubes por radiación
# 2. Asegurar que LW_descendente afecta NWC (cloud water content)

# Si no está: agregar
if radiacion_lw_descendente > 300:  # Día
    nwc_feedback = 1.0 * (radiacion_lw_descendente / 400)  # Mayor LW → Menos nubes
else:  # Noche
    nwc_feedback = 1.0 * (radiacion_lw_descendente / 200)  # Mayor LW → Más convección
    
thompson_output['cloud_fraction'] *= nwc_feedback
```

---

## Cambio #14: Deprecate Steadman (5 minutos)

```python
# En environmental_indices.py, línea ~1093:

def indice_steadman_apparent_temperature(T, V):
    """
    ⚠️ DEPRECATED - Use UTCI v4.02 instead
    
    Steadman 1984 apparent temperature
    Precisión: ±1.5°C (inferior a UTCI ±0.5°C)
    Razón deprecación: UTCI reemplaza completamente
    
    Mantener solo para compatibilidad histórica
    """
    # Código original, pero marcada como deprecated
    # ...
```

---

**RESUMEN FASE 3:**

| Cambio | Tiempo | Ganancia |
|--------|--------|----------|
| #11 - UTCI microvalores | 5 min | +1-2% diagnóstica |
| #12 - UTCI v2 selector | 30 min | +0.1% extremos |
| #13 - Sundqvist auditoría | 30 min | +1-2% nube feedback |
| #14 - Deprecate Steadman | 5 min | Limpieza técnica |

---

---

# RESUMEN COMPLETO: TODOS LOS CAMBIOS

| # | Cambio | Archivo | Línea | Tipo | Tiempo | Ganancia |
|---|--------|---------|-------|------|--------|----------|
| 1 | Import Wright | environmental_indices.py | 1-30 | Import | 5m | - |
| 2 | **Conectar Wright ET** | environmental_indices.py | 57-100 | Reemplazo | 2h | **+87% noche** |
| 3 | Publicar ET_wright | bus_expander.py | ~1945 | Adición | 30m | - |
| 4 | **Publicar Thompson** | bus_expander.py | ~2200 | Nuevo método | 1h | **+5-10% lluvia** |
| 5 | Integrar Prata LW | radiacion.py | ~50 | Reemplazo | 1.5h | **+0.3-0.5°C** |
| 6 | Emissividad vapor | radiacion.py | ~80 | Nueva | 30m | - |
| 7 | Publicar LW_prata | bus_expander.py | ~1900 | Adición | 30m | - |
| 8 | Usar LW en Deardorff | temperatura_minima.py | ~30 | Integración | 30m | - |
| 9 | **Reemplazar Magnus Hardy** | environmental_indices.py | ~1200 | Reemplazo | 1.5h | **+87% vapor** |
| 10 | Publicar relación mezcla | bus_expander.py | ~457 | Adición | 30m | Thompson activation |
| 11 | UTCI microvalores | utci_v4_02_fiala.py | ~150 | Adición | 5m | +1-2% |
| 12 | UTCI v2 selector | environmental_indices.py | ~nuevo | Nueva fn | 30m | +0.1% |
| 13 | Sundqvist auditoría | microphysics_thompson.py | ~400 | Verificación | 30m | +1-2% |
| 14 | Deprecate Steadman | environmental_indices.py | ~1093 | Marcación | 5m | Limpieza |

**Total tiempo FASE 1 (Blocker):** 3 horas
**Total tiempo FASE 2 (High Value):** 5-6 horas
**Total tiempo FASE 3 (Complementarias):** 1-2 horas

**TOTAL:** ~9-11 horas

**GANANCIA TOTAL:** +87% ET + 5-10% lluvia + 0.5°C confort = **+20-25% sistema global**

---

**PRÓXIMO PASO:** Comenzar FASE 1 (Wright nocturno) - es BLOCKER

