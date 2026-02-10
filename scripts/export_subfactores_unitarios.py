#!/usr/bin/env python3
"""Exporta lista unica de subfactores publicados con bus.publicar."""
from __future__ import annotations

import ast
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
OUT_TXT = OUTPUT_DIR / "subfactores_unitarios.txt"
OUT_JSON = OUTPUT_DIR / "subfactores_unitarios.json"
OUT_OP_TXT = OUTPUT_DIR / "subfactores_unitarios_operativos.txt"
OUT_OP_JSON = OUTPUT_DIR / "subfactores_unitarios_operativos.json"


NON_OP_PREFIXES = (
    "test_",
    "CIERRE_",
    "ejemplo_",
)

NON_OP_MARKERS = (
    "_BACKUP_",
    "_CERTIFICADO",
)

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "archive",
    "backups",
    "mod_backups",
    "BACKUP_SELLO_SHA256_20260206_022119",
    "data",
}


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
            p = Path(root) / f
            if _is_ignored_path(p):
                continue
            yield p


def _is_test_path(path: Path) -> bool:
    if "tests" in path.parts:
        return True
    if path.name.startswith("test_"):
        return True
    return False


def _is_non_operational_file(path: Path) -> bool:
    name = path.name
    if name.startswith(NON_OP_PREFIXES):
        return True
    for marker in NON_OP_MARKERS:
        if marker in name:
            return True
    return False


def _extract_str_constant(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def _is_publicar_call(call: ast.Call) -> bool:
    func = call.func
    return isinstance(func, ast.Attribute) and func.attr == "publicar"


def main() -> int:
    names = set()
    operativos = set()
    for path in iter_py_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        try:
            tree = ast.parse(text)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_publicar_call(node):
                if not node.args:
                    continue
                name = _extract_str_constant(node.args[0])
                if name:
                    names.add(name)
                    if not _is_test_path(path) and not _is_non_operational_file(path):
                        operativos.add(name)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sorted_names = sorted(names)
    OUT_TXT.write_text("\n".join(sorted_names) + "\n", encoding="utf-8")
    OUT_JSON.write_text(
        "[\n" + ",\n".join(f"  \"{n}\"" for n in sorted_names) + "\n]\n",
        encoding="utf-8",
    )
    sorted_operativos = sorted(operativos)
    OUT_OP_TXT.write_text("\n".join(sorted_operativos) + "\n", encoding="utf-8")
    OUT_OP_JSON.write_text(
        "[\n" + ",\n".join(f"  \"{n}\"" for n in sorted_operativos) + "\n]\n",
        encoding="utf-8",
    )
    print(f"Subfactores unitarios: {len(sorted_names)}")
    print(f"Escrito: {OUT_TXT}")
    print(f"Escrito: {OUT_JSON}")
    print(f"Subfactores unitarios operativos: {len(sorted_operativos)}")
    print(f"Escrito: {OUT_OP_TXT}")
    print(f"Escrito: {OUT_OP_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
