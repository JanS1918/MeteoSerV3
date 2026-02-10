"""
Driver WiFi Real - Descubre dispositivos en red local usando mDNS/zeroconf
"""
import logging
import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf, ServiceInfo
import socket

logger = logging.getLogger(__name__)


@dataclass
class WiFiDeviceInfo:
    """Información completa de dispositivo WiFi/red"""
    hostname: str
    ip_address: str
    port: int
    service_type: str
    properties: Dict
    detected_at: datetime


class WiFiDriver:
    """Driver real para descubrimiento de dispositivos en red local"""
    
    # Servicios a monitorear
    MONITORED_SERVICES = [
        '_http._tcp.local.',
        '_mqtt._tcp.local.',
        '_homeassistant._tcp.local.',
        '_esphome._tcp.local.',
        '_tasmota._tcp.local.',
        '_shelly._tcp.local.',
        '_ecowitt._tcp.local.',
        '_weatherstation._tcp.local.',
    ]
    
    # Patrones de identificación
    DEVICE_PATTERNS = {
        'shelly': 'SHELLY_DEVICE',
        'tasmota': 'TASMOTA_DEVICE',
        'esphome': 'ESPHOME_DEVICE',
        'ecowitt': 'ECOWITT_WEATHER_STATION',
        'ws-': 'WEATHER_STATION',
        'sensor': 'GENERIC_SENSOR',
    }
    
    def __init__(self):
        self.detected_devices: Dict[str, WiFiDeviceInfo] = {}
        self.zeroconf: Optional[Zeroconf] = None
        self.browsers: List[ServiceBrowser] = []
        self._running = False
        self._new_devices: Set[str] = set()
        
    async def start(self):
        """Inicia el descubrimiento mDNS/zeroconf"""
        if self._running:
            return
            
        try:
            self._running = True
            self.zeroconf = Zeroconf()
            
            # Crear browsers para cada servicio
            for service_type in self.MONITORED_SERVICES:
                browser = ServiceBrowser(
                    self.zeroconf,
                    service_type,
                    handlers=[self._on_service_state_change]
                )
                self.browsers.append(browser)
                
            logger.info(f"🌐 WiFi/mDNS: Monitoreando {len(self.MONITORED_SERVICES)} servicios")
            
        except Exception as e:
            logger.error(f"Error iniciando WiFi driver: {e}")
            self._running = False
    
    async def stop(self):
        """Detiene el descubrimiento"""
        if not self._running:
            return
            
        self._running = False
        
        # Cerrar browsers
        for browser in self.browsers:
            try:
                browser.cancel()
            except:
                pass
        self.browsers.clear()
        
        # Cerrar zeroconf
        if self.zeroconf:
            try:
                self.zeroconf.close()
            except:
                pass
            self.zeroconf = None
            
        logger.info("🌐 WiFi/mDNS detenido")
    
    def _on_service_state_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange
    ):
        """Callback cuando cambia estado de un servicio"""
        try:
            if state_change is ServiceStateChange.Added:
                asyncio.create_task(self._handle_service_added(zeroconf, service_type, name))
            elif state_change is ServiceStateChange.Removed:
                self._handle_service_removed(name)
        except Exception as e:
            logger.error(f"Error en callback de servicio: {e}")
    
    async def _handle_service_added(self, zeroconf: Zeroconf, service_type: str, name: str):
        """Procesa un nuevo servicio descubierto"""
        try:
            info = zeroconf.get_service_info(service_type, name, timeout=3000)
            
            if not info:
                return
            
            # Extraer información
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            if not addresses:
                return
                
            ip_address = addresses[0]
            port = info.port
            hostname = info.server.rstrip('.')
            
            # Propiedades del servicio
            properties = {}
            if info.properties:
                for key, value in info.properties.items():
                    try:
                        properties[key.decode('utf-8')] = value.decode('utf-8')
                    except:
                        properties[key] = value
            
            device_id = f"{hostname}:{ip_address}"
            
            device_info = WiFiDeviceInfo(
                hostname=hostname,
                ip_address=ip_address,
                port=port,
                service_type=service_type,
                properties=properties,
                detected_at=datetime.now()
            )
            
            # Guardar y notificar
            self.detected_devices[device_id] = device_info
            self._new_devices.add(device_id)
            
            sensor_type = self.identify_device(device_info)
            logger.info(
                f"🌐 WiFi: {hostname} | "
                f"{ip_address}:{port} | "
                f"{service_type} | {sensor_type}"
            )
            
        except Exception as e:
            logger.debug(f"Error procesando servicio {name}: {e}")
    
    def _handle_service_removed(self, name: str):
        """Procesa un servicio que desaparece"""
        # Por ahora solo log, podríamos marcar como offline
        logger.debug(f"🌐 Servicio removido: {name}")
    
    def identify_device(self, device: WiFiDeviceInfo) -> str:
        """Identifica tipo de dispositivo por hostname y propiedades"""
        hostname_lower = device.hostname.lower()
        
        # Por hostname
        for pattern, device_type in self.DEVICE_PATTERNS.items():
            if pattern in hostname_lower:
                return device_type
        
        # Por propiedades
        props_str = str(device.properties).lower()
        if 'shelly' in props_str:
            return 'SHELLY_DEVICE'
        if 'tasmota' in props_str:
            return 'TASMOTA_DEVICE'
        if 'weather' in props_str or 'meteo' in props_str:
            return 'WEATHER_STATION'
        
        # Por tipo de servicio
        service_lower = device.service_type.lower()
        if 'weather' in service_lower:
            return 'WEATHER_STATION'
        if 'mqtt' in service_lower:
            return 'MQTT_DEVICE'
        
        return 'UNKNOWN_NETWORK_DEVICE'
    
    async def scan_network(self, subnet: str = None) -> List[WiFiDeviceInfo]:
        """Escaneo activo de red (opcional, complementa mDNS)"""
        # Por ahora solo retorna los descubiertos por mDNS
        # Se podría implementar escaneo ARP/ICMP aquí
        return self.get_devices()
    
    async def test_connection(self, ip: str, port: int, timeout: float = 2.0) -> bool:
        """Testea conexión TCP a un dispositivo"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    async def http_request(
        self,
        ip: str,
        port: int = 80,
        path: str = '/',
        method: str = 'GET',
        timeout: float = 5.0
    ) -> Optional[str]:
        """Realiza petición HTTP simple"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )
            
            # Enviar request
            request = f"{method} {path} HTTP/1.1\r\nHost: {ip}\r\nConnection: close\r\n\r\n"
            writer.write(request.encode())
            await writer.drain()
            
            # Leer respuesta
            response = await asyncio.wait_for(
                reader.read(8192),
                timeout=timeout
            )
            
            writer.close()
            await writer.wait_closed()
            
            return response.decode('utf-8', errors='ignore')
            
        except Exception as e:
            logger.debug(f"Error en HTTP request a {ip}:{port}: {e}")
            return None
    
    def get_devices(self) -> List[WiFiDeviceInfo]:
        """Retorna lista de dispositivos detectados"""
        return list(self.detected_devices.values())
    
    def get_new_devices(self) -> List[WiFiDeviceInfo]:
        """Retorna dispositivos nuevos desde último check"""
        new = [self.detected_devices[dev_id] for dev_id in self._new_devices 
               if dev_id in self.detected_devices]
        self._new_devices.clear()
        return new
    
    async def cleanup(self):
        """Limpia recursos"""
        await self.stop()
