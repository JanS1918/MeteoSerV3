# -*- coding: utf-8 -*-
"""
Módulo de validación externa de sismos usando múltiples APIs públicas y gratuitas.
Incluye:
- USGS Earthquake API (global, fiable, sin API key)
- IGN España (catálogo nacional, scraping o integración indirecta)

La función principal consulta todas las fuentes posibles y devuelve True si al menos una confirma un sismo reciente en la zona.
"""
import requests
import datetime
from typing import Optional

# Coordenadas por defecto (Madrid, España)
DEFAULT_LAT = 40.4168
DEFAULT_LON = -3.7038


def check_usgs_earthquake(lat: float, lon: float, radius_km: float = 100, minutos: int = 10) -> bool:
    """
    Consulta USGS Earthquake API para sismos recientes cerca de la ubicación.
    Devuelve True si hay sismos recientes (últimos X minutos) en el radio indicado.
    """
    ahora = datetime.datetime.now(datetime.timezone.utc)
    starttime = (ahora - datetime.timedelta(minutes=minutos)).isoformat()
    url = (
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
        f"&latitude={lat}&longitude={lon}&maxradiuskm={radius_km}"
        f"&starttime={starttime}"
    )
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return False
        data = resp.json()
        if data.get("features") and len(data["features"]) > 0:
            return True
        return False
    except Exception:
        return False

def check_ign_earthquake(lat: float, lon: float, radius_km: float = 100, minutos: int = 10) -> bool:
    """
    Consulta IGN España (requiere scraping o integración indirecta).
    Devuelve True si hay sismos recientes cerca.
    """
    # Integración real pendiente
    return False

def validar_sismo_externo(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON, minutos: int = 10) -> bool:
    """
    Consulta todas las fuentes externas posibles. Si alguna confirma sismo, devuelve True.
    """
    fuentes = [
        lambda: check_usgs_earthquake(lat, lon, minutos=minutos),
        lambda: check_ign_earthquake(lat, lon, minutos=minutos),
    ]
    for f in fuentes:
        try:
            if f():
                return True
        except Exception:
            continue
    return False
