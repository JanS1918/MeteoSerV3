# Contexto Maestro Global - Información centralizada del sistema.
# Ahora carga parámetros de configuración dinámicamente y publica automáticamente al Bus de Capas de Información.
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from core.system.constants import ESTACION

logger = logging.getLogger(__name__)


class ContextoMaestro:
    # Contexto básico con información geográfica y temporal.
    def __init__(self, elevation_ground=None, elevation_total=None, lat=None, lon=None, sensor_height_above_ground=None, hora_utc=None, elevacion_solar=None, presion_barometrica=None, estado_suelo=None, usar_config=True):
        # Inicializa atributos
        self.elevation_ground = elevation_ground
        self.elevation_total = elevation_total
        self.lat = lat
        self.lon = lon
        self.sensor_height_above_ground = sensor_height_above_ground
        self.hora_utc = hora_utc
        self.elevacion_solar = elevacion_solar
        self.presion_barometrica = presion_barometrica
        self.estado_suelo = estado_suelo or {}
        self.usar_config = usar_config
        self.z0_calle = 0.3  # Rugosidad del terreno (m) - Argentona zona urbana costera
        # Calcular la estación del año
        self.estacion = self._calcular_estacion()

        # Publicar valores físicos en el bus
        try:
            from core.bus.bus_capas_informacion import obtener_bus
            from physical_constants_bus import PHYSICAL_CONSTANTS
            bus = obtener_bus()
            for nombre, datos in PHYSICAL_CONSTANTS.items():
                bus.publicar(
                    variable=f"contexto.fisica.{nombre}",
                    valor=datos['valor'],
                    nivel="CORE",
                    origen="core.context.ContextoMaestro",
                    confianza=1.0,
                    unidad=datos.get('unidad', ''),
                    notas=f"{datos.get('fuente', '')} | {datos.get('justificación', '')}"
                )
        except Exception as e:
            logger.warning(f"Error al publicar valores físicos en el bus: {e}")
    def actualizar_astronomia(self):
        import datetime
        from core.arcos_solares import calcular_posicion_sol
        self.hora_utc = datetime.datetime.now(datetime.timezone.utc)
        datos_sol = calcular_posicion_sol(self.lat, self.lon, self.hora_utc, altitud_m=self.elevation_ground)
        elevacion = datos_sol.get("elevacion_solar_deg")
        self.elevacion_solar = max(0.0, elevacion) if elevacion is not None else 0.0
    
    def _calcular_estacion(self):
        """Calcula la estación del año basado en el día del año."""
        from datetime import datetime
        ahora = datetime.now()
        dia_ano = ahora.timetuple().tm_yday
        
        # Definir los días de transición de estaciones (aproximados)
        dia_equinoccio_primavera = 80
        dia_solsticio_verano = 172
        dia_equinoccio_otono = 266
        dia_solsticio_invierno = 355
        
        if dia_equinoccio_primavera <= dia_ano < dia_solsticio_verano:
            return "primavera"
        elif dia_solsticio_verano <= dia_ano < dia_equinoccio_otono:
            return "verano"
        elif dia_equinoccio_otono <= dia_ano < dia_solsticio_invierno:
            return "otono"
        else:
            return "invierno"


class ContextoMaestroGlobal:
    # Singleton global que proporciona contexto maestro a todo el sistema.
    
    _instance = None
    
    @classmethod
    def obtener_contexto(cls, actualizar=False):
        if cls._instance is None:
            # Crear con valores por defecto (Argentona, Barcelona)
            cls._instance = ContextoMaestro(
                elevation_ground=ESTACION.ALTITUD - 13.0,
                elevation_total=ESTACION.ALTITUD,
                lat=ESTACION.LATITUD,
                lon=ESTACION.LONGITUD,
                sensor_height_above_ground=13.0
            )
        
        if actualizar:
            cls._instance.actualizar_astronomia()
        
        return cls._instance
    
    @classmethod
    def establecer_contexto(cls, contexto):
        cls._instance = contexto
        return cls._instance
    @classmethod
    def resetear(cls):
        cls._instance = None
