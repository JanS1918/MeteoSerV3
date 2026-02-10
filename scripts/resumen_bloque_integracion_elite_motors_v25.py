#!/usr/bin/env python3
"""Resumen por bloque de subfactores en integracion_elite_motors_v25."""
from __future__ import annotations

from pathlib import Path
import csv
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "output" / "subfactores_operativos_origen.csv"
OUT_MD = ROOT / "output" / "bloque_integracion_elite_motors_v25.md"
TARGET_FILE = "core/indices/integracion_elite_motors_v25.py"


def main() -> int:
    if not IN_CSV.exists():
        raise SystemExit(f"Missing {IN_CSV}")

    subfactor_origens: dict[str, list[tuple[str, int]]] = defaultdict(list)
    with IN_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            file = row["file"].replace("\\", "/")
            line = int(row["line"]) if row["line"].isdigit() else 0
            subfactor_origens[row["subfactor"]].append((file, line))

    bloque = {
        name: origenes
        for name, origenes in subfactor_origens.items()
        if any(file == TARGET_FILE for file, _ in origenes)
    }

    lines: list[str] = []
    lines.append("# Bloque: integracion_elite_motors_v25")
    lines.append("")
    lines.append(f"Archivo: {TARGET_FILE}")
    lines.append(f"Subfactores: {len(bloque)}")
    lines.append("")

    solapados = []
    for name, origenes in sorted(bloque.items()):
        otros = [f"{file}:{line}" for file, line in origenes if file != TARGET_FILE]
        if otros:
            solapados.append((name, otros))

    lines.append("## Subfactores")
    lines.append("")
    for name, origenes in sorted(bloque.items()):
        origenes_fmt = ", ".join(f"{file}:{line}" for file, line in origenes)
        flag = " (solapado)" if any(file != TARGET_FILE for file, _ in origenes) else ""
        lines.append(f"- {name}{flag}: {origenes_fmt}")

    lines.append("")
    lines.append("## Solapamientos")
    lines.append("")
    if solapados:
        for name, otros in solapados:
            lines.append(f"- {name}: {', '.join(otros)}")
    else:
        lines.append("(ninguno)")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Escrito: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
