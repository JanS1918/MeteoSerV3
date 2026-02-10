"""
Integrador de Prediction Engine V51
Propósito: Conectar prediction_engine con el scheduler automático
Flujo: scheduler → carga prediction_engine → ejecuta modelos → publica predicciones
"""

import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class IntegradorPredictionEngineV51:
    """
    Integra el MotorPrediccion con el scheduler automático
    
    Funcionalidades:
    1. Intenta cargar modelos LSTM si existen
    2. Ejecuta predicciones si hay modelos disponibles
    3. Publica predicciones al bus (compatible con BusEstadoGlobal)
    4. Gracefully degrada si no hay modelos disponibles
    """
    
    def __init__(self):
        """Inicializa el integrador"""
        self.motor = None
        self.disponible = False
        self.modelos_cargados = 0
        self.predicciones_ejecutadas = 0
        
        self._intentar_cargar_motor()
    
    def _intentar_cargar_motor(self):
        """Intenta cargar el motor de predicción"""
        try:
            from core.prediction.prediction_engine import obtener_motor_prediccion
            from core.bus import obtener_bus
            
            # Obtener bus genérico
            bus = obtener_bus()
            
            # Obtener motor
            self.motor = obtener_motor_prediccion(bus)
            self.disponible = True
            
            logger.info("[PREDICTION_ENGINE] Motor de predicción disponible")
            
        except ImportError as e:
            logger.debug(f"[PREDICTION_ENGINE] Motor no disponible (ImportError): {e}")
            self.disponible = False
        except Exception as e:
            logger.debug(f"[PREDICTION_ENGINE] Error cargando motor: {e}")
            self.disponible = False
    
    def cargar_modelo(self, nombre: str, ruta: str, variables: list, horizonte: int = 5) -> bool:
        """
        Carga un modelo LSTM
        
        Args:
            nombre: Nombre del modelo (ej: "utci", "precipitacion")
            ruta: Ruta al archivo del modelo
            variables: Variables del bus necesarias como entrada
            horizonte: Minutos que predice hacia adelante
        
        Returns:
            True si se cargó exitosamente
        """
        if not self.disponible or self.motor is None:
            logger.warning(f"[PREDICTION_ENGINE] No se puede cargar modelo '{nombre}': motor no disponible")
            return False
        
        try:
            self.motor.cargar_modelo(nombre, ruta, variables, horizonte)
            self.modelos_cargados += 1
            logger.info(f"[PREDICTION_ENGINE] Modelo '{nombre}' cargado exitosamente")
            return True
        except Exception as e:
            logger.warning(f"[PREDICTION_ENGINE] Error cargando modelo '{nombre}': {e}")
            return False
    
    def ejecutar_predicciones(self) -> Dict:
        """
        Ejecuta todas las predicciones disponibles
        
        Returns:
            Dict con resultados {nombre_modelo: valor_predicho}
        """
        resultados = {}
        
        if not self.disponible or self.motor is None:
            return resultados
        
        if not self.motor.modelos:
            return resultados
        
        try:
            for nombre_modelo in self.motor.modelos.keys():
                try:
                    prediccion = self.motor.predecir(nombre_modelo)
                    
                    if prediccion is not None:
                        resultados[nombre_modelo] = prediccion
                        self.predicciones_ejecutadas += 1
                        
                        logger.debug(f"[PREDICTION_ENGINE] Predicción {nombre_modelo}: {prediccion:.2f}")
                
                except Exception as e:
                    logger.debug(f"[PREDICTION_ENGINE] Error prediciendo {nombre_modelo}: {e}")
            
            return resultados
        
        except Exception as e:
            logger.error(f"[PREDICTION_ENGINE] Error ejecutando predicciones: {e}")
            return {}
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas del motor"""
        stats = {
            "disponible": self.disponible,
            "modelos_cargados": self.modelos_cargados,
            "predicciones_ejecutadas": self.predicciones_ejecutadas
        }
        
        if self.motor:
            stats.update(self.motor.obtener_estadisticas())
        
        return stats


# Instancia global
_integrador_global = None

def obtener_integrador_prediction_engine() -> IntegradorPredictionEngineV51:
    """Obtiene la instancia global del integrador"""
    global _integrador_global
    
    if _integrador_global is None:
        _integrador_global = IntegradorPredictionEngineV51()
    
    return _integrador_global
