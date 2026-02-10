"""
Módulo de Ubicación y Astronomía.

Funcionalidades:
- Detección jerárquica de ubicación
- Cálculos astronómicos (amanecer, atardecer, radiación teórica)
- Indexación de parámetros para 6 motores (luz, ritmo circadiano, nocturno, etc.)

Uso:
    from core.location import detect_location, radiacion_teorica
    
    coords = detect_location(system)
    rad = radiacion_teorica(coords["lat"], dia_año, hora_decimal)
"""

from .location_module import (
    coords_valid,
    parse_coord,
    coords_es_spain,
    detect_location,
    arco_solar,
    radiacion_teorica,
    hhmm_a_minutos,
    minutos_a_hhmm,
    calcular_anejo_astronomico,
)

__all__ = [
    "coords_valid",
    "parse_coord",
    "coords_es_spain",
    "detect_location",
    "arco_solar",
    "radiacion_teorica",
    "hhmm_a_minutos",
    "minutos_a_hhmm",
    "calcular_anejo_astronomico",
]
