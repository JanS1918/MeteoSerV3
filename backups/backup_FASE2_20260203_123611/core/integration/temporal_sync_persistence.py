# ============================================================
# SINCRONÍA TEMPORAL Y PERSISTENCIA DE EMERGENCIA
# Archivo: core/integration/temporal_sync_persistence.py
# ============================================================
"""
Módulo de Sincronía Temporal y Persistencia de Emergencia.

OBJETIVO:
- Usar dateutc del paquete Ecowitt para timestamping preciso
- Implementar last_valid_value fallback en lugar de 0.0
- Proporcionar sincronización para motores físicos

ARQUITECTURA:
1. parse_dateutc(): Convertir string dateutc de Ecowitt a datetime con tz
2. get_last_valid_sensor(): Buscar último valor válido de la DB
3. apply_temporal_sync(): Inyectar timestamp sincronizado en contexto
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def parse_dateutc(dateutc_str: str) -> Optional[datetime]:
    """
    Parsear string dateutc de Ecowitt (formato: 'YYYY-MM-DD HH:MM:SS').
    Retorna datetime con timezone UTC.
    
    Args:
        dateutc_str: String del paquete Ecowitt (ej: "2026-02-01 12:30:45")
    
    Returns:
        datetime con tz=UTC, o None si falla
    """
    if not dateutc_str:
        return None
    try:
        # Formato estándar de Ecowitt: 'YYYY-MM-DD HH:MM:SS'
        dt = datetime.strptime(str(dateutc_str).strip(), "%Y-%m-%d %H:%M:%S")
        # Asumir UTC (Ecowitt típicamente envía UTC)
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return dt_utc
    except Exception as e:
        logger.warning(f"No se pudo parsear dateutc '{dateutc_str}': {e}")
        return None


def get_last_valid_sensor(
    sensor_id: str,
    system_obj: Any,
    fallback_value: float = None
) -> Tuple[Optional[float], str]:
    """
    Obtener el último valor válido de un sensor desde sistema.
    
    Búsqueda jerárquica:
    1. sensores activos en memory
    2. last_valid_value en metadata (si existe)
    3. fallback_value (si se proporciona)
    4. None (sin valor)
    
    Args:
        sensor_id: Identificador del sensor (ej: "humedad_interior")
        system_obj: Objeto sistema con .sensores y .sensores_metadata
        fallback_value: Valor fallback explícito (usar en lugar de 0.0)
    
    Returns:
        Tupla (valor_válido, fuente_descripción)
    """
    try:
        # 1. Intentar valor actual en memoria
        if hasattr(system_obj, 'sensores') and sensor_id in system_obj.sensores:
            val = system_obj.sensores[sensor_id]
            if val is not None:
                return float(val), "MEMORY_ACTIVE"
        
        # 2. Intentar last_valid_value desde metadata
        if hasattr(system_obj, 'sensores_metadata') and sensor_id in system_obj.sensores_metadata:
            meta = system_obj.sensores_metadata[sensor_id]
            if isinstance(meta, dict):
                last_valid = meta.get('last_valid_value')
                if last_valid is not None:
                    return float(last_valid), "METADATA_PERSISTENT"
        
        # 3. Fallback explícito (NO usar 0.0 a menos que sea intencional)
        if fallback_value is not None:
            return float(fallback_value), "EXPLICIT_FALLBACK"
        
        # 4. Sin valor disponible
        logger.warning(f"[PERSISTENCIA] Sensor {sensor_id} sin valor válido disponible")
        return None, "NO_VALUE_AVAILABLE"
    
    except Exception as e:
        logger.exception(f"Error obteniendo last_valid_sensor para {sensor_id}: {e}")
        return fallback_value, "ERROR_FALLBACK"


def store_last_valid_value(
    sensor_id: str,
    value: float,
    system_obj: Any
) -> bool:
    """
    Almacenar último valor válido en metadata para persistencia de emergencia.
    
    Args:
        sensor_id: Identificador del sensor
        value: Valor válido a guardar
        system_obj: Objeto sistema
    
    Returns:
        True si se guardó correctamente, False si error
    """
    try:
        if not hasattr(system_obj, 'sensores_metadata'):
            return False
        
        if sensor_id not in system_obj.sensores_metadata:
            system_obj.sensores_metadata[sensor_id] = {}
        
        system_obj.sensores_metadata[sensor_id]['last_valid_value'] = float(value)
        system_obj.sensores_metadata[sensor_id]['last_valid_timestamp'] = datetime.now(timezone.utc).isoformat()
        
        logger.debug(f"[PERSISTENCIA] Guardado last_valid_value={value} para {sensor_id}")
        return True
    
    except Exception as e:
        logger.exception(f"Error guardando last_valid_value para {sensor_id}: {e}")
        return False


def apply_temporal_sync(
    data_dict: Dict[str, Any],
    system_obj: Any
) -> Dict[str, Any]:
    """
    Inyectar timestamp sincronizado desde dateutc en el diccionario de datos.
    
    Modifica data_dict in-place para añadir:
    - _dateutc_parsed: datetime parseada
    - _dateutc_iso: ISO string UTC
    - _timestamp_ms: timestamp en milisegundos
    
    Args:
        data_dict: Diccionario de datos Ecowitt
        system_obj: Objeto sistema (para logs)
    
    Returns:
        Diccionario actualizado con info de sincronía temporal
    """
    try:
        dateutc_str = data_dict.get('dateutc')
        if dateutc_str:
            dt_utc = parse_dateutc(dateutc_str)
            if dt_utc:
                data_dict['_dateutc_parsed'] = dt_utc
                data_dict['_dateutc_iso'] = dt_utc.isoformat()
                data_dict['_timestamp_ms'] = int(dt_utc.timestamp() * 1000)
                logger.info(f"[SYNC TEMPORAL] dateutc={dateutc_str} parseado correctamente")
                return data_dict
        
        # Fallback: usar hora actual
        dt_now = datetime.now(timezone.utc)
        data_dict['_dateutc_parsed'] = dt_now
        data_dict['_dateutc_iso'] = dt_now.isoformat()
        data_dict['_timestamp_ms'] = int(dt_now.timestamp() * 1000)
        logger.warning(f"[SYNC TEMPORAL] Usando hora del servidor (dateutc no disponible)")
        return data_dict
    
    except Exception as e:
        logger.exception(f"Error en apply_temporal_sync: {e}")
        return data_dict


def reset_monin_obukhov_on_pressure_change(
    pressure_status: str,
    system_obj: Any
) -> bool:
    """
    Resetear estado de Monin-Obukhov cuando P pasa de False → True.
    
    Esto limpia los estados de estabilidad anteriores para que el motor
    pueda recalibrar con la nueva presión validada.
    
    Args:
        pressure_status: "OK" (True) o "ERROR"/"DEGRADED" (False)
        system_obj: Objeto sistema con acceso a engines
    
    Returns:
        True si se reseteó correctamente
    """
    try:
        # Obtener estado anterior de presión desde metadata
        prev_pressure_status = system_obj.sensores_metadata.get(
            '__INTERNAL__', {}
        ).get('prev_pressure_status', 'ERROR')
        
        # Transición False → True
        if prev_pressure_status != 'OK' and pressure_status == 'OK':
            logger.info("[RESET MONIN-OBUKHOV] Presión pasó de falta a OK. Reseteando estados.")
            
            # Resetear estados del motor si existe
            if hasattr(system_obj, 'indices_engine'):
                # TODO: Implementar reset específico si es necesario
                logger.debug("[RESET] Estabilidad atmosférica reseteable")
            
            # Guardar estado actual para próxima comparación
            if '__INTERNAL__' not in system_obj.sensores_metadata:
                system_obj.sensores_metadata['__INTERNAL__'] = {}
            system_obj.sensores_metadata['__INTERNAL__']['prev_pressure_status'] = 'OK'
            
            return True
        else:
            # Guardar estado para próxima comparación
            if '__INTERNAL__' not in system_obj.sensores_metadata:
                system_obj.sensores_metadata['__INTERNAL__'] = {}
            system_obj.sensores_metadata['__INTERNAL__']['prev_pressure_status'] = pressure_status
        
        return False
    
    except Exception as e:
        logger.exception(f"Error en reset_monin_obukhov_on_pressure_change: {e}")
        return False
