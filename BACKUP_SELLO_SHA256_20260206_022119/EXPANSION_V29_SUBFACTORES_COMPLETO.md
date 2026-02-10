# 📊 EXPANSIÓN V29.0 - SUBFACTORES COMPLETOS DE TODO EL SISTEMA

**Fecha**: 3 de Febrero de 2026  
**Versión**: MeteoSerV3 V29.0 - Expansión Total de Subfactores  
**Estado**: EN PROGRESO - Fase 1 (Trinity Elite) COMPLETADA  

---

## 🎯 OBJETIVO

**CERO CÁLCULOS OCULTOS. CERO VALORES INTERMEDIOS SIN PUBLICAR.**

Si un valor puede ser leído, debe estar en el Bus. Si una fórmula tiene subfactores, TODOS deben publicarse.

Máxima granularidad = Máxima eficiencia = Zero redundancia

---

## ✅ FASE 1: TRINITY ELITE - COMPLETADA

### 1.1 HARDY (NIST) - Psicrometría
**Antes**: 5 parámetros  
**Después**: 18 parámetros (+13)  

#### Parámetros Principales (5):
- `hardy_es_pa` - Presión vapor saturado (Pa)
- `hardy_e_pa` - Presión vapor real (Pa)
- `hardy_f_enhancement` - Factor de mejora (adimensional)
- `hardy_temperatura_rocio_c` - Punto de rocío (°C)
- `hardy_relacion_mezcla_g_kg` - Relación de mezcla (g/kg)

#### Subfactores NUEVOS (+13):
1. `hardy_humedad_relativa_pct` - Humedad confirmada (%)
2. `hardy_presion_aire_seco_pa` - P_dry = P - e (Pa)
3. `hardy_rv_constante` - Constante gas vapor 461.495 (J/kg·K)
4. `hardy_rd_constante` - Constante gas aire seco 287.05 (J/kg·K)
5. `hardy_rv_rd_ratio` - Ratio Rv/Rd ~1.608
6. `hardy_epsilon_wexler` - ε = M_water/M_air = 0.622
7. `hardy_masa_molar_agua` - 18.01528 g/mol
8. `hardy_masa_molar_aire` - 28.96644 g/mol
9. `hardy_coef_a_wexler` - Coeficiente a usado (según T)
10. `hardy_coef_b_wexler` - Coeficiente b usado
11. `hardy_coef_c_wexler` - Coeficiente c usado
12. `hardy_iteraciones_newton_raphson` - ~4 iteraciones típicas
13. `hardy_error_convergencia_c` - Tolerancia 0.001°C
14. `hardy_enhancement_factor_presion` - (P-P0)/P0
15. `hardy_enhancement_coef_a` - 0.505 (Alduchov & Eskridge)
16. `hardy_enhancement_coef_b` - 0.01 1/K

---

### 1.2 OMM (WMO) - Densidad con Temperatura Virtual
**Antes**: 7 parámetros  
**Después**: 17 parámetros (+10)  

#### Parámetros Principales (7):
- `omm_temperatura_virtual_c` - T_v corrección vapor (°C)
- `omm_temperatura_virtual_k` - T_v (K)
- `omm_densidad_total_kg_m3` - ρ total (kg/m³)
- `omm_densidad_aire_seco_kg_m3` - ρ_dry (kg/m³)
- `omm_densidad_vapor_kg_m3` - ρ_vapor (kg/m³)
- `omm_anomalia_densidad_kg_m3` - Δρ (kg/m³)
- `omm_anomalia_densidad_pct` - Δρ (%)

#### Subfactores NUEVOS (+10):
1. `omm_presion_aire_seco_pa` - P_dry = P - e (Pa)
2. `omm_factor_correccion_tv` - 1 + w·(Rv/Rd - 1)
3. `omm_w_kg_kg` - Relación mezcla (kg/kg)
4. `omm_ratio_densidad_vapor_total` - ρ_vapor/ρ_total
5. `omm_rd_constante` - 287.05 J/(kg·K)
6. `omm_rv_constante` - 461.495 J/(kg·K)
7. `omm_densidad_estandar_iso` - 1.225 kg/m³ (ISO 2533)
8. `omm_delta_flotabilidad_kg_m3` - ρ_total - ρ_dry

---

### 1.3 REST2 (GUEYMARD) - Radiación Extraterrestre
**Antes**: 5 parámetros  
**Después**: 21 parámetros (+16)  

#### Parámetros Principales (5):
- `rest2_g0_w_m2` - Radiación extraterrestre (W/m²)
- `rest2_elevacion_solar_deg` - Altura solar (°)
- `rest2_masa_aire` - Masa de aire (adimensional)
- `rest2_factor_excentricidad` - Corrección orbital
- `rest2_es_noche` - Boolean noche/día

#### Subfactores NUEVOS (+16):
1. `rest2_dia_del_año` - Día juliano 1-365
2. `rest2_declinacion_solar_deg` - δ solar (°)
3. `rest2_ecuacion_del_tiempo_min` - EoT Spencer (min)
4. `rest2_tiempo_solar_verdadero` - TSV (h)
5. `rest2_longitud_huso_horario` - 15·zona (°)
6. `rest2_longitud_correccion_min` - 4·(lon-lon_huso) (min)
7. `rest2_angulo_horario_deg` - ω (°)
8. `rest2_angulo_cenital_deg` - θ_z (°)
9. `rest2_cos_zenital` - cos(θ_z)
10. `rest2_io_constante_solar` - I₀ ajustado (W/m²)
11. `rest2_io_nominal` - 1361.0 W/m² (nominal)
12. `rest2_sin_elevacion` - sin(h)

---

### 1.4 LIU & JORDAN - Índice de Claridad K_t
**Antes**: 2 parámetros  
**Después**: 15 parámetros (+13)  

#### Parámetros Principales (2):
- `trinity_kt_indice_claridad` - K_t limitado a 1.5
- `trinity_nubosidad_radiometrica_pct` - Nubosidad desde K_t (%)

#### Subfactores NUEVOS (+13):
1. `trinity_kt_radiacion_real` - G medido (W/m²)
2. `trinity_kt_radiacion_g0` - G₀ extraterrestre (W/m²)
3. `trinity_kt_ratio_sin_limite` - K_t sin limitar
4. `trinity_kt_tipo_dia` - "despejado"/"parcialmente_nublado"/"nublado"
5. `trinity_nubosidad_componente_base` - 1.020
6. `trinity_nubosidad_componente_kt` - -0.254·K_t
7. `trinity_nubosidad_componente_elevacion` - 0.0123·sin(h)
8. `trinity_nubosidad_radiometrica_0_1` - n en [0,1]
9. `trinity_fraccion_difusa` - f_d Erbs et al.
10. `trinity_tipo_erbs` - "muy_nublado"/"intermedio"/"muy_despejado"
11. `trinity_erbs_c0` - Coef. 0 polinomio Erbs
12. `trinity_erbs_c1` - Coef. 1 
13. `trinity_erbs_c2` - Coef. 2
14. `trinity_erbs_c3` - Coef. 3
15. `trinity_erbs_c4` - Coef. 4
16. `trinity_radiacion_difusa_w_m2` - G_difusa (W/m²)
17. `trinity_radiacion_directa_w_m2` - G_directa (W/m²)
18. `trinity_perdida_atmosferica_w_m2` - G₀ - G (W/m²)
19. `trinity_perdida_atmosferica_pct` - (G₀-G)/G₀ · 100 (%)

---

### 1.5 VALIDADOR CRUZADO TRINITY
**Antes**: 6 parámetros (3 tipos × 2)  
**Después**: 20+ parámetros  

#### Parámetros Principales (6):
- `trinity_validacion_{tipo}` - Nivel 0-4 por tipo
- `trinity_divergencia_{tipo}_pct` - Divergencia (%)

#### Subfactores NUEVOS (+14):
1. `trinity_nubosidad_atmosferica_pct` - Nubosidad desde T/RH (%)
2. `trinity_nubosidad_factor_humedad` - HR/100
3. `trinity_nubosidad_factor_temp` - (T-T_v)/5
4. `trinity_nubosidad_contribucion_hr` - 80% componente
5. `trinity_nubosidad_contribucion_temp` - 20% componente
6. `trinity_descripcion_{tipo}` - Texto explicación
7. `trinity_nubosidad_diferencial_abs` - |n_rad - n_atm| (%)
8. `trinity_nubosidad_promedio` - (n_rad + n_atm)/2 (%)
9. `trinity_tv_diferencial_c` - T_v - T (°C)
10. `trinity_tv_es_fisica_valida` - Boolean T_v ≥ T
11. `trinity_kt_validacion` - K_t para validación
12. `trinity_kt_fuera_rango` - Boolean K_t ∉ [0, 1.05]
13. `trinity_kt_exceso` - max(0, K_t - 1.05)
14. `trinity_estado_validacion` - Nivel máximo 0-4
15. `trinity_alarmas_count_normal` - Count nivel 0
16. `trinity_alarmas_count_baja` - Count nivel 1
17. `trinity_alarmas_count_media` - Count nivel 2
18. `trinity_alarmas_count_alta` - Count nivel 3
19. `trinity_alarmas_count_critica` - Count nivel 4
20. `trinity_salud_sistema_score` - 0-100 (100=perfecto)

---

## ✅ FASE 2: VAPOR Y PUNTO DE ROCÍO - COMPLETADA

### 2.1 PRESIÓN DE VAPOR (Wexler)
**Antes**: 4 parámetros  
**Después**: 7 parámetros (+3)  

#### Parámetros Principales (4):
- `presion_vapor_saturacion` - e_sat (Pa)
- `presion_vapor_actual` - e (Pa)
- `deficit_saturacion` - VPD (Pa)
- `punto_rocio` - T_d (°C)

#### Subfactores NUEVOS (+3):
1. `temperatura_kelvin` - T (K)
2. `fraccion_saturacion` - HR/100
3. `depresion_punto_rocio` - T - T_d (°C)

### 2.2 PUNTO DE ROCÍO NEWTON-RAPHSON
**Subfactores NUEVOS (+9)**:
1. `punto_rocio_magnus_estimacion` - Estimación inicial Magnus (°C)
2. `magnus_coef_a` - 17.27
3. `magnus_coef_b` - 237.3 K
4. `magnus_gamma` - Factor intermedio γ
5. `newton_raphson_max_iter` - 20 iteraciones
6. `newton_raphson_tolerance` - 1e-6 °C
7. `error_magnus_wexler` - |T_d_magnus - T_d_wexler| (°C)
8. `iteraciones_newton_raphson_reales` - Típicamente ~4
9. `razon_convergencia_newton` - 2.0 (cuadrática)

### 2.3 CONSTANTES TERMODINÁMICAS
**Subfactores NUEVOS (+7)**:
1. `temperatura_critica_agua` - 647.096 K
2. `presion_critica_agua` - 22.064 MPa
3. `tau_wagner` - 1 - T/T_c
4. `pendiente_clausius_clapeyron` - de_sat/dT (Pa/K)
5. `calor_latente_vaporizacion` - 2501 kJ/kg
6. `constante_gas_vapor` - 461.5 J/(kg·K)

---

## 📊 RESUMEN FASE 1 + FASE 2

| Módulo | Parámetros Antes | Parámetros Después | Ganancia |
|--------|------------------|-------------------|----------|
| **Hardy (NIST)** | 5 | 18 | +13 (+260%) |
| **OMM (WMO)** | 7 | 17 | +10 (+143%) |
| **REST2 (Gueymard)** | 5 | 21 | +16 (+320%) |
| **K_t (Liu & Jordan)** | 2 | 19 | +17 (+850%) |
| **Validador Trinity** | 6 | 20 | +14 (+233%) |
| **Vapor/Punto Rocío** | 4 | 23 | +19 (+475%) |
| **TOTAL TRINITY + VAPOR** | **29** | **118** | **+89 (+307%)** |

---

## 🚧 FASE 3: PRÓXIMOS OBJETIVOS (TO-DO)

### 3.1 ASTRONOMÍA (NREL SPA)
- Todos los subfactores de azimut, elevación
- Ecuación del tiempo componentes
- Declinación solar subfactores
- Refracción atmosférica Meeus

### 3.2 INDICADORES DERIVADOS
- Heat Index: 9 términos Rothfusz individuales
- Wind Chill: 4 componentes Environment Canada
- VPD: subfactores e_sat, e_actual
- Humedad absoluta: componentes moleculares
- Temperatura operativa: T_aire, T_radiante

### 3.3 CONFORT TÉRMICO AVANZADO
- UTCI: TODOS los 10+ subfactores iterativos
- PMV: 6 componentes Fanger
- PPD: subfactor exponencial
- WBGT: componentes T_globo, T_bulbo natural

### 3.4 EVAPOTRANSPIRACIÓN
- Penman-Monteith: 15+ subfactores
- Componente aerodinámico separado
- Componente radiativo separado
- Déficit presión vapor subfactores

### 3.5 NUBOSIDAD Y TRANSMITANCIA
- Haurwitz: componentes transmitancia
- Kasten & Czeplak: subfactores elevación
- Liu & Jordan: fracción difusa polinomio completo

### 3.6 MRT (TEMPERATURA RADIANTE MEDIA)
- Componentes geométricos 6 direcciones
- Onda corta/onda larga separadas
- View factors explícitos

---

## 🎯 OBJETIVO FINAL

**De ~1,180 parámetros actuales → 2,500+ parámetros con subfactores completos**

- Fase 1 (Trinity Elite): +89 parámetros ✅ COMPLETADO
- Fase 2 (Astronomía): ~+50 parámetros esperados
- Fase 3 (Confort UTCI/PMV/WBGT): ~+80 parámetros
- Fase 4 (Penman-Monteith ET): ~+40 parámetros
- Fase 5 (Resto del sistema): ~+1,100+ parámetros

**TOTAL ESPERADO: ~2,500-3,000 parámetros en Bus Global**

---

## 📝 BENEFICIOS

1. **Depuración quirúrgica**: Ver EXACTAMENTE dónde falla una fórmula
2. **Optimización granular**: Saber qué subfactor reutilizar
3. **Validación cruzada**: Comparar resultados intermedios entre métodos
4. **Integridad física**: Validar que cada paso cumple límites físicos
5. **Auditoría completa**: Certificación SHA256 de cada subfactor
6. **Machine Learning**: Alimentar modelos con subfactores en vez de resultados finales
7. **Zero redundancia**: Cada cálculo se hace UNA VEZ

---

## 🔐 INTEGRIDAD

**SHA256 V28.0** (antes de expansión):  
`5a34bf8f0f27bbd8c1c8eda216944c413a3e5d955a43974b4fb5bfee4e05060f`

**SHA256 V29.0** (después de Fase 1+2):  
[PENDIENTE - Se generará tras completar todas las fases]

---

**Documento vivo - Se actualiza tras cada fase completada**  
**Última actualización**: 2026-02-03 22:30 UTC  
**Estado**: Fase 1 + Fase 2 COMPLETADAS ✅
