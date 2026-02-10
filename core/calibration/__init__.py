"""
Módulo de CALIBRACIÓN - Auto-optimización de sensores
======================================================

Sistema completo de calibración con:
- DetectorBias: Detección avanzada (offset, regresión, deriva temporal)
- CalibradorRegresion: Correcciones por ML
- ManagerCalibracion: Gestión de múltiples sensores
- OrquestadorCalibracion: Automatización completa
"""

# Básico (siempre disponible)
from core.calibration.auto_calibrator import (
    AutoCalibrador,
    ModeloCalibracion,
    obtener_auto_calibrador
)

# Avanzado (requiere sklearn)
try:
    from core.calibration.bias_detector import DetectorBias
    from core.calibration.regression_calibrator import (
        CalibradorRegresion,
        ManagerCalibracion
    )
    from core.calibration.auto_calibrator import (
        OrquestadorCalibracion,
        obtener_orquestador_calibracion
    )
    CALIBRACION_AVANZADA_DISPONIBLE = True
except ImportError:
    DetectorBias = None
    CalibradorRegresion = None
    ManagerCalibracion = None
    OrquestadorCalibracion = None
    obtener_orquestador_calibracion = None
    CALIBRACION_AVANZADA_DISPONIBLE = False

__all__ = [
    # Básico
    'AutoCalibrador',
    'ModeloCalibracion',
    'obtener_auto_calibrador',
    # Avanzado
    'DetectorBias',
    'CalibradorRegresion',
    'ManagerCalibracion',
    'OrquestadorCalibracion',
    'obtener_orquestador_calibracion',
    'CALIBRACION_AVANZADA_DISPONIBLE'
]
