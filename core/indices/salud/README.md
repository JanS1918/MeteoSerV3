# Salud - Salud Pública y Riesgos Ambientales

Este módulo define los cálculos para evaluación de condiciones de salud ambiental y riesgos de exposición. Las fórmulas se basan en estándares OMS, ASHRAE, e ISO para calidad del aire, radiación UV, y confort térmico extremo.

## Entradas esperadas
- `temperatura` (°C)
- `humedad` (%)
- `radiacion` (W/m²)
- `uv` (índice UVI, 0-16+)
- `viento_kmh` (km/h)
- `visibilidad_km` (km)
- `punto_rocio` (°C)
- `presion` (hPa)
- `hora` (0-23)
- `dia` (1-31)
- `mes` (1-12)
- `anio` (YYYY)

## Fórmulas base

- **uvi_personal_robusto**
  - Exposición UV personalizada según hora del día
  - OMS/WMO 0-16+ escala (0=bajo, 16+=extremo)
  - Penalización por hora solar 10-15h

- **calor_extremo**
  - Probabilidad de golpe de calor (0-100)
  - Función de temperatura, humedad, radiación
  - >35°C + humedad marca riesgo crítico

- **frio_extremo**
  - Probabilidad de hipotermia/congelación (0-100)
  - Función de temperatura, viento (wind chill)
  - <-5°C + viento marca riesgo crítico

- **helada_local_riesgo**
  - Riesgo de helada en cultivos/infraestructura
  - Función de punto de rocío, temperatura nocturna, viento
  - Método Yates-McLean

- **calidad_aire_interior**
  - Calidad de aire interior estimado (0-100)
  - Inverso de humedad y point de rocío (proxy CO₂)
  - ASHRAE 62.1 referencia

- **calidad_aire_exterior**
  - Calidad de aire exterior por visibilidad (0-100)
  - Proxy de contaminación por visibilidad
  - <5km = aire contaminado

- **indice_salud_sintetico**
  - Síntesis ponderada 0-100 de exposición de salud
  - Recomendación: >70 = día saludable

## Salidas
- `uvi_personal`
- `calor_extremo`
- `frio_extremo`
- `helada_riesgo`
- `aire_interior`
- `aire_exterior`
- `indice_salud_sintetico`

## Notas
- Basado en OMS/WMO UV guidelines
- ASHRAE 62.1-2019 para calidad de aire interior
- Wind chill: modelo Osczevski-Bluestein (2005)
- Helada: método Yates-McLean simplificado
- Nota: índice invertido (bajo=mala salud, alto=buena salud)
- Robusto: nunca retorna None, siempre válido 0-100

## Referencias
- OMS/WMO: UV Index and risk categories
- ASHRAE 62.1-2019: Ventilation and acceptable indoor air quality
- ISO 12944: Corrosion protection of steel structures by coatings
- Osczevski & Bluestein: Wind chill temperature calculation (2005)
