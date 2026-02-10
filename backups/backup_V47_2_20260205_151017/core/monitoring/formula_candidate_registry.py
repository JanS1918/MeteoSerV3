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

logger = logging.getLogger("meteoser.formula_candidate_registry")


class FormulaCandidateRegistry:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._path = base_dir / "data" / "formula_candidates.json"
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
            logger.exception("No se pudo cargar formula_candidates.json")
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
            logger.exception("No se pudo guardar formula_candidates.json")

    def listar_por_parametro(self, parametro: str) -> List[Dict[str, Any]]:
        parametro_norm = normalizar_parametro_bus(parametro)
        return [c for c in self._data if c.get("parametro") == parametro_norm]

    def _normalizar_candidata(self, cand: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-corrección total: adapta candidatos al lenguaje canónico."""
        if cand.get("parametro"):
            cand["parametro"] = normalizar_parametro_bus(str(cand.get("parametro")))
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

    def resolver(self, nombre: str) -> Optional[Dict[str, Any]]:
        if not nombre:
            return None
        for cand in self._data:
            if cand.get("id") == nombre:
                return cand
            aliases = cand.get("aliases") or []
            if nombre in aliases:
                return cand
        return None

    def resolver_por_alias(self, texto: str) -> Optional[Dict[str, Any]]:
        if not texto:
            return None
        texto_norm = texto.strip().lower()
        for cand in self._data:
            aliases = cand.get("aliases") or []
            if any(texto_norm == str(a).strip().lower() for a in aliases):
                return cand
        return None

    @staticmethod
    def obtener_inputs(cand: Dict[str, Any]) -> List[str]:
        return normalizar_lista_parametros_entrada(cand.get("inputs") or [])

    @staticmethod
    def obtener_funcion(cand: Dict[str, Any]):
        modulo = cand.get("module")
        funcion = cand.get("function")
        if not modulo or not funcion:
            return None
        try:
            import importlib
            mod = importlib.import_module(modulo)
            fn = getattr(mod, funcion, None)
            return fn if callable(fn) else None
        except Exception:
            return None
