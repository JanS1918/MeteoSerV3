"""
Sensor Assimilator: Integra sensores detectados al sistema principal
Valida cruzadamente y asimila datos al motor ambiental
"""

import logging
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SensorAssimilator:
    """Gestor de asimilación de sensores al sistema central"""
    
    def __init__(self, system_core=None):
        """
        Inicializa el asimilador
        system_core: referencia al core SystemCore para acceso a sensores
        """
        self.system_core = system_core
        self.assimilated_sensors: Dict[str, Dict] = {}
        self.validation_rules: Dict[str, callable] = self._init_validation_rules()
        self.lock = asyncio.Lock()
    
    def _init_validation_rules(self) -> Dict[str, callable]:
        """Inicializa reglas de validación cruzada"""
        return {
            'CO2_VALIDATION': self._validate_co2_combustion,
            'HUMIDITY_RANGE': self._validate_humidity_range,
            'TEMPERATURE_RANGE': self._validate_temperature_range,
            'PRESSURE_SANITY': self._validate_pressure_sanity,
        }
    
    async def assimilate_sensor(self, hardware_info: Dict, sensor_config: Dict) -> bool:
        """
        Asimila un sensor nuevo al sistema
        
        hardware_info: Información del hardware detectado
        sensor_config: Configuración del sensor (mappings, conversiones, etc)
        """
        try:
            async with self.lock:
                sensor_id = hardware_info.get('sensor_id')
                sensor_type = hardware_info.get('sensor_type')
                
                logger.info(f"🧬 Asimilando {sensor_id} ({sensor_type})...")
                
                # Crear metadata de asimilación
                metadata = {
                    'detected_at': datetime.now().isoformat(),
                    'source': hardware_info.get('source'),
                    'hardware_metadata': hardware_info.get('metadata', {}),
                    'sensor_config': sensor_config,
                    'validation_enabled': True
                }
                
                self.assimilated_sensors[sensor_id] = metadata
                
                # Si tenemos acceso al core, registrar el sensor
                if self.system_core:
                    await self._register_in_core(sensor_id, sensor_type, sensor_config)
                
                logger.info(f"[OK] {sensor_id} asimilado al sistema")
                return True
        
        except Exception as e:
            logger.error(f"Error asimilando sensor: {e}")
            return False
    
    async def _register_in_core(self, sensor_id: str, sensor_type: str, config: Dict):
        """Registra el sensor en el SystemCore"""
        try:
            if hasattr(self.system_core, 'sensores_metadata'):
                self.system_core.sensores_metadata[sensor_id] = {
                    'type': sensor_type,
                    'detected': True,
                    'config': config
                }
                logger.info(f"Sensor {sensor_id} registrado en SystemCore")
        except Exception as e:
            logger.error(f"Error registrando en core: {e}")
    
    async def ingest_sensor_data(self, sensor_id: str, data: Dict) -> Optional[Dict]:
        """
        Ingesta datos de un sensor asimilado
        Aplica validación cruzada antes de asimilar
        """
        try:
            if sensor_id not in self.assimilated_sensors:
                logger.warning(f"Sensor no asimilado: {sensor_id}")
                return None
            
            # Aplicar validaciones
            validated_data = await self._validate_sensor_data(sensor_id, data)
            
            if validated_data is None:
                logger.warning(f"Datos rechazados para {sensor_id}: no pasaron validación")
                return None
            
            # Ingestar al core si está disponible
            if self.system_core:
                await self._ingest_to_core(sensor_id, validated_data)
            
            return validated_data
        
        except Exception as e:
            logger.error(f"Error ingesting datos de {sensor_id}: {e}")
            return None
    
    async def _validate_sensor_data(self, sensor_id: str, data: Dict) -> Optional[Dict]:
        """Valida datos de sensor aplicando reglas cruzadas"""
        validated = data.copy()
        
        # Aplicar reglas de validación
        for rule_name, rule_func in self.validation_rules.items():
            try:
                result = await rule_func(sensor_id, validated)
                if result is False:
                    logger.debug(f"Validación {rule_name} falló para {sensor_id}")
                    return None
            except Exception as e:
                logger.debug(f"Error en regla {rule_name}: {e}")
        
        return validated
    
    async def _validate_co2_combustion(self, sensor_id: str, data: Dict) -> bool:
        """
        Valida CO2 contra PM2.5 para detectar modo COMBUSTIÓN
        Si CO2 es alto pero PM2.5 es bajo, es sospechoso
        """
        co2 = data.get('co2')
        pm25 = data.get('pm25')
        
        if not co2 or not pm25:
            return True  # No hay datos cruzados para validar
        
        # Regla: Si CO2 > 1200 ppm, PM2.5 debe ser > 35 (humo indicativo)
        if co2 > 1200 and pm25 < 35:
            logger.warning(f"CO2 alto ({co2}) pero PM2.5 bajo ({pm25}): posible sensor fantasma")
            return False
        
        return True
    
    async def _validate_humidity_range(self, sensor_id: str, data: Dict) -> bool:
        """Valida rango de humedad (0-100%)"""
        humidity = data.get('humidity')
        
        if humidity is not None:
            if not (0 <= humidity <= 100):
                logger.warning(f"Humedad fuera de rango: {humidity}%")
                return False
        
        return True
    
    async def _validate_temperature_range(self, sensor_id: str, data: Dict) -> bool:
        """Valida rango de temperatura (-50 a +80°C)"""
        temperature = data.get('temperature')
        
        if temperature is not None:
            if not (-50 <= temperature <= 80):
                logger.warning(f"Temperatura fuera de rango: {temperature}°C")
                return False
        
        return True
    
    async def _validate_pressure_sanity(self, sensor_id: str, data: Dict) -> bool:
        """Valida presión (típicamente 950-1050 hPa)"""
        pressure = data.get('pressure')
        
        if pressure is not None:
            if not (900 <= pressure <= 1100):
                logger.warning(f"Presión fuera de rango: {pressure} hPa")
                return False
        
        return True
    
    async def _ingest_to_core(self, sensor_id: str, data: Dict):
        """Ingesta datos validados al SystemCore"""
        try:
            if hasattr(self.system_core, 'sensores'):
                for key, value in data.items():
                    core_key = f"{sensor_id}_{key}"
                    self.system_core.sensores[core_key] = value
                    logger.debug(f"Ingested {core_key} = {value}")
        except Exception as e:
            logger.error(f"Error ingesting to core: {e}")
    
    def get_assimilated_sensors(self) -> Dict:
        """Retorna sensores asimilados"""
        return self.assimilated_sensors.copy()
    
    async def remove_sensor(self, sensor_id: str) -> bool:
        """Desasimila un sensor del sistema"""
        try:
            async with self.lock:
                if sensor_id in self.assimilated_sensors:
                    del self.assimilated_sensors[sensor_id]
                    logger.info(f"Sensor {sensor_id} desasimilado")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error desasimilando {sensor_id}: {e}")
            return False
