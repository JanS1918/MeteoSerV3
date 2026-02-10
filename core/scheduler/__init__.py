# Scheduler automático de MeteoSerV3 V51
from .calculador_indices_automatico import (
    CalculadorIndicesAutomatico,
    iniciar_calculador_indices,
    detener_calculador_indices,
    obtener_calculador_indices
)

__all__ = [
    'CalculadorIndicesAutomatico',
    'iniciar_calculador_indices',
    'detener_calculador_indices',
    'obtener_calculador_indices'
]
