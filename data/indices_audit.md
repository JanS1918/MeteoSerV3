# Índices auditados
Fecha: auto-generado

## indice_alerta_frio_extremo
- Firma: (temp, viento, humedad)
- Doc: Índice de alerta de frío extremo basado en:
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_alerta_calor_extremo
- Firma: (temp, uv, humedad)
- Doc: Índice de alerta de calor extremo basado en:
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_heat_index_c
- Firma: (temp_c, humedad)
- Doc: (sin docstring)
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_wind_chill_c
- Firma: (temp_c, viento_kmh)
- Doc: (sin docstring)
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_bulbo_humedo_c
- Firma: (temp_c, humedad)
- Doc: (sin docstring)
- Sugerencia: Considerar `pythermalcomfort` para WBGT/globo.

## indice_humidex
- Firma: (temp_c, humedad)
- Doc: (sin docstring)
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_humedad_absoluta_gm3
- Firma: (temp_c, humedad)
- Doc: (sin docstring)
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_vpd_kpa
- Firma: (temp_c, humedad)
- Doc: (sin docstring)
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_entalpia_kjkg
- Firma: (temp_c, humedad, presion_kpa)
- Doc: (sin docstring)
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_wbgt
- Firma: (temp_c, humedad, radiacion, viento_kmh)
- Doc: (sin docstring)
- Sugerencia: Considerar `pythermalcomfort` para WBGT/globo.

## indice_pmv_ppd_simple
- Firma: (temp_c, humedad, viento_kmh)
- Doc: (sin docstring)
- Sugerencia: Usar `pythermalcomfort` para PMV/PPD si está disponible.

## indice_aqi_pm25
- Firma: (pm25)
- Doc: (sin docstring)
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_alerta_tormenta
- Firma: (uv, radiacion, presion, tendencia_presion, rayos)
- Doc: Índice de alerta de tormenta basado en:
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_confort_general
- Firma: (ot, humedad, co2)
- Doc: Índice de confort general basado en:
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_bochorno_real
- Firma: (ot, humedad)
- Doc: Bochorno real: sensación de calor pegajoso.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_aire_seco
- Firma: (humedad)
- Doc: Aire seco: riesgo de deshidratación ambiental.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_aire_pegajoso
- Firma: (humedad, ot)
- Doc: Aire pegajoso: humedad alta + temperatura moderada/alta.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_confort_nocturno
- Firma: (ot, ruido, luz)
- Doc: Confort nocturno: combina temperatura, ruido y luz para valorar el descanso.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_frio_incomodo
- Firma: (ot)
- Doc: Frío incómodo por OT baja.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_aire_cargado
- Firma: (co2, tiempo_sin_ventilar_h)
- Doc: Aire cargado: CO2 alto + tiempo sin ventilación.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_deshidratacion_ambiental
- Firma: (humedad, tiempo_h)
- Doc: Deshidratación ambiental: HR baja mantenida.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_aire_enrarecido
- Firma: (co2, pm25)
- Doc: Aire enrarecido: mezcla de CO2 y PM2.5.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_ventilacion_ideal
- Firma: (co2, humedad, ot)
- Doc: Ventilación ideal: cuánto conviene ventilar AHORA.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_salud_edificio
- Firma: (humedad_media, tiempo_hr_alta_h, condensacion_eventos)
- Doc: Salud del edificio: inverso de humedad crónica + condensación.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_riesgo_moho
- Firma: (humedad, tiempo_hr_alta_h, temperatura)
- Doc: Riesgo de moho: HR alta + tiempo + T moderada.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_riesgo_condensacion_ventanas
- Firma: (t_int, hr_int, t_ext)
- Doc: Condensación en ventanas: punto de rocío interior vs T de vidrio (aprox T_ext).
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_riesgo_olor_cerrado
- Firma: (humedad, tiempo_sin_ventilar_h)
- Doc: Olor a cerrado: HR + tiempo sin ventilación.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_riesgo_helada_local
- Firma: (punto_rocio, t_ext, radiacion_nocturna, viento)
- Doc: IRHL: riesgo de helada local.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_riesgo_micro_lluvias
- Firma: (hr_ext, irll_base, cambio_viento, presion_tendencia)
- Doc: IRLL: riesgo de micro-lluvias (sprinkles).
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_estabilidad_termica_futura
- Firma: (estabilidad_actual, ireav, delta_t_in_out, viento_ext)
- Doc: IETF: predice si la vivienda mantendrá su temperatura.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_condensacion_oculta_armarios
- Firma: (irsh, irin, ersf, historial_nocturno)
- Doc: IRCA: riesgo de condensación oculta en armarios.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_renovacion_efectiva_aire
- Firma: (co2, pm25, irin, irae, actividad_humana)
- Doc: IREA: cuánto se ha renovado realmente el aire.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.

## indice_ritmo_circadiano_ambiental
- Firma: (ot, luz, ruido, estabilidad_termica, irin)
- Doc: IRCA-HUMANO: si el ambiente favorece sueño o vigilia.
- Sugerencia: Revisar precisión; considerar librerías científicas o validación con datos.
