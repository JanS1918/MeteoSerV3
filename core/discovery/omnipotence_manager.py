"""
Gestor de Omnipotencia V1.5 - Orquesta el descubrimiento y asimilación
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime

from .universal_scanner import UniversalHardwareScanner, DetectedDevice
from .driver_installer import DriverInstaller

logger = logging.getLogger(__name__)

class OmnipotenceManager:
    """Orquestador del sistema de omnipotencia"""
    
    def __init__(self, system_core):
        self.system_core = system_core
        self.scanner = UniversalHardwareScanner()
        self.installer = DriverInstaller()
        self.last_check = datetime.now()
        self._running = False
        self._task = None
        
    async def start(self):
        """Inicia el sistema de omnipotencia"""
        if self._running:
            return
            
        self._running = True
        await self.scanner.start()
        self._task = asyncio.create_task(self._assimilation_loop())
        logger.info("🛸 OMNIPOTENCIA V1.5 ACTIVADA - Sistema de asimilación en línea")
        
    async def stop(self):
        """Detiene el sistema"""
        self._running = False
        await self.scanner.stop()
        if self._task:
            self._task.cancel()
            
    async def _assimilation_loop(self):
        """Bucle de asimilación de nuevos dispositivos"""
        while self._running:
            try:
                # Buscar nuevos dispositivos
                new_devices = self.scanner.get_new_devices(self.last_check)
                self.last_check = datetime.now()
                
                for device in new_devices:
                    await self._process_new_device(device)
                    
                await asyncio.sleep(10)  # Check cada 10 segundos
            except Exception as e:
                logger.error(f"Error en assimilation loop: {e}")
                await asyncio.sleep(5)
                
    async def _process_new_device(self, device: DetectedDevice):
        """Procesa un nuevo dispositivo detectado"""
        try:
            logger.info(f"[BUSCAR] Procesando nuevo dispositivo: {device.name} ({device.type})")
            
            # Intentar identificar e instalar driver si es necesario
            sensor_type = await self._identify_sensor(device.metadata)
            if sensor_type:
                # Poner en cola la instalación sin bloquear
                await self.installer.install_driver_async(sensor_type)
            
            # Registrar evento de hardware nuevo
            if hasattr(self.system_core, 'registrar_evento'):
                evento = {
                    'tipo': 'hardware_detected',
                    'dispositivo': device.name,
                    'via': device.type.upper(),
                    'direccion': device.address,
                    'sensor_identificado': sensor_type or 'desconocido',
                    'timestamp': device.detected_at.isoformat()
                }
                self.system_core.registrar_evento('hardware', evento)
                logger.info(f"[OK] Dispositivo registrado: {device.name}")
                
        except Exception as e:
            logger.error(f"Error procesando dispositivo {device.name}: {e}")
    
    async def _identify_sensor(self, device_info: dict) -> Optional[str]:
        """Identifica el tipo de sensor por su información"""
        name = device_info.get('name', '').lower()
        manufacturer = device_info.get('manufacturer', '').lower()
        product = device_info.get('product', '').lower()
        
        # Patrones de identificación
        if 'co2' in name or 'mh-z19' in name or 'scd' in name:
            return 'MH_Z19'
        if 'pm2.5' in name or 'plantower' in name or 'pms' in name:
            return 'PMS5003'
        if 'radon' in name:
            return 'RADON_EYE'
        if 'bme280' in name:
            return 'BME280'
        if 'bme680' in name:
            return 'BME680'
        if 'sht31' in name:
            return 'SHT31'
        if 'shelly' in manufacturer or 'shelly' in product:
            return 'SHELLY_DEVICE'
        if 'tasmota' in name:
            return 'TASMOTA_DEVICE'
            
        return None
            
    def get_status(self) -> dict:
        """Estado del sistema de omnipotencia"""
        devices = self.scanner.get_devices()
        return {
            'activo': self._running,
            'dispositivos_detectados': len(devices),
            'drivers_instalados': len(self.installer.installed_drivers),
            'dispositivos': [
                {
                    'id': d.id,
                    'nombre': d.name,
                    'tipo': d.type,
                    'detectado': d.detected_at.isoformat()
                }
                for d in devices
            ]
        }
