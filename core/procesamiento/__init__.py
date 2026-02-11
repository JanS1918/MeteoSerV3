"""Módulo de procesamiento - batch, deduplicación."""

from .deduplicador import (
    DeduplicadorEventos,
    DeduplicadorIdempotencia,
    obtener_deduplicador_eventos,
    obtener_deduplicador_idempotencia,
    iniciar_deduplicadores
)

from .batch_processor import (
    ProcesadorBatch,
    GestorProcesadoresBatch,
    obtener_gestor_batch,
    iniciar_procesadores_batch
)

__all__ = [
    'DeduplicadorEventos',
    'DeduplicadorIdempotencia',
    'obtener_deduplicador_eventos',
    'obtener_deduplicador_idempotencia',
    'iniciar_deduplicadores',
    'ProcesadorBatch',
    'GestorProcesadoresBatch',
    'obtener_gestor_batch',
    'iniciar_procesadores_batch'
]
