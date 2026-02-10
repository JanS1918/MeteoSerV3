from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from core.indices.bus_estado_global import BusEstadoGlobal
from core.system.constants import ESTACION

class Ubicacion(BaseModel):
    latitud: float = Field(default=0.0)
    longitud: float = Field(default=0.0)
    altitud: float = Field(default=0.0)

class EstadoPanel(BaseModel):
    ubicacion: Ubicacion
    temperatura: float = Field(default=0.0)
    humedad: float = Field(default=0.0)
    presion: float = Field(default=1013.25)
    cajones: List[Any] = Field(default_factory=list)
    factor_z: float = Field(default=1.0)
    vector_26: float = Field(default=0.0)
    # Puedes añadir más campos según el Bus
    otros: Dict[str, Any] = Field(default_factory=dict)


def serializar_estado_atomico(bus: Optional[BusEstadoGlobal] = None) -> EstadoPanel:
    bus = bus or BusEstadoGlobal.obtener_instancia()
    # Extraer ubicación
    lat = bus._estado.get("latitud", ESTACION.LATITUD)
    lon = bus._estado.get("longitud", ESTACION.LONGITUD)
    alt = bus._estado.get("altitud", ESTACION.ALTITUD - 13.0)
    ubicacion = Ubicacion(latitud=float(lat or 0.0), longitud=float(lon or 0.0), altitud=float(alt or 0.0))
    # Extraer sensores principales
    temperatura = float(bus._estado.get("temperatura", 0.0) or 0.0)
    humedad = float(bus._estado.get("humedad", 0.0) or 0.0)
    presion = float(bus._estado.get("presion", 1013.25) or 1013.25)
    # Factor Z y Vector #26
    factor_z = float(bus._estado.get("factor_z", 1.0) or 1.0)
    vector_26 = float(bus._estado.get("vector_26", 0.0) or 0.0)
    # Cajones (array, puede estar vacío)
    cajones = bus._estado.get("cajones", [])
    if cajones is None:
        cajones = []
    # Otros datos: todo lo demás
    otros = {k: v for k, v in bus._estado.items() if k not in {"latitud", "longitud", "altitud", "temperatura", "humedad", "presion", "factor_z", "vector_26", "cajones"}}
    return EstadoPanel(
        ubicacion=ubicacion,
        temperatura=temperatura,
        humedad=humedad,
        presion=presion,
        cajones=cajones,
        factor_z=factor_z,
        vector_26=vector_26,
        otros=otros
    )
