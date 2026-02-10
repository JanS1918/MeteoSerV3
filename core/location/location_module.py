"""
Módulo de Ubicación y Astronomía - MeteoSer

Recuperado del backup ojo_20260202_102049
Responsabilidades:
- Detectar ubicación desde múltiples fuentes
- Calcular arco solar y radiación
- Calcula amanecer/atardecer (astronómico e híbrido)
- Estimar nubosidad
- Calcular índices astronómicos

Motores que dependen de este módulo:
- luz_natural, ritmo_circadiano, nocturno, ambiental, confort, radiación_uv
"""

import datetime
import math
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE VALIDACIÓN Y PARSEO
# ═══════════════════════════════════════════════════════════════════════════

def coords_valid(lat: Any, lon: Any) -> bool:
    """
    Validar que lat/lon estén dentro de rangos geográficos válidos.
    
    Args:
        lat: Latitud (puede ser None, str, o float)
        lon: Longitud (puede ser None, str, o float)
    
    Returns:
        True si ambas coordenadas son válidas, False en caso contrario
    """
    try:
        if lat is None or lon is None:
            return False
        lat_f = float(lat)
        lon_f = float(lon)
        return (-90 <= lat_f <= 90) and (-180 <= lon_f <= 180)
    except (ValueError, TypeError):
        return False


def parse_coord(val: Any) -> Optional[float]:
    """
    Parsear múltiples formatos de coordenadas (grados, con decimales, con cardinales).
    
    Soporta:
    - "41.5507" → 41.5507
    - "41.5507N" o "41.5507n" → 41.5507
    - "41.5507S" o "41.5507s" → -41.5507
    - "2.397W" o "2.397w" → -2.397
    - "2.397E" o "2.397e" → 2.397
    - "41,5507" (coma decimal) → 41.5507
    
    Args:
        val: Valor a parsear (puede ser None, str, int, float)
    
    Returns:
        Coordenada como float, o None si no es válida
    """
    if val is None:
        return None
    
    try:
        s = str(val).strip().lower().replace(',', '.')
        sign = 1.0
        
        # Detectar cardinales (N, S, E, O, W)
        if s and s[-1] in ('n', 's', 'e', 'o', 'w'):
            suffix = s[-1]
            s = s[:-1].strip()
            if suffix in ('s', 'o', 'w'):  # Sur, Oeste (Oeste = "O" o "W")
                sign = -1.0
        
        return float(s) * sign
    except (ValueError, TypeError, AttributeError):
        return None


def coords_es_spain(lat: Any, lon: Any) -> bool:
    """
    Validar que las coordenadas correspondan a España continental.
    
    Rango aproximado:
    - Latitud: 35° - 44.5°N
    - Longitud: -10° - 4.5°E
    
    Args:
        lat: Latitud
        lon: Longitud
    
    Returns:
        True si está dentro de España, False en caso contrario
    """
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        return (35 <= lat_f <= 44.5) and (-10 <= lon_f <= 4.5)
    except (ValueError, TypeError):
        return False


# ═══════════════════════════════════════════════════════════════════════════
# DETECCIÓN DE UBICACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def detect_location(
    system: Any,
    config_path: str = "config.txt",
    fallback_lat: float = 41.553267,
    fallback_lon: float = 2.396845,
) -> Dict[str, Any]:
    """
    Detectar ubicación jerárquicamente:
    1. Config file (manual)
    2. Sensores (si hay sensores de ubicación)
    3. SystemManager (si guardó coordenadas previamente)
    4. Fallback (constantes selladas para Argentona)
    
    Args:
        system: SystemManager o SystemCore con sensores
        config_path: Ruta al archivo de configuración
        fallback_lat: Latitud fallback
        fallback_lon: Longitud fallback
    
    Returns:
        Dict con {"lat": float, "lon": float, "origen": str}
        origen ∈ {"manual", "sensor", "manager", "fallback"}
    """
    latitud = None
    longitud = None
    origen = "fallback"
    
    # OPCIÓN 1: Leer de config file
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            for line in f:
                if "latitud" in line.lower():
                    latitud = parse_coord(line.split(":")[-1].strip())
                if "longitud" in line.lower():
                    longitud = parse_coord(line.split(":")[-1].strip())
        
        if coords_valid(latitud, longitud):
            origen = "manual"
            return {
                "lat": float(latitud),
                "lon": float(longitud),
                "origen": origen,
            }
    except Exception as e:
        logger.debug(f"No config file at {config_path}: {e}")
    
    # OPCIÓN 2: Leer de sensores
    try:
        sensores = system.sensores if hasattr(system, 'sensores') else {}
        lat_sensor = sensores.get("latitud") or sensores.get("lat")
        lon_sensor = sensores.get("longitud") or sensores.get("lon")
        
        if lat_sensor is not None and lon_sensor is not None:
            latitud = parse_coord(lat_sensor)
            longitud = parse_coord(lon_sensor)
            if coords_valid(latitud, longitud):
                origen = "sensor"
                return {
                    "lat": float(latitud),
                    "lon": float(longitud),
                    "origen": origen,
                }
    except Exception as e:
        logger.debug(f"Error reading sensor coordinates: {e}")
    
    # OPCIÓN 3: Consultar SystemManager
    try:
        if hasattr(system, 'obtener_coordenadas'):
            coords = system.obtener_coordenadas()
            if coords and isinstance(coords, dict):
                latitud = coords.get("lat")
                longitud = coords.get("lon")
                if coords_valid(latitud, longitud):
                    origen = coords.get("origen", "manager")
                    return {
                        "lat": float(latitud),
                        "lon": float(longitud),
                        "origen": origen,
                    }
    except Exception as e:
        logger.debug(f"Error querying SystemManager: {e}")
    
    # OPCIÓN 4: Fallback
    logger.warning(f"Using fallback coordinates (Argentona): {fallback_lat}, {fallback_lon}")
    return {
        "lat": fallback_lat,
        "lon": fallback_lon,
        "origen": "fallback",
    }


# ═══════════════════════════════════════════════════════════════════════════
# CÁLCULOS ASTRONÓMICOS
# ═══════════════════════════════════════════════════════════════════════════

def arco_solar(lat_deg: float, day_of_year: int) -> float:
    """
    Calcular el arco solar (ángulo recorrido por el sol en el día).
    
    Aproximación: ω₀ = 2 × arccos(-tan(lat) × tan(δ))
    donde δ = 23.44° × sin(2π × (day - 81) / 365)
    
    Args:
        lat_deg: Latitud en grados
        day_of_year: Día del año (1-366)
    
    Returns:
        Arco solar en grados
    """
    try:
        lat_rad = math.radians(lat_deg)
        delta = math.radians(23.44 * math.sin(2 * math.pi * (day_of_year - 81) / 365.0))
        
        arg = -math.tan(lat_rad) * math.tan(delta)
        arg = max(-1.0, min(1.0, arg))  # Clamp a [-1, 1]
        
        omega_0 = math.degrees(math.acos(arg))
        return 2 * omega_0
    except Exception as e:
        logger.warning(f"Error calculating solar arc: {e}")
        return 180.0  # Aproximación neutra


def radiacion_teorica(lat_deg: float, day_of_year: int, hora_decimal: float) -> float:
    """
    Calcular radiación solar teórica (W/m²) en una hora específica.
    
    Modelo: sin(h) = sin(φ)×sin(δ) + cos(φ)×cos(δ)×cos(ω)
    donde h = altura solar, φ = latitud, δ = declinación, ω = ángulo horario
    
    Luego: I = Gsc × Dr × sin(h)
    
    Args:
        lat_deg: Latitud en grados
        day_of_year: Día del año (1-366)
        hora_decimal: Hora como decimal (0-24)
    
    Returns:
        Irradiancia solar en W/m² (0 si está bajo el horizonte)
    """
    try:
        lat_rad = math.radians(lat_deg)
        delta = math.radians(23.44 * math.sin(2 * math.pi * (day_of_year - 81) / 365.0))
        omega = math.radians((hora_decimal - 12.0) * 15.0)
        
        sin_alt = (
            math.sin(lat_rad) * math.sin(delta) +
            math.cos(lat_rad) * math.cos(delta) * math.cos(omega)
        )
        
        if sin_alt <= 0:
            return 0.0
        
        # Constante solar (GSC) y distancia relativa (Dr)
        gsc = 1361.0  # W/m² (constante solar)
        dr = 1.0 + 0.033 * math.cos(2 * math.pi * day_of_year / 365.0)
        
        return gsc * dr * sin_alt
    except Exception as e:
        logger.warning(f"Error calculating theoretical radiation: {e}")
        return 0.0


# ═══════════════════════════════════════════════════════════════════════════
# UTILIDADES DE TIEMPO
# ═══════════════════════════════════════════════════════════════════════════

def hhmm_a_minutos(hhmm: str) -> Optional[int]:
    """
    Convertir formato HH:MM a minutos totales desde medianoche.
    
    Args:
        hhmm: String en formato "HH:MM"
    
    Returns:
        Minutos totales, o None si formato es inválido
    """
    try:
        if not hhmm or ":" not in str(hhmm):
            return None
        h, m = str(hhmm).split(":")[:2]
        return int(h) * 60 + int(m)
    except (ValueError, AttributeError, IndexError):
        return None


def minutos_a_hhmm(total_min: int) -> str:
    """
    Convertir minutos totales a formato HH:MM.
    
    Args:
        total_min: Minutos desde medianoche
    
    Returns:
        String en formato "HH:MM"
    """
    try:
        total_min = int(total_min) % (24 * 60)  # Normalizar a 0-1439
        h = total_min // 60
        m = total_min % 60
        return f"{h:02d}:{m:02d}"
    except (ValueError, TypeError):
        return "--:--"


# ═══════════════════════════════════════════════════════════════════════════
# AMANECER/ATARDECER INTEGRADORES
# ═══════════════════════════════════════════════════════════════════════════

def calcular_anejo_astronomico(
    lat: float,
    lon: float,
    sensores: Dict[str, Any],
    indices: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calcular todo lo relativo a amanecer/atardecer (astronómico, sensor e híbrido).
    
    Integra:
    - Amanecer/atardecer astronómico (función externa tools.amanecer_atardecer)
    - Detección sensor (radiación y UV)
    - Lógica híbrida (reconciliar sensores con astronomía)
    
    Args:
        lat: Latitud
        lon: Longitud
        sensores: Dict de sensores {clave: valor}
        indices: Dict de índices donde se actualizarán resultados
    
    Returns:
        Dict actualizado con máximo de claves
    """
    try:
        # Importar herramienta externa
        from tools.amanecer_atardecer import calcular_amanecer_atardecer
        
        # Obtener offset UTC y día del año
        try:
            from zoneinfo import ZoneInfo
            ahora = datetime.datetime.now(ZoneInfo("Europe/Madrid"))
            utc_offset = ahora.utcoffset()
            utc_offset = int(utc_offset.total_seconds() / 3600) if utc_offset else 1
        except Exception:
            try:
                utc_offset = datetime.datetime.now().astimezone().utcoffset()
                utc_offset = int(utc_offset.total_seconds() / 3600) if utc_offset else 1
            except Exception:
                utc_offset = 1  # Fallback a GMT+1
        
        hoy = datetime.datetime.now().timetuple().tm_yday
        
        # Calcular amanecer/atardecer astronómico
        horas_sol = calcular_amanecer_atardecer(lat, lon, hoy, utc_offset)
        amanecer_astro = horas_sol.get("amanecer", "--:--")
        atardecer_astro = horas_sol.get("atardecer", "--:--")
        
        # Hora actual en minutos desde medianoche
        now = datetime.datetime.now()
        ahora_min = now.hour * 60 + now.minute
        amanecer_min = hhmm_a_minutos(amanecer_astro)
        atardecer_min = hhmm_a_minutos(atardecer_astro)
        
        # Detectar si es día según sensores
        rad = sensores.get("radiacion")
        uv = sensores.get("uv")
        try:
            rad_val = float(rad) if rad is not None else None
        except (ValueError, TypeError):
            rad_val = None
        try:
            uv_val = float(uv) if uv is not None else None
        except (ValueError, TypeError):
            uv_val = None
        
        es_dia_sensor = False
        if rad_val is not None and rad_val >= 50:
            es_dia_sensor = True
        if uv_val is not None and uv_val > 0.1:
            es_dia_sensor = True
        
        # Detectar si es día según astronomía
        es_dia_astronomico = None
        if amanecer_min is not None and atardecer_min is not None:
            if amanecer_min <= atardecer_min:
                es_dia_astronomico = amanecer_min <= ahora_min <= atardecer_min
            else:  # En polos, amanecer > atardecer
                es_dia_astronomico = (ahora_min >= amanecer_min or ahora_min <= atardecer_min)
        
        # Lógica híbrida: reconciliar sensor con astronomía
        amanecer_hibrido = amanecer_astro
        atardecer_hibrido = atardecer_astro
        ventana_min = 90  # Ventana de tolerancia en minutos
        umbral_desvio_min = 30  # Desvío máximo aceptado
        
        # Si astronomía dice "noche" pero sensores dicen "día", y estamos cerca del amanecer
        if es_dia_astronomico is False and es_dia_sensor and amanecer_min is not None:
            if abs(ahora_min - amanecer_min) <= ventana_min:
                amanecer_hibrido = minutos_a_hhmm(ahora_min)
        
        # Si astronomía dice "día" pero sensores dicen "noche", y estamos cerca del atardecer
        if es_dia_astronomico is True and not es_dia_sensor and atardecer_min is not None:
            if abs(ahora_min - atardecer_min) <= ventana_min:
                atardecer_hibrido = minutos_a_hhmm(ahora_min)
        
        # Actualizar índices
        indices["amanecer_astronomico"] = amanecer_astro
        indices["atardecer_astronomico"] = atardecer_astro
        indices["amanecer_hibrido"] = amanecer_hibrido
        indices["atardecer_hibrido"] = atardecer_hibrido
        indices["amanecer"] = amanecer_hibrido
        indices["atardecer"] = atardecer_hibrido
        indices["es_dia_astronomico"] = es_dia_astronomico
        indices["es_dia_sensor"] = es_dia_sensor
        
        # Desvíos
        amanecer_h_min = hhmm_a_minutos(amanecer_hibrido)
        atardecer_h_min = hhmm_a_minutos(atardecer_hibrido)
        desvio_amanecer = None
        desvio_atardecer = None
        
        if amanecer_min is not None and amanecer_h_min is not None:
            desvio_amanecer = abs(amanecer_h_min - amanecer_min)
        if atardecer_min is not None and atardecer_h_min is not None:
            desvio_atardecer = abs(atardecer_h_min - atardecer_min)
        
        # Detectar inconsistencias
        inconsistencia_sensor = (
            es_dia_astronomico is not None and es_dia_astronomico != es_dia_sensor
        )
        inconsistencia_hibrida = False
        if desvio_amanecer is not None and desvio_amanecer >= umbral_desvio_min:
            inconsistencia_hibrida = True
        if desvio_atardecer is not None and desvio_atardecer >= umbral_desvio_min:
            inconsistencia_hibrida = True
        
        indices["desvio_amanecer_min"] = desvio_amanecer
        indices["desvio_atardecer_min"] = desvio_atardecer
        indices["inconsistencia_luz"] = (inconsistencia_sensor or inconsistencia_hibrida)
        indices["inconsistencia_sensor_luz"] = inconsistencia_sensor
        indices["inconsistencia_hibrida"] = inconsistencia_hibrida
        
    except ImportError:
        logger.warning("tools.amanecer_atardecer no disponible; usando fallbacks")
        indices["amanecer"] = "--:--"
        indices["atardecer"] = "--:--"
    except Exception as e:
        logger.exception(f"Error calculating sunrise/sunset: {e}")
        indices["amanecer"] = "--:--"
        indices["atardecer"] = "--:--"
    
    return indices
