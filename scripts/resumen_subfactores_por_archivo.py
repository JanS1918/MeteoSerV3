#!/usr/bin/env python3
"""Resumen de subfactores operativos por archivo origen."""
from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import csv

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "output" / "subfactores_operativos_origen.csv"
OUT_MD = ROOT / "output" / "subfactores_operativos_por_archivo.md"


def main() -> int:
    if not IN_CSV.exists():
        raise SystemExit(f"Missing {IN_CSV}")

    files = defaultdict(set)
    with IN_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            files[row["file"].replace("\\", "/")].add(row["subfactor"])

    lines = []
    lines.append("# Subfactores operativos por archivo")
    lines.append("")

    for file, names in sorted(files.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lines.append(f"## {file} ({len(names)})")
        for name in sorted(names):
            lines.append(f"- {name}")
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Escrito: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
