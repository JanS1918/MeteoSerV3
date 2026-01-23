"""Registro limpio temporal para reemplazar registry.py corrupto.
"""
from typing import Callable, Dict, List, Optional, Tuple
from pathlib import Path
import json
import time
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
STATUS_FILE = DATA_DIR / "indices_registry_status.json"

_registry: Dict[str, List[Tuple[int, Callable]]] = {}


def register_index(name: str, func: Callable, priority: int = 50) -> None:
    """Registrar una implementación para `name` con `priority` (mayor = preferido)."""
    lst = _registry.setdefault(name, [])
    lst.append((int(priority), func))
    lst.sort(key=lambda x: x[0], reverse=True)


def get_index_impl(name: str) -> Optional[Callable]:
    """Devolver la implementación preferida para `name` o None si no existe."""
    lst = _registry.get(name)
    if not lst:
        return None
    return lst[0][1]


def list_registered() -> Dict[str, List[str]]:
    """Listar índices registrados con sus implementaciones (por nombre)."""
    out = {}
    for k, lst in _registry.items():
        out[k] = [f"priority={p}:{getattr(f, '__name__', str(f))}" for p, f in lst]
    return out


def try_register_library_fallbacks() -> None:
    """Registrar implementaciones basadas en librerías si están disponibles.

    Añade implementaciones preferentes para PMV/PPD y WBGT cuando
    `pythermalcomfort` esté instalado.
    """
    if importlib.util.find_spec("pythermalcomfort") is None:
        return
    try:
        from pythermalcomfort.models import pmv_ppd as _py_pmv_ppd

        def _pmv_ppd_lib(ta, tr, vel, rh, met=1.2, clo=0.5):
            try:
                return _py_pmv_ppd(ta=ta, tr=tr, vel=vel, rh=rh, met=met, clo=clo)
            except Exception:
                return None

        register_index("pmv_ppd", _pmv_ppd_lib, priority=100)
    except Exception:
        pass
    try:
        from pythermalcomfort.models import wbgt as _py_wbgt

        def _wbgt_lib(tdb, rh, v):
            try:
                return _py_wbgt(tdb=tdb, rh=rh, v=v)
            except Exception:
                return None

        register_index("wbgt", _wbgt_lib, priority=100)
    except Exception:
        pass


def update_registry_and_write_status(sensor_file: Optional[str] = None) -> None:
    """Actualizar el registro intentando detectar mejoras y escribir estado.

    - vuelve a registrar implementaciones basadas en librerías
    - detecta sensores listados en `sensor_file` (si existe) para informar
    - escribe `data/indices_registry_status.json` con timestamp y registro
    """
    try:
        try_register_library_fallbacks()
    except Exception:
        pass

    sensors = []
    try:
        if sensor_file:
            p = Path(sensor_file)
        else:
            p = DATA_DIR / "last_sensores.json"
        if p.exists():
            content = json.loads(p.read_text(encoding="utf-8"))
            # Expecting a list or dict with sensors
            if isinstance(content, dict):
                # try common shapes
                if "sensors" in content and isinstance(content["sensors"], list):
                    sensors = content["sensors"]
                else:
                    # fallback: try values
                    sensors = list(content.values())
            elif isinstance(content, list):
                sensors = content
    except Exception:
        sensors = []

    detected = []
    for s in sensors:
        try:
            if isinstance(s, dict):
                name = s.get("canonical") or s.get("name") or s.get("map_to")
            else:
                name = str(s)
            if name:
                detected.append(name)
        except Exception:
            continue

    status = {
        "timestamp": int(time.time()),
        "registered": list_registered(),
        "detected_sensors": detected,
    }
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATUS_FILE.write_text(json.dumps(status, indent=2), encoding="utf-8")
    except Exception:
        pass


try:
    try_register_library_fallbacks()
except Exception:
    pass
