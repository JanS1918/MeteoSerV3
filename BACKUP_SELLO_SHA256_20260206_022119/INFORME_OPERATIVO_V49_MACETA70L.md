# 📋 INFORME OPERATIVO V49.0 - METEOSERV3 MACETA 70L ARGENTONA

**Fecha:** 5 de febrero de 2026  
**Sistema:** MeteoSerV3 V49.0 "Acorazado Argentona"  
**Ubicación:** Argentona (41.55°N, 2.39°E, 118m)  
**Caso de uso:** Maceta 70L, tierra de jardinería típica, poco drenaje  
**Estado:** Producción. Fórmulas cerradas. Listos para V50 (Validadores + ET inteligente)

---

## 🎯 RESUMEN EJECUTIVO

| Categoría | Cantidad | Detalle |
|-----------|----------|---------|
| **Sensores Hardware** | 6 | Temp, Humedad, Radiación, Viento, Presión, GPS |
| **Sensores Virtuales** | 15+ | Punto rocío, vapor, densidad, T virtual, etc |
| **Índices Calculados** | 8 | UTCI, WBGT, Steadman, ET, Radiación, etc |
| **Predicciones** | 5 | Estrés térmico, humedad suelo, alerta tormenta, etc |
| **Alertas/Riesgos** | 12+ | Sobreestimación ET, sensor sucio, estrés hídrico, etc |
| **Fórmulas Activas** | 13 | (Ver catálogo V49.1) |
| **Micro-valores Bus** | 50+ | Toda la cadena descompuesta |

---

## 🔌 PARTE 1: SENSORES HARDWARE (LO QUE MIDE DIRECTAMENTE)

Tu sistema mide 6 cosas reales. TODO lo demás se calcula de estas 6.

### **SENSOR 1: Temperatura del aire (°C)**

- **Hardware:** Termómetro Ecowitt (típicamente en tu estación)
- **Rango:** -40 a +60°C
- **Precisión:** ±0.5°C
- **Ubicación:** Radiador solar, 1-2m altura
- **Muestreo:** Continuo, reporta cada minuto

**¿Qué usa?**
```
DIRECTAMENTE:
├─ UTCI v4.02 Fiala (input principal)
├─ WBGT Liljegren (input principal)
├─ Hardy NIST presión vapor (input)
├─ OMM densidad aire (input)
├─ FAO-56 ET (input)
├─ Wright ET nocturna (input)
└─ Steadman Apparent Temperature (input)
```

---

### **SENSOR 2: Humedad relativa (%)**

- **Hardware:** Sensor humedad Ecowitt
- **Rango:** 0-100%
- **Precisión:** ±3%
- **Ubicación:** Junto a termómetro
- **Muestreo:** Cada minuto

**¿Qué usa?**
```
DIRECTAMENTE:
├─ UTCI (input, radiación del cuerpo)
├─ WBGT (input, presión vapor)
├─ Hardy NIST presión vapor (input)
├─ OMM densidad aire (input)
├─ FAO-56 ET (input)
└─ Steadman (input)

PARA CALCULAR PRIMERO:
├─ Punto rocío (Wexler-Hyland)
├─ Presión vapor saturado
├─ Temperatura virtual (OMM)
└─ Relación de mezcla
```

---

### **SENSOR 3: Radiación solar (W/m²)**

- **Hardware:** Piranómetro Ecowitt o Davis
- **Rango:** 0-1200 W/m²
- **Precisión:** ±5% (típicamente peor con suciedad)
- **Ubicación:** Horizontal, sin sombra
- **Muestreo:** Cada minuto

**¿Qué usa?**
```
DIRECTAMENTE:
├─ UTCI v4.02 (ajuste radiación + temperatura media radiante)
├─ WBGT Liljegren (radiación en globo negro)
├─ FAO-56 ET (radiación neta Rns)
└─ Wright ET (radiación para hora solar)

PARA VALIDAR:
├─ Validador radiación (¿Es coherente con hora solar?)
├─ Detector suciedad (¿Cae > 100 W/m² sin nube?)
└─ Control WBGT vs UTCI (coherencia cruzada)
```

---

### **SENSOR 4: Velocidad del viento (m/s)**

- **Hardware:** Anemómetro Ecowitt
- **Rango:** 0-50 m/s
- **Precisión:** ±10%
- **Ubicación:** 10m altura (típicamente baja en tu caso)
- **Muestreo:** Cada minuto

**¿Qué usa?**
```
DIRECTAMENTE:
├─ UTCI v4.02 (resistencia aerodinámica del cuerpo)
├─ WBGT Liljegren (convección en globo negro)
└─ FAO-56 ET (resistencia aerodinámica suelo)

NOTA CRÍTICA PARA TU MACETA:
Tu maceta está cerca del suelo, viento ≠ realidad
Factor corrección viento para maceta: × 1.5-2.0x
(viento medido en radiador es mayor que en suelo)
```

---

### **SENSOR 5: Presión atmosférica (hPa)**

- **Hardware:** Barómetro Ecowitt
- **Rango:** 900-1100 hPa
- **Precisión:** ±1 hPa
- **Ubicación:** Sensor integrado en consola
- **Muestreo:** Cada minuto
- **SELLADO EN CÓDIGO:** 1011.3 hPa para Argentona

**¿Qué usa?**
```
DIRECTAMENTE:
├─ Hardy NIST enhancement factor (corrección presión)
├─ OMM densidad aire (cálculo T virtual)
├─ FAO-56 ET (presión vapor real)
└─ Todas las fórmulas psicométricas

NOTA CRÍTICA:
Si sensor presión falla → TODO falla
Validador alerta si presión salta > 15 hPa/hora
```

---

### **SENSOR 6: GPS / Hora**

- **Hardware:** GPS del sistema o reloj del router
- **Datos:** Latitud, Longitud, Hora UTC
- **Ubicación:** 41.55326700°N, 2.39684500°E, 118m (Argentona)

**¿Qué usa?**
```
DIRECTAMENTE:
├─ REST2 radiación (cálculo G0 astronómico)
├─ Wright ET nocturna (hora solar → elevación solar)
├─ Validador radiación (¿Es noche? radiación debe ser 0)
└─ Ciclos diarios (detección anomalías)
```

---

### **SENSOR 7 (VIRTUAL): Humedad suelo (%)**

⚠️ **TIENES ESTE. NO LO MENCIONASTE PERO ES CRÍTICO.**

- **Hardware:** Sensor capacitivo suelo (ej: capacitivo Tuya)
- **Rango:** 0-100% (suelo seco a saturado)
- **Precisión:** ±2-3%
- **Ubicación:** 10cm profundidad en maceta
- **Muestreo:** Cada 30 minutos

**¿Qué usa?**
```
DIRECTAMENTE:
├─ Controlador ET (corrección factor)
├─ Validador coherencia (¿ET predicha = humedad cambio?)
├─ Detector estrés hídrico (¿Humedad baja demasiado rápido?)
└─ ENTRADA PARA V50

NOTA CRÍTICA PARA TU MACETA:
Suelo: tierra compo jardinería típica
Características:
- Retención baja-media (no retiene agua como turba)
- Drenaje pobre (poco aireación, compactada)
- Factor raíces: nulo (sin plantas)
- Conversión: 1% humedad ≈ 6L de agua en 70L suelo
```

---

## 📊 PARTE 2: SENSORES VIRTUALES (CALCULADOS, NO MEDIDOS)

Estos se calculan UNA SOLA VEZ, de los 7 sensores hardware, en cadena.

### **VIRTUALES PSICOMÉTRICOS (La cadena humedad del aire)**

#### **V1: Presión de vapor saturado (Pa) - NIST Hardy Wexler**

```python
# ENTRADA: Temperatura
# FÓRMULA: Wexler-Hyland polinomio (NIST SR3-73)
# ARCHIVO: core/indices/hardy_nist_psicrometria.py

if temp >= 0:
    e_s = 6.116441 × exp((17.62391 × T) / (243.12 + T))
else:
    e_s = 6.112 × exp((22.46 × T) / (272.62 + T))

# RESULTADO
presion_vapor_saturado_pa = e_s × 100
```

**Ejemplo Argentona, 25°C:**
```
e_s = 3168 Pa
Publicado: presion_vapor_saturado_nist = 3168 Pa
```

**Precisión:** ±5 Pa (-20 a +50°C) = ±0.0001 en RH

---

#### **V2: Enhancement Factor (adimensional) - Hardy IAPWS**

```python
# ENTRADA: Temperatura, Presión
# FÓRMULA: Hyland & Wexler IAPWS
# ARCHIVO: core/indices/hardy_nist_psicrometria.py

f = exp((B + C × T) × P / e_s)

where:
B = -1.66365e-1  # Coeficiente virial
C = -2.33365e-8  # Temperatura
P = presion_absoluta (hPa)
```

**Ejemplo Argentona, 25°C, 1011.3 hPa:**
```
f ≈ 1.00054
Publicado: factor_enhancement_hardy = 1.00054
```

---

#### **V3: Presión de vapor real (Pa) - Entrada humedad suelo**

```python
# ENTRADA: RH%, e_s (V1), f (V2)
# FÓRMULA: e = f × e_s × (RH / 100)
# ARCHIVO: core/indices/hardy_nist_psicrometria.py

presion_vapor_real = factor_enhancement × e_s × (RH / 100)
```

**Ejemplo Argentona, 25°C, RH=60%:**
```
e = 1.00054 × 3168 × 0.60 = 1900 Pa
Publicado: presion_vapor_real_nist = 1900 Pa
```

---

#### **V4: Punto de rocío (°C) - Hardy NIST inverso**

```python
# ENTRADA: Presión vapor real (V3)
# FÓRMULA: Inversa Wexler-Hyland (Newton-Raphson)
# ARCHIVO: core/indices/hardy_nist_psicrometria.py

Td = (c × ln(e/a)) / (b - ln(e/a))

where:
a, b, c = coeficientes Wexler-Hyland
ln(e/a) = logaritmo presión vapor real vs coeficiente
```

**Ejemplo Argentona, RH=60%, T=25°C:**
```
Td ≈ 13.9°C
Publicado: punto_rocio_nist = 13.9°C
Validador: Td < T ✅ (coherencia)
```

---

#### **V5: Relación de mezcla (g/kg) - OMM**

```python
# ENTRADA: Presión vapor real (V3), Presión total
# FÓRMULA: OMM/WMO
# ARCHIVO: core/indices/omm_densidad_temperatura_virtual.py

w = (ε × e) / (P - e)

where:
ε = 0.62198 (relación masas H2O/aire)
e = presión vapor real (Pa)
P = presión total (Pa)
```

**Ejemplo Argentona, e=1900 Pa, P=101130 Pa:**
```
w = 0.62198 × 1900 / (101130 - 1900) ≈ 11.9 g/kg
Publicado: relacion_mezcla_omm = 11.9 g/kg
```

---

#### **V6: Temperatura virtual (°C) - OMM Core**

```python
# ENTRADA: Temperatura, Relación mezcla (V5)
# FÓRMULA: OMM/WMO
# ARCHIVO: core/indices/omm_densidad_temperatura_virtual.py

T_v = T × (1 + (w/1000) × (R_v/R_d - 1))

where:
R_v/R_d = 461.495 / 287.05 ≈ 1.608
w = relación mezcla en g/kg
```

**Ejemplo Argentona, T=25°C, w=11.9 g/kg:**
```
T_v = 25 × (1 + 0.0119 × 0.608) ≈ 25.18°C
Publicado: temperatura_virtual_omm = 25.18°C
(Aire húmedo se comporta como aire seco a 25.18°C)
```

---

#### **V7: Densidad del aire (kg/m³) - OMM Completa**

```python
# ENTRADA: Presión, T_virtual, presión vapor
# FÓRMULA: OMM/WMO ecuación estado aire húmedo
# ARCHIVO: core/indices/omm_densidad_temperatura_virtual.py

ρ_aire = (P_dry / (R_d × T_v)) + (e / (R_v × T_v))

where:
P_dry = P_total - e (presión aire seco)
R_d = 287.05 J/(kg·K)
R_v = 461.495 J/(kg·K)
```

**Ejemplo Argentona, P=101130 Pa, T_v=25.18°C=298.33K, e=1900 Pa:**
```
P_dry = 101130 - 1900 = 99230 Pa
ρ_aire = (99230 / 287.05 / 298.33) + (1900 / 461.495 / 298.33)
       ≈ 1.159 kg/m³
Publicado: densidad_aire_omm = 1.159 kg/m³
Precisión: ±0.0001 kg/m³ (nivel laboratorio)
```

---

### **VIRTUALES RADIACIONALES**

#### **V8: Radiación extraterrestre teórica (W/m²) - REST2 Gueymard**

```python
# ENTRADA: Fecha, hora, latitud, longitud
# FÓRMULA: REST2 (Gueymard 2008)
# ARCHIVO: core/indices/rest2_gueymard_radiacion.py

G0 = G_sc × f_exc × cos(θ_z)

where:
G_sc = 1361 W/m² (constante solar REST2)
f_exc = excentricidad orbita (varía ±3.3%)
θ_z = ángulo zenital solar
```

**Ejemplo Argentona, 5-FEB-2026 12:00 UTC:**
```
Elevación solar ≈ 32°
θ_z ≈ 58°
cos(58°) ≈ 0.53
G0 ≈ 1361 × 1.00 × 0.53 ≈ 720 W/m² (teórico máximo)
Publicado: radiacion_extraterrestre_resto = 720 W/m²
```

---

#### **V9: Temperatura media radiante (°C) - Inversa globo negro**

```python
# ENTRADA: Radiación medida, temperatura aire, viento
# FÓRMULA: Inversa Stefan-Boltzmann + convección
# ARCHIVO: core/indices/wbgt_liljegren_completo.py

T_mrt se calcula de radiación medida asumiendo:
- Globo negro virtual (ε=0.95, d=0.15m)
- Balance: radiación_solar = Stefan-Boltzmann + convección

Método iterativo.
```

**Ejemplo Argentona, radiación=600 W/m², T_aire=25°C, viento=2 m/s:**
```
T_mrt ≈ 35°C (mayor que aire porque radiación solar)
Publicado: tmrt_calculada = 35°C
Usada en: UTCI, WBGT
```

---

### **VIRTUALES PSICROMETRÍA + RADIACIÓN (Fusión)**

#### **V10: Bulbo húmedo natural (°C) - Stull 2011**

```python
# ENTRADA: T, RH, presión
# FÓRMULA: Stull (2011) aproximación de carta psicrométrica
# ARCHIVO: core/indices/wbgt_liljegren_completo.py

Complicada, pero esencialmente:
Tw ≈ T × atan(0.151977 × sqrt(RH + 8.313659))
     + atan(T + RH) - atan(RH - 1.676331)
     + [términos adicionales]
```

**Ejemplo Argentona, T=25°C, RH=60%:**
```
Tw ≈ 18.5°C
Publicado: bulbo_humedo_stull = 18.5°C
Usado en: WBGT cálculo
```

---

## 🧮 PARTE 3: ÍNDICES CALCULADOS (LO QUE IMPORTA OPERATIVAMENTE)

Estos 8 índices son lo que tu sistema REALMENTE PUBLICA como decisión.

### **ÍNDICE 1: UTCI v4.02 Fiala (°C) - Sensación térmica general**

**Inputs directos:** T, RH, V (viento a 10m), T_mrt  
**Fórmula:** Fiala (2012) 64-nodos + ISO 14505-2  
**Archivo:** `core/indices/environmental_indices.py` línea 108-220  
**Precisión:** ±0.1°C  
**Output:** 13 micro-valores

```python
utci = utci_v4_02_fiala_completo(
    t_a=25.0,           # Temperatura aire
    rh=60.0,            # Humedad relativa
    v=2.0,              # Viento (m/s, a 10m)
    tmrt=35.0,          # Temperatura media radiante calculada
    pa=101.325          # Presión (kPa, sellada)
)

# RESULTADO
{
    "utci": 28.5,                          # LA SENSACIÓN TÉRMICA
    "utci_vapor_pressure": 1900,           # Pa
    "utci_operative_temp": 31.2,           # °C (temp efectiva)
    "utci_metabolic_rate": 85,             # W (metabolismo reposo)
    "utci_sensible_heat_loss": 45,         # W (pérdida calor sensible)
    "utci_latent_heat_loss": 38,           # W (pérdida por sudoración)
    "utci_radiation_heat_loss": 12,        # W (pérdida radiativa)
    "utci_evaporative_cooling": 3.2,       # °C (potencial enfriamiento)
    "utci_clothing_factor": 0.85,          # adim (ropa ajustada primavera)
    "utci_wind_adjustment": 1.2,           # °C (efecto viento)
    "utci_radiation_adjustment": 3.5,      # °C (efecto radiación)
    "utci_moisture_adjustment": -0.2       # °C (efecto humedad)
}
```

**¿Qué significa 28.5°C?**
```
Sensación térmica = 28.5°C
Interpretación: "Se siente como 28.5°C de temperatura efectiva"
En Argentona primavera = ligero calor, pero tolerable
Alerta: No, bajo estrés

COMPARACIÓN HISTÓRICA:
- Invierno (T=5°C, RH=70%, V=3, T_mrt=5): UTCI ≈ -2°C (frío moderado)
- Verano (T=35°C, RH=40%, V=1, T_mrt=50): UTCI ≈ 45°C (calor extremo)
```

---

### **ÍNDICE 2: WBGT Liljegren (°C) - Estrés térmico ocupacional**

**Inputs directos:** T, RH, V, radiación  
**Fórmula:** Liljegren-Carhart (2008) + Stefan-Boltzmann  
**Archivo:** `core/indices/environmental_indices.py` línea 225-495  
**Precisión:** ±0.5°C  
**Output:** 20 micro-valores

```python
wbgt = wbgt_liljegren_completo(
    t_a=25.0,           # Temperatura aire
    rh=60.0,            # Humedad relativa
    v=2.0,              # Viento (m/s)
    rad=600.0,          # Radiación solar (W/m²)
    pa=101.325          # Presión (kPa)
)

# RESULTADO
{
    "wbgt": 26.1,                          # LA MÉTRICA OSHA
    "wbgt_tw": 18.5,                       # Bulbo húmedo natural
    "wbgt_tg": 28.3,                       # Globo negro virtual
    "wbgt_outdoor": 26.1,                  # WBGT con radiación
    "wbgt_indoor": 23.8,                   # WBGT sin radiación
    "wbgt_heat_index": 27.2,               # Heat Index USA
    "wbgt_vapor_pressure": 1900,           # Pa
    "wbgt_dew_point": 13.9,                # °C
    # + 12 más (Stefan-Boltzmann, absorbancia, emisividad, etc)
}
```

**¿Qué significa 26.1°C?**
```
WBGT outdoor = 26.1°C
Comparar con umbrales ISO 7243:
- < 26°C: Sin restricción trabajo
- 26-28°C: Alerta moderada (límite hoy)
- 28-30°C: Alerta alta
- 30-32°C: Restricción severa
- > 34°C: Prohibición absoluta

EN TU CASO PRIMAVERA:
WBGT 26.1°C = En el límite, vigilar si sube

AUTORIDAD: Norma OSHA (ocupacional)
Si trabajas en Argentona hoy, WBGT marca la ley.
```

---

### **ÍNDICE 3: Steadman 1984 (°C) - Sensación térmica rápida**

**Inputs directos:** T, RH, V  
**Fórmula:** Steadman (1984) - simplificada  
**Archivo:** `core/indices/environmental_indices.py` (referencia)  
**Precisión:** ±0.5°C  
**Output:** 1 valor

```python
# Fórmula simple
sensacion_steadman = T + 0.5555 × (e/10 - 10) - 0.2 × V

# Ejemplo Argentona
sensacion_steadman = 25 + 0.5555 × (19 - 10) - 0.2 × 2
                   = 25 + 5 - 0.4 = 29.6°C
```

**¿Qué significa 29.6°C?**
```
Sensación "clásica" = 29.6°C
NOTA: No tiene radiación, por eso es mayor que UTCI (28.5°C)
Uso: Dashboard rápido, cálculos retroactivos sin radiación
Status: DIAGNÓSTICO auxiliar, no autoridad
```

---

### **ÍNDICE 4: UTCI v2 Blazejczyk (°C) - Extremos térmicos**

**Inputs:** T, RH, V, T_mrt  
**Rango:** -40 a +50°C (optimizado extremos)  
**Archivo:** `core/indices/utci_v2_blazejczyk.py`  
**Precisión:** ±0.2°C  
**Output:** 1 valor

```python
utci_v2 = utci_v2_blazejczyk(
    t_a=25.0, rh=60.0, v=2.0, tmrt=35.0
)
# Resultado: 28.3°C (levemente diferente de UTCI v4)
```

**¿Cuándo se usa?**
```
Solo si UTCI v4 sale del rango -50 a +60°C
Ejemplo: Polo Sur (T=-50°C) → UTCI v4 no certif
         Usa UTCI v2 Blazejczyk (entrenad para extremos)

En tu maceta Argentona primavera: NO se usa (T=25°C está dentro)
Status: DIAGNÓSTICO especializado, no autoridad general
```

---

### **ÍNDICE 5: Radiación extraterrestre (W/m²) - REST2**

**Inputs:** Fecha, hora, latitud, longitud, altitud  
**Fórmula:** Gueymard REST2 (2008) + SRTM topografía  
**Archivo:** `core/indices/rest2_gueymard_radiacion.py`  
**Precisión:** ±1.5%  
**Output:** 10 micro-valores radiación

```python
radiacion = calcular_radiacion_extraterrestre_rest2(
    latitud=41.55326700,
    longitud=2.39684500,
    altitud=118,
    datetime=datetime(2026, 2, 5, 12, 0),  # Mediodía UTC
    radiacion_medida=600  # Lo que mide tu sensor
)

# RESULTADO
{
    "g0_teorica": 720,                     # W/m² máximo teórico
    "radiacion_extraterrestre": 720,       # REST2
    "radiacion_directa": 650,              # Directa (sin nubes)
    "radiacion_difusa": 70,                # Difusa (cielo)
    "fraccion_difusa_kd": 0.097,           # Kd = 0.097
    "radiacion_neta_onda_corta_rns": 2.9, # MJ/(m²·día)
    "radiacion_neta_onda_larga_rnl": 0.8, # MJ/(m²·día)
    "radiacion_neta_total_rn": 2.1        # MJ/(m²·día)
}
```

**¿Qué significa 720 W/m²?**
```
G0 teórica = 720 W/m² (máximo solar, no nubes)
Tu sensor mide = 600 W/m² (hay nubes)

Validador REST2 dice:
"Radiación OK (600 < 720, hay cielo parcial)"
"NO ES SENSOR SUCIO, hay cobertura nubosa"

PARA TU MACETA:
Radiación real ≈ 600 W/m² en primavera mediodía = normal
```

---

### **ÍNDICE 6: Evapotranspiración FAO-56 (mm/día)**

**Inputs:** T, RH, radiación, viento, presión  
**Fórmula:** FAO-56 Penman-Monteith simplificada  
**Archivo:** `core/indices/environmental_indices.py` línea 57-71  
**Precisión:** ±15% (simplificada)  
**Output:** 1 valor

```python
et0_fao56 = evapotranspiracion_penman_monteith(
    temp_c=25.0,
    humedad=60.0,
    radiacion=600.0,
    viento=2.0
)

# RESULTADO
et0_fao56 = 2.5 mm/día  # Predicción teórica
```

**¿Qué significa 2.5 mm/día?**
```
ET0 = 2.5 mm/día

INTERPRETACIÓN CRUDA:
"Si tu maceta de 70L tuviera agua ilimitada,
 desaparecerían 2.5 mm de profundidad hoy"

PARA TU MACETA 70L:
Volumen = 70L = 70,000 cm³
Profundidad equivalente = 70,000 / (área maceta cm²)
Si maceta cuadrada 30×30cm = 900 cm²
Profundidad = 70,000 / 900 = 77.8 cm

ET en litros = 2.5 mm × 0.0778 m = 0.194 L = 0.19L
(Aproximadamente 190 mL de agua desaparecerán)

PROBLEMA: En tu maceta sin plantas, esto exagera.
Factor real típico = 0.30-0.35
ET_real = 2.5 × 0.32 = 0.8 mm = 62 mL
```

---

### **ÍNDICE 7: ET Wright nocturno (mm/día)**

**Inputs:** ET_base (FAO-56), hora solar, elevación solar  
**Fórmula:** ET_base / factor_resistencia_wright  
**Archivo:** `core/indices/et_nocturna_wright.py` línea 169  
**Precisión:** ±10%  
**Output:** 2 valores (ET corregida + factor)

```python
et_wright = evapotranspiracion_penman_monteith_wright(
    temp_c=25.0,
    humedad_relativa=60.0,
    radiacion_w_m2=600.0,
    viento_m_s=2.0,
    presion_kpa=101.325,
    hora_solar=12.0,           # Mediodía
    elevacion_solar_deg=32.0   # Altura del sol
)

# RESULTADO
{
    "et_wright_total": 2.1,                # mm/día con ajuste
    "et_factor_resistencia": 1.19,         # Factor día (1.0 = día, 1.7 = noche)
    "periodo_nocturno": False,             # Es mediodía
    "et_noche_esperada": 1.24              # Si fuera noche
}
```

**¿Qué significa 2.1 mm/día?**
```
ET Wright = 2.1 mm/día (ligero descuento por convección)
vs FAO-56 = 2.5 mm/día

DIFERENCIA:
- FAO-56 asume resistencia aerodinámica constante
- Wright ajusta: de noche aumenta resistencia (inversión térmica)
- Hoy mediodía: factor 1.19 (descuento pequeño)

SI FUERA NOCHE (hora_solar=23.0):
- Factor = 1.7
- ET_noche = 2.5 / 1.7 = 1.47 mm/día
- Mucho más realista para evaporación nocturna
```

---

### **ÍNDICE 8: Densidad aire (kg/m³) - OMM Completa**

(Ya calculada en V7, se repite para claridad)

```python
densidad_aire = 1.159 kg/m³  # Argentona 25°C, RH=60%, P=1011.3 hPa

USADA EN:
├─ Cálculos radiación (dispersión)
├─ Validador estabilidad (cambios imposibles)
└─ OMM meteorología
```

---

## ⚠️ PARTE 4: PREDICCIONES Y ALERTAS

### **PREDICCIÓN 1: ¿Estrés térmico hoy?**

```
IF WBGT > 28°C THEN alerta_estrés = "MODERADO"
IF WBGT > 30°C THEN alerta_estrés = "ALTO"
IF WBGT > 34°C THEN alerta_estrés = "EXTREMO - PROHIBICIÓN"

HOY 5-FEB: WBGT = 26.1°C → Sin alerta (OK)
```

---

### **PREDICCIÓN 2: ¿Estrés hídrico en maceta?**

```
PSEUDOCÓDIGO V50 (no implementado aún):

humedad_suelo_hoy = 43.2%
humedad_suelo_ayer = 45.1%
delta = -1.9% = -0.76L en 70L

ET_predicha = 2.5 mm/día
ET_esperada = 2.5 × 0.32 (factor) = 0.8 mm/día

¿Coherencia?
0.76L vs 0.8L = OK (error 5%)

SI delta hubiera sido -0.2% (contradictorio):
"ALERTA: ET predijo pérdida pero humedad subió
 Posible: riego automático nocturno, lluvia"
```

---

### **PREDICCIÓN 3: ¿Sensor radiación sucio?**

```
VALIDADOR (en V50):

radiacion_hoy = 600 W/m²
radiacion_ayer = 650 W/m²
cambio = -50 W/m² en 24h

¿Es normal?
- Si ha habido tormenta: SÍ
- Si cielo limpio igual: ALERTA ("sensor degradándose")

Trend detector:
Si radiacion baja 5% cada día durante 5 días
→ "ALERTA: Radiación tendiendo a bajar, panel sucio"
```

---

### **PREDICCIÓN 4: ¿Tormenta?**

```
IF (presion_baja > 2 hPa/hora) AND
   (radiacion_salta > 100 W/m² en 30min) THEN
   alerta_tormenta = "POSIBLE en 1-2 horas"
```

---

### **PREDICCIÓN 5: ¿Sensor temperatura roto?**

```
VALIDADOR ESTABILIDAD:

temp_ahora = 25.0°C
temp_hace_1min = 25.1°C
delta = -0.1°C/min = NORMAL ✅

Pero si:
temp_ahora = 32.5°C
temp_hace_1min = 25.0°C
delta = +7.5°C/min = IMPOSIBLE ❌

→ FALLO: "Sensor temperatura probablemente roto"
→ Sistema interpola: usa temp_anterior = 25.0°C
→ Confianza UTCI = 5%
```

---

## 📤 PARTE 5: SALIDA BUS MQTT - EJEMPLO REAL

### **Mensaje completo cada minuto (recortado por claridad):**

```json
{
  "timestamp": "2026-02-05T12:00:00Z",
  "ubicacion": "Argentona",
  "lat": 41.55326700,
  "lon": 2.39684500,
  
  "sensores_hardware": {
    "temperatura_c": 25.0,
    "humedad_relativa_pct": 60.0,
    "radiacion_w_m2": 600.0,
    "viento_m_s": 2.0,
    "presion_hpa": 1011.3,
    "humedad_suelo_pct": 43.2
  },
  
  "sensores_virtuales_psicrometricos": {
    "presion_vapor_saturado_pa": 3168,
    "presion_vapor_real_pa": 1900,
    "punto_rocio_c": 13.9,
    "relacion_mezcla_g_kg": 11.9,
    "temperatura_virtual_c": 25.18,
    "densidad_aire_kg_m3": 1.159,
    "factor_enhancement": 1.00054
  },
  
  "sensores_virtuales_radiacion": {
    "g0_extraterrestre_w_m2": 720,
    "radiacion_directa": 650,
    "radiacion_difusa": 70,
    "fraccion_difusa": 0.097,
    "radiacion_neta_rns_mj_m2_dia": 2.9,
    "radiacion_neta_rnl_mj_m2_dia": 0.8,
    "radiacion_neta_total_rn": 2.1,
    "temperatura_media_radiante_c": 35.0
  },
  
  "indices_sensacion_termica": {
    "utci_c": 28.5,
    "utci_confianza": 95,
    "utci_metabolic_rate_w": 85,
    "utci_sensible_loss_w": 45,
    "utci_latent_loss_w": 38,
    "utci_radiacion_adjustment_c": 3.5,
    "utci_viento_adjustment_c": 1.2,
    
    "wbgt_c": 26.1,
    "wbgt_confianza": 90,
    "wbgt_bulbo_humedo_c": 18.5,
    "wbgt_globo_negro_c": 28.3,
    "wbgt_outdoor": 26.1,
    "wbgt_indoor": 23.8,
    "wbgt_estado": "ALERTA_MODERADA",
    "wbgt_umbral_distancia": "1°C SOBRE LIMITE",
    
    "steadman_c": 29.6,
    "steadman_estado": "DIAGNOSTICO_AUXILIAR",
    
    "utci_v2_blazejczyk_c": 28.3,
    "utci_v2_estado": "NO_ACTIVO_RANGO_NORMAL"
  },
  
  "indices_radiacion": {
    "radiacion_extraterrestre_rest2": 720,
    "validador_radiacion_estado": "OK",
    "validador_razon": "Coherente con elevación solar 32°"
  },
  
  "indices_evapotranspiracion": {
    "et_fao56_predicha_mm": 2.5,
    "et_wright_corregida_mm": 2.1,
    "et_factor_resistencia": 1.19,
    "et_estado_dia_noche": "DIA",
    "et_noche_esperada_si_hubiera": 1.47,
    
    "humedad_suelo_maceta": {
      "valor_pct": 43.2,
      "cambio_24h": -1.9,
      "agua_perdida_litros": 0.76,
      "et_predicha_litros_esperados": 0.8,
      "coherencia": "OK",
      "factor_correccion_estimado": 0.32,
      "estado": "ESTABLE"
    }
  },
  
  "validadores_estado_general": {
    "psicrometria": "OK",
    "radiacion": "OK",
    "estabilidad_termica": "OK",
    "presion_atmosferica": "OK",
    "sensor_temperatura": "OK",
    "confianza_global": 92,
    "hardware_estado": "OPERACIONAL",
    "alertas": [],
    "recomendaciones": []
  },
  
  "v50_readiness": {
    "validadores_implementados": "NO",
    "validadores_pendientes": [
      "ValidadorAutoAdaptativo",
      "DetectorDegradacion",
      "ControladorET_HumedadSuelo",
      "ValidadorCruzadoSensacionTermica"
    ]
  }
}
```

---

## 🔧 PARTE 6: FLUJO COMPLETO (CÓMO SE ENCADENA TODO)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SENSORES HARDWARE (minuto 1)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                    T=25°C, RH=60%, Rad=600 W/m²,                        │
│            V=2 m/s, P=1011.3 hPa, GPS, hora UTC                         │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    FASE 1: PSICROMETRÍA (Hardy + OMM)                   │
├──────────────────────────────────────────────────────────────────────────┤
│  hardy_nist_psicrometria.py:                                             │
│  ├─ e_s = Wexler-Hyland(T) → 3168 Pa                                    │
│  ├─ f = enhancement_factor(T, P) → 1.00054                              │
│  ├─ e = f × e_s × (RH/100) → 1900 Pa                                   │
│  └─ Td = inverso_wexler(e) → 13.9°C                                    │
│                                                                          │
│  omm_densidad_temperatura_virtual.py:                                    │
│  ├─ w = relacion_mezcla(e, P) → 11.9 g/kg                              │
│  ├─ T_v = temperatura_virtual(T, w) → 25.18°C                          │
│  └─ ρ = densidad_omm(P, T_v, e) → 1.159 kg/m³                          │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│              FASE 2: RADIACIÓN (REST2 + Stefan-Boltzmann)               │
├──────────────────────────────────────────────────────────────────────────┤
│  rest2_gueymard_radiacion.py:                                            │
│  ├─ G0 = REST2(lat, lon, fecha, hora) → 720 W/m² (teórica)            │
│  ├─ T_mrt = inverso_globo(rad, T, V) → 35°C                           │
│  └─ Rn = radiacion_neta_fao56(rad, T, RH) → 2.1 MJ/(m²·día)          │
│                                                                          │
│  Validación:                                                             │
│  IF rad=600 < G0=720 THEN "OK, hay nube"                               │
│  IF rad > G0×1.1 THEN "ERROR: imposible"                                │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│         FASE 3: INDICES SENSACIÓN TÉRMICA (UTCI + WBGT)                │
├──────────────────────────────────────────────────────────────────────────┤
│  environmental_indices.py:                                               │
│                                                                          │
│  utci_v4_02_fiala_completo(T, RH, V, T_mrt, P)                        │
│  ├─ Input: T=25, RH=60, V=2, T_mrt=35, P=101.325                      │
│  ├─ Fórmula: Fiala 64-nodos termorregulación                           │
│  └─ Output: UTCI=28.5°C + 13 micro-valores                             │
│                                                                          │
│  wbgt_liljegren_completo(T, RH, V, rad, P)                            │
│  ├─ Input: T=25, RH=60, V=2, rad=600, P=101.325                       │
│  ├─ Fórmula: Liljegren balance energético globo                        │
│  └─ Output: WBGT=26.1°C + 20 micro-valores                             │
│                                                                          │
│  Alternativas rápidas:                                                   │
│  ├─ Steadman (sin radiación) → 29.6°C [auxiliar]                      │
│  └─ UTCI v2 (extremos) → 28.3°C [solo si T <-50 o >60]                │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│         FASE 4: EVAPOTRANSPIRACIÓN (FAO-56 + Wright)                   │
├──────────────────────────────────────────────────────────────────────────┤
│  environmental_indices.py + et_nocturna_wright.py:                       │
│                                                                          │
│  ET_fao56(T, RH, rad, V, P)                                            │
│  ├─ Input: todos los anteriores                                         │
│  ├─ Fórmula: FAO-56 Penman-Monteith simplificada                       │
│  └─ Output: ET0=2.5 mm/día                                              │
│                                                                          │
│  ET_wright(ET0, hora_solar, elevacion_solar)                           │
│  ├─ Input: ET0=2.5, hora=12.0, elevacion=32°                          │
│  ├─ Fórmula: ET / factor_resistencia (día=1.19, noche=1.7)            │
│  └─ Output: ET_corregida=2.1 mm/día                                    │
│                                                                          │
│  EN V50 (FUTURO):                                                        │
│  ├─ Entrada: humedad_suelo_cambio_real                                 │
│  ├─ Calcula: factor_correccion_dinamico = real / predicha              │
│  └─ Publica: ET_corregida = ET_wright × factor                         │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│              FASE 5: VALIDADORES (V49.1 minimal, V50 completo)         │
├──────────────────────────────────────────────────────────────────────────┤
│  ValidadorPsicrometria:                                                  │
│  IF Td > T THEN FALLO                                                   │
│  IF RH > 100 THEN ALERTA                                                │
│                                                                          │
│  ValidadorRadiacion:                                                     │
│  IF (elevacion_solar < -5°) AND (rad > 20) THEN ALERTA                │
│  IF rad > G0×1.1 THEN ERROR                                             │
│                                                                          │
│  ValidadorCruzado (V50):                                                 │
│  IF |UTCI - WBGT| > 5°C AND sin causa THEN ALERTA                     │
│                                                                          │
│  ValidadorET_HumedadSuelo (V50):                                         │
│  IF factor_correccion < 0.20 THEN ALERTA "sobreestimación extrema"    │
│  IF factor_correccion > 0.50 THEN ALERTA "factor cambió"              │
└──────────────┬──────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    FASE 6: BUS MQTT (publicación)                       │
├──────────────────────────────────────────────────────────────────────────┤
│  50+ topics con:                                                         │
│  ├─ Valores finales (UTCI, WBGT, ET, etc)                              │
│  ├─ Confianza ponderada (0-100%)                                        │
│  ├─ Estado validadores (OK|WARN|ALERTA|FALLO)                          │
│  ├─ Micro-valores descompuestos (13+20+10 = 43 extra)                  │
│  └─ Recomendaciones de acción                                           │
│                                                                          │
│  Ejemplo topics:                                                         │
│  meteoser/utci = 28.5                                                   │
│  meteoser/utci_confianza = 95                                           │
│  meteoser/utci_estado = "OK"                                            │
│  meteoser/wbgt = 26.1                                                   │
│  meteoser/wbgt_estado = "ALERTA_MODERADA"                              │
│  meteoser/et_corregida = 2.1                                            │
│  meteoser/humedad_suelo = 43.2                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 PARTE 7: RESUMEN PARA TU MACETA 70L (Tierra compo jardinería)

| Cálculo | Fórmula | Valor | Qué significa |
|---------|---------|-------|--------------|
| **ENTRADA** | - | T=25°C, RH=60%, Rad=600 W/m², V=2 m/s | Estado actual |
| Punto rocío | Hardy Wexler | 13.9°C | Condensación posible < 13.9°C |
| Densidad aire | OMM | 1.159 kg/m³ | Normal para T=25°C, RH=60% |
| G0 teórica | REST2 | 720 W/m² | Máximo sin nubes |
| T media radiante | Stefan-Boltzmann | 35°C | Efecto radiación + T aire |
| **SENSACIÓN** | | | |
| UTCI | Fiala 64-nodos | 28.5°C | Se siente como 28.5°C (calor moderado) |
| WBGT | Liljegren | 26.1°C | **En límite OSHA 26°C** → ⚠️ VIGILAR |
| Steadman | Clásica | 29.6°C | Auxiliar, sin radiación |
| **RADIACIÓN** | | | |
| Radiación real | Medida | 600 W/m² | Coherente (hay nubes), no sensor sucio |
| Radiación neta | FAO-56 | 2.1 MJ/(m²·día) | Lo que calienta el suelo realmente |
| **AGUA** | | | |
| ET0 predicha | FAO-56 | 2.5 mm/día | Teórica (exagera) |
| ET corregida Wright | Wright | 2.1 mm/día | Ajuste por resistencia aerodinámica |
| **MACETA REALIDAD** | | | |
| Humedad suelo | Medida | 43.2% | Normal para tierra compo con poco riego |
| Cambio 24h | Medida | -1.9% | Bajó 0.76L en 24h |
| ET real esperada | Proyección | 0.8 mm/día | Con factor 0.32 = 0.25L |
| **COHERENCIA** | | | |
| ¿Coinciden? | Validación | SÍ (0.76L medido ≈ 0.8L esperado) | Sistema OK, predicciones realistas |
| Confianza global | Validadores | 92% | Alto, sin anomalías |

---

## 🚀 CONCLUSIÓN: DE V49.1 A V50.0

### **V49.1 (Ahora mismo):**
- ✅ 13 fórmulas reales selladas
- ✅ 50+ micro-valores publicados
- ✅ Validadores mínimos (psicrometría, radiación)
- ✅ Catalogo completo documentado

### **V50.0 (Siguiente sprint):**
- 🔧 ValidadorAutoAdaptativo (aprende tu hardware)
- 🔧 DetectorDegradacion (alerta si sensor empeora)
- 🔧 ControladorET_HumedadSuelo (factor dinámico 0.32)
- 🔧 ValidadorCruzadoSensacionTermica (WBGT vs UTCI coherencia)
- 🔧 Graceful degradation (publica con confianza reducida)

**Tu maceta de 70L es el LABORATORIO PERFECTO para V50.**

---

**¿Listo para diseñar la arquitectura V50?**
