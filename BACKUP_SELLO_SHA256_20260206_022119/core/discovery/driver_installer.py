"""
Driver Installer: Auto-descarga e instala librerías de sensores
Sistema de auto-recuperación de dependencias sin detener el motor principal
"""

import logging
import asyncio
import subprocess
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DriverSpec:
    """Especificación de driver para un tipo de sensor"""
    sensor_type: str
    libraries: List[str]
    protocol: str
    parser_module: Optional[str] = None
    git_url: Optional[str] = None
    pypi_package: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'sensor_type': self.sensor_type,
            'libraries': self.libraries,
            'protocol': self.protocol,
            'parser_module': self.parser_module,
            'git_url': self.git_url,
            'pypi_package': self.pypi_package
        }


class DriverInstaller:
    """Gestor de auto-instalación de drivers"""
    
    # Especificaciones de drivers conocidos
    DRIVER_SPECS = {
        'MH_Z19_CO2': DriverSpec(
            sensor_type='MH_Z19_CO2',
            libraries=['pyserial', 'mh_z19'],
            protocol='UART',
            pypi_package='mh-z19'
        ),
        'SGP30_CO2_SENSOR': DriverSpec(
            sensor_type='SGP30_CO2_SENSOR',
            libraries=['Adafruit-CircuitPython-SGP30', 'busio'],
            protocol='I2C',
            pypi_package='adafruit-circuitpython-sgp30'
        ),
        'BME680': DriverSpec(
            sensor_type='BME680',
            libraries=['bme680'],
            protocol='I2C/SPI',
            pypi_package='bme680'
        ),
        'SHT31': DriverSpec(
            sensor_type='SHT31',
            libraries=['Adafruit-CircuitPython-SHT31D'],
            protocol='I2C',
            pypi_package='adafruit-circuitpython-sht31d'
        ),
        'SHELLY_DEVICE': DriverSpec(
            sensor_type='SHELLY_DEVICE',
            libraries=['requests'],
            protocol='HTTP_REST',
            pypi_package='requests'
        ),
        'TASMOTA_DEVICE': DriverSpec(
            sensor_type='TASMOTA_DEVICE',
            libraries=['requests', 'paho-mqtt'],
            protocol='HTTP_REST/MQTT',
            pypi_package='paho-mqtt'
        ),
    }
    
    def __init__(self):
        self.installed_drivers: Dict[str, bool] = {}
        self.installation_lock = asyncio.Lock()
        self.install_queue: List[str] = []
    
    async def get_driver_spec(self, sensor_type: str) -> Optional[DriverSpec]:
        """Obtiene la especificación de driver para un tipo de sensor"""
        return self.DRIVER_SPECS.get(sensor_type)
    
    async def install_driver(self, sensor_type: str) -> Tuple[bool, str]:
        """
        Instala el driver para un sensor específico
        Retorna (éxito, mensaje)
        """
        async with self.installation_lock:
            # Evitar instalaciones duplicadas
            if self.installed_drivers.get(sensor_type):
                return True, f"Driver {sensor_type} ya instalado"
            
            spec = await self.get_driver_spec(sensor_type)
            if not spec:
                return False, f"Especificación desconocida para {sensor_type}"
            
            logger.info(f"Iniciando instalación de driver: {sensor_type}")
            
            try:
                # Instalar librerías de PyPI
                if spec.pypi_package:
                    success, msg = await self._install_pypi_package(spec.pypi_package)
                    if not success:
                        logger.error(f"Fallo al instalar {spec.pypi_package}: {msg}")
                        return False, msg
                else:
                    for lib in spec.libraries:
                        success, msg = await self._install_pypi_package(lib)
                        if not success:
                            logger.error(f"Fallo al instalar {lib}: {msg}")
                            return False, msg
                
                self.installed_drivers[sensor_type] = True
                logger.info(f"Driver {sensor_type} instalado exitosamente")
                return True, f"Driver {sensor_type} instalado exitosamente"
            
            except Exception as e:
                error_msg = f"Error instalando driver {sensor_type}: {e}"
                logger.error(error_msg)
                return False, error_msg
    
    async def _install_pypi_package(self, package_name: str) -> Tuple[bool, str]:
        """Instala un paquete de PyPI"""
        try:
            import sys
            result = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'pip', 'install', '--upgrade', package_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=60)
            
            if result.returncode == 0:
                return True, f"Instalado {package_name}"
            else:
                return False, stderr.decode()
        
        except asyncio.TimeoutError:
            return False, f"Timeout instalando {package_name}"
        except Exception as e:
            return False, str(e)
    
    async def install_driver_async(self, sensor_type: str):
        """
        Instala driver de forma asíncrona sin bloquear el motor principal
        Se ejecuta en background
        """
        self.install_queue.append(sensor_type)
    
    async def process_install_queue(self):
        """Procesa la cola de instalaciones en background"""
        while True:
            try:
                while self.install_queue:
                    sensor_type = self.install_queue.pop(0)
                    success, msg = await self.install_driver(sensor_type)
                    logger.info(f"Instalación de {sensor_type}: {msg}")
                
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error procesando queue de instalación: {e}")
                await asyncio.sleep(5)
    
    async def verify_driver(self, sensor_type: str) -> bool:
        """Verifica si un driver está disponible"""
        spec = await self.get_driver_spec(sensor_type)
        if not spec:
            return False
        
        try:
            for lib in spec.libraries:
                try:
                    __import__(lib.split('-')[0].replace('-', '_'))
                except ImportError:
                    logger.warning(f"Librería {lib} no disponible para {sensor_type}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error verificando driver {sensor_type}: {e}")
            return False
    
    def get_installed_drivers(self) -> Dict[str, bool]:
        """Retorna los drivers instalados"""
        return self.installed_drivers.copy()
