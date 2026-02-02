"""
Radar Universal de Hardware - USB/Serial, BLE, WiFi
"""
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

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
    """Escáner universal que detecta hardware por cualquier medio"""
    
    def __init__(self):
        self.devices: Dict[str, DetectedDevice] = {}
        self.scan_interval = 30  # segundos
        self._running = False
        self._task = None
        
    async def start(self):
        """Inicia el radar de hardware"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._scan_loop())
        logger.info("🛸 Radar Universal ACTIVADO - Escaneando USB, BLE, WiFi...")
        
    async def stop(self):
        """Detiene el radar"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
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
        """Escanea puertos USB/Serial"""
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                device_id = f"usb_{port.device}"
                if device_id not in self.devices:
                    device = DetectedDevice(
                        id=device_id,
                        name=port.description or port.device,
                        type='usb',
                        address=port.device,
                        metadata={
                            'vid': port.vid,
                            'pid': port.pid,
                            'serial_number': port.serial_number,
                            'manufacturer': port.manufacturer,
                            'product': port.product
                        },
                        detected_at=datetime.now()
                    )
                    self.devices[device_id] = device
                    logger.info(f"🔌 Nuevo USB detectado: {port.description} en {port.device}")
        except Exception as e:
            logger.debug(f"USB scan error: {e}")
            
    async def _scan_bluetooth(self):
        """Escanea dispositivos Bluetooth BLE"""
        try:
            from bleak import BleakScanner
            devices = await BleakScanner.discover(timeout=5.0)
            
            for device in devices:
                device_id = f"ble_{device.address}"
                if device_id not in self.devices:
                    ble_device = DetectedDevice(
                        id=device_id,
                        name=device.name or "BLE Device",
                        type='ble',
                        address=device.address,
                        metadata={
                            'rssi': device.rssi,
                            'details': device.details
                        },
                        detected_at=datetime.now()
                    )
                    self.devices[device_id] = ble_device
                    logger.info(f"📡 Nuevo BLE detectado: {device.name} ({device.address})")
        except Exception as e:
            logger.debug(f"BLE scan error: {e}")
            
    async def _scan_wifi(self):
        """Escanea red WiFi con mDNS/ZeroConf"""
        try:
            from zeroconf import ServiceBrowser, Zeroconf
            # Por ahora, solo logging, implementación completa después
            logger.debug("WiFi/mDNS scan ejecutado")
        except Exception as e:
            logger.debug(f"WiFi scan error: {e}")
            
    def get_devices(self) -> List[DetectedDevice]:
        """Retorna todos los dispositivos detectados"""
        return list(self.devices.values())
        
    def get_new_devices(self, since: datetime) -> List[DetectedDevice]:
        """Retorna dispositivos detectados desde una fecha"""
        return [d for d in self.devices.values() if d.detected_at > since]
