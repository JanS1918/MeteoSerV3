from typing import Dict, Any

class MotorRecomendaciones:
    def generar_aviso(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica real: devolver recomendación unificada existente
        rec = datos.get("recomendacion") if isinstance(datos, dict) else None
        if rec:
            return rec
        return {"estado": "Sin recomendación", "motivos": {}}
