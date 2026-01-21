# Calibración avanzada de índices de cetrería (Opción C)

Este documento explica cómo ajustar automáticamente los pesos de los índices de cetrería con feedback real y cómo aplicar los resultados en MeteoSer.

## 1) Recolección de feedback

El backend registra feedback en data/feedback_registros.jsonl cuando se llama al endpoint /feedback_prediccion.

Estructura esperada por línea (JSONL):
- nombre: índice (ej. "visibilidad_terreno", "viento_cetreria")
- valor: valor estimado (0-100)
- valor_real: valor real observado (0-100)
- snapshot: { sensores, indices }

## 2) Calibrar pesos

Ejecuta la calibración de pesos (modo recomendado):

```bash
python tools/calibrar_cetreria.py --modo pesos --min-muestras 8 --guardar
```

Esto genera data/cetreria_calibracion.json con los pesos ajustados y un sesgo (bias) por índice.

Si quieres solo reporte (sin guardar):

```bash
python tools/calibrar_cetreria.py --modo pesos --min-muestras 8
```

## 3) Calibración lineal (opcional)

Si deseas un ajuste lineal simple sobre el valor final:

```bash
python tools/calibrar_cetreria.py --modo lineal
```

## 4) Aplicación en el backend

El motor de índices lee automáticamente los pesos de data/cetreria_calibracion.json.

### Autocalibración (opcional)

Si quieres que se calibren automáticamente cuando llega feedback, puedes habilitar estas variables:

- METEOSER_AUTOCALIB=1
- METEOSER_AUTOCALIB_MIN_SAMPLES=8
- METEOSER_AUTOCALIB_MIN_NEW_ROWS=10
- METEOSER_AUTOCALIB_COOLDOWN_S=3600
- METEOSER_AUTOCALIB_POLL_S=120

## 5) Notas

- Cuantas más muestras reales tengas por índice, mejor será la calibración.
- Si faltan sensores en el snapshot, esas muestras se omiten.
