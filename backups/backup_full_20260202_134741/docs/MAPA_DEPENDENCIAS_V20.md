# MAPA DE DEPENDENCIAS - ARQUITECTURA DE CASCADA V2.0

**Generado:** 2026-02-01T19:09:07.627116

## Filosofía del Sistema

Este sistema implementa una Arquitectura de Cascada Integral donde:
- Cada variable física se calcula UNA SOLA VEZ por ciclo
- Las fórmulas complejas publican todos sus subresultados
- Los demás nodos consumen del Bus de Estado Global sin recalcular
- Se garantiza consistencia atómica en toda la cadena de cálculo

## Grafo de Dependencias

### tendencia_barometrica

**Publica:**
- `presion_filtrada`
- `delta_presion_tidal`
- `delta_presion_wind`
- `densidad_aire`

**Consume:**
- (ninguna - predicción base)

### lluvia_local

**Publica:**
- `pwv`
- `eta_convective`
- `tau_uv`

**Consume:**
- `densidad_aire`
- `nubosidad`

### cota_nieve

**Publica:**
- `temp_bulbo_humedo`
- `isoterma_0c`
- `densidad_virial`

**Consume:**
- `densidad_aire`
- `punto_rocio`

### tormenta_inminente

**Publica:**
- `cape`
- `gradiente_presion`
- `indice_severidad`

**Consume:**
- `nubosidad`
- `densidad_aire`
- `punto_rocio`

### helada_radiativa

**Publica:**
- `radiacion_neta`
- `temp_superficie`
- `kappa_suelo`

**Consume:**
- (ninguna - predicción base)

### visibilidad_bucholtz

**Publica:**
- `beta_ext`
- `beta_rayleigh`
- `indice_refraccion`

**Consume:**
- `nubosidad`
- `densidad_aire`

### riesgo_niebla

**Publica:**
- `deficit_saturacion`

**Consume:**
- `temp_bulbo_humedo`
- `nubosidad`
- `punto_rocio`
- `presion_vapor`

### disipacion_humo

**Publica:**
- `lambda_ach`
- `tasa_renovacion_aire`

**Consume:**
- `densidad_aire`

### saturacion_co2

**Publica:**
- `concentracion_co2_equilibrio`
- `tasa_acumulacion`

**Consume:**
- `densidad_aire`
- `tasa_renovacion_aire`

### et_real

**Publica:**
- `et0_penman`
- `kcb`
- `ke`
- `deficit_presion_vapor`

**Consume:**
- `punto_rocio`
- `densidad_aire`
- `radiacion_neta`

### utci

**Publica:**
- `utci`
- `temp_radiante_media`
- `velocidad_viento_corregida`

**Consume:**
- `punto_rocio`
- `densidad_aire`
- `radiacion_neta`

### monin_obukhov

**Publica:**
- `zeta`
- `longitud_obukhov`
- `u_star`
- `flujo_calor`

**Consume:**
- `densidad_aire`

### nubosidad_haurwitz

**Publica:**
- `nubosidad`
- `transmitancia`
- `radiacion_teorica`

**Consume:**
- (ninguna - predicción base)

### incomodidad_termica

**Publica:**
- `thi`
- `indice_calor`

**Consume:**
- `punto_rocio`
- `densidad_aire`

### punto_rocio_wexler

**Publica:**
- `punto_rocio`
- `presion_vapor`
- `factor_compresibilidad`

**Consume:**
- (ninguna - predicción base)

### indice_sequia

**Publica:**
- `deficit_hidrico`
- `spi`

**Consume:**
- `et0_penman`
- `pwv`

### recomendacion_riego

**Publica:**
- `volumen_agua_necesario`
- `deficit_mad`

**Consume:**
- `et0_penman`
- `deficit_hidrico`

### wbgt_liljegren

**Publica:**
- `wbgt`
- `temp_globo`
- `temp_bulbo_natural`

**Consume:**
- `punto_rocio`
- `densidad_aire`
- `radiacion_neta`

### tiempo_ventilacion

**Publica:**
- `caudal_ventilacion_stack`
- `caudal_ventilacion_wind`

**Consume:**
- `densidad_aire`

### riesgo_mojar_ropa

**Publica:**
- `tiempo_secado`
- `coef_transferencia_masa`

**Consume:**
- `punto_rocio`
- `deficit_presion_vapor`

### pseudo_voc

**Publica:**
- `voc_estimado`
- `tasa_degradacion_uv`

**Consume:**
- `tasa_renovacion_aire`

### temp_radiante_int

**Publica:**
- `tmrt_interior`
- `factor_forma`

**Consume:**
- `radiacion_neta`

### ruido_relativo

**Publica:**
- `nivel_sonoro_eq`

**Consume:**
- (ninguna - predicción base)

### corrientes_internas

**Publica:**
- `velocidad_flujo_interior`
- `diferencial_presion`

**Consume:**
- `densidad_aire`

### riesgo_moho

**Publica:**
- `indice_moho`
- `tiempo_germinacion`

**Consume:**
- `punto_rocio`
- `tasa_renovacion_aire`

## Análisis de Reutilización

Variables más reutilizadas:

- **`densidad_aire`**: 13 consumidores
  - lluvia_local
  - cota_nieve
  - tormenta_inminente
  - visibilidad_bucholtz
  - disipacion_humo
  - saturacion_co2
  - et_real
  - utci
  - monin_obukhov
  - incomodidad_termica
  - wbgt_liljegren
  - tiempo_ventilacion
  - corrientes_internas
- **`punto_rocio`**: 9 consumidores
  - cota_nieve
  - tormenta_inminente
  - riesgo_niebla
  - et_real
  - utci
  - incomodidad_termica
  - wbgt_liljegren
  - riesgo_mojar_ropa
  - riesgo_moho
- **`nubosidad`**: 4 consumidores
  - lluvia_local
  - tormenta_inminente
  - visibilidad_bucholtz
  - riesgo_niebla
- **`radiacion_neta`**: 4 consumidores
  - et_real
  - utci
  - wbgt_liljegren
  - temp_radiante_int
- **`tasa_renovacion_aire`**: 3 consumidores
  - saturacion_co2
  - pseudo_voc
  - riesgo_moho
- **`et0_penman`**: 2 consumidores
  - indice_sequia
  - recomendacion_riego
- **`temp_bulbo_humedo`**: 1 consumidores
  - riesgo_niebla
- **`presion_vapor`**: 1 consumidores
  - riesgo_niebla
- **`pwv`**: 1 consumidores
  - indice_sequia
- **`deficit_hidrico`**: 1 consumidores
  - recomendacion_riego
- **`deficit_presion_vapor`**: 1 consumidores
  - riesgo_mojar_ropa

## Predicciones Base (No consumen de otras)

- **tendencia_barometrica**: Publica `presion_filtrada`, `delta_presion_tidal`, `delta_presion_wind`, `densidad_aire`
- **helada_radiativa**: Publica `radiacion_neta`, `temp_superficie`, `kappa_suelo`
- **nubosidad_haurwitz**: Publica `nubosidad`, `transmitancia`, `radiacion_teorica`
- **punto_rocio_wexler**: Publica `punto_rocio`, `presion_vapor`, `factor_compresibilidad`
- **ruido_relativo**: Publica `nivel_sonoro_eq`
