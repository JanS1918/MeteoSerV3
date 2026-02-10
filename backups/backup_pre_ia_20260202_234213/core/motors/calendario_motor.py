from typing import Dict, Any

class MotorCalendario:
    def gestionar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica real: devolver calendario local
        calendario = datos.get("calendario", []) if isinstance(datos, dict) else []
        return {"calendario": calendario, "total": len(calendario)}
