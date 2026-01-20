from typing import Dict, Any


class MotorAmbiental:
    def analizar(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Lógica real: analizar ambiente con sensores e índices
        sensores = datos.get("sensores", {}) if isinstance(datos, dict) else {}
        indices = datos.get("indices", {}) if isinstance(datos, dict) else {}

        resultado = {"estado": "ok", "detalles": {}, "anomalias": []}

        co2 = sensores.get("co2")
        humedad = sensores.get("humedad_interior") or sensores.get("humedad")
        ruido = sensores.get("ruido")
        luz = sensores.get("luz")

        if co2 is not None:
            try:
                if float(co2) > 1200:
                    resultado["detalles"]["aire_cargado"] = "CO2 alto"
            except Exception:
                pass
        if humedad is not None:
            try:
                if float(humedad) < 35:
                    resultado["detalles"]["aire_seco"] = "Humedad baja"
                if float(humedad) > 70:
                    resultado["detalles"]["aire_humedo"] = "Humedad alta"
            except Exception:
                pass
        if ruido is not None:
            try:
                if float(ruido) > 70:
                    resultado["detalles"]["ruido_alto"] = "Ruido elevado"
            except Exception:
                pass
        if luz is not None:
            try:
                if float(luz) > 80:
                    resultado["detalles"]["luz_alta"] = "Luz intensa"
            except Exception:
                pass

        # Apoyarse en índices calculados
        riesgo_niebla = indices.get("riesgo_niebla", {}).get("valor")
        if riesgo_niebla is not None and float(riesgo_niebla) > 60:
            resultado["detalles"]["niebla"] = "Riesgo de niebla alto"

        aire_cargado = indices.get("aire_cargado", {}).get("valor")
        if aire_cargado is not None and float(aire_cargado) > 60:
            resultado["detalles"]["aire_cargado_idx"] = "Aire cargado según índice"

        # Anomalías simples
        try:
            t_ext = sensores.get("temperatura")
            t_int = sensores.get("temperatura_interior")
            if t_ext is not None and t_int is not None:
                if abs(float(t_int) - float(t_ext)) > 8:
                    resultado["anomalias"].append("Diferencia térmica alta int/ext")
        except Exception:
            pass

        return resultado
