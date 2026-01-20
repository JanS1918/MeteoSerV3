from typing import Dict, Any

class MotorSubmenu:
    def obtener_detalle(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        # Submenú detallado real: causas, acciones, historial y algoritmos
        sensores = datos.get("sensores", {}) if isinstance(datos, dict) else {}
        indices = datos.get("indices", {}) if isinstance(datos, dict) else {}
        predicciones = datos.get("predicciones", {}) if isinstance(datos, dict) else {}
        auto_mejora = datos.get("auto_mejora", {}) if isinstance(datos, dict) else {}

        causas = []
        acciones = []
        if indices.get("riesgo_lluvia", {}).get("valor", 0) > 60:
            causas.append("HR alta + lluvia detectada")
            acciones.append("Llevar paraguas")
        if indices.get("alerta_tormenta", {}).get("valor", 0) > 60:
            causas.append("Presión baja + rayos + radiación baja")
            acciones.append("Evitar exterior")
        if indices.get("aire_cargado", {}).get("valor", 0) > 60:
            causas.append("CO2 alto sostenido")
            acciones.append("Ventilar")

        historial = {k: sensores.get(k) for k in ["temperatura", "humedad", "co2", "pm25", "viento", "lluvia"] if k in sensores}
        algoritmos = list(auto_mejora.keys()) if isinstance(auto_mejora, dict) else []

        return {
            "submenu": "detallado",
            "causas": causas,
            "acciones": acciones,
            "historial": historial,
            "predicciones": predicciones,
            "algoritmos": algoritmos
        }
