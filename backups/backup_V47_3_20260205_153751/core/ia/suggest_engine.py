"""
IA MODO SUGGEST: Propuestas con aprobación humana
"""

class AISuggestEngine:
    """Motor de sugerencias con requerimiento de aprobación."""
    
    def __init__(self, assistant, bus):
        self.assistant = assistant
        self.bus = bus
        self.pending_approvals = {}
    
    async def suggest_fallback(self, sensor_id: str, reason: str) -> dict:
        """Propone usar fallback ISA (requiere aprobación)."""
        suggestion = {
            "id": f"suggest_{sensor_id}_{int(__import__('time').time())}",
            "type": "use_fallback",
            "sensor_id": sensor_id,
            "reason": reason,
            "confidence": 0.85,
            "status": "pending_approval"
        }
        self.pending_approvals[suggestion["id"]] = suggestion
        self.bus.publicar("ia_suggestion", suggestion, "suggestion")
        return suggestion
    
    async def suggest_calibration(self, sensor_id: str) -> dict:
        """Propone calibración de sensor."""
        suggestion = {
            "id": f"suggest_{sensor_id}_calib",
            "type": "calibrate_sensor",
            "sensor_id": sensor_id,
            "confidence": 0.75,
            "status": "pending_approval"
        }
        self.pending_approvals[suggestion["id"]] = suggestion
        return suggestion
    
    async def approve_suggestion(self, suggestion_id: str, approved_by: str) -> bool:
        """Aprueba una sugerencia (registra aprobación)."""
        if suggestion_id in self.pending_approvals:
            suggestion = self.pending_approvals[suggestion_id]
            suggestion["status"] = "approved"
            suggestion["approved_by"] = approved_by
            suggestion["approved_at"] = __import__('datetime').datetime.now().isoformat()
            self.bus.publicar("ia_approval", suggestion, "approval_log")
            return True
        return False
    
    async def reject_suggestion(self, suggestion_id: str, rejected_by: str, reason: str = "") -> bool:
        """Rechaza una sugerencia."""
        if suggestion_id in self.pending_approvals:
            suggestion = self.pending_approvals[suggestion_id]
            suggestion["status"] = "rejected"
            suggestion["rejected_by"] = rejected_by
            suggestion["rejection_reason"] = reason
            suggestion["rejected_at"] = __import__('datetime').datetime.now().isoformat()
            self.bus.publicar("ia_rejection", suggestion, "rejection_log")
            return True
        return False
    
    def get_pending_approvals(self) -> list:
        """Retorna sugerencias pendientes de aprobación."""
        return [s for s in self.pending_approvals.values() if s["status"] == "pending_approval"]
