# -*- coding: utf-8 -*-
"""
Generador de Libro Blanco de la Estación.
Extrae todas las claves publicadas al Bus desde bus_expander.py
y genera un listado de referencia.
"""
from pathlib import Path
import re
from datetime import datetime

ROOT = Path(r"c:/Users/kioko/Desktop/MeteoSerV3")
BUS_EXPANDER = ROOT / "core" / "system" / "bus_expander.py"
OUT_FILE = ROOT / "LIBRO_BLANCO_ESTACION.txt"

pattern = re.compile(r"publicar\(\s*['\"]([^'\"]+)['\"]")

keys = []
if BUS_EXPANDER.exists():
    text = BUS_EXPANDER.read_text(encoding="utf-8", errors="ignore")
    keys = pattern.findall(text)

# Deduplicar preservando orden
seen = set()
keys_unique = []
for k in keys:
    if k not in seen:
        seen.add(k)
        keys_unique.append(k)

# Encabezado
header = [
    "LIBRO BLANCO DE LA ESTACION - ARGENTONA",
    "========================================",
    f"Fecha: {datetime.now().isoformat()}",
    f"Total de parametros: {len(keys_unique)}",
    "",
    "Listado de claves publicadas al Bus:",
    ""
]

content = "\n".join(header + [f"- {k}" for k in keys_unique])
OUT_FILE.write_text(content, encoding="utf-8")

print(f"Generado: {OUT_FILE}")
print(f"Total parametros: {len(keys_unique)}")
