"""
ML Calibrator (stub de compatibilidad)
======================================

Provee `justice_calibrator` para evitar fallos de importación en auto_system_optimizer.
"""

from __future__ import annotations

from typing import Dict, Any


def justice_calibrator(*args, **kwargs) -> Dict[str, Any]:
    """Retorna un resultado neutro cuando no hay calibrador ML real."""
    return {
        "status": "stub",
        "calibrated": False,
        "score": 0.0,
        "details": {},
    }
