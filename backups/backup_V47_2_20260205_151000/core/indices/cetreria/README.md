# Cetrería Local

Este módulo define los cálculos base para el índice de cetrería y sus sub‑índices. Las fórmulas parten de un esquema simple y son ampliables con refuerzos históricos y sensores auxiliares.

## Entradas esperadas
- `viento_medio` (m/s o km/h, consistente con el resto de sensores)
- `rachas`
- `temperatura`
- `punto_rocio`
- `humedad`
- `nubosidad_estimada`
- `radiacion`
- `var_t_5min`
- `lluvia_24h`
- `lluvia_1h`
- `sensacion_termica`

## Fórmulas base

- **viento_cetreria**
	- $100 * (0.6 * clamp(1 - viento\_medio / 30) + 0.3 * clamp(1 - rachas / 40) + 0.1 * clamp(1 - |rachas - viento\_medio| / 20))$
- **visibilidad_terreno**
	- $100 * (0.5 * nub\_factor + 0.3 * (1 - sat\_factor) + 0.2 * (1 - rh\_factor))$
- **termales_probabilidad**
	- $100 * (0.4 * rad\_factor + 0.2 * varT\_factor + 0.2 * nub\_factor + 0.1 * viento\_factor + 0.1 * hum\_factor)$
- **barro_campo**
	- $100 * (0.6 * lluvia\_factor + 0.3 * reciente\_factor - 0.3 * secado\_factor)$
- **confort_ave**
	- $100 * (0.4 * temp\_factor + 0.3 * sens\_factor + 0.2 * rad\_factor + 0.1 * viento\_factor)$
- **indice_seguridad_vuelo**
	- $100 * (0.4 * viento\_cetreria + 0.3 * visibilidad\_terreno + 0.2 * (1 - barro\_campo) + 0.1 * termales\_probabilidad)$
- **indice_cetreria**
	- $100 * (0.4 * indice\_seguridad\_vuelo + 0.3 * viento\_cetreria + 0.2 * visibilidad\_terreno + 0.1 * confort\_ave)$

## Salidas
- `viento_cetreria`
- `visibilidad_terreno`
- `termales_probabilidad`
- `barro_campo`
- `confort_ave`
- `indice_viento_cetreria`
- `indice_visibilidad_cetreria`
- `indice_termales`
- `indice_seguridad_vuelo`
- `indice_cetreria`

## Notas
- Si faltan datos críticos, el índice correspondiente devuelve `None`.
- `punto_rocio` se estima automáticamente cuando solo hay temperatura y HR.
- `riesgo_empaniamiento_optica` pertenece al módulo de Astronomía Local y se reutiliza en el panel de Cetrería.
- La variable `var_t_5min` se obtiene de la tendencia térmica corta (histórico reciente).
