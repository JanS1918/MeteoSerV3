#!/usr/bin/env python3
"""CAPA 24: Alert Filter System - Filtro visual de alertas para UI (integra CentinelaV30)"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional

logger = logging.getLogger("alert_filter_system")


class AlertSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class AlertCategory(Enum):
    WATCHDOG = "watchdog"
    CANARY = "canary"
    CASCADE = "cascade"
    DRIFT = "drift"
    RESOURCE = "resource"
    OVERFITTING = "overfitting"
    SANDBOX = "sandbox"
    BUS = "bus"
    BIAS = "bias"
    SYSTEM = "system"


@dataclass
class UIAlert:
    alert_id: str
    severity: AlertSeverity
    category: AlertCategory
    message: str
    timestamp: float
    details: Dict = None
    acknowledged: bool = False


class AlertFilterSystem:
    """Sistema de filtrado y priorización de alertas para UI (integra CentinelaV30)."""
    
    def __init__(self):
        self.alerts: List[UIAlert] = []
        self.filters = {
            "severity_min": AlertSeverity.LOW,
            "categories": set(AlertCategory),
            "max_alerts": 100,
        }
        self.acknowledged_alerts = set()
        logger.info("✅ AlertFilterSystem inicializado (integración CentinelaV30)")
    
    def add_alert(self, severity: AlertSeverity, category: AlertCategory,
                 message: str, details: Optional[Dict] = None) -> str:
        """Agrega alerta al sistema."""
        alert_id = f"{category.value}_{len(self.alerts)}"
        import time
        alert = UIAlert(alert_id, severity, category, message, time.time(), details)
        self.alerts.append(alert)
        logger.debug(f"📢 Alerta agregada: {severity.value} [{category.value}] {message[:50]}")
        return alert_id
    
    def set_filter(self, severity_min: AlertSeverity = None, categories: List[AlertCategory] = None):
        """Configura filtros de visualización."""
        if severity_min:
            self.filters["severity_min"] = severity_min
        if categories:
            self.filters["categories"] = set(categories)
        logger.info(f"✅ Filtros configurados: severidad>={severity_min}, categorías={len(self.filters['categories'])}")
    
    def get_filtered_alerts(self, acknowledged: bool = False) -> List[UIAlert]:
        """Retorna alertas filtradas según criterios."""
        severity_order = [AlertSeverity.CRITICAL, AlertSeverity.HIGH, AlertSeverity.MEDIUM,
                         AlertSeverity.LOW, AlertSeverity.INFO]
        
        filtered = [
            a for a in self.alerts
            if a.category in self.filters["categories"] and
               severity_order.index(a.severity) <= severity_order.index(self.filters["severity_min"]) and
               a.acknowledged == acknowledged
        ]
        
        # Ordenar por severidad (críticas primero)
        filtered.sort(key=lambda a: severity_order.index(a.severity))
        return filtered[:self.filters["max_alerts"]]
    
    def acknowledge_alert(self, alert_id: str):
        """Marca alerta como reconocida en UI."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.acknowledged_alerts.add(alert_id)
                logger.info(f"✅ Alerta {alert_id} reconocida")
                return True
        return False
    
    def get_critical_alerts(self) -> List[UIAlert]:
        """Retorna solo alertas CRÍTICAS no reconocidas."""
        return [a for a in self.alerts
                if a.severity == AlertSeverity.CRITICAL and not a.acknowledged]
    
    def get_dashboard_summary(self) -> Dict:
        """Resumen para dashboard UI."""
        all_alerts = self.get_filtered_alerts()
        by_severity = {}
        for severity in AlertSeverity:
            by_severity[severity.value] = len([a for a in all_alerts if a.severity == severity])
        
        return {
            "total_alerts": len(all_alerts),
            "critical_count": len(self.get_critical_alerts()),
            "by_severity": by_severity,
            "recent_alerts": [
                {
                    "id": a.alert_id,
                    "severity": a.severity.value,
                    "category": a.category.value,
                    "message": a.message,
                    "timestamp": a.timestamp
                }
                for a in all_alerts[:10]
            ]
        }
    
    def centinela_integration_point(self, watchdog_event: str, reason: str):
        """Integración con CentinelaV30: publica eventos del watchdog como alertas."""
        if "HEARTBEAT" in watchdog_event.upper():
            self.add_alert(AlertSeverity.CRITICAL, AlertCategory.WATCHDOG,
                          f"Watchdog timeout: {reason}")
        elif "RESTORE" in watchdog_event.upper():
            self.add_alert(AlertSeverity.HIGH, AlertCategory.WATCHDOG,
                          f"Snapshot restaurado: {reason}")
