#!/usr/bin/env python3
"""
Auto-registro de formulas descubiertas (solo para duelos/analisis).

Genera un archivo JSON con todas las funciones candidatas encontradas en
core.indices, agrupadas por parametro.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict

from core.monitoring.duel_round_robin import _discover_formulas


def build_auto_registry() -> Dict[str, Any]:
    discovered, unmapped = _discover_formulas()
    payload = {
        "timestamp": datetime.now().isoformat(),
        "parameters": {k: [asdict(f) for f in v] for k, v in discovered.items()},
        "counts": {
            "parameters": len(discovered),
            "formulas": sum(len(v) for v in discovered.values()),
            "unmapped": len(unmapped),
        },
        "unmapped": unmapped,
    }
    return payload


def write_auto_registry(output_path: Path) -> Dict[str, Any]:
    payload = build_auto_registry()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    out_path = Path.cwd() / "data" / "auto_formula_registry.json"
    payload = write_auto_registry(out_path)
    print("Auto-registry written to:", out_path)
    print("parameters:", payload["counts"]["parameters"])
    print("formulas:", payload["counts"]["formulas"])
    print("unmapped:", payload["counts"]["unmapped"])
