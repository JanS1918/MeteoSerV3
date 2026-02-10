# Riego - Gestión Agrícola de Agua

Este módulo define los cálculos para necesidad de riego y balance hídrico agrícola. Las fórmulas se basan en referencias de la FAO y USDA sobre evapotranspiración, infiltración y estrés hídrico.

## Entradas esperadas
- `lluvia_1h` (mm)
- `lluvia_24h` (mm)
- `temperatura` (°C)
- `radiacion` (W/m²)
- `humedad` (%)
- `viento_kmh` (km/h)
- `humedad_suelo` (%, capacidad de campo)

## Fórmulas base

- **balance_hidrico_neto**
  - ΔH = Lluvia - ET₀ - Escorrentía - Infiltración
  - 100 = ganancia neta (>2mm), 0 = pérdida severa (<-3mm)

- **et0_fao56**
  - Evapotranspiración de referencia FAO-56 (Penman-Monteith)
  - Función de radiación, temperatura, viento, humedad

- **estres_cultivo**
  - Factor de estrés 0-1 (1 = sin estrés, 0 = estrés crítico)
  - Parametrizable por tipo de cultivo y suelo
  
- **disponibilidad_agua_cultivable**
  - Días hasta sequedad del suelo
  - Considerando ET₀ y contenido de agua actual

- **eficiencia_infiltracion**
  - Ratio infiltración/escorrentía (Green-Ampt)
  - 100% = todo se infiltra, 0% = pura escorrentía

- **indice_riego_sintetico**
  - Síntesis ponderada 0-100 de todos los sub-índices
  - Recomendación: >60 = riego recomendado

## Salidas
- `balance_hidrico_neto`
- `et0_fao56`
- `estres_cultivo`
- `disponibilidad_agua`
- `eficiencia_infiltracion`
- `indice_riego_sintetico`

## Notas
- Basado en estándares FAO-56 (Allen et al., 1998)
- Infiltración calculada con método Green-Ampt (1911)
- Si faltan datos críticos, usa valores históricos como fallback
- La variable `humedad_suelo` es esencial; sin ella, asume 50% capacidad de campo
- Robusto: nunca retorna None, siempre válido 0-100

## Referencias
- FAO-56: Crop evapotranspiration (Allen et al., 1998)
- Green-Ampt: Soil infiltration model (Green & Ampt, 1911)
- USDA: Soil water availability by soil type
