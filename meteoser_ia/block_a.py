from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
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

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILENAME = "sensor_registry.json"

ECOWITT_TYPE_MAP = {
    "WH57": SensorType.ECOWITT_WH57,
    "WH65": SensorType.ECOWITT_WH65,
    "WH32": SensorType.ECOWITT_WH32,
    "WH40": SensorType.ECOWITT_WH40,
    "WH45": SensorType.ECOWITT_WH45,
    "WH41": SensorType.ECOWITT_WH41,
    "WH43": SensorType.ECOWITT_WH43,
    "WH51": SensorType.ECOWITT_WH51,
}

TABLET_CAPABILITY_MAP = {
    "presencia": SensorType.TABLET_PROXIMITY,
    "luz_int": SensorType.TABLET_LIGHT,
    "ruido_int": SensorType.TABLET_MICROPHONE,
    "temp_int": SensorType.TABLET_TEMPERATURE,
    "hum_int": SensorType.TABLET_HUMIDITY,
}

CAPABILITY_KEYS = {
    "temp_ext": ["temp_ext", "temperature", "temp", "tempf", "outdoor_temp", "temperatura"],
    "hum_ext": ["humedad", "humidity", "hum", "humedad_relativa", "rh"],
    "viento": ["viento", "wind", "wind_speed", "wind_kph", "wind_mph", "velocidad_viento"],
    "lluvia": ["lluvia", "rain", "rain_rate", "precip", "precip_rate"],
    "radiacion": ["radiacion", "radiation", "solar_radiation"],
    "uv": ["uv", "uv_index"],
    "presion": ["presion", "pressure", "barometer", "presion_barometrica", "pressure_inhg"],
    "rayos": ["rayos", "lightning", "lightning_distance", "lightning_count"],
    "hum_suelo": ["hum_suelo", "soil_moisture", "soil"],
    "pm25_int": ["pm25", "pm2_5", "pm25_int"],
    "co2_int": ["co2", "co2_int"],
    "wbgt_real": ["wbgt", "wbgt_real"],
    "temp_int": ["temp_int", "temperature_in", "temp_in", "temperatura_interior"],
    "hum_int": ["hum_int", "humidity_in", "humedad_interior"],
    "presencia": ["presencia", "presence", "ocupacion"],
    "luz_int": ["luz", "light", "lux"],
    "ruido_int": ["ruido", "noise", "db"],
}


def _load_sensor_registry() -> Dict[str, List[Dict[str, Any]]]:
    registry_path = PROJECT_ROOT / REGISTRY_FILENAME
    if registry_path.exists():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            return data.get("sensors", {}) if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning(f"No se pudo leer {registry_path}: {e}")
    try:
        from core.integration.integration_manager import SensorIntegrationManager
        manager = SensorIntegrationManager(str(PROJECT_ROOT))
        return manager.registry.sensors
    except Exception as e:
        logger.warning(f"No se pudo cargar registro desde integración: {e}")
    return {}


def _infer_caps_from_type(sensor_type: str) -> List[str]:
    mapping = {
        "WH65": ["temp_ext", "hum_ext", "viento", "lluvia", "radiacion", "uv", "presion"],
        "WH57": ["rayos"],
        "WH51": ["hum_suelo"],
        "WH32": ["temp_int", "hum_int"],
        "WH43": ["pm25_int"],
        "ICASA_CO2": ["co2_int"],
        "WN38": ["wbgt_real"],
        "TABLET": ["presencia", "luz_int", "ruido_int", "temp_int", "hum_int"],
    }
    return mapping.get(sensor_type, [])


def detect_tablet_sensors() -> List[SensorMetadata]:
    logger.info("Detectando sensores de la tablet...")
    registry = _load_sensor_registry()
    sensors = []
    for entry in registry.get("TABLET", []):
        base_id = str(entry.get("id", "tablet"))
        caps = _infer_caps_from_type("TABLET")
        for cap in caps:
            s_type = TABLET_CAPABILITY_MAP.get(cap, SensorType.TABLET_PROXIMITY)
            sid = f"{base_id}_{cap}"
            sensors.append(SensorMetadata(
                id=sid,
                type=s_type,
                name=f"Tablet {cap}",
                description=f"Sensor tablet para {cap}",
                is_internal=False,
                is_virtual=False,
                capabilities={"capabilities": [cap], "source": "tablet"},
            ))
    return sensors


def detect_ecowitt_sensors() -> List[SensorMetadata]:
    logger.info("Detectando sensores Ecowitt...")
    registry = _load_sensor_registry()
    sensors: List[SensorMetadata] = []
    for sensor_type, entries in registry.items():
        if sensor_type not in ECOWITT_TYPE_MAP:
            continue
        for entry in entries:
            sid = str(entry.get("id", f"ecowitt_{sensor_type}"))
            caps = _infer_caps_from_type(sensor_type)
            sensors.append(SensorMetadata(
                id=sid,
                type=ECOWITT_TYPE_MAP[sensor_type],
                name=f"Ecowitt {sensor_type}",
                description=f"Sensor Ecowitt {sensor_type}",
                is_internal=False,
                is_virtual=False,
                capabilities={"capabilities": caps, "source": "ecowitt"},
            ))
    return sensors



def detect_external_devices() -> List[SensorMetadata]:
    logger.info("Detectando dispositivos externos (USB/BLE/APIs)...")
    registry = _load_sensor_registry()
    sensors: List[SensorMetadata] = []
    for sensor_type, entries in registry.items():
        if sensor_type in ECOWITT_TYPE_MAP or sensor_type == "TABLET":
            continue
        for entry in entries:
            sid = str(entry.get("id", f"ext_{sensor_type}"))
            metadata = entry.get("metadata", {}) if isinstance(entry, dict) else {}
            source = str(metadata.get("source", "external")).lower()
            if "ble" in source:
                s_type = SensorType.BLE_GENERIC
            elif "usb" in source or "serial" in source:
                s_type = SensorType.USB_GENERIC
            else:
                s_type = SensorType.VIRTUAL_EXTERNAL_API
            caps = _infer_caps_from_type(sensor_type)
            sensors.append(SensorMetadata(
                id=sid,
                type=s_type,
                name=f"Externo {sensor_type}",
                description=f"Dispositivo externo {sensor_type}",
                is_internal=False,
                is_virtual=False,
                capabilities={"capabilities": caps, "source": source or "external"},
            ))
    return sensors



def discover_all_sensors() -> SensorRegistrySnapshot:
    logger.info("Iniciando descubrimiento global de sensores (Bloque A)...")
    discovered: List[SensorMetadata] = []
    discovered.extend(detect_tablet_sensors())
    discovered.extend(detect_ecowitt_sensors())
    discovered.extend(detect_external_devices())
    for sensor in discovered:
        SENSOR_REGISTRY.register_sensor(sensor)
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
    values: Dict[str, Any] = {}
    try:
        from main_asgi import system as live_system
    except Exception:
        live_system = None

    sensores = getattr(live_system, "sensores", {}) if live_system else {}
    derivados = getattr(live_system, "sensores_derivados", {}) if live_system else {}
    data = getattr(live_system, "data", {}) if live_system else {}
    try:
        indices = live_system.indices.obtener_todos() if live_system and live_system.indices else {}
    except Exception:
        indices = {}

    sources = [sensores, derivados, indices, data]

    def _get_value_by_keys(keys: List[str]) -> Optional[Any]:
        for key in keys:
            for src in sources:
                if key in src and src[key] is not None:
                    return src[key]
        return None

    type_map = {
        SensorType.ECOWITT_WH57: "WH57",
        SensorType.ECOWITT_WH65: "WH65",
        SensorType.ECOWITT_WH32: "WH32",
        SensorType.ECOWITT_WH40: "WH40",
        SensorType.ECOWITT_WH45: "WH45",
        SensorType.ECOWITT_WH41: "WH41",
        SensorType.ECOWITT_WH43: "WH43",
        SensorType.ECOWITT_WH51: "WH51",
        SensorType.TABLET_TEMPERATURE: "TABLET",
        SensorType.TABLET_HUMIDITY: "TABLET",
        SensorType.TABLET_LIGHT: "TABLET",
        SensorType.TABLET_PROXIMITY: "TABLET",
        SensorType.TABLET_MICROPHONE: "TABLET",
    }

    caps = metadata.capabilities.get("capabilities", []) if isinstance(metadata.capabilities, dict) else []
    if not caps:
        caps = _infer_caps_from_type(type_map.get(metadata.type, ""))

    for cap in caps:
        keys = CAPABILITY_KEYS.get(cap, [])
        val = _get_value_by_keys(keys)
        if val is not None:
            values[cap] = val

    if not values:
        direct = _get_value_by_keys([metadata.id, metadata.name])
        if direct is not None:
            values[metadata.id] = direct

    return values


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
    logger.info("SMOKE TEST Bloque A: descubrimiento y lectura básica")
    snapshot = discover_all_sensors()
    for sensor in list(snapshot.sensors.values())[:5]:
        reading = read_sensor(sensor.id)
        logger.info(f"Sensor {sensor.id} lectura: {reading.values if reading else None}")

