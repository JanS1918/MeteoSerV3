# Estructura de datos y jerarquía de valores MeteoSer
from typing import List, Dict, Optional
import enum

class Fiabilidad(enum.Enum):
    ALTA = 'alta'
    MEDIA = 'media'
    BAJA = 'baja'
    FALLA = 'falla'

class ValorSistema:
    def __init__(
        self,
        nombre: str,
        tipo: str,
        valor: float,
        unidad: str,
        fiabilidad: Fiabilidad,
        icono: str,
        prioridad: int,
        sensores: Optional[List[str]] = None,
        dependencias: Optional[List[str]] = None,
        alerta: Optional[str] = None,
        cambios: int = 0,
        estabilizado: bool = True,
        loop_detectado: bool = False,
    ):
        self.nombre = nombre
        self.tipo = tipo
        self.valor = valor
        self.unidad = unidad
        self.fiabilidad = fiabilidad
        self.icono = icono
        self.prioridad = prioridad
        self.sensores = sensores or []
        self.dependencias = dependencias or []
        self.alerta = alerta
        self.cambios = cambios
        self.estabilizado = estabilizado
        self.loop_detectado = loop_detectado

class GrupoValores:
    def __init__(self, nombre: str, icono: str, valores: List[ValorSistema], prioridad: int):
        self.nombre = nombre
        self.icono = icono
        self.valores = sorted(valores, key=lambda v: v.prioridad, reverse=True)
        self.prioridad = prioridad

class JerarquiaUI:
    def __init__(self, grupos: List[GrupoValores]):
        self.grupos = sorted(grupos, key=lambda g: g.prioridad, reverse=True)

# Ejemplo de inicialización (se completará dinámicamente desde el sistema)
def ejemplo_jerarquia():
    temp = ValorSistema('Temperatura', 'sensor', 21.5, '°C', Fiabilidad.ALTA, 'icon-temp', 100, ['sensor_temp'], ['UTCI'])
    sensacion = ValorSistema('Sensación térmica', 'índice', 20.0, '°C', Fiabilidad.MEDIA, 'icon-sensacion', 90, ['sensor_temp', 'sensor_hum'], ['UTCI'])
    humedad = ValorSistema('Humedad relativa', 'sensor', 60, '%', Fiabilidad.ALTA, 'icon-humedad', 80, ['sensor_hum'])
    grupo_temp = GrupoValores('Temperatura & Humedad', 'icon-grupo-temp', [temp, sensacion, humedad], 100)
    # ...otros grupos y valores...
    return JerarquiaUI([grupo_temp])
