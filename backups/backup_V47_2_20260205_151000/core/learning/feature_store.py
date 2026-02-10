import logging
"""
FEATURE STORE: Almacén de features para modelos
CONFIDENCE SCORING: Puntuación de confianza por dato
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class FeatureStore:
    """Almacén de features históricos para modelos ML."""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.store_file = self.workspace / "data" / "feature_store.jsonl"
        self.store_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def record_features(self, sensor_id: str, features: Dict, metadata: Dict = None):
        """Registra un conjunto de features."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": sensor_id,
            "features": features,
            "metadata": metadata or {}
        }
        
        with open(self.store_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_recent_features(self, sensor_id: str, limit: int = 100) -> List[Dict]:
        """Retorna features recientes de un sensor."""
        features = []
        try:
            with open(self.store_file, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry["sensor_id"] == sensor_id:
                        features.append(entry)
        except:
            logging.exception("Silent except at 41 - revisar contexto")
        
        return features[-limit:]


class ConfidenceScorer:
    """Calcula puntuación de confianza para cada dato."""
    
    def __init__(self, anomaly_detector, feature_store):
        self.anomaly_detector = anomaly_detector
        self.feature_store = feature_store
    
    async def compute_confidence(self, sensor_id: str, measurement: Dict, detection_result: Dict) -> float:
        """
        Computa confianza del dato (0-1).
        Combina: detector score + consistencia histórica + metadata.
        """
        # Base: score del detector
        confidence = 1.0 - detection_result.get("score", 0)
        
        # Modificador: consistencia histórica
        recent_features = self.feature_store.get_recent_features(sensor_id, limit=10)
        if recent_features:
            historical_avg = sum(f["features"].get("value", 0) for f in recent_features) / len(recent_features)
            current_value = measurement.get("value", 0)
            
            # Si está muy lejos del histórico, restar confianza
            if abs(current_value - historical_avg) > 3 * self._compute_std(recent_features):
                confidence *= 0.8
        
        return max(0, min(1, confidence))
    
    def _compute_std(self, features: List[Dict]) -> float:
        """Computa desviación estándar de features."""
        values = [f["features"].get("value", 0) for f in features]
        if len(values) < 2:
            return 0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5
