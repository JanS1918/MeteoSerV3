from enum import Enum

class AlertLevel(Enum):
    CRITICAL = "crítica"
    HIGH = "alta"
    MEDIUM = "media"
    LOW = "baja"

ALERT_COLORS = {
    AlertLevel.CRITICAL: "red",
    AlertLevel.HIGH: "orange",
    AlertLevel.MEDIUM: "yellow",
    AlertLevel.LOW: "green",
}

class Alert:
    def __init__(self, level: AlertLevel, message: str, requires_intervention: bool, reason: str = ""):
        self.level = level
        self.color = ALERT_COLORS[level]
        self.message = message
        self.requires_intervention = requires_intervention
        self.reason = reason

    def to_dict(self):
        return {
            "level": self.level.value,
            "color": self.color,
            "message": self.message,
            "requires_intervention": self.requires_intervention,
            "reason": self.reason,
        }