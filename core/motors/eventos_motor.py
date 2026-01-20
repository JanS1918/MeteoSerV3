from typing import Dict, Any

class MotorEventos:
    def consultar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica real: devolver eventos registrados localmente
        eventos = datos.get("eventos", []) if isinstance(datos, dict) else []
        return {"eventos": eventos, "total": len(eventos)}
