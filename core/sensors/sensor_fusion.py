"""
Fusión avanzada de sensores MeteoSer.

Incluye:
- Fusión de sensores primarios
- Estimaciones de refuerzo (permitidas)
- Sensores virtuales (permitidos)
- Prohibiciones estrictas (no inventar datos, no sustituir sensores)
"""

from typing import Dict, Any, Optional
from core.logger import get_logger
import math
from core.indices.environmental_indices import _dew_point


class SensorFusion:
    """
    Motor de fusión de sensores MeteoSer.
    """

    def __init__(self, log_engine: Optional[Any] = None):
        if log_engine is not None:
            self._log = log_engine
        else:
            self._log = get_logger("SensorFusion")

    def _log_debug(self, msg: str) -> None:
        if self._log:
            self._log.debug(msg)

    # ------------------------------------------------------------
    # FUSIÓN DE TEMPERATURA
    # ------------------------------------------------------------

    def fusionar_temperatura(self, sensores: Dict[str, Dict[str, Any]], contexto: Dict[str, Any]) -> Optional[float]:
        valores = []
        pesos = []
        for nombre, datos in sensores.items():
            if datos["tipo"] == "temperatura_interior":
                valor = contexto.get(nombre)
                if valor is not None:
                    valores.append(valor)
                    pesos.append(datos.get("fiabilidad", 100.0))
        if not valores:
            return None
        if len(valores) == 1:
            return valores[0]
        total_peso = sum(pesos)
        fusion = sum(v * p for v, p in zip(valores, pesos)) / total_peso
        self._log_debug(f"[FusionTemp] valores={valores}, pesos={pesos}, fusion={fusion}")
        return fusion

    # ------------------------------------------------------------
    # FUSIÓN DE HUMEDAD
    # ------------------------------------------------------------

    def fusionar_humedad(self, sensores: Dict[str, Dict[str, Any]], contexto: Dict[str, Any]) -> Optional[float]:
        valores = []
        pesos = []
        for nombre, datos in sensores.items():
            if datos["tipo"] == "humedad_interior":
                valor = contexto.get(nombre)
                if valor is not None:
                    valores.append(valor)
                    pesos.append(datos.get("fiabilidad", 100.0))
        if not valores:
            return None
        if len(valores) == 1:
            return valores[0]
        total_peso = sum(pesos)
        fusion = sum(v * p for v, p in zip(valores, pesos)) / total_peso
        self._log_debug(f"[FusionHR] valores={valores}, pesos={pesos}, fusion={fusion}")
        return fusion

    # ------------------------------------------------------------
    # SENSORES VIRTUALES PERMITIDOS
    # ------------------------------------------------------------

    def estimar_punto_rocio(self, temperatura: float, humedad: float) -> Optional[float]:
        if temperatura is None or humedad is None:
            return None
        try:
            return _dew_point(float(temperatura), float(humedad))
        except Exception:
            return None

    def estimar_ot(self, temperatura: float, radiacion: float = 0.0) -> Optional[float]:
        if temperatura is None:
            return None
        return temperatura + radiacion * 0.1

    # ------------------------------------------------------------
    # PROHIBICIONES
    # ------------------------------------------------------------

    def prohibido_inventar(self) -> None:
        if self._log:
            self._log.warning("[SensorFusion] PROHIBIDO inventar datos")
