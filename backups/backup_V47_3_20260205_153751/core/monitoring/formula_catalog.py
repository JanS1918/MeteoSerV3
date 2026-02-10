#!/usr/bin/env python3
"""
Catálogo simple de fórmulas.

Expone una interfaz estable para listar fórmulas disponibles.
Se alimenta de FORMULA_HIERARCHY.
"""

from __future__ import annotations

from typing import List
from core.bus.formula_hierarchy import FORMULA_HIERARCHY, Fórmula


class FormulaCatalogo:
    def __init__(self) -> None:
        self._formulas: List[Fórmula] = []

    def cargar(self) -> None:
        """Carga fórmulas desde FORMULA_HIERARCHY."""
        self._formulas = []
        try:
            grupos = FORMULA_HIERARCHY or {}
            for _, formulas in grupos.items():
                if isinstance(formulas, dict):
                    self._formulas.extend(list(formulas.values()))
                elif isinstance(formulas, list):
                    self._formulas.extend(formulas)
        except Exception:
            self._formulas = []

    def obtener_todas(self) -> List[Fórmula]:
        return list(self._formulas)
