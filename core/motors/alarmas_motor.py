from typing import Dict, Any

class MotorAlarmas:
    def gestionar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica real: devolver alarmas registradas localmente
        alarmas = datos.get("alarmas", []) if isinstance(datos, dict) else []
        return {"alarmas": alarmas, "total": len(alarmas)}
