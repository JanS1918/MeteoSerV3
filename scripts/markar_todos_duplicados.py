#!/usr/bin/env python3
"""
Produce output/subfactores_con_duplicado.csv con columnas:
name, is_duplicated (True/False), cluster_id (or ''), cluster_members (semicolon list or '')
"""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent
DUP = ROOT / 'output' / 'duplicados_fuzzy.csv'
MAPPING = ROOT / 'output' / 'mapping_subfactores_origen.csv'
OUT = ROOT / 'output' / 'subfactores_con_duplicado.csv'

# load clusters
clusters = {}
with DUP.open(encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        cid = r['cluster_id']
        members = [m for m in r['members'].split(';') if m.strip()]
        clusters[cid] = members

# build member->cluster map
member_cluster = {}
for cid, members in clusters.items():
    for m in members:
        member_cluster[m] = (cid, members)

# read all names
with MAPPING.open(encoding='utf-8') as f_in, OUT.open('w', encoding='utf-8', newline='') as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    writer.writerow(['name','is_duplicated','cluster_id','cluster_members'])
    for r in reader:
        name = r['name']
        if name in member_cluster:
            cid, members = member_cluster[name]
            writer.writerow([name,'True',cid,';'.join(members)])
        else:
            writer.writerow([name,'False','',''])

print('Generado', OUT)
