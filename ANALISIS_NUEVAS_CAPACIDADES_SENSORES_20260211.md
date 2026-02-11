# Nuevas Capacidades y Oportunidades con Sensores Físicos y Virtuales

Fecha: 11 de febrero de 2026

---


## 1. ¿Qué puertas se abren con los nuevos sensores?

### Predicciones y alertas mejoradas o nuevas
- Predicción precisa de enfermedades fúngicas y estrés hídrico (humedad foliar, temp. hoja/suelo).
- Alertas de calidad de aire interior/exterior (CO₂, PM1, PM2.5, COV).
- Detección de fugas y consumos anómalos (sensor de fugas, caudalímetros).
- WBGT y estrés térmico real (globo negro WN38, bulbo húmedo). El WN38 marcará la mayor diferencia en precisión y cumplimiento normativo.
- Mapeo de microclimas y zonas críticas (más variables físicas, interpolación).

### Nuevos índices y sensores virtuales posibles
- Índice de confort térmico avanzado (globo negro, bulbo húmedo, temp. aire, humedad, viento).
- Índice de calidad de aire compuesto (CO₂, PM1, PM2.5, COV, humedad, temp.).
- Índice de riesgo de enfermedades (ML: humedad foliar, temp. hoja, lluvia, viento).
- Índice de eficiencia de riego (humedad foliar, suelo, consumo de agua, fugas).
- Detección de eventos anómalos (fugas, humedad, caudal, patrones de uso).
- Sensores virtuales de interpolación (zonas sin cobertura física).


### Ejemplos concretos de nuevas capacidades
- Alertas automáticas de ventilación (CO₂ real en invernaderos, aulas, oficinas).
- Predicción de aparición de hongos tras lluvias intensas.
- Detección y corte automático de fugas de agua.
- Mapas de microclimas para optimizar riego y energía.
- Validación de condiciones laborales seguras (WBGT físico, alertas en tiempo real).
- WBGT real y certificable gracias al WN38 (globo negro), diferencial para seguridad y cumplimiento normativo.
---

## 4. Qué podemos ir preparando antes de que lleguen los sensores

1. Definir y documentar los modelos de datos para cada nuevo sensor (WN38, WN34D, WN35, WH46D, WN36, WH55).
2. Crear o adaptar parsers y validadores para los nuevos formatos de datos.
3. Preparar endpoints y lógica de ingestión para recibir datos de los nuevos sensores.
4. Diseñar simuladores de datos (mocks) para pruebas y desarrollo sin hardware físico.
5. Actualizar y ampliar los tests unitarios y de integración para cubrir los nuevos sensores y escenarios.
6. Revisar y modularizar la lógica de fusión física/virtual para facilitar la integración.
7. Planificar la actualización de dashboards y reportes para mostrar los nuevos índices y alertas.
8. Documentar el flujo de integración y los puntos de extensión para facilitar la puesta en marcha.
9. Preparar scripts de migración o limpieza para eliminar redundancias y simulaciones obsoletas cuando los sensores estén activos.
10. Revisar la arquitectura para asegurar escalabilidad y robustez ante el aumento de datos y variables.

---

## 2. ¿Estamos en el techo?

No. Los nuevos sensores no solo sustituyen virtuales, sino que:
- Permiten crear índices y modelos antes imposibles o poco fiables.
- Habilitan validación cruzada físico + virtual (mayor robustez).
- Abren la puerta a modelos predictivos de IA mucho más precisos.
- Permiten cumplir normativas y certificaciones (WBGT real, calidad de aire laboral).

---

## 3. Oportunidades adicionales y sugerencias

- Integración con sistemas de riego, HVAC, alarmas y mantenimiento.
- Personalización de alertas según perfil de usuario o zona.
- Generación de reportes automáticos para auditoría y cumplimiento.
- Uso de sensores de fugas para control de llenado, detección de reboses o usos no autorizados.
- Simulación avanzada de escenarios críticos (fuga, contaminación, estrés térmico).
- Creación de dashboards en tiempo real con mapas de calor y alertas inteligentes.
- Implementación de aprendizaje automático para predicción de eventos extremos.
- Uso de sensores virtuales como respaldo ante fallos físicos o para interpolar datos en zonas sin cobertura.

---

## 4. Resumen

La llegada de estos sensores físicos avanzados no solo mejora la precisión, sino que habilita nuevas predicciones, índices y automatizaciones que antes eran imposibles o muy poco fiables. El sistema sube de nivel en precisión, robustez y valor predictivo real, abriendo nuevas oportunidades de innovación y servicio.

---

_Archivo generado automáticamente por GitHub Copilot (GPT-4.1) a petición del usuario._

---

## 7. Mejoras propuestas (energía, dominancia y gobernanza)

Esta sección adapta el análisis previo para incorporar las mejoras de gobernanza y dinámica dominante solicitadas: Índice de Energía Atmosférica Disponible (IEAD), Inercia Nocturna, Dominant Driver Selector, System Reliability Score (SRS) e Índice de Incertidumbre Intrínseca.

### 7.1 Índice de Energía Atmosférica Disponible (IEAD)
- Propósito: elevar una variable rectora que sintetice la "energía" útil en la columna atmosférica local.
- Entradas propuestas: Radiación neta (Rn), gradiente térmico (superficie ↔ aire), viento (turbulencia proxy), humedad relativa (inversa), variabilidad radiativa.
- Salida: IEAD (0–100). IEAD gobierna la agresividad de motores convectivos, umbrales adaptativos y escala de predicción 30–60 min.

### 7.2 Inercia Nocturna
- Propósito: añadir memoria física nocturna que capture condiciones acumuladas (recarga/descarga térmica) y su efecto en heladas/rocío/niebla.
- Entradas: Rn acumulada nocturna (negativa), duración viento bajo, HR sostenida, gradiente suelo–aire.
- Salida: INERCIA (unidad relativa). Usada por motores de helada, condensación estructural y predicción de niebla.

### 7.3 Dominant Driver Selector
- Propósito: seleccionar 1–2 drivers dominantes (radiación / estabilidad / humedad / viento / contaminación) por ciclo y aplicar pesos únicamente a los motores relevantes.
- Mecanismo: calcular score por driver y aplicar hysteresis para evitar cambios bruscos. Drivers seleccionados filtran features para modelos cortos.

### 7.4 Índice de Incertidumbre Intrínseca
- Propósito: cuantificar incertidumbre física real (no solo calidad de sensor) basada en variabilidad y cobertura.
- Entradas: std(rad_short), std(wind), cambio rápido de nubosidad, cobertura sensorial (número sensores activos).
- Salida: UNC (0–1). Reduce confianza y fuerza modos conservadores si alto.

### 7.5 System Reliability Score (SRS)
- Propósito: métrica operativa por minuto que sintetiza integridad de sensores, coherencia física y conflictos entre módulos.
- Uso: gating de ajustes automáticos, degradación controlada, activación de circuit breaker de autoajuste.

---

## 8. Fórmulas esbozo y reglas rápidas

Estas fórmulas son iniciales y deben calibrarse con histórico local.

- IEAD ≈ w1*Rn_norm + w2*gradT_norm + w3*viento_norm + w4*(1−HR_norm) + w5*varRad_norm
	- Normalizar cada término a [0,1], w_i suman 1. Ajustar por calibración local.

- Inercia ≈ α*sum(Rn_neg_acumulada_nocturna) + β*(tiempo_viento_bajo_h) + γ*(HR_sostenida_pct) + δ*(grad_suelo_aire_norm)

- UNC (Incertidumbre) ≈ normalize(std_rad_short + std_wind + variability_cloud + sensor_coverage_factor)

- SRS ≈ f(sensor_health, physical_coherence_score, alert_saturation_ratio, model_confidence)
	- Devuelve 0–100; si SRS < umbral → activar modo conservador

Reglas rápidas:
- Si IEAD bajo y Dominant Driver = estabilidad → reducir probabilidad convectiva y aumentar probabilidad de niebla/helada.
- Si Inercia alta nocturna → elevar riesgo helada y condensación estructural.
- Si UNC elevada → degradar predicción ML a rule-based y avisar en metadata.

---

## 9. APIs internas y contrato de estado

Propuesta de endpoint interno que exponen el estado rector:

GET /internal/state
Response JSON:
{
	"timestamp": "ISO",
	"iead": 67.3,
	"inercia": 12.5,
	"dominant_driver": "radiacion",
	"dominant_scores": {"radiacion": 0.82, "viento": 0.12},
	"uncertainty": 0.23,
	"srs": 89,
	"explanations": ["IEAD alto por radiación neta", "SRS penalizado por PM inconsistent"]
}

Este endpoint sirve para gobernar motores y para exponer métricas en dashboards y alertas.

---

## 10. Prioridades de implementación (prácticas)

1. Implementar Motor de Coherencia Física Global (produce physical_coherence_score y explanations).
2. Exponer `GET /internal/state` con IEAD, Inercia, Dominant Driver, UNC y SRS.
3. Dominant Driver Selector con hysteresis y reglas de filtrado de features.
4. Separación de aprendizaje en 3 velocidades y gating por SRS.
5. Añadir índices virtuales críticos: Rn integrado, Índice de Mezcla Atmosférica, Índice Fúngico Dinámico.

---

## 11. Métricas a monitorizar desde el día 1

- `srs_minute` (System Reliability Score)
- `iead_value` y `iead_trend`
- `inercia_nocturna`
- `dominant_driver` (label + score)
- `uncertainty_index`
- `alert_saturation_ratio`
- Drift por sensor (24h vs 7d)

---

_Actualizado: incorpora propuestas de gobernanza, energía disponible y métricas operativas para preparar la integración de los nuevos sensores y convertir MeteoSer en un núcleo meteorológico coherente._

---

## 12. Precedencia y limitadores físicos (formalización)

Para evitar ambigüedad operacional, se define la precedencia absoluta entre capas y los limitadores físicos superiores (hard limits). Esta tabla es la referencia para cualquier motor:

1. Seguridad física (hard thresholds) — no negociable: condiciones que fuerzan acciones (ej. T < punto de congelación en superficie → alerta helada inmediata).
2. Coherencia física global — validez energética y balance radiativo; penaliza/impide decisiones incompatibles con la conservación física.
3. Energía disponible (IEAD) — regula agresividad convectiva y límites máximos de efectos (ej. prob lluvia máxima permisible dada IEAD).
4. Régimen atmosférico (Dominant Driver) — determina qué subsistemas tienen prioridad de influencia.
5. Motores especializados (decisiones de dominio) — ejecutan lógicas específicas sujetas a lo anterior.

Limitadores físicos (ejemplos concretos):
- Probabilidad máxima lluvia 60min ≤ f(IEAD, compresión_atm) (no más del X% si IEAD<Y).
- Evaporación máxima ≤ función de Rn positivo y viento (no generar ET irreales si Rn negativo).
- Si sensores críticos offline o SRS < T_low → activar HARD FALLBACK MODE (solo reglas A).

Todos los motores deben chequear la tabla de precedencia antes de aplicar ajustes.

---

## 13. Clasificación de decisiones A / B / C

Definición obligatoria para cada regla/modelo: tipo de decisión

- Tipo A — Físicas duras (non-negotiable): basadas en leyes físicas o umbrales absolutos (p. ej. punto de rocío > T => condensación). Siempre evaluadas primero.
- Tipo B — Físicas probabilísticas: dependen de IEAD/Inercia/Régimen (p. ej. probabilidad lluvia 30–60min). Sujetos a precedencia y limitadores.
- Tipo C — Heurísticas / ML: ajustes finos y recomendaciones (p. ej. sugerencias de riego optimizadas). Solo aplican si SRS y UNC lo permiten.

Regla: Ninguna decisión Tipo C puede invalidar una Tipo A; Tipo B solo opera dentro de los límites marcados por A y precedida por checks de coherencia.

---

## 14. Modos operativos globales y transiciones

El sistema debe declarar un `Modo Operativo Global` cada minuto (Estado Meta):

- `Modo Conservador` — SRS bajo o UNC alta; ML desactivado; reglas A activas.
- `Modo Normal` — operación estándar; ML con límites; ajustes moderados.
- `Modo Convectivo` — IEAD alto y Dominant Driver = radiación con interacción convectiva; motores convectivos aumentan agresividad.
- `Modo Radiativo` — Inercia nocturna dominante; prioridad a heladas/niebla/condensación.
- `Modo Degradado` — sensores críticos offline; fallback rules-only.

Transiciones:
- Definir condiciones de entrada/salida (ej.: IEAD↑ por encima de umbral durante X min → modo Convectivo).
- Hysteresis para evitar switching frecuente (persistencia mínima por modo).

---

## 15. Puntos sin consenso y propuesta para consensuar

- Normalización vs valor físico: consenso: almacenar y exponer ambos; decisiones críticas requieren referencia física y umbral absoluto.
- Forma no lineal de IEAD: consenso propuesto: usar combinación multiplicativa y sumatoria; validar con histórico y ajustar pesos.
- Hard fallback: definir umbrales SRS y sensores críticos; acuerdo operativo necesario sobre qué sensores son críticos.

Propuesta para cerrar consenso: crear un documento corto (1 página) por cada punto con ejemplos numéricos y pruebas históricas para validar elecciones (p.ej. IEAD variantes vs skill score 30–60min).

---

## 16. Ideas adicionales y refinamientos

- Índice de Compresión Atmosférica (derivada presión + otros) para mejorar predicción corta.
- Detector de Ruptura Energética (CUSUM) para prioridades inmediatas.
- Coherencia Espacial Virtual y Score de Madurez del Día.
- Regulador de Aprendizaje: A/B automáticos y rollback si SRS cae.
- Explicabilidad: cada ajuste persiste con evidencia (últimos N registros) y motivo.

---

_Documento ampliado con formalización de precedencia, decisiones y modos operativos para facilitar consensos y evitar ambigüedad antes de codificar._
