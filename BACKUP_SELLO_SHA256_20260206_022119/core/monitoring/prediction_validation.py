"""
Sistema de validación y feedback automático para aprendizaje.

COMPONENTES CRÍTICOS:
1. PredictionValidator - Compara predicción vs realidad
2. AutomaticFeedbackGenerator - Genera feedback automático
3. Integración en el flujo principal
"""

import json
import logging
import time
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("meteoser.prediction_validation")


class PredictionValidator:
    """
    Valida predicciones comparándolas con datos reales.
    Calcula métricas de error (MAE, RMSE, MAPE).
    Genera feedback automático.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
        self.predicciones_path = base_dir / "data" / "predicciones_historico.jsonl"
        self.sensores_path = base_dir / "data" / "sensores_historico.json"
        self.validaciones_path = base_dir / "data" / "validaciones_predicciones.jsonl"
        self.metricas_path = base_dir / "data" / "metricas_validacion.json"
    
    def validar_predicciones_pendientes(self, ventana_horas: int = 24) -> List[Dict[str, Any]]:
        """
        Valida predicciones que ya tienen datos reales disponibles.
        
        Args:
            ventana_horas: Cuántas horas después validar (por defecto 24h)
        
        Returns:
            Lista de validaciones realizadas
        """
        if not self.predicciones_path.exists() or not self.sensores_path.exists():
            return []
        
        validaciones = []
        ventana_segundos = ventana_horas * 3600
        ahora = time.time()
        
        try:
            # Leer predicciones
            predicciones_raw = self.predicciones_path.read_text(encoding="utf-8").strip().split("\n")
            predicciones = [json.loads(line) for line in predicciones_raw if line]
            
            # Leer datos reales (sensores históricos)
            sensores_raw = json.loads(self.sensores_path.read_text(encoding="utf-8"))
            
            # Para cada predicción, buscar si hay datos reales después de X horas
            for pred in predicciones:
                ts_pred = pred.get("timestamp")
                ts_validacion = ts_pred + ventana_segundos
                
                # Si aún no han pasado X horas, no validar
                if ts_validacion > ahora:
                    continue
                
                # Buscar datos reales cercanos al tiempo de validación
                datos_reales = self._buscar_datos_reales(sensores_raw, ts_validacion, ventana_segundos // 10)
                
                if not datos_reales:
                    continue
                
                # Comparar predicciones vs realidad
                predicciones_vals = pred.get("predicciones", {})
                
                # Extender: solo validar si la predicción tiene campos reconocibles
                validacion = self._comparar_prediccion(
                    timestamp_pred=ts_pred,
                    prediccion=predicciones_vals,
                    realidad=datos_reales,
                    motor_id=pred.get("motor", "desconocido")
                )
                
                if validacion:
                    validaciones.append(validacion)
                    self._guardar_validacion(validacion)
        
        except Exception as e:
            logger.error(f"Error validando predicciones: {e}")
        
        return validaciones
    
    def _buscar_datos_reales(self, sensores_raw: List, ts_target: float, tolerancia_segundos: int) -> Optional[Dict]:
        """Busca datos reales más cercanos a un timestamp objetivo."""
        if not isinstance(sensores_raw, list) or len(sensores_raw) == 0:
            return None
        
        mejor = None
        mejor_diff = float('inf')
        
        for record in sensores_raw:
            ts_record = record.get("timestamp")
            if ts_record is None:
                continue
            
            diff = abs(ts_record - ts_target)
            if diff < mejor_diff and diff <= tolerancia_segundos:
                mejor_diff = diff
                mejor = record
        
        return mejor.get("sensores", {}) if mejor else None
    
    def _comparar_prediccion(
        self,
        timestamp_pred: float,
        prediccion: Dict[str, Any],
        realidad: Dict[str, Any],
        motor_id: str
    ) -> Optional[Dict]:
        """
        Compara una predicción con datos reales.
        Calcula métricas de error.
        """
        if not prediccion or not realidad:
            return None
        
        errores = {}
        campo_validable = False
        
        # Campos que típicamente predecimos
        campos_prediccion = ["temperatura_mañana", "humedad_mañana", "viento_mañana", "probabilidad_lluvia"]
        
        for campo_pred in campos_prediccion:
            if campo_pred not in prediccion:
                continue
            
            # Mapear campo predicción a campo real
            campo_real = self._mapear_campo_prediccion_realidad(campo_pred)
            if campo_real not in realidad:
                continue
            
            val_pred = prediccion[campo_pred]
            val_real = realidad[campo_real]
            
            if val_pred is None or val_real is None:
                continue
            
            try:
                val_pred = float(val_pred)
                val_real = float(val_real)
                
                error_abs = abs(val_pred - val_real)
                error_rel = (error_abs / abs(val_real)) * 100 if val_real != 0 else 0
                
                errores[campo_pred] = {
                    "prediccion": val_pred,
                    "realidad": val_real,
                    "error_absoluto": error_abs,
                    "error_relativo": error_rel
                }
                campo_validable = True
            except (ValueError, TypeError):
                continue
        
        if not campo_validable:
            return None
        
        # Calcular métricas globales
        errores_abs = [e["error_absoluto"] for e in errores.values()]
        mae = statistics.mean(errores_abs) if errores_abs else 0
        rmse = (sum(e**2 for e in errores_abs) / len(errores_abs))**0.5 if errores_abs else 0
        
        # Determinar si fue correcta
        es_correcta = mae < 2.0  # Umbral: error menor a 2 unidades
        
        return {
            "timestamp": time.time(),
            "timestamp_prediccion": timestamp_pred,
            "motor": motor_id,
            "errores_por_campo": errores,
            "mae": mae,
            "rmse": rmse,
            "correcta": es_correcta,
            "tipo_feedback": "correcta" if es_correcta else "incorrecta",
            "confianza": 1.0 - min(mae / 10, 1.0)  # Confianza basada en MAE
        }
    
    def _mapear_campo_prediccion_realidad(self, campo_pred: str) -> str:
        """Mapea nombres de campos de predicción a nombres de sensores reales."""
        mapeo = {
            "temperatura_mañana": "temperatura",
            "humedad_mañana": "humedad",
            "viento_mañana": "viento",
            "presion_mañana": "presion",
        }
        return mapeo.get(campo_pred, campo_pred)
    
    def _guardar_validacion(self, validacion: Dict) -> None:
        """Guarda resultado de validación en archivo."""
        try:
            with open(self.validaciones_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(validacion, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Error guardando validación: {e}")


class AutomaticFeedbackGenerator:
    """
    Genera feedback automático basado en validaciones.
    Lee validaciones y las convierte en feedback para aprendizaje.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
        self.validaciones_path = base_dir / "data" / "validaciones_predicciones.jsonl"
        self.feedback_path = base_dir / "data" / "feedback_usuario_historico.jsonl"
        self.feedback_stats_path = base_dir / "data" / "feedback_estadisticas.json"
    
    def generar_feedback_desde_validaciones(self) -> int:
        """
        Lee validaciones y genera feedback automático.
        Retorna cantidad de feedback generado.
        """
        if not self.validaciones_path.exists():
            return 0
        
        count = 0
        stats = {
            "total_validaciones": 0,
            "feedback_generado": 0,
            "correctas": 0,
            "incorrectas": 0,
            "mae_promedio": 0.0,
            "confianza_promedio": 0.0
        }
        
        try:
            validaciones_raw = self.validaciones_path.read_text(encoding="utf-8").strip().split("\n")
            validaciones = [json.loads(line) for line in validaciones_raw if line]
            
            maes = []
            confianzas = []
            
            for validacion in validaciones:
                # Generar ID único para la predicción
                pred_id = f"pred_{validacion['timestamp_prediccion']:.0f}_{validacion['motor']}"
                
                # Crear feedback automático
                feedback = {
                    "timestamp": time.time(),
                    "tipo": validacion["tipo_feedback"],
                    "prediccion_id": pred_id,
                    "prediccion": {k: v["prediccion"] for k, v in validacion["errores_por_campo"].items()},
                    "realidad": {k: v["realidad"] for k, v in validacion["errores_por_campo"].items()},
                    "comentario": f"Validación automática: MAE={validacion['mae']:.2f}",
                    "confianza_usuario": validacion["confianza"],
                    "origen": "sistema_automatico",
                    "motor_origen": validacion["motor"]
                }
                
                # Guardar feedback
                self._guardar_feedback(feedback)
                count += 1
                
                # Recopilar estadísticas
                stats["feedback_generado"] += 1
                if validacion["correcta"]:
                    stats["correctas"] += 1
                else:
                    stats["incorrectas"] += 1
                
                maes.append(validacion["mae"])
                confianzas.append(validacion["confianza"])
            
            stats["total_validaciones"] = len(validaciones)
            stats["mae_promedio"] = statistics.mean(maes) if maes else 0
            stats["confianza_promedio"] = statistics.mean(confianzas) if confianzas else 0
            
            # Guardar estadísticas
            self._guardar_estadisticas(stats)
            
            logger.info(f"Feedback automático generado: {count} registros")
        
        except Exception as e:
            logger.error(f"Error generando feedback: {e}")
        
        return count
    
    def _guardar_feedback(self, feedback: Dict) -> None:
        """Guarda feedback en histórico."""
        try:
            with open(self.feedback_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(feedback, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Error guardando feedback: {e}")
    
    def _guardar_estadisticas(self, stats: Dict) -> None:
        """Guarda estadísticas de feedback."""
        try:
            self.feedback_stats_path.write_text(
                json.dumps(stats, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Error guardando estadísticas: {e}")


class LearningLoopValidator:
    """
    Valida que el loop de aprendizaje esté funcionando.
    Genera reportes de salud del aprendizaje.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        
        self.base_dir = base_dir
    
    def generar_reporte_aprendizaje(self) -> Dict[str, Any]:
        """Genera reporte completo del estado del aprendizaje."""
        reporte = {
            "timestamp": datetime.now().isoformat(),
            "componentes": {}
        }
        
        # 1. Estado de predicciones
        pred_path = self.base_dir / "data" / "predicciones_historico.jsonl"
        if pred_path.exists():
            count = len(pred_path.read_text().strip().split("\n"))
            reporte["componentes"]["predicciones"] = {
                "archivo": "predicciones_historico.jsonl",
                "registros": count,
                "status": "OK" if count > 0 else "VACIO"
            }
        
        # 2. Estado de validaciones
        val_path = self.base_dir / "data" / "validaciones_predicciones.jsonl"
        if val_path.exists():
            count = len(val_path.read_text().strip().split("\n"))
            reporte["componentes"]["validaciones"] = {
                "archivo": "validaciones_predicciones.jsonl",
                "registros": count,
                "status": "OK" if count > 0 else "PENDIENTE"
            }
        
        # 3. Estado de feedback automático
        fb_path = self.base_dir / "data" / "feedback_usuario_historico.jsonl"
        if fb_path.exists():
            count = len(fb_path.read_text().strip().split("\n"))
            reporte["componentes"]["feedback"] = {
                "archivo": "feedback_usuario_historico.jsonl",
                "registros": count,
                "status": "OK" if count > 0 else "VACIO"
            }
        
        # 4. Estadísticas de feedback
        stats_path = self.base_dir / "data" / "feedback_estadisticas.json"
        if stats_path.exists():
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
            reporte["estadisticas"] = stats
        
        # 5. Salud general
        tiene_predicciones = reporte["componentes"].get("predicciones", {}).get("registros", 0) > 0
        tiene_validaciones = reporte["componentes"].get("validaciones", {}).get("registros", 0) > 0
        tiene_feedback = reporte["componentes"].get("feedback", {}).get("registros", 0) > 0
        
        salud = "EXCELENTE" if (tiene_predicciones and tiene_validaciones and tiene_feedback) else \
                "BUENO" if (tiene_predicciones and tiene_validaciones) else \
                "PARCIAL" if tiene_predicciones else \
                "NULO"
        
        reporte["salud_general"] = {
            "estado": salud,
            "componentes_activos": sum([tiene_predicciones, tiene_validaciones, tiene_feedback]),
            "componentes_totales": 3
        }
        
        return reporte


def validar_y_generar_feedback_automatico(base_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Función auxiliar para ejecutar el ciclo completo:
    1. Validar predicciones pendientes
    2. Generar feedback automático
    3. Reportar salud
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[2]
    
    resultado = {
        "timestamp": time.time(),
        "validaciones_ejecutadas": 0,
        "feedback_generado": 0,
        "reporte": {}
    }
    
    try:
        # 1. Validar
        validator = PredictionValidator(base_dir)
        validaciones = validator.validar_predicciones_pendientes(ventana_horas=24)
        resultado["validaciones_ejecutadas"] = len(validaciones)
        
        # 2. Generar feedback
        fb_gen = AutomaticFeedbackGenerator(base_dir)
        resultado["feedback_generado"] = fb_gen.generar_feedback_desde_validaciones()
        
        # 3. Reportar
        loop_validator = LearningLoopValidator(base_dir)
        resultado["reporte"] = loop_validator.generar_reporte_aprendizaje()
    
    except Exception as e:
        logger.error(f"Error en ciclo de aprendizaje: {e}")
        resultado["error"] = str(e)
    
    return resultado
