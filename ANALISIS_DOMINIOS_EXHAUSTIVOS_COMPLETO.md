# 🔍 AUDITORÍA EXHAUSTIVA DE DOMINIOS Y FUNCIONES DEL SISTEMA
**Fecha:** 10 de febrero de 2026  
**Filosofía:** Siempre lo mejor del mundo, respetando precisión sin ensuciar con ruido

---

## 📊 RESUMEN EJECUTIVO

**SITUACIÓN ACTUAL:**
- ✅ **4 dominios v2.0 activos:** Cetrería, Lluvia, Deporte, Confort
- ⚠️ **4 dominios COMPLETOS pero NO publicados:** Riego, Astronomía, Salud, Hidrología
- ✅ **ASHRAE55 Adaptativo:** Código robusto disponible (VTT + confort adaptativo)
- ❌ **Viticultura/Plagas:** NO existe en el código actual

**ÍNDICES TOTALES EN EL SISTEMA:** 150+ funciones/fórmulas

---

## 🏗️ DOMINIOS A IMPLEMENTAR (FINAL RECOMENDADO)

### **DOMINIO 1: CETRERÍA** ✅ v2.0 COMPLETO
**Status:** Publicado en bus_expander  
**Sub-índices (5):**
- Viento cetrería (0-100)
- Visibilidad terreno (0-100)
- Termales probabilidad (0-100)
- Barro campo (0-100)
- Confort ave (0-100)

**Sintético:** indice_cetreria_sintetico (combinación ponderada)

**Recomendación UI:** "¿Buen día para volar gavilan? SÍ/NO + confianza%"

---

### **DOMINIO 2: LLUVIA** ✅ v2.0 COMPLETO
**Status:** Publicado en bus_expander  
**Sub-índices (4):**
- Riesgo inundación (0-100) [basado en intensidad lluvia + escorrentía]
- Visibilidad carretera (0-100) [Kasten-Hanel + lluvia]
- Adherencia terreno (0-100) [saturación suelo + humedad]
- Probabilidad rayos (0-100) [Sundqvist + CAPE fallback]

**Sintético:** indice_lluvia_sintetico

**Recomendación UI:** "¿Va a llover/rayos? SÍ/NO + confianza%"

---

### **DOMINIO 3: DEPORTE** ✅ v2.0 COMPLETO
**Status:** Publicado en bus_expander  
**Sub-índices (4):**
- Adherencia terreno deporte (0-100)
- Visibilidad deporte (0-100)
- Viento juego limpio (0-100)
- Confort atletas (0-100) [UTCI]

**Sintético:** indice_deporte_sintetico

**Recomendación UI:** "¿Jugar fútbol/tenis hoy? SÍ/NO + confianza%"

---

### **DOMINIO 4: CONFORT** ✅ v2.0 COMPLETO
**Status:** Publicado en bus_expander  
**Sub-índices (4):**
- Temperatura ideal (0-100) [Gaussiana centrada 20°C]
- Humedad ideal (0-100) [Gaussiana centrada 50%RH]
- Índice UV (0-100) [Radiación + elevación solar]
- Sensación térmica (0-100) [UTCI + viento]

**Sintético:** indice_confort_sintetico

**Recomendación UI:** "¿Clima cómodo ahora? SÍ/NO + confianza%"

---

### **DOMINIO 5: RIEGO** 🚀 A CREAR (v2.0 FORMAT)
**Status:** CÓDIGO EXISTE en environmental_indices.py (líneas ~2160-2430), PERO NO EMPAQUEADO

**Funciones existentes encontradas:**
1. `balance_hidrico_delta_h()` [ΔH = Lluvia - ET0 - Escorrentía - Infiltración]
2. `estres_hidrico_cultivo()` [Factor 0-1, por tipo cultivo/suelo]
3. `disponibilidad_agua_cultivable()` [Días hasta sequedad]

**Sub-índices a generar (4+):**
- **Balance hídrico neto** (0-100): Ganancia/pérdida de agua en perfil
  - Input: lluvia_1h, ET0, escorrentía, infiltración
  - Fórmula: ΔH = Lluvia - ET0 - Escor - Infiltr
  - Interpretación: >2mm=bueno, <-3mm=riego urgente
  
- **Estrés hídrico cultivo** (0-100): Factor de reducción por déficit agua
  - Input: humedad_suelo_pct, tipo_cultivo (maíz/trigo/general), tipo_suelo (5 tipos)
  - Fórmula: f = (H - H_pm) / (H_cc - H_pm)
  - H_pm: punto marchitez permanente (12-15% según cultivo)
  - H_cc: capacidad de campo (18-48% según suelo)
  
- **Disponibilidad agua cultivable** (0-100): Días hasta sequedad
  - Input: humedad_suelo_pct, ET0_promedio_7d_mm
  - Fórmula: Días = agua_disponible / ET_promedio
  - Urgencia: >7d=OK, 4-7d=monitorear, <1d=crítico
  
- **Infiltración vs escorrentía** (0-100): Eficiencia infiltración
  - Input: lluvia_rate (mm/h), tipo_suelo, pendiente_terreno
  - Modelo: Green-Ampt simplificado (en hidrology_indices.py)

**Sensors usados:** WH51 (humedad_suelo), WH65 (lluvia, temperatura para ET0)

**No es "ruido":** Mejor decisión de riego = +15-20% rendimiento cosecha. FAO-56 estándar.

**Recomendación UI:** "¿Riego hoy? SÍ/NO + confianza% + 'Estrés cultivo X%, sequedad en Y días'"

---

### **DOMINIO 6: ASTRONOMÍA** 🚀 A CREAR (v2.0 FORMAT)
**Status:** MECÁNICA SÍ EXISTE (astronomia_recursiva.py: NREL SPA + Ciddor), PERO NO ÍNDICES DERIVADOS

**Funciones disponibles:**
1. `AstronomiaRecursiva.calcular_posicion_solar_nrel_spa()` [Azimut, elevación aparente, distancia_AU]
2. `AstronomiaRecursiva.calcular_posicion_lunar_meeus()` [Posición lunar, fase]

**Sub-índices a generar (5+):**

- **Horas de luz solar** (0-100): Cantidad de luz disponible
  - Input: elevación solar a lo largo del día (desde astronomia.py)
  - Cálculo: Suma tiempo con elevación > 0°
  - Mapeo a 0-100: 0h=0%, máximo del año (16h en verano)=100%
  - Precisión: ±2 minutos (astronomia_recursiva es NREL SPA)
  
- **Disponibilidad para observación nocturna** (0-100): Noche oscura sin luna
  - Input: fase lunar (iluminación %), elevación solar (debe ser <-6° para twilight astronómico)
  - Fórmula: score = (100 - % iluminación luna) × (1 si elevación<-18° else 0.5)
  - Interpretación: >70%=excelente, <30%=pobre
  
- **Amplitud térmica anual tendencial** (0-100): Capacidad de ciclo diurno
  - Input: Máxima radiación solar extraterrestre hoy (REST2 Gueymard ya calculado)
  - Fórmula: Amplitud≈(Rad_extr × insolación × K_transmisión) / inercia_térmica
  - Indica cuan "violento" será el ciclo T hoy
  
- **Claridad del cielo (Kt índice)** (0-100): Transmitancia atmosférica
  - Input: Radiación solar real vs teórica extraterrestre
  - Fórmula: K_t = Radiación_global / Radiación_extraterrestre
  - 0.75<K_t<0.85 = día despejado (buenos para solar)
  - K_t>0.85 = imposible (ruido en sensores)
  
- **Visibilidad nocturna sin instrumentos** (0-100): Cantidad de estrellas visibles
  - Input: Luz ambiente (si se tuviera), HR (afecta transmitancia), elevación solar < -18°
  - Simplificado: Si elevación<-18° Y HR<70% Y K_t>0.6 → Score alto
  - Score bajo: HR>80% O elevación>-10° O K_t<0.4

**Sensors usados:** WH65 (radiación), cálculos puros (sin sensor extra)

**¿Es "ruido"?** NO. Estos índices tienen utilidad real:
- Horas luz: agricultura, biología, energía solar
- Obs nocturna: astrofotografía, astronomía
- Amplitud térmica: predicción heladas
- K_t: eficiencia paneles solares
- Visibilidad: contaminación lumínica

**Recomendación UI:** "¿Buena noche para astrofotografía? SÍ/NO con X% fases lunares + Y horas oscuridad"

---

### **DOMINIO 7: SALUD** 🚀 A CREAR (v2.0 FORMAT)
**Status:** FUNCIONES ESPARCIDAS EN environmental_indices.py + confort_indices.py, NO EMPAQUEADAS

**Funciones ENCONTRADAS en código:**
1. `indice_uvi_robusto()` [UV basado en radiación + elevación solar]
2. `indice_alerta_calor_extremo()` [Temp>32°C + UV>7 + humedad>60%]
3. `indice_alerta_frio_extremo()` [Temp<5°C + viento>10kmh + humedad<40%]
4. `indice_riesgo_helada_local()` [Yates-McLean: punto rocío + T_ext + radiación nocturna + viento]
5. `indice_salud_edificio()` [ASHRAE 62.1: humedad crónica, condensación, moho, ácaros]

**Sub-índices a generar (6):**

- **Índice UV personal** (0-100): Riesgo quemadura solar
  - Input: radiación W/m², elevación solar
  - Fórmula: UVI ≈ (Rad × cos(zenita)) / 25
  - Mapeo 0-100: 0-2=bajo, 3-5=moderado, 6-7=alto, 8-10=muy alto, >11=extremo (100%)
  - Referencia: Gafas UV recomendadas si >7
  
- **Riesgo estrés por calor extremo** (0-100): Capacidad corporal para hacer actividad
  - Input: Temp>32°C, UV>7, humedad>60%
  - Componentes: Temperatura percibida (WBGT o UTCI) >35°C, deshidratación, golpe de calor
  - Score: 0-25 verde, 26-50 amarillo, 51-75 naranja, 76-100 rojo
  - NO es "ruido": estrés térmico = hospitalización en extremos
  
- **Riesgo hipotermia** (0-100): Pérdida de calor corporal peligrosa
  - Input: Temp<0°C + viento fuerte (wind chill) + humedad (evaporación)
  - Fórmula: Wind chill = 13.12 + 0.6215×T - 11.37×(v^0.16) + 0.3965×T×(v^0.16)
  - Score: 0-30 sin riesgo, 31-60 riesgo moderado, 61-100 riesgo severo
  
- **Riesgo helada local** (0-100): Congelación de plantas/rocío en superficies
  - Input: Punto rocío, T_ext, radiación nocturna (cobertura nubosa), viento
  - Fórmula: Yates-McLean (línea 9237 environmental_indices.py)
  - Útil para agricultura + predicción escarcha
  
- **Salud del aire interior** (0-100): Riesgo de moho, ácaros, contaminación tóxica
  - Input: Humedad media (%), tiempo con HR>60% (horas acumuladas), eventos condensación
  - Componentes:
    - Humedad crónica: >60% sostenida → moho (Aspergillus, Penicillium)
    - Condensación repetida: >168h con HR>60% → riesgo alto (ISO 13788)
    - CO2 interior (si se tuviera): >1200ppm → saturación, mala decisión ventilación
  - Score ASHRAE 62.1: >70=saludable, <40=muy seco (problemas respiratorios)
  
- **Alerta de calidad aire exterior** (0-100): Contaminación atmosférica
  - Input: PM2.5 (si se tuviera), visibilidad (proxy de partículas), NO₂ (si existe)
  - Simplificado: AQI = f(PM2.5) en µg/m³
  - 0-50=bueno, 51-100=aceptable, >300=peligroso
  - Alternativa SIN sensor PM: Si visibilidad<500m Y HR>60% → Score bajo (niebla contaminada)

**Sensors usados:** WH65 (radiación, temperatura, humedad), visual (visibilidad)

**¿Es "ruido"?** NO. Salud es CRÍTICA:
- UV: cáncer de piel
- Calor extremo: golpes de calor (13,000 muertes/año en Europa ola2024)
- Frío extremo: hipotermia
- Helada: pérdidas agrícolas
- Aire interior: asma, alergias (WHO: 4M muertes/año por aire interior)

**Recomendación UI:** "¿Riesgo para la salud hoy? BAJO (verde) / MODERADO (amarillo) / ALTO (rojo) - UV muy alto 9, Calor 35°C percibido"

---

### **DOMINIO 8: HIDROLOGÍA** 🚀 A CREAR (v2.0 FORMAT)
**Status:** CODE EXISTS (hidrology_indices.py, 307 líneas), NO PUBLICADO

**Funciones disponibles:**
1. `InfiltracionEscorrentia.infiltracion_mm_h()` [Green-Ampt]
2. `InfiltracionEscorrentia.escorrentia_mm_h()` [Pendiente + lluvia rate]
3. `calcular_spi()` [Índice Estandarizado Precipitación: déficit de lluvia]

**Sub-índices a generar (4):**

- **Tasa infiltración potencial** (0-100): Velocidad agua penetra suelo
  - Input: Tipo suelo (estimado de HR + T), lluvia_rate (mm/h), pendiente
  - Fórmula: Green-Ampt: I(t) = K_s × t + S × ln(1 + I(t)/S)
  - K_s: conductividad saturada (0.3-25 mm/h según suelo)
  - Mapeo 0-100: 0mm/h=0%, 25mm/h (máximo arenoso)=100%
  - Interpretación: >50%=infiltra bien, <10%=escurre todo
  
- **Riesgo escorrentía** (0-100): Agua que baja sin infiltrar (pérdida + inundación)
  - Input: lluvia_rate, escorrentia (función Green-Ampt), pendiente_terreno
  - Fórmula: Escor = lluvia_rate - infiltración potencial
  - Score: 0%=toda infiltra, 100%=toda escurre (peligro inundación)
  - Combinado con "riesgo_inundacion" del dominio Lluvia
  
- **Índice estandarizado precipitación (SPI)** (0-100): Déficit/exceso lluvia histórico
  - Input: Precipitación acumulada mensual, serie histórica (últimos 30 años si hay)
  - Fórmula: SPI_3m = (Precip_3m_acum - Media_histórica) / Desviación_estándar
  - Mapeo: SPI<-1.5=sequía moderada, <-2=severa, >1.5=lluvia excesiva
  - Temporal: 3 meses, 6 meses, 12 meses (múltiples escalas)
  
- **Estado de humedad del suelo tendencial** (0-100): Acumulación agua a largo plazo
  - Input: ΔH diario (balance hídrico del dominio Riego)
  - Acumulación: suma ΔH últimos 7-30 días
  - Score: -50mm acumulado (seco)=0%, 0mm=50%, +50mm (saturado)=100%
  - Predictor de sequía/exceso a escala agraria

**Sensors usados:** WH51 (si estuviera, sería mejor), WH65 (lluvia), cálculos puros

**¿Es "ruido"?** NO. Hidrología es INGENIERÍA HIDRÁULICA:
- Infiltración: drenaje, inundaciones, contaminación freática
- Escorrentía: erosión, sedimentos, contaminación difusa
- SPI: sequía agraria, estrés hídrico regional
- Estado suelo: predicción almacenamiento agua subterránea

**Recomendación UI:** "¿Riesgo de inundación local? BAJO (infiltra 80%) / EXTREMO (escurre 95% pendiente 20%)"

---

### **DOMINIO 9: ASHRAE55 ADAPTATIVO** 🚀 A CREAR (OPCIONAL, PARA INTERIORES)
**Status:** CODE COMPLETE (ashrae55_adaptive_vtt.py, 420 líneas), NO PUBLICADO

**Este dominio es para PUNTOS INTERIORES (si se añaden sensores de temperatura interior)**

**Sub-índices (si hay datos interior):**

- **Confort adaptativo ASHRAE-55** (0-100): Zona de confort según clima exterior
  - Input: T_aire_interior, T_media_exterior_running (7-30 días)
  - Fórmula: T_neutral = 0.31 × T_ext_running + 17.8
  - Límites: ±3.5°C (80% aceptabilidad) ó ±2.5°C (90%)
  - Score: Si T_int dentro zona → 100%, fuera → degrada
  - ASHRAE Standard 55-2020 (más liberal que PMV/PPD clásico)
  
- **Riesgo de moho VTT** (0-100): Crecimiento microbiano en interiores
  - Input: Humedad interior, T_interior, concentración de esporas
  - Fórmulas de sorción: isoterma dinámico + crecimiento exponencial
  - Score: <0.8 (safe), 0.8-0.9 (risk), >0.9 (critical)
  - Referencia VTT (Helsinki): isotermas de sorción para Aspergillus, Penicillium

**NOTA:** Este dominio solo tiene sentido si hay sensores de temperatura/humedad INTERIOR.  
De momento, RECOMENDACIÓN: **APLAZAR hasta que haya datos interiores.**

---

## 📋 TABLA COMPARATIVA: DOMINIOS RECOMENDADOS

| Dominio | Estado | Sensores | Sub-índices | Precisión | Necesidad |
|---------|--------|----------|-------------|-----------|-----------|
| **Cetrería** | ✅ v2.0 | WH65 | 5 | Alta | CRÍTICA-Aplicación |
| **Lluvia** | ✅ v2.0 | WH65, WH51 | 4 | Alta (Kasten-Hanel) | CRÍTICA-Riesgo |
| **Deporte** | ✅ v2.0 | WH65 | 4 | Alta (UTCI) | MEDIA-Ocio |
| **Confort** | ✅ v2.0 | WH65 | 4 | Alta (UTCI) | ALTA-Salud |
| **Riego** | 🔄 Crear | WH65, WH51 | 4 | Alta (FAO-56) | CRÍTICA-Agricultura |
| **Astronomía** | 🔄 Crear | WH65 | 5 | Muy Alta (NREL SPA) | MEDIA-Aplicaciones |
| **Salud** | 🔄 Crear | WH65, visual | 6 | Alta (estándares OMS) | CRÍTICA-Salud pública |
| **Hidrología** | 🔄 Crear | WH65, (WH51) | 4 | Buena (Green-Ampt) | MEDIA-Ingeniería |
| **ASHRAE55** | ⏸️ Aplazar | Interior (no presente) | 2 | Alta | BAJA-Sin datos |

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### **FASE 1: CREAR WRAPPERS v2.0 (1-2 horas)**
```python
# Crear estos nuevos archivos con estructura calcular_*_completa():

✅ core/indices/riego/riego_indices.py
   - En base a funciones de environmental_indices.py
   - Integra balance_hidrico + estres_cultivo + disponibilidad_agua + infiltracion
   - calcular_riego_completa(datos_sensores) → dict

✅ core/indices/astronomia/astronomia_indices.py
   - En base a astronomia_recursiva.py
   - Convierte posiciones en índices: horas_luz, obs_nocturna, amplitud_térmica, K_t, visibilidad_noche
   - calcular_astronomia_completa(datos_sensores) → dict

✅ core/indices/salud/salud_indices.py
   - Consolida funciones de environmental_indices.py
   - Reúne: UV, calor_extremo, frio_extremo, helada, salud_edificio
   - calcular_salud_completa(datos_sensores) → dict

✅ core/indices/hidrologia/hidrologia_indices.py
   - En base a hidrology_indices.py
   - Integra infiltración + escorrentía + SPI + estado_humedad
   - calcular_hidrologia_completa(datos_sensores) → dict
```

### **FASE 2: INTEGRAR EN bus_expander.py (1 hora)**
Añadir bloques análogos a Cetrería/Lluvia/Deporte/Confort para los 4 nuevos dominios.

### **FASE 3: CONSTRUIR recommendation_summarizer.py (2 horas)**
Convertir 8 índices sintéticos → 8 recomendaciones con confianza + reasoning.

### **FASE 4: VALIDAR (1 hora)**
Tests rápidos para cada dominio.

**TIEMPO TOTAL:** ~4-5 horas

---

## ⚠️ DOMINIOS DESCARTADOS (HONESTIDAD TOTAL)

### ❌ **Viticultura específica**
**Razón:** NO encontrado en código. Crear desde cero requeriría:
- Datos históricos de viñedos (10+ años)
- Modelos fenológicos específicos (Bárbara, BBCH)
- Validación agraria regional

**Alternativa:** Puede implementarse DENTRO del dominio Salud como sub-índice "Riesgo oidio/mildiu" si se añaden datos de humedad relativa y temperatura nocturna mínima. FAO tiene modelos integrados.

### ❌ **Plagas específicas (mosca blanca, pulgón, etc.)**
**Razón:** Sin sensor de conteo/luz, solo puedo estimar por temperatura (rango óptimo reproductor).

**Alternativa:** Crear sub-índice "Riesgo de plagas" en Salud basado en:
- Temperatura óptima reproducción por insecto (15-25°C típicamente)
- Humedad (facilitaría desarrollo)
- Estimador: Acumulación grados-día sobre T_base

Pero esto sería **impreciso sin datos reales de capturas.**

---

## 🎯 MI RECOMENDACIÓN FINAL HONESTA

**IMPLEMENTAR 8 DOMINIOS EN v2.0:**

```
┌──────────────────────────────────────────────────────────┐
│ DOMINIOS PRIORITARIOS (IMPLEMENTAR YA)                  │
├──────────────────────────────────────────────────────────┤
│ 1. ✅ CETRERÍA       (Re-hecho v2.0)                     │
│ 2. ✅ LLUVIA         (Re-hecho v2.0)                     │
│ 3. ✅ DEPORTE        (Re-hecho v2.0)                     │
│ 4. ✅ CONFORT        (Re-hecho v2.0)                     │
│ 5. 🔄 RIEGO          (CREAR de environmental_indices)   │
│ 6. 🔄 ASTRONOMÍA     (CREAR de astronomia_recursiva)    │
│ 7. 🔄 SALUD          (CONSOLIDAR de funciones sueltas)  │
│ 8. 🔄 HIDROLOGÍA     (CREAR de hidrology_indices)       │
└──────────────────────────────────────────────────────────┘

OMITIR POR AHORA:
┌──────────────────────────────────────────────────────────┐
│ • ASHRAE55 Adaptativo (sin sensores interiores)         │
│ • Viticultura (datos no presentes)                      │
│ • Plagas (sin sensor conteo: imprecisión)               │
└──────────────────────────────────────────────────────────┘
```

**¿CONFIRMADO ESTE PLAN?**

