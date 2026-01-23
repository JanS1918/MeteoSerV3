from typing import Optional
from core.system.system_manager import SystemManager

_manager: Optional[SystemManager] = None
_system = None


def get_manager() -> SystemManager:
    global _manager, _system
    if _manager is None:
        _manager = SystemManager()
        try:
            _system = _manager.iniciar()
        except Exception:
            # iniciar puede fallar en contextos de import temprana; dejar manager disponible
            _system = None
    return _manager


def get_system():
    global _manager, _system
    if _manager is None:
        get_manager()
    if _system is None and _manager is not None:
        try:
            _system = _manager.iniciar()
        except Exception:
            _system = None
    return _system
