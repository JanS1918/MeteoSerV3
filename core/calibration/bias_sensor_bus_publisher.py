#!/usr/bin/env python3
"""CAPA 23: Bias Sensores - Publica offsets de sesgo de sensores al Bus MQTT"""

import logging
import json
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger("bias_detector_bus")


@dataclass
class BiasOffset:
    sensor_name: str
    bias_offset_celsius: float
    confidence: float
    last_calibration_ts: float


class BiasSensorBusPublisher:
    """Publica offsets de sesgo de sensores al Bus MQTT para sincronización."""
    
    MQTT_TOPIC_PREFIX = "meteoser/calibration"
    
    def __init__(self, mqtt_client=None):
        self.mqtt_client = mqtt_client
        self.bias_registry: Dict[str, BiasOffset] = {}
        logger.info("[OK] BiasSensorBusPublisher inicializado")
    
    def register_bias(self, sensor_name: str, bias_offset_celsius: float,
                     confidence: float, last_calibration_ts: float):
        """Registra bias offset para sensor."""
        self.bias_registry[sensor_name] = BiasOffset(
            sensor_name, bias_offset_celsius, confidence, last_calibration_ts
        )
        logger.debug(f"📝 Sesgo registrado {sensor_name}: {bias_offset_celsius:+.2f}°C (conf={confidence:.0%})")
    
    def publish_to_bus(self, sensor_name: str) -> bool:
        """Publica bias offset al Bus MQTT."""
        if sensor_name not in self.bias_registry:
            logger.warning(f"[WARNING] {sensor_name} no tiene bias registrado")
            return False
        
        bias = self.bias_registry[sensor_name]
        topic = f"{self.MQTT_TOPIC_PREFIX}/sensor_{sensor_name}_bias_offset"
        
        payload = {
            "sensor": sensor_name,
            "bias_celsius": bias.bias_offset_celsius,
            "confidence": bias.confidence,
            "timestamp": bias.last_calibration_ts
        }
        
        if self.mqtt_client:
            try:
                self.mqtt_client.publish(topic, json.dumps(payload))
                logger.info(f"[OK] Publicado bias {sensor_name} en {topic}")
                return True
            except Exception as e:
                logger.error(f"[ERROR] Error publicando bias {sensor_name}: {e}")
                return False
        else:
            logger.debug(f"📡 [SIMULATE] Publicaría {topic}: {payload}")
            return True
    
    def publish_all_biases(self) -> Dict[str, bool]:
        """Publica todos los biases al Bus."""
        results = {}
        for sensor_name in self.bias_registry:
            results[sensor_name] = self.publish_to_bus(sensor_name)
        return results
    
    def get_bias_for_sensor(self, sensor_name: str) -> Optional[float]:
        """Obtiene offset de sesgo para aplicar."""
        if sensor_name in self.bias_registry:
            return self.bias_registry[sensor_name].bias_offset_celsius
        return None
