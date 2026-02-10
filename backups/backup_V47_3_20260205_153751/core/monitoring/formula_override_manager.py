from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Any, List

logger = logging.getLogger("meteoser.formula_override")


class FormulaOverrideManager:
    """
    Gestiona overrides de fórmulas por parámetro y escenario.
    Formato:
    {
      "punto_rocio": {
        "default": "hardy_temperatura_rocio_c",
        "scenarios": [
          {"temp_min": null, "temp_max": 0, "formula": "punto_rocio_magnus"}
        ],
        "updated": 1730000000
      }
    }
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._path = base_dir / "data" / "formula_overrides.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            self._data = json.loads(self._path.read_text(encoding="utf-8")) or {}
        except Exception:
            logger.exception("No se pudo cargar formula_overrides.json")
            self._data = {}

    def _save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("No se pudo guardar formula_overrides.json")

    def set_default(self, parametro: str, formula_tecnica: str) -> None:
        registro = self._data.setdefault(parametro, {})
        registro["default"] = formula_tecnica
        registro["updated"] = time.time()
        self._save()

    def set_scenarios(self, parametro: str, scenarios: List[Dict[str, Any]]) -> None:
        registro = self._data.setdefault(parametro, {})
        registro["scenarios"] = scenarios
        registro["updated"] = time.time()
        self._save()

    def clear(self, parametro: str) -> None:
        if parametro in self._data:
            del self._data[parametro]
            self._save()

    def get_override(self, parametro: str, temperatura: Optional[float] = None) -> Optional[str]:
        registro = self._data.get(parametro)
        if not registro:
            return None
        scenarios = registro.get("scenarios") or []
        if temperatura is not None:
            for sc in scenarios:
                t_min = sc.get("temp_min")
                t_max = sc.get("temp_max")
                if (t_min is None or temperatura >= t_min) and (t_max is None or temperatura < t_max):
                    return sc.get("formula")
        return registro.get("default")

    def dump(self) -> Dict[str, Any]:
        return self._data.copy()
