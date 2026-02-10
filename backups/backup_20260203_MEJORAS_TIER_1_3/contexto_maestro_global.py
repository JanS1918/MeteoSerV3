"""
Contexto Maestro Global - Información centralizada del sistema.
Ahora carga parámetros de configuración dinámicamente.
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ContextoMaestro:
    """Contexto básico con información geográfica y temporal."""
    
    def __init__(self, elevation_ground=None, elevation_total=None, 
                 lat=None, lon=None, sensor_height_above_ground=None,
                 hora_utc=None, elevacion_solar=None, presion_barometrica=None, 
                 estado_suelo=None, usar_config=True):
        """
        Inicializa contexto maestro.
        
        Si usar_config=True (default), lee de config_estacion.json.
        Los parámetros explícitos sobrescriben valores de config.
        """
        import datetime
        
        # Intentar cargar config dinámica
        config = None
        if usar_config:
            try:
                from core.config.config_loader import cargar_config
                config = cargar_config()
                ubi = config.get_ubicacion()
                terreno = config.get_terreno()
                suelo = config.get_suelo()
                
                # Usar valores de config si no fueron sobrescritos
                elevation_ground = elevation_ground or ubi.get("altitud_suelo_m", 96.0)
                elevation_total = elevation_total or ubi.get("altitud_sensor_m", 109.0)
                lat = lat or ubi.get("latitud", 41.5513)
                lon = lon or ubi.get("longitud", 2.3998)
                sensor_height_above_ground = sensor_height_above_ground or ubi.get("altura_sobre_suelo_m", 13.0)
                
                # Terreno de config
                z0_calle = terreno.get("z0_calle_m", 0.5)
                z0_terraza = terreno.get("z0_terraza_m", 0.03)
                
                # Estado suelo por defecto de config
                if estado_suelo is None:
                    estado_suelo = {
                        "humedad": suelo.get("humedad_fraccion", 0.25),
                        "temperatura": suelo.get("temperatura_c", 15.0),
                        "conductividad": suelo.get("conductividad_w_mk", 0.8)
                    }
                
                logger.info(f"✅ Config dinámico cargado: {config}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo cargar config dinámico: {e}. Usando defaults.")
                elevation_ground = elevation_ground or 96.0
                elevation_total = elevation_total or 109.0
                lat = lat or 41.5513
                lon = lon or 2.3998
                sensor_height_above_ground = sensor_height_above_ground or 13.0
                z0_calle = 0.5
                z0_terraza = 0.03
        else:
            # Modo sin config, solo defaults
            elevation_ground = elevation_ground or 96.0
            elevation_total = elevation_total or 109.0
            lat = lat or 41.5513
            lon = lon or 2.3998
            sensor_height_above_ground = sensor_height_above_ground or 13.0
            z0_calle = 0.5
            z0_terraza = 0.03
        
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
        # Atributo estacion
        self.estacion = "Argentona_V3"
        # Atributos de terreno desde config
        self.z0_calle = z0_calle  # Rugosidad zona urbana
        self.z0_terraza = z0_terraza  # Rugosidad terraza
        # Config object
        self._config = config
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
