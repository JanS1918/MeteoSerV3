#!/usr/bin/env python3
"""Resumen de origenes por grupo de subfactores operativos."""
from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import csv

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "output" / "subfactores_operativos_origen.csv"
OUT_MD = ROOT / "output" / "subfactores_operativos_origen_resumen.md"

KNOWN_PREFIXES = [
    "wbgt",
    "utci",
    "ai",
    "watchdog",
    "datos",
    "physics",
    "sensores",
    "alerta",
    "alert",
    "metrics",
    "Prediccion",
    "Sensores",
]


def bucket(name: str) -> str:
    if "." in name:
        return name.split(".", 1)[0]
    for p in KNOWN_PREFIXES:
        if name.startswith(p + "_") or name.startswith(p):
            return p
    if "_" in name:
        return name.split("_", 1)[0]
    return "misc"


def main() -> int:
    if not IN_CSV.exists():
        raise SystemExit(f"Missing {IN_CSV}")

    groups = defaultdict(lambda: defaultdict(set))
    totals = defaultdict(int)

    with IN_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["subfactor"]
            file = row["file"]
            group = bucket(name)
            groups[group][name].add(file)
            totals[group] += 1

    lines = []
    lines.append("# Resumen de origenes por grupo (operativos)")
    lines.append("")

    for group in sorted(groups.keys(), key=lambda g: (-len(groups[g]), g)):
        lines.append(f"## {group} ({len(groups[group])})")
        for name in sorted(groups[group].keys()):
            files = sorted(groups[group][name])
            files_txt = ", ".join(files)
            lines.append(f"- {name}: {files_txt}")
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Escrito: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
