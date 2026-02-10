#!/usr/bin/env python3
"""
Genera:
- output/predicciones_completas.csv  (id,name,category,origin)
- output/sensores_canónicos.json    (canonical -> aliases)

Lee `bus_subfactores_reales.txt` y `core/sensors/sensor_aliases.py`.
"""
import re
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUS_FILE = ROOT / 'bus_subfactores_reales.txt'
SENSOR_ALIASES_PY = ROOT / 'core' / 'sensors' / 'sensor_aliases.py'
OUT_DIR = ROOT / 'output'
OUT_DIR.mkdir(exist_ok=True)
CSV_OUT = OUT_DIR / 'predicciones_completas.csv'
JSON_OUT = OUT_DIR / 'sensores_canónicos.json'

# Parse bus_subfactores_reales.txt
subfactores = []
if BUS_FILE.exists():
    text = BUS_FILE.read_text(encoding='utf-8')
    # Buscar líneas que comienzan con número punto espacio y nombre
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)\.\s+(.+)$", line)
        if m:
            idx = int(m.group(1))
            name = m.group(2).strip()
            # normalizar: quitar comas finales
            name = name.rstrip(',')
            subfactores.append((idx, name))
else:
    print(f"ERROR: no se encontró {BUS_FILE}")

# Escribir CSV
with CSV_OUT.open('w', encoding='utf-8', newline='') as f:
    f.write('id,name,category,origin\n')
    for idx, name in subfactores:
        # category desconocida -> dejar vacía
        origin = 'bus_subfactores_reales.txt'
        # Escape comillas en name
        safe_name = name.replace('"', '""')
        f.write(f'{idx},"{safe_name}",,"{origin}"\n')

# Cargar SENSOR_ALIASES
sensor_map = {}
if SENSOR_ALIASES_PY.exists():
    # Import by path
    import importlib.util
    spec = importlib.util.spec_from_file_location('sensor_aliases_local', str(SENSOR_ALIASES_PY))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        aliases = getattr(mod, 'SENSOR_ALIASES', {})
        # normalize keys to str
        for k, v in aliases.items():
            sensor_map[str(k)] = list(v)
    except Exception as e:
        print('ERROR cargando SENSOR_ALIASES:', e)
else:
    print(f"ERROR: no se encontró {SENSOR_ALIASES_PY}")

# Escribir JSON
with JSON_OUT.open('w', encoding='utf-8') as f:
    json.dump(sensor_map, f, indent=2, ensure_ascii=False)

print('Generados:')
print(' -', CSV_OUT)
print(' -', JSON_OUT)
