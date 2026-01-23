"""Paquete de utilidades de `core`.

Exporta funciones auxiliares y submódulos como `daynight`.
"""
from .daynight import estado_dia_hibrido  # reexportar la función principal

def safe_get(dictionary, key, default=None):
    try:
        return dictionary.get(key, default)
    except Exception:
        return default

__all__ = ["estado_dia_hibrido", "safe_get"]
