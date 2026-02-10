# Listado global de sensores, sensores virtuales, predicciones, alertas y riesgos

## Sensores principales
- temperatura
- humedad
- presion
- viento
- lluvia (pluviómetro)
- radiacion
- humedad del suelo (WH51)


## Sensores virtuales de lluvia
- rain_sensor_norte
- rain_sensor_sur
- rain_sensor_este
- rain_sensor_oeste
- rain_sensor_frontal
- rain_sensor_orografica
- rain_sensor_frontal_componente_1
- rain_sensor_frontal_componente_2
- rain_sensor_frontal_componente_3
- rain_sensor_orografica_componente_1
- rain_sensor_orografica_componente_2
- rain_sensor_orografica_componente_3

## Sensores virtuales de tendencia y anomalía (auto-generados)
Para cada variable útil del sistema, existen sensores virtuales que calculan:
- **tendencia_[variable]**: Detecta si la variable sube o baja (ejemplo: tendencia_temperatura, tendencia_lluvia, tendencia_humedad, etc).
- **anomalia_[variable]**: Detecta si el último valor es anómalo respecto a su historial (ejemplo: anomalia_temperatura, anomalia_lluvia, anomalia_humedad, etc).

Variables cubiertas: temperatura, humedad, presion, viento, lluvia, radiacion, humedad_suelo, wbgt, stress_index, co2, pm25, pm10, uv, altitud.

Estos sensores virtuales están siempre activos, publicados en el bus y disponibles para cualquier cálculo, predicción, alerta, índice o riesgo.

## Predicciones
- rain_pred (predicción de lluvia)
- storm_pred (predicción de tormenta)

## Alertas
- Lluvia detectada (por tipo y dirección)
- Predicción de lluvia
- Predicción de tormenta

## Riesgos
- Riesgo de inundación (por acumulación de lluvia)
- Riesgo de sequía (por baja humedad del suelo)
- Riesgo de tormenta (por predicción y sensores virtuales)

## Otros sensores derivados
- ET0 (evapotranspiración de referencia)
- ET (evapotranspiración real)
- punto_rocio
- sensacion_termica
- densidad_aire
- presion_vapor
- humedad_absoluta

---
Todos estos sensores y variables están publicados en el bus y disponibles para cualquier cálculo, predicción, alerta o auditoría.

Si necesitas el listado en formato JSON, Excel o con detalles técnicos, indícalo y lo genero.
