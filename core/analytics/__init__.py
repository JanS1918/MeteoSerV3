"""
core.analytics
══════════════════════════════════════════════════════════════════════════════

Módulo de análisis avanzado del sistema MeteoSerV3.

Componentes:
  - analisis_historico: Análisis temporal, tendencias y predicciones
  - calculador_salud: Puntuación integral 0-100 del sistema
  - gestor_tenants: Multi-tenancy con aislamiento completo

Fecha: 2026-02-11
"""

from .analisis_historico import (
    AnalizadorHistorico,
    obtener_analizador,
    iniciar_analizador
)

from .calculador_salud import (
    CalculadorSalud,
    obtener_calculador,
    iniciar_calculador_salud
)

from .gestor_tenants import (
    GestorTenants,
    ConfiguracionTenant,
    EstadoTenant,
    obtener_gestor_tenants,
    iniciar_gestor_tenants
)

__all__ = [
    'AnalizadorHistorico',
    'obtener_analizador',
    'iniciar_analizador',
    'CalculadorSalud',
    'obtener_calculador',
    'iniciar_calculador_salud',
    'GestorTenants',
    'ConfiguracionTenant',
    'EstadoTenant',
    'obtener_gestor_tenants',
    'iniciar_gestor_tenants'
]
