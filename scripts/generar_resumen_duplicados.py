#!/usr/bin/env python3
"""
Agrupa subfactores por nombre normalizado y genera:
- output/duplicados_summary.csv
- output/duplicados_summary.json

Columnas CSV: norm, originals, total, funcionales_count, no_funcionales_count, solo_backups_count, recommendation
"""
from pathlib import Path
import csv
import json
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
MAPPING = ROOT / 'output' / 'mapping_subfactores_origen.csv'
FUNC = ROOT / 'output' / 'funcionales.csv'
NOFUNC = ROOT / 'output' / 'no_funcionales.csv'
OUT_CSV = ROOT / 'output' / 'duplicados_summary.csv'
OUT_JSON = ROOT / 'output' / 'duplicados_summary.json'

# normalize
def normalize(name):
    s = name.lower()
    s = ''.join(ch for ch in unicodedata.normalize('NFD', s) if unicodedata.category(ch) != 'Mn')
    s = ''.join(c for c in s if c.isalnum())
    return s

# load all names
all_names = []
with MAPPING.open(encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        all_names.append(r['name'])

# load funcionales set
func_set = set()
with FUNC.open(encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        func_set.add(row['name'])

# load no_func map with reason
no_func_map = {}
with NOFUNC.open(encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        no_func_map[row['name']] = row['reason']

# group by norm
groups = {}
for n in all_names:
    norm = normalize(n)
    groups.setdefault(norm, []).append(n)

summary = []
for norm, names in groups.items():
    if len(names) <= 1:
        continue
    total = len(names)
    funcionales_count = sum(1 for n in names if n in func_set)
    no_funcionales_count = sum(1 for n in names if n in no_func_map)
    solo_backups_count = sum(1 for n in names if no_func_map.get(n) == 'solo_en_backups')
    # detect probable typos: presence of spaces within token or ' ' in original or weird sequences
    typo_flag = any(' ' in n or '  ' in n or '�' in n or 'ividad' in n for n in names)
    # recommendation heuristics
    if funcionales_count > 1:
        rec = 'fusionar_activas'  # multiple active entries -> merge
    elif funcionales_count == 1 and no_funcionales_count > 0:
        rec = 'mantener_activa_y_fusionar/recuperar_otras'
    elif funcionales_count == 0 and solo_backups_count > 0:
        rec = 'recuperar_desde_backups'
    elif typo_flag:
        rec = 'corregir_nombre_typos'
    else:
        rec = 'revisar_manual'
    summary.append({
        'norm': norm,
        'originals': names,
        'total': total,
        'funcionales_count': funcionales_count,
        'no_funcionales_count': no_funcionales_count,
        'solo_backups_count': solo_backups_count,
        'recommendation': rec
    })

# write CSV
with OUT_CSV.open('w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['norm','originals','total','funcionales_count','no_funcionales_count','solo_backups_count','recommendation'])
    for row in summary:
        writer.writerow([row['norm'],';'.join(row['originals']),row['total'],row['funcionales_count'],row['no_funcionales_count'],row['solo_backups_count'],row['recommendation']])

# write JSON
OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print('Generado:', OUT_CSV, OUT_JSON)
print('Grupos con duplicados:', len(summary))
