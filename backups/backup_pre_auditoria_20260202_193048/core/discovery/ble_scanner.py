"""
BLE Scanner: Detecta sensores Bluetooth Low Energy
Monitorea beacons y servicios BLE de sensores ambientales
"""

import logging
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BLEDevice:
    """Representa un dispositivo Bluetooth detectado"""
    address: str
    name: Optional[str] = None
    rssi: Optional[int] = None
    manufacturer_data: Optional[Dict] = None
    service_uuids: Optional[List[str]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'address': self.address,
            'name': self.name,
            'rssi': self.rssi,
            'manufacturer_data': self.manufacturer_data,
            'service_uuids': self.service_uuids,
            'timestamp': self.timestamp.isoformat()
        }


class BLEScanner:
    """Escanea y monitorea dispositivos Bluetooth Low Energy"""
    
    # Mapeo de UUIDs de sensores conocidos
    KNOWN_SENSORS = {
        '181A': 'ENVIRONMENTAL_SENSING',
        '181B': 'USER_DATA',
        '182A': 'HEART_RATE',
        '181F': 'BATTERY_SERVICE',
    }
    
    # Sensores específicos por nombre/prefix
    SENSOR_PATTERNS = {
        'MH370': 'MH370_HYGROMETER',
        'CGP3': 'CGP3_CO2_METER',
        'SHT': 'SHT_TEMP_HUMIDITY',
        'LYWSD': 'LYWSD_TEMP_HUMIDITY',
    }
    
    def __init__(self):
        self.detected_devices: Dict[str, BLEDevice] = {}
        self.lock = asyncio.Lock()
        self.is_scanning = False
        self.scanner = None
    
    async def _init_ble_scanner(self):
        """Inicializa el scanner BLE (bleak para multiplataforma)"""
        try:
            from bleak import BleakScanner
            self.scanner = BleakScanner
            return True
        except ImportError:
            logger.warning("bleak no está instalado. BLE no disponible.")
            return False
    
    async def scan_ble_devices(self, timeout: int = 5) -> List[BLEDevice]:
        """Escanea dispositivos BLE disponibles"""
        if not self.scanner:
            if not await self._init_ble_scanner():
                return []
        
        devices = []
        try:
            from bleak import BleakScanner
            scanner = BleakScanner()
            await scanner.start()
            await asyncio.sleep(timeout)
            await scanner.stop()
            
            for device, advertisement_data in scanner.discovered_devices_and_advertisement_data.items():
                ble_device = BLEDevice(
                    address=device.address,
                    name=device.name,
                    rssi=advertisement_data.rssi,
                    manufacturer_data=dict(advertisement_data.manufacturer_data) if advertisement_data.manufacturer_data else None,
                    service_uuids=list(advertisement_data.service_uuids) if advertisement_data.service_uuids else None
                )
                
                # Identificar tipo de sensor
                sensor_type = await self.identify_sensor_type(ble_device)
                if sensor_type:
                    ble_device.name = sensor_type
                
                devices.append(ble_device)
                logger.info(f"Detectado BLE: {ble_device.to_dict()}")
        
        except Exception as e:
            logger.error(f"Error escaneando BLE: {e}")
        
        return devices
    
    async def identify_sensor_type(self, device: BLEDevice) -> Optional[str]:
        """Identifica el tipo de sensor BLE"""
        if device.name:
            for pattern, sensor_type in self.SENSOR_PATTERNS.items():
                if pattern.upper() in device.name.upper():
                    return sensor_type
        
        if device.service_uuids:
            for uuid in device.service_uuids:
                if uuid.startswith('0000181'):
                    return 'ENVIRONMENTAL_SENSOR'
        
        return None
    
    async def continuous_scan(self, interval: int = 10):
        """Escanea continuamente dispositivos BLE"""
        if not await self._init_ble_scanner():
            logger.error("No se pudo inicializar scanner BLE")
            return
        
        self.is_scanning = True
        while self.is_scanning:
            try:
                devices = await self.scan_ble_devices(timeout=8)
                
                async with self.lock:
                    for device in devices:
                        # Solo agregar si es sensor conocido
                        if device.name and any(pattern in device.name.upper() for pattern in self.SENSOR_PATTERNS):
                            self.detected_devices[device.address] = device
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error en continuous_scan BLE: {e}")
                await asyncio.sleep(interval)
    
    async def get_detected_devices(self) -> List[BLEDevice]:
        """Retorna los dispositivos BLE detectados"""
        async with self.lock:
            return list(self.detected_devices.values())
    
    def stop_scanning(self):
        """Detiene el escaneo continuo"""
        self.is_scanning = False
