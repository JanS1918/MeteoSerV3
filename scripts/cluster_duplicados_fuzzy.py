#!/usr/bin/env python3
"""
Clusteriza subfactores por similitud (fuzzy) usando difflib y componentes conectadas.
Genera:
- output/duplicados_fuzzy.csv
- output/duplicados_fuzzy.json
"""
from pathlib import Path
import csv
import json
import difflib
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
MAPPING = ROOT / 'output' / 'mapping_subfactores_origen.csv'
FUNC = ROOT / 'output' / 'funcionales.csv'
NOFUNC = ROOT / 'output' / 'no_funcionales.csv'
OUT_CSV = ROOT / 'output' / 'duplicados_fuzzy.csv'
OUT_JSON = ROOT / 'output' / 'duplicados_fuzzy.json'

# load names
names = []
with MAPPING.open(encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        names.append(r['name'])

# helper normalize
def normalize_simple(s):
    s = s.lower()
    s = ''.join(ch for ch in unicodedata.normalize('NFD', s) if unicodedata.category(ch) != 'Mn')
    return s

norm_names = [normalize_simple(n) for n in names]

# build similarity edges
cutoff = 0.82
n = len(names)
parent = list(range(n))

def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a

def union(a,b):
    ra = find(a); rb = find(b)
    if ra != rb:
        parent[rb] = ra

# Use difflib to get close matches for each name
for i, name in enumerate(names):
    # consider candidates from all names
    candidates = difflib.get_close_matches(name, names, n=50, cutoff=cutoff)
    for c in candidates:
        if c == name:
            continue
        j = names.index(c)
        union(i,j)

# build clusters
clusters = {}
for i in range(n):
    r = find(i)
    clusters.setdefault(r, []).append(names[i])

# load funcionales and nofunc maps
func_set = set()
with FUNC.open(encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        func_set.add(row['name'])
no_func_map = {}
with NOFUNC.open(encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        no_func_map[row['name']] = row['reason']

summary = []
for root_idx, items in clusters.items():
    if len(items) <= 1:
        continue
    funcionales_count = sum(1 for it in items if it in func_set)
    no_funcionales_count = sum(1 for it in items if it in no_func_map)
    solo_backups_count = sum(1 for it in items if no_func_map.get(it) == 'solo_en_backups')
    # recommendation similar heuristics
    if funcionales_count > 1:
        rec = 'fusionar_activas'
    elif funcionales_count == 1 and (no_funcionales_count > 0 or solo_backups_count>0):
        rec = 'mantener_activa_y_recuperar_otros'
    elif funcionales_count == 0 and (no_funcionales_count > 0 or solo_backups_count>0):
        rec = 'recuperar_o_revisar_backups'
    else:
        rec = 'revisar_manual'
    summary.append({
        'cluster_id': root_idx,
        'members': items,
        'size': len(items),
        'funcionales_count': funcionales_count,
        'no_funcionales_count': no_funcionales_count,
        'solo_backups_count': solo_backups_count,
        'recommendation': rec
    })

# write CSV
with OUT_CSV.open('w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['cluster_id','size','funcionales_count','no_funcionales_count','solo_backups_count','recommendation','members'])
    for row in summary:
        writer.writerow([row['cluster_id'],row['size'],row['funcionales_count'],row['no_funcionales_count'],row['solo_backups_count'],row['recommendation'],';'.join(row['members'])])

OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print('Generado:', OUT_CSV, OUT_JSON)
print('Clusters encontrados:', len(summary))
