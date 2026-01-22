import json
from pathlib import Path

p = Path(__file__).parent.parent / 'data' / 'last_ecowitt_payload.json'
if not p.exists():
    print('No existe', p)
    raise SystemExit(1)
raw = json.loads(p.read_text(encoding='utf-8'))
data = raw.get('data') or raw
print('Llaves recibidas en payload:', sorted(list(data.keys())))

# Helpers similar a main_asgi
def _to_float(val):
    try:
        return float(val)
    except Exception:
        return None

lluvia_rate_candidates = [
    ("rainratein", data.get("rainratein")),
    ("rain_ratein", data.get("rain_ratein")),
    ("rainrate", data.get("rainrate")),
    ("rain_rate", data.get("rain_rate")),
    ("rainrate_mm", data.get("rainrate_mm")),
]
lluvia_acum_candidates = [
    ("rainin", data.get("rainin")),
    ("dailyrainin", data.get("dailyrainin")),
    ("eventrainin", data.get("eventrainin")),
    ("hourlyrainin", data.get("hourlyrainin")),
    ("dailyrainmm", data.get("dailyrainmm")),
    ("eventrainmm", data.get("eventrainmm")),
    ("hourlyrainmm", data.get("hourlyrainmm")),
    ("rainmm", data.get("rainmm")),
]

best_rate = None
best_rate_unit = None
for key, val in lluvia_rate_candidates:
    if val is None:
        continue
    rate_val = _to_float(val)
    if rate_val is None:
        continue
    unit = "in" if key.endswith("in") else "mm"
    if best_rate is None or rate_val > best_rate:
        best_rate = rate_val
        best_rate_unit = unit

best_acum = None
best_acum_unit = None
for key, val in lluvia_acum_candidates:
    if val is None:
        continue
    acum_val = _to_float(val)
    if acum_val is None:
        continue
    unit = "in" if key.endswith("in") else "mm"
    if best_acum is None or acum_val > best_acum:
        best_acum = acum_val
        best_acum_unit = unit

lluvia = None
lluvia_rate = None
if best_rate is not None:
    lluvia_rate_mm = best_rate * 25.4 if best_rate_unit == "in" else best_rate
    lluvia = round(lluvia_rate_mm, 2)
    lluvia_rate = round(lluvia_rate_mm, 2)
    modo = 'from_rate'
elif best_acum is not None:
    lluvia_acum_mm = best_acum * 25.4 if best_acum_unit == "in" else best_acum
    lluvia = round(lluvia_acum_mm, 2)
    modo = 'from_acum'
else:
    modo = 'no_data'

print('\nDetección lluvia: modo:', modo)
print('best_rate:', best_rate, best_rate_unit)
print('best_acum:', best_acum, best_acum_unit)
print('lluvia (mm):', lluvia)
print('lluvia_rate (mm/h o mm):', lluvia_rate)

# Calcular indice_lluvia = lluvia + lluvia_rate (según formulas.json)
ll = (lluvia or 0.0) + (lluvia_rate or 0.0)
print('\nIndice_lluvia (lluvia + lluvia_rate) =', ll)

# Mostrar campos de lluvia originales
print('\nCampos de lluvia originales en payload:')
for k in ['rainratein','rain_ratein','rainrate','rain_rate','rainrate_mm','rainin','dailyrainin','eventrainin','hourlyrainin','dailyrainmm','eventrainmm','hourlyrainmm','rainmm']:
    if k in data:
        print(' ', k, ':', data.get(k))

# Resumen y recomendación
if ll == 0.0:
    print('\nDiagnóstico: no hay registro de lluvia reciente en el payload (todos los campos relevantes son cero o ausentes).\n-> Por eso "probabilidad de lluvia" e índices relacionados aparecen a 0 en la UI.')
    print('\nSugerencias:')
    print('- Verificar el pluviómetro físico (no obstruido).')
    print('- Verificar que la estación esté enviando correctamente campos como "rainin" o "rainratein".')
    print('- Si esperas lluvia pero no se registra, intentar un muestreo/reinicio del sensor o comprobar logs de recepción en `logs/servicio_out.log`.')
else:
    print('\nNo es cero; el índice de lluvia debería reflejar esto en la UI.')
