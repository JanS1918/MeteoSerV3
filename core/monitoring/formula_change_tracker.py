from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("meteoser.formula_change_tracker")


@dataclass
class CambioFormula:
    ts: float
    formula_anterior: Optional[str]
    formula_nueva: Optional[str]
    motivo: str
    auditoria: Optional[str] = None


class FormulaChangeTracker:
    """
    Rastrea cambios de fórmula por valor/índice y expone un resumen para UI.
    - No genera alertas por sí mismo.
    - Solo marca bucle si detecta alternancia repetida.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._path = base_dir / "data" / "formula_change_log.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Dict] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            self._data = json.loads(self._path.read_text(encoding="utf-8")) or {}
        except Exception:
            logger.exception("No se pudo cargar el log de cambios de fórmula")
            self._data = {}

    def _save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("No se pudo guardar el log de cambios de fórmula")

    def registrar_cambio(
        self,
        nombre_valor: str,
        formula_anterior: Optional[str],
        formula_nueva: Optional[str],
        motivo: str,
    ) -> None:
        registro = self._data.setdefault(nombre_valor, {
            "cambios": [],
            "estabilizado": False,
            "last_estabilizado": None,
            "loop_detectado": False,
        })
        registro["cambios"].append({
            "ts": time.time(),
            "formula_anterior": formula_anterior,
            "formula_nueva": formula_nueva,
            "motivo": motivo,
        })
        registro["estabilizado"] = False
        registro["loop_detectado"] = self._detectar_bucle(registro["cambios"])
        self._save()

    def marcar_estabilizado(self, nombre_valor: str, estabilizado: bool = True) -> None:
        registro = self._data.setdefault(nombre_valor, {
            "cambios": [],
            "estabilizado": False,
            "last_estabilizado": None,
            "loop_detectado": False,
        })
        registro["estabilizado"] = bool(estabilizado)
        registro["last_estabilizado"] = time.time() if estabilizado else None
        registro["loop_detectado"] = self._detectar_bucle(registro["cambios"])
        self._save()

    def registrar_auditoria(self, nombre_valor: str, resultado: str) -> None:
        registro = self._data.setdefault(nombre_valor, {
            "cambios": [],
            "estabilizado": False,
            "last_estabilizado": None,
            "loop_detectado": False,
        })
        if registro.get("cambios"):
            registro["cambios"][-1]["auditoria"] = resultado
        self._save()

    def obtener_estado(self, nombre_valor: str) -> Dict:
        registro = self._data.get(nombre_valor) or {}
        cambios = registro.get("cambios", [])
        last_est = registro.get("last_estabilizado")
        if last_est:
            cambios_visibles = [c for c in cambios if c.get("ts", 0) > last_est]
        else:
            cambios_visibles = cambios
        return {
            "cambios": len(cambios_visibles) if not registro.get("estabilizado") else 0,
            "estabilizado": bool(registro.get("estabilizado")),
            "loop_detectado": bool(registro.get("loop_detectado")),
            "ultimo_cambio": cambios[-1] if cambios else None,
        }

    def resumen_ui(self) -> Dict[str, Dict]:
        resumen: Dict[str, Dict] = {}
        for nombre in self._data.keys():
            resumen[nombre] = self.obtener_estado(nombre)
        return resumen

    def listar_parametros(self) -> List[str]:
        return list(self._data.keys())

    def obtener_cambios(self, nombre_valor: str) -> List[Dict]:
        registro = self._data.get(nombre_valor) or {}
        return list(registro.get("cambios", []))

    def ultimo_cambio(self, nombre_valor: str) -> Optional[Dict]:
        cambios = self.obtener_cambios(nombre_valor)
        return cambios[-1] if cambios else None

    @staticmethod
    def _detectar_bucle(cambios: List[Dict]) -> bool:
        if len(cambios) < 4:
            return False
        recientes = cambios[-6:]
        formulas = [c.get("formula_nueva") for c in recientes if c.get("formula_nueva")]
        if len(formulas) < 4:
            return False
        # Detecta patrón alternante A-B-A-B
        a, b = formulas[-4], formulas[-3]
        if not a or not b or a == b:
            return False
        return formulas[-4:] == [a, b, a, b]
