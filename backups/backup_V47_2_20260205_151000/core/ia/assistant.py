"""
IA READ-ONLY: Explicaciones y resúmenes de anomalías
Sin poder de decisión, solo información
"""

class AIAssistant:
    """Asistente IA para explicaciones legibles."""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client  # Placeholder para LLM real
        self.version = "1.0"
    
    async def explain_anomaly(self, detection_result: dict, context: dict) -> str:
        """Genera explicación legible de una anomalía."""
        status = detection_result["status"]
        reasons = detection_result["reasons"]
        score = detection_result["score"]
        
        explanation = f"[IA ANÁLISIS] Sensor {context.get('sensor_id', 'unknown')}: "
        
        if status == "OK":
            explanation += "Lectura normal. "
        elif status == "DUDOSO":
            explanation += f"Lectura sospechosa (confianza: {score:.0%}). "
            
            if "valor_fuera_rango_fisico" in reasons:
                explanation += "Valor fuera de rangos físicos conocidos. "
            if "salto_temporal_imposible" in reasons:
                explanation += "Cambio demasiado rápido (posible rebote sensor). "
            if "incoherencia_variables_cruzadas" in reasons:
                explanation += "Variables no son coherentes entre sí. "
            if "outlier_detectado" in reasons:
                explanation += "Outlier estadístico detectado. "
        
        explanation += "[NO TOMA ACCIONES - MODO OBSERVACIÓN]"
        return explanation
    
    async def suggest_maintenance(self, sensor_id: str, anomaly_history: list) -> str:
        """Sugiere mantenimiento basado en histórico."""
        if len(anomaly_history) < 5:
            return ""
        
        anomaly_rate = len([a for a in anomaly_history[-100:] if a["status"] == "DUDOSO"]) / 100
        
        if anomaly_rate > 0.5:
            return f"[IA SUGERENCIA] {sensor_id}: Posible fallo de sensor. Revisar calibración."
        elif anomaly_rate > 0.2:
            return f"[IA SUGERENCIA] {sensor_id}: Sensor inestable. Considerar limpieza o reemplazo."
        
        return ""
