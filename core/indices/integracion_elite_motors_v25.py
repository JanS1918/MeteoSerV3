"""
integracion_elite_motors_v25.py

Script de integración de los 6 motores de élite en el Bus de Estado Global
y en la cascada de las 26 predicciones (incluyendo Vector de Aproximación).

Este archivo coordina la inyección de variables maestras en el bus
y la reforma de las predicciones para consumirlas.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from core.indices.elite_motors_v25 import EliteMotorsV25
from core.indices.bucholtz_rayleigh_v25 import BucholtzRayleighV25
from core.indices.vector_aproximacion_v26 import VectorAproximacion
from core.indices.bus_estado_global import BusEstadoGlobal


logger = logging.getLogger(__name__)


class IntegracionMotoresV25:
    """Orquestador de la integración de motores de élite en la cascada"""
    
    def __init__(self):
        self.elite_motors = EliteMotorsV25()
        self.bucholtz = BucholtzRayleighV25()
        self.vector_aproximacion = VectorAproximacion()
        self.bus = BusEstadoGlobal()
    
    def ejecutar_ciclo_completo(self, sensores: Dict[str, Any], 
                               contexto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el ciclo completo de los 6 motores de élite y retorna
        todas las variables maestras para inyectar en el bus.
        """
        ciclo_timestamp = datetime.now().isoformat()
        
        logger.info(f"[V2.5] Iniciando ciclo de motores de élite: {ciclo_timestamp}")
        
        # Fase 1: Ejecutar motores de élite
        variables_maestras = self.elite_motors.ciclo_completo(sensores, contexto)
        
        # Fase 2: Ejecutar Visibilidad Bucholtz-Rayleigh reformulada
        masa_aire_type = variables_maestras.get("masas_de_aire", {}).get("tipo", "Templada")
        bucholtz_result = self.bucholtz.visibilidad_bucholtz_completa(
            sensores.get("temperatura", 15),
            sensores.get("presion", 1019.1),
            sensores.get("humedad", 60),
            contexto.get("angulo_cenital", 45),
            masa_aire_type
        )
        variables_maestras["visibilidad_bucholtz_v25"] = bucholtz_result
        
        # Fase 3: Ejecutar Vector de Aproximación (#26)
        tendencia_presion = contexto.get("tendencia_presion_hpa_h", 0)
        vector_result = self.vector_aproximacion.vector_final_aproximacion(
            sensores.get("presion", 1019.1),
            tendencia_presion,
            sensores.get("winddir", 0),
            sensores.get("viento", 0),
            sensores.get("radiacion", 0),
            contexto.get("radiacion_teorica", 100),
            contexto.get("azimut_solar", 180),
            contexto.get("angulo_cenital", 45),
            contexto.get("rayos_detectados", 0),
            contexto.get("rssi_promedio", -80)
        )
        variables_maestras["vector_aproximacion"] = vector_result
        
        # Fase 4: Publicar todas las variables maestras en el bus
        self._publicar_en_bus(variables_maestras, sensores, ciclo_timestamp)
        
        # Fase 5: Generar resumen de precisión
        resumen_precision = self._generar_resumen_precision(variables_maestras)
        
        logger.info(f"[V2.5] Ciclo completado. Precisión: {resumen_precision['consistencia']}")
        
        return {
            "timestamp": ciclo_timestamp,
            "variables_maestras": variables_maestras,
            "resumen_precision": resumen_precision,
            "estado_motores": "OPERACIONAL"
        }
    
    def _publicar_en_bus(self, variables: Dict[str, Any], 
                        sensores: Dict[str, Any], 
                        timestamp: str) -> None:
        """
        Publica todas las variables maestras de los motores en el Bus de Estado Global
        """
        # Publicar cada motor como variable maestra
        self.bus.publicar("masas_de_aire", variables.get("masas_de_aire", {}), 
                         {"source": "MotorMasasDeAire", "timestamp": timestamp})
        
        self.bus.publicar("capa_limite", variables.get("capa_limite", {}),
                         {"source": "MotorCapaLimite", "timestamp": timestamp})
        
        self.bus.publicar("temperatura_suelo", variables.get("temperatura_suelo", 0),
                         {"source": "MotorCapaLimite", "timestamp": timestamp})
        
        self.bus.publicar("opacidad_nubes", variables.get("opacidad_nubes", {}),
                         {"source": "MotorOpacidadNubes", "timestamp": timestamp})
        
        self.bus.publicar("ventilacion_tactica", variables.get("ventilacion_tactica", {}),
                         {"source": "MotorVentilacionTactica", "timestamp": timestamp})
        
        self.bus.publicar("autocalibration_estado", variables.get("autocalibration", {}),
                         {"source": "MotorAutocalibration", "timestamp": timestamp})
        
        self.bus.publicar("forense_estado", variables.get("forense", {}),
                         {"source": "MotorSimulacionForense", "timestamp": timestamp})
        
        # Publicar Visibilidad Bucholtz V2.5 (reemplaza la versión antigua)
        self.bus.publicar("visibilidad_bucholtz_v25", 
                         variables.get("visibilidad_bucholtz_v25", {}),
                         {"source": "BucholtzRayleighV25", "timestamp": timestamp,
                          "reemplaza": "visibilidad_kasten_hanel"})
        
        # Publicar Vector de Aproximación (#26)
        self.bus.publicar("vector_aproximacion", 
                         variables.get("vector_aproximacion", {}),
                         {"source": "VectorAproximacion", "timestamp": timestamp,
                          "prediccion_id": 26})
        
        logger.info("[V2.5] Variables maestras publicadas en el bus")
    
    def _generar_resumen_precision(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un informe de coherencia física de las predicciones"""
        autocalib = variables.get("autocalibration", {})
        chi_squared = autocalib.get("chi_squared", 0)
        
        consistencia = "EXCELENTE" if chi_squared < 10 else \
                      "BUENA" if chi_squared < 50 else "SOSPECHOSA"
        
        vector = variables.get("vector_aproximacion", {})
        alerta = vector.get("nivel_alerta", "✓ VERDE")
        
        return {
            "chi_squared": round(chi_squared, 2),
            "consistencia": consistencia,
            "alertas_activas": autocalib.get("alertas", []),
            "nivel_alerta_general": alerta,
            "motores_operacionales": 6,
            "predicciones_reformuladas": 26
        }


def integrar_motores_en_environmental_indices(env_indices_instance):
    """
    Función de inyección para integrar los motores de élite
    en la clase EnvironmentalIndices existente.
    
    Llamar desde environmental_indices.calcular_indices()
    """
    try:
        integracion = IntegracionMotoresV25()
        
        # Preparar sensores y contexto desde env_indices_instance
        sensores = {
            "temperatura": env_indices_instance._get_sensor("temperatura", {}).get("valor", 15),
            "presion": env_indices_instance._get_sensor("presion", {}).get("valor", 1019.1),
            "humedad": env_indices_instance._get_sensor("humedad", {}).get("valor", 60),
            "viento": env_indices_instance._get_sensor("viento", {}).get("valor", 5),
            "winddir": env_indices_instance._get_sensor("winddir", {}).get("valor", 0),
            "radiacion": env_indices_instance._get_sensor("radiacion", {}).get("valor", 0),
        }
        
        contexto = {
            "altura_mast": getattr(env_indices_instance.system.contexto, 'sensor_height_above_ground', 13),
            "altura_ground": 0,
            "radiacion_nocturna": 50,
            "estabilidad_monin": 0,
            "angulo_cenital": 45,
            "tendencia_presion_hpa_h": 0,
            "azimut_solar": 180,
            "rayos_detectados": 0,
            "rssi_promedio": -80
        }
        
        # Ejecutar ciclo completo
        resultado = integracion.ejecutar_ciclo_completo(sensores, contexto)
        
        # Almacenar resultado en el sistema para posterior acceso
        env_indices_instance.motores_elite_resultado = resultado
        
        logger.info("[V2.5] Motores de élite integrados exitosamente")
        return resultado
        
    except Exception as e:
        logger.error(f"[V2.5] Error en integración de motores: {e}")
        return None
