#!/usr/bin/env python3
"""
Compara subfactores no funcionales contra el listado completo para detectar duplicados
o nombres muy parecidos. Genera:
- output/duplicados_report.md
- output/duplicados.json
"""
from pathlib import Path
import csv
import json
import difflib
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
MAPPING = ROOT / 'output' / 'mapping_subfactores_origen.csv'
NO_FUNC = ROOT / 'output' / 'no_funcionales.csv'
OUT_MD = ROOT / 'output' / 'duplicados_report.md'
OUT_JSON = ROOT / 'output' / 'duplicados.json'

# helpers

def normalize(name):
    # lowercase, strip accents, keep alnum
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

# load no funcionales
no_func = []
with NO_FUNC.open(encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        no_func.append(r['name'])

# build normalized map
norm_map = {}
for n in all_names:
    norm = normalize(n)
    norm_map.setdefault(norm, []).append(n)

# compare
report = {}
for n in no_func:
    entry = {'name': n, 'exact_norm_matches': [], 'close_matches': []}
    norm = normalize(n)
    if norm in norm_map:
        entry['exact_norm_matches'] = norm_map[norm]
    # use difflib to find close matches among all_names
    close = difflib.get_close_matches(n, all_names, n=6, cutoff=0.78)
    # also try normalized fuzzy: compare norm against unique norms
    unique_norms = list(norm_map.keys())
    close_norms = difflib.get_close_matches(norm, unique_norms, n=6, cutoff=0.78)
    # expand close_norms to original names
    close_from_norms = []
    for cn in close_norms:
        close_from_norms.extend(norm_map.get(cn, []))
    # combine and dedupe
    combined = []
    for c in close + close_from_norms:
        if c not in combined:
            combined.append(c)
    # remove exact same name
    combined = [c for c in combined if c != n]
    entry['close_matches'] = combined
    report[n] = entry

# write outputs
OUT_MD.write_text('# Duplicados / coincidencias probables\n\n' + '\n'.join(
    f"## {r}\n- Norm matches: {report[r]['exact_norm_matches']}\n- Close matches: {report[r]['close_matches']}\n"
    for r in report
), encoding='utf-8')
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('Generado:', OUT_MD, OUT_JSON)
