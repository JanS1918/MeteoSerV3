#!/usr/bin/env python3
"""
Mapea subfactores -> archivos que llaman `bus.publicar('subfactor')`.
También busca sensores canónicos usados en `system.actualizar_sensor('sensor')`.
Genera:
- output/mapping_subfactores_origen.csv  (name,found,files)
- output/subfactores_no_implementados.txt
- output/sensores_usados.json
"""
import csv
import re
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
CSV_IN = ROOT / 'output' / 'predicciones_completas.csv'
OUT_DIR = ROOT / 'output'
OUT_DIR.mkdir(exist_ok=True)
MAPPING_CSV = OUT_DIR / 'mapping_subfactores_origen.csv'
MISSING_TXT = OUT_DIR / 'subfactores_no_implementados.txt'
SENSORES_JSON = OUT_DIR / 'sensores_usados.json'

# Leer subfactores
subfactores = []
with CSV_IN.open(encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        subfactores.append(r['name'])

# Scan .py files
py_files = list(ROOT.rglob('*.py'))

# regex for bus.publicar('name' or "name")
bus_pub_re = re.compile(r"bus\.publicar\(\s*['\"]([a-zA-Z0-9_\-]+)['\"]")
# regex for system.actualizar_sensor('sensor')
sys_upd_re = re.compile(r"system\.actualizar_sensor\(\s*['\"]([a-zA-Z0-9_\-]+)['\"]")

# map
mapping = {name: [] for name in subfactores}
found_set = set()

sensores_used = {}

for p in py_files:
    try:
        text = p.read_text(encoding='utf-8')
    except Exception:
        continue
    for m in bus_pub_re.finditer(text):
        name = m.group(1)
        if name in mapping:
            mapping[name].append(str(p.relative_to(ROOT)))
            found_set.add(name)
    for m in sys_upd_re.finditer(text):
        s = m.group(1)
        sensores_used.setdefault(s, []).append(str(p.relative_to(ROOT)))

# escribir mapping csv
with MAPPING_CSV.open('w', encoding='utf-8', newline='') as f:
    f.write('name,found,files\n')
    for name in subfactores:
        files = ';'.join(mapping.get(name, []))
        f.write(f'"{name}",{int(bool(files))},"{files}"\n')

# missing list
missing = [n for n in subfactores if n not in found_set]
with MISSING_TXT.open('w', encoding='utf-8') as f:
    for n in missing:
        f.write(n + '\n')

# sensores used
with SENSORES_JSON.open('w', encoding='utf-8') as f:
    json.dump(sensores_used, f, indent=2, ensure_ascii=False)

print('Hecho:')
print(' -', MAPPING_CSV)
print(' -', MISSING_TXT, f'({len(missing)} no implementados)')
print(' -', SENSORES_JSON)
