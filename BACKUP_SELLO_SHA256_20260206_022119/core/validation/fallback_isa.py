"""
FALLBACK ISA - Reemplazo automático de sensores dudosos con modelo físico
Modo: suggest (por defecto) → force (configurable)
"""

class FallbackISA:
    """Proporciona valores ISA (atmósfera estándar) para sensores fallidos."""
    
    def __init__(self, system, config=None):
        self.system = system
        self.config = config or {}
        self.auto_fallback_enabled = self.config.get("AUTO_FALLBACK", False)
        self.fallback_history = []
    
    def compute_isa_pressure(self, altitude_m: float) -> float:
        """Calcula presión ISA según altitud (Barometric formula)."""
        if altitude_m < 11000:
            return 101325 * (1 - 0.0065 * altitude_m / 288.15) ** 5.255
        else:
            return 22632.06 * (216.65 / (216.65 + 0.0010 * (altitude_m - 11000))) ** 34.163
    
    def compute_isa_temperature(self, altitude_m: float) -> float:
        """Calcula temperatura ISA según altitud (en Celsius)."""
        if altitude_m < 11000:
            return 15.0 - 0.0065 * altitude_m
        else:
            return -56.5
    
    async def get_fallback(self, sensor_id: str, sensor_type: str, location: dict, mode: str = "suggest"):
        """
        Retorna valor fallback.
        mode: 'suggest' = solo propone, 'force' = sustituye
        """
        altitude = location.get("altitud", 0)
        
        if sensor_type == "presion":
            value = self.compute_isa_pressure(altitude)
        elif sensor_type == "temperatura":
            value = self.compute_isa_temperature(altitude)
        else:
            value = None
        
        fallback = {
            "sensor_id": sensor_id,
            "value": value,
            "source": "ISA_MODEL",
            "mode": mode,
            "altitude": altitude
        }
        
        self.fallback_history.append(fallback)
        return fallback
    
    def get_fallback_rate(self, window_seconds: int = 3600) -> float:
        """Retorna % de lecturas que usaron fallback en la ventana."""
        if not self.fallback_history:
            return 0.0
        return len([f for f in self.fallback_history[-100:]]) / max(1, len(self.fallback_history[-100:]))
