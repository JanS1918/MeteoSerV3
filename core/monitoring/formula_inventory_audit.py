#!/usr/bin/env python3
"""
Formula inventory audit.

Scans core/indices for callable formula-like functions and compares them
against FORMULA_HIERARCHY. This does not modify any registry.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Set

from core.bus import formula_hierarchy as fh


def _iter_modules(package_name: str) -> List[str]:
    modules = []
    try:
        pkg = importlib.import_module(package_name)
        for mod in pkgutil.walk_packages(pkg.__path__, package_name + "."):
            modules.append(mod.name)
    except Exception:
        return []
    return modules


def _is_formula_candidate(fn_name: str) -> bool:
    # Heuristica: funciones relevantes suelen contener verbos clave.
    tokens = ("indice_", "calcular_", "utci", "wbgt", "et", "radiacion", "presion", "rocio")
    return any(t in fn_name for t in tokens)


def audit() -> Dict[str, List[str]]:
    hierarchy = fh.FORMULA_HIERARCHY or {}
    registered: Set[str] = set()
    for _, group in hierarchy.items():
        for formula in group.values():
            registered.add(formula.nombre_tecnico)

    discovered: Set[str] = set()
    modules = _iter_modules("core.indices")
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if _is_formula_candidate(name):
                discovered.add(name)

    missing_in_hierarchy = sorted(discovered - registered)
    missing_in_code = sorted(registered - discovered)

    return {
        "discovered": sorted(discovered),
        "registered": sorted(registered),
        "missing_in_hierarchy": missing_in_hierarchy,
        "missing_in_code": missing_in_code,
    }


if __name__ == "__main__":
    report = audit()
    print("FORMULA INVENTORY AUDIT")
    print("discovered=", len(report["discovered"]))
    print("registered=", len(report["registered"]))
    print("missing_in_hierarchy=", len(report["missing_in_hierarchy"]))
    print("missing_in_code=", len(report["missing_in_code"]))
    if report["missing_in_hierarchy"]:
        print("\nMissing in hierarchy:")
        for name in report["missing_in_hierarchy"]:
            print("-", name)
    if report["missing_in_code"]:
        print("\nMissing in code:")
        for name in report["missing_in_code"]:
            print("-", name)
