"""
Config Loader - Carga configuración dinámica de estación meteorológica.

Permite que MeteoSerV3 sea portable a cualquier ubicación sin cambiar código.
Lee de data/config_estacion.json y proporciona acceso centralizado.
"""
import json
import logging
import os
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigEstacion:
    """Gestor de configuración de estación meteorológica."""
    
    _instance = None
    _config = None
    
    def __init__(self, ruta_config: Optional[str] = None):
        """
        Inicializa config desde archivo JSON.
        
        Args:
            ruta_config: Ruta a config_estacion.json. 
                        Si None, busca en data/config_estacion.json
        """
        if ruta_config is None:
            # Buscar en ubicación relativa
            base_dir = Path(__file__).parent.parent.parent  # Subir a raíz proyecto
            ruta_config = base_dir / "data" / "config_estacion.json"
        
        ruta_config = Path(ruta_config)
        
        if not ruta_config.exists():
            logger.error(f"❌ Config no encontrada: {ruta_config}")
            raise FileNotFoundError(f"No existe {ruta_config}")
        
        try:
            with open(ruta_config, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"✅ Config cargada desde {ruta_config}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error JSON en config: {e}")
            raise
    
    @classmethod
    def obtener_instancia(cls, ruta_config: Optional[str] = None) -> 'ConfigEstacion':
        """
        Singleton: obtiene instancia única de config.
        
        Args:
            ruta_config: Solo se usa en primera llamada
        """
        if cls._instance is None:
            cls._instance = ConfigEstacion(ruta_config)
        return cls._instance
    
    @classmethod
    def resetear(cls):
        """Resetea singleton (útil para tests)."""
        cls._instance = None
        cls._config = None
    
    def get(self, ruta: str, default: Any = None) -> Any:
        """
        Accede a valor en config con notación de puntos.
        
        Args:
            ruta: "ubicacion.latitud_grados" accede a config["ubicacion"]["latitud_grados"]
            default: Valor si no existe
        
        Returns:
            Valor de config o default
        
        Ejemplo:
            >>> config.get("ubicacion.latitud_grados")
            41.5513
            >>> config.get("ubicacion.inexistente", -999)
            -999
        """
        partes = ruta.split('.')
        valor = self._config
        
        for parte in partes:
            if isinstance(valor, dict):
                valor = valor.get(parte)
                if valor is None:
                    return default
            else:
                return default
        
        return valor if valor is not None else default
    
    def get_ubicacion(self) -> Dict[str, float]:
        """Retorna datos de ubicación."""
        return {
            "latitud": self.get("ubicacion.latitud_grados"),
            "longitud": self.get("ubicacion.longitud_grados"),
            "altitud_suelo_m": self.get("ubicacion.altitud_suelo_m"),
            "altitud_sensor_m": self.get("ubicacion.altitud_sensor_m"),
            "altura_sobre_suelo_m": self.get("ubicacion.altura_sensor_sobre_suelo_m"),
        }
    
    def get_terreno(self) -> Dict[str, Any]:
        """Retorna datos de terreno."""
        return {
            "z0_calle_m": self.get("terreno.z0_calle_m"),
            "z0_terraza_m": self.get("terreno.z0_terraza_m"),
            "tipo_suelo": self.get("terreno.tipo_suelo"),
            "tipo_terreno": self.get("terreno.tipo_terreno"),
            "vegetacion_dominante": self.get("terreno.vegetacion_dominante"),
        }
    
    def get_suelo(self) -> Dict[str, float]:
        """Retorna valores por defecto de suelo."""
        return {
            "humedad_fraccion": self.get("suelo.humedad_fraccion_default", 0.25),
            "temperatura_c": self.get("suelo.temperatura_c_default", 15.0),
            "conductividad_w_mk": self.get("suelo.conductividad_w_mk_default", 0.8),
            "albedo": self.get("suelo.albedo_default", 0.23),
            "emisividad": self.get("suelo.emisividad_default", 0.95),
        }
    
    def get_sensores(self) -> Dict[str, Any]:
        """Retorna config de sensores."""
        return {
            "presion_fallback_hpa": self.get("sensores.presion_fallback_hpa", "AUTO"),
            "presion_altitud_base_m": self.get("sensores.presion_fallback_altitiud_base_m", 96.0),
            "ewma_alpha": self.get("sensores.ewma_alpha_default", 0.5),
            "intervalo_lectura_s": self.get("sensores.intervalo_lectura_s", 60),
            "timeout_s": self.get("sensores.timeout_sensor_s", 300),
        }
    
    def get_validacion(self) -> Dict[str, Any]:
        """Retorna config de validación."""
        return {
            "enabled": self.get("validacion.enabled", True),
            "rango_temperatura": self.get("validacion.rango_temperatura_c", [-99, 99]),
            "rango_presion": self.get("validacion.rango_presion_hpa", [800, 1100]),
            "rango_humedad": self.get("validacion.rango_humedad_pct", [0, 100]),
            "rango_viento": self.get("validacion.rango_viento_ms", [0, 50]),
            "outliers_enabled": self.get("validacion.deteccion_outliers_enabled", True),
            "outlier_iqr_mult": self.get("validacion.outlier_iqr_multiplicador", 1.5),
        }
    
    def get_cache(self) -> Dict[str, Any]:
        """Retorna config de caché."""
        return {
            "enabled": self.get("cache.enabled", True),
            "ttl_constantes_s": self.get("cache.ttl_constantes_s", 60),
            "ttl_indices_s": self.get("cache.ttl_indices_s", 300),
        }
    
    def __repr__(self) -> str:
        estacion = self.get("estacion.nombre", "DESCONOCIDA")
        lat = self.get("ubicacion.latitud_grados", 0)
        lon = self.get("ubicacion.longitud_grados", 0)
        return f"ConfigEstacion({estacion} @ {lat:.4f}°, {lon:.4f}°)"


# Función de conveniencia
def cargar_config(ruta: Optional[str] = None) -> ConfigEstacion:
    """Carga config singleton."""
    return ConfigEstacion.obtener_instancia(ruta)
