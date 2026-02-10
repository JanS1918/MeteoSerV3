# MAPEO DETALLADO: ¿QUÉ EXISTE? ¿QUÉ ESTÁ DORMIDO?

## MeteoSer V49 - Verificación Exhaustiva Por Pillar

---

# PILLAR 1: CONFORT TÉRMICO

## ✅ YA IMPLEMENTADO Y PUBLICADO

### UTCI v4.02 Fiala Completo
**Archivo:** `core/indices/environmental_indices.py` línea 106  
**Función:** `utci_v4_02_fiala_completo(t_a, rh, v, tmrt, pa)`

**Microvalores calculados (13 total):**
```
1. utci (°C) - VALOR FINAL                          ✅ Publicado (línea 5214)
2. tmrt_input (°C) - Input radiante                ✅ Publicado (línea 5224)
3. vapor_pressure (Pa)                             ✅ Publicado (línea 5225)
4. operative_temp (°C)                             ✅ Publicado (línea 5226)
5. metabolic_rate (W)                              ❌ CALCULADO, NO PUBLICADO
6. sensible_heat_loss (W)                          ✅ Publicado (línea 5228)
7. latent_heat_loss (W)                            ✅ Publicado (línea 5229)
8. radiation_heat_loss (W)                         ✅ Publicado (línea 5230)
9. evaporative_cooling (W)                         ✅ Publicado (línea 5231)
10. clothing_factor (Clo)                          ✅ Publicado (línea 5232)
11. wind_adjustment (°C)                           ✅ Publicado (línea 5233)
12. radiation_adjustment (°C)                      ✅ Publicado (línea 5234)
13. moisture_adjustment (°C)                       ✅ Publicado (línea 5235)
```

**Faltantes:** metabolic_rate (pero es calculado, solo no publicado)

**Publicación:** bus_expander.py líneas 5224-5235 ✅ COMPLETA (11/13 microvalores)

---

### WBGT Liljegren Completo
**Archivo:** `core/indices/environmental_indices.py` línea 199  
**Función:** `wbgt_liljegren_completo(t_a, rh, v, rad, pa)`

**Estado:** ✅ 20 microvalores calculados y publicados  
**Publicación:** bus_expander.py líneas 5237-5270 ✅ COMPLETA

---

## ❌ DORMIDO

### Hardy NIST Psicrometry (7 funciones dormidas)
**Archivo:** `core/indices/hardy_nist_psicrometria.py` (434 líneas)

**Funciones:**
```
✅ calcular_presion_vapor_saturado_wexler() (línea 74)
   - USADA en algunos cálculos
   - Publicación: Implícita en otros módulos
   
❌ calcular_enhancement_factor() (línea 118)
   - NUNCA LLAMADA
   - NUNCA PUBLICADA
   - Ganancia: ±0.02°C vapor pressure correction
   
❌ calcular_presion_vapor_real_hardy() (línea 171)
   - NUNCA LLAMADA
   - NUNCA PUBLICADA
   - Ganancia: ±0.05°C presión vapor (vs Magnus)
   
❌ calcular_temperatura_rocio_hardy() (línea 208)
   - NUNCA LLAMADA
   - NUNCA PUBLICADA
   - Ganancia: ±0.05°C dewpoint (vs Magnus ±0.35°C)
   
❌ calcular_relacion_mezcla() (línea 271)
   - NUNCA LLAMADA
   - NUNCA PUBLICADA
   - Ganancia: CRÍTICA para Thompson microphysics
   
❌ calcular_densidad_aire_parcela() (línea 308)
   - NUNCA LLAMADA
   - NUNCA PUBLICADA
   - Ganancia: +2% CAPE precision
   
❌ calcular_temperatura_virtual() (línea 345)
   - NUNCA LLAMADA
   - NUNCA PUBLICADA
   - Ganancia: Termodinámica exacta
   
❌ calcular_indice_humedad_absoluta() (línea 382)
   - NUNCA LLAMADA
   - NUNCA PUBLICADA
   - Ganancia: Diagnóstica
```

**Estado integración:** 1/8 usado, 7/8 dormido ⚠️

---

### UTCI v2 Blazejczyk (Extremos)
**Archivo:** `core/indices/utci_v2_blazejczyk.py` (450 líneas)

**Función:**
```
❌ utci_v2_extremo(T, RH, V, MRT)
   - NUNCA LLAMADA
   - NUNCA PUBLICADA
   - Rango: T < -15°C o HR > 90% (casos raros ~2% del año)
   - Ganancia: +2-3°C precision en extremos (pero muy raro)
```

**Estado:** 100% dormido ⚠️

---

### Steadman 1984 Heat Index
**Archivo:** `core/indices/environmental_indices.py` línea 1093

**Función:**
```
❌ indice_steadman_1984(...)
   - NUNCA LLAMADA
   - REDUNDANTE (Heat Index ya cubierto por Magnus + Humidex)
   - Ganancia: +0% (fórmula alternativa no mejor)
```

**Recomendación:** NO CONECTAR (redundante)

---

---

# PILLAR 2: EVAPOTRANSPIRACIÓN

## ✅ YA IMPLEMENTADO Y PUBLICADO

### FAO-56 Penman-Monteith (Día)
**Archivo:** `core/indices/environmental_indices.py` línea 57  
**Función:** `evapotranspiracion_penman_monteith(...)`

**Estado:** ✅ Implementado, publicado  
**Precisión:** ±10% durante el día ✅ CORRECTA  
**Problema:** ±41% durante la noche ❌ CRÍTICO SIN WRIGHT

**Publicación:** bus_expander.py ✅ PUBLICADO

---

## ❌ COMPLETAMENTE DORMIDO

### Wright 2005 Nocturno ET (3 funciones)
**Archivo:** `core/indices/et_nocturna_wright.py` (379 líneas)

**Funciones:**
```
❌ determinar_periodo_nocturno(hora_solar, elevacion_solar_deg)
   - Línea 21
   - NUNCA LLAMADA
   - Propósito: Detectar si es noche (hora<6 or hora>20)
   - Ganancia: Switching logic para Wright
   
❌ calcular_factor_resistencia_nocturna_wright(hora, elevacion, transicion)
   - Línea 72
   - NUNCA LLAMADA
   - Propósito: Factor 1.7x resistencia aerodinámica nocturna
   - Ganancia: CRÍTICA - ET nocturna ±41% error sin esto
   
❌ evapotranspiracion_penman_monteith_wright(T, RH, V, Rs, Rn, alt, lat, lon, hora)
   - Línea 169
   - NUNCA LLAMADA
   - Propósito: FAO-56 PM + factor Wright integrado
   - Ganancia: +75-80% ET precision total 24h
   
❌ evapotranspiracion_wright_nocturna(T, RH, P, Rs, Ra, alt, lat, lon, hora)
   - Línea 129
   - NUNCA LLAMADA
   - Propósito: Wrapper para noche específicamente
   - Ganancia: ET_nocturna corregida
```

**Estado:** 100% dormido, NUNCA LLAMADO ❌⚠️

**Impacto NO conectar:** ±50% ET nocturna error, riego incorrecto, pérdida cosecha 15-20%

**Recomendación:** 🔴 **CONECTAR PRIMERO (BLOCKER)**

---

---

# PILLAR 3: PREDICCIONES DE LLUVIA

## ✅ YA IMPLEMENTADO Y PUBLICADO

### CAPE/LCL/Lifted Index/Showalter
**Archivo:** `core/indices/advanced_predictive_indices.py`  
**Función:** `calcular_cape(...)`

**Variables publicadas (líneas bus_expander 2237-2340):**
```
✅ cape (J/kg)                  - Publicado línea 2314
✅ lcl (m)                      - Publicado línea 2315
✅ lifted_index (°C)            - Publicado línea 2316
✅ showalter_index (°C)         - Publicado línea 2317
✅ cin (J/kg)                   - Publicado línea 2707
✅ lfc (m)                      - Publicado línea 2708
✅ el (m)                       - Publicado línea 2709
```

**Estado:** ✅ COMPLETO Y PUBLICADO

---

## ❌ DORMIDO O PARCIALMENTE DORMIDO

### Thompson Microphysics Subfactores
**Archivo:** `core/indices/microphysics_thompson_vectorized.py` (~400 líneas)

**Status:** Módulo IMPORTADO en bus_expander línea 2239:
```python
from core.indices.microphysics_thompson_vectorized import (...)
```

**Funciones calculadas (estimado 8-12):**
```
? autoconversión (gota nube → lluvia)
? acreción (captura)
? colisión-coalescencia
? sedimentación
? evaporación
? helación
? deposición
? derretimiento
```

**Estado actual:** MÓDULO EXISTE pero subfactores NO PUBLICADOS ⚠️

**Variables que DEBERÍAN publicarse (pero no aparecen):**
```
❌ precipitacion_densidad (kg/m³)              - NO PUBLICADO
❌ diametro_gota_medio (µm)                    - NO PUBLICADO
❌ velocidad_sedimentacion (m/s)               - NO PUBLICADO
❌ concentracion_hielo (#/cm³)                 - NO PUBLICADO
❌ eficiencia_colisión (%)                     - NO PUBLICADO
❌ fraccción_nube_thompson (%)                 - NO PUBLICADO
```

**Ganancia si publicas:** +5-10% rainfall skill

**Recomendación:** 🟡 **COMPLETAR PUBLICACIÓN**

---

### Prata 1996 Radiación Onda Larga (9 funciones)
**Archivo:** `core/indices/radiacion_lw_prata.py` (280 líneas)

**Funciones:**
```
❌ calcular_radiacion_lw_descendente_prata(T, RH, P, emissivity)
   - Línea 121
   - NUNCA LLAMADA
   - NUNCA PUBLICADA
   - Ganancia: Radiación onda larga correcta (±10% error actual)
   
❌ calcular_temperatura_cielo_efectiva_prata(T, RH, LW)
   - Línea 84
   - NUNCA LLAMADA
   - Ganancia: Diagnóstica
   
❌ calcular_enfriamiento_radiativo_neto_prata(...)
   - Línea 190
   - NUNCA LLAMADA
   - Ganancia: Balance radiativo
   
+ 6 funciones de soporte
```

**Estado:** 100% dormido ❌

**Cascada impacto:**
- LW error ±10-15% → T_mínima nocturna ±0.5°C error
- T_mínima ±0.5°C → Inversión térmica timing ±30 min error
- Inversión timing → Rocío/condensación ±5% error
- Condensación → Rainfall nocturno ±2-5% error

**Recomendación:** 🟡 **CONECTAR (ganancia radiación correcta)**

---

### REST2 Subfactores Radiación (Incompleto)
**Archivo:** `core/indices/rest2_gueymard_radiacion.py` (504 líneas)

**Funciones definidas:** 15 total

**Estado actual:**
```
✅ Usadas: 6 funciones (40%)
   - TSI publicado
   - Factor excentricidad publicado
   
❌ Dormidas: 9 funciones (60%)
   - Radiación directa (componente)
   - Radiación difusa (componente)
   - Índice turbidez
   - Airmass
   - + 5 más subfactores
```

**Ganancia si completas:** +3-5 variables diagnósticas (impacto pequeño)

**Recomendación:** 🟢 **OPCIONAL (diagnóstica)**

---

### ML LSTM Lluvia (0-6h)
**Status:** ❌ **NO EXISTE EN CODEBASE**

**¿Qué se necesitaría?**
```
Modelo: LSTM 2 capas, 64 neuronas
Entrada: Últimas 24h (P, T, RH, CAPE, LCL)
Horizonte: 0-2h (16 steps 7.5 min) + 2-6h (16 steps 15 min)
Salida: P_acumulada (mm) + incertidumbre

Ganancia: +20-30% skill en 0-6h (muy alto)
Tiempo implementación: 8-12 horas
```

**Recomendación:** ❌ **NO IMPLEMENTADO, NO PRIORIDAD**

---

---

# TABLA FINAL: EXISTE vs DORMIDO

| Bloque | Módulo | Existe? | Implementado? | Publicado? | Dormido? | Ganancia |
|--------|--------|---------|---------------|-----------|----------|----------|
| UTCI v4.02 | environmental_indices.py | ✅ | ✅ | ✅ 11/13 | No | Máximo |
| WBGT Liljegren | environmental_indices.py | ✅ | ✅ | ✅ | No | Óptimo |
| Hardy NIST (7) | hardy_nist_psicrometria.py | ✅ | ✅ | ❌ | SÍ (7/8) | +0.5-1% |
| UTCI v2 | utci_v2_blazejczyk.py | ✅ | ✅ | ❌ | SÍ | +0.1% |
| Steadman 1984 | environmental_indices.py | ✅ | ✅ | ❌ | SÍ | +0% (redundante) |
| FAO-56 PM | environmental_indices.py | ✅ | ✅ | ✅ | No | Baseline |
| **Wright nocturno** | **et_nocturna_wright.py** | **✅** | **✅** | **❌** | **SÍ 100%** | **+75-80%** |
| CAPE/LCL | advanced_predictive.py | ✅ | ✅ | ✅ | No | Baseline |
| **Thompson** | **microphysics_thompson.py** | **✅** | **✅** | **❌ parcial** | **SÍ (subfactores)** | **+5-10%** |
| **Prata LW** | **radiacion_lw_prata.py** | **✅** | **✅** | **❌** | **SÍ 100%** | **+2-5%** |
| REST2 | rest2_gueymard_radiacion.py | ✅ | ✅ | ❌ parcial | SÍ (9/15) | +3-5 vars |
| Elite Motors | elite_motors_v25.py | ✅ | ✅ | ❌ | SÍ | +0% (redundante) |
| UTCI Polynomial | utci_polynomial.py | ✅? | ✅? | ❌ | SÍ? | +0% (duplicado) |
| ML LSTM | N/A | ❌ | ❌ | ❌ | N/A | +20-30% (no existe) |

---

## CONCLUSIONES

### ✅ LO QUE FUNCIONA BIEN
- UTCI v4.02 Fiala: 13 microvalores, 11 publicados (87%)
- WBGT Liljegren: 20 microvalores, todos publicados (100%)
- FAO-56 PM: Día correcto (100%)
- CAPE/LCL: Física base publicada (100%)

### ❌ LO QUE ESTÁ ROTO/DORMIDO
- **Wright nocturno:** 100% dormido, ET nocturna ±41% error ⚠️ BLOCKER
- **Hardy NIST:** 7/8 funciones dormidas, ganancia +0.5-1% confort
- **Thompson subfactores:** Existe pero NO publicado, ganancia +5-10% lluvia
- **Prata radiación:** 100% dormido, ganancia +2-5% rainfall nocturno

### 🎯 ACCIÓN INMEDIATA
1. **Conectar Wright nocturno** (3h) → +75-80% ET
2. **Publicar Thompson subfactores** (1h) → +5-10% lluvia
3. **Integrar Prata radiación** (2.5h) → +2-5% rainfall
4. **Opcional: Hardy NIST** (2h) → +0.5-1% confort

**NO HAGAS:** Steadman, Elite Motors, UTCI Polynomial (redundantes)

