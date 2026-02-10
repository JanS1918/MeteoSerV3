"""
Driver USB Real - Conecta con hardware USB/Serial usando pyusb y pyserial
"""
import logging
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)


@dataclass
class USBDeviceInfo:
    """Información completa de dispositivo USB"""
    port: str
    vid: int
    pid: int
    manufacturer: Optional[str]
    product: Optional[str]
    serial_number: Optional[str]
    description: str
    detected_at: datetime


class USBDriver:
    """Driver real para detección y comunicación USB/Serial"""
    
    # Base de datos de sensores conocidos VID:PID
    KNOWN_DEVICES = {
        (0x10C4, 0xEA60): {'name': 'SGP30_CO2', 'baudrate': 9600},
        (0x1546, 0x01A7): {'name': 'MH_Z19_CO2', 'baudrate': 9600},
        (0x0403, 0x6001): {'name': 'FTDI_GENERIC', 'baudrate': 115200},
        (0x1A86, 0x7523): {'name': 'CH340_GENERIC', 'baudrate': 9600},
        (0x10C4, 0xEA80): {'name': 'CP2102_GENERIC', 'baudrate': 115200},
        (0x2341, 0x0043): {'name': 'ARDUINO_UNO', 'baudrate': 9600},
        (0x2341, 0x0001): {'name': 'ARDUINO_MEGA', 'baudrate': 9600},
    }
    
    def __init__(self):
        self.detected_devices: Dict[str, USBDeviceInfo] = {}
        self.active_connections: Dict[str, serial.Serial] = {}
        
    async def scan(self) -> List[USBDeviceInfo]:
        """Escanea puertos USB disponibles"""
        devices = []
        try:
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                device_id = port.device
                
                device_info = USBDeviceInfo(
                    port=port.device,
                    vid=port.vid or 0,
                    pid=port.pid or 0,
                    manufacturer=port.manufacturer,
                    product=port.product,
                    serial_number=port.serial_number,
                    description=port.description,
                    detected_at=datetime.now()
                )
                
                # Actualizar cache
                self.detected_devices[device_id] = device_info
                devices.append(device_info)
                
                # Log con identificación
                sensor_info = self.identify_device(device_info)
                logger.info(
                    f"🔌 USB: {port.device} | "
                    f"VID:PID={hex(port.vid or 0)}:{hex(port.pid or 0)} | "
                    f"{sensor_info['name']} | {port.description}"
                )
                
        except Exception as e:
            logger.error(f"Error escaneando USB: {e}")
            
        return devices
    
    def identify_device(self, device: USBDeviceInfo) -> Dict:
        """Identifica tipo de sensor por VID:PID"""
        vid_pid = (device.vid, device.pid)
        
        if vid_pid in self.KNOWN_DEVICES:
            return self.KNOWN_DEVICES[vid_pid]
        
        # Intentar por nombre/descripción
        desc_lower = device.description.lower()
        if 'arduino' in desc_lower:
            return {'name': 'ARDUINO', 'baudrate': 9600}
        if 'cp210' in desc_lower:
            return {'name': 'CP210X', 'baudrate': 115200}
        if 'ftdi' in desc_lower:
            return {'name': 'FTDI', 'baudrate': 115200}
        if 'ch340' in desc_lower or 'ch341' in desc_lower:
            return {'name': 'CH34X', 'baudrate': 9600}
            
        return {'name': 'UNKNOWN', 'baudrate': 9600}
    
    async def connect(self, port: str, baudrate: int = 9600, timeout: float = 1.0) -> bool:
        """Conecta a un puerto serial"""
        try:
            if port in self.active_connections:
                logger.warning(f"Puerto {port} ya está conectado")
                return True
                
            conn = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=timeout
            )
            
            self.active_connections[port] = conn
            logger.info(f"[OK] Conectado a {port} @ {baudrate} baud")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a {port}: {e}")
            return False
    
    async def disconnect(self, port: str):
        """Desconecta un puerto"""
        if port in self.active_connections:
            try:
                self.active_connections[port].close()
                del self.active_connections[port]
                logger.info(f"🔌 Desconectado de {port}")
            except Exception as e:
                logger.error(f"Error desconectando {port}: {e}")
    
    async def read(self, port: str, size: int = 1024) -> Optional[bytes]:
        """Lee datos de un puerto"""
        if port not in self.active_connections:
            logger.error(f"Puerto {port} no está conectado")
            return None
            
        try:
            conn = self.active_connections[port]
            if conn.in_waiting > 0:
                return conn.read(min(conn.in_waiting, size))
            return None
        except Exception as e:
            logger.error(f"Error leyendo de {port}: {e}")
            return None
    
    async def write(self, port: str, data: bytes) -> bool:
        """Escribe datos a un puerto"""
        if port not in self.active_connections:
            logger.error(f"Puerto {port} no está conectado")
            return False
            
        try:
            conn = self.active_connections[port]
            conn.write(data)
            return True
        except Exception as e:
            logger.error(f"Error escribiendo a {port}: {e}")
            return False
    
    async def query_sensor(self, port: str, command: bytes, wait_ms: int = 500) -> Optional[bytes]:
        """Envía comando y espera respuesta"""
        if await self.write(port, command):
            await asyncio.sleep(wait_ms / 1000.0)
            return await self.read(port)
        return None
    
    def get_devices(self) -> List[USBDeviceInfo]:
        """Retorna lista de dispositivos detectados"""
        return list(self.detected_devices.values())
    
    async def cleanup(self):
        """Limpia todas las conexiones"""
        for port in list(self.active_connections.keys()):
            await self.disconnect(port)
