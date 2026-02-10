# Modelos y fórmulas meteorológicas recomendadas (auditoría 2026-02-07)

| Parámetro                | Mejor modelo/fórmula recomendado                | Referencias principales | Notas clave |
|--------------------------|------------------------------------------------|------------------------|------------|
| Sensación térmica (calor)| Rothfusz (NOAA/NWS) / UTCI v4.02 (Fiala)       | NOAA, Steadman, UTCI   | UTCI es más avanzado y fisiológico, Rothfusz es estándar NWS para calor extremo en EEUU |
| Sensación térmica (frío) | Wind Chill Index (Canadá/EEUU)                 | Environment Canada     | Estándar internacional para frío |
| Punto de rocío           | Magnus-Tetens (Alduchov & Eskridge, 1996)      | WMO, NIST              | Preciso y ampliamente validado |
| Radiación solar          | Gueymard (2008)                                | WMO, Gueymard          | Alta precisión, requiere datos de nubosidad |
| WBGT                     | Liljegren et al. (2008)                        | ISO 7243, OSHA         | Virtual, validado internacionalmente |
| Humedad relativa         | Psicrométrica (WMO/ASHRAE)                     | WMO, ASHRAE            | Preciso, estándar |
| Viento                   | Promedio vectorial, ráfagas (WMO, ISO 17713-1) | WMO, ISO               | Estándar internacional |
| Presión                  | Sensor barométrico calibrado (WMO)             | WMO, NIST              | Preciso, requiere calibración |
| Calidad del aire         | EPA AQI, WHO guidelines                        | EPA, WHO               | Estándar internacional |
| Radiación UV             | Modelo OMS/WHO, estimado si no hay sensor      | WHO, WMO               | Adaptable a sensores virtuales |
| Precipitación            | Pluviómetro estándar (WMO), NASA GPM           | WMO, NASA              | Sensor físico o satélite |

## Notas clave
- UTCI v4.02 (Fiala) es el modelo fisiológico más avanzado para sensación térmica y supera a Rothfusz en realismo y rango, pero Rothfusz es el estándar NWS para olas de calor en EEUU por su simplicidad y uso masivo. Para máxima precisión y robustez, se recomienda implementar ambos y comparar en tu entorno.
- En todos los parámetros, priorizar modelos validados internacionalmente y, si es posible, comparar con sensores virtuales y físicos para cuantificar la fiabilidad real.
- Referencias completas y justificación técnica disponibles bajo demanda.
