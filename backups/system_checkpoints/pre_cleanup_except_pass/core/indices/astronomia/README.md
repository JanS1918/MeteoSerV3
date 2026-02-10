# Astronomía Local

Este módulo consolida los indicadores que ayudan a evaluar la calidad del cielo nocturno con datos reales de MeteoSer. La lógica combina sensores ambientales, cálculos astronómicos y un índice compuesto de observación.

## Objetivo

- Determinar horas útiles de observación nocturna y calidad de cielo.
- Detectar inconsistencias entre luz astronómica y sensores reales.
- Priorizar condiciones favorables para observación visual o instrumental.

## Entradas principales

Sensores y derivados utilizados (según disponibilidad):

- `temperatura`, `humedad`, `viento`.
- `radiacion`, `uv`.
- `nubosidad_estimada` (derivado), `radiacion_teorica`.
- `fase_lunar` (derivado astronómico).
- `riesgo_niebla`, `riesgo_empaniamiento_optica`, `seeing_termico_basico`.

## Índices generados

### Derivados base

- `transparencia_atmosferica`: sequedad + nubosidad + radiación.
- `riesgo_empaniamiento_optica`: riesgo de empañamiento óptico por rocío/HR/viento.
- `seeing_termico_basico`: seeing térmico por variaciones de temperatura y viento.
- `fase_lunar`: % de iluminación lunar.
- `cielo_observable_nocturno`: calidad nocturna 0–100.

### Compuestos y contexto astronómico

- `duracion_noche_h`: horas de noche según duración de día.
- `ventana_observacion_nocturna`: horas útiles según calidad del cielo.
- `indice_cielo_astronomico`: índice 0–100 que combina calidad y ventana nocturna.
- `indice_cielo_astronomico_nivel`: clasificación textual (`buena`, `regular`, `mala`).

### Sincronización astronómica/híbrida

Se calcula `amanecer_astronomico` y `atardecer_astronomico` (por lat/lon). Luego se ajusta un amanecer/atardecer híbrido cuando los sensores de luz (`radiacion`, `uv`) detectan un desfase cercano, produciendo:

- `amanecer_hibrido`, `atardecer_hibrido`
- `es_dia_astronomico`, `es_dia_sensor`
- `desvio_amanecer_min`, `desvio_atardecer_min`
- `inconsistencia_luz`, `inconsistencia_sensor_luz`, `inconsistencia_hibrida`

## Fórmulas principales

### Seeing térmico básico

$$
seeing = 100 \cdot (0.6 \cdot \frac{\Delta T_{5m}}{3} + 0.4 \cdot \frac{viento}{8})
$$

### Cielo observable nocturno

$$
calidad\_base = 0.5 \cdot (1 - nub) + 0.5 \cdot transp
$$

$$
penal = 0.4 \cdot niebla + 0.2 \cdot emp + 0.2 \cdot seeing + penal\_luna
$$

$$
calidad = 100 \cdot (calidad\_base - penal)
$$

La penalización lunar aumenta con la iluminación:

- $0\%$ si fase $\le 20$.
- $0.1\cdot fase$ si $20 < fase \le 50$.
- $0.25\cdot fase$ si $50 < fase \le 80$.
- $0.4\cdot fase$ si fase $> 80$.

### Ventana de observación nocturna

$$
ventana = duracion\_noche\_h \cdot \frac{cielo\_observable}{100}
$$

### Índice de cielo astronómico

$$
indice\_cielo = 100 \cdot (0.7 \cdot \frac{cielo\_observable}{100} + 0.3 \cdot \frac{ventana}{6})
$$

## Salida en UI

- Panel “Astronomía local” con `indice_cielo_astronomico`.
- Overlay con detalle de: nubosidad, transparencia, niebla, empañamiento óptico, seeing, fase lunar, ventana nocturna, duración de noche y amanecer/atardecer.

## Integración y catálogo

Los índices de astronomía están catalogados en `core/indices/index_catalog.py` con la categoría `astronomia`. Esto permite:

- Mostrar los índices en el panel.
- Exponerlos en la API de estado.
- Usarlos en recomendaciones (`unified_recommendation_engine`).

## Notas operativas

- Las métricas derivadas se marcan como `estimado` cuando faltan sensores directos.
- La inconsistencia entre luz astronómica y sensores reales se expone para validación manual.
- El módulo es compatible con calibración global por feedback.
