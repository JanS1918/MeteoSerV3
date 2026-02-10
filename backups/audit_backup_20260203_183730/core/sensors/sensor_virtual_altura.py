"""
Sensor Virtual Altura - Publica altura del sensor de forma automática en el bus.

Permite que Monin-Obukhov y otras fórmulas lean 'z' del bus en lugar de
estar hardcodeadas. Se actualiza desde ContextoMaestro.
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SensorVirtualAltura:
    """Sensor virtual que publica altura del sensor en el bus de estado."""
    
    def __init__(self, bus=None):
        """
        Inicializa sensor virtual.
        
        Args:
            bus: BusEstadoGlobal instance (opcional)
        """
        self.bus = bus
        self.altura_efectiva_m = 2.0  # Altura por defecto para cálculos (z)
        self.z0_m = 0.5  # Rugosidad por defecto
        self.elevacion_suelo_m = 96.0  # Elevación del terreno
        self.elevacion_sensor_m = 109.0  # Elevación del sensor
    
    def actualizar_desde_contexto(self, contexto) -> None:
        """
        Actualiza valores del sensor desde ContextoMaestro.
        
        Args:
            contexto: ContextoMaestro con información de ubicación
        """
        if contexto is None:
            return
        
        try:
            # Altura efectiva para cálculos (típicamente 2 m para condiciones estándar)
            self.altura_efectiva_m = getattr(contexto, 'sensor_height_above_ground', 2.0)
            
            # Rugosidad del terreno
            self.z0_m = getattr(contexto, 'z0_calle', 0.5)
            
            # Elevaciones
            self.elevacion_suelo_m = getattr(contexto, 'elevation_ground', 96.0)
            self.elevacion_sensor_m = getattr(contexto, 'elevation_total', 109.0)
            
            logger.debug(f"✅ Sensor virtual altura actualizado desde contexto")
            
            # Publicar en bus si existe
            if self.bus:
                self._publicar_en_bus()
        
        except Exception as e:
            logger.warning(f"⚠️ Error actualizando sensor virtual: {e}")
    
    def _publicar_en_bus(self) -> None:
        """Publica valores del sensor en el bus de estado."""
        if self.bus is None:
            return
        
        try:
            # Publicar altura efectiva
            self.bus.publicar("altura_sensor_efectiva_m", self.altura_efectiva_m, metadata={
                "tipo": "altura_efectiva",
                "unidad": "m",
                "fuente": "sensor_virtual_altura",
                "fiabilidad": 1.0,
                "descripcion": "Altura efectiva para cálculos micrometereológicos"
            })
            
            # Publicar rugosidad
            self.bus.publicar("rugosidad_z0_m", self.z0_m, metadata={
                "tipo": "rugosidad",
                "unidad": "m",
                "fuente": "sensor_virtual_altura",
                "fiabilidad": 1.0,
                "descripcion": "Longitud de rugosidad del terreno"
            })
            
            # Publicar elevaciones
            self.bus.publicar("elevacion_suelo_m", self.elevacion_suelo_m, metadata={
                "tipo": "elevacion",
                "unidad": "m",
                "fuente": "sensor_virtual_altura",
                "fiabilidad": 1.0,
                "descripcion": "Elevación del nivel del suelo sobre nivel del mar"
            })
            
            self.bus.publicar("elevacion_sensor_m", self.elevacion_sensor_m, metadata={
                "tipo": "elevacion",
                "unidad": "m",
                "fuente": "sensor_virtual_altura",
                "fiabilidad": 1.0,
                "descripcion": "Elevación del sensor sobre nivel del mar"
            })
            
            logger.debug("📡 Sensor virtual altura publicado en bus")
        
        except Exception as e:
            logger.warning(f"⚠️ Error publicando sensor virtual en bus: {e}")
    
    def obtener_altura_efectiva(self) -> float:
        """Retorna altura efectiva para cálculos."""
        return self.altura_efectiva_m
    
    def obtener_z0(self) -> float:
        """Retorna rugosidad del terreno."""
        return self.z0_m
    
    def obtener_elevacion_sensor(self) -> float:
        """Retorna elevación del sensor sobre nivel del mar."""
        return self.elevacion_sensor_m
    
    def obtener_dict(self) -> Dict[str, float]:
        """Retorna todos los valores como diccionario."""
        return {
            "altura_efectiva_m": self.altura_efectiva_m,
            "z0_m": self.z0_m,
            "elevacion_suelo_m": self.elevacion_suelo_m,
            "elevacion_sensor_m": self.elevacion_sensor_m,
            "altura_sobre_suelo_m": self.elevacion_sensor_m - self.elevacion_suelo_m,
        }
    
    def __repr__(self) -> str:
        return (f"SensorVirtualAltura(z={self.altura_efectiva_m}m, "
                f"z0={self.z0_m}m, elev={self.elevacion_sensor_m}m)")


def crear_sensor_virtual_altura(contexto=None, bus=None) -> SensorVirtualAltura:
    """
    Factory para crear sensor virtual altura.
    
    Args:
        contexto: ContextoMaestro (opcional)
        bus: BusEstadoGlobal (opcional)
    
    Returns:
        SensorVirtualAltura configurado
    """
    sensor = SensorVirtualAltura(bus)
    if contexto:
        sensor.actualizar_desde_contexto(contexto)
    return sensor


if __name__ == "__main__":
    # Test
    print("╔════════════════════════════════════════════╗")
    print("║   Test SensorVirtualAltura                ║")
    print("╚════════════════════════════════════════════╝\n")
    
    sensor = SensorVirtualAltura()
    
    print("Valores por defecto:")
    for k, v in sensor.obtener_dict().items():
        print(f"  {k}: {v}")
    
    print(f"\n{sensor}")
