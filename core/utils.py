"""Compat shim: exponer utilidades y permitir `core.utils.daynight`.

Este módulo existe para compatibilidad retroactiva. Para que
`import core.utils.daynight` funcione incluso si hay un paquete
`core.utils`, exponemos `__path__` y cargamos el submódulo cuando sea posible.
"""
import os
import importlib

# Marcar este módulo como paquete a efectos del import de submódulos
__path__ = [os.path.dirname(__file__)]

def safe_get(dictionary, key, default=None):
    try:
        return dictionary.get(key, default)
    except Exception:
        return default

# Intentar importar submódulos comunes para compatibilidad
try:
    daynight_mod = importlib.import_module("core.utils.daynight")
    estado_dia_hibrido = getattr(daynight_mod, "estado_dia_hibrido", None)
except Exception:
    daynight_mod = None
    estado_dia_hibrido = None

__all__ = ["safe_get", "estado_dia_hibrido"]