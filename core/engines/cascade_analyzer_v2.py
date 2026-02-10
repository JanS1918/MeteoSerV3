"""
Cascade Analyzer v2 (stub de compatibilidad)
===========================================

Provee una función mínima para evitar errores de importación en
core.engines.auto_system_optimizer.
"""

from __future__ import annotations

from typing import Dict, Any


def cascade_analyzer(*args, **kwargs) -> Dict[str, Any]:
    """Retorna un resultado neutro cuando el analizador real no está disponible."""
    return {
        "status": "stub",
        "issues": [],
        "score": 0.0,
        "details": {},
    }
