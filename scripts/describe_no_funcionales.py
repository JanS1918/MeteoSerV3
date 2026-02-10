#!/usr/bin/env python3
"""
Genera `output/no_funcionales_report.md` describiendo los 72 subfactores no funcionales.
Incluye: name, reason, archivos donde aparece y snippets de contexto.
Para los 6 sin implementación añade una descripción sugerida.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NO_FUNC_CSV = ROOT / 'output' / 'no_funcionales.csv'
MAPPING_CSV = ROOT / 'output' / 'mapping_subfactores_origen.csv'
OUT = ROOT / 'output' / 'no_funcionales_report.md'

# load mapping into dict
mapping = {}
with MAPPING_CSV.open(encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        name = r['name']
        files = [x for x in r['files'].split(';') if x.strip()]
        mapping[name] = files

# read no_funcionales
no_func = []
with NO_FUNC_CSV.open(encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        no_func.append((r['name'], r['reason']))

# helper to get snippet
def get_snippets(file_path, token, max_snippets=2):
    p = ROOT / file_path
    if not p.exists():
        return []
    text = p.read_text(encoding='utf-8', errors='ignore')
    lines = text.splitlines()
    token_low = token.lower()
    snippets = []
    for i, line in enumerate(lines):
        if token_low in line.lower():
            start = max(0, i-2)
            end = min(len(lines), i+3)
            snippet = '\n'.join(lines[start:end])
            snippets.append({'file': str(file_path), 'line': i+1, 'snippet': snippet})
            if len(snippets) >= max_snippets:
                break
    return snippets

# suggested descriptions for the 6
suggestions = {
    'año': 'Año actual (valor numérico del año).',
    'dias_helada_acumulados_año': 'Contador de días con helada acumulados durante el año.',
    'emis ividad_cuerpo_humano': 'Probable "emisividad_cuerpo_humano" -> emisividad térmica del cuerpo humano (para cálculos radiativos).',
    'emis ividad_cuerpo_negro': 'Probable "emisividad_cuerpo_negro" -> emisividad del cuerpo negro (constante para calibración radiativa).',
    'es_año_bisiesto': 'Booleano que indica si el año actual es bisiesto.',
    'utci_categoria_estrés': 'Categoría de estrés térmico según el índice UTCI (por ejemplo: neutro, ligero, moderado, fuerte).'
}

lines_out = []
lines_out.append('# Informe: subfactores no funcionales\n')
for name, reason in no_func:
    lines_out.append(f'## {name}\n')
    lines_out.append(f'- Razón: {reason}\n')
    files = mapping.get(name, [])
    if files:
        active = [f for f in files if 'backup' not in f.lower() and 'sello' not in f.lower()]
        if active:
            lines_out.append(f'- Archivos (activos):')
            for f in active[:10]:
                lines_out.append(f'  - {f}')
        else:
            lines_out.append(f'- Archivos (solo en backups):')
            for f in files[:10]:
                lines_out.append(f'  - {f}')
    else:
        lines_out.append('- Archivos: ninguno encontrado')

    # add snippets from up to 3 files
    snippet_added = 0
    for f in files[:6]:
        s = get_snippets(f, name, max_snippets=1)
        if s:
            lines_out.append(f'- Snippet desde `{f}` (línea {s[0]["line"]}):\n')
            lines_out.append('```\n' + s[0]['snippet'] + '\n```\n')
            snippet_added += 1
        if snippet_added >= 2:
            break

    # suggestion for the 6 missing
    if name in suggestions:
        lines_out.append(f'- Descripción sugerida: {suggestions[name]}\n')
    lines_out.append('\n')

OUT.write_text('\n'.join(lines_out), encoding='utf-8')
print('Generado', OUT)
