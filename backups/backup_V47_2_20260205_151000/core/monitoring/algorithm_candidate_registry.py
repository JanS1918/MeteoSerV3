"""
Registro de candidatas de algoritmos.
Auto‑corrige inputs al lenguaje canónico.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.bus.parametros_canonicos import (
    normalizar_lista_parametros_entrada,
    normalizar_parametro_bus,
    resolver_parametro_entrada,
)

logger = logging.getLogger("meteoser.algorithm_candidate_registry")


class AlgorithmCandidateRegistry:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._path = base_dir / "data" / "algorithm_candidates.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._data = raw.get("candidates", []) or []
            elif isinstance(raw, list):
                self._data = raw
            else:
                self._data = []
        except Exception:
            logger.exception("No se pudo cargar algorithm_candidates.json")
            self._data = []

    def listar(self) -> List[Dict[str, Any]]:
        return list(self._data)

    def agregar(self, cand: Dict[str, Any]) -> None:
        if not cand or not cand.get("id"):
            return
        cand = self._normalizar_candidata(cand)
        existente = next((c for c in self._data if c.get("id") == cand.get("id")), None)
        if existente:
            return
        self._data.append(cand)
        try:
            payload = {"candidates": self._data}
            self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("No se pudo guardar algorithm_candidates.json")

    def listar_por_categoria(self, categoria: str) -> List[Dict[str, Any]]:
        categoria_norm = normalizar_parametro_bus(categoria)
        return [c for c in self._data if c.get("categoria") == categoria_norm]

    def _normalizar_candidata(self, cand: Dict[str, Any]) -> Dict[str, Any]:
        if cand.get("categoria"):
            cand["categoria"] = normalizar_parametro_bus(str(cand.get("categoria")))
        if cand.get("inputs"):
            inputs = cand.get("inputs") or []
            normalizados = []
            for raw in inputs:
                if not isinstance(raw, str):
                    continue
                canon = resolver_parametro_entrada(raw) or raw
                normalizados.append(canon)
            cand["inputs"] = normalizar_lista_parametros_entrada(normalizados)
        return cand
