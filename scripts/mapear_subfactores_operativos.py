#!/usr/bin/env python3
"""Mapa subfactores operativos a archivos/lineas donde se publican."""
from __future__ import annotations

from pathlib import Path
import csv
import os
import re

ROOT = Path(__file__).resolve().parent.parent
IN_TXT = ROOT / "output" / "subfactores_unitarios_operativos.txt"
OUT_CSV = ROOT / "output" / "subfactores_operativos_origen.csv"

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "archive",
    "backups",
    "mod_backups",
    "BACKUP_SELLO_SHA256_20260206_022119",
    "data",
    "tests",
}

NON_OP_PREFIXES = (
    "test_",
    "CIERRE_",
    "ejemplo_",
)

NON_OP_MARKERS = (
    "_BACKUP_",
    "_CERTIFICADO",
)


def _is_ignored_path(path: Path) -> bool:
    parts = {p for p in path.parts}
    if parts.intersection(IGNORE_DIRS):
        return True
    for p in path.parts:
        lower = p.lower()
        if lower.startswith("backup") or lower.startswith("backups"):
            return True
    return False


def iter_py_files():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not _is_ignored_path(Path(d))]
        for f in files:
            if not f.endswith(".py"):
                continue
            if f.startswith("test_"):
                continue
            if f.startswith(NON_OP_PREFIXES):
                continue
            if any(marker in f for marker in NON_OP_MARKERS):
                continue
            p = Path(root) / f
            if _is_ignored_path(p):
                continue
            yield p


def main() -> int:
    if not IN_TXT.exists():
        raise SystemExit(f"Missing {IN_TXT}")

    subfactores = [line.strip() for line in IN_TXT.read_text(encoding="utf-8").splitlines() if line.strip()]

    rows = []
    for path in iter_py_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            for name in subfactores:
                if name not in line:
                    continue
                if re.search(r"bus\.publicar\(\s*['\"]%s['\"]" % re.escape(name), line):
                    rows.append({
                        "subfactor": name,
                        "file": str(path.relative_to(ROOT)),
                        "line": idx,
                    })

    rows.sort(key=lambda r: (r["subfactor"], r["file"], r["line"]))
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["subfactor", "file", "line"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Escrito: {OUT_CSV}")
    print(f"Entradas: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
