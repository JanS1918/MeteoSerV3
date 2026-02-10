#!/usr/bin/env python3
"""Lista subfactores operativos cuyo origen no esta en core/"""
from __future__ import annotations

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent
IN_CSV = ROOT / "output" / "subfactores_operativos_origen.csv"
OUT_MD = ROOT / "output" / "subfactores_operativos_fuente_no_core.md"

ALLOWED_NON_CORE = {
    "WATCHDOG_INTEGRIDAD_V43_1.py": "guardian watchdog (integrity monitoring)",
    "integrador_datos_recuperados.py": "data recovery ingestion tool",
}


def main() -> int:
    if not IN_CSV.exists():
        raise SystemExit(f"Missing {IN_CSV}")

    rows = []
    with IN_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            file = row["file"].replace("\\", "/")
            if not file.startswith("core/"):
                rows.append((row["subfactor"], file, row["line"]))

    rows.sort()

    allowed = []
    attention = []
    for name, file, line in rows:
        reason = ALLOWED_NON_CORE.get(file)
        if reason:
            allowed.append((name, file, line, reason))
        else:
            attention.append((name, file, line))

    lines = []
    lines.append("# Subfactores operativos fuera de core/")
    lines.append("")
    lines.append("")
    lines.append("## Clasificacion")
    lines.append("")
    lines.append("Archivos permitidos (operativos auxiliares):")
    if ALLOWED_NON_CORE:
        for file, reason in sorted(ALLOWED_NON_CORE.items()):
            lines.append(f"- {file}: {reason}")
    else:
        lines.append("(ninguno)")

    lines.append("")
    lines.append("## Detalle")
    lines.append("")

    if not rows:
        lines.append("(ninguno)")
    else:
        if allowed:
            lines.append("Permitidos:")
            for name, file, line, reason in allowed:
                lines.append(f"- {name}: {file}:{line} ({reason})")
        if attention:
            if allowed:
                lines.append("")
            lines.append("Revisar:")
            for name, file, line in attention:
                lines.append(f"- {name}: {file}:{line}")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Escrito: {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
