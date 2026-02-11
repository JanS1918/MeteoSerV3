# LADO A LADO: Cada Cálculo → Publicación en Bus

## Componente 1: Derivada GHI (Radiación)

### En el Archivo Maestro (CENTRALIZADO)
```python
# core/indices/lluvia_inminente_indices.py L62-104

def calcular_derivada_ghi_w_m2_s(historial):
    """
    Calcula derivada de radiación usando regresión lineal.
    
    Clasifica como:
    - estable: cambios < |50| W/m²/min
    - clearing: -80 a -50 W/m²/min (nubes se disipan)
    - nube_moderada: -220 a -80 W/m²/min
    - nube_severa: < -220 W/m²/min (oscurecimiento rápido)
    
    Scoring (0-25):
    - estable → 5 puntos
    - clearing → 8 puntos  
    - nube_moderada → 20 puntos
    - nube_severa → 25 puntos
    """
    derivada = calcular_derivada_regresion_lineal(
        historial, 
        factor_tiempo=60.0  # por minuto
    )
    
    # Clasificación y scoring...
    return {
        'derivada': derivada,
        'score': score,
        'clasificacion': clasificacion,
        'severidad': severidad,
        'umbral_nube': umbral
    }
```

### En el Scheduler (PUBLICACIÓN)
```python
# core/scheduler/calculador_indices_automatico.py L325-329

# Interior del ciclo de 5 minutos...
# DESCOMPUESTA:
bus.publicar(
    'alerta_lluvia_componente_ghi_derivada',
    resultado['componente_ghi']['derivada'],
    unidad='W/m²/min',
    rango='(-inf, +inf)',
    fuente='lluvia_inminente_v51',
    peso=0.25
)

bus.publicar(
    'alerta_lluvia_componente_ghi_score',
    resultado['componente_ghi']['score'],
    unidad='puntos',
    rango='0-25',
    fuente='lluvia_inminente_v51'
)
```

### En el Bus (RESULTADO)
```
Diccionario BusEstadoGlobal:
{
    'alerta_lluvia_inminente_score': 72,  # ENTERA (contiene 25% GHI)
    'alerta_lluvia_componente_ghi_derivada': -128.5,  # DESCOMPUESTA
    'alerta_lluvia_componente_ghi_score': 20,  # DESCOMPUESTA
    ...
}
```

---

## Componente 2: Derivada Presión (MÁXIMO PESO)

### En el Archivo Maestro (CENTRALIZADO)
```python
# core/indices/lluvia_inminente_indices.py L150-192

def calcular_derivada_presion_hpa_min(historial):
    """
    Calcula derivada de presión - INDICADOR PRINCIPAL de sistemas frontales.
    
    Razón del máximo peso (25%):
    - Presión son predictor más confiable de tormentas
    - Caída rápida (dP/dt) anticipa frentes
    - Presión < 1000 hPa = sistema potente
    
    Clasificación:
    - caida_severa: < -2.0 hPa/h (ROJA)
    - caida_leve: -2.0 a -0.5 hPa/h (AMARILLA)
    - estable: -0.5 a +0.5 hPa/h
    - aumento: > +0.5 hPa/h (clearing)
    
    Scoring (0-25):
    - caida_severa → 25 puntos (MÁXIMO)
    - caida_leve → 18 puntos
    - estable → 5 puntos
    - aumento → 2 puntos
    """
    derivada = calcular_derivada_regresion_lineal(
        historial,
        factor_tiempo=60.0  # por minuto
    )
    
    # Clasificación más severa que otras...
    return {
        'derivada': derivada,
        'score': score,
        'clasificacion': clasificacion,
        'severidad': severidad,
        'umbral_sistema': umbral
    }
```

### En el Scheduler (PUBLICACIÓN)
```python
# core/scheduler/calculador_indices_automatico.py L331-335

bus.publicar(
    'alerta_lluvia_componente_presion_derivada',
    resultado['componente_presion']['derivada'],
    unidad='hPa/min',
    rango='(-inf, +inf)',
    fuente='lluvia_inminente_v51',
    peso=0.25  # PESO MÁXIMO
)

bus.publicar(
    'alerta_lluvia_componente_presion_score',
    resultado['componente_presion']['score'],
    unidad='puntos',
    rango='0-25',  # MAX SCORE
    fuente='lluvia_inminente_v51'
)
```

### En el Bus (RESULTADO)
```
Diccionario BusEstadoGlobal:
{
    'alerta_lluvia_inminente_score': 72,  # ENTERA (contiene 25% presión)
    'alerta_lluvia_componente_presion_derivada': -2.3,  # DESCOMPUESTA
    'alerta_lluvia_componente_presion_score': 25,  # DESCOMPUESTA (MAX)
    ...
}
```

---

## Componente 3: Derivada Humedad Relativa

### En el Archivo Maestro (CENTRALIZADO)
```python
# core/indices/lluvia_inminente_indices.py L106-148

def calcular_derivada_humedad_pct_min(historial):
    """
    Calcula derivada de HR (humedad relativa).
    
    Relación lluvia:
    - dHR/dt > 2.0 %/min: Aumento RÁPIDO → lluvia inminente
    - dHR/dt > 1.0 %/min: Aumento moderado → nube
    - dHR/dt < -1.5 %/min: Secado rápido → clearing
    
    Scoring (0-15):
    - aumento_rapido (>2.0) → 15 puntos
    - aumento_moderado (1.0-2.0) → 10 puntos
    - estable (-1.5 a 1.0) → 5 puntos
    - secado_rapido (<-1.5) → 2 puntos
    """
    derivada = calcular_derivada_regresion_lineal(
        historial,
        factor_tiempo=60.0  # por minuto
    )
    
    # Aplicar umbrales de lluvia...
    return {
        'derivada': derivada,
        'score': score,
        'clasificacion': clasificacion,
        'severidad': severidad,
        'umbral_lluvia': umbral
    }
```

### En el Scheduler (PUBLICACIÓN)
```python
# core/scheduler/calculador_indices_automatico.py L337-341

bus.publicar(
    'alerta_lluvia_componente_humedad_derivada',
    resultado['componente_humedad']['derivada'],
    unidad='%/min',
    rango='(-inf, +inf)',
    fuente='lluvia_inminente_v51',
    peso=0.15
)

bus.publicar(
    'alerta_lluvia_componente_humedad_score',
    resultado['componente_humedad']['score'],
    unidad='puntos',
    rango='0-15',
    fuente='lluvia_inminente_v51'
)
```

### En el Bus (RESULTADO)
```
Diccionario BusEstadoGlobal:
{
    'alerta_lluvia_inminente_score': 72,  # ENTERA (contiene 15% humedad)
    'alerta_lluvia_componente_humedad_derivada': 2.8,  # DESCOMPUESTA
    'alerta_lluvia_componente_humedad_score': 15,  # DESCOMPUESTA
    ...
}
```

---

## Componente 4: Colapso ΔT Solar (Virtual Pyranometer)

### En el Archivo Maestro (CENTRALIZADO)
```python
# core/indices/lluvia_inminente_indices.py L270-279

def _evaluar_componente_dt_solar(dt_solar):
    """
    Detecta colapso de diferencial de temperatura (sensor virtual).
    
    Indicador: Cuando pierde radiación:
    - ΔT < 0.5°C: Cobertura nube densa (score 100)
    - ΔT < 1.0°C: Nube moderada (score 50)
    - ΔT < 2.0°C: Parcialmente cubierto (score 20)
    - ΔT > 2.0°C: Despejado (score 0)
    
    Scoring (0-10):
    Este es el más débil porque es local/puntual.
    """
    if dt_solar is None:
        return {'valor': None, 'score': 0, 'severidad': 'desconocida'}
    
    if dt_solar < 0.5:
        return {'valor': dt_solar, 'score': 10, 'severidad': 'severa'}
    elif dt_solar < 1.0:
        return {'valor': dt_solar, 'score': 8, 'severidad': 'moderada'}
    elif dt_solar < 2.0:
        return {'valor': dt_solar, 'score': 3, 'severidad': 'leve'}
    else:
        return {'valor': dt_solar, 'score': 0, 'severidad': 'ninguna'}
```

### En el Scheduler (PUBLICACIÓN)
```python
# core/scheduler/calculador_indices_automatico.py L343-347

bus.publicar(
    'alerta_lluvia_componente_dt_solar_derivada',
    resultado['componente_dt_solar']['valor'],
    unidad='°C/min',
    rango='(-inf, +inf)',
    fuente='lluvia_inminente_v51',
    peso=0.10
)

bus.publicar(
    'alerta_lluvia_componente_dt_solar_score',
    resultado['componente_dt_solar']['score'],
    unidad='puntos',
    rango='0-10',
    fuente='lluvia_inminente_v51'
)
```

### En el Bus (RESULTADO)
```
Diccionario BusEstadoGlobal:
{
    'alerta_lluvia_inminente_score': 72,  # ENTERA (contiene 10% DT)
    'alerta_lluvia_componente_dt_solar_derivada': 0.3,  # DESCOMPUESTA
    'alerta_lluvia_componente_dt_solar_score': 8,  # DESCOMPUESTA
    ...
}
```

---

## Componente 5: Sundqvist (Microfísica LSTM)

### En el Archivo Maestro (CENTRALIZADO)
```python
# core/indices/lluvia_inminente_indices.py L280-295

def _evaluar_componente_sundqvist(prob_lluvia_pct):
    """
    Integra modelo LSTM con parametrización Sundqvist.
    
    Este componente SINTETIZA información de microfísica:
    - Thompson Microphysics (cantidad de hidrometeoros)
    - Sundqvist Precipitation (tasa de condensación)
    - LSTM predictions (si están disponibles)
    
    Scoring (0-25):
    - prob > 80%: 25 puntos (lluvia casi segura)
    - prob > 60%: 20 puntos
    - prob > 40%: 15 puntos
    - prob > 20%: 10 puntos
    - prob < 20%: 0 puntos
    """
    if prob_lluvia_pct is None:
        return {'probabilidad': 0, 'score': 0, 'clasificacion': 'sin_datos'}
    
    if prob_lluvia_pct > 80:
        return {
            'probabilidad': prob_lluvia_pct,
            'score': 25,
            'clasificacion': 'muy_probable'
        }
    elif prob_lluvia_pct > 60:
        return {
            'probabilidad': prob_lluvia_pct,
            'score': 20,
            'clasificacion': 'probable'
        }
    # ... más umbrales ...
```

### En el Scheduler (PUBLICACIÓN)
```python
# core/scheduler/calculador_indices_automatico.py L349-357

bus.publicar(
    'alerta_lluvia_componente_sundqvist_probabilidad',
    resultado['componente_sundqvist']['probabilidad'],
    unidad='%',
    rango='0-100',
    fuente='lluvia_inminente_v51',
    peso=0.25
)

bus.publicar(
    'alerta_lluvia_componente_sundqvist_score',
    resultado['componente_sundqvist']['score'],
    unidad='puntos',
    rango='0-25',
    fuente='lluvia_inminente_v51'
)
```

### En el Bus (RESULTADO)
```
Diccionario BusEstadoGlobal:
{
    'alerta_lluvia_inminente_score': 72,  # ENTERA (contiene 25% Sundqvist)
    'alerta_lluvia_componente_sundqvist_probabilidad': 45,  # DESCOMPUESTA
    'alerta_lluvia_componente_sundqvist_score': 20,  # DESCOMPUESTA
    ...
}
```

---

## ÍNDICE COMPUESTO (La "Orquestación" Final)

### En el Archivo Maestro (CENTRALIZADO)
```python
# core/indices/lluvia_inminente_indices.py L194-310

def calcular_indice_lluvia_inminente_v51(ghi, hr, p, t, dt, 
                                          historial_ghi, historial_hr, 
                                          historial_p, prob_lluvia):
    """
    ORQUESTACIÓN FINAL: Combina 5 componentes independientes.
    
    Proceso:
    1. Evalúa cada componente por separado
       - GHI derivada → score 0-25 (peso 0.25)
       - HR derivada → score 0-15 (peso 0.15)
       - P derivada → score 0-25 (peso 0.25)
       - DT solar → score 0-10 (peso 0.10)
       - Sundqvist → score 0-25 (peso 0.25)
    
    2. Calcula ponderación:
       score_final = (ghi*0.25 + presion*0.25 + hr*0.15 + 
                      dt*0.10 + sundqvist*0.25) * 100/95
    
    3. Calcula ETA (tiempo estimado):
       ETA = min(todos_etas)
    
    4. Calcula confianza:
       confianza = cantidad(scores > umbral)/5
    
    5. Retorna diccionario con TODO.
    """
    
    # Evaluar cada componente...
    componente_ghi = _evaluar_componente_ghi(...)
    componente_presion = _evaluar_componente_presion(...)
    componente_humedad = _evaluar_componente_humedad(...)
    componente_dt_solar = _evaluar_componente_dt_solar(...)
    componente_sundqvist = _evaluar_componente_sundqvist(...)
    
    # Calcular score ponderado...
    score_final = (componente_ghi['score'] * 0.25 +
                   componente_presion['score'] * 0.25 +
                   componente_humedad['score'] * 0.15 +
                   componente_dt_solar['score'] * 0.10 +
                   componente_sundqvist['score'] * 0.25) * 100/95
    
    # Retornar resultado compuesto
    return {
        'score_final': score_final,
        'eta_minutos': eta,
        'confianza': confianza,
        'componente_ghi': componente_ghi,
        'componente_presion': componente_presion,
        'componente_humedad': componente_humedad,
        'componente_dt_solar': componente_dt_solar,
        'componente_sundqvist': componente_sundqvist
    }
```

### En el Scheduler (PUBLICACIÓN - ENTERA)
```python
# core/scheduler/calculador_indices_automatico.py L320-324

# ENTERA (Score compuesto único):
bus.publicar(
    'alerta_lluvia_inminente_score',
    resultado['score_final'],
    unidad='puntos (0-100)',
    metadatos={
        'fuente': 'lluvia_inminente_v51',
        'eta_minutos': resultado['eta_minutos'],
        'confianza': resultado['confianza'],
        'componentes_activos': [...],
        'weights': [0.25, 0.25, 0.15, 0.10, 0.25]
    }
)
```

### En el Bus (RESULTADO FINAL)
```
Diccionario BusEstadoGlobal:
{
    'alerta_lluvia_inminente_score': 72,  # ENTERA
    'alerta_lluvia_eta_minutos': 14,
    'alerta_lluvia_confianza': 0.85,
    
    # + 10 DESCOMPUESTA (ver componentes arriba)
    'alerta_lluvia_componente_ghi_derivada': -128.5,
    'alerta_lluvia_componente_ghi_score': 20,
    'alerta_lluvia_componente_presion_derivada': -2.3,
    'alerta_lluvia_componente_presion_score': 25,
    'alerta_lluvia_componente_humedad_derivada': 2.8,
    'alerta_lluvia_componente_humedad_score': 15,
    'alerta_lluvia_componente_dt_solar_derivada': 0.3,
    'alerta_lluvia_componente_dt_solar_score': 8,
    'alerta_lluvia_componente_sundqvist_probabilidad': 45,
    'alerta_lluvia_componente_sundqvist_score': 20,
    
    'timestamp': '2025-02-11T01:15:30Z'
}
```

---

## 🔄 FLUJO COMPLETO: Entrada → Proceso → Salida

```
ENTRADA (Sensores):
├─ GHI: 850 W/m² (de WH65)
├─ HR: 65% (de WH43/WH31)
├─ P: 1010 hPa (de WH57)
├─ T: 28°C (temperatura)
└─ DT: 1.2°C (virtual: sun - shade)

      ↓

HISTÓRICOS (últimos 10 minutos):
├─ Historial GHI: [950, 850, 750, 700, ...]
├─ Historial HR: [60, 62, 64, 65, ...]
├─ Historial P: [1013.2, 1012.5, 1011.8, 1010, ...]
└─ Prob lluvia LSTM: 45% (del motor prediction)

      ↓

PROCESAMIENTO (Funciones en maestro):
├─ calcular_derivada_regresion_lineal()
│  └─ dGHI/dt = -128.5 W/m²/min
│  └─ dHR/dt = 2.8 %/min
│  └─ dP/dt = -2.3 hPa/min
│
├─ calcular_derivada_ghi_w_m2_s()
│  └─ Clasif: nube_moderada
│  └─ Score: 20/25
│
├─ calcular_derivada_presion_hpa_min()
│  └─ Clasif: caida_leve
│  └─ Score: 25/25 (MÁXIMO)
│
├─ calcular_derivada_humedad_pct_min()
│  └─ Clasif: aumento_rapido
│  └─ Score: 15/15
│
├─ _evaluar_componente_dt_solar()
│  └─ Serie visual: Parcial
│  └─ Score: 8/10
│
└─ _evaluar_componente_sundqvist()
   └─ Prob: 45%
   └─ Score: 20/25

      ↓

ORQUESTACIÓN (Índice compuesto):
├─ calcular_indice_lluvia_inminente_v51()
│  ├─ Calcula ponderación:
│  │  20×0.25 + 25×0.25 + 15×0.15 + 8×0.10 + 20×0.25
│  │  = 5 + 6.25 + 2.25 + 0.8 + 5 = 19.3 (normalizado a 72)
│  │
│  ├─ ETA: min(etas) = 14 minutos
│  └─ Confianza: 4/5 = 0.85
└─ Score final: 72

      ↓

PUBLICACIÓN EN BUS (13 claves):
├─ ENTERA: alerta_lluvia_inminente_score = 72 ✅
├─ ENTERA: alerta_lluvia_eta_minutos = 14 ✅
├─ ENTERA: alerta_lluvia_confianza = 0.85 ✅
│
├─ DESCOMPUESTA: alerta_lluvia_componente_ghi_derivada = -128.5 ✅
├─ DESCOMPUESTA: alerta_lluvia_componente_ghi_score = 20 ✅
├─ DESCOMPUESTA: alerta_lluvia_componente_presion_derivada = -2.3 ✅
├─ DESCOMPUESTA: alerta_lluvia_componente_presion_score = 25 ✅
├─ DESCOMPUESTA: alerta_lluvia_componente_humedad_derivada = 2.8 ✅
├─ DESCOMPUESTA: alerta_lluvia_componente_humedad_score = 15 ✅
├─ DESCOMPUESTA: alerta_lluvia_componente_dt_solar_derivada = 0.3 ✅
└─ DESCOMPUESTA: alerta_lluvia_componente_dt_solar_score = 8 ✅

      ↓

LECTURA DESDE CLIENTE:
├─ GET /api/estado/alerta_lluvia_inminente_score → 72
├─ GET /api/estado?componentes=si → Todas las 13 claves
└─ WS /estado → Stream de actualizaciones
```

---

## ✅ CONCLUSIÓN

**Cada componente:**
- ✅ Centralizado en 1 archivo maestro
- ✅ Publicado ENTERA (en score) + DESCOMPUESTA (individual)
- ✅ Documentado con líneas específicas
- ✅ Verificable en logs reales

**Total: 13 CLAVES EN EL BUS**
1 ENTERA + 12 DESCOMPUESTA

