"""
Transient Classifier (stub de compatibilidad)
============================================

Provee `transient_classifier` para evitar fallos de importación.
"""

from __future__ import annotations

from typing import Dict, Any


def transient_classifier(*args, **kwargs) -> Dict[str, Any]:
    """Retorna clasificación neutra cuando el clasificador real no está disponible."""
    return {
        "status": "stub",
        "is_transient": False,
        "confidence": 0.0,
        "details": {},
    }
