"""Módulo de almacenamiento - compresión y archivado."""

from .compresor_datos import (
    CompresorDatos,
    GestorArchivoHistorico,
    obtener_gestor_archivo_historico,
    iniciar_gestor_archivado
)

__all__ = [
    'CompresorDatos',
    'GestorArchivoHistorico',
    'obtener_gestor_archivo_historico',
    'iniciar_gestor_archivado'
]
