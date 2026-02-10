"""
🛡️ CAPA 40: FEEDBACK LEARNING AUDITOR
Valida que el sistema de confianza del Feedback Learning V47.2
no se auto-engañe con confianza falsa o sobreajuste (overfitting).

EVITA:
- Confianza inflada sin validaciones reales
- Overfitting (100% confianza en 3 validaciones)
- Auto-refuerzo de errores sistemáticos
- Modelos que "memorizan" en lugar de generalizar

VALIDA:
✅ Confianza proporcional a número de validaciones
✅ No hay racha sospechosa de aciertos perfectos
✅ Distribución de errores es normal (no sesgada)
✅ Accuracy no sube artificialmente sin nuevas validaciones

AUTOR: V47.3 SUMMUM - Guardian Inteligente
FECHA: 2026-02-05
"""

import json
import logging
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class FeedbackLearningAuditor:
    """
    Auditor de confianza del Feedback Learning.
    
    Detecta patrones sospechosos que indican auto-engaño o overfitting
    en el sistema de aprendizaje por refuerzo.
    """
    
    # Umbrales de detección
    VALIDACIONES_MINIMAS_ALTA_CONFIANZA = 30   # Validaciones antes de confianza >90%
    RACHA_MAXIMA_PERFECTA = 15                 # Aciertos consecutivos permitidos
    CONFIANZA_MAXIMA_SIN_VALIDACIONES = 75.0   # % confianza sin validaciones
    DESVIACION_MAXIMA_ACCURACY = 5.0           # % cambio accuracy sin validaciones
    VENTANA_TEMPORAL_AUDIT = 24                # Horas para detectar anomalías
    
    # Umbrales de overfitting
    RATIO_CONFIANZA_VALIDACIONES = 3.0  # confianza/validaciones (ej: 90%/30 valid = 3.0)
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.estado_file = self.data_dir / "feedback_learning_auditor_estado.json"
        self.estado = self._cargar_estado()
        
        logger.info("✅ FeedbackLearningAuditor inicializado")
    
    def _cargar_estado(self) -> Dict:
        """Carga estado persistente del auditor."""
        if self.estado_file.exists():
            with open(self.estado_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "auditorias_totales": 0,
            "alertas_generadas": 0,
            "modelos_auditados": {},  # {modelo: {parametro: {...}}}
            "historico_anomalias": [],
            "ultima_actualizacion": None
        }
    
    def _guardar_estado(self):
        """Guarda estado persistente."""
        self.estado["ultima_actualizacion"] = datetime.now().isoformat()
        with open(self.estado_file, 'w', encoding='utf-8') as f:
            json.dump(self.estado, f, indent=2, ensure_ascii=False)
    
    def auditar_confianza(
        self,
        modelo: str,
        parametro: str,
        confianza_actual: float,
        validaciones_totales: int,
        accuracy: float,
        ultimas_validaciones: List[Dict]
    ) -> Tuple[bool, List[str], float]:
        """
        Audita la confianza de un modelo para un parámetro.
        
        Args:
            modelo: "deardorff_v47", "wright_v47", etc.
            parametro: "temperatura_minima", "et0", etc.
            confianza_actual: Confianza que el modelo tiene (0-100%)
            validaciones_totales: Número total de validaciones
            accuracy: Accuracy actual (0-100%)
            ultimas_validaciones: [{"resultado": "EXACTO|BUENO|ERROR", "timestamp": ...}]
        
        Returns:
            (es_confiable, [alertas], confianza_ajustada)
        """
        self.estado["auditorias_totales"] += 1
        alertas = []
        
        # Crear entrada para modelo/parámetro si no existe
        if modelo not in self.estado["modelos_auditados"]:
            self.estado["modelos_auditados"][modelo] = {}
        
        if parametro not in self.estado["modelos_auditados"][modelo]:
            self.estado["modelos_auditados"][modelo][parametro] = {
                "confianza_historico": [],
                "accuracy_historico": [],
                "validaciones_historico": [],
                "primera_auditoria": datetime.now().isoformat()
            }
        
        audit_data = self.estado["modelos_auditados"][modelo][parametro]
        
        # ============================================================
        # 1. VALIDAR CONFIANZA vs VALIDACIONES
        # ============================================================
        if validaciones_totales < self.VALIDACIONES_MINIMAS_ALTA_CONFIANZA:
            if confianza_actual > 90.0:
                alertas.append(
                    f"⚠️ OVERFITTING: Confianza {confianza_actual:.1f}% con solo "
                    f"{validaciones_totales} validaciones (mínimo {self.VALIDACIONES_MINIMAS_ALTA_CONFIANZA})"
                )
        
        # ============================================================
        # 2. VALIDAR RATIO CONFIANZA/VALIDACIONES
        # ============================================================
        if validaciones_totales > 0:
            ratio = confianza_actual / validaciones_totales
            if ratio > self.RATIO_CONFIANZA_VALIDACIONES:
                alertas.append(
                    f"⚠️ RATIO SOSPECHOSO: Confianza/Validaciones = {ratio:.2f} "
                    f"(máximo {self.RATIO_CONFIANZA_VALIDACIONES})"
                )
        
        # ============================================================
        # 3. DETECTAR RACHA PERFECTA SOSPECHOSA
        # ============================================================
        racha_perfecta = self._detectar_racha_perfecta(ultimas_validaciones)
        if racha_perfecta > self.RACHA_MAXIMA_PERFECTA:
            alertas.append(
                f"⚠️ RACHA PERFECTA: {racha_perfecta} aciertos consecutivos "
                f"(máximo esperado {self.RACHA_MAXIMA_PERFECTA})"
            )
        
        # ============================================================
        # 4. VALIDAR CAMBIO DE ACCURACY SIN VALIDACIONES NUEVAS
        # ============================================================
        if audit_data["accuracy_historico"]:
            accuracy_anterior = audit_data["accuracy_historico"][-1]
            validaciones_anterior = audit_data["validaciones_historico"][-1]
            
            if validaciones_totales == validaciones_anterior:
                # Sin validaciones nuevas
                cambio_accuracy = abs(accuracy - accuracy_anterior)
                
                if cambio_accuracy > self.DESVIACION_MAXIMA_ACCURACY:
                    alertas.append(
                        f"⚠️ ACCURACY CAMBIÓ {cambio_accuracy:.1f}% sin validaciones nuevas"
                    )
        
        # ============================================================
        # 5. VALIDAR DISTRIBUCIÓN DE ERRORES
        # ============================================================
        distribucion_normal = self._validar_distribucion_errores(ultimas_validaciones)
        if not distribucion_normal:
            alertas.append(
                "⚠️ DISTRIBUCIÓN ANORMAL: Errores no siguen patrón esperado "
                "(posible sesgo sistemático)"
            )
        
        # ============================================================
        # 6. CALCULAR CONFIANZA AJUSTADA
        # ============================================================
        confianza_ajustada = self._calcular_confianza_ajustada(
            confianza_actual,
            validaciones_totales,
            accuracy,
            len(alertas)
        )
        
        # Guardar histórico
        audit_data["confianza_historico"].append(confianza_actual)
        audit_data["accuracy_historico"].append(accuracy)
        audit_data["validaciones_historico"].append(validaciones_totales)
        
        # Mantener últimos 100 registros
        for key in ["confianza_historico", "accuracy_historico", "validaciones_historico"]:
            audit_data[key] = audit_data[key][-100:]
        
        # Registrar alertas
        if alertas:
            self.estado["alertas_generadas"] += len(alertas)
            self._registrar_anomalia(modelo, parametro, alertas)
            
            for alerta in alertas:
                logger.warning(f"🛡️ {modelo}/{parametro}: {alerta}")
        
        self._guardar_estado()
        
        es_confiable = len(alertas) == 0
        return (es_confiable, alertas, confianza_ajustada)
    
    def _detectar_racha_perfecta(self, ultimas_validaciones: List[Dict]) -> int:
        """
        Detecta racha de aciertos perfectos consecutivos.
        
        Returns:
            Longitud de la racha perfecta actual
        """
        racha = 0
        
        for validacion in reversed(ultimas_validaciones):
            if validacion.get("resultado") == "EXACTO":
                racha += 1
            else:
                break
        
        return racha
    
    def _validar_distribucion_errores(self, ultimas_validaciones: List[Dict]) -> bool:
        """
        Valida que los errores sigan una distribución normal.
        
        Un modelo que solo acierta en ciertos rangos y falla sistemáticamente
        en otros indica sesgo, no confianza real.
        
        Returns:
            True si distribución es normal, False si hay sesgo
        """
        if len(ultimas_validaciones) < 10:
            return True  # Datos insuficientes
        
        # Extraer resultados de últimas 30 validaciones
        resultados = [
            v.get("resultado", "ERROR")
            for v in ultimas_validaciones[-30:]
        ]
        
        # Contar tipos
        exactos = resultados.count("EXACTO")
        buenos = resultados.count("BUENO")
        errores = resultados.count("ERROR")
        criticos = resultados.count("CRITICO")
        
        total = len(resultados)
        
        # Distribución esperada (aproximada):
        # EXACTO: 30-50%
        # BUENO: 30-50%
        # ERROR: 10-30%
        # CRITICO: 0-10%
        
        pct_exactos = (exactos / total) * 100
        pct_criticos = (criticos / total) * 100
        
        # Sesgo hacia perfección (sospechoso)
        if pct_exactos > 70:
            return False
        
        # Sesgo hacia errores críticos (modelo malo)
        if pct_criticos > 20:
            return False
        
        return True
    
    def _calcular_confianza_ajustada(
        self,
        confianza_original: float,
        validaciones: int,
        accuracy: float,
        num_alertas: int
    ) -> float:
        """
        Calcula confianza ajustada basada en auditoría.
        
        Reduce confianza si hay alertas o datos insuficientes.
        """
        confianza = confianza_original
        
        # Penalizar por pocas validaciones
        if validaciones < self.VALIDACIONES_MINIMAS_ALTA_CONFIANZA:
            factor_validaciones = validaciones / self.VALIDACIONES_MINIMAS_ALTA_CONFIANZA
            confianza = min(confianza, self.CONFIANZA_MAXIMA_SIN_VALIDACIONES * factor_validaciones)
        
        # Penalizar por alertas
        penalizacion_por_alerta = 10.0  # % por cada alerta
        confianza -= num_alertas * penalizacion_por_alerta
        
        # Alinear con accuracy real
        if accuracy < confianza:
            # Confianza no puede ser mayor que accuracy demostrado
            confianza = accuracy
        
        return max(0.0, min(100.0, confianza))
    
    def _registrar_anomalia(self, modelo: str, parametro: str, alertas: List[str]):
        """Registra anomalía detectada en histórico."""
        self.estado["historico_anomalias"].append({
            "timestamp": datetime.now().isoformat(),
            "modelo": modelo,
            "parametro": parametro,
            "alertas": alertas
        })
        
        # Mantener últimas 500 anomalías
        self.estado["historico_anomalias"] = self.estado["historico_anomalias"][-500:]
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas completas del auditor.
        
        Returns:
            {
                "auditorias_totales": 5234,
                "alertas_generadas": 127,
                "tasa_alertas": 2.4,
                "modelos_sospechosos": [...],
                "anomalias_ultimas_24h": 5
            }
        """
        total_auditorias = self.estado["auditorias_totales"]
        total_alertas = self.estado["alertas_generadas"]
        
        tasa_alertas = (total_alertas / total_auditorias * 100) if total_auditorias > 0 else 0.0
        
        # Anomalías últimas 24h
        fecha_limite = datetime.now() - timedelta(hours=self.VENTANA_TEMPORAL_AUDIT)
        anomalias_24h = sum(
            1 for anomalia in self.estado["historico_anomalias"]
            if datetime.fromisoformat(anomalia["timestamp"]) > fecha_limite
        )
        
        # Modelos sospechosos (con >5 alertas en 24h)
        modelos_sospechosos = []
        for anomalia in self.estado["historico_anomalias"][-100:]:
            if datetime.fromisoformat(anomalia["timestamp"]) > fecha_limite:
                modelo_param = f"{anomalia['modelo']}/{anomalia['parametro']}"
                if modelo_param not in modelos_sospechosos:
                    # Contar alertas de este modelo en 24h
                    alertas_modelo = sum(
                        1 for a in self.estado["historico_anomalias"]
                        if a["modelo"] == anomalia["modelo"]
                        and a["parametro"] == anomalia["parametro"]
                        and datetime.fromisoformat(a["timestamp"]) > fecha_limite
                    )
                    if alertas_modelo >= 5:
                        modelos_sospechosos.append({
                            "modelo": anomalia["modelo"],
                            "parametro": anomalia["parametro"],
                            "alertas_24h": alertas_modelo
                        })
        
        return {
            "auditorias_totales": total_auditorias,
            "alertas_generadas": total_alertas,
            "tasa_alertas": round(tasa_alertas, 2),
            "anomalias_ultimas_24h": anomalias_24h,
            "modelos_sospechosos": modelos_sospechosos
        }


# ============================================================================
# INTEGRACIÓN CON FEEDBACK LEARNING V47.2
# ============================================================================

def integrar_auditor_en_feedback():
    """
    Ejemplo de integración del auditor en feedback_learning_v472.py
    
    Añadir al método obtener_confianza():
    
    ```python
    # En feedback_learning_v472.py
    from core.learning.feedback_learning_auditor import FeedbackLearningAuditor
    
    self.auditor = FeedbackLearningAuditor()
    
    def obtener_confianza(self, parametro):
        modelo_data = self.modelos.get(parametro, {})
        confianza = modelo_data.get("confianza", 75.0)
        validaciones = len(modelo_data.get("validaciones", []))
        accuracy = modelo_data.get("accuracy", 0.0)
        ultimas_val = modelo_data.get("validaciones", [])[-30:]
        
        # AUDITAR CONFIANZA
        es_confiable, alertas, confianza_ajustada = self.auditor.auditar_confianza(
            modelo="sistema_actual",
            parametro=parametro,
            confianza_actual=confianza,
            validaciones_totales=validaciones,
            accuracy=accuracy,
            ultimas_validaciones=ultimas_val
        )
        
        if not es_confiable:
            logger.warning(f"⚠️ Confianza ajustada: {confianza:.1f}% → {confianza_ajustada:.1f}%")
            confianza = confianza_ajustada
        
        return {
            "confianza": confianza,
            "accuracy": accuracy,
            "validaciones": validaciones,
            "auditoria": {
                "es_confiable": es_confiable,
                "alertas": alertas
            }
        }
    ```
    """
    pass


if __name__ == "__main__":
    # Test básico
    logging.basicConfig(level=logging.INFO)
    
    auditor = FeedbackLearningAuditor()
    
    # Test: Confianza legítima
    ultimas_val_legitimas = [
        {"resultado": "EXACTO", "timestamp": "2026-02-05T10:00:00"},
        {"resultado": "BUENO", "timestamp": "2026-02-05T10:05:00"},
        {"resultado": "EXACTO", "timestamp": "2026-02-05T10:10:00"},
        {"resultado": "ERROR", "timestamp": "2026-02-05T10:15:00"},
    ] * 10  # 40 validaciones
    
    es_conf, alertas, conf_ajust = auditor.auditar_confianza(
        modelo="deardorff_v47",
        parametro="temperatura_minima",
        confianza_actual=85.0,
        validaciones_totales=40,
        accuracy=82.5,
        ultimas_validaciones=ultimas_val_legitimas
    )
    
    print(f"\n✅ Confianza legítima: {es_conf}")
    print(f"   Alertas: {alertas}")
    print(f"   Confianza ajustada: {conf_ajust:.1f}%")
    
    # Test: Overfitting (alta confianza, pocas validaciones)
    es_conf, alertas, conf_ajust = auditor.auditar_confianza(
        modelo="modelo_sospechoso",
        parametro="et0",
        confianza_actual=95.0,
        validaciones_totales=5,
        accuracy=100.0,
        ultimas_validaciones=[{"resultado": "EXACTO"}] * 5
    )
    
    print(f"\n⚠️ Overfitting detectado: {not es_conf}")
    print(f"   Alertas: {alertas}")
    print(f"   Confianza ajustada: {conf_ajust:.1f}%")
    
    # Estadísticas
    stats = auditor.obtener_estadisticas()
    print(f"\n📊 Estadísticas: {json.dumps(stats, indent=2)}")
