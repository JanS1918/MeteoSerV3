from typing import Dict, Any


class MotorEdificio:
    def diagnosticar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Diagnóstico real usando sensores e índices
        sensores = datos.get("sensores", {}) if isinstance(datos, dict) else {}
        indices = datos.get("indices", {}) if isinstance(datos, dict) else {}

        resultado = {"salud_edificio": "buena", "detalles": {}, "riesgos": []}

        riesgo_moho = indices.get("riesgo_moho", {}).get("valor")
        if riesgo_moho is not None and float(riesgo_moho) > 60:
            resultado["riesgos"].append("Riesgo de moho elevado")

        condensacion = indices.get("riesgo_condensacion_ventanas", {}).get("valor")
        if condensacion is not None and float(condensacion) > 60:
            resultado["riesgos"].append("Riesgo de condensación en ventanas")

        olor = indices.get("riesgo_olor_cerrado", {}).get("valor")
        if olor is not None and float(olor) > 60:
            resultado["riesgos"].append("Riesgo de olor a cerrado")

        salud = indices.get("salud_edificio", {}).get("valor")
        if salud is not None:
            if float(salud) < 60:
                resultado["salud_edificio"] = "degradada"
            elif float(salud) < 80:
                resultado["salud_edificio"] = "moderada"

        humedad = sensores.get("humedad_interior")
        if humedad is not None:
            try:
                if float(humedad) > 70:
                    resultado["detalles"]["humedad_alta"] = "Humedad interior alta"
            except Exception:
                pass

        return resultado
