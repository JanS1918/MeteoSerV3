#!/usr/bin/env python3
"""Genera un resumen agrupado de subfactores unitarios."""
from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import json

ROOT = Path(__file__).resolve().parent.parent
IN_TXT = ROOT / "output" / "subfactores_unitarios.txt"
OUT_MD = ROOT / "output" / "subfactores_unitarios_resumen.md"
OUT_JSON = ROOT / "output" / "subfactores_unitarios_resumen.json"
IN_OP_TXT = ROOT / "output" / "subfactores_unitarios_operativos.txt"
OUT_OP_MD = ROOT / "output" / "subfactores_unitarios_operativos_resumen.md"
OUT_OP_JSON = ROOT / "output" / "subfactores_unitarios_operativos_resumen.json"

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


def _build_summary(items: list[str], title: str) -> tuple[list[str], dict]:
    groups = defaultdict(list)
    for name in items:
        groups[bucket(name)].append(name)

    for g in groups.values():
        g.sort()

    summary = {k: g for k, g in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))}

    lines = []
    lines.append(title)
    lines.append("")
    lines.append(f"Total: {len(items)}")
    lines.append("")
    for group, names in summary.items():
        lines.append(f"## {group} ({len(names)})")
        for n in names:
            lines.append(f"- {n}")
        lines.append("")

    return lines, summary


def main() -> int:
    if not IN_TXT.exists():
        raise SystemExit(f"Missing {IN_TXT}")

    items = [line.strip() for line in IN_TXT.read_text(encoding="utf-8").splitlines() if line.strip()]
    lines, summary = _build_summary(items, "# Resumen de subfactores unitarios")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito: {OUT_MD}")
    print(f"Escrito: {OUT_JSON}")

    if IN_OP_TXT.exists():
        items_op = [line.strip() for line in IN_OP_TXT.read_text(encoding="utf-8").splitlines() if line.strip()]
        lines_op, summary_op = _build_summary(items_op, "# Resumen de subfactores unitarios operativos")
        OUT_OP_MD.write_text("\n".join(lines_op), encoding="utf-8")
        OUT_OP_JSON.write_text(json.dumps(summary_op, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Escrito: {OUT_OP_MD}")
        print(f"Escrito: {OUT_OP_JSON}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
