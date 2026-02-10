#!/usr/bin/env python3
"""
Clasifica subfactores en funcionales (tienen implementación en archivos no-backup)
vs no funcionales.
Genera:
- output/funcionales.csv  (name,files)
- output/no_funcionales.csv (name,reason)
- output/funcionalidad_resumen.json
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPPING = ROOT / 'output' / 'mapping_subfactores_origen.csv'
MISSING = ROOT / 'output' / 'subfactores_no_implementados.txt'
OUT_DIR = ROOT / 'output'
OUT_DIR.mkdir(exist_ok=True)
FUNC_CSV = OUT_DIR / 'funcionales.csv'
NO_FUNC_CSV = OUT_DIR / 'no_funcionales.csv'
SUMMARY = OUT_DIR / 'funcionalidad_resumen.json'

# helper: consider a path active if it does NOT contain 'backup' (case-insensitive)
def is_active_path(p):
    low = p.lower()
    return 'backup' not in low and 'backup_sello' not in low and 'sello' not in low

# read mapping
mapping = {}
with MAPPING.open(encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        name = r['name']
        files = [x for x in r['files'].split(';') if x.strip()]
        mapping[name] = files

missing = set()
if MISSING.exists():
    with MISSING.open(encoding='utf-8') as f:
        for l in f:
            missing.add(l.strip())

funcionales = {}
no_funcionales = {}

for name, files in mapping.items():
    if name in missing:
        no_funcionales[name] = 'no_implementado'
        continue
    if not files:
        no_funcionales[name] = 'no_implementado'
        continue
    active_files = [p for p in files if is_active_path(p)]
    if active_files:
        funcionales[name] = active_files
    else:
        # exists but only in backups
        no_funcionales[name] = 'solo_en_backups'

# write funcionales
with FUNC_CSV.open('w', encoding='utf-8') as f:
    f.write('name,files\n')
    for n, fs in sorted(funcionales.items()):
        f.write(f'"{n}","{";".join(fs)}"\n')

# write no funcionales
with NO_FUNC_CSV.open('w', encoding='utf-8') as f:
    f.write('name,reason\n')
    for n, reason in sorted(no_funcionales.items()):
        f.write(f'"{n}","{reason}"\n')

res = {
    'total_subfactores': len(mapping),
    'funcionales': len(funcionales),
    'no_funcionales': len(no_funcionales),
    'no_implementados_list': sorted([n for n, r in no_funcionales.items() if r=='no_implementado']),
    'solo_en_backups_count': sum(1 for r in no_funcionales.values() if r=='solo_en_backups')
}
with SUMMARY.open('w', encoding='utf-8') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)

print('Generado:')
print(' -', FUNC_CSV)
print(' -', NO_FUNC_CSV)
print(' -', SUMMARY)
print('Resumen:', res)
