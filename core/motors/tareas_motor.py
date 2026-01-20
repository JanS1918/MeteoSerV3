from typing import Dict, Any

class MotorTareas:
    def gestionar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica real: devolver tareas registradas localmente
        tareas = datos.get("tareas", []) if isinstance(datos, dict) else []
        return {"tareas": tareas, "total": len(tareas)}
