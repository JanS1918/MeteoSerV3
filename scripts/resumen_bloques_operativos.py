#!/usr/bin/env python3
"""Genera reportes de bloques para todos los archivos operativos."""
from __future__ import annotations

from pathlib import Path
import csv
from collections import defaultdict
import re

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "output" / "subfactores_operativos_origen.csv"
OUT_DIR = ROOT / "output"


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

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for file, items in sorted(file_to_subfactors.items()):
        slug = _slugify(file)
        out_md = OUT_DIR / f"bloque_{slug}.md"

        lines: list[str] = []
        lines.append(f"# Bloque: {file}")
        lines.append("")
        lines.append(f"Archivo: {file}")
        lines.append(f"Subfactores: {len(items)}")
        lines.append("")
        lines.append("## Subfactores")
        lines.append("")
        for name, line in sorted(items, key=lambda x: (x[0], x[1])):
            lines.append(f"- {name}: {file}:{line}")
        lines.append("")
        lines.append("## Solapamientos")
        lines.append("")
        lines.append("(ninguno)")

        out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Reportes generados: {len(file_to_subfactors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
