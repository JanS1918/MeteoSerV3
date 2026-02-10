"""
Grabadores de histórico para aprendizaje del sistema.
Guardan ABSOLUTAMENTE TODO para que el sistema pueda aprender.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("meteoser.history_recorders")


class PredictionHistoryRecorder:
    """Guarda CADA predicción hecha para auditoría y validación."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
        self.historico_path = base_dir / "data" / "predicciones_historico.jsonl"
    
    def guardar_prediccion(
        self,
        timestamp: float,
        motor_id: str,
        predicciones: Dict[str, Any],
        confianza: float = 0.0,
        contexto: Optional[Dict] = None
    ) -> None:
        """
        Guarda una predicción hecha por cualquier motor.
        
        Args:
            timestamp: Momento de la predicción
            motor_id: ID del motor (ej: "MotorPrediccionLocal", "MotorViento")
            predicciones: Dict con las predicciones
            confianza: Confianza global de la predicción (0-1)
            contexto: Contexto adicional (ej: datos de entrada)
        """
        record = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "motor": motor_id,
            "predicciones": predicciones,
            "confianza": confianza,
            "contexto": contexto or {}
        }
        
        try:
            # Append-only: agregar a archivo existente
            with open(self.historico_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.debug(f"Predicción guardada: {motor_id} en {timestamp}")
        except Exception as e:
            logger.error(f"Error guardando predicción: {e}")


class IndicesHistoryRecorder:
    """Guarda CADA cálculo de índices para auditoría de fórmulas."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
        self.historico_path = base_dir / "data" / "indices_historico.jsonl"
    
    def guardar_indices(
        self,
        timestamp: float,
        indices: Dict[str, Any],
        datos_entrada: Optional[Dict] = None,
        formula_usada: Optional[Dict] = None
    ) -> None:
        """
        Guarda índices calculados.
        
        Args:
            timestamp: Momento del cálculo
            indices: Dict con los índices (UTCI, rocío, Steadman, etc)
            datos_entrada: Temperatura, humedad, presión usados
            formula_usada: Qué fórmula se usó para cada índice
        """
        record = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "indices": indices,
            "datos_entrada": datos_entrada or {},
            "formula_usada": formula_usada or {}
        }
        
        try:
            with open(self.historico_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.debug(f"Índices guardados en {timestamp}")
        except Exception as e:
            logger.error(f"Error guardando índices: {e}")


class AlertHistoryRecorder:
    """Guarda CADA alerta generada para auditoría."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
        self.historico_path = base_dir / "data" / "alertas_historico.jsonl"
    
    def guardar_alerta(
        self,
        timestamp: float,
        tipo_alerta: str,
        nivel: str,
        valor_actual: float,
        umbral: float,
        sensor: str,
        accion_recomendada: str = "",
        confirmada: Optional[bool] = None
    ) -> None:
        """
        Guarda una alerta generada.
        
        Args:
            timestamp: Momento de la alerta
            tipo_alerta: Tipo (ej: "viento_alto", "temperatura_extrema")
            nivel: "rojo" | "naranja" | "amarillo" | "verde"
            valor_actual: Valor medido
            umbral: Umbral que se superó
            sensor: Sensor que disparó (ej: "windspeedmph_original")
            accion_recomendada: Qué hacer
            confirmada: Si el usuario confirmó que fue correcta
        """
        record = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "tipo": tipo_alerta,
            "nivel": nivel,
            "valor": valor_actual,
            "umbral": umbral,
            "sensor": sensor,
            "accion": accion_recomendada,
            "confirmada": confirmada
        }
        
        try:
            with open(self.historico_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.debug(f"Alerta guardada: {tipo_alerta} nivel {nivel}")
        except Exception as e:
            logger.error(f"Error guardando alerta: {e}")


class DuelHistoryRecorder:
    """Guarda resultado de CADA duelo de fórmulas."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
        self.historico_path = base_dir / "data" / "duelos_historico.jsonl"
    
    def guardar_duelo(
        self,
        timestamp: float,
        parametro: str,
        formula_a: Dict[str, Any],
        formula_b: Dict[str, Any],
        resultado_a: float,
        resultado_b: float,
        datos_entrada: Dict[str, Any],
        ganador: str,
        diferencia: float,
        razon_victoria: str = ""
    ) -> None:
        """
        Guarda resultado de un duelo entre fórmulas.
        
        Args:
            timestamp: Momento del duelo
            parametro: Qué se está calculando (ej: "sensacion_termica")
            formula_a: Metadata de fórmula A
            formula_b: Metadata de fórmula B
            resultado_a: Resultado de fórmula A
            resultado_b: Resultado de fórmula B
            datos_entrada: Datos usados (T, H, P, etc)
            ganador: Nombre de la fórmula ganadora
            diferencia: Diferencia absoluta entre resultados
            razon_victoria: Por qué ganó
        """
        record = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "parametro": parametro,
            "formula_a": {
                "nombre": formula_a.get("nombre_tecnico", "desconocida"),
                "nivel": formula_a.get("nivel", "FALLBACK"),
                "resultado": resultado_a
            },
            "formula_b": {
                "nombre": formula_b.get("nombre_tecnico", "desconocida"),
                "nivel": formula_b.get("nivel", "FALLBACK"),
                "resultado": resultado_b
            },
            "datos_entrada": datos_entrada,
            "ganador": ganador,
            "diferencia": diferencia,
            "razon": razon_victoria
        }
        
        try:
            with open(self.historico_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.debug(f"Duelo guardado: {parametro} - {ganador} gana")
        except Exception as e:
            logger.error(f"Error guardando duelo: {e}")


class FeedbackHistoryRecorder:
    """Guarda feedback del usuario sobre predicciones."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
        self.historico_path = base_dir / "data" / "feedback_usuario_historico.jsonl"
    
    def guardar_feedback(
        self,
        timestamp: float,
        tipo_feedback: str,
        prediccion_id: str,
        prediccion_original: Any,
        valor_real: Any,
        comentario: str = "",
        confianza_feedback: float = 1.0
    ) -> None:
        """
        Guarda feedback de usuario sobre predicción.
        
        Args:
            timestamp: Momento del feedback
            tipo_feedback: "correcta" | "incorrecta" | "parcial" | "incierta"
            prediccion_id: ID único de la predicción
            prediccion_original: Qué predijo el motor
            valor_real: Cuál fue el valor real
            comentario: Comentario del usuario
            confianza_feedback: Qué tan seguro está el usuario (0-1)
        """
        record = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "tipo": tipo_feedback,
            "prediccion_id": prediccion_id,
            "prediccion": prediccion_original,
            "realidad": valor_real,
            "comentario": comentario,
            "confianza_usuario": confianza_feedback
        }
        
        try:
            with open(self.historico_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.debug(f"Feedback guardado: {tipo_feedback}")
        except Exception as e:
            logger.error(f"Error guardando feedback: {e}")


class VirtualSensorHistoryRecorder:
    """Guarda CADA cálculo de sensores virtuales derivados."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
        self.historico_path = base_dir / "data" / "sensores_virtuales_historico.jsonl"
    
    def guardar_sensor_virtual(
        self,
        timestamp: float,
        nombre_sensor: str,
        valor: float,
        unidad: str,
        formula_nivel: str,
        datos_usados: Dict[str, Any]
    ) -> None:
        """
        Guarda cálculo de sensor virtual.
        
        Args:
            timestamp: Momento del cálculo
            nombre_sensor: Nombre (ej: "UTCI", "punto_rocio", "steadman")
            valor: Valor calculado
            unidad: Unidad (°C, %, etc)
            formula_nivel: Nivel de fórmula usada (ELITE, STANDARD, etc)
            datos_usados: Datos de entrada (T, H, P, etc)
        """
        record = {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "sensor": nombre_sensor,
            "valor": valor,
            "unidad": unidad,
            "formula_nivel": formula_nivel,
            "datos_usados": datos_usados
        }
        
        try:
            with open(self.historico_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.debug(f"Sensor virtual guardado: {nombre_sensor}={valor}{unidad}")
        except Exception as e:
            logger.error(f"Error guardando sensor virtual: {e}")


# Singleton global para acceso desde cualquier lado
_prediction_recorder = None
_indices_recorder = None
_alert_recorder = None
_duel_recorder = None
_feedback_recorder = None
_virtual_sensor_recorder = None


def get_recorders(base_dir: Optional[Path] = None):
    """Obtiene instancias de todos los recorders."""
    global _prediction_recorder, _indices_recorder, _alert_recorder
    global _duel_recorder, _feedback_recorder, _virtual_sensor_recorder
    
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[2]
    
    if _prediction_recorder is None:
        _prediction_recorder = PredictionHistoryRecorder(base_dir)
        _indices_recorder = IndicesHistoryRecorder(base_dir)
        _alert_recorder = AlertHistoryRecorder(base_dir)
        _duel_recorder = DuelHistoryRecorder(base_dir)
        _feedback_recorder = FeedbackHistoryRecorder(base_dir)
        _virtual_sensor_recorder = VirtualSensorHistoryRecorder(base_dir)
    
    return {
        "predicciones": _prediction_recorder,
        "indices": _indices_recorder,
        "alertas": _alert_recorder,
        "duelos": _duel_recorder,
        "feedback": _feedback_recorder,
        "sensores_virtuales": _virtual_sensor_recorder
    }
