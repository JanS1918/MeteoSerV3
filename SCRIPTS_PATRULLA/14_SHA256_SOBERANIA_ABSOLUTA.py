# -*- coding: utf-8 -*-
"""
Genera SHA256 de soberanía absoluta sobre el estado actual del proyecto.
"""
from pathlib import Path
import hashlib

ROOT = Path(r"c:/Users/kioko/Desktop/MeteoSerV3")
OUT_FILE = ROOT / "SHA256_SOBERANIA_ABSOLUTA.txt"

# Archivos críticos a sellar
patterns = ["**/*.py", "**/*.json", "**/*.txt"]

files = []
for pat in patterns:
    files.extend([p for p in ROOT.glob(pat) if p.is_file()])

# Orden determinista
files = sorted(files, key=lambda p: str(p).lower())

h = hashlib.sha256()
for p in files:
    rel = p.relative_to(ROOT).as_posix()
    h.update(rel.encode("utf-8"))
    h.update(b"\n")
    h.update(p.read_bytes())
    h.update(b"\n")

sha = h.hexdigest()
OUT_FILE.write_text(sha, encoding="utf-8")
print(f"SHA256 Soberania Absoluta: {sha}")
print(f"Archivo: {OUT_FILE}")
