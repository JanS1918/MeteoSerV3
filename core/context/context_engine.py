"""
ContextEngine — El cerebro integrador de MeteoSer.

Une:
- SensorSystem
- EnvironmentalEngines
- CommunicationEngine
- AutoImprovementSystem

Produce un contexto unificado listo para API y UI.
"""

from typing import Dict, Any, Optional
from core.engines.sensor_engine import SensorSystem
from core.engines.environmental_engines import MotorAmbiental
from core.engines.communication_engine import CommunicationEngine
from core.engines.auto_improvement_engine import AutoImprovementSystem
from core.logging.log_engine import LogEngine


class ContextEngine:
    """
    Orquesta todos los motores y produce un estado global coherente.
    """

    def __init__(self, log_engine: Optional[LogEngine] = None):
        self._log = log_engine

        self.sensores = SensorSystem(log_engine)
        self.ambiental = MotorAmbiental(log_engine)
        self.comunicacion = CommunicationEngine(log_engine)
        self.auto = AutoImprovementSystem(log_engine)

        self._ultimo_contexto: Dict[str, Any] = {}

    # ------------------------------------------------------------
    # ACTUALIZACIÓN PRINCIPAL
    # ------------------------------------------------------------

    def actualizar(self, datos_sensores: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza todos los motores y devuelve un contexto global.
        """

        # 1. Fusión de sensores
        fusion = self.sensores.actualizar(datos_sensores)

        # 2. Índices ambientales — construir contexto y usar el motor de análisis
        contexto_ambiental = {
            "temperatura_interior": fusion.get("temperatura_fusionada"),
            "humedad_interior": fusion.get("humedad_fusionada"),
            "punto_rocio": fusion.get("punto_rocio_estimado"),
        }
        indices = self.ambiental.analizar(contexto_ambiental)

        # 3. Auto-mejora
        self.auto.registrar_evento(
            {"tipo": "ciclo", "indice_relacionado": None, "aceptado": True}
        )
        auto = self.auto.ciclo()

        # 4. Construcción del contexto final
        contexto = {
            "sensores": fusion,
            "indices": indices,
            "auto": auto,
        }

        self._ultimo_contexto = contexto
        return contexto

    # ------------------------------------------------------------
    # ACCESO AL CONTEXTO
    # ------------------------------------------------------------

    def obtener_contexto(self) -> Dict[str, Any]:
        return self._ultimo_contexto
