# 🗺️ PLANO OROGRÁFICO Y ENTORNO METEOSER

**Fecha de generación:** 6 de febrero de 2026

---

## 1. Coordenadas y Altitud
- Latitud: (consultar system.location.get("latitud"))
- Longitud: (consultar system.location.get("longitud"))
- Altitud: (consultar system.location.get("altitud"))
- Origen: manual/gps/SRTM

## 2. Orografía y relieve
- Altitud SRTM: (system.location.load_altitude_srtm())
- Relieve local: (consultar SRTM tiles, pendiente, orientación)
- Pendiente media: (calcular a partir de SRTM)
- Orientación dominante: (calcular a partir de SRTM)
- Distancia a mar: (calcular desde lat/lon)
- Distancia a montaña: (calcular desde SRTM)

## 3. Tipo de suelo
- Suelo dominante: (consultar sensor WH51 o base de datos local)
- Humedad suelo: (system.data["humedad_suelo"])
- Textura: (arcilloso, arenoso, limoso, mixto)
- Profundidad: (consultar base de datos local)
- Capacidad de retención: (consultar base de datos local)

## 4. Vegetación y entorno
- Vegetación dominante: (consultar base de datos local o sensores)
- Cobertura vegetal: (porcentaje estimado)
- Cultivos presentes: (consultar base de datos local)
- Árboles/arbustos: (consultar base de datos local)
- Estado fenológico: (consultar base de datos local)

## 5. Sensores y hardware
- WH65: exterior completo (T, HR, presión, viento, lluvia, radiación, UV)
- WH57: rayos
- WH31: interior (T/HR extra)
- WH51: suelo
- HP2550A: centraliza y sincroniza
- Otros: PM25, PM10, nubosidad, LW infrarrojo nocturno

## 6. Variables ambientales
- Temperatura
- Humedad
- Presión barométrica
- Radiación global
- UV index
- Lluvia / lluvia_rate
- Viento (velocidad/dirección)
- PM25, PM10
- Nubosidad

## 7. Fórmulas y cálculos activos
- Psicrometría Hardy NIST
- Densidad aire OMM/WMO
- Gas ideal
- Radiación solar REST2 Gueymard
- WBGT Liljegren
- UTCI v4.02/v2
- FAO-56 Penman-Monteith
- Wright nocturno
- Riesgos (calor, frío, helada, tormenta)
- Alertas meteorológicas
- Tendencias y cambios rápidos
- Predicciones ML (LSTM)
- Predicciones físicas (CAPE, LCL, microfísica, Sundqvist, etc.)
- Validación física, anomalías, outliers
- Auto-discovery y metadatos

## 8. Fórmulas de Arco Solar y Lunar (implementación MeteoSer)

### 🌞 Arco Solar (MeteoSer V49)

**Fórmula:**

```
arco_solar = max(0, sin(elevacion_solar_rad))
# elevacion_solar_rad = ángulo de elevación solar en radianes (SPA NREL + Ciddor)
# Se publica en el bus como 'arco_solar' y 'elevacion_solar_deg'
```

- **Ventaja:** Solo depende de la física solar real, sin heurísticos ni tablas. Permite calcular radiación, día híbrido y coherencia luz con máxima precisión.
- **Referencia:** [core/arcos_solares.py], [core/indices/astronomia_recursiva.py]

### 🌙 Arco Lunar (MeteoSer V49)

**Fórmula:**

```
arco_lunar = max(0, sin(elevacion_lunar_rad))
# elevacion_lunar_rad = ángulo de elevación lunar en radianes (algoritmo Meeus optimizado)
# Se publica en el bus como 'arco_lunar' y 'elevacion_lunar_deg'
```

- **Ventaja:** Permite modelar la influencia lunar en radiación nocturna, humedad y ciclos circadianos. Precisión sub-grado.
- **Referencia:** [core/arcos_solares.py], [core/indices/astronomia_recursiva.py]

(Altitud SRTM: system.location.load_altitude_srtm() ← API real SRTM integrada)

## 9. Llamadas y endpoints principales
- `/api/panel/superior` (coordenadas, altitud, orografía)
- `/api/panel/central` (variables ambientales, radiación, WBGT, UTCI)
- `/api/panel/inferior` (tendencias, predicciones, alertas)
- `/api/sensores/historial` (histórico de sensores)
- `/api/virtuales` (sensores virtuales)
- `/api/predicciones` (predicciones ML y físicas)
- `/api/validacion` (anomalías, outliers)
- `/api/entorno` (vegetación, suelo, cultivos)
- `/api/orografia` (relieve, pendiente, orientación)

## 10. Datos externos y bases de datos
- SRTM (altitud, relieve)
- SoilGrids (tipo de suelo, textura, profundidad)
- Copernicus (vegetación, cultivos)
- OpenStreetMap (entorno, distancias)
- MeteoSer local (histórico, calibración)

## 11. Referencias internas
- [core/system/bus_expander.py] (publica todo al bus)
- [core/indices/environmental_indices.py] (fórmulas físicas)
- [core/virtual/virtual_sensors.py] (sensores virtuales)
- [core/prediction/prediction_engine.py] (predicción ML)
- [core/validation/sensor_anomaly_detector.py] (anomalías)
- [core/validation/outlier_detector.py] (outliers)
- [core/validation/sensor_validator_cascada.py] (validación)

---

**Este archivo es el plano maestro del entorno, orografía, suelo, vegetación, sensores, variables, fórmulas y endpoints de MeteoSer.**
Puedes consultarlo para saber qué tienes, qué se calcula, y dónde buscar cada dato.
