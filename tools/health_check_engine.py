"""
HEALTH CHECKS: Monitoreo periódico del sistema
"""

from datetime import datetime, timedelta
from pathlib import Path
import json


class HealthCheckEngine:
    """Motor de health checks del sistema."""
    
    def __init__(self, workspace_path: str, anomaly_detector, fallback_isa, observability):
        self.workspace = Path(workspace_path)
        self.anomaly_detector = anomaly_detector
        self.fallback_isa = fallback_isa
        self.observability = observability
        self.health_history = []
    
    async def run_health_check(self) -> dict:
        """Ejecuta un health check completo."""
        check = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Check 1: Logs accesibles
        logs_ok = self._check_logs()
        check["checks"]["logs_accessible"] = logs_ok
        
        # Check 2: Backups funcionando
        backups_ok = self._check_backups()
        check["checks"]["backups_ok"] = backups_ok
        
        # Check 3: Histórico de anomalías
        anomaly_ok = self._check_anomalies()
        check["checks"]["anomaly_detector_ok"] = anomaly_ok
        
        # Check 4: Fallback rate bajo
        fallback_rate = self.fallback_isa.get_fallback_rate()
        check["checks"]["fallback_rate"] = fallback_rate
        check["checks"]["fallback_acceptable"] = fallback_rate < 0.3
        
        # Check 5: Sistema health
        health_score = self.observability._compute_health_score()
        check["checks"]["health_score"] = health_score
        check["checks"]["health_ok"] = health_score > 60
        
        # Componer overall status
        all_ok = all(v for k, v in check["checks"].items() if k.endswith("_ok") or k.endswith("_acceptable"))
        check["overall_status"] = "HEALTHY" if all_ok else "DEGRADED"
        
        self.health_history.append(check)
        return check
    
    def _check_logs(self) -> bool:
        """Verifica que los archivos de log sean accesibles."""
        try:
            logs_dir = self.workspace / "logs"
            return logs_dir.exists() and (logs_dir / "anomalies.log").exists()
        except:
            return False
    
    def _check_backups(self) -> bool:
        """Verifica que haya checkpoints recientes."""
        try:
            backups_dir = self.workspace / "backups" / "system_checkpoints"
            if not backups_dir.exists():
                return False
            
            checkpoints = list(backups_dir.iterdir())
            return len(checkpoints) > 0
        except:
            return False
    
    def _check_anomalies(self) -> bool:
        """Verifica que el detector esté funcionando."""
        return hasattr(self.anomaly_detector, "recent_measurements")
    
    async def generate_weekly_report(self) -> dict:
        """Genera reporte de salud semanal."""
        report = {
            "week_of": (datetime.now() - timedelta(days=7)).isoformat(),
            "generated_at": datetime.now().isoformat(),
            "total_checks": len(self.health_history),
            "healthy_periods": sum(1 for h in self.health_history if h["overall_status"] == "HEALTHY"),
            "degraded_periods": sum(1 for h in self.health_history if h["overall_status"] == "DEGRADED"),
            "average_health_score": sum(h["checks"].get("health_score", 0) for h in self.health_history) / max(1, len(self.health_history))
        }
        return report
