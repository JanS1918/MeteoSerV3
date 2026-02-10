# Scheduler automático de MeteoSerV3 V51
from .calculador_indices_automatico import (
    CalculadorIndicesAutomatico,
    iniciar_calculador_indices,
    detener_calculador_indices,
    obtener_calculador_indices
)

from .calculador_derivadas_rapidas_v51 import (
    CalculadorDerivadosRapidosV51,
    iniciar_calculador_derivadas_rapidas,
    detener_calculador_derivadas_rapidas,
    obtener_calculador_derivadas_rapidas
)

__all__ = [
    'CalculadorIndicesAutomatico',
    'iniciar_calculador_indices',
    'detener_calculador_indices',
    'obtener_calculador_indices',
    'CalculadorDerivadosRapidosV51',
    'iniciar_calculador_derivadas_rapidas',
    'detener_calculador_derivadas_rapidas',
    'obtener_calculador_derivadas_rapidas'
]
