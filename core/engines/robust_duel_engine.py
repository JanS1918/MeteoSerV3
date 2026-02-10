"""
Robust Duel Engine (stub de compatibilidad)
==========================================

Provee `robust_duel_engine` para evitar fallos de importación.
"""

from __future__ import annotations

from typing import Dict, Any


def robust_duel_engine(*args, **kwargs) -> Dict[str, Any]:
    """Retorna un resultado neutro cuando el motor real no está disponible."""
    return {
        "status": "stub",
        "winner": None,
        "margin": 0.0,
        "details": {},
    }
