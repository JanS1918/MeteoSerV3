"""
═══════════════════════════════════════════════════════════════════════════════
🔗 INTEGRADOR V47.2 - MOS + FEEDBACK LEARNING
═══════════════════════════════════════════════════════════════════════════════

Orquesta la integración de:
  - MOS Clustering V47.2 (corrección de valores numéricos)
  - Feedback Learning V47.2 (confianza de modelos)
  - Publicación al Bus (valores corregidos + confianzas)
  - Auto-configuración de sensores futuros

Fecha: 2026-02-05
Versión: V47.2 SUMMUM
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
import time
from pathlib import Path
from typing import Dict, Optional

from core.validation.mos_clustering_v472 import MOSClusteringV472
from core.learning.feedback_learning_v472 import FeedbackLearningV472

logger = logging.getLogger(__name__)


class IntegradorV472:
    """
    Orquestador central para MOS + Feedback Learning.
    
    Funciones:
    - Integra correcciones MOS con confianzas Feedback
    - Publica valores corregidos al Bus
    - Auto-configura sensores futuros
    - Mantiene coherencia entre subsistemas
    """
    
    def __init__(self, bus=None, data_path: str = "data"):
        self.bus = bus
        self.data_path = Path(data_path)
        
        # Subsistemas
        self.mos = MOSClusteringV472(bus=bus, data_path=str(self.data_path))
        self.feedback = FeedbackLearningV472(bus=bus, data_path=str(self.data_path))
        
        # Registrar callbacks de sensores
        self._registrar_callbacks_sensores()
        
        logger.info("🔗 Integrador V47.2 inicializado (MOS + Feedback)")
    
    # ═══════════════════════════════════════════════════════════════════════
    # CALLBACKS SENSORES
    # ═══════════════════════════════════════════════════════════════════════
    
    def _registrar_callbacks_sensores(self):
        """
        Registra callbacks para obtener valores reales de sensores.
        Auto-configurable para sensores futuros.
        """
        if not self.bus:
            logger.warning("[WARNING] Bus no disponible. Callbacks de sensores no registrados.")
            return
        
        # Temperatura
        self.feedback.registrar_callback_sensor(
            "temperatura",
            lambda: self.bus.obtener("temperatura", 0.0)
        )
        self.feedback.registrar_callback_sensor(
            "temperatura_minima",
            lambda: self.bus.obtener("temperatura_minima_dia", 0.0)
        )
        self.feedback.registrar_callback_sensor(
            "temperatura_maxima",
            lambda: self.bus.obtener("temperatura_maxima_dia", 0.0)
        )
        
        # Humedad
        self.feedback.registrar_callback_sensor(
            "humedad",
            lambda: self.bus.obtener("humedad", 0.0)
        )
        
        # Lluvia
        self.feedback.registrar_callback_sensor(
            "lluvia_acumulada",
            lambda: self.bus.obtener("lluvia_acumulada", 0.0)
        )
        self.feedback.registrar_callback_sensor(
            "probabilidad_lluvia",
            lambda: 1.0 if self.bus.obtener("lluvia_acumulada", 0.0) > 0.1 else 0.0
        )
        
        # Viento
        self.feedback.registrar_callback_sensor(
            "viento_velocidad",
            lambda: self.bus.obtener("viento_velocidad", 0.0)
        )
        self.feedback.registrar_callback_sensor(
            "viento_direccion",
            lambda: self.bus.obtener("viento_direccion", 0.0)
        )
        
        # Radiación
        self.feedback.registrar_callback_sensor(
            "radiacion_solar",
            lambda: self.bus.obtener("radiacion_solar", 0.0)
        )
        
        # Humedad suelo
        self.feedback.registrar_callback_sensor(
            "humedad_suelo",
            lambda: self.bus.obtener("humedad_suelo", 0.0)
        )
        
        # Presión
        self.feedback.registrar_callback_sensor(
            "presion",
            lambda: self.bus.obtener("presion", 0.0)
        )
        
        # ET0 (calculado)
        self.feedback.registrar_callback_sensor(
            "et0",
            lambda: self.bus.obtener("et0_diario", 0.0)
        )
        
        # UTCI (calculado)
        self.feedback.registrar_callback_sensor(
            "utci",
            lambda: self.bus.obtener("utci", 0.0)
        )
        
        logger.info("[OK] Callbacks de sensores registrados")
    
    # ═══════════════════════════════════════════════════════════════════════
    # PREDICCIÓN CON CORRECCIÓN INTEGRADA
    # ═══════════════════════════════════════════════════════════════════════
    
    def predecir_con_correccion(
        self,
        modelo: str,
        parametro: str,
        valor_teorico: float,
        condiciones: Dict,
        ventana_validacion_h: Optional[float] = None
    ) -> Dict:
        """
        Realiza predicción con corrección MOS y tracking de feedback.
        
        Args:
            modelo: Nombre del modelo ("deardorff_v47", "wright", "thompson", etc.)
            parametro: Parámetro predicho ("temperatura_minima", "et0", etc.)
            valor_teorico: Valor predicho por el modelo (sin corrección)
            condiciones: Condiciones meteorológicas actuales
            ventana_validacion_h: Horas hasta validación (None = auto)
        
        Returns:
            {
                "valor_teorico": 8.5,
                "valor_corregido": 8.2,
                "bias_aplicado": -0.3,
                "confianza_mos": 99.7,
                "confianza_modelo": 85.2,
                "escenario": "ALFA",
                "estado_mos": "ACTIVA",
            }
        """
        # Obtener corrección MOS
        correccion_mos = self.mos.obtener_correccion(parametro, condiciones)
        
        if correccion_mos:
            # Aplicar corrección
            valor_corregido = valor_teorico + correccion_mos["bias"]
            
            resultado = {
                "valor_teorico": valor_teorico,
                "valor_corregido": valor_corregido,
                "bias_aplicado": correccion_mos["bias"],
                "confianza_mos": correccion_mos["confianza"],
                "escenario": correccion_mos["escenario"],
                "estado_mos": correccion_mos["estado"],
            }
        else:
            # Sin corrección disponible
            valor_corregido = valor_teorico
            
            resultado = {
                "valor_teorico": valor_teorico,
                "valor_corregido": valor_corregido,
                "bias_aplicado": 0.0,
                "confianza_mos": 0.0,
                "escenario": "N/A",
                "estado_mos": "APRENDIENDO",
            }
        
        # Obtener confianza del modelo (Feedback Learning)
        confianza_modelo = self.feedback.obtener_confianza(parametro)
        resultado["confianza_modelo"] = confianza_modelo["confianza"]
        resultado["accuracy_modelo"] = confianza_modelo["accuracy"]
        
        # Registrar predicción en ambos subsistemas
        # MOS: Para aprender BIAS
        self.mos.registrar_prediccion(
            parametro=parametro,
            valor_predicho=valor_teorico,  # Valor teórico (sin corrección)
            condiciones=condiciones,
            ventana_validacion_h=ventana_validacion_h or 12
        )
        
        # Feedback: Para aprender confianza del modelo
        self.feedback.registrar_prediccion(
            modelo=modelo,
            parametro=parametro,
            valor_predicho=valor_corregido,  # Valor corregido (con MOS)
            ventana_validacion_h=ventana_validacion_h,
            metadatos={"valor_teorico": valor_teorico, "condiciones": condiciones}
        )
        
        # Publicar al Bus
        self._publicar_resultado(parametro, resultado)
        
        return resultado
    
    def _publicar_resultado(self, parametro: str, resultado: Dict):
        """Publica valores corregidos y confianzas al Bus."""
        if not self.bus:
            return
        
        # Valor teórico
        self.bus.publicar(f"{parametro}_teorico", resultado["valor_teorico"], "unidad")
        
        # Valor corregido (PRINCIPAL)
        self.bus.publicar(f"{parametro}_corregido", resultado["valor_corregido"], "unidad")
        
        # Confianzas
        self.bus.publicar(f"{parametro}_confianza_mos", resultado["confianza_mos"], "%")
        self.bus.publicar(f"{parametro}_confianza_modelo", resultado["confianza_modelo"], "%")
        self.bus.publicar(f"{parametro}_accuracy", resultado.get("accuracy_modelo", 0.0), "%")
        
        # Metadatos MOS
        self.bus.publicar(f"{parametro}_bias_aplicado", resultado["bias_aplicado"], "unidad")
        self.bus.publicar(f"{parametro}_escenario_mos", resultado["escenario"], "estado")
        self.bus.publicar(f"{parametro}_estado_mos", resultado["estado_mos"], "estado")
    
    # ═══════════════════════════════════════════════════════════════════════
    # VALIDACIÓN PERIÓDICA
    # ═══════════════════════════════════════════════════════════════════════
    
    def validar_predicciones_pendientes(self):
        """
        Ejecuta validación de predicciones pendientes.
        Llamar periódicamente (ej: cada 5 minutos).
        """
        # MOS: Validar contra sensores (para calcular BIAS)
        def obtener_valor_real_mos(parametro: str) -> float:
            """Callback para MOS: obtiene valor real del sensor."""
            if parametro in self.feedback.callbacks_sensores:
                return self.feedback.callbacks_sensores[parametro]()
            raise ValueError(f"No hay callback para {parametro}")
        
        self.mos.validar_predicciones_pendientes(obtener_valor_real_mos)
        
        # Feedback: Validar predicciones (para calcular confianza)
        self.feedback.validar_predicciones_pendientes()
        
        # Validación estacional (ejecutar cada 3 meses)
        self.mos.validacion_estacional_automatica()
        
        # Monitoreo de DRIFT (ejecutar cada 30 días)
        for parametro in self.mos.parametros_mos:
            for escenario in ["ALFA", "BETA", "GAMMA", "DELTA"]:
                self.mos.monitorear_drift_bias(parametro, escenario)
        
        # Auditoría global (ejecutar cuando todos completen)
        for parametro in self.mos.parametros_mos:
            self.mos.auditoria_global_consistencia(parametro)
    
    # ═══════════════════════════════════════════════════════════════════════
    # AUTO-CONFIGURACIÓN SENSORES FUTUROS
    # ═══════════════════════════════════════════════════════════════════════
    
    def registrar_sensor_nuevo(
        self,
        parametro: str,
        sensor: str,
        frecuencia_h: float,
        umbral_acierto: float,
        unidad: str,
        callback_sensor: callable
    ):
        """
        Auto-configura feedback para sensor recién añadido.
        
        Example:
            integrador.registrar_sensor_nuevo(
                parametro="pm25_aire",
                sensor="PMS5003",
                frecuencia_h=0.083,
                umbral_acierto=5.0,
                unidad="µg/m³",
                callback_sensor=lambda: bus.obtener("pm25", 0.0)
            )
        """
        # Configurar en Feedback Learning
        config = {
            "sensor": sensor,
            "frecuencia_h": frecuencia_h,
            "umbral_acierto_absoluto": umbral_acierto,
            "unidad": unidad,
            "feedback_viable": True,
            "tipo_validacion": "continuo",
        }
        
        self.feedback.auto_detectar_sensores_futuros(parametro, config)
        self.feedback.registrar_callback_sensor(parametro, callback_sensor)
        
        logger.critical(
            f"🆕 SENSOR NUEVO REGISTRADO: {parametro} ({sensor}). "
            f"MOS + Feedback Learning AUTO-CONFIGURADO."
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # ESTADÍSTICAS
    # ═══════════════════════════════════════════════════════════════════════
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas completas del sistema.
        
        Returns:
            {
                "mos": {
                    "temperatura_minima": {
                        "ALFA": {"activa": True, "bias": -0.30, "confianza": 99.7},
                        ...
                    },
                    ...
                },
                "feedback": {
                    "temperatura": {"confianza": 85.2, "accuracy": 88.5},
                    ...
                }
            }
        """
        estadisticas = {
            "mos": {},
            "feedback": {},
            "timestamp": time.time(),
        }
        
        # MOS
        for parametro in self.mos.parametros_mos:
            estadisticas["mos"][parametro] = {}
            for escenario in ["ALFA", "BETA", "GAMMA", "DELTA"]:
                esc_data = self.mos.parametros_mos[parametro]["escenarios"][escenario]
                estadisticas["mos"][parametro][escenario] = {
                    "activa": esc_data["activa"],
                    "bias": esc_data["bias_promedio"],
                    "confianza": esc_data["confianza"],
                    "std_dev": esc_data["std_dev"],
                    "eventos": esc_data["contador"],
                }
        
        # Feedback
        for parametro in self.feedback.modelos:
            estadisticas["feedback"][parametro] = self.feedback.obtener_confianza(parametro)
        
        return estadisticas
