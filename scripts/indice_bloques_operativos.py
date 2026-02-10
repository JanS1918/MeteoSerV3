#!/usr/bin/env python3
"""Genera un indice maestro de reportes de bloques operativos."""
from __future__ import annotations

from pathlib import Path
import csv
from collections import defaultdict
import re

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output"
OUT_MD = OUT_DIR / "indice_bloques_operativos.md"
IN_CSV = OUT_DIR / "subfactores_operativos_origen.csv"


def _slugify(path: str) -> str:
    slug = path.replace("\\", "/")
    slug = slug.replace("/", "__")
    slug = re.sub(r"[^A-Za-z0-9_\.\-]", "_", slug)
    return slug


def main() -> int:
    if not IN_CSV.exists():
        raise SystemExit(f"Missing {IN_CSV}")

    file_to_subfactors: dict[str, list[tuple[str, int]]] = defaultdict(list)
    with IN_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            file = row["file"].replace("\\", "/")
            line = int(row["line"]) if row["line"].isdigit() else 0
            file_to_subfactors[file].append((row["subfactor"], line))

    bloques = []
    for file in sorted(file_to_subfactors.keys()):
        slug = _slugify(file)
        bloques.append(OUT_DIR / f"bloque_{slug}.md")
    lines: list[str] = []
    lines.append("# Indice de bloques operativos")
    lines.append("")
    if not bloques:
        lines.append("(ninguno)")
    else:
        for bloque in bloques:
            rel = bloque.relative_to(ROOT).as_posix()
            lines.append(f"- [{rel}]({rel})")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Escrito: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
