# TOP 20 PARÁMETROS DERIVADOS CON FÓRMULAS Y CONSUMIDORES

**Fecha**: 3 de febrero de 2026  
**Basado en**: INDEX_CATALOG + environmental_indices.py + módulos de cálculo

---

## RANKING DE DERIVADOS (por importancia + consumo del sistema)

### 1. PUNTO DE ROCÍO (Td)
**Categoría**: Meteorología  
**Sensores Base**: T, HR  
**Tipo**: Derivado (Wexler-Hyland NIST)

#### Fórmula
```
e_sat = saturacion_vapor_hyland_wexler(T_C, P_hPa)
e_actual = e_sat × (HR / 100)
T_d = Wexler⁻¹(e_actual)  [inversa aproximada]

Donde:
  e_sat = 100 × exp(
    -2.8365744 × 10³ × T_k⁻² 
    - 6.028076559 × 10³ × T_k⁻¹
    + 1.954348080 × 10¹
    - 2.737830188 × 10⁻² × T_k
    + 1.6261698 × 10⁷ × T_k²
    + 7.0229056 × 10⁻¹⁰ × T_k³
  )
```

**Requiere**: UTCI, PMV, sensación térmica, riesgo de helada, condensación, cetrería  
**Consumidores**: EnvironmentalIndices.punto_rocio() → bus → dashboard  

---

### 2. SENSACIÓN TÉRMICA (ST)
**Categoría**: Confort  
**Sensores Base**: T, HR, V  
**Tipo**: Derivado (Steadman 1984)

#### Fórmula
```
ST = T + (e_a - e_ref) × k1 - k2 × V - k3

Donde:
  k1 = 0.33 × (1 + 0.2 × I_cl)  [modulado por ropa]
  k2 = 0.70 / (1 + 0.15 × I_cl)
  k3 = 4.00 × (1 - 0.1 × I_cl)
  
  I_cl = 0.5 clo (verano)
  e_a = presion_vapor_actual (hPa)
  e_ref = presion_vapor_confort ≈ 12 hPa
  V = viento (m/s)
```

**Requiere**: Dashboard, alertas, recomendaciones  
**Consumidores**: EnvironmentalIndices.sensacion_termica() → cetrería  

---

### 3. UTCI (Universal Thermal Climate Index)
**Categoría**: Confort Térmico Profesional  
**Sensores Base**: T, HR, V@1.1m, Tmrt, P  
**Tipo**: Derivado (polinomio ISO 14505-2)

#### Fórmula Principal (Fiala-Höppe 2012)
```
UTCI = utci_polynomial(T_a, T_mrt, V_1.1m, VP, info_turbulencia, info_rayleigh)

Donde:
  T_a = temperatura aire (°C)
  T_mrt = temperatura radiante media (°C) ← CALC PROFESIONAL
  V_1.1m = viento a 1.1m (m/s) ← NORMALIZADO con ley logarítmica
  VP = presión vapor (hPa) ← Motor: Diamond_Refined_v1
  
Polinomio: ~8000 líneas de coeficientes ISO
```

#### Sub-fórmula: T_mrt (Temperatura Radiante Media - Höppe 1993)
```
T_mrt = (G_solar × f_svf × α / σε + T_sky) ^ 0.25

Donde:
  G_solar = radiación solar global (W/m²)
  f_svf = sky view factor (p.ej. 0.5 para calle)
  α = absortancia solar (0.7 para piel)
  σ = constante Stefan-Boltzmann (5.67e-8)
  ε = emitividad (0.95)
  T_sky = temperatura radiante cielo (K)
```

#### Sub-fórmula: Viento Normalizado (ISO 7726)
```
V(1.1m) = V_sensor × ln(1.1 / z0) / ln(z_sensor / z0)

Donde:
  z0 = rugosidad superficial (0.5m calle, 0.03m terraza)
  z_sensor = altura real del sensor
```

**Requiere**: Alertas, aplicaciones salud ocupacional, deportes  
**Consumidores**: EnvironmentalIndices.indice_utci() → MotorMotor de alertas  

---

### 4. WBGT (Wet Bulb Globe Temperature)
**Categoría**: Estrés Térmico Ocupacional  
**Sensores Base**: T, HR, Radiación, V  
**Tipo**: Derivado (Liljegren-Carhart 2008)

#### Fórmula
```
WBGT = 0.7 × T_wb + 0.2 × T_g + 0.1 × T_a

Donde:
  T_wb = temperatura de bulbo húmedo (°C)
  T_g = temperatura de globo (°C)
  T_a = temperatura del aire (°C)
```

#### Sub-fórmula: T_wb (sin psicrómetro)
```
e_actual = (HR / 100) × e_sat(T)
A = e_actual / P_atm
T_wb = T - (HR / 100) × (T - T_rocio) × (1 + 0.0016 × A)
```

#### Sub-fórmula: T_g (sin globo negro)
```
T_g = T + (Radiacion / 1000) × 12 - V × 0.5
T_g = clamp(T_g, T - 5, T + 20)  [validación física]
```

**Requiere**: Alertas ocupacionales, deportes, ejército  
**Consumidores**: MotorAlertas → dashboards corporativos  

---

### 5. PMV (Predicted Mean Vote)
**Categoría**: Confort Térmico Fanger  
**Sensores Base**: T, HR, V, Radiación  
**Tipo**: Derivado (Fanger 1972 + circadiano)

#### Fórmula Fanger Simplificada
```
PMV = (0.303 × e^(-0.036×M) + 0.0275) × (M - W - 3.05 × [5.73 - 0.007×M - VP] 
      - 3.05 × 0.42 × [M - W - 58.15] - 1.7 × 10^(-5) × M × (5867 - VP) 
      - 0.0014 × M × (34 - T_a) - [f_cl × h_c × (T_cl - T_a)])

Donde:
  M = tasa metabólica (1.2 met ≈ oficina)
  W = trabajo externo (≈0)
  VP = presión vapor (hPa)
  T_cl = temperatura piel estimada
  f_cl = factor ropa (≈1.0)
  h_c = coef. convección (W/m²K)
```

**Requiere**: Sistemas HVAC, edificios inteligentes  
**Consumidores**: EnvironmentalIndices.indice_pmv() → automatización  

---

### 6. VPD (Vapor Pressure Deficit)
**Categoría**: Aire  
**Sensores Base**: T, HR, P  
**Tipo**: Derivado (presión vapor)

#### Fórmula
```
VPD_kPa = (e_sat(T) - e_actual) / 1000

Donde:
  e_sat(T) = saturacion_vapor_hyland_wexler(T, P)  [Pa]
  e_actual = e_sat × (HR / 100)  [Pa]
  
Rango típico: 0.5-3.5 kPa (confort: ~1.5 kPa)
```

**Requiere**: Agricultura (riego), control de humedad  
**Consumidores**: MotorRiego → recomendaciones agua  

---

### 7. BULBO HÚMEDO (T_wb)
**Categoría**: Aire  
**Sensores Base**: T, HR  
**Tipo**: Derivado (Stull 2011)

#### Fórmula (Stull Approximation)
```
T_wb = T × arctan(0.151977 × √(HR + 8.313659)) 
       + arctan(T + HR) 
       - arctan(HR - 1.676331) 
       + 0.00391838 × HR^1.5 × arctan(0.023101 × HR) 
       - 4.686035

Donde: T en °C, HR en %
Precisión: ±0.5°C en rango 0-60°C
```

**Requiere**: WBGT, estrés térmico, agricultura  
**Consumidores**: WBGT → alertas ocupacionales  

---

### 8. EVAPOTRANSPIRACIÓN (ET₀)
**Categoría**: Hidrología  
**Sensores Base**: T, HR, Radiación, V, Presión  
**Tipo**: Derivado (FAO-56 Penman-Monteith)

#### Fórmula Completa
```
ET₀ = [0.408 × Δ × (Rn - G) + γ × (900/(T+273)) × u₂ × (es - ea)] 
      / [Δ + γ × (1 + 0.34 × u₂)]

Donde:
  Δ = pendiente curva saturación (kPa/°C)
  Rn = radiación neta (MJ/m²/día)
  G = flujo calor suelo (MJ/m²/día) ≈ 0 (simplif.)
  γ = constante psicrométrica (0.67 kPa/°C)
  u₂ = viento a 2m (m/s)
  es = presión vapor saturada (hPa)
  ea = presión vapor actual (hPa)
```

**Requiere**: Riego inteligente, agricultura  
**Consumidores**: MotorRiego.analizar() → recomendaciones  

---

### 9. HUMEDAD ABSOLUTA (Ha)
**Categoría**: Aire  
**Sensores Base**: T, HR, P  
**Tipo**: Derivado (Hyland-Wexler)

#### Fórmula
```
Ha_g_m3 = (q × ρ_aire) / 1000

Donde:
  q = humedad específica (kg_vapor/kg_aire)
  ρ_aire = densidad aire (kg/m³) por CIPM-2007
  
q = (0.622 × e_actual) / (P - 0.378 × e_actual)
  e_actual = (HR/100) × e_sat(T)
```

**Requiere**: Sistemas aire, conservación, laboratorios  
**Consumidores**: EnvironmentalIndices.indice_humedad_absoluta() → control  

---

### 10. RIESGO DE HELADA (Frost Risk)
**Categoría**: Meteorología  
**Sensores Base**: T, HR, Radiación, V  
**Tipo**: Derivado (Snyder 1985)

#### Fórmula
```
T_min_suelo = T_aire - (radiacion_neta / (h_c × A))

Donde:
  radiacion_neta = G × (1 - α) - ε × σ × T_k^4
  h_c = 5.6 + 4.1 × V  [W/m²K]  (Crawley)
  
Si T_min_suelo ≤ 0°C:
  riesgo_helada = 1.0
Sino:
  riesgo_helada = max(0, (T_rocio - T_min_suelo) / 3)  [escala 0-1]
```

**Requiere**: Agricultura, alertas meteorológicas  
**Consumidores**: MotorAlertas → alertas helada  

---

### 11. NUBOSIDAD ESTIMADA (C_est)
**Categoría**: Meteorología  
**Sensores Base**: Radiación, T, HR, V  
**Tipo**: Derivado (Ineichen-Perez)

#### Fórmula
```
C_est = 1 - (G_real / G_teorica)

Donde:
  G_real = radiación medida (W/m²)
  G_teorica = radiación extraterrestre corregida por altura solar
            = I₀ × cos(Z) × τ_rayleigh × τ_ozone × τ_water
  
τ_rayleigh ≈ 0.4 (cielo claro)
τ_ozone = 0.95
τ_water depende de PWV
```

**Requiere**: UTCI, pronósticos, cetrería  
**Consumidores**: EnvironmentalIndices → Dashboard  

---

### 12. ÍNDICE UV (UV)
**Categoría**: Radiación  
**Sensores Base**: UV (directo) o Radiación (indirecto)  
**Tipo**: Híbrido

#### Fórmula (si es radiación)
```
UV_index ≈ (G_solar / G_ref) × UV_base

Donde:
  G_solar = radiación global medida (W/m²)
  G_ref = radiación referencia cielo claro (≈1000 W/m²)
  UV_base = 13 (máximo típico)
  
Si hay sensor UV directo:
  UV_index = UV_sensor (lectura directa)
```

**Requiere**: Alertas salud, protección solar  
**Consumidores**: Dashboard → recomendaciones  

---

### 13. VISIBILIDAD LOCAL (Vis)
**Categoría**: Meteorología  
**Sensores Base**: T, HR, Nubosidad, Radiación  
**Tipo**: Derivado (Bucholtz-Rayleigh)

#### Fórmula Profesional
```
Vis = -ln(τ_visual) / β

Donde:
  τ_visual = transmitancia visible (0-1)
  β = coeficiente extinción (Rayleigh + aerosol)
  
τ_visual = τ_Rayleigh × τ_Mie × τ_Ozone × τ_H2O

τ_Mie depende de HR (higroscopicidad)
Rango: Vis = 10km (claro) a 200m (niebla densa)
```

**Requiere**: Cetrería, navegación, alertas  
**Consumidores**: cetreria_indices.visibilidad_terreno()  

---

### 14. PRESIÓN DE VAPOR (VP)
**Categoría**: Aire  
**Sensores Base**: T, HR  
**Tipo**: Derivado

#### Fórmula
```
VP_hPa = (HR / 100) × saturacion_vapor_hyland_wexler(T, P)

Hyland-Wexler (NIST):
  log₁₀(VP_Pa) = A₁ + A₂×T + A₃×T² + A₄×T³ + A₅×log₁₀(T)

Donde A₁...A₅ son coeficientes NIST para agua/hielo
```

**Requiere**: UTCI, Penman-Monteith, psicrometría  
**Consumidores**: utci_polynomial() → cálculos termodinámicos  

---

### 15. ENTALPÍA DEL AIRE (h)
**Categoría**: Aire  
**Sensores Base**: T, HR, P  
**Tipo**: Derivado

#### Fórmula
```
h = cp_a × T + q × (L_v + cp_v × T)

Donde:
  cp_a = 1004.67 J/kg/K (aire seco)
  cp_v = 1850 J/kg/K (vapor)
  L_v = 2.501e6 - 2370×T (calor latente, J/kg)
  q = humedad específica (kg/kg)
  
Unidad: kJ/kg (aire húmedo)
```

**Requiere**: Diagramas psicrométricos, HVAC  
**Consumidores**: EnvironmentalIndices.indice_entalpia()  

---

### 16. RIESGO DE LLUVIA (RiskRain)
**Categoría**: Meteorología  
**Sensores Base**: HR, lluvia, presión, radiación  
**Tipo**: Derivado (Clausius-Clapeyron)

#### Fórmula
```
PWV = (1 / (g × ρ_w)) × ∫ e(T) × RH / M dz

P(precip_next_1h) = f(PWV, dP/dt, nubosidad, UV)

Donde:
  PWV = precipitable water vapor (mm)
  g = 9.81 m/s²
  ρ_w = 1000 kg/m³
  dP/dt = tendencia presión (hPa/h)
  
Si PWV > 30mm Y dP/dt < -1.0 hPa/h:
  Riesgo_lluvia = 70% +
```

**Requiere**: Alertas, predicciones locales  
**Consumidores**: MotorAlertas.analizar()  

---

### 17. TENDENCIA PRESIÓN (dP/dt)
**Categoría**: Tendencias  
**Sensores Base**: Presión (histórico 1h)  
**Tipo**: Derivado

#### Fórmula
```
dP/dt = (P_actual - P_1h_atras) / 3600 [hPa/s]

Interpretación:
  dP/dt < -1.0 hPa/h → baja rápida (tormenta próxima)
  dP/dt > +1.0 hPa/h → sube rápida (frente frío/cálido)
  |dP/dt| < 0.5 hPa/h → estable
```

**Requiere**: Alertas meteorológicas, predicciones  
**Consumidores**: MotorAlertas → tendencia_presion()  

---

### 18. VIENTO CETRERÍA (V_cetreria)
**Categoría**: Cetrería  
**Sensores Base**: V, rachas  
**Tipo**: Derivado (índice especializado)

#### Fórmula
```
V_cetreria = max(V_medio, V_rachas) × factor_direccion

Donde:
  factor_direccion = 1.0 (norte) → 0.7 (sur)
  
Interpretación (escala 0-100):
  V_cetreria < 5 m/s → Excelente
  5-10 m/s → Bueno
  10-15 m/s → Marginal
  > 15 m/s → Peligroso
```

**Requiere**: Cetrería, deportes extremos  
**Consumidores**: cetreria_indices.viento_cetreria()  

---

### 19. ÍNDICE DE CONFORT GENERAL (Comfort_Gen)
**Categoría**: Confort Compuesto  
**Sensores Base**: T_int, HR_int, CO₂  
**Tipo**: Derivado (fusión ponderada)

#### Fórmula
```
Comfort_Gen = 0.4 × factor_T + 0.3 × factor_HR + 0.3 × factor_CO2

Donde:
  factor_T = clamp(100 - |T_int - 21| × 5, 0, 100)  [rango ideal 19-23°C]
  factor_HR = clamp(100 - |HR_int - 50| × 3, 0, 100)  [rango ideal 40-60%]
  factor_CO2 = clamp(100 - (CO2 - 400) / 10, 0, 100)  [límite 1000 ppm]
  
Resultado: 0-100 (100=óptimo)
```

**Requiere**: Dashboard, automatización inteligente  
**Consumidores**: EnvironmentalIndices.confort_general() → recomendaciones  

---

### 20. RIESGO DE MOHO (Mold_Risk)
**Categoría**: Edificio  
**Sensores Base**: HR_int, T_int, histórico  
**Tipo**: Derivado (indicador de tiempo)

#### Fórmula
```
Mold_Risk = f(HR_media_24h, tiempo_HR>65%, T_int)

Si HR > 65% por > 12h continuas:
  Mold_Risk = (tiempo_h - 12) × 0.05  [0-1 escala]
  
Si T_int < 15°C Y HR > 70%:
  Mold_Risk += 0.2  [factor condensación]
  
Mold_Risk = clamp(Mold_Risk, 0, 1)

Interpretación:
  < 0.2 → Sin riesgo
  0.2-0.4 → Riesgo bajo
  0.4-0.6 → Riesgo moderado
  > 0.6 → Riesgo alto (ALERTA)
```

**Requiere**: Alertas de salud, recomendaciones ventilación  
**Consumidores**: EnvironmentalIndices.riesgo_moho() → alertas  

---

## TABLA RESUMEN: CONSUMIDORES Y PUBLICACIÓN

| Derivado | Fórmula Principal | Consumidor Primario | Publicación Bus |
|----------|------------------|-------------------|-----------------|
| 1. Punto Rocío | Wexler-NIST | UTCI, PMV, helada | ✅ SI |
| 2. Sensación Térmica | Steadman 1984 | Dashboard, cetrería | ✅ SI |
| 3. UTCI | ISO 14505-2 | Alertas, deportes | ✅ SI |
| 4. WBGT | Liljegren 2008 | Alertas ocupacionales | ✅ SI |
| 5. PMV | Fanger 1972 | Sistemas HVAC | ✅ SI |
| 6. VPD | Vapor balance | Riego inteligente | ✅ SI |
| 7. Bulbo Húmedo | Stull 2011 | WBGT, psicrometría | ✅ SI |
| 8. ET₀ (Riego) | FAO-56 PM | Automatización riego | ✅ SI |
| 9. Humedad Absoluta | CIPM-2007 | Control calidad aire | ✅ SI |
| 10. Riesgo Helada | Snyder 1985 | Alertas agrícolas | ✅ SI |
| 11. Nubosidad Est. | Ineichen 2006 | Cetrería, pronósticos | ✅ SI |
| 12. Índice UV | Radiación/directo | Alertas salud | ✅ SI |
| 13. Visibilidad | Bucholtz-Rayleigh | Cetrería, aviación | ✅ SI |
| 14. Presión Vapor | Hyland-Wexler | Psicrometría | ✅ SI |
| 15. Entalpía | Termodinámica | Diagramas HVAC | ✅ SI |
| 16. Riesgo Lluvia | Clausius-Clapeyron | Alertas | ✅ SI |
| 17. Tendencia P | Diferencial | Pronósticos | ✅ SI |
| 18. Viento Cetrería | Especializado | Deportes extremos | ✅ SI |
| 19. Confort General | Fusión ponderada | Dashboard inteligente | ✅ SI |
| 20. Riesgo Moho | Temporal | Alertas salud edificio | ✅ SI |

---

## NOTAS TÉCNICAS

### Motor de Cálculo Unificado
- **Diamond_Refined_v1**: Presión vapor exacta (Hyland-Wexler + Greenspan)
- **CIPM-2007**: Densidad aire con virial
- **ISO 7726**: Normalización viento logarítmica
- **ISO 14505-2**: Polinomio UTCI profesional

### Validaciones Aplicadas
- Rango de temperatura: -40°C a +60°C
- Rango humedad: 0-100%
- Coherencia: T_rocio ≤ T_actual SIEMPRE

### Jerarquía de Dependencias
```
Sensores base (Top 5) 
  ↓
Derivados Tier 1 (Punto rocío, VPD, bulbo húmedo)
  ↓
Derivados Tier 2 (UTCI, WBGT, PMV)
  ↓
Derivados Tier 3 (Índices compuestos, alertas)
```

---

**Generado por**: CIERRE_INGENIERIA_V30_0.py  
**Última actualización**: 3 FEB 2026 10:15 UTC  
**Certificado**: SHA256 en `sha256_v30_0.txt`
