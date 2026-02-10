#!/usr/bin/env python3
"""
Deduplica subfactores publicados con bus.publicar cuando el valor publicado
(es expresion + unidad) es identico dentro de la misma funcion.

Flujo recomendado:
1) Generar plan:   python scripts/dedup_clones.py --plan
2) Aplicar lote:   python scripts/dedup_clones.py --apply --batch-index 0 --batch-size 20

Salidas:
- output/dedup_plan.json
- output/dedup_plan_summary.json
- output/dedup_applied_batch_<n>.json
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
PLAN_PATH = OUTPUT_DIR / "dedup_plan.json"
PLAN_SUM_PATH = OUTPUT_DIR / "dedup_plan_summary.json"

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


def iter_py_files() -> List[Path]:
    py_files: List[Path] = []
    for root, dirs, files in os.walk(ROOT):
        # prune ignored dirs
        dirs[:] = [d for d in dirs if not _is_ignored_path(Path(d))]
        for f in files:
            if not f.endswith(".py"):
                continue
            p = Path(root) / f
            if _is_ignored_path(p):
                continue
            py_files.append(p)
    return py_files


def _norm_text(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


class PublishCollector(ast.NodeVisitor):
    def __init__(self, source: str):
        self.source = source
        self.class_stack: List[str] = []
        self.func_stack: List[str] = []
        self.entries: List[Dict] = []

    def _current_scope(self) -> str:
        if self.class_stack and self.func_stack:
            return "{}::{}".format(".".join(self.class_stack), ".".join(self.func_stack))
        if self.func_stack:
            return "::".join(self.func_stack)
        if self.class_stack:
            return ".".join(self.class_stack)
        return "<module>"

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    def visit_Expr(self, node: ast.Expr):
        if isinstance(node.value, ast.Call) and _is_publicar_call(node.value):
            call = node.value
            if not call.args:
                return
            name = _extract_str_constant(call.args[0])
            if not name:
                return
            expr_src = _get_node_src(self.source, call.args[1]) if len(call.args) >= 2 else ""
            unit_src = _get_node_src(self.source, call.args[2]) if len(call.args) >= 3 else ""
            entry = {
                "name": name,
                "expr": _norm_text(expr_src),
                "unit": _norm_text(unit_src),
                "scope": self._current_scope(),
                "line_start": getattr(node, "lineno", None),
                "line_end": getattr(node, "end_lineno", None),
            }
            self.entries.append(entry)
        self.generic_visit(node)


def _is_publicar_call(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute) and func.attr == "publicar":
        return True
    return False


def _extract_str_constant(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def _get_node_src(source: str, node: ast.AST) -> str:
    src = ast.get_source_segment(source, node)
    if src is not None:
        return src
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def build_plan() -> Dict:
    py_files = iter_py_files()

    entries: List[Dict] = []
    name_set = set()

    for path in py_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        try:
            tree = ast.parse(text)
        except Exception:
            continue
        collector = PublishCollector(text)
        collector.visit(tree)
        for e in collector.entries:
            e["file"] = str(path.relative_to(ROOT))
            entries.append(e)
            name_set.add(e["name"])

    # count usage of each name (string literal occurrences in code)
    name_counts: Dict[str, int] = {n: 0 for n in name_set}
    if name_counts:
        for path in py_files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            try:
                tree = ast.parse(text)
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if node.value in name_counts:
                        name_counts[node.value] += 1

    # group by (file, scope, expr, unit)
    groups: Dict[Tuple[str, str, str, str], List[Dict]] = {}
    for e in entries:
        key = (e["file"], e["scope"], e["expr"], e["unit"])
        groups.setdefault(key, []).append(e)

    # build plan
    plan_groups: List[Dict] = []
    for key, items in groups.items():
        unique_names = sorted({i["name"] for i in items})
        if len(unique_names) <= 1:
            continue
        # canonical = most used
        canonical = max(unique_names, key=lambda n: (name_counts.get(n, 0), n))
        # choose keep entry: first occurrence of canonical or first item
        keep_entry = None
        for it in items:
            if it["name"] == canonical:
                keep_entry = it
                break
        if keep_entry is None:
            keep_entry = items[0]

        removals = []
        for it in items:
            if it is keep_entry:
                continue
            removals.append(it)

        plan_groups.append({
            "file": key[0],
            "scope": key[1],
            "expr": key[2],
            "unit": key[3],
            "canonical": canonical,
            "names": unique_names,
            "keep": keep_entry,
            "remove": removals,
        })

    # sort by size desc then name
    plan_groups.sort(key=lambda g: (-len(g["names"]), g["canonical"]))

    plan = {
        "total_entries": len(entries),
        "total_groups": len(plan_groups),
        "groups": plan_groups,
    }
    return plan


def _apply_replacements(text: str, replacements: Dict[str, str]) -> str:
    for old, new in replacements.items():
        if old == new:
            continue
        pattern = re.compile(r"(['\"])%s\1" % re.escape(old))
        text = pattern.sub(lambda m: f"{m.group(1)}{new}{m.group(1)}", text)
    return text


def _apply_removals(text: str, ranges: List[Tuple[int, int]]) -> str:
    if not ranges:
        return text
    lines = text.splitlines()
    for start, end in sorted(ranges, key=lambda r: r[0], reverse=True):
        if start is None or end is None:
            continue
        start_idx = max(0, start - 1)
        end_idx = min(len(lines), end)
        if start_idx >= end_idx:
            continue
        del lines[start_idx:end_idx]
    new_text = "\n".join(lines)
    if text.endswith("\n"):
        new_text += "\n"
    return new_text


def apply_batch(plan: Dict, batch_index: int, batch_size: int) -> Dict:
    groups = plan.get("groups", [])
    start = batch_index * batch_size
    end = min(len(groups), start + batch_size)
    batch = groups[start:end]

    # build per-file ops
    file_replacements: Dict[str, Dict[str, str]] = {}
    file_removals: Dict[str, List[Tuple[int, int]]] = {}

    for g in batch:
        canonical = g["canonical"]
        for name in g["names"]:
            if name == canonical:
                continue
            file_replacements.setdefault("*", {})[name] = canonical

        # remove duplicate publicar calls
        for r in g["remove"]:
            file_removals.setdefault(r["file"], []).append(
                (r.get("line_start"), r.get("line_end"))
            )

        # ensure keep entry uses canonical name
        keep = g["keep"]
        if keep["name"] != canonical:
            file_replacements.setdefault("*", {})[keep["name"]] = canonical

    changed_files = []

    for path in iter_py_files():
        rel = str(path.relative_to(ROOT))
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        original = text
        repls = file_replacements.get("*", {})
        if repls:
            text = _apply_replacements(text, repls)
        removals = file_removals.get(rel, [])
        if removals:
            text = _apply_removals(text, removals)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed_files.append(rel)

    report = {
        "batch_index": batch_index,
        "batch_size": batch_size,
        "groups_applied": len(batch),
        "changed_files": changed_files,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", action="store_true", help="Generar plan de deduplicacion")
    parser.add_argument("--apply", action="store_true", help="Aplicar un lote del plan")
    parser.add_argument("--batch-index", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=20)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.plan:
        plan = build_plan()
        PLAN_PATH.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        PLAN_SUM_PATH.write_text(
            json.dumps({
                "total_entries": plan["total_entries"],
                "total_groups": plan["total_groups"],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Plan generado: {PLAN_PATH}")
        print(f"Resumen: {PLAN_SUM_PATH}")
        return 0

    if args.apply:
        if not PLAN_PATH.exists():
            print("No existe el plan. Ejecuta con --plan primero.")
            return 1
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        report = apply_batch(plan, args.batch_index, args.batch_size)
        out_report = OUTPUT_DIR / f"dedup_applied_batch_{args.batch_index}.json"
        out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Lote aplicado: {out_report}")
        return 0

    print("Nada que hacer. Usa --plan o --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
