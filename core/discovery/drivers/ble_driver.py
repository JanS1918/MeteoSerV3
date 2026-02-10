"""
Driver BLE Real - Conecta con dispositivos Bluetooth Low Energy usando bleak
"""
import logging
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

logger = logging.getLogger(__name__)


@dataclass
class BLEDeviceInfo:
    """Información completa de dispositivo BLE"""
    address: str
    name: Optional[str]
    rssi: int
    manufacturer_data: Dict
    service_uuids: List[str]
    detected_at: datetime


class BLEDriver:
    """Driver real para detección y comunicación BLE"""
    
    # UUIDs de servicios conocidos
    KNOWN_SERVICES = {
        '0000181a-0000-1000-8000-00805f9b34fb': 'ENVIRONMENTAL_SENSING',
        '0000181b-0000-1000-8000-00805f9b34fb': 'USER_DATA',
        '0000181f-0000-1000-8000-00805f9b34fb': 'BATTERY_SERVICE',
        '0000180f-0000-1000-8000-00805f9b34fb': 'BATTERY_SERVICE_SHORT',
        'ebe0ccb0-7a0a-4b0c-8a1a-6ff2997da3a6': 'XIAOMI_MIJIA',
    }
    
    # Patrones de nombre para sensores conocidos
    NAME_PATTERNS = {
        'LYWSD': 'XIAOMI_TEMP_HUMIDITY',
        'MHO-C401': 'XIAOMI_TEMP_HUMIDITY',
        'CGP3': 'QINGPING_CO2',
        'CGD1': 'QINGPING_TEMP_HUMIDITY',
        'SHT': 'SENSIRION_SENSOR',
        'ATC': 'ATC_THERMOMETER',
    }
    
    def __init__(self):
        self.detected_devices: Dict[str, BLEDeviceInfo] = {}
        self.active_clients: Dict[str, BleakClient] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        
    async def scan(self, timeout: float = 5.0) -> List[BLEDeviceInfo]:
        """Escanea dispositivos BLE disponibles"""
        # BLE DESHABILITADO permanentemente
        return []
    
    def identify_device(self, device: BLEDeviceInfo) -> str:
        """Identifica tipo de sensor por nombre y servicios"""
        # Por nombre
        if device.name:
            for pattern, sensor_type in self.NAME_PATTERNS.items():
                if pattern in device.name.upper():
                    return sensor_type
        
        # Por servicios UUID
        for uuid in device.service_uuids:
            uuid_lower = uuid.lower()
            if uuid_lower in self.KNOWN_SERVICES:
                return self.KNOWN_SERVICES[uuid_lower]
        
        return 'UNKNOWN_BLE_DEVICE'
    
    async def connect(self, address: str, timeout: float = 10.0) -> bool:
        """Conecta a un dispositivo BLE"""
        try:
            if address in self.active_clients:
                if self.active_clients[address].is_connected:
                    logger.warning(f"Ya conectado a {address}")
                    return True
                else:
                    # Cliente existe pero desconectado, eliminar
                    del self.active_clients[address]
            
            client = BleakClient(address, timeout=timeout)
            await client.connect()
            
            self.active_clients[address] = client
            logger.info(f"[OK] Conectado a BLE {address}")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a {address}: {e}")
            return False
    
    async def disconnect(self, address: str):
        """Desconecta de un dispositivo BLE"""
        if address in self.active_clients:
            try:
                await self.active_clients[address].disconnect()
                del self.active_clients[address]
                logger.info(f"📡 Desconectado de {address}")
            except Exception as e:
                logger.error(f"Error desconectando {address}: {e}")
    
    async def read_characteristic(self, address: str, characteristic_uuid: str) -> Optional[bytes]:
        """Lee una característica BLE"""
        if address not in self.active_clients:
            logger.error(f"No hay conexión con {address}")
            return None
            
        try:
            client = self.active_clients[address]
            data = await client.read_gatt_char(characteristic_uuid)
            return bytes(data)
        except Exception as e:
            logger.error(f"Error leyendo característica {characteristic_uuid}: {e}")
            return None
    
    async def write_characteristic(self, address: str, characteristic_uuid: str, data: bytes) -> bool:
        """Escribe una característica BLE"""
        if address not in self.active_clients:
            logger.error(f"No hay conexión con {address}")
            return False
            
        try:
            client = self.active_clients[address]
            await client.write_gatt_char(characteristic_uuid, data)
            return True
        except Exception as e:
            logger.error(f"Error escribiendo característica {characteristic_uuid}: {e}")
            return False
    
    async def enable_notifications(
        self,
        address: str,
        characteristic_uuid: str,
        callback: Callable[[int, bytearray], None]
    ) -> bool:
        """Habilita notificaciones de una característica"""
        if address not in self.active_clients:
            logger.error(f"No hay conexión con {address}")
            return False
            
        try:
            client = self.active_clients[address]
            await client.start_notify(characteristic_uuid, callback)
            self.notification_handlers[f"{address}:{characteristic_uuid}"] = callback
            logger.info(f"🔔 Notificaciones habilitadas en {address}:{characteristic_uuid}")
            return True
        except Exception as e:
            logger.error(f"Error habilitando notificaciones: {e}")
            return False
    
    async def disable_notifications(self, address: str, characteristic_uuid: str) -> bool:
        """Deshabilita notificaciones"""
        if address not in self.active_clients:
            return False
            
        try:
            client = self.active_clients[address]
            await client.stop_notify(characteristic_uuid)
            key = f"{address}:{characteristic_uuid}"
            if key in self.notification_handlers:
                del self.notification_handlers[key]
            logger.info(f"🔕 Notificaciones deshabilitadas en {address}:{characteristic_uuid}")
            return True
        except Exception as e:
            logger.error(f"Error deshabilitando notificaciones: {e}")
            return False
    
    async def get_services(self, address: str) -> Optional[List[str]]:
        """Lista servicios disponibles en un dispositivo"""
        if address not in self.active_clients:
            logger.error(f"No hay conexión con {address}")
            return None
            
        try:
            client = self.active_clients[address]
            services = []
            for service in client.services:
                services.append(str(service.uuid))
            return services
        except Exception as e:
            logger.error(f"Error listando servicios: {e}")
            return None
    
    def get_devices(self) -> List[BLEDeviceInfo]:
        """Retorna lista de dispositivos detectados"""
        return list(self.detected_devices.values())
    
    async def cleanup(self):
        """Limpia todas las conexiones"""
        for address in list(self.active_clients.keys()):
            await self.disconnect(address)
