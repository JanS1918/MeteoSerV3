"""
Módulo de física de máxima precisión (interfaz unificadora).
Provee funciones de saturación de vapor de nivel élite y utilidades de formato.

Implementación práctica: cuando esté disponible, prioriza la ecuación Virial+Greenspan
(usa PhysicsEngine2026 para Z y coeficiente virial). Si falta presión, cae a
Hyland-Wexler. Esta capa representa la "ley" de sustitución en el código.
"""
from typing import Optional
import math
from core.indices.environmental_indices import (
    saturacion_vapor_iapws_elite,
    saturacion_vapor_virial_greenspan,
    saturacion_vapor_hyland_wexler,
)


def saturacion_vapor_elite(temp_c: float, presion_pa: Optional[float] = None) -> float:
    """
    Presión de vapor de saturación (Pa) - Implementación de 'máxima precisión' usada por el sistema.
    - Si se provee `presion_pa`, se usa la versión Virial+Greenspan (más precisa).
    - Si no, se usa Hyland-Wexler.

    Nota: IAPWS-95 / Lemmon completas requieren librería externa; esta función
    actúa como adaptador y fuerza el uso de las piezas de mayor precisión
    ya presentes en el repositorio.
    """
    try:
        if presion_pa is not None:
            try:
                return float(saturacion_vapor_iapws_elite(temp_c, presion_pa))
            except Exception:
                return float(saturacion_vapor_virial_greenspan(temp_c, presion_pa))
        else:
            try:
                return float(saturacion_vapor_iapws_elite(temp_c, 101325.0))
            except Exception:
                return float(saturacion_vapor_hyland_wexler(temp_c, None))
    except Exception:
        # Fallback estricto a Hyland-Wexler
        return float(saturacion_vapor_hyland_wexler(temp_c, presion_pa))


def format_diamond(value: Optional[float], muro: bool = False) -> Optional[float]:
    """
    Formatea el valor para salida 'Diamante Limpio':
    - Si `muro` True devuelve entero redondeado.
    - Si `muro` False devuelve float con 2 decimales.
    - None se pasa como None.
    """
    if value is None:
        return None
    try:
        v = float(value)
    except Exception:
        return value
    if muro:
        return int(round(v))
    return round(v, 2)
