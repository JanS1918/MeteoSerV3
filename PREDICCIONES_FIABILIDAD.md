# Fiabilidad de predicciones (local)

Este módulo funciona solo con sensores propios y feedback local.

## Feedback
- Endpoint: `POST /feedback_prediccion`
- Guarda en `data/feedback_registros.jsonl` con snapshot y valores reales.

## Backtest rápido
Genera métricas (MAE y Brier si aplica) desde el feedback local:

```bash
C:/Users/kioko/Desktop/MeteoSerV3/.venv/Scripts/python.exe tools/backtest_predicciones.py --save
```

Salida guardada en:
- `data/metrics_predicciones.json`
- `data/metrics_history.jsonl`

## Monitor de degradación
Detecta subida anormal de MAE con histórico:

```bash
C:/Users/kioko/Desktop/MeteoSerV3/.venv/Scripts/python.exe tools/monitor_predicciones.py --window 10 --threshold 0.2
```

Salida:
- `data/alerts_predicciones.json`

## Configuración
Variables de entorno útiles:
- `METEOSER_OUTLIER_Z` (default 4)
- `METEOSER_OUTLIER_MIN_SAMPLES` (default 10)
- `METEOSER_OUTLIER_ACTION` (clamp|reject)
- `METEOSER_MIN_CONFIDENCE` (default 0.4)
- `METEOSER_VIRTUAL_CONF_BONUS` (default 0.05)
- `METEOSER_VIRTUAL_CONF_MIN` (default 0.9)
- `METEOSER_FEEDBACK_UNCERTAINTY` (default 12)

Notas:
- Para aplicar el bonus, envía `origin="virtual"` o `certificado=true` en `/sensor_virtual`.

## Retraining local
Ejecuta recalibración cuando el monitor detecte degradación:

```bash
C:/Users/kioko/Desktop/MeteoSerV3/.venv/Scripts/python.exe tools/auto_retrain.py
```

Forzar recalibración:

```bash
C:/Users/kioko/Desktop/MeteoSerV3/.venv/Scripts/python.exe tools/auto_retrain.py --force
```
