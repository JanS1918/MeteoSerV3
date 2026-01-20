"""
ApiEngine — Interfaz pública de MeteoSer.

Expone:
- Estado actual
- Índices
- Sensores
- Recomendaciones
- Comunicación oral
"""

from typing import Dict, Any
from core.context.context_engine import ContextEngine
from core.logging.log_engine import LogEngine


class ApiEngine:
    """
    API interna y externa de MeteoSer.
    """

    def __init__(
        self, context_engine: ContextEngine, log_engine: LogEngine = None
    ) -> None:
        self.ctx: ContextEngine = context_engine
        self._log: LogEngine = log_engine

    # ------------------------------------------------------------
    # CONSULTAS
    # ------------------------------------------------------------

    def obtener_estado(self) -> Dict[str, Any]:
        return self.ctx.obtener_contexto()

    def obtener_indices(self) -> Dict[str, Any]:
        return self.ctx.obtener_contexto().get("indices", {})

    def obtener_sensores(self) -> Dict[str, Any]:
        return self.ctx.obtener_contexto().get("sensores", {})

    # ------------------------------------------------------------
    # ACCIONES
    # ------------------------------------------------------------

    def anunciar_estado(self) -> None:
        estado: Dict[str, Any] = self.obtener_estado()
        texto: str = (
            f"Temperatura {estado['sensores']['temperatura_fusionada']} grados."
        )
        self.ctx.comunicacion.responder(texto, estado)

    def anunciar_indices(self) -> None:
        indices: Dict[str, Any] = self.obtener_indices()
        texto = "Aquí tienes los índices ambientales."
        self.ctx.comunicacion.responder(texto, indices)
