"""
Universal Orchestrator: Coordinador maestro del Radar de Hardware
Orquesta simultáneamente USB, BLE, WiFi y asimilación inteligente
"""

import logging
import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .usb_scanner import USBScanner, USBDevice
from .ble_scanner import BLEScanner, BLEDevice
from .mdns_scanner import mDNSScanner, mDNSDevice
from .driver_installer import DriverInstaller

logger = logging.getLogger(__name__)


class DetectionSource(str, Enum):
    """Fuente de detección del dispositivo"""
    USB = "USB/SERIAL"
    BLE = "BLUETOOTH"
    MDNS = "WIFI/MDNS"
    ECOWITT = "ECOWITT"
    CUSTOM = "CUSTOM"


class SensorState(str, Enum):
    """Estado del sensor en el ciclo de asimilación"""
    DETECTED = "detected"
    DRIVER_INSTALLING = "driver_installing"
    READY = "ready"
    ACTIVE = "active"
    ERROR = "error"


@dataclass
class DetectedHardware:
    """Representa hardware detectado y listo para asimilación"""
    sensor_id: str
    sensor_type: str
    source: DetectionSource
    metadata: Dict = field(default_factory=dict)
    state: SensorState = SensorState.DETECTED
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'source': self.source.value,
            'metadata': self.metadata,
            'state': self.state.value,
            'timestamp': self.timestamp.isoformat(),
            'error_message': self.error_message
        }


class UniversalOrchestrator:
    """Coordinador maestro del descubrimiento universal"""
    
    def __init__(self):
        self.usb_scanner = USBScanner()
        self.ble_scanner = BLEScanner()
        self.mdns_scanner = mDNSScanner()
        self.driver_installer = DriverInstaller()
        
        self.detected_hardware: Dict[str, DetectedHardware] = {}
        self.pending_assimilation: List[DetectedHardware] = []
        
        self.lock = asyncio.Lock()
        self.is_running = False
        
        # Callbacks para notificaciones
        self.on_new_hardware: Optional[Callable] = None
        self.on_ready_for_assimilation: Optional[Callable] = None
        self.on_installation_complete: Optional[Callable] = None
    
    async def start_universal_scan(self):
        """Inicia todos los escáneres simultáneamente"""
        if self.is_running:
            logger.warning("Escaneo universal ya en ejecución")
            return
        
        self.is_running = True
        logger.info("🛸 Iniciando Radar Universal de Hardware...")
        
        # Iniciar todos los escáneres en paralelo
        scan_tasks = [
            asyncio.create_task(self.usb_scanner.continuous_scan(interval=5)),
            asyncio.create_task(self.ble_scanner.continuous_scan(interval=10)),
            asyncio.create_task(self.mdns_scanner.continuous_scan(interval=15)),
            asyncio.create_task(self.driver_installer.process_install_queue()),
            asyncio.create_task(self._orchestration_loop())
        ]
        
        try:
            await asyncio.gather(*scan_tasks)
        except Exception as e:
            logger.error(f"Error en escaneo universal: {e}")
    
    async def stop_universal_scan(self):
        """Detiene todos los escáneres"""
        self.is_running = False
        self.usb_scanner.stop_scanning()
        self.ble_scanner.stop_scanning()
        self.mdns_scanner.stop_scanning()
        logger.info("Radar Universal detenido")
    
    async def _orchestration_loop(self):
        """Loop principal de orquestación"""
        while self.is_running:
            try:
                # Recolectar dispositivos de todos los escáneres
                usb_devices = await self.usb_scanner.get_detected_devices()
                ble_devices = await self.ble_scanner.get_detected_devices()
                mdns_devices = await self.mdns_scanner.get_detected_devices()
                
                # Procesar USB/Serial
                for device in usb_devices:
                    await self._process_usb_device(device)
                
                # Procesar BLE
                for device in ble_devices:
                    await self._process_ble_device(device)
                
                # Procesar mDNS
                for device in mdns_devices:
                    await self._process_mdns_device(device)
                
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"Error en loop de orquestación: {e}")
                await asyncio.sleep(3)
    
    async def _process_usb_device(self, device: USBDevice):
        """Procesa un dispositivo USB detectado"""
        if not device.product:
            return
        
        sensor_id = f"usb_{device.port}"
        
        async with self.lock:
            if sensor_id in self.detected_hardware:
                return  # Ya procesado
            
            hardware = DetectedHardware(
                sensor_id=sensor_id,
                sensor_type=device.product,
                source=DetectionSource.USB,
                metadata={
                    'port': device.port,
                    'manufacturer': device.manufacturer,
                    'vid': device.vid,
                    'pid': device.pid
                }
            )
            
            self.detected_hardware[sensor_id] = hardware
            self.pending_assimilation.append(hardware)
            
            logger.info(f"🔌 Nuevo Hardware USB detectado: {hardware.to_dict()}")
            
            if self.on_new_hardware:
                await self.on_new_hardware(hardware)
    
    async def _process_ble_device(self, device: BLEDevice):
        """Procesa un dispositivo BLE detectado"""
        if not device.name:
            return
        
        sensor_id = f"ble_{device.address}"
        
        async with self.lock:
            if sensor_id in self.detected_hardware:
                return  # Ya procesado
            
            hardware = DetectedHardware(
                sensor_id=sensor_id,
                sensor_type=device.name,
                source=DetectionSource.BLE,
                metadata={
                    'address': device.address,
                    'rssi': device.rssi,
                    'services': device.service_uuids
                }
            )
            
            self.detected_hardware[sensor_id] = hardware
            self.pending_assimilation.append(hardware)
            
            logger.info(f"📡 Nuevo Hardware Bluetooth detectado: {hardware.to_dict()}")
            
            if self.on_new_hardware:
                await self.on_new_hardware(hardware)
    
    async def _process_mdns_device(self, device: mDNSDevice):
        """Procesa un dispositivo mDNS detectado"""
        if not device.type_:
            return
        
        sensor_id = f"mdns_{device.hostname}"
        
        async with self.lock:
            if sensor_id in self.detected_hardware:
                return  # Ya procesado
            
            hardware = DetectedHardware(
                sensor_id=sensor_id,
                sensor_type=device.type_,
                source=DetectionSource.MDNS,
                metadata={
                    'hostname': device.hostname,
                    'ip': device.ip_address,
                    'port': device.port
                }
            )
            
            self.detected_hardware[sensor_id] = hardware
            self.pending_assimilation.append(hardware)
            
            logger.info(f"🌐 Nuevo Hardware WiFi detectado: {hardware.to_dict()}")
            
            if self.on_new_hardware:
                await self.on_new_hardware(hardware)
    
    async def assimilate_hardware(self, sensor_id: str) -> bool:
        """
        Asimila un hardware detectado
        - Descarga el driver si es necesario
        - Lo prepara para ingesta de datos
        """
        async with self.lock:
            hardware = self.detected_hardware.get(sensor_id)
            if not hardware:
                logger.error(f"Hardware no encontrado: {sensor_id}")
                return False
            
            hardware.state = SensorState.DRIVER_INSTALLING
        
        try:
            logger.info(f"📥 Iniciando asimilación de {sensor_id}...")
            
            # Instalar driver si es necesario
            spec = await self.driver_installer.get_driver_spec(hardware.sensor_type)
            if spec:
                success, msg = await self.driver_installer.install_driver(hardware.sensor_type)
                if not success:
                    async with self.lock:
                        hardware.state = SensorState.ERROR
                        hardware.error_message = msg
                    logger.error(f"Fallo en instalación: {msg}")
                    return False
            
            async with self.lock:
                hardware.state = SensorState.READY
            
            logger.info(f"[OK] {sensor_id} listo para asimilación")
            
            if self.on_ready_for_assimilation:
                await self.on_ready_for_assimilation(hardware)
            
            return True
        
        except Exception as e:
            async with self.lock:
                hardware.state = SensorState.ERROR
                hardware.error_message = str(e)
            logger.error(f"Error asimilando {sensor_id}: {e}")
            return False
    
    async def get_pending_hardware(self) -> List[DetectedHardware]:
        """Retorna hardware esperando asimilación"""
        async with self.lock:
            pending = [h for h in self.pending_assimilation 
                      if h.state == SensorState.DETECTED]
            return pending
    
    async def get_all_detected(self) -> List[DetectedHardware]:
        """Retorna todo hardware detectado"""
        async with self.lock:
            return list(self.detected_hardware.values())
    
    async def register_callback(self, event: str, callback: Callable):
        """Registra callbacks para eventos"""
        if event == 'new_hardware':
            self.on_new_hardware = callback
        elif event == 'ready_for_assimilation':
            self.on_ready_for_assimilation = callback
        elif event == 'installation_complete':
            self.on_installation_complete = callback
