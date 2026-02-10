"""
Módulo BUS - Capas de Información Inteligente + Infraestructura de Datos Masivos
==================================================================================

Sistema de flujo de datos:
- BusCapasInformacion: 4 capas jerárquicas (CORE, CALCULATED, INTERMEDIATE, DEBUG)
- BusIndexer: Búsqueda inteligente por ADN (O(k))
- BusAsyncWriter: Escritura sin contención (lock-free)
- DatoConHistorico: Variables con histórico integrado
- BusSnapshotDinamico: Resumen automático sin sesgo
"""

# Componentes originales (Capas)
from core.bus.bus_capas_informacion import (
    BusCapasInformacion,
    CapaInformacion,
    TimeseriesVariable,
    MetadatosLinaje,
    obtener_bus
)

from core.bus.bus_v3_adapter import BusV3Adapter

from core.bus.monitor_bus import (
    MonitorBusRealtime,
    mostrar_monitor_una_vez
)

# Nuevos componentes (Datos Masivos)
from core.bus.bus_indexer import BusIndexer, NodoTrie
from core.bus.bus_async_writer import BusAsyncWriter, WriterConIntento
from core.bus.dato_historico import DatoConHistorico, BufferCircular
from core.bus.bus_snapshot import BusSnapshotDinamico, SnapshotBuilder

__all__ = [
    # Capas originales
    'BusCapasInformacion',
    'CapaInformacion',
    'TimeseriesVariable',
    'MetadatosLinaje',
    'obtener_bus',
    'BusV3Adapter',
    'MonitorBusRealtime',
    'mostrar_monitor_una_vez',
    # Datos masivos
    'BusIndexer',
    'NodoTrie',
    'BusAsyncWriter',
    'WriterConIntento',
    'DatoConHistorico',
    'BufferCircular',
    'BusSnapshotDinamico',
    'SnapshotBuilder'
]
