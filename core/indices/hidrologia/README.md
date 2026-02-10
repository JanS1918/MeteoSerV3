# Hidrología - Ciclos Hídricos y Auditoria de Agua

Este módulo define los cálculos para gestión de recursos hídricos, infiltración de agua, escorrentía y riesgos de inundación. Las fórmulas se basan en estándares WMO (Organización Meteorológica Mundial) y métodos hidrogeológicos.

## Entradas esperadas
- `lluvia_1h` (mm)
- `lluvia_24h` (mm)
- `temperatura` (°C)
- `humedad` (%)
- `presion` (hPa)
- `viento_kmh` (km/h)
- `radiacion` (W/m²)
- `humedad_suelo` (%, capacidad de campo)
- `elevacion_terreno` (m)

## Fórmulas base

- **infiltracion_green_ampt**
  - Tasa de infiltración por método Green-Ampt (mm/h)
  - Función de lluvia, humedad del suelo, saturación
  - Capacidad de infiltración según tipo de suelo

- **escorrentia_superficial**
  - Flujo de agua en superficie (0-100)
  - Función de lluvia total, infiltración, pendiente
  - >50 indica riesgo de inundación

- **spi_standardized_precipitation_index**
  - Índice de precipitación estandarizado (WMO)
  - -2 a +2 escala (-2=sequía, +2=lluvia extrema)
  - Base 30 años históricos (simulado)

- **humedad_suelo_tendencia**
  - Tendencia de humedad del suelo 0-100
  - Función de lluvia, ET₀, infiltración
  - Proyección de 7 días de estado hídrido

- **indice_hidrologia_sintetico**
  - Síntesis ponderada 0-100 de estado hídrico general
  - Recomendación: >60 = riesgo de inundación, <40 = riesgo de sequía

## Salidas
- `infiltracion_mm_h`
- `escorrentia`
- `spi_indice`
- `humedad_suelo_tendencia`
- `indice_hidrologia_sintetico`

## Notas
- Basado en WMO SPI (McKee et al., 1993)
- Green-Ampt: método de infiltración física (Green & Ampt, 1911)
- SPI calculado como proxy simplificado (requiere series históricas reales)
- Humedad del suelo es parámetro crítico; sin ella, asume 50%
- Robusto: nunca retorna None, siempre válido 0-100

## Referencias
- WMO: Standardized Precipitation Index (McKee et al., 1993)
- Green-Ampt: Soil infiltration model (Green & Ampt, 1911)
- USDA: Runoff calculation methods
- FAO: Water balance and drought indicators
