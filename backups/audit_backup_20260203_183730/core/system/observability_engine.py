"""
OBSERVABILIDAD: Métricas, alertas y health checks
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta

class ObservabilityEngine:
    """Motor de observabilidad y métricas."""
    
    def __init__(self, bus):
        self.bus = bus
        self.metrics = defaultdict(lambda: {"count": 0, "total": 0.0, "last_30min": []})
        self.alerts = []
    
    def record_metric(self, metric_name: str, value: float):
        """Registra una métrica."""
        self.metrics[metric_name]["count"] += 1
        self.metrics[metric_name]["total"] += value
        self.metrics[metric_name]["last_30min"].append({"time": time.time(), "value": value})
        
        # Limpiar histórico
        cutoff = time.time() - 1800
        self.metrics[metric_name]["last_30min"] = [
            m for m in self.metrics[metric_name]["last_30min"] if m["time"] > cutoff
        ]
    
    def get_metric(self, metric_name: str) -> dict:
        """Retorna estadísticas de una métrica."""
        m = self.metrics[metric_name]
        if m["count"] == 0:
            return {"mean": 0, "count": 0}
        
        mean = m["total"] / m["count"]
        recent_values = [v["value"] for v in m["last_30min"]]
        
        return {
            "metric": metric_name,
            "mean": mean,
            "count": m["count"],
            "recent_count": len(recent_values),
            "recent_mean": sum(recent_values) / len(recent_values) if recent_values else 0,
            "recent_max": max(recent_values) if recent_values else 0
        }
    
    async def check_alert_threshold(self, metric_name: str, threshold: float):
        """Verifica si una métrica excede umbral y genera alerta."""
        m = self.get_metric(metric_name)
        if m.get("recent_mean", 0) > threshold:
            alert = {
                "type": "threshold_exceeded",
                "metric": metric_name,
                "threshold": threshold,
                "actual": m.get("recent_mean"),
                "timestamp": datetime.now().isoformat()
            }
            self.alerts.append(alert)
            self.bus.publicar("alert", alert, "alert")
            return True
        return False
    
    async def publish_metrics(self):
        """Publica todas las métricas al Bus."""
        metrics_summary = {
            "timestamp": datetime.now().isoformat(),
            "anomaly_detections_per_hour": self.get_metric("anomalies_detected"),
            "fallback_activations_per_hour": self.get_metric("fallbacks_used"),
            "percent_simulated_data": self.get_metric("percent_simulated"),
            "system_health": self._compute_health_score()
        }
        self.bus.publicar("metrics_summary", metrics_summary, "metrics")
    
    def _compute_health_score(self) -> float:
        """Computa score de salud del sistema (0-100)."""
        anomalies = self.get_metric("anomalies_detected").get("recent_count", 0)
        fallbacks = self.get_metric("fallbacks_used").get("recent_count", 0)
        
        # Score base 100, resta 5 por cada anomalía y 10 por cada fallback
        score = max(0, 100 - anomalies * 5 - fallbacks * 10)
        return score
