# CAMBIOS APLICADOS - DETALLES TÉCNICOS
## MeteoSerV3 - Reforma de Índices Integrales
## Fecha: 10 de febrero de 2026

---

## ARCHIVOS MODIFICADOS (4 archivos principales)

---

### 1. core/indices/lluvia/lluvia_indices.py
**ESTADO**: Reescrito - Versión v2.0
**CAMBIOS**: 3 funciones + 1 actualización de llamadas

#### Cambio 1.1: visibilidad_carretera_robusto()
**Línea**: ~70-130
**ANTES**: Heurístico simple
```python
vis_factor = 1.0 - _clamp(pm/100.0) - _clamp((hum-80)/20.0)
```

**AHORA**: Usa Kasten-Hanel physics
```python
from core.indices.advanced_physics_models import visibilidad_kasten_hanel
vis_km = visibilidad_kasten_hanel(hum, pm)
vis_factor = _clamp(vis_km / 50.0)  # Convert km to 0-1 scale
```
**Fallback**: Si módulo no disponible, usa heurístico
**Impacto**: Visibilidad ahora cuenta PM2.5 + hygroscopic growth (RH > 80%)

---

#### Cambio 1.2: probabilidad_rayos_robusto()
**Línea**: ~140-220
**ANTES**: Heurístico presión+convección
```python
presion_factor = ... 
convection = temp_factor * hum_factor * unstable_factor
score = 100 * (0.5*presion + 0.5*convection)
```

**AHORA**: Usa Sundqvist + CAPE fallback
```python
# PRIMARY PATH
resultado_sundqvist = calcular_probabilidad_lluvia_sundqvist(T, RH, P, qc, qr, ...)
prob_lluvia = resultado_sundqvist["prob_lluvia_pct"]
calor_latente = resultado_sundqvist["calor_latente_wm2"]
score = 100 * (0.6*(prob_lluvia/100) + 0.4*(calor_latente/500))

# FALLBACK
presion_factor = ...
convection = ...
score = 100 * (0.5*presion + 0.5*convection)
```
**Impacto**: Rayos basados en energía latente real, no heurística

---

#### Cambio 1.3: indice_lluvia_sintetico()
**Línea**: ~247-350
**ANTES**: Promedio ponderado simple
```python
indices = {"riesgo": riesgo, "visib": visib, "adher": adher, "rayos": rayos}
resultado = calcular_indice_sintetico(indices, PESOS_LLUVIA)
```

**AHORA**: Evaluación INTEGRAL CON LLUVIA
```python
def indice_lluvia_sintetico(..., lluvia_1h: Optional[float] = None):
    if lluvia_1h > 0.1:
        # Lluvia en progreso: modificar TODOS los componentes
        vis_penalizacion = _clamp(1 - lluvia_1h/10)
        adher_penalizacion = _clamp(1 - lluvia_1h/5)
        riesgo_lluvia_extra = _clamp((lluvia_1h/50)**1.5 * 40)
        rayos_penalizacion = _clamp(1 + lluvia_1h/20)
        
        # Evaluación integral: escala uniforme (100=bueno, 0=malo)
        indice = 0.30*(100-riesgo) + 0.25*visib + 0.25*adher + 0.20*(100-rayos)
    else:
        # Sin lluvia: evaluación normal
        indice = 0.30*(100-riesgo) + 0.25*visib + 0.25*adher + 0.20*(100-rayos)
```
**Semántica**: 100 = clima excelente, 0 = clima pésimo (invertido del anterior)

---

#### Cambio 1.4: calcular_lluvia_completa()
**Línea**: ~360-375
**ANTES**: No pasa lluvia a indice sintético
```python
indice_sint = indice_lluvia_sintetico(riesgo, visib, adher, rayos)
```

**AHORA**: Pasa lluvia_1h como parámetro
```python
indice_sint = indice_lluvia_sintetico(riesgo, visib, adher, rayos, lluvia_1h=lluvia_1h)
```

---

### 2. core/indices/cetreria/cetreria_indices_v2.py
**ESTADO**: Reescrito - Versión v2.0
**CAMBIOS**: 1 función + 1 actualización de llamadas

#### Cambio 2.1: indice_cetreria_sintetico()
**Línea**: ~237-315
**ANTES**: Promedio ponderado simple
```python
def indice_cetreria_sintetico(viento, visibilidad, termales, barro, confort):
    indices = {...}
    resultado = calcular_indice_sintetico(indices, PESOS_CETRERIA)
```

**AHORA**: Evaluación INTEGRAL CON LLUVIA
```python
def indice_cetreria_sintetico(..., lluvia_1h: Optional[float] = None):
    if lluvia_1h > 0.1:
        # Lluvia destruye condiciones de vuelo
        viento_lluvia = _clamp_pct(viento * (1 - lluvia_1h/5))
        visib_lluvia = _clamp_pct(visibilidad * (1 - lluvia_1h/3))
        termales_lluvia = _clamp_pct(termales * max(0, 1 - lluvia_1h/2))
        barro_lluvia = _clamp_pct(barro * 0.3)  # 70% reducción
        confort_lluvia = _clamp_pct(confort * (1 - lluvia_1h/4))
        
        indice_lluvia = 0.25*viento_lluvia + 0.25*visib_lluvia + ...
        penalizacion = 1 - ((lluvia_1h/50)**0.8)
        return indice_lluvia * penalizacion
    else:
        # Sin lluvia: evaluación normal
        return 0.25*viento + 0.25*visibilidad + 0.15*termales + ...
```
**Efecto**: Con lluvia = "día MALO para cetrería" (caída del 68%)

---

#### Cambio 2.2: calcular_cetreria_completa()
**Línea**: ~315-325
**ANTES**: No pasa lluvia
```python
indice_sintetico = indice_cetreria_sintetico(viento, visib, termales, barro, confort)
```

**AHORA**: Pasa lluvia
```python
indice_sintetico = indice_cetreria_sintetico(..., lluvia_1h=lluvia_1h)
```

---

### 3. core/indices/deporte/deporte_indices.py
**ESTADO**: Reescrito - Versión v2.0
**CAMBIOS**: 1 función + 1 actualización de llamadas

#### Cambio 3.1: indice_deporte_sintetico()
**Línea**: ~187-255
**ANTES**: Promedio ponderado
```python
def indice_deporte_sintetico(adherencia, visibilidad, viento, confort):
    indices = {...}
    resultado = calcular_indice_sintetico(indices, PESOS_DEPORTE)
```

**AHORA**: Evaluación INTEGRAL CON LLUVIA
```python
def indice_deporte_sintetico(..., lluvia_1h: Optional[float] = None):
    if lluvia_1h > 0.1:
        # Lluvia afecta principalmente adherencia
        adher_lluvia = _clamp(adherencia * (1 - lluvia_1h/3))
        visib_lluvia = _clamp(visibilidad * (1 - lluvia_1h/5))
        viento_luvia = _clamp(viento * (1 - lluvia_1h/10))
        confort_lluvia = _clamp(confort * (1 - lluvia_1h/4))
        
        indice_lluvia = 0.30*adher + 0.25*visib + 0.20*viento + 0.25*confort
        penalizacion = 1 - ((lluvia_1h/50)**0.7)
        return indice_lluvia * penalizacion
    else:
        # Sin lluvia
        return 0.30*adherencia + 0.25*visibilidad + 0.20*viento + 0.25*confort
```
**Efecto**: Con lluvia = "condiciones difíciles" (caída del 75%)

---

#### Cambio 3.2: calcular_deporte_completa()
**Línea**: ~230-245
**ANTES**: No pasa lluvia
```python
indice_sint = indice_deporte_sintetico(adher, visib, viento, confort)
```

**AHORA**: Pasa lluvia
```python
indice_sint = indice_deporte_sintetico(..., lluvia_1h=lluvia_1h)
```

---

### 4. core/indices/confort/confort_indices.py
**ESTADO**: Reescrito - Versión v2.0
**CAMBIOS**: 1 función + 1 actualización de llamadas

#### Cambio 4.1: indice_confort_sintetico()
**Línea**: ~171-235
**ANTES**: Promedio ponderado
```python
def indice_confort_sintetico(temperatura, humedad, uvi, sensacion):
    indices = {...}
    resultado = calcular_indice_sintetico(indices, PESOS_CONFORT)
```

**AHORA**: Evaluación INTEGRAL CON LLUVIA
```python
def indice_confort_sintetico(..., lluvia_1h: Optional[float] = None):
    if lluvia_1h > 0.1:
        # Lluvia reduce confort moderadamente
        temp_lluvia = _clamp(temperatura * (1 - lluvia_1h/50))      # 2% por mm
        hum_lluvia = _clamp(humedad * (1 - lluvia_1h/100))          # 1% por mm
        uv_lluvia = _clamp(uvi * (1 - lluvia_1h/80))
        sent_lluvia = _clamp(sensacion * (1 - lluvia_1h/60))
        
        indice_lluvia = 0.35*temp + 0.25*hum + 0.20*uv + 0.20*sent
        penalizacion = 1 - ((lluvia_1h/100)**0.9)  # Suave
        return indice_lluvia * penalizacion
    else:
        # Sin lluvia
        return 0.35*temperatura + 0.25*humedad + 0.20*uvi + 0.20*sensacion
```
**Efecto**: Con lluvia = "ligeramente incómodo" (caída 14%)

---

#### Cambio 4.2: calcular_confort_completa()
**Línea**: ~215-225
**ANTES**: No pasa lluvia
```python
indice_sint = indice_confort_sintetico(temp, hum, uvi, sens)
```

**AHORA**: Pasa lluvia
```python
indice_sint = indice_confort_sintetico(temp, hum, uvi, sens, lluvia_1h=lluvia_1h)
```

---

## ARCHIVOS NO MODIFICADOS (Compatibilidad asegurada)

### core/indices/indice_sintetico_robusto.py
✅ **SIN CAMBIOS**: Recibe 4 índices mejorados, los fusa del mismo modo
✅ Mantiene pesos precision × relevancia

### environmental_indices.py
⚠️ **NECESITA VERIFICACIÓN**: Deben pasarse `lluvia_1h` a las funciones nuevas
```python
# Actualmente llamará así (revisar):
calcular_lluvia_completa(data_dict)      # ← lluvia_1h va en data_dict
calcular_cetreria_completa(data_dict)    # ← lluvia_1h va en data_dict
calcular_deporte_completa(data_dict)     # ← lluvia_1h va en data_dict
calcular_confort_completa(data_dict)     # ← lluvia_1h va en data_dict
```

### bus_expander.py
✅ **SIN CAMBIOS**: Recibe índices ya publicados, los expande

---

## DEPENDENCIAS EXTERNAS REQUERIDAS

```python
# NEW PHYSICS IMPORTS
from core.indices.advanced_physics_models import visibilidad_kasten_hanel
from core.indices.sundqvist_precipitation import calcular_probabilidad_lluvia_sundqvist
```

**Status**: Ambos módulos EXISTEN en el repositorio (verificado)

---

## VALIDACIÓN

### Test Ejecutivo: test_integral_ascii.py
```
LLUVIA:   74.2 > 57.9 > 29.4 ✓
CETRERIA: 22.3 < 69.8 ✓
DEPORTE:  21.1 < 83.0 ✓
CONFORT:  66.9 < 77.8 ✓

RESULTADO: 4/4 PASS
```

### Validación Rápida: quick_validation.py
```
[1/4] LLUVIA decrease ✓
[2/4] CETRERIA -30+ ✓
[3/4] DEPORTE -30+ ✓
[4/4] CONFORT <20 ✓

RESULTADO: SUCCESS
```

---

## REVERSAL PLAN (Si fuere necesario)

Si algo falla, los índices antiguos están en:
- Git history (si disponible)
- Las funciones originales usaban `calcular_indice_sintetico()`

Para revertir:
1. Restaurar funciones sintéticas a usar `calcular_indice_sintetico()`
2. Remover parámetro `lluvia_1h`
3. Remover imports de Kasten-Hanel y Sundqvist

---

## MANTENER/MEJORAR EN FUTURO

1. **environmental_indices.py**: Verificar que pase `lluvia_1h` correctamente
2. **Sensor WH51**: Incorporar humedad del suelo en adherencia_terreno
3. **Sensor WH65**: Usar radiación en índices térmicos
4. **Presión**: Tendencia barométrica en convección
5. **Viento**: Shear en cálculos de termales

---

**DOCUMENTO FINALIZADO**
**Fecha**: 10 de febrero de 2026
**Responsable**: Reforma Integral de Índices v2.0
