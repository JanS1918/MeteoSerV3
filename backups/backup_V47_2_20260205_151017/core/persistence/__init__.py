"""
Módulo de PERSISTENCIA - Almacenamiento Histórico con InfluxDB
==============================================================

Sistema completo de persistencia con:
- InfluxDBManager: Cliente wrapper para InfluxDB 2.x
- ArchivadorSeriesTemporales: Archivado automático del Bus
- Consultas optimizadas con agregación/downsampling
"""

try:
    from core.persistence.influxdb_manager import (
        InfluxDBManager,
        INFLUXDB_AVAILABLE
    )
    from core.persistence.timeseries_archiver import (
        ArchivadorSeriesTemporales,
        obtener_archivador
    )
    PERSISTENCIA_DISPONIBLE = True
except ImportError:
    InfluxDBManager = None
    ArchivadorSeriesTemporales = None
    obtener_archivador = None
    INFLUXDB_AVAILABLE = False
    PERSISTENCIA_DISPONIBLE = False

__all__ = [
    'InfluxDBManager',
    'ArchivadorSeriesTemporales',
    'obtener_archivador',
    'INFLUXDB_AVAILABLE',
    'PERSISTENCIA_DISPONIBLE'
]
