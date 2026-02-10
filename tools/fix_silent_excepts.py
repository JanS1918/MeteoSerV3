"""Detecta (y opcionalmente corrige) bloques `except: pass` en el repositorio.
Modo por defecto: dry-run (lista ubicaciones). Para aplicar cambios, ejecutar con --apply.

Uso:
    python tools/fix_silent_excepts.py        # dry-run
    python tools/fix_silent_excepts.py --apply  # aplicar cambios (hace backup .bak por archivo)
"""

import ast
import os
import sys
import io
from typing import List, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IGNORED_DIRS = {'.venv', '__pycache__', 'backups', 'node_modules', '.git', 'tools/nssm'}


def find_pass_except_locations(code: str) -> List[Tuple[int,int]]:
    """Devuelve lista de (lineno, end_lineno) del handler que contiene sólo pass o pass+docstring"""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    locations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            # If the handler body is empty -> skip
            if not getattr(node, 'body', None):
                continue
            # Normalize: ignore Expr(Str) docstring at start
            body = list(node.body)
            while body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], 'value', None), ast.Constant) and isinstance(body[0].value.value, str):
                body = body[1:]
            # If remaining body is single Pass node -> match
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                lineno = node.lineno
                end_lineno = getattr(body[0], 'end_lineno', lineno)
                locations.append((lineno, end_lineno))
    return locations


def list_files(root: str) -> List[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored
        parts = set(dirpath.replace('\\','/').split('/'))
        if parts & IGNORED_DIRS:
            continue
        for f in filenames:
            if f.endswith('.py'):
                files.append(os.path.join(dirpath, f))
    return files


def show_context(lines: List[str], lineno: int, pad: int = 3) -> str:
    i = max(0, lineno - 1 - pad)
    j = min(len(lines), lineno - 1 + pad)
    return ''.join(f"{k+1:5d}: {lines[k]}" for k in range(i, j))


def apply_fix_to_code(code: str, locations: List[Tuple[int,int]]) -> str:
    """Reemplaza `except ...:\n    pass` por `except Exception as e:\n    logging.exception(...)` manteniendo indentación."""
    lines = code.splitlines(keepends=True)
    offset = 0
    for lineno, end_lineno in sorted(locations, key=lambda x: x[0], reverse=True):
        idx = lineno - 1
        # find indentation of the except block
        except_line = lines[idx]
        indent = except_line[:len(except_line) - len(except_line.lstrip())] + '    '
        # replacement text
        repl = f"{indent}logging.exception(\"Silent except at {lineno} - revisar contexto\")\n"
        # replace the pass (we assume pass is within end_lineno line)
        # Find the line index of 'pass' within range
        pass_idx = None
        for p in range(lineno-1, end_lineno):
            if lines[p].strip().startswith('pass'):
                pass_idx = p
                break
        if pass_idx is None:
            continue
        lines[pass_idx] = repl
    return ''.join(lines)


def main():
    apply = '--apply' in sys.argv
    files = list_files(ROOT)
    total = 0
    matches = 0
    results = []
    for fp in files:
        total += 1
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                code = fh.read()
        except Exception:
            continue
        locations = find_pass_except_locations(code)
        if locations:
            matches += 1
            results.append((fp, locations))
    # print summary
    print(f"Scanned {total} .py files. Found {matches} files with silent excepts.")
    for fp, locs in results:
        print('\n' + fp)
        with open(fp, 'r', encoding='utf-8') as fh:
            lines = fh.readlines()
        for lineno, end in locs:
            print(f"  - except at line {lineno}..{end}")
            print(show_context(lines, lineno, pad=2))

    if apply and results:
        import shutil
        import logging as _logging
        _logging.basicConfig(level=_logging.INFO)
        for fp, locs in results:
            bak = fp + '.bak'
            shutil.copy2(fp, bak)
            with open(fp, 'r', encoding='utf-8') as fh:
                code = fh.read()
            newcode = apply_fix_to_code(code, locs)
            with open(fp, 'w', encoding='utf-8') as fh:
                fh.write('import logging\n' + newcode if not code.lstrip().startswith('import') else newcode)
            print(f"Patched {fp} (backup: {bak})")
        print("Applied fixes. Review backups *.bak")

if __name__ == '__main__':
    main()
