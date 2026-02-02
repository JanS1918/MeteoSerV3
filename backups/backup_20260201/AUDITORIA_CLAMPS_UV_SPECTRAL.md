# 🔒 AUDITORÍA DE CLAMPS - MOTOR UV SPECTRAL DIAMOND V3
**Fecha**: 31 enero 2026  
**Auditor**: Sistema de Excelencia Retroactiva  
**Ley aplicada**: Prohibición de Constantes Ciegas + Vigilancia de Topes

---

## ⚠️ CLAMPS DETECTADOS EN EL MOTOR UV

### 1️⃣ **_calcular_masa_optica() - Línea 120**
```python
masa = 1.0 / max(0.001, math.cos(zenith_rad))
```
**Tipo**: Protección contra división por cero  
**Justificación**: ✅ SEGURIDAD FÍSICA  
- Evita masa óptica infinita en horizonte (sol rasante)  
- Clamp mínimo 0.001 equivale a zenith ~89.94°  
- **VEREDICTO**: LEGÍTIMO - Límite de seguridad real

---

### 2️⃣ **_calcular_indice_claridad() - Línea 147**
```python
return max(0.0, min(1.0, kt))
```
**Tipo**: Límite físico del índice de claridad  
**Justificación**: ✅ LÍMITE FÍSICO ABSOLUTO  
- Kt es una relación G/G0, físicamente acotada a [0, 1]  
- 0 = todo absorbido, 1 = radiación extraterrestre completa  
- **VEREDICTO**: LEGÍTIMO - Definición matemática de Kt

---

### 3️⃣ **_calcular_ozono_estacional() - Línea 196**
```python
return max(200.0, min(500.0, ozono_du))
```
**Tipo**: Límites observacionales de ozono estratosférico  
**Justificación**: ⚠️ **CLAMP DE SEGURIDAD CONSERVADOR**  
- Valores observados: 200-500 DU (climatología satelital)  
- Van Heuklon puede diverger en condiciones extremas (agujero de ozono, erupciones)  
- **VEREDICTO**: LEGÍTIMO pero PUEDE MEJORAR  
- **ACCIÓN**: Mantener clamp pero loguear advertencia si se activa

---

### 4️⃣ **_corrector_presion() - Línea 215**
```python
return max(0.75, min(1.05, factor))
```
**Tipo**: Límites de presión atmosférica razonable  
**Justificación**: ⚠️ **CLAMP FÍSICO-PRÁCTICO**  
- 0.75 = ~600 hPa (Everest, estaciones de montaña extremas)  
- 1.05 = ~1100 hPa (máximo observado en anticiclones siberianos)  
- **VEREDICTO**: LEGÍTIMO pero RESTRICTIVO  
- **ACCIÓN**: Nuestro barómetro mide 970-1050 hPa, este clamp NUNCA se activará en Argentona  
- **RECOMENDACIÓN**: Mantener pero añadir logging si se activa

---

### 5️⃣ **_corrector_vapor() - Línea 238**
```python
return max(0.95, min(1.05, factor))
```
**Tipo**: Límite de efecto de vapor de agua sobre UV  
**Justificación**: ⚠️ **CLAMP EMPÍRICO**  
- Vapor de agua absorbe UV débilmente (banda 290-320 nm)  
- Rango ±5% es conservador según literatura  
- **VEREDICTO**: LEGÍTIMO pero PUEDE SER MÁS DINÁMICO  
- **ACCIÓN**: Considerar ampliar a ±10% en condiciones extremas (100% RH)

---

### 6️⃣ **_corrector_aerosoles() - Líneas 284-287**
```python
rh = max(0.0, min(100.0, humedad_rel)) / 100.0  # Línea 284
...
return max(0.5, min(1.0, transmitancia))        # Línea 310
```
**Tipo**: Clamp de humedad + transmitancia mínima  
**Justificación**: ⚠️ **DUAL: SANITIZACIÓN + LÍMITE FÍSICO**  
- Clamp de humedad (0-100%): ✅ SANITIZACIÓN DE ENTRADA  
- Clamp de transmitancia (0.5-1.0): ⚠️ LÍMITE CONSERVADOR  
  - 0.5 = 50% transmitancia en días MUY brumosos (AOD > 1.0)  
  - **VEREDICTO**: LEGÍTIMO pero puede ser más permisivo  
  - **ACCIÓN**: Bajar a 0.3 para permitir condiciones de incendios/calima severa

---

### 7️⃣ **_transferencia_radiativa_uv() - Línea 346**
```python
return max(0.0, uv)
```
**Tipo**: Protección contra UV negativo  
**Justificación**: ✅ SEGURIDAD MATEMÁTICA  
- UV negativo es físicamente imposible  
- Puede ocurrir por errores numéricos en cálculos exponenciales  
- **VEREDICTO**: LEGÍTIMO - Límite de seguridad real

---

## 📊 RESUMEN EJECUTIVO

| Clamp | Línea | Veredicto | Acción |
|-------|-------|-----------|--------|
| max(0.001, cos(Z)) | 120 | ✅ LEGÍTIMO | NINGUNA |
| max(0, min(1, Kt)) | 147 | ✅ LEGÍTIMO | NINGUNA |
| max(200, min(500, O3)) | 196 | ⚠️ CONSERVADOR | AÑADIR LOGGING |
| max(0.75, min(1.05, Presión)) | 215 | ⚠️ RESTRICTIVO | AÑADIR LOGGING |
| max(0.95, min(1.05, Vapor)) | 238 | ⚠️ EMPÍRICO | CONSIDERAR ±10% |
| max(0.5, min(1.0, Aerosol)) | 310 | ⚠️ CONSERVADOR | BAJAR A 0.3 |
| max(0.0, UV) | 346 | ✅ LEGÍTIMO | NINGUNA |

---

## ✅ CONSTANTES AUDITADAS VS SENSORES REALES

| Constante | Valor Fijo | Sensor Real | Estado |
|-----------|------------|-------------|--------|
| Ozono | ~~0.3 DU~~ | ✅ Van Heuklon (lat, fecha) | MODERNIZADO |
| Masa Óptica | ~~1/cos(Z)~~ | ✅ Kasten-Young (1989) | MODERNIZADO |
| Presión ISA | ~~1013.25 hPa~~ | ✅ Barómetro Argentona | MODERNIZADO |
| AOD Base | 0.15 | ⚠️ FIJO (mejorable con visibilidad) | PENDIENTE |
| Constante Solar | 1367 W/m² | ⚠️ FIJO (mejorable con ciclo solar) | ACEPTABLE |
| Tau Rayleigh | 0.15 | ⚠️ FIJO (mejorable con presión real) | PENDIENTE |

---

## 🎯 ACCIONES RECOMENDADAS

1. ✅ **COMPLETADO**: Kasten-Young, Van Heuklon, Presión Real, Aerosoles Hänel
2. ⚠️ **MEJORABLE**: Tau Rayleigh debería usar presión real en lugar de 0.15 fijo
3. ⚠️ **MEJORABLE**: AOD base (0.15) podría usar sensor de visibilidad si disponible
4. 📋 **LOGGING**: Añadir advertencias cuando los clamps de ozono/presión/aerosol se activen
5. 🔧 **CALIBRACIÓN**: Bajar clamp de aerosoles a 0.3 para permitir calima severa

---

## 🔒 SELLO PERMANENTE

Esta auditoría queda registrada bajo la **Ley de Excelencia Retroactiva**.  
Queda prohibido simplificar estas fórmulas en futuras actualizaciones.  
Cualquier modificación debe pasar por nueva auditoría de clamps.

**Firma Digital**: Spectral_Diamond_v3  
**Fecha**: 2026-01-31  
**Nivel de Sintonización**: DIAMANTE 💎
