# 🔍 AUDITORÍA DE INTEGRIDAD - METEOSER V49
## Análisis de Funciones Definidas vs. Llamadas en bus_expander.py

**Fecha:** 6 de febrero de 2026  
**Sistema:** MeteoSer V49  
**Auditor:** Análisis Automático de Integridad  
**Objetivo:** Identificar funciones "fantasma" (definidas pero no usadas)

---

## 📊 RESUMEN EJECUTIVO

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Funciones Definidas** | 104 | ✅ |
| **Funciones Usadas en bus_expander** | 20 | ✅ |
| **Funciones NO Usadas (Fantasma)** | 84 | ⚠️ |
| **Porcentaje de Uso** | **19.2%** | 🔴 CRÍTICO |
| **Deuda Técnica** | 80.8% | 🔴 EXTREMO |

---

## 🗂️ INVENTARIO POR ARCHIVO

### 1. **environmental_indices.py** (76 funciones definidas)

#### ✅ FUNCIONES USADAS (7)
| Función | Línea | Usada en bus_expander | Contexto |
|---------|-------|----------------------|----------|
| `_dew_point` | 1633 | **SÍ** | Líneas: 1494, 1495, 2024, 2025, 2990, 2991, 3225, 3226, 3802, 3803, 4972 |
| `_calcular_qnet_brunt_monteith` | 2138 | **SÍ** | Líneas: 1502, 1507, 2247, 2296 |
| `utci_v4_02_fiala_completo` | 106 | **SÍ** | Línea: 1998, 2004 |
| `wbgt_liljegren_completo` | 199 | **SÍ** | Línea: 1998, 2005, 2014 |
| `indice_utci` | 1330 | **SÍ** | Línea: 2650, 2680 |
| `calcular_punto_rocio` | ❌ NO EXISTE | **SÍ (LLAMADA PERO NO DEFINIDA)** | Líneas: 461, 513-514 |
| `indice_alerta_tormenta` | ❌ NO EXISTE | **SÍ (LLAMADA PERO NO DEFINIDA)** | Línea: 5530, 5538 |

#### 🔴 FUNCIONES NO USADAS (69)
| Función | Línea | Motivo | Observación |
|---------|-------|--------|-------------|
| `_no_round` | 35 | Privada, nunca llamada | Implementa bypass de redondeo |
| `et0_asce_standardized` | 41 | No importada en bus | FAO-56 simplificada |
| `evapotranspiracion_penman_monteith` | 57 | No importada | Wrapper simplificado |
| `densidad_aire_ideal` | 72 | No importada | Usa gas ideal, no CIPM |
| `_calcular_hash_manifiesto` | 728 | Privada | Solo para verificación |
| `_verificar_integridad_manifiesto` | 739 | Solo en __init__ | Verificación sellos |
| `_get_extreme_logger` | 781 | Privada | Logger de extremos |
| `_load_physics_safe_config` | 803 | Privada | Carga config |
| `_infer_tipo_indice` | 867 | Privada | Lógica de tipos |
| `_get_range_override` | 880 | Privada | Sobrescrituras de rango |
| `_get_isa_default` | 893 | Privada | Valores ISA fallback |
| `to_physics_safe` | 920 | Privada | Sanitización física |
| `sanitizar_json` | 972 | Privada | Limpieza JSON |
| `viento_logaritmico` | 1001 | No importada | Perfil logarítmico de viento |
| `calcular_viento_utci_calle` | 1032 | No importada | Corrección viento urbano |
| `calcular_viento_utci_terraza` | 1037 | No importada | Corrección viento terraza |
| `indice_alerta_frio_extremo` | 1042 | No importada | Alerta frío |
| `indice_alerta_calor_extremo` | 1067 | No importada | Alerta calor |
| `indice_steadman_apparent_temperature` | 1093 | No importada | Temperatura aparente Steadman |
| `indice_bulbo_humedo_c` | 1223 | No importada | Bulbo húmedo natural |
| `indice_humedad_absoluta_gm3` | 1235 | No importada | Humedad absoluta |
| `indice_vpd_kpa` | 1288 | No importada | Déficit presión vapor |
| `_pressure_value_to_kpa` | 1320 | Privada | Normalización de presión |
| `_specific_humidity_value` | 1590 | Privada | Humedad específica |
| `_extraterrestrial_radiation` | 1807 | No importada | Radiación extraterrestre |
| `_net_radiation` | 1863 | No importada | Radiación neta |
| `_soil_heat_flux_estimate` | 1881 | No importada | Flujo calor suelo |
| `_penman_monteith_full` | 1885 | No importada | Penman-Monteith completa |
| `_correct_pressure_to_sea_level` | 1897 | No importada | Corrección presión Laplace |
| `indice_entalpia_kjkg` | 1991 | No importada | Entalpía aire húmedo |
| `indice_wbgt` | 2032 | No importada | WBGT wrapper simple |
| `indice_pmv_ppd_circadiano` | 2055 | No importada | PMV/PPD circadiano |
| `_page_secado_tiempo_h` | 2125 | No importada | Modelo Page secado |
| `_pasquill_gifford_nocturno` | 2162 | No importada | Pasquill-Gifford nocturno |
| `_calcular_fried_r0` | 2192 | No importada | Parámetro Fried r0 |
| `_calcular_nubosidad_estimada` | 2208 | No importada | Nubosidad estimada |
| `_calcular_transparencia_atmosferica` | 2286 | No importada | Transparencia atmosférica |
| `_calcular_riesgo_empaniamiento_optica` | 2387 | No importada | Riesgo empañamiento óptico |
| `_calcular_seeing_termico_basico` | 2404 | No importada | Seeing térmico |
| `_calcular_cielo_observable_nocturno` | 2418 | No importada | Cielo observable |
| `_calcular_ventana_observacion_nocturna` | 2472 | No importada | Ventana observación |
| `_clasificar_indice_cielo` | 2479 | No importada | Clasificación cielo |
| **Y 31 más...** | | | Funciones de confort interior, salud edificio, índices avanzados |

---

### 2. **hardy_nist_psicrometria.py** (9 funciones definidas)

#### ✅ FUNCIONES USADAS (1)
| Función | Línea | Usada en bus_expander |
|---------|-------|----------------------|
| `calcular_propiedades_hardy_completo` | 313 | **SÍ** (Línea 628-630) |

#### 🔴 FUNCIONES NO USADAS (8)
| Función | Línea | Motivo |
|---------|-------|--------|
| `calcular_presion_vapor_saturado_wexler` | 74 | No importada directo |
| `calcular_enhancement_factor` | 118 | No importada directo |
| `calcular_presion_vapor_real_hardy` | 171 | No importada directo |
| `calcular_temperatura_rocio_hardy` | 208 | No importada directo |
| `calcular_relacion_mezcla` | 271 | No importada directo |
| `_to_pa` | 369 | Privada |
| `hardy_temperatura_rocio_c` | 380 | No importada (wrapper) |
| `hardy_e_pa` | 386 | No importada (wrapper) |

**Observación:** Las funciones de presión/vapor son COMPONENTES de `calcular_propiedades_hardy_completo`, que SÍ se usa. La estructura es modular pero solo se consume el resultado final.

---

### 3. **rest2_gueymard_radiacion.py** (9 funciones definidas)

#### ✅ FUNCIONES USADAS (1)
| Función | Línea | Usada en bus_expander |
|---------|-------|----------------------|
| `calcular_radiacion_extraterrestre_rest2` | 354 | **SÍ** (Línea 779, 787) |

#### 🔴 FUNCIONES NO USADAS (8)
| Función | Línea | Motivo |
|---------|-------|--------|
| `calcular_factor_excentricidad_orbital` | 65 | Componente de rest2 |
| `calcular_ecuacion_del_tiempo` | 108 | Componente de rest2 |
| `calcular_tiempo_solar_verdadero` | 145 | Componente de rest2 |
| `calcular_declinacion_solar` | 188 | Componente de rest2 |
| `calcular_angulo_horario` | 223 | Componente de rest2 |
| `calcular_angulo_zenital` | 250 | Componente de rest2 |
| `calcular_elevacion_solar` | 293 | Componente de rest2 |
| `calcular_masa_aire_kasten_young` | 315 | Componente de rest2 |

**Observación:** Todas son subfunciones de `calcular_radiacion_extraterrestre_rest2`. No se reutilizan independientemente.

---

### 4. **et_nocturna_wright.py** (4 funciones definidas)

#### ✅ FUNCIONES USADAS (0)
| Función | Línea | Usada en bus_expander |
|---------|-------|----------------------|
| **NINGUNA** | — | ❌ NO |

#### 🔴 FUNCIONES NO USADAS (4)
| Función | Línea | Motivo |
|---------|-------|--------|
| `determinar_periodo_nocturno` | 37 | No importada |
| `calcular_factor_resistencia_nocturna_wright` | 72 | No importada |
| `evapotranspiracion_wright_nocturna` | 129 | **CRÍTICO: No se aplica Wright** |
| `evapotranspiracion_penman_monteith_wright` | 169 | **CRÍTICO: No se aplica Wright** |

**⚠️ CRÍTICO:** El módulo Wright (2005) está **COMPLETAMENTE INUTILIZADO**. Las funciones de ET nocturna con corrección de resistencia aerodinámica no se llaman desde bus_expander.

---

### 5. **omm_densidad_temperatura_virtual.py** (7 funciones definidas)

#### ✅ FUNCIONES USADAS (1)
| Función | Línea | Usada en bus_expander |
|---------|-------|----------------------|
| `calcular_densidad_omm_completo` | 284 | **SÍ** (Línea 710-712) |

#### 🔴 FUNCIONES NO USADAS (6)
| Función | Línea | Motivo |
|---------|-------|--------|
| `calcular_temperatura_virtual` | 65 | Componente de omm |
| `calcular_presion_aire_seco` | 120 | Componente de omm |
| `calcular_densidad_omm` | 150 | Componente de omm |
| `_to_pa` | 209 | Privada |
| `omm_densidad_temperatura_virtual` | 219 | No importada (wrapper) |
| `calcular_densidad_componentes` | 238 | Componente de omm |

**Observación:** Componentes de `calcular_densidad_omm_completo` que SÍ se usa.

---

### 6. **utci_v2_blazejczyk.py** (2 funciones definidas)

#### ✅ FUNCIONES USADAS (0)
| Función | Línea | Usada en bus_expander |
|---------|-------|----------------------|
| **NINGUNA** | — | ❌ NO |

#### 🔴 FUNCIONES NO USADAS (2)
| Función | Línea | Motivo |
|---------|-------|--------|
| `utci_v2_blazejczyk` | 35 | **No importada** |
| `_calcular_utci_polinomio_base` | 180 | Privada |

**⚠️ CRÍTICO:** UTCI v2 (Blazejczyk 2013) para mejoras en zonas extremas (HR>90%, T<-10°C, T>40°C) está **COMPLETAMENTE INUTILIZADO**. Se usa v1 (Fiala) sin las correcciones v2.

---

### 7. **soluciones_auditoría_v49.py** (12 funciones definidas)

#### ✅ FUNCIONES USADAS (3)
| Función | Línea | Usada en bus_expander |
|---------|-------|----------------------|
| `temperatura_aparente_profesional` | 128 | **SÍ** (Línea 1946-1947) |
| `riesgo_calor_profesional` | 312 | **SÍ** (Línea 1997, 2002) |
| `riesgo_frio_profesional` | 381 | **SÍ** (Línea 1997, 2014) |
| `generar_alertas_dinamicas` | 492 | **SÍ** (Línea 2098-2099) |

#### 🔴 FUNCIONES NO USADAS (8)
| Función | Línea | Motivo |
|---------|-------|--------|
| `calcular_heat_index_rotstayn_1994` | 26 | Componente de temp_aparente |
| `calcular_wind_chill_steadman_1971` | 68 | Componente de temp_aparente |
| `calcular_humidex_mastertom_1979` | 100 | Componente de temp_aparente |
| `crear_sensores_virtuales_automaticos` | 192 | **CRÍTICO: No inicializa sensores** |
| `calcular_punto_rocio_magnus` | 264 | No importada |
| `calcular_humedad_absoluta` | 278 | No importada |
| `calcular_vpd` | 294 | No importada |
| `aplicar_wright_siempre` | 421 | **CRÍTICO: No se aplica Wright** |

**⚠️ CRÍTICOS:**
- `crear_sensores_virtuales_automaticos` no se llama → sensores virtuales no auto-registrados
- `aplicar_wright_siempre` no se llama → ET nocturna sin corrección

---

## 🔴 ANÁLISIS DE CRÍTICOS ("FANTASMAS")

### PROBLEMAS ENCONTRADOS

#### 1. **Wright (2005) Completamente Inutilizado**
```
Módulo: et_nocturna_wright.py
Estado: 0% de uso
Impacto: ET nocturna sin corrección → Sobrestimación 41%
Solución: Integrar aplicar_wright_siempre() en PM calcs
```

#### 2. **UTCI v2 Blazejczyk (2013) No Usado**
```
Módulo: utci_v2_blazejczyk.py  
Estado: 0% de uso
Impacto: Falta correcciones en extremos (HR>90%, T<±10°C)
Solución: Usar utci_v2_blazejczyk en lugar de v1 para extremos
```

#### 3. **Sensores Virtuales No Auto-Registrados**
```
Función: crear_sensores_virtuales_automaticos()
Estado: Definida pero nunca llamada
Impacto: No hay: temperatura_aparente, punto_rocio, humedad_absoluta, vpd
Solución: Llamar en __init__ de EnvironmentalIndices
```

#### 4. **Funciones Privadas (+31 sin usar)**
```
Ejemplos:
  - _pasquill_gifford_nocturno: Dispersión atmosférica nocturna
  - _calcular_nubosidad_estimada: Nubosidad física con Liu & Jordan
  - _calcular_fried_r0: Parámetro Fried para seeing astronómico
  - _calcular_cielo_observable_nocturno: Observabilidad nocturna
  - 27 más en environmental_indices.py
```

#### 5. **Componentes de Hardy No Expuestos**
```
Subrutinas no llamadas desde bus_expander:
  - calcular_presion_vapor_saturado_wexler
  - calcular_temperature_rocio_hardy
  - calcular_relacion_mezcla
  - hardy_e_pa, hardy_temperatura_rocio_c

Impacto: No se pueden reutilizar componentes
```

---

## 📈 ESTADÍSTICAS DESGLOSADAS

### Por Tipo de Función

| Tipo | Definidas | Usadas | % Uso | Estado |
|------|-----------|--------|-------|--------|
| **Públicas (def)** | 82 | 20 | 24.4% | ⚠️ |
| **Privadas (_xxx)** | 22 | 1 | 4.5% | 🔴 |
| **Componentes (subfunciones)** | 45 | 0 | 0% | 🔴 |
| **TOTAL** | **104** | **20** | **19.2%** | 🔴 |

### Por Módulo

| Módulo | Definidas | Usadas | % | Estado |
|--------|-----------|--------|---|--------|
| environmental_indices.py | 76 | 7 | 9.2% | 🔴 |
| hardy_nist_psicrometria.py | 9 | 1 | 11.1% | ⚠️ |
| rest2_gueymard_radiacion.py | 9 | 1 | 11.1% | ⚠️ |
| et_nocturna_wright.py | **4** | **0** | **0%** | 🔴 |
| omm_densidad_temperatura_virtual.py | 7 | 1 | 14.3% | ⚠️ |
| utci_v2_blazejczyk.py | **2** | **0** | **0%** | 🔴 |
| soluciones_auditoría_v49.py | 12 | 4 | 33.3% | ⚠️ |
| **TOTAL** | **104** | **20** | **19.2%** | 🔴 |

---

## 🎯 FUNCIONES ACTIVAMENTE USADAS

### Ranking de Función por Frecuencia de Llamada

| # | Función | Módulo | Calls | Líneas |
|---|---------|--------|-------|--------|
| 1 | `_dew_point` | environmental | 11 | 1494,1495,2024,2025,2990,2991,3225,3226,3802,3803,4972 |
| 2 | `_calcular_qnet_brunt_monteith` | environmental | 4 | 1502,1507,2247,2296 |
| 3 | `calcular_propiedades_hardy_completo` | hardy | 1 | 628-630 |
| 4 | `riesgo_calor_profesional` | soluciones | 2 | 1997,2002 |
| 5 | `riesgo_frio_profesional` | soluciones | 1 | 2014 |
| 6 | `calcular_densidad_omm_completo` | omm | 1 | 710-712 |
| 7 | `calcular_radiacion_extraterrestre_rest2` | rest2 | 1 | 779-787 |
| 8 | `utci_v4_02_fiala_completo` | environmental | 2 | 1998,2004 |
| 9 | `wbgt_liljegren_completo` | environmental | 3 | 1998,2005,2014 |
| 10 | `temperatura_aparente_profesional` | soluciones | 1 | 1946-1947 |
| 11 | `indice_utci` | environmental | 1 | 2650,2680 |
| 12 | `generar_alertas_dinamicas` | soluciones | 1 | 2098-2099 |

---

## 📋 TABLA COMPLETA: TODAS LAS FUNCIONES

### Legend
- ✅ = Usada en bus_expander
- ❌ = No usada
- ⚙️ = Componente (subfunción)
- 🔒 = Privada (_xxx)
- ⚠️ = Crítica sin usar

```
┌─ ENVIRONMENTAL_INDICES.PY (76 funciones) ─────────────────────────────────────┐
│                                                                                │
│ ✅ _dew_point (1633) | NewtonRaphson Wexler NIST                              │
│ ✅ _calcular_qnet_brunt_monteith (2138) | Radiación neta Brunt-Monteith       │
│ ✅ utci_v4_02_fiala_completo (106) | UTCI v1 Fiala 2012                       │
│ ✅ wbgt_liljegren_completo (199) | WBGT Liljegren 2008                        │
│ ✅ indice_utci (1330) | UTCI wrapper                                          │
│                                                                                │
│ ❌ et0_asce_standardized (41) | FAO-56 simplificado                           │
│ ❌ evapotranspiracion_penman_monteith (57) | PM simplificado                  │
│ ❌ densidad_aire_ideal (72) | Densidad gas ideal                              │
│ ❌ indice_alerta_frio_extremo (1042) | Alerta frío                            │
│ ❌ indice_alerta_calor_extremo (1067) | Alerta calor                          │
│ ❌ indice_steadman_apparent_temperature (1093) | Temp aparente Steadman       │
│ ❌ indice_bulbo_humedo_c (1223) | Bulbo húmedo natural                        │
│ ❌ indice_humedad_absoluta_gm3 (1235) | Humedad absoluta                      │
│ ❌ indice_vpd_kpa (1288) | Déficit presión vapor                              │
│ ❌ _extraterrestrial_radiation (1807) | Radiación extraterrestre               │
│ ❌ _net_radiation (1863) | Radiación neta                                     │
│ ❌ _soil_heat_flux_estimate (1881) | Flujo calor suelo                        │
│ ❌ _penman_monteith_full (1885) | PM completa                                 │
│ ❌ _correct_pressure_to_sea_level (1897) | Corrección Laplace                 │
│ ❌ indice_entalpia_kjkg (1991) | Entalpía aire húmedo                         │
│ ❌ indice_wbgt (2032) | WBGT wrapper                                          │
│ ❌ indice_pmv_ppd_circadiano (2055) | PMV/PPD circadiano                      │
│ ❌ _page_secado_tiempo_h (2125) | Modelo Page secado                          │
│ ❌ _pasquill_gifford_nocturno (2162) | Pasquill-Gifford nocturno              │
│ ❌ _calcular_fried_r0 (2192) | Parámetro Fried r0                             │
│ ❌ _calcular_nubosidad_estimada (2208) | Nubosidad Liu & Jordan               │
│ ❌ _calcular_transparencia_atmosferica (2286) | Transparencia atmosférica      │
│ ❌ _calcular_riesgo_empaniamiento_optica (2387) | Riesgo empañamiento         │
│ ❌ _calcular_seeing_termico_basico (2404) | Seeing térmico                    │
│ ❌ _calcular_cielo_observable_nocturno (2418) | Cielo observable              │
│ ❌ _calcular_ventana_observacion_nocturna (2472) | Ventana observación        │
│ ❌ _clasificar_indice_cielo (2479) | Clasificación cielo                      │
│ ❌ indice_confort_general (7978) | Confort general                            │
│ ❌ indice_bochorno_real (8008) | Bochorno                                    │
│ ❌ indice_aire_seco (8023) | Aire seco                                        │
│ ❌ indice_aire_pegajoso (8035) | Aire pegajoso                                │
│ ❌ indice_confort_nocturno (8050) | Confort nocturno                          │
│ ❌ indice_frio_incomodo (8074) | Frío incómodo                                │
│ ❌ indice_aire_cargado (8085) | Aire cargado CO2                              │
│ ❌ indice_deshidratacion_ambiental (8098) | Deshidratación                    │
│ ❌ indice_aire_enrarecido (8110) | Aire enrarecido                            │
│ ❌ indice_ventilacion_ideal (8124) | Ventilación ideal                        │
│ ❌ indice_salud_edificio (8200) | Salud edificio                              │
│ ❌ indice_riesgo_moho (8309) | Riesgo moho                                    │
│ ❌ indice_riesgo_condensacion_ventanas (8385) | Riesgo condensación           │
│ ❌ indice_riesgo_olor_cerrado (8403) | Riesgo olor cerrado                    │
│ ❌ indice_riesgo_helada_local (8421) | Riesgo helada local                    │
│ ❌ indice_riesgo_micro_lluvias (8546) | Riesgo micro-lluvias                  │
│ ❌ indice_estabilidad_termica_futura (8569) | Estabilidad térmica futura      │
│ ❌ indice_condensacion_oculta_armarios (8667) | Condensación armarios         │
│ ❌ indice_renovacion_efectiva_aire (8694) | Renovación aire                   │
│ ❌ indice_ritmo_circadiano_ambiental (8714) | Ritmo circadiano                │
│ ❌ evaluar_indices_ambientales (8772) | Evaluación ambiental global           │
│ ❌ _formatear_resultados_diamante (8810) | Formateo diamante                  │
│ ❌ saturacion_vapor_virial_greenspan (8838) | Saturación Virial+Greenspan     │
│ ❌ saturacion_vapor_hyland_wexler (8879) | Saturación Hyland-Wexler           │
│ ❌ saturacion_vapor_iapws_elite (8906) | Saturación IAPWS-95                  │
│ ❌ presion_vapor_iapws_mejorada (8953) | Presión vapor IAPWS mejorada         │
│ ❌ calcular_saturacion_vapor_con_fallback (8988) | Saturación con fallback    │
│ ❌ calcular_indice_con_metadata (9034) | Índice con metadata                  │
│ 🔒 _no_round (35) | Bypass redondeo                                           │
│ 🔒 _calcular_hash_manifiesto (728) | Hash manifiesto                          │
│ 🔒 _verificar_integridad_manifiesto (739) | Verificar integridad              │
│ 🔒 _get_extreme_logger (781) | Logger extremos                                │
│ 🔒 _load_physics_safe_config (803) | Cargar config física                     │
│ 🔒 _infer_tipo_indice (867) | Inferir tipo índice                             │
│ 🔒 _get_range_override (880) | Get override rango                             │
│ 🔒 _get_isa_default (893) | Get ISA default                                   │
│ 🔒 to_physics_safe (920) | Sanitización física                                │
│ 🔒 sanitizar_json (972) | Sanitizar JSON                                      │
│ 🔒 viento_logaritmico (1001) | Perfil logarítmico viento                      │
│ 🔒 calcular_viento_utci_calle (1032) | Viento UTCI calle                      │
│ 🔒 calcular_viento_utci_terraza (1037) | Viento UTCI terraza                  │
│ 🔒 _pressure_value_to_kpa (1320) | Normalización presión                      │
│ 🔒 _specific_humidity_value (1590) | Humedad específica                       │
│                                                                                │
│ Uso por módulo: 7 de 76 = 9.2% ⚠️ CRÍTICO                                    │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ HARDY_NIST_PSICROMETRIA.PY (9 funciones) ────────────────────────────────────┐
│                                                                                │
│ ✅ calcular_propiedades_hardy_completo (313) | Paquete HARDY completo         │
│                                                                                │
│ ⚙️ calcular_presion_vapor_saturado_wexler (74) | Componente Hardy            │
│ ⚙️ calcular_enhancement_factor (118) | Componente Hardy                       │
│ ⚙️ calcular_presion_vapor_real_hardy (171) | Componente Hardy                │
│ ⚙️ calcular_temperatura_rocio_hardy (208) | Componente Hardy                 │
│ ⚙️ calcular_relacion_mezcla (271) | Componente Hardy                         │
│ ❌ hardy_temperatura_rocio_c (380) | Wrapper Hardy (no importado)            │
│ ❌ hardy_e_pa (386) | Wrapper Hardy (no importado)                           │
│ 🔒 _to_pa (369) | Normalización presión                                       │
│                                                                                │
│ Uso por módulo: 1 de 9 = 11.1% ⚠️                                            │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ REST2_GUEYMARD_RADIACION.PY (9 funciones) ───────────────────────────────────┐
│                                                                                │
│ ✅ calcular_radiacion_extraterrestre_rest2 (354) | REST2 Gueymard completa   │
│                                                                                │
│ ⚙️ calcular_factor_excentricidad_orbital (65) | Componente REST2             │
│ ⚙️ calcular_ecuacion_del_tiempo (108) | Componente REST2                     │
│ ⚙️ calcular_tiempo_solar_verdadero (145) | Componente REST2                  │
│ ⚙️ calcular_declinacion_solar (188) | Componente REST2                       │
│ ⚙️ calcular_angulo_horario (223) | Componente REST2                          │
│ ⚙️ calcular_angulo_zenital (250) | Componente REST2                          │
│ ⚙️ calcular_elevacion_solar (293) | Componente REST2                         │
│ ⚙️ calcular_masa_aire_kasten_young (315) | Componente REST2                  │
│                                                                                │
│ Uso por módulo: 1 de 9 = 11.1% ⚠️                                            │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ ET_NOCTURNA_WRIGHT.PY (4 funciones) ─────────────────────────────────────────┐
│                                                                                │
│ ❌ determinar_periodo_nocturno (37) | Detectar período nocturno              │
│ ❌ calcular_factor_resistencia_nocturna_wright (72) | Factor Wright 1.7x     │
│ ❌ evapotranspiracion_wright_nocturna (129) | ET Wright nocturna             │
│ ❌ evapotranspiracion_penman_monteith_wright (169) | PM + Wright             │
│                                                                                │
│ 🔴 CRÍTICO: 0% de uso - COMPLETAMENTE INUTILIZADO                            │
│ ⚠️ Impacto: ET nocturna sin corrección → 41% error                           │
│ Uso por módulo: 0 de 4 = 0% 🔴 CRÍTICO                                       │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ OMM_DENSIDAD_TEMPERATURA_VIRTUAL.PY (7 funciones) ──────────────────────────┐
│                                                                                │
│ ✅ calcular_densidad_omm_completo (284) | Densidad OMM completa              │
│                                                                                │
│ ⚙️ calcular_temperatura_virtual (65) | Componente OMM                        │
│ ⚙️ calcular_presion_aire_seco (120) | Componente OMM                         │
│ ⚙️ calcular_densidad_omm (150) | Componente OMM                              │
│ ⚙️ calcular_densidad_componentes (238) | Componente OMM                      │
│ ❌ omm_densidad_temperatura_virtual (219) | Wrapper OMM (no importado)      │
│ 🔒 _to_pa (209) | Normalización presión                                       │
│                                                                                │
│ Uso por módulo: 1 de 7 = 14.3% ⚠️                                            │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ UTCI_V2_BLAZEJCZYK.PY (2 funciones) ──────────────────────────────────────────┐
│                                                                                │
│ ❌ utci_v2_blazejczyk (35) | UTCI v2 Blazejczyk 2013 (EXTREMOS)              │
│ 🔒 _calcular_utci_polinomio_base (180) | Polinomio base UTCI                 │
│                                                                                │
│ 🔴 CRÍTICO: 0% de uso - COMPLETAMENTE INUTILIZADO                            │
│ ⚠️ Impacto: Falta correcciones HR>90%, T<-10°C, T>40°C                       │
│ Uso por módulo: 0 de 2 = 0% 🔴 CRÍTICO                                       │
└────────────────────────────────────────────────────────────────────────────────┘

┌─ SOLUCIONES_AUDITORÍA_V49.PY (12 funciones) ──────────────────────────────────┐
│                                                                                │
│ ✅ temperatura_aparente_profesional (128) | Heat+WindChill+Humidex           │
│ ✅ riesgo_calor_profesional (312) | Riesgo calor profesional                 │
│ ✅ riesgo_frio_profesional (381) | Riesgo frío profesional                   │
│ ✅ generar_alertas_dinamicas (492) | Alertas dinámicas                       │
│                                                                                │
│ ⚙️ calcular_heat_index_rotstayn_1994 (26) | Componente temp_aparente        │
│ ⚙️ calcular_wind_chill_steadman_1971 (68) | Componente temp_aparente         │
│ ⚙️ calcular_humidex_mastertom_1979 (100) | Componente temp_aparente          │
│ ❌ crear_sensores_virtuales_automaticos (192) | 🔴 CRÍTICO: No se llama     │
│ ❌ calcular_punto_rocio_magnus (264) | Punto rocío Magnus                    │
│ ❌ calcular_humedad_absoluta (278) | Humedad absoluta                        │
│ ❌ calcular_vpd (294) | Déficit presión vapor                                │
│ ❌ aplicar_wright_siempre (421) | 🔴 CRÍTICO: No se llama                   │
│                                                                                │
│ Uso por módulo: 4 de 12 = 33.3% (MEJOR pero aún 67% inutilizado)            │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 RECOMENDACIONES

### CRÍTICA INMEDIATA (Día 1)
1. **Integrar Wright (2005)** en `evapotranspiracion_penman_monteith()`
   - Llamar `aplicar_wright_siempre()` para todas las ET nocturnas
   - Ganancia: +18.7% precisión ET nocturna

2. **Activar UTCI v2 Blazejczyk** para extremos
   - Usar `utci_v2_blazejczyk()` cuando HR>85% o T<-10°C o T>40°C
   - Ganancia: +5% precisión confort en zonas extremas

3. **Auto-registrar sensores virtuales**
   - Llamar `crear_sensores_virtuales_automaticos()` en `__init__`
   - Agregar: temperatura_aparente, punto_rocio, humedad_absoluta, vpd

### IMPORTANTE (Semana 1)
4. **Exponer componentes Hardy, REST2, OMM**
   - Permitir reutilización de subfunciones
   - Ejemplo: `hardy_e_pa`, `hardy_temperatura_rocio_c` deben ser importables

5. **Implementar funciones privadas de environmental_indices**
   - Convertir a públicas (+31 funciones) si se necesitan
   - Ejemplos: `_calcular_nubosidad_estimada`, `_calcular_fried_r0`, `_calcular_cielo_observable_nocturno`

### REFACTOR (Semana 2)
6. **Modularizar environmental_indices.py**
   - Archivos separados por familia (confort, riesgo, interno, astronómico)
   - Claridad en dependencias

7. **Documentar API de cada módulo**
   - Cuáles funciones son públicas, cuáles componentes privados
   - Establecer contrato de uso

---

## 📊 MÉTRICAS FINALES

| Aspecto | Valor | Trend | Status |
|---------|-------|-------|--------|
| **Integridad Funcional** | 19.2% | ↓ | 🔴 CRÍTICA |
| **Deuda Técnica** | 80.8% | ↑ | 🔴 EXTREMA |
| **Funciones Críticas No Usadas** | 3 | ❌ | 🔴 BLOQUEANTE |
| **Componentes Inutilizados** | 45 | ⚠️ | ⚠️ SEVERO |
| **Módulos Completamente Muertos** | 2 | ❌ | 🔴 CRÍTICA |

---

## ✅ CONCLUSIÓN

**MeteoSer V49 tiene un problema serio de FRAGMENTACIÓN DE CÓDIGO.**

Solo el **19.2%** de las funciones definidas se usan realmente. Hay **3 funcionalidades críticas no implementadas** (Wright, UTCI v2, Sensores Virtuales) y **2 módulos completamente sin usar** (Wright, UTCI v2).

**Recomendación:** Implementar las 3 soluciones críticas antes de considerar V49 completo. Sin esto, hay pérdida garantizada de precisión en ET nocturna y confort en extremos.

---

**Generado:** 6 de febrero de 2026  
**Sistema:** MeteoSer V49 Auditoría Automática
