"""
BUS AUTO-CAPTURE V19.0 - Decorador Selectivo para Publicación Automática

Sistema inteligente de captura de diccionarios retornados por funciones.
Solo se publica lo explícitamente marcado.
Mantiene control total sobre nombres, prefijos y filtros.

Filosofía:
- NO intercepta todo ciegamente (eso sería caos)
- SÍ marca funciones específicas para auto-publicación
- SÍ añade prefijos claros por módulo
- SÍ filtra qué keys incluir/excluir
- SÍ mantiene la soberanía de datos
"""

import logging
from functools import wraps
from typing import Callable, Optional, List, Any, Dict
from threading import Lock

logger = logging.getLogger("meteoser.bus_auto_capture")


class BusAutoCapture:
    """
    Sistema de decoradores para captura selectiva y controlada.
    """

    # Thread-safe singleton para acceso al Bus
    _bus_instance = None
    _lock = Lock()

    @classmethod
    def set_bus_instance(cls, bus):
        """Registra la instancia del Bus global."""
        with cls._lock:
            cls._bus_instance = bus

    @classmethod
    def get_bus(cls):
        """Obtiene la instancia del Bus."""
        if cls._bus_instance is None:
            logger.warning("⚠️ Bus no registrado aún en BusAutoCapture")
        return cls._bus_instance

    @staticmethod
    def _infer_unit(key: str) -> str:
        """
        Inferencia inteligente de unidades basada en el nombre de la clave.
        
        Patrones soportados:
        - temp, temperatura → °C
        - humedad, hr, rh → %
        - presion, pressure → hPa
        - co2, dioxido → ppm
        - pm25, pm2.5 → µg/m³
        - viento, wind → km/h
        - radiacion, solar, irradiance → W/m²
        - lluvia, precipitacion, rain → mm
        - rocion → °C
        - velocidad → km/h
        Y más...
        """
        key_lower = key.lower()

        unit_patterns = {
            "°C": [
                "temp", "temperatura", "rocio", "dew", "tmin", "tmax", "tavg",
                "termometro", "air_temp", "dry_bulb", "wet_bulb",
            ],
            "%": [
                "humedad", "hr", "rh", "humidity", "relative_humidity",
                "humedad_relativa", "moisture", "saturation",
            ],
            "hPa": [
                "presion", "pressure", "barometric", "barometrica", "presion_atmosferica",
                "pa", "hectopascal",
            ],
            "ppm": [
                "co2", "dioxido", "carbono", "carbon_dioxide", "co2_concentration",
                "ch4", "metano", "n2o", "oxido_nitroso",
            ],
            "µg/m³": [
                "pm25", "pm2.5", "pm10", "particulado", "particulate",
                "material_particulado", "no2", "so2", "o3", "ozono",
            ],
            "km/h": [
                "viento", "wind", "velocidad", "speed", "velocidad_viento",
                "wind_speed", "racha", "gust",
            ],
            "W/m²": [
                "radiacion", "solar", "irradiance", "irradiancia", "radiation",
                "shortwave", "uvi", "uv",
            ],
            "mm": [
                "lluvia", "precipitacion", "rain", "rainfall", "precip",
                "acumulada", "accumulated", "grosor", "espesor",
            ],
            "m/s": [
                "velocidad_ms", "speed_ms", "metro_segundo",
            ],
            "°": [
                "direccion", "direction", "azimuth", "angulo", "angle",
                "rumbo", "bearing", "orientacion",
            ],
            "índice": [
                "index", "indice", "score", "puntuacion", "escala",
                "calidad", "quality", "confort", "comfort", "peligro", "danger",
            ],
            "valor": [
                "count", "contador", "cantidad", "numero", "number",
                "magnitud", "magnitude", "valor", "value",
            ],
        }

        for unit, patterns in unit_patterns.items():
            if any(pattern in key_lower for pattern in patterns):
                return unit

        return "valor"  # Fallback

    @staticmethod
    def publish_dict(
        prefix: str,
        include_keys: Optional[List[str]] = None,
        exclude_keys: Optional[List[str]] = None,
        auto_unit: bool = True,
    ):
        """
        Decorador para marcar funciones que retornan Dict para auto-publicación.

        Args:
            prefix: Prefijo para las claves (ej: "pred_lluvia", "sensor_virtual")
            include_keys: Lista de keys a incluir (None = todas)
            exclude_keys: Lista de keys a excluir
            auto_unit: Si True, infiere unidades automáticamente

        Ejemplo:
            @BusAutoCapture.publish_dict("pred_temp", include_keys=["temp_6h", "temp_12h"])
            def predecir_temperatura(...):
                return {"temp_6h": 22.5, "temp_12h": 20.0, "_internal": 0}
                # Publica: pred_temp_temp_6h, pred_temp_temp_12h
                # NO publica: pred_temp__internal
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)

                # Procesar si retorna Dict
                if isinstance(result, dict):
                    bus = BusAutoCapture.get_bus()
                    if bus is None:
                        logger.warning(
                            f"⚠️ Bus no disponible para {prefix}.{func.__name__}"
                        )
                        return result

                    published_count = 0

                    for key, value in result.items():
                        # Aplicar filtros
                        if exclude_keys and key in exclude_keys:
                            continue

                        if include_keys and key not in include_keys:
                            continue

                        # Evitar variables internas (_temp, __flag, etc)
                        if key.startswith("_"):
                            continue

                        # Construir nombre completo
                        full_name = f"{prefix}_{key}"

                        # Inferir unidad
                        unit = (
                            BusAutoCapture._infer_unit(key) if auto_unit else "valor"
                        )

                        # Manejar valores anidados
                        try:
                            if isinstance(value, dict):
                                # Publicar recursivamente
                                BusAutoCapture._publish_nested(
                                    bus, full_name, value, auto_unit
                                )
                                published_count += 1
                            elif isinstance(value, (int, float, bool, str)):
                                bus.publicar(full_name, value, unit)
                                published_count += 1
                        except Exception as e:
                            logger.warning(
                                f"⚠️ Error publicando {full_name}: {e}"
                            )

                    if published_count > 0:
                        logger.debug(
                            f"✅ {func.__name__}: {published_count} valores publicados bajo '{prefix}'"
                        )

                return result

            return wrapper

        return decorator

    @staticmethod
    def _publish_nested(
        bus, base_name: str, data: Dict[str, Any], auto_unit: bool = True, depth: int = 0
    ):
        """
        Publica recursivamente diccionarios anidados.
        Limita profundidad para evitar infinitos.
        """
        if depth > 3:  # Limitar profundidad
            return

        for key, value in data.items():
            if key.startswith("_"):
                continue

            full_name = f"{base_name}_{key}"

            if isinstance(value, dict):
                BusAutoCapture._publish_nested(bus, full_name, value, auto_unit, depth + 1)
            elif isinstance(value, (int, float, bool, str)):
                unit = BusAutoCapture._infer_unit(key) if auto_unit else "valor"
                try:
                    bus.publicar(full_name, value, unit)
                except Exception as e:
                    logger.warning(f"⚠️ Error publicando nested {full_name}: {e}")

    @staticmethod
    def publish_value(prefix: str, auto_unit: bool = True):
        """
        Decorador simple para funciones que retornan valores únicos.

        Ejemplo:
            @BusAutoCapture.publish_value("pred")
            def predecir_lluvia_6h(...):
                return 85.5  # Se publica como "pred_lluvia_6h" = 85.5
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)

                if result is not None:
                    bus = BusAutoCapture.get_bus()
                    if bus is None:
                        return result

                    full_name = f"{prefix}_{func.__name__}"
                    unit = (
                        BusAutoCapture._infer_unit(full_name) if auto_unit else "valor"
                    )

                    try:
                        bus.publicar(full_name, result, unit)
                    except Exception as e:
                        logger.warning(f"⚠️ Error publicando {full_name}: {e}")

                return result

            return wrapper

        return decorator


# Alias corto para uso frecuente
capture_dict = BusAutoCapture.publish_dict
capture_value = BusAutoCapture.publish_value
