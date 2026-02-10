import logging
"""
Radar Universal de Hardware - USB/Serial, BLE, WiFi - INTEGRACIÓN REAL
"""
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .drivers.usb_driver import USBDriver
from .drivers.ble_driver import BLEDriver
from .drivers.wifi_driver import WiFiDriver

logger = logging.getLogger(__name__)

@dataclass
class DetectedDevice:
    """Dispositivo detectado por el radar"""
    id: str
    name: str
    type: str  # 'usb', 'ble', 'wifi'
    address: str
    metadata: Dict
    detected_at: datetime

class UniversalHardwareScanner:
    """Escáner universal que detecta hardware por cualquier medio - DRIVERS REALES"""
    
    def __init__(self):
        self.devices: Dict[str, DetectedDevice] = {}
        self.scan_interval = 30  # segundos
        self._running = False
        self._task = None
        self.failures = {"usb": 0, "ble": 0, "wifi": 0}
        self.last_errors = {"usb": None, "ble": None, "wifi": None}
        self.last_scan_at = {"usb": None, "ble": None, "wifi": None}
        
        # Drivers reales
        self.usb_driver = USBDriver()
        self.ble_driver = BLEDriver()
        self.wifi_driver = WiFiDriver()
        
    async def start(self):
        """Inicia el radar de hardware con drivers reales"""
        if self._running:
            return
        self._running = True
        
        # Iniciar driver WiFi (mDNS continuo)
        await self.wifi_driver.start()
        
        self._task = asyncio.create_task(self._scan_loop())
        logger.info("🛸 Radar Universal ACTIVADO - Drivers reales USB/BLE/WiFi operativos")
        
    async def stop(self):
        """Detiene el radar y limpia drivers"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logging.exception("Silent except at 59 - revisar contexto")
        
        # Limpiar drivers
        await self.usb_driver.cleanup()
        await self.ble_driver.cleanup()
        await self.wifi_driver.cleanup()
                
    async def _scan_loop(self):
        """Bucle principal de escaneo"""
        while self._running:
            try:
                await self._scan_all_interfaces()
                await asyncio.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"Error en scan loop: {e}")
                await asyncio.sleep(5)
                
    async def _scan_all_interfaces(self):
        """Escanea todas las interfaces en paralelo"""
        try:
            await asyncio.gather(
                self._scan_usb_serial(),
                self._scan_bluetooth(),
                self._scan_wifi(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Error en scan all: {e}")
            
    async def _scan_usb_serial(self):
        """Escanea puertos USB/Serial usando driver real"""
        try:
            usb_devices = await self.usb_driver.scan()
            
            for usb_dev in usb_devices:
                device_id = f"usb_{usb_dev.port}"
                if device_id not in self.devices:
                    sensor_info = self.usb_driver.identify_device(usb_dev)
                    device = DetectedDevice(
                        id=device_id,
                        name=f"{sensor_info['name']} ({usb_dev.description})",
                        type='usb',
                        address=usb_dev.port,
                        metadata={
                            'vid': usb_dev.vid,
                            'pid': usb_dev.pid,
                            'serial_number': usb_dev.serial_number,
                            'manufacturer': usb_dev.manufacturer,
                            'product': usb_dev.product,
                            'sensor_type': sensor_info['name'],
                            'baudrate': sensor_info['baudrate']
                        },
                        detected_at=usb_dev.detected_at
                    )
                    self.devices[device_id] = device
                    logger.info(f"🔌 USB REAL: {sensor_info['name']} en {usb_dev.port}")
            self.failures["usb"] = 0
            self.last_errors["usb"] = None
            self.last_scan_at["usb"] = datetime.utcnow()
        except Exception as e:
            self.failures["usb"] += 1
            self.last_errors["usb"] = str(e)
            logger.warning(f"USB scan falló ({self.failures['usb']}): {e}")
            
    async def _scan_bluetooth(self):
        """Escanea dispositivos Bluetooth BLE usando driver real"""
        try:
            ble_devices = await self.ble_driver.scan(timeout=5.0)
            
            for ble_dev in ble_devices:
                device_id = f"ble_{ble_dev.address}"
                if device_id not in self.devices:
                    sensor_type = self.ble_driver.identify_device(ble_dev)
                    device = DetectedDevice(
                        id=device_id,
                        name=f"{sensor_type} ({ble_dev.name or 'Unknown'})",
                        type='ble',
                        address=ble_dev.address,
                        metadata={
                            'rssi': ble_dev.rssi,
                            'manufacturer_data': ble_dev.manufacturer_data,
                            'service_uuids': ble_dev.service_uuids,
                            'sensor_type': sensor_type
                        },
                        detected_at=ble_dev.detected_at
                    )
                    self.devices[device_id] = device
                    logger.info(f"📡 BLE REAL: {sensor_type} @ {ble_dev.address} ({ble_dev.rssi}dBm)")
            self.failures["ble"] = 0
            self.last_errors["ble"] = None
            self.last_scan_at["ble"] = datetime.utcnow()
        except Exception as e:
            self.failures["ble"] += 1
            self.last_errors["ble"] = str(e)
            logger.warning(f"BLE scan falló ({self.failures['ble']}): {e}")
            
    async def _scan_wifi(self):
        """Escanea red WiFi con mDNS usando driver real"""
        try:
            # WiFi driver usa mDNS continuo, solo obtenemos nuevos
            wifi_devices = self.wifi_driver.get_new_devices()
            
            for wifi_dev in wifi_devices:
                device_id = f"wifi_{wifi_dev.hostname}"
                if device_id not in self.devices:
                    sensor_type = self.wifi_driver.identify_device(wifi_dev)
                    device = DetectedDevice(
                        id=device_id,
                        name=f"{sensor_type} ({wifi_dev.hostname})",
                        type='wifi',
                        address=wifi_dev.ip_address,
                        metadata={
                            'hostname': wifi_dev.hostname,
                            'port': wifi_dev.port,
                            'service_type': wifi_dev.service_type,
                            'properties': wifi_dev.properties,
                            'sensor_type': sensor_type
                        },
                        detected_at=wifi_dev.detected_at
                    )
                    self.devices[device_id] = device
                    logger.info(f"🌐 WiFi REAL: {sensor_type} @ {wifi_dev.ip_address} ({wifi_dev.hostname})")
            self.failures["wifi"] = 0
            self.last_errors["wifi"] = None
            self.last_scan_at["wifi"] = datetime.utcnow()
        except Exception as e:
            self.failures["wifi"] += 1
            self.last_errors["wifi"] = str(e)
            logger.warning(f"WiFi scan falló ({self.failures['wifi']}): {e}")
            
    def get_devices(self) -> List[DetectedDevice]:
        """Retorna todos los dispositivos detectados"""
        return list(self.devices.values())
        
    def get_new_devices(self, since: datetime) -> List[DetectedDevice]:
        """Retorna dispositivos detectados desde una fecha"""
        return [d for d in self.devices.values() if d.detected_at > since]

    def get_health(self) -> Dict[str, Dict[str, Optional[str]]]:
        """Retorna estado de salud por interfaz"""
        return {
            "usb": {
                "failures": self.failures["usb"],
                "last_error": self.last_errors["usb"],
                "last_scan_at": self.last_scan_at["usb"].isoformat() if self.last_scan_at["usb"] else None,
            },
            "ble": {
                "failures": self.failures["ble"],
                "last_error": self.last_errors["ble"],
                "last_scan_at": self.last_scan_at["ble"].isoformat() if self.last_scan_at["ble"] else None,
            },
            "wifi": {
                "failures": self.failures["wifi"],
                "last_error": self.last_errors["wifi"],
                "last_scan_at": self.last_scan_at["wifi"].isoformat() if self.last_scan_at["wifi"] else None,
            },
        }
