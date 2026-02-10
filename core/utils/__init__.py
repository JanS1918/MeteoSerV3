"""
Utilidades del sistema MeteoSer
"""

from .rolling_windows import RollingWindowManager, RollingWindow


def safe_get(dictionary, key, default=None):
	"""Acceso seguro a dicts (compatibilidad con core.config)."""
	try:
		if dictionary is None:
			return default
		return dictionary.get(key, default)
	except Exception:
		return default


__all__ = ['RollingWindowManager', 'RollingWindow', 'safe_get']
