"""
INTEGRACIÓN: Acorazado completo - orquestación de todos los componentes
"""

import asyncio
import logging
from pathlib import Path


class AcorazadoOrchestrator:
    """Orquestador central del sistema Acorazado."""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.logger = logging.getLogger("AcorazadoOrchestrator")
        self.components = {}
    
    async def initialize_all_components(self):
        """Inicializa todos los componentes en orden seguro."""
        
        # 1. Checkpoint & backup
        from core.validation.anomaly_detector import AnomalyDetector
        from core.logging.audit_trail import AuditTrail
        from core.validation.fallback_isa import FallbackISA
        from core.ia.assistant import AIAssistant
        from core.ia.suggest_engine import AISuggestEngine
        from core.system.observability_engine import ObservabilityEngine
        from core.learning.feature_store import FeatureStore, ConfidenceScorer
        from core.learning.model_governance import ModelRegistry, RetrainingPipeline
        from core.security.policies import SecretsManager, DataRetentionPolicy, AccessControl
        
        # Inicializar componentes
        self.components["anomaly_detector"] = AnomalyDetector()
        self.components["audit_trail"] = AuditTrail(str(self.workspace))
        self.components["fallback"] = FallbackISA()
        self.components["ai_assistant"] = AIAssistant()
        self.components["ai_engine"] = AISuggestEngine()
        self.components["observability"] = ObservabilityEngine()
        self.components["feature_store"] = FeatureStore(str(self.workspace))
        self.components["confidence"] = ConfidenceScorer(
            self.components["anomaly_detector"]
        )
        self.components["model_registry"] = ModelRegistry(str(self.workspace))
        self.components["retrain_pipeline"] = RetrainingPipeline(
            self.components["feature_store"],
            self.components["model_registry"]
        )
        self.components["secrets"] = SecretsManager()
        self.components["retention"] = DataRetentionPolicy(str(self.workspace))
        
        self.logger.info("✅ Todos los componentes inicializados")
    
    async def process_measurement(self, measurement: dict) -> dict:
        """Procesa una medición a través del pipeline completo."""
        
        # 1. Anomalía
        anomaly = self.components["anomaly_detector"].detect(measurement)
        
        # 2. Auditoría
        self.components["audit_trail"].log_anomaly(anomaly)
        
        # 3. Fallback si es necesario
        if anomaly["status"] != "OK":
            fallback = self.components["fallback"].get_fallback(
                measurement, mode="suggest"
            )
            self.components["audit_trail"].log_fallback_activation(fallback)
        else:
            fallback = None
        
        # 4. Confianza
        confidence = self.components["confidence"].compute_confidence(
            measurement, anomaly
        )
        
        # 5. Observabilidad
        self.components["observability"].record_metric("measurements_processed", 1)
        if anomaly["status"] != "OK":
            self.components["observability"].record_metric(
                "anomalies_detected", 1
            )
        
        # 6. Feature store
        self.components["feature_store"].record_features(
            measurement, {"anomaly": anomaly, "confidence": confidence}
        )
        
        result = {
            "measurement": measurement,
            "anomaly": anomaly,
            "fallback": fallback,
            "confidence": confidence,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return result
    
    async def daily_maintenance(self):
        """Tareas de mantenimiento diario."""
        
        # Limpiar datos antiguos
        cleanup_result = self.components["retention"].cleanup_old_data()
        self.logger.info(f"Limpieza diaria: {cleanup_result}")
        
        # Chequeo de salud
        health_score = self.components["observability"]._compute_health_score()
        self.logger.info(f"Health score: {health_score}")
        
        # Revisar si aplica retraining
        models_to_retrain = ["anomaly_detector", "confidence_scorer"]
        for model_name in models_to_retrain:
            job = await self.components["retrain_pipeline"].schedule_retrain(
                model_name, trigger="periodic"
            )
            self.logger.info(f"Retraining programado: {job}")
    
    def get_system_status(self) -> dict:
        """Retorna estado del sistema completo."""
        return {
            "timestamp": str(Path.cwd()),
            "components": list(self.components.keys()),
            "health": self.components["observability"]._compute_health_score(),
            "recent_anomalies": len([
                m for m in self.components["feature_store"].get_recent_features(
                    hours=1
                ) if m.get("anomaly", {}).get("status") != "OK"
            ]) if self.components.get("feature_store") else 0
        }
