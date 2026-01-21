from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ExternalIntegrationMode(str, enum.Enum):
    MOCK = "mock"
    LIVE = "live"


EXTERNAL_INTEGRATION_MODE: ExternalIntegrationMode = ExternalIntegrationMode.LIVE

logger = logging.getLogger("meteoser_ia.block_a")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [BLOQUE A] [%(levelname)s] %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)


class SensorType(str, enum.Enum):
    TABLET_ACCELEROMETER = "tablet_accelerometer"
    TABLET_GYROSCOPE = "tablet_gyroscope"
    TABLET_LIGHT = "tablet_light"
    TABLET_PROXIMITY = "tablet_proximity"
    TABLET_BAROMETER = "tablet_barometer"
    TABLET_TEMPERATURE = "tablet_temperature"
    TABLET_HUMIDITY = "tablet_humidity"
    TABLET_GPS = "tablet_gps"
    TABLET_MICROPHONE = "tablet_microphone"
    TABLET_CAMERA = "tablet_camera"

    ECOWITT_WH57 = "ecowitt_wh57"
    ECOWITT_WH65 = "ecowitt_wh65"
    ECOWITT_WH32 = "ecowitt_wh32"
    ECOWITT_WH40 = "ecowitt_wh40"
    ECOWITT_WH45 = "ecowitt_wh45"
    ECOWITT_WH41 = "ecowitt_wh41"
    ECOWITT_WH43 = "ecowitt_wh43"
    ECOWITT_WH51 = "ecowitt_wh51"

    USB_GENERIC = "usb_generic"
    BLE_GENERIC = "ble_generic"
    VIRTUAL_EXTERNAL_API = "virtual_external_api"
    VIRTUAL_DERIVED = "virtual_derived"


@dataclass
class SensorMetadata:
    id: str
    type: SensorType
    name: str
    description: str
    is_internal: bool
    is_virtual: bool
    capabilities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SensorReading:
    sensor_id: str
    timestamp: float
    values: Dict[str, Any]
    valid: bool
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class SensorRegistrySnapshot:
    sensors: Dict[str, SensorMetadata] = field(default_factory=dict)


class SensorRegistry:
    def __init__(self) -> None:
        self._sensors: Dict[str, SensorMetadata] = {}

    def register_sensor(self, metadata: SensorMetadata) -> None:
        if metadata.id in self._sensors:
            logger.debug(f"Sensor ya registrado, actualizando: {metadata.id}")
        else:
            logger.info(f"Registrando nuevo sensor: {metadata.id} ({metadata.type})")
        self._sensors[metadata.id] = metadata

    def unregister_sensor(self, sensor_id: str) -> None:
        if sensor_id in self._sensors:
            logger.info(f"Eliminando sensor del registro IA: {sensor_id}")
            del self._sensors[sensor_id]

    def get_sensor(self, sensor_id: str) -> Optional[SensorMetadata]:
        return self._sensors.get(sensor_id)

    def list_sensors(self) -> List[SensorMetadata]:
        return list(self._sensors.values())

    def snapshot(self) -> SensorRegistrySnapshot:
        return SensorRegistrySnapshot(sensors=dict(self._sensors))


SENSOR_REGISTRY = SensorRegistry()


def detect_tablet_sensors() -> List[SensorMetadata]:
    logger.info("Detectando sensores de la tablet...")
    # TODO: Implementar integración real
    logger.warning("Detección LIVE de sensores de tablet no implementada todavía.")
    return []


def detect_ecowitt_sensors() -> List[SensorMetadata]:
    logger.info("Detectando sensores Ecowitt...")
    # TODO: Implementar integración real
    logger.warning("Detección LIVE de sensores Ecowitt no implementada todavía.")
    return []


def detect_external_devices() -> List[SensorMetadata]:
    logger.info("Detectando dispositivos externos (USB/BLE/APIs)...")
    # TODO: Implementar integración real
    logger.warning("Detección LIVE de dispositivos externos no implementada todavía.")
    return []


def discover_all_sensors() -> SensorRegistrySnapshot:
    logger.info("Iniciando descubrimiento global de sensores (Bloque A)...")
    # TODO: Implementar descubrimiento real
    snapshot = SENSOR_REGISTRY.snapshot()
    logger.info(
        f"Descubrimiento completado. Sensores registrados: {len(snapshot.sensors)}"
    )
    return snapshot


def read_sensor(sensor_id: str) -> Optional[SensorReading]:
    metadata = SENSOR_REGISTRY.get_sensor(sensor_id)
    if metadata is None:
        logger.warning(f"Intento de lectura de sensor no registrado: {sensor_id}")
        return None

    timestamp = time.time()

    # Solo integración real
    values = _read_live_values_for_sensor(metadata)

    valid, errors = validate_sensor_reading(metadata, values)

    reading = SensorReading(
        sensor_id=metadata.id,
        timestamp=timestamp,
        values=values,
        valid=valid,
        validation_errors=errors,
    )

    if not valid:
        logger.warning(
            f"Lectura inválida para sensor {metadata.id}: {errors} (valores={values})"
        )
    else:
        logger.debug(f"Lectura válida para sensor {metadata.id}: {values}")

    return reading


def _read_live_values_for_sensor(metadata: SensorMetadata) -> Dict[str, Any]:
    logger.warning(
        f"Lectura LIVE no implementada para sensor {metadata.id} ({metadata.type}). "
        f"Se devolverán valores vacíos."
    )
    return {}


def validate_sensor_reading(
    metadata: SensorMetadata, values: Dict[str, Any]
) -> (bool, List[str]):
    errors: List[str] = []

    if not isinstance(values, dict):
        errors.append("Los valores del sensor no son un diccionario.")

    if metadata.type == SensorType.TABLET_LIGHT:
        lux = values.get("lux")
        if lux is None:
            errors.append("Falta el campo 'lux'.")
        elif not (0 <= lux <= 200000):
            errors.append(f"Valor de 'lux' fuera de rango: {lux}")

    if metadata.type == SensorType.ECOWITT_WH32:
        temp = values.get("temperature")
        hum = values.get("humidity")
        if temp is None:
            errors.append("Falta 'temperature'.")
        if hum is None:
            errors.append("Falta 'humidity'.")
        if temp is not None and not (-40 <= temp <= 80):
            errors.append(f"Temperatura fuera de rango: {temp}")
        if hum is not None and not (0 <= hum <= 100):
            errors.append(f"Humedad fuera de rango: {hum}")

    return (len(errors) == 0, errors)


def _run_smoke_test() -> None:
    # Eliminado: solo integración real
    pass
