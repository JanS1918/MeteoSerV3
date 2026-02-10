#!/usr/bin/env python3
"""
Extrae snippets alrededor de cada llamada a bus.publicar('subfactor'), normaliza
los snippets y agrupa por hash para detectar implementaciones idénticas.
Genera:
- output/implementaciones_identicas.csv (subfactor,file,hash,identical_group_id)
- output/implementaciones_identicas_summary.json
- output/implementaciones_identicas_examples.txt (ejemplos de snippets idénticos)
"""
from pathlib import Path
import csv
import re
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent
MAPPING = ROOT / 'output' / 'mapping_subfactores_origen.csv'
OUT_CSV = ROOT / 'output' / 'implementaciones_identicas.csv'
OUT_SUM = ROOT / 'output' / 'implementaciones_identicas_summary.json'
OUT_EX = ROOT / 'output' / 'implementaciones_identicas_examples.txt'

# lee mapping
subfactor_files = {}
with MAPPING.open(encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        name = row['name']
        files = [x for x in row['files'].split(';') if x.strip()]
        subfactor_files[name] = files

# regex para encontrar bus.publicar('name' or "name")
pub_re_tpl = r"bus\.publicar\(\s*(['\"])%s\1"

def extract_snippets_for_file(path, token):
    p = ROOT / path
    if not p.exists():
        return []
    try:
        text = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return []
    snippets = []
    # find all occurrences of the token in bus.publicar
    pat = re.compile(pub_re_tpl % re.escape(token))
    for m in pat.finditer(text):
        start_idx = m.start()
        # get line number
        before = text[:start_idx]
        line_no = before.count('\n')
        lines = text.splitlines()
        # attempt to find enclosing def by searching upwards for a line starting with 'def ' or 'class '
        func_start = None
        for i in range(line_no, -1, -1):
            if re.match(r"^\s*(def|class)\s+", lines[i]):
                func_start = i
                break
        # find function end by searching next def/class at same indent or end
        func_end = None
        if func_start is not None:
            indent_match = re.match(r"^(\s*)", lines[func_start])
            base_indent = len(indent_match.group(1)) if indent_match else 0
            for j in range(func_start+1, len(lines)):
                m2 = re.match(r"^(\s*)(def|class)\s+", lines[j])
                if m2 and len(m2.group(1)) <= base_indent:
                    func_end = j
                    break
        # fallback: use window of +/- 30 lines
        if func_start is None:
            start = max(0, line_no-15)
            end = min(len(lines), line_no+16)
        else:
            start = max(0, func_start)
            end = func_end if func_end is not None else min(len(lines), line_no+16)
        snippet = "\n".join(lines[start:end])
        snippets.append({'file': str(path), 'line': line_no+1, 'snippet': snippet})
    return snippets

# normalize snippet: remove comments, collapse whitespace
def normalize_snippet(s):
    # remove python comments
    lines = s.splitlines()
    no_comments = []
    for L in lines:
        # remove inline comments but keep # in strings naive approach: remove after # if not in quotes
        # simplistic: split at # if number of quotes before is even
        idx = None
        quote_count = 0
        for i,ch in enumerate(L):
            if ch in ('"', "'"):
                quote_count += 1
            if ch == '#' and quote_count % 2 == 0:
                idx = i
                break
        if idx is not None:
            L2 = L[:idx]
        else:
            L2 = L
        no_comments.append(L2)
    s2 = '\n'.join(no_comments)
    # collapse multiple spaces and normalize indent
    s3 = '\n'.join(line.rstrip() for line in s2.splitlines())
    s3 = re.sub(r"\s+", ' ', s3)
    s3 = s3.strip()
    return s3

hash_map = {}  # hash -> list of (subfactor,file,line)
entry_rows = []

for subfactor, files in subfactor_files.items():
    # skip if no files
    if not files:
        continue
    for f in files:
        snippets = extract_snippets_for_file(f, subfactor)
        if not snippets:
            continue
        for sn in snippets:
            norm = normalize_snippet(sn['snippet'])
            h = hashlib.sha256(norm.encode('utf-8')).hexdigest()
            hash_map.setdefault(h, []).append({'subfactor': subfactor, 'file': sn['file'], 'line': sn['line'], 'snippet': norm})
            entry_rows.append({'subfactor': subfactor, 'file': sn['file'], 'line': sn['line'], 'hash': h})

# identify identical groups where same hash appears in multiple file contexts
identical_groups = {h: items for h, items in hash_map.items() if len(items) > 1}

# write CSV of all entries
with OUT_CSV.open('w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['subfactor','file','line','hash','identical_group'])
    gid = 0
    hash_to_gid = {}
    for row in entry_rows:
        h = row['hash']
        if h in identical_groups:
            if h not in hash_to_gid:
                gid += 1
                hash_to_gid[h] = gid
            ig = hash_to_gid[h]
        else:
            ig = ''
        writer.writerow([row['subfactor'],row['file'],row['line'],h,ig])

# write summary
summary = {
    'total_snippets': len(entry_rows),
    'identical_groups_count': len(identical_groups),
    'identical_pairs_total': sum(len(v) for v in identical_groups.values())
}
OUT_SUM.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

# write examples
with OUT_EX.open('w', encoding='utf-8') as f:
    for gid, (h, items) in enumerate(identical_groups.items(), start=1):
        f.write(f'=== GROUP {gid} (hash={h}) ===\n')
        for it in items:
            f.write(f"- {it['subfactor']} @ {it['file']}:{it['line']}\n")
        f.write('\nSNIPPET:\n')
        f.write(items[0]['snippet'] + '\n\n')

print('Generado:', OUT_CSV, OUT_SUM, OUT_EX)
print('Grupos idénticos encontrados:', len(identical_groups))
