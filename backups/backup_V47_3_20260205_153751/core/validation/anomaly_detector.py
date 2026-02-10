"""
DETECTOR DE ANOMALÍAS V1.0 - MODO MONITOR
Propósito: detectar lecturas sospechosas (rangos físicos, saltos temporales, coherencia cruzada)
Publicación: tags en el Bus, logs en logs/anomalies.log
Acción: MODO MONITOR (no altera datos, solo marca DUDOSO)
"""

import logging
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("meteoser.anomaly_detector")


class AnomalyDetector:
    """Detector híbrido de anomalías con múltiples heurísticas."""
    
    def __init__(self, bus, system):
        self.bus = bus
        self.system = system
        self.logger = logging.getLogger("meteoser.anomaly_detector")
        
        # Configuración de thresholds editables
        self.config = {
            # Rangos físicos absolutos (WMO estándares)
            "temp_min": -89.2,  # Vostok, 1983
            "temp_max": 56.7,   # Oven, Libia, 1922
            "humedad_min": 0.0,
            "humedad_max": 100.0,
            "presion_min": 870.0,  # Tifón Tip, 1979
            "presion_max": 1085.0,  # Tonopah, Nevada, 1983
            
            # Saltos temporales (cambios en 60 segundos)
            "temp_jump_threshold": 10.0,  # °C/min es físicamente imposible
            "presion_jump_threshold": 5.0,  # hPa/min es muy agresivo
            "humedad_jump_threshold": 50.0,  # %/min es irreal
            
            # Coherencia cruzada: si humedad es baja, presión no puede cambiar mucho
            "coherence_weight": 0.5,
            
            # Configuración del detector
            "enable_monitor": True,  # Modo monitor (True = no altera, False = activa acciones)
            "log_level": "WARNING",  # DEBUG, INFO, WARNING
            "history_window_seconds": 300,  # Ventana para detectar tendencias
        }
        
        # Histórico reciente (últimas N mediciones)
        self.recent_measurements: List[Dict] = []
        self.max_history = 50  # Mantener últimas 50 mediciones
    
    async def detect(self, measurement: Dict) -> Dict:
        """
        Detecta anomalías en una medición.
        Retorna: {status, reasons, score, action}
        """
        status = "OK"
        reasons: List[str] = []
        score = 0.0  # 0-1, donde 1 es anomalía segura
        action = "PUBLISH_NORMAL"
        
        try:
            # Test 1: Rangos físicos absolutos
            if not self._check_physical_ranges(measurement):
                status = "DUDOSO"
                reasons.append("valor_fuera_rango_fisico")
                score += 0.8
            
            # Test 2: Saltos temporales imposibles
            if len(self.recent_measurements) > 0:
                jump_detected = self._check_temporal_jumps(measurement)
                if jump_detected:
                    status = "DUDOSO"
                    reasons.append("salto_temporal_imposible")
                    score += 0.7
            
            # Test 3: Coherencia cruzada
            coherence_issue = self._check_cross_variable_coherence(measurement)
            if coherence_issue:
                status = "DUDOSO"
                reasons.append("incoherencia_variables_cruzadas")
                score += 0.6
            
            # Test 4: Detector de outliers simple (Z-score histórico)
            if len(self.recent_measurements) >= 10:
                outlier_detected = self._check_outlier_zscore(measurement)
                if outlier_detected:
                    status = "DUDOSO"
                    reasons.append("outlier_detectado")
                    score += 0.4
            
            # Normalizar score a [0, 1]
            score = min(score, 1.0)
            
            # Añadir medición al histórico
            self._add_to_history(measurement)
            
            # Determinar acción
            if status == "OK":
                action = "PUBLISH_NORMAL"
            else:
                action = "PUBLISH_WITH_DUDOSO_TAG" if self.config["enable_monitor"] else "TRIGGER_FALLBACK"
            
            result = {
                "status": status,  # OK | DUDOSO | SUSPECTED_SENSOR_FAILURE
                "reasons": reasons,
                "score": score,  # 0.0-1.0 confianza de anomalía
                "action": action,
                "detector_version": "1.0",
                "timestamp": datetime.now().isoformat()
            }
            
            # Log si es importante
            if status != "OK":
                self.logger.warning(f"ANOMALIA DETECTADA: {measurement.get('sensor_id', 'unknown')} - status={status}, reasons={reasons}, score={score:.2f}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error en detector de anomalías: {e}", exc_info=True)
            return {
                "status": "ERROR",
                "reasons": [str(e)],
                "score": 0.0,
                "action": "PUBLISH_WITH_ERROR_TAG",
                "detector_version": "1.0",
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_physical_ranges(self, measurement: Dict) -> bool:
        """Verifica que todos los valores estén dentro de rangos físicos posibles."""
        try:
            temp = measurement.get("temperatura")
            if temp is not None:
                if not (self.config["temp_min"] <= temp <= self.config["temp_max"]):
                    self.logger.debug(f"Temperatura fuera de rango: {temp}°C")
                    return False
            
            humedad = measurement.get("humedad")
            if humedad is not None:
                if not (self.config["humedad_min"] <= humedad <= self.config["humedad_max"]):
                    self.logger.debug(f"Humedad fuera de rango: {humedad}%")
                    return False
            
            presion = measurement.get("presion_barometrica")
            if presion is not None:
                if not (self.config["presion_min"] <= presion <= self.config["presion_max"]):
                    self.logger.debug(f"Presión fuera de rango: {presion} hPa")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Error verificando rangos físicos: {e}")
            return True  # Asumir OK en caso de error
    
    def _check_temporal_jumps(self, measurement: Dict) -> bool:
        """Detecta cambios imposibles entre mediciones consecutivas (saltos > threshold)."""
        try:
            if not self.recent_measurements:
                return False
            
            last = self.recent_measurements[-1]
            
            # Calcular delta temporales (asumiendo ~60s entre mediciones)
            delta_temp = abs(measurement.get("temperatura", 0) - last.get("temperatura", 0))
            delta_presion = abs(measurement.get("presion_barometrica", 0) - last.get("presion_barometrica", 0))
            delta_humedad = abs(measurement.get("humedad", 0) - last.get("humedad", 0))
            
            if delta_temp > self.config["temp_jump_threshold"]:
                self.logger.debug(f"Salto de temperatura: {delta_temp:.2f}°C en 1 minuto")
                return True
            
            if delta_presion > self.config["presion_jump_threshold"]:
                self.logger.debug(f"Salto de presión: {delta_presion:.2f} hPa en 1 minuto")
                return True
            
            if delta_humedad > self.config["humedad_jump_threshold"]:
                self.logger.debug(f"Salto de humedad: {delta_humedad:.2f}% en 1 minuto")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error verificando saltos temporales: {e}")
            return False
    
    def _check_cross_variable_coherence(self, measurement: Dict) -> bool:
        """Verifica coherencia entre variables (ej. humedad baja pero presión cambiando mucho)."""
        try:
            humedad = measurement.get("humedad", 50)
            temp = measurement.get("temperatura", 15)
            presion = measurement.get("presion_barometrica", 1013)
            
            # Heurística 1: Si humedad es muy baja (< 5%), presión no debería cambiar rápido
            # porque el aire es muy seco y estable
            if humedad < 5:
                if len(self.recent_measurements) > 0:
                    delta_presion = abs(presion - self.recent_measurements[-1].get("presion_barometrica", presion))
                    if delta_presion > 2.0:  # Más de 2 hPa/min con humedad < 5% es sospechoso
                        self.logger.debug(f"Incoherencia: humedad={humedad}% pero presión salta {delta_presion} hPa")
                        return True
            
            # Heurística 2: Humedad muy alta (>95%) + temperatura muy baja (<-20°C) es raro
            if humedad > 95 and temp < -20:
                self.logger.debug(f"Incoherencia: humedad={humedad}% con temp={temp}°C (posible congelación sensor)")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error verificando coherencia cruzada: {e}")
            return False
    
    def _check_outlier_zscore(self, measurement: Dict) -> bool:
        """Detecta outliers usando Z-score sobre el histórico reciente."""
        try:
            if len(self.recent_measurements) < 10:
                return False
            
            temp = measurement.get("temperatura")
            if temp is None:
                return False
            
            # Calcular media y desviación estándar del histórico
            temps = [m.get("temperatura") for m in self.recent_measurements[-20:] if m.get("temperatura") is not None]
            if len(temps) < 5:
                return False
            
            mean_temp = sum(temps) / len(temps)
            variance = sum((t - mean_temp) ** 2 for t in temps) / len(temps)
            std_temp = math.sqrt(variance)
            
            if std_temp == 0:  # Evitar división por cero
                return False
            
            z_score = abs((temp - mean_temp) / std_temp)
            
            # Z-score > 3 indica outlier significativo
            if z_score > 3.0:
                self.logger.debug(f"Outlier detectado: temperatura={temp}°C, z-score={z_score:.2f}")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error detectando outliers: {e}")
            return False
    
    def _add_to_history(self, measurement: Dict):
        """Añade una medición al histórico reciente."""
        measurement["_timestamp"] = datetime.now().isoformat()
        self.recent_measurements.append(measurement)
        
        # Mantener ventana de histórico
        if len(self.recent_measurements) > self.max_history:
            self.recent_measurements = self.recent_measurements[-self.max_history:]
    
    def get_config(self) -> Dict:
        """Retorna configuración actual (para ajustes dinámicos)."""
        return self.config.copy()
    
    def update_config(self, new_config: Dict):
        """Actualiza configuración de thresholds."""
        for key, value in new_config.items():
            if key in self.config:
                self.config[key] = value
                self.logger.info(f"Threshold actualizado: {key} = {value}")
            else:
                self.logger.warning(f"Configuración desconocida: {key}")
    
    async def publish_to_bus(self, measurement: Dict, detection_result: Dict):
        """Publica los resultados del detector al Bus con metadata."""
        try:
            # Publicar resultado de detección
            sensor_id = measurement.get("sensor_id", "unknown")
            
            # Crear payload con metadata de detección
            payload = {
                "status": detection_result["status"],
                "score": detection_result["score"],
                "reasons": detection_result["reasons"],
                "detector_version": detection_result["detector_version"],
                "timestamp": detection_result["timestamp"]
            }
            
            # Publicar en el Bus
            self.bus.publicar(f"anomaly_detection_{sensor_id}", payload, "metadata")
            
            # Publicar flag de dudoso si aplica
            if detection_result["status"] == "DUDOSO":
                self.bus.publicar(f"{sensor_id}_dudoso", True, "boolean")
            
            self.logger.debug(f"Resultado de detección publicado al Bus para {sensor_id}")
        
        except Exception as e:
            self.logger.error(f"Error publicando resultado de detección: {e}", exc_info=True)
