"""
═══════════════════════════════════════════════════════════════════════════════
[STATS] FEEDBACK LEARNING V47.2 - REINFORCEMENT AUTOMÁTICO
═══════════════════════════════════════════════════════════════════════════════

Sistema de aprendizaje por refuerzo para predicciones.
Solo activo para parámetros con sensores verificables automáticamente.

Características:
  - Auto-detección de sensores disponibles
  - Registro automático de predicciones
  - Validación automática contra sensores
  - Ajuste de confianza progresivo (+/- puntos)
  - Cálculo de accuracy histórico
  - Auto-configuración para sensores futuros

Fecha: 2026-02-05
Versión: V47.2 SUMMUM
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import logging
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN: PARÁMETROS VERIFICABLES
# ═══════════════════════════════════════════════════════════════════════════

PARAMETROS_VERIFICABLES = {
    # Parámetro: configuración de verificación
    "temperatura": {
        "sensor": "DHT22",
        "frecuencia_h": 1.0,
        "umbral_acierto_absoluto": 0.5,  # ±0.5°C = acierto
        "umbral_acierto_relativo": None,
        "unidad": "°C",
        "feedback_viable": True,
        "tipo_validacion": "continuo",
    },
    "temperatura_minima": {
        "sensor": "DHT22",
        "frecuencia_h": 12.0,
        "umbral_acierto_absoluto": 0.5,
        "unidad": "°C",
        "feedback_viable": True,
        "tipo_validacion": "ventana",
    },
    "temperatura_maxima": {
        "sensor": "DHT22",
        "frecuencia_h": 12.0,
        "umbral_acierto_absoluto": 0.5,
        "unidad": "°C",
        "feedback_viable": True,
        "tipo_validacion": "ventana",
    },
    "humedad": {
        "sensor": "DHT22",
        "frecuencia_h": 1.0,
        "umbral_acierto_absoluto": 5.0,  # ±5%
        "unidad": "%",
        "feedback_viable": True,
        "tipo_validacion": "continuo",
    },
    "lluvia_acumulada": {
        "sensor": "Pluviómetro",
        "frecuencia_h": 0.083,  # 5 min
        "umbral_acierto_absoluto": 0.5,  # ±0.5 mm
        "unidad": "mm",
        "feedback_viable": True,
        "tipo_validacion": "acumulativo",
    },
    "probabilidad_lluvia": {
        "sensor": "Pluviómetro",
        "frecuencia_h": 3.0,
        "umbral_acierto_absoluto": None,
        "unidad": "%",
        "feedback_viable": True,
        "tipo_validacion": "binario",  # Llovió o no
    },
    "viento_velocidad": {
        "sensor": "Anemómetro",
        "frecuencia_h": 0.017,  # 1 min
        "umbral_acierto_absoluto": 1.0,  # ±1 m/s
        "unidad": "m/s",
        "feedback_viable": True,
        "tipo_validacion": "continuo",
    },
    "viento_direccion": {
        "sensor": "Veleta",
        "frecuencia_h": 0.017,
        "umbral_acierto_absoluto": 22.5,  # ±22.5° (1 octante)
        "unidad": "°",
        "feedback_viable": True,
        "tipo_validacion": "continuo",
    },
    "radiacion_solar": {
        "sensor": "Piranómetro",
        "frecuencia_h": 0.017,
        "umbral_acierto_absoluto": 50,  # ±50 W/m²
        "unidad": "W/m²",
        "feedback_viable": True,
        "tipo_validacion": "continuo",
    },
    "humedad_suelo": {
        "sensor": "WH51",
        "frecuencia_h": 0.5,  # 30 min
        "umbral_acierto_absoluto": 3.0,  # ±3%
        "unidad": "%",
        "feedback_viable": True,
        "tipo_validacion": "continuo",
    },
    "presion": {
        "sensor": "BME280",
        "frecuencia_h": 1.0,
        "umbral_acierto_absoluto": 2.0,  # ±2 hPa
        "unidad": "hPa",
        "feedback_viable": True,
        "tipo_validacion": "continuo",
    },
    "et0": {
        "sensor": "Calculado",
        "frecuencia_h": 24.0,
        "umbral_acierto_absoluto": 0.5,  # ±0.5 mm
        "unidad": "mm",
        "feedback_viable": True,
        "tipo_validacion": "indirecto",
    },
    "utci": {
        "sensor": "Calculado",
        "frecuencia_h": 1.0,
        "umbral_acierto_absoluto": 1.0,  # ±1°C
        "unidad": "°C",
        "feedback_viable": True,
        "tipo_validacion": "indirecto",
    },
    
    # ─────────────────────────────────────────────────────────────────────
    # PARÁMETROS NO VERIFICABLES (Manual opcional)
    # ─────────────────────────────────────────────────────────────────────
    "niebla": {
        "sensor": None,
        "frecuencia_manual_año": 4,
        "feedback_viable": False,
        "razon": "Requiere sensor de visibilidad (10k€)",
    },
    "helada_visual": {
        "sensor": None,
        "frecuencia_manual_año": 4,
        "feedback_viable": False,
        "razon": "T<0 detecta helada, escarcha requiere inspección visual",
    },
    "granizo": {
        "sensor": None,
        "frecuencia_manual_año": 1,
        "feedback_viable": False,
        "razon": "Requiere sensor acústico o cámara",
    },
    "calima": {
        "sensor": None,
        "frecuencia_manual_año": 3,
        "feedback_viable": False,
        "razon": "Requiere sensor de aerosoles/visibilidad",
    },
}

# Sistema de puntuación para aciertos/errores
SISTEMA_PUNTUACION = {
    "ACIERTO_EXACTO": +15,          # Predicción perfecta
    "ACIERTO_BUENO": +10,           # Dentro del umbral
    "ACIERTO_ACEPTABLE": +5,        # Cerca del umbral
    "ERROR_PEQUEÑO": -3,            # Error tolerable
    "ERROR_MEDIO": -8,              # Error significativo
    "ERROR_GRANDE": -15,            # Error grave
    "ERROR_CRÍTICO": -25,           # Error crítico (ej: helada no predicha)
}


# ═══════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: FEEDBACK LEARNING V47.2
# ═══════════════════════════════════════════════════════════════════════════

class FeedbackLearningV472:
    """
    Sistema de aprendizaje por refuerzo para predicciones.
    
    Características:
    - Registro automático de predicciones
    - Validación automática contra sensores
    - Ajuste de confianza progresivo
    - Auto-configuración para sensores futuros
    """
    
    def __init__(self, bus=None, data_path: str = "data"):
        self.bus = bus
        self.data_path = Path(data_path)
        self.data_path.mkdir(exist_ok=True)
        
        # Estado de modelos (confianza, historial, accuracy)
        self.modelos = {}
        
        # Callbacks para obtener valores reales de sensores
        self.callbacks_sensores = {}
        
        # Cargar estado persistente
        self._cargar_estado()
        
        # Auto-configurar modelos para parámetros verificables
        self._auto_configurar_modelos()
        
        logger.info("[STATS] Feedback Learning V47.2 inicializado")
    
    # ═══════════════════════════════════════════════════════════════════════
    # AUTO-CONFIGURACIÓN
    # ═══════════════════════════════════════════════════════════════════════
    
    def _auto_configurar_modelos(self):
        """
        Auto-configura modelos para todos los parámetros verificables.
        Preparado para sensores futuros.
        """
        for parametro, config in PARAMETROS_VERIFICABLES.items():
            if not config.get("feedback_viable", False):
                logger.info(
                    f"⏭️ Feedback DESACTIVADO para {parametro}: "
                    f"{config.get('razon', 'No verificable')}"
                )
                continue
            
            # Inicializar modelo si no existe
            if parametro not in self.modelos:
                self.modelos[parametro] = {
                    "confianza_base": 75.0,  # Confianza inicial
                    "predicciones": [],
                    "accuracy": 0.0,
                    "total_validaciones": 0,
                    "total_aciertos": 0,
                    "config": config,
                    "activo": True,
                }
                
                logger.info(
                    f"[OK] Feedback ACTIVO para {parametro} "
                    f"(sensor: {config['sensor']}, frecuencia: cada {config['frecuencia_h']*60:.0f} min)"
                )
    
    def registrar_callback_sensor(self, parametro: str, callback: Callable):
        """
        Registra callback para obtener valor real del sensor.
        
        Args:
            parametro: Nombre del parámetro
            callback: Función que retorna valor actual del sensor
                      Firma: () -> float
        
        Example:
            feedback.registrar_callback_sensor(
                "temperatura",
                lambda: bus.obtener("temperatura")
            )
        """
        self.callbacks_sensores[parametro] = callback
        logger.debug(f"📡 Callback registrado para {parametro}")
    
    def auto_detectar_sensores_futuros(self, nuevo_parametro: str, config: Dict):
        """
        Auto-configura feedback para sensor recién añadido.
        
        Args:
            nuevo_parametro: Nombre del parámetro (ej: "pm25_aire")
            config: Configuración del sensor
                {
                    "sensor": "PMS5003",
                    "frecuencia_h": 0.083,
                    "umbral_acierto_absoluto": 5.0,
                    "unidad": "µg/m³",
                    "feedback_viable": True,
                    "tipo_validacion": "continuo",
                }
        """
        if nuevo_parametro in PARAMETROS_VERIFICABLES:
            logger.warning(
                f"[WARNING] Parámetro {nuevo_parametro} ya existe. "
                f"Actualizando configuración."
            )
        
        # Agregar a configuración global
        PARAMETROS_VERIFICABLES[nuevo_parametro] = config
        
        # Auto-configurar modelo
        if config.get("feedback_viable", False):
            self.modelos[nuevo_parametro] = {
                "confianza_base": 75.0,
                "predicciones": [],
                "accuracy": 0.0,
                "total_validaciones": 0,
                "total_aciertos": 0,
                "config": config,
                "activo": True,
            }
            
            logger.critical(
                f"🆕 NUEVO SENSOR DETECTADO: {nuevo_parametro} "
                f"(sensor: {config['sensor']}). Feedback automático ACTIVADO."
            )
    
    # ═══════════════════════════════════════════════════════════════════════
    # REGISTRO DE PREDICCIONES
    # ═══════════════════════════════════════════════════════════════════════
    
    def registrar_prediccion(
        self,
        modelo: str,
        parametro: str,
        valor_predicho: float,
        ventana_validacion_h: float = None,
        metadatos: Dict = None
    ):
        """
        Registra predicción para validar posteriormente.
        
        Args:
            modelo: Nombre del modelo (ej: "deardorff_v47", "thompson", "wright")
            parametro: Parámetro predicho (ej: "temperatura_minima")
            valor_predicho: Valor predicho por el modelo
            ventana_validacion_h: Horas hasta validación (None = usar config)
            metadatos: Datos adicionales (ej: condiciones, probabilidad)
        """
        if parametro not in self.modelos:
            logger.debug(
                f"Parámetro {parametro} no tiene feedback activo. Ignorando predicción."
            )
            return
        
        if not self.modelos[parametro]["activo"]:
            return
        
        # Determinar ventana de validación
        if ventana_validacion_h is None:
            ventana_validacion_h = self.modelos[parametro]["config"]["frecuencia_h"]
        
        # Registrar predicción
        prediccion = {
            "modelo": modelo,
            "valor_predicho": valor_predicho,
            "timestamp": time.time(),
            "timestamp_validacion": time.time() + (ventana_validacion_h * 3600),
            "validado": False,
            "metadatos": metadatos or {},
        }
        
        self.modelos[parametro]["predicciones"].append(prediccion)
        
        logger.debug(
            f"📝 {modelo} → {parametro}: Predicción registrada "
            f"{valor_predicho:.2f} {self.modelos[parametro]['config']['unidad']} "
            f"(validar en {ventana_validacion_h}h)"
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # VALIDACIÓN AUTOMÁTICA
    # ═══════════════════════════════════════════════════════════════════════
    
    def validar_predicciones_pendientes(self):
        """
        Valida todas las predicciones cuya ventana ha expirado.
        Ejecutar periódicamente (ej: cada 5 minutos).
        """
        timestamp_actual = time.time()
        
        for parametro in self.modelos:
            if not self.modelos[parametro]["activo"]:
                continue
            
            for pred in self.modelos[parametro]["predicciones"]:
                if pred["validado"]:
                    continue
                
                if timestamp_actual < pred["timestamp_validacion"]:
                    continue  # Aún no llegó la ventana
                
                # Validar predicción
                self._validar_prediccion(parametro, pred)
    
    def _validar_prediccion(self, parametro: str, pred: Dict):
        """Valida predicción individual contra sensor real."""
        # Obtener valor real del sensor
        try:
            if parametro in self.callbacks_sensores:
                valor_real = self.callbacks_sensores[parametro]()
            else:
                logger.warning(
                    f"[WARNING] No hay callback para {parametro}. "
                    f"No se puede validar predicción."
                )
                pred["validado"] = True  # Marcar como validado para no reintentar
                return
        except Exception as e:
            logger.error(f"Error obteniendo valor real de {parametro}: {e}")
            return
        
        # Evaluar acierto
        config = self.modelos[parametro]["config"]
        tipo_validacion = config["tipo_validacion"]
        
        if tipo_validacion == "continuo":
            evaluacion = self._evaluar_continuo(
                pred["valor_predicho"],
                valor_real,
                config["umbral_acierto_absoluto"]
            )
        elif tipo_validacion == "binario":
            evaluacion = self._evaluar_binario(pred, valor_real)
        elif tipo_validacion == "ventana":
            evaluacion = self._evaluar_ventana(pred["valor_predicho"], valor_real, config)
        else:
            evaluacion = self._evaluar_continuo(
                pred["valor_predicho"],
                valor_real,
                config.get("umbral_acierto_absoluto", 1.0)
            )
        
        # Ajustar confianza del modelo
        self._ajustar_confianza(parametro, pred["modelo"], evaluacion)
        
        # Marcar como validado
        pred["validado"] = True
        pred["valor_real"] = valor_real
        pred["evaluacion"] = evaluacion
        
        # Guardar estado
        self._guardar_estado()
    
    def _evaluar_continuo(self, predicho: float, real: float, umbral: float) -> Dict:
        """Evalúa predicción continua (temperatura, humedad, etc.)"""
        error = abs(predicho - real)
        
        if error < umbral * 0.3:
            tipo = "ACIERTO_EXACTO"
        elif error < umbral:
            tipo = "ACIERTO_BUENO"
        elif error < umbral * 1.5:
            tipo = "ACIERTO_ACEPTABLE"
        elif error < umbral * 2.5:
            tipo = "ERROR_PEQUEÑO"
        elif error < umbral * 5:
            tipo = "ERROR_MEDIO"
        else:
            tipo = "ERROR_GRANDE"
        
        return {
            "tipo": tipo,
            "puntos": SISTEMA_PUNTUACION[tipo],
            "error": error,
            "predicho": predicho,
            "real": real,
        }
    
    def _evaluar_binario(self, pred: Dict, valor_real: float) -> Dict:
        """Evalúa predicción binaria (lluvia sí/no, helada sí/no)"""
        # Predicción binaria basada en probabilidad
        prob_predicha = pred["metadatos"].get("probabilidad", 50)
        predicho_si = prob_predicha > 50
        
        # Determinar si realmente ocurrió (ej: lluvia > 0.1 mm)
        real_si = valor_real > 0.1
        
        if predicho_si == real_si:
            if predicho_si:
                # Predijo SÍ y ocurrió
                tipo = "ACIERTO_EXACTO"
            else:
                # Predijo NO y no ocurrió
                tipo = "ACIERTO_BUENO"
        else:
            if real_si and not predicho_si:
                # No predijo, pero ocurrió (ERROR CRÍTICO)
                tipo = "ERROR_CRÍTICO"
            else:
                # Predijo, pero no ocurrió (ERROR MEDIO)
                tipo = "ERROR_MEDIO"
        
        return {
            "tipo": tipo,
            "puntos": SISTEMA_PUNTUACION[tipo],
            "predicho_si": predicho_si,
            "real_si": real_si,
            "probabilidad": prob_predicha,
        }
    
    def _evaluar_ventana(self, predicho: float, real: float, config: Dict) -> Dict:
        """Evalúa predicción de ventana (T_min, T_max)"""
        # Similar a continuo, pero con más tolerancia
        umbral = config["umbral_acierto_absoluto"] * 1.2  # +20% tolerancia
        return self._evaluar_continuo(predicho, real, umbral)
    
    def _ajustar_confianza(self, parametro: str, modelo: str, evaluacion: Dict):
        """Ajusta confianza del modelo basado en evaluación."""
        confianza_actual = self.modelos[parametro]["confianza_base"]
        puntos = evaluacion["puntos"]
        
        # Aplicar ajuste gradual (factor 0.1 para suavizar)
        delta_confianza = puntos * 0.1
        
        confianza_nueva = confianza_actual + delta_confianza
        confianza_nueva = max(30, min(99, confianza_nueva))  # Límites [30-99%]
        
        self.modelos[parametro]["confianza_base"] = confianza_nueva
        
        # Actualizar estadísticas
        self.modelos[parametro]["total_validaciones"] += 1
        if puntos > 0:
            self.modelos[parametro]["total_aciertos"] += 1
        
        # Recalcular accuracy
        total = self.modelos[parametro]["total_validaciones"]
        aciertos = self.modelos[parametro]["total_aciertos"]
        accuracy = (aciertos / total * 100) if total > 0 else 0
        self.modelos[parametro]["accuracy"] = accuracy
        
        # Publicar al Bus
        if self.bus:
            self.bus.publicar(f"feedback_{parametro}_confianza", confianza_nueva, "%")
            self.bus.publicar(f"feedback_{parametro}_accuracy", accuracy, "%")
            self.bus.publicar(f"feedback_{parametro}_validaciones", total, "eventos")
            self.bus.publicar(f"feedback_{modelo}_confianza", confianza_nueva, "%")
        
        # Log
        simbolo = "[OK]" if puntos > 0 else "[ERROR]"
        logger.info(
            f"{simbolo} {modelo} → {parametro}: {evaluacion['tipo']} "
            f"({puntos:+d} pts). Confianza: {confianza_actual:.1f}% → {confianza_nueva:.1f}%. "
            f"Accuracy: {accuracy:.1f}% ({aciertos}/{total})"
        )
    
    # ═══════════════════════════════════════════════════════════════════════
    # FEEDBACK MANUAL (Opcional, para parámetros no verificables)
    # ═══════════════════════════════════════════════════════════════════════
    
    def registrar_validacion_manual(
        self,
        parametro: str,
        modelo: str,
        predicho: bool,
        realidad: bool,
        timestamp: float = None
    ):
        """
        Permite validación manual para parámetros sin sensor.
        
        Args:
            parametro: "niebla", "helada_visual", "granizo", etc.
            modelo: Modelo que hizo la predicción
            predicho: True si predijo el evento
            realidad: True si ocurrió el evento
            timestamp: Timestamp del evento (None = ahora)
        """
        if parametro not in PARAMETROS_VERIFICABLES:
            logger.warning(f"Parámetro {parametro} no reconocido")
            return
        
        if parametro not in self.modelos:
            # Crear entrada manual
            self.modelos[parametro] = {
                "confianza_base": 75.0,
                "validaciones_manuales": [],
                "total_validaciones": 0,
                "total_aciertos": 0,
                "accuracy": 0.0,
                "config": PARAMETROS_VERIFICABLES[parametro],
                "activo": False,  # No activo para feedback automático
            }
        
        acierto = (predicho == realidad)
        
        self.modelos[parametro]["validaciones_manuales"].append({
            "modelo": modelo,
            "predicho": predicho,
            "realidad": realidad,
            "acierto": acierto,
            "timestamp": timestamp or time.time(),
        })
        
        self.modelos[parametro]["total_validaciones"] += 1
        if acierto:
            self.modelos[parametro]["total_aciertos"] += 1
        
        total = self.modelos[parametro]["total_validaciones"]
        aciertos = self.modelos[parametro]["total_aciertos"]
        accuracy = (aciertos / total * 100) if total > 0 else 0
        self.modelos[parametro]["accuracy"] = accuracy
        
        # Publicar al Bus (solo informativo)
        if self.bus:
            self.bus.publicar(f"validacion_manual_{parametro}_total", total, "eventos")
            self.bus.publicar(f"validacion_manual_{parametro}_accuracy", accuracy, "%")
        
        logger.info(
            f"📝 Validación manual {parametro}: {'[OK] ACIERTO' if acierto else '[ERROR] ERROR'}. "
            f"Accuracy manual: {accuracy:.1f}% ({aciertos}/{total})"
        )
        
        self._guardar_estado()
    
    # ═══════════════════════════════════════════════════════════════════════
    # OBTENER CONFIANZA
    # ═══════════════════════════════════════════════════════════════════════
    
    def obtener_confianza(self, parametro: str) -> Dict:
        """
        Obtiene confianza actual del parámetro.
        
        Returns:
            {
                "confianza": 82.5,
                "accuracy": 85.2,
                "total_validaciones": 150,
                "activo": True
            }
        """
        if parametro not in self.modelos:
            return {
                "confianza": 75.0,  # Default
                "accuracy": 0.0,
                "total_validaciones": 0,
                "activo": False,
            }
        
        return {
            "confianza": self.modelos[parametro]["confianza_base"],
            "accuracy": self.modelos[parametro]["accuracy"],
            "total_validaciones": self.modelos[parametro]["total_validaciones"],
            "activo": self.modelos[parametro]["activo"],
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # PERSISTENCIA
    # ═══════════════════════════════════════════════════════════════════════
    
    def _guardar_estado(self):
        """Guarda estado persistente a disco."""
        archivo = self.data_path / "feedback_learning_v472_estado.json"
        
        # Preparar datos para serialización (sin callbacks)
        datos_serializables = {}
        for parametro, datos in self.modelos.items():
            datos_serializables[parametro] = {
                k: v for k, v in datos.items()
                if k not in ["config"]  # Config se regenera en __init__
            }
        
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(datos_serializables, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando estado Feedback Learning V47.2: {e}")
    
    def _cargar_estado(self):
        """Carga estado persistente desde disco."""
        archivo = self.data_path / "feedback_learning_v472_estado.json"
        
        if not archivo.exists():
            logger.info("No hay estado previo Feedback Learning V47.2. Iniciando limpio.")
            return
        
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
            
            # Restaurar estado (config se agregará en auto_configurar)
            for parametro, datos_param in datos.items():
                self.modelos[parametro] = datos_param
            
            logger.info(
                f"[OK] Estado Feedback Learning V47.2 cargado: {len(self.modelos)} parámetros"
            )
        except Exception as e:
            logger.error(f"Error cargando estado Feedback Learning V47.2: {e}")
