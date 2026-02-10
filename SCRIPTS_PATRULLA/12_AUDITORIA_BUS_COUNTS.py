# -*- coding: utf-8 -*-
import re
from pathlib import Path

root = Path(r"c:/Users/kioko/Desktop/MeteoSerV3")
keys_read = {}
keys_pub = {}

for path in root.rglob('*.py'):
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    for m in re.finditer(r"bus\.leer\(\s*['\"]([^'\"]+)['\"]", text):
        k = m.group(1)
        keys_read[k] = keys_read.get(k, 0) + 1
    for m in re.finditer(r"bus\.publicar\(\s*['\"]([^'\"]+)['\"]", text):
        k = m.group(1)
        keys_pub[k] = keys_pub.get(k, 0) + 1

def top(d, n=20):
    return sorted(d.items(), key=lambda x: (-x[1], x[0]))[:n]

print("TOP_READ")
for k, v in top(keys_read, 20):
    print(v, k)
print("TOP_PUB")
for k, v in top(keys_pub, 20):
    print(v, k)
