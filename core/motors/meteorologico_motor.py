from typing import Dict, Any

class MotorMeteorologico:
    def calcular_indices(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica real: devolver índices meteorológicos ya calculados
        indices = datos.get("indices", {}) if isinstance(datos, dict) else {}
        meteorologia = {k: v for k, v in indices.items() if isinstance(k, str) and (
            "riesgo" in k or "alerta" in k or "niebla" in k or "lluvia" in k or "viento" in k or "visibilidad" in k
        )}
        return {"indices": meteorologia, "detalles": "Índices meteorológicos reales"}
