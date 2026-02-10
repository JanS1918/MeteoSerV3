"""
mDNS/WiFi Scanner: Detecta dispositivos IoT en la red local
Descubre sensores Shelly, Tasmota, ESPHome y otros por mDNS/ZeroConf
"""

import logging
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class mDNSDevice:
    """Representa un dispositivo detectado por mDNS"""
    hostname: str
    ip_address: Optional[str] = None
    port: Optional[int] = None
    type_: Optional[str] = None
    properties: Optional[Dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'port': self.port,
            'type': self.type_,
            'properties': self.properties,
            'timestamp': self.timestamp.isoformat()
        }


class mDNSScanner:
    """Escanea y monitorea dispositivos IoT en WiFi por mDNS"""
    
    # Patrones de sensores IoT conocidos
    SENSOR_PATTERNS = {
        'shelly': 'SHELLY_DEVICE',
        'tasmota': 'TASMOTA_DEVICE',
        'esphome': 'ESPHOME_DEVICE',
        'co2': 'CO2_SENSOR',
        'humi': 'HUMIDITY_SENSOR',
        'temp': 'TEMPERATURE_SENSOR',
        'zigbee': 'ZIGBEE_BRIDGE',
        'mqtt': 'MQTT_BRIDGE',
    }
    
    def __init__(self):
        self.detected_devices: Dict[str, mDNSDevice] = {}
        self.lock = asyncio.Lock()
        self.is_scanning = False
        self.mdns_browser = None
    
    async def _init_mdns_scanner(self):
        """Inicializa el escáner mDNS (zeroconf/avahi)"""
        try:
            from zeroconf import ServiceBrowser, Zeroconf
            self.Zeroconf = Zeroconf
            self.ServiceBrowser = ServiceBrowser
            return True
        except ImportError:
            logger.warning("zeroconf no está instalado. mDNS no disponible.")
            return False
    
    async def scan_mdns_devices(self, timeout: int = 5, service_type: str = "_http._tcp.local.") -> List[mDNSDevice]:
        """Escanea dispositivos mDNS disponibles"""
        if not await self._init_mdns_scanner():
            return []
        
        devices = []
        try:
            from zeroconf import Zeroconf, ServiceBrowser
            
            class MDNSListener:
                def __init__(self):
                    self.services = []
                
                def add_service(self, zeroconf, service_type, name):
                    self.services.append(name)
                
                def update_service(self, zeroconf, service_type, name):
                    pass
                
                def remove_service(self, zeroconf, service_type, name):
                    pass
            
            listener = MDNSListener()
            zeroconf = Zeroconf()
            browser = ServiceBrowser(zeroconf, service_type, listener)
            
            await asyncio.sleep(timeout)
            
            for service_name in listener.services:
                device = mDNSDevice(
                    hostname=service_name.replace(f'.{service_type}', ''),
                    type_='HTTP_SERVICE'
                )
                
                # Identificar tipo de sensor
                sensor_type = await self.identify_sensor_type(device)
                if sensor_type:
                    device.type_ = sensor_type
                
                devices.append(device)
                logger.info(f"Detectado mDNS: {device.to_dict()}")
            
            zeroconf.close()
        
        except Exception as e:
            logger.error(f"Error escaneando mDNS: {e}")
        
        return devices
    
    async def identify_sensor_type(self, device: mDNSDevice) -> Optional[str]:
        """Identifica el tipo de sensor por nombre de host"""
        hostname_lower = device.hostname.lower()
        
        for pattern, sensor_type in self.SENSOR_PATTERNS.items():
            if pattern in hostname_lower:
                return sensor_type
        
        return None
    
    async def continuous_scan(self, interval: int = 15):
        """Escanea continuamente dispositivos mDNS"""
        if not await self._init_mdns_scanner():
            logger.error("No se pudo inicializar scanner mDNS")
            return
        
        self.is_scanning = True
        while self.is_scanning:
            try:
                devices = await self.scan_mdns_devices(timeout=10)
                
                async with self.lock:
                    for device in devices:
                        self.detected_devices[device.hostname] = device
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error en continuous_scan mDNS: {e}")
                await asyncio.sleep(interval)
    
    async def get_detected_devices(self) -> List[mDNSDevice]:
        """Retorna los dispositivos mDNS detectados"""
        async with self.lock:
            return list(self.detected_devices.values())
    
    def stop_scanning(self):
        """Detiene el escaneo continuo"""
        self.is_scanning = False
