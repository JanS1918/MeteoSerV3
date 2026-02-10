"""
MIDDLEWARE DE METADATOS - Expone status/meta para cada lectura
Integración mínima en el Bus
"""

class MetadataMiddleware:
    """Enriquece publicaciones del Bus con metadatos de status."""
    
    def __init__(self, bus, anomaly_detector):
        self.bus = bus
        self.anomaly_detector = anomaly_detector
        self._metadata_cache = {}
    
    async def enrich_measurement(self, sensor_id: str, measurement: dict, detection_result: dict) -> dict:
        """Añade metadatos de detección a la medición."""
        return {
            "value": measurement.get("value"),
            "unit": measurement.get("unit"),
            "meta": {
                "status": detection_result["status"],
                "score": detection_result["score"],
                "reasons": detection_result["reasons"],
                "detector_version": detection_result["detector_version"]
            },
            "sensor_id": sensor_id,
            "timestamp": detection_result["timestamp"]
        }
    
    async def publish_with_metadata(self, sensor_id: str, value: float, unit: str, detection_result: dict):
        """Publica valor con metadatos en el Bus."""
        enriched = await self.enrich_measurement(sensor_id, {"value": value, "unit": unit}, detection_result)
        self.bus.publicar(f"{sensor_id}_with_meta", enriched, "metadata")
        self._metadata_cache[sensor_id] = enriched
    
    def get_metadata(self, sensor_id: str) -> dict:
        """Retorna metadatos cached para un sensor."""
        return self._metadata_cache.get(sensor_id, {})
