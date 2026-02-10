# 🧾 AUDITORÍA COMPLETA — TODO LO QUE CALCULA METEOSER V49

**Fecha:** 5 de febrero de 2026  
**Objetivo:** Inventario técnico de *todo* lo que MeteoSer calcula, por familias, indicando fórmula, módulo y salida.

> **Nota clave**: Algunas salidas dependen de si el sensor existe o si el motor está cargado. Cuando una familia requiere hardware opcional o modelo ML cargado, se indica explícitamente.

---

## 0) MAPA MAESTRO (DÓNDE SE CALCULA TODO)

**Orquestador principal de salidas al bus:**  
- [core/system/bus_expander.py](core/system/bus_expander.py) → publica secciones 1–32 y auto‑descubrimiento de predicciones/virtuales/calibración.

**Motores principales de fórmulas físicas:**  
- [core/indices/environmental_indices.py](core/indices/environmental_indices.py)  
- [core/indices/rest2_gueymard_radiacion.py](core/indices/rest2_gueymard_radiacion.py)  
- [core/indices/et_nocturna_wright.py](core/indices/et_nocturna_wright.py)  
- [core/indices/hardy_nist_psicrometria.py](core/indices/hardy_nist_psicrometria.py)  
- [core/indices/omm_densidad_temperatura_virtual.py](core/indices/omm_densidad_temperatura_virtual.py)  
- [core/indices/utci_v2_blazejczyk.py](core/indices/utci_v2_blazejczyk.py)

**Predicción ML (si se carga modelo):**  
- [core/prediction/prediction_engine.py](core/prediction/prediction_engine.py)

**Validación y anomalías:**  
- [core/indices/physical_consistency.py](core/indices/physical_consistency.py)  
- [core/validation/sensor_anomaly_detector.py](core/validation/sensor_anomaly_detector.py)  
- [core/validation/outlier_detector.py](core/validation/outlier_detector.py)  
- [core/validation/sensor_validator_cascada.py](core/validation/sensor_validator_cascada.py)

**Sensores virtuales (si se registran):**  
- [core/virtual/virtual_sensors.py](core/virtual/virtual_sensors.py)

---

## 1) FAMILIA: SENSORES BASE (INPUTS)

**Origen:** `system.data` + hardware disponible.  
**Uso:** Alimentan todo lo demás.

**Variables típicas usadas por las fórmulas:**
- `temperatura`
- `humedad`
- `presion_barometrica`
- `velocidad_viento`
- `direccion_viento`
- `radiacion_global`
- `uv_index`
- `lluvia` / `lluvia_rate`
- `pm25`, `pm10` (si existe calidad aire)
- `nubosidad` (si existe)

**Publicación raw en bus (si existen):**  
- Ver sección de sensores virtuales raw en [core/system/bus_expander.py](core/system/bus_expander.py#L1920-L1947)

---

## 2) FAMILIA: SENSORES VIRTUALES (DERIVADOS DIRECTOS)

### 2.1 Virtuales básicos en bus
**Fuente:** [core/system/bus_expander.py](core/system/bus_expander.py#L1920-L1984)

Calcula y publica:
- `temperatura_aparente` (actualmente simplificada)
- `tendencia_presion` (derivada de histórico)
- `*_raw` (temperatura, humedad, presión, viento, radiación)

### 2.2 Gestor de sensores virtuales (dinámicos)
**Fuente:** [core/virtual/virtual_sensors.py](core/virtual/virtual_sensors.py)

Sistema **modular** que permite registrar virtuales con `VirtualSensorManager`.  
**Importante:** Las `default_specs()` son **ejemplos** y **no se ejecutan automáticamente**.

Si se registran, se publican como `virtual_<id>` vía auto‑descubrimiento:  
- [core/system/bus_expander.py](core/system/bus_expander.py#L6570-L6592)

---

## 3) FAMILIA: PSICROMETRÍA + AIRE HÚMEDO (NIST + OMM)

### 3.1 NIST Hardy (psicrometría de élite)
**Archivo:** [core/indices/hardy_nist_psicrometria.py](core/indices/hardy_nist_psicrometria.py)

Calcula:
- `presion_vapor_saturado` (Wexler‑Hyland) → `calcular_presion_vapor_saturado_wexler()`
- `enhancement_factor` (Hyland/Wexler) → `calcular_enhancement_factor()`
- `presion_vapor_real`
- `punto_rocio` (inverso Wexler)
- `relacion_mezcla`

### 3.2 OMM/WMO (densidad aire con temperatura virtual)
**Archivo:** [core/indices/omm_densidad_temperatura_virtual.py](core/indices/omm_densidad_temperatura_virtual.py)

Calcula:
- `temperatura_virtual` → `calcular_temperatura_virtual()`
- `densidad_aire_omm` → `calcular_densidad_aire_omm()`
- `densidad_aire_seco`, `densidad_vapor`

### 3.3 Gas ideal (fallback rápido)
**Archivo:** [core/indices/environmental_indices.py](core/indices/environmental_indices.py#L72)

- `densidad_aire_ideal()`

### 3.4 IAPWS Numba (batch / vectorizado)
**Archivo:** [core/indices/physics_numba.py](core/indices/physics_numba.py)

- `densidad_aire_puro()`
- `densidad_aire_vectorizado()`

---

## 4) FAMILIA: RADIACIÓN SOLAR

### 4.1 REST2 Gueymard (autoridad solar)
**Archivo:** [core/indices/rest2_gueymard_radiacion.py](core/indices/rest2_gueymard_radiacion.py)

- `calcular_radiacion_extraterrestre_rest2()`
- Radiación G0, directa, difusa, fracción difusa
- Radiación neta onda corta/larga (FAO‑56 en subfactores)

### 4.2 Temperatura media radiante (vía WBGT)
**Archivo:** [core/indices/environmental_indices.py](core/indices/environmental_indices.py)

- Parte de `wbgt_liljegren_completo()` (balance radiativo y convectivo)

---

## 5) FAMILIA: SENSACIÓN TÉRMICA

### 5.1 UTCI v4.02 (autoridad confort)
**Archivo:** [core/indices/environmental_indices.py](core/indices/environmental_indices.py#L106)

- `utci_v4_02_fiala_completo()`
- 13 micro‑valores (vapor, temperatura operativa, pérdidas calor, ajustes)

### 5.2 WBGT Liljegren (autoridad ocupacional)
**Archivo:** [core/indices/environmental_indices.py](core/indices/environmental_indices.py#L199)

- `wbgt_liljegren_completo()`
- 20 micro‑valores (TWB, TG, vapor, heat index, wind chill, etc.)

### 5.3 Steadman 1984 (clásica rápida)
**Archivo:** [core/indices/environmental_indices.py](core/indices/environmental_indices.py)

- `indice_steadman_apparent_temperature` (referenciada en jerarquía)

### 5.4 UTCI v2 Blazejczyk (extremos)
**Archivo:** [core/indices/utci_v2_blazejczyk.py](core/indices/utci_v2_blazejczyk.py)

- `utci_v2_blazejczyk()`

---

## 6) FAMILIA: EVAPOTRANSPIRACIÓN

### 6.1 FAO‑56 simplificada
**Archivo:** [core/indices/environmental_indices.py](core/indices/environmental_indices.py#L57)

- `evapotranspiracion_penman_monteith()`

### 6.2 Wright nocturno (completo)
**Archivo:** [core/indices/et_nocturna_wright.py](core/indices/et_nocturna_wright.py)

- `evapotranspiracion_penman_monteith_wright()`
- `calcular_factor_resistencia_nocturna_wright()`
- `determinar_periodo_nocturno()`

### 6.3 Wright nocturno (aplicación factor)
**Archivo:** [core/indices/et_nocturna_wright.py](core/indices/et_nocturna_wright.py)

- `evapotranspiracion_wright_nocturna()`

---

## 7) FAMILIA: ÍNDICES DE RIESGO (scores 0–100)

**Fuente:** [core/system/bus_expander.py](core/system/bus_expander.py#L1958-L2024)

Calcula:
- `riesgo_calor` → umbral temperatura + humedad
- `riesgo_frio` → umbral temperatura + viento
- `riesgo_helada` → temperatura + punto de rocío (`_dew_point`)
- `riesgo_tormenta` → presión baja + humedad

---

## 8) FAMILIA: ALERTAS METEOROLÓGICAS

**Fuente:** [core/system/bus_expander.py](core/system/bus_expander.py#L2050-L2189)

Calcula:
- `alerta_tormenta` (presión + humedad + radiación)
- `alerta_calor_extremo` (temperatura + humedad + UV)
- `alerta_frio_extremo` (temperatura + viento)
- `alerta_polvo` (PM2.5 + PM10 + viento)
- `alerta_niebla` (T − Td)
- `alerta_rachas_peligrosas` (rachas)
- `alerta_helada_radiativa` (T baja + HR baja)
- `alerta_rayos` (fallback local)

---

## 9) FAMILIA: TENDENCIAS Y CAMBIOS RÁPIDOS

**Fuente:** [core/system/bus_expander.py](core/system/bus_expander.py#L2189-L2350)

Calcula:
- Tendencias 1h y 3h de temperatura, presión, humedad
- Aceleraciones (°C/h², m/s/h²)
- Cambios rápidos (flags booleanos)
- Variabilidad barométrica
- Cambio rápido de nubosidad (por radiación)

---

## 10) FAMILIA: PREDICCIONES

### 10.1 Predicción ML (LSTM) — si se cargan modelos
**Fuente:** [core/prediction/prediction_engine.py](core/prediction/prediction_engine.py)

- `MotorPrediccion` con modelos LSTM
- Publica `prediccion.<modelo>_plus_<min>min`
- Confianza basada en histórico

### 10.2 Predicciones físicas (convectivas y microfísica)
**Fuente:** [core/system/bus_expander.py](core/system/bus_expander.py#L2350-L2550)

Publica (si hay datos necesarios):
- CAPE, LCL, Lifted Index, Showalter Index
- Microfísica Thompson + ajuste Sundqvist
- Probabilidad lluvia / severidad tormenta (VGP/BRN)

---

## 11) FAMILIA: VALIDACIÓN, ANOMALÍAS, OUTLIERS

### 11.1 Consistencia física
**Archivo:** [core/indices/physical_consistency.py](core/indices/physical_consistency.py)

Valida:
- Radiación nocturna
- UV nocturno
- HR vs punto de rocío
- Temperatura vs radiación
- Presión vs altitud
- Viento vs variabilidad

### 11.2 Detector de anomalías
**Archivo:** [core/validation/sensor_anomaly_detector.py](core/validation/sensor_anomaly_detector.py)

- Rango físico
- Saltos temporales
- Consistencia cruzada (humedad/lluvia, presión/lluvia)
- Simulación de valores si falla (vía `SensorSimulator`)

### 11.3 Detector de outliers estadístico
**Archivo:** [core/validation/outlier_detector.py](core/validation/outlier_detector.py)

- IQR, Z‑score, sensor pegado, ruido excesivo

### 11.4 Validador en cascada
**Archivo:** [core/validation/sensor_validator_cascada.py](core/validation/sensor_validator_cascada.py)

- Bloquea índices si faltan sensores críticos
- Informa índices disponibles/bloqueados

---

## 12) FAMILIA: AUTO‑DISCOVERY Y METADATOS

**Fuente:** [core/system/bus_expander.py](core/system/bus_expander.py#L6540-L6670)

Auto‑descubre y publica:
- Predicciones (`pred_...`)
- Sensores virtuales (`virtual_...`)
- Calibración (`calibr_...`)
- Fusión de sensores (`fusion_...`)
- Metadatos de auto‑descubrimiento

---

## 13) FAMILIAS ADICIONALES (SECCIONES 1–32 DEL BUS)

Estas familias están **completamente implementadas y publicadas** por el BusExpander.  
Se detallan en [core/system/bus_expander.py](core/system/bus_expander.py#L120-L260) y se agrupan así:

- **Física base** (constantes, unidades, conversiones)  
- **Vapor/atmósfera** (presiones, mezclas, densidad)  
- **Astronomía** (posición solar, ciclos)  
- **Geografía / estimación geo**  
- **Confort avanzado**  
- **Suelo/ET**  
- **Interior**  
- **Especializados**  
- **Anomalías / calibración / estadísticas**  
- **Biofísica, energía renovable, grados día**  

> Para auditoría completa de cada subfactor y su nombre exacto en el bus, el origen oficial es el propio BusExpander.

---

## ✅ CONCLUSIÓN

Esta auditoría enumera **todas las familias** de cálculo activas en MeteoSer V49 y **las fórmulas/módulos exactos** que las originan.  
Si quieres, puedo generar una **tabla exhaustiva de cada variable publicada** con su fórmula y dependencia, pero sería una salida masiva (1,500–2,000+ entradas) directamente del BusExpander.
