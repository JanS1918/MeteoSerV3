"""
Contexto Maestro Global - Información centralizada del sistema.
"""
import logging

logger = logging.getLogger(__name__)


class ContextoMaestro:
    """Contexto básico con información geográfica y temporal."""
    
    def __init__(self, elevation_ground=96.0, elevation_total=109.0, 
                 lat=41.5513, lon=2.3998, sensor_height_above_ground=13.0,
                 hora_utc=None, elevacion_solar=None, presion_barometrica=None, estado_suelo=None):
        import datetime
        self.elevation_ground = elevation_ground
        self.elevation_total = elevation_total
        self.lat = lat
        self.lon = lon
        self.sensor_height_above_ground = sensor_height_above_ground
        self.hora_utc = hora_utc or datetime.datetime.now(datetime.timezone.utc)
        self.elevacion_solar = elevacion_solar if elevacion_solar is not None else 45.0  # grados
        self.presion_barometrica = presion_barometrica if presion_barometrica is not None else 1013.25  # hPa
        self.estado_suelo = estado_suelo if estado_suelo is not None else {
            "humedad": 0.25,  # fracción volumétrica
            "temperatura": 15.0,  # °C
            "conductividad": 0.8  # W/mK
        }
        # Atributo estacion para Argentona_V3 (Directiva de Integridad ISA)
        self.estacion = "Argentona_V3"
        # Atributos adicionales para compatibilidad con perfil de viento
        self.z0_calle = 0.5  # Rugosidad típica zona urbana (m)
        self.z0_terraza = 0.03  # Rugosidad terraza (m)
    def actualizar_astronomia(self):
        import datetime
        self.hora_utc = datetime.datetime.now(datetime.timezone.utc)
        # Simulación simple de elevación solar
        hora = self.hora_utc.hour + self.hora_utc.minute / 60.0
        self.elevacion_solar = max(0.0, 90.0 * abs(12.0 - hora) / 12.0)


class ContextoMaestroGlobal:
    """Singleton global que proporciona contexto maestro a todo el sistema."""
    
    _instance = None
    
    @classmethod
    def obtener_contexto(cls, actualizar=False):
        """
        Obtiene la instancia global del contexto.
        
        Parámetros:
        -----------
        actualizar : bool
            Si True, actualiza el contexto (ej: astronomía)
            
        Retorna:
        --------
        ContextoMaestro
            Instancia con información geográfica y temporal
        """
        if cls._instance is None:
            # Crear con valores por defecto (Argentona, Barcelona)
            cls._instance = ContextoMaestro(
                elevation_ground=96.0,
                elevation_total=109.0,
                lat=41.5513,
                lon=2.3998,
                sensor_height_above_ground=13.0
            )
        
        if actualizar:
            cls._instance.actualizar_astronomia()
        
        return cls._instance
    
    @classmethod
    def establecer_contexto(cls, contexto):
        """Establece una instancia personalizada de contexto."""
        cls._instance = contexto
        return cls._instance
    
    @classmethod
    def resetear(cls):
        """Resetea el contexto al estado inicial."""
        cls._instance = None
