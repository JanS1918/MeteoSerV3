"""
USB/Serial Scanner: Detecta sensores conectados por cable
Vigila puertos COM/USB del PC y presencias de UART/I2C
"""

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import subprocess
import re

logger = logging.getLogger(__name__)


@dataclass
class USBDevice:
    """Representa un dispositivo USB detectado"""
    port: str
    manufacturer: Optional[str] = None
    product: Optional[str] = None
    serial_number: Optional[str] = None
    vid: Optional[str] = None
    pid: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'port': self.port,
            'manufacturer': self.manufacturer,
            'product': self.product,
            'serial_number': self.serial_number,
            'vid': self.vid,
            'pid': self.pid,
            'timestamp': self.timestamp.isoformat()
        }


class USBScanner:
    """Escanea y monitorea puertos USB/Serial del sistema"""
    
    # Mapeo de VID:PID a tipos de sensores conocidos
    KNOWN_SENSORS = {
        '10C4:EA60': 'SGP30_CO2_SENSOR',  # Silicon Labs
        '1546:01A7': 'MH_Z19_CO2',  # MH-Z19 CO2
        '0403:6001': 'FTDI_SERIAL',  # FTDI (muchos sensores)
        '1A86:7523': 'CH340_SERIAL',  # CH340 (sensores baratos)
        '10C4:EA80': 'CP2102_SERIAL',  # CP2102 (Zigbee, etc)
    }
    
    def __init__(self):
        self.detected_devices: Dict[str, USBDevice] = {}
        self.lock = asyncio.Lock()
        self.is_scanning = False
    
    async def scan_usb_devices(self) -> List[USBDevice]:
        """Escanea puertos USB/COM disponibles"""
        try:
            if self._is_windows():
                return await self._scan_windows()
            elif self._is_linux():
                return await self._scan_linux()
            elif self._is_macos():
                return await self._scan_macos()
        except Exception as e:
            logger.error(f"Error escaneando USB: {e}")
        return []
    
    def _is_windows(self) -> bool:
        import platform
        return platform.system() == 'Windows'
    
    def _is_linux(self) -> bool:
        import platform
        return platform.system() == 'Linux'
    
    def _is_macos(self) -> bool:
        import platform
        return platform.system() == 'Darwin'
    
    async def _scan_windows(self) -> List[USBDevice]:
        """Escanea puertos COM en Windows usando WMI"""
        devices = []
        try:
            # Usar powershell para listar puertos COM
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', 
                 'Get-WmiObject Win32_SerialPort | Select-Object Name,Description,Manufacturer,PNPDeviceID'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[2:]:  # Skip headers
                    if line.strip():
                        parts = [p.strip() for p in line.split(' ', 3)]
                        if len(parts) >= 1:
                            port = parts[0]
                            desc = parts[1] if len(parts) > 1 else ""
                            manuf = parts[2] if len(parts) > 2 else ""
                            pnp = parts[3] if len(parts) > 3 else ""
                            
                            # Extraer VID:PID del PNP ID
                            vid_pid = self._extract_vid_pid(pnp)
                            
                            device = USBDevice(
                                port=port,
                                manufacturer=manuf,
                                product=desc,
                                vid=vid_pid[0] if vid_pid else None,
                                pid=vid_pid[1] if vid_pid else None
                            )
                            devices.append(device)
                            logger.info(f"Detectado USB: {device.to_dict()}")
        except Exception as e:
            logger.error(f"Error en _scan_windows: {e}")
        
        return devices
    
    async def _scan_linux(self) -> List[USBDevice]:
        """Escanea /dev/ttyUSB* y /dev/ttyACM* en Linux"""
        devices = []
        import glob
        
        for pattern in ['/dev/ttyUSB*', '/dev/ttyACM*']:
            for port in glob.glob(pattern):
                device = USBDevice(port=port)
                devices.append(device)
                logger.info(f"Detectado puerto Linux: {port}")
        
        return devices
    
    async def _scan_macos(self) -> List[USBDevice]:
        """Escanea /dev/tty.usb* en macOS"""
        devices = []
        import glob
        
        for pattern in ['/dev/tty.usb*', '/dev/cu.usb*']:
            for port in glob.glob(pattern):
                device = USBDevice(port=port)
                devices.append(device)
                logger.info(f"Detectado puerto macOS: {port}")
        
        return devices
    
    def _extract_vid_pid(self, pnp_id: str) -> tuple:
        """Extrae VID y PID del PnP Device ID"""
        match = re.search(r'VID_([0-9A-Fa-f]+).*PID_([0-9A-Fa-f]+)', pnp_id)
        if match:
            return (match.group(1).upper(), match.group(2).upper())
        return (None, None)
    
    async def identify_sensor_type(self, device: USBDevice) -> Optional[str]:
        """Identifica el tipo de sensor por VID:PID"""
        if device.vid and device.pid:
            vidpid = f"{device.vid}:{device.pid}"
            sensor_type = self.KNOWN_SENSORS.get(vidpid)
            if sensor_type:
                return sensor_type
        
        # Intentar inferir por manufacturer/product
        if device.manufacturer:
            if 'MH-Z19' in device.product or 'MH-Z19' in device.manufacturer:
                return 'MH_Z19_CO2'
            elif 'SGP30' in device.product:
                return 'SGP30_CO2_SENSOR'
        
        return None
    
    async def continuous_scan(self, interval: int = 5):
        """Escanea continuamente los puertos USB"""
        self.is_scanning = True
        while self.is_scanning:
            try:
                async with self.lock:
                    devices = await self.scan_usb_devices()
                    
                    # Actualizar detected_devices
                    for device in devices:
                        sensor_type = await self.identify_sensor_type(device)
                        if sensor_type:
                            device.product = sensor_type
                        self.detected_devices[device.port] = device
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error en continuous_scan: {e}")
                await asyncio.sleep(interval)
    
    async def get_detected_devices(self) -> List[USBDevice]:
        """Retorna los dispositivos detectados"""
        async with self.lock:
            return list(self.detected_devices.values())
    
    def stop_scanning(self):
        """Detiene el escaneo continuo"""
        self.is_scanning = False
