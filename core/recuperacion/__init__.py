"""Módulo de recuperación - failover y health checks."""

from .gestor_failover import (
    VerificadorSalud,
    GestorRecuperacion,
    obtener_gestor_recuperacion,
    iniciar_failover_recovery
)

__all__ = [
    'VerificadorSalud',
    'GestorRecuperacion',
    'obtener_gestor_recuperacion',
    'iniciar_failover_recovery'
]
