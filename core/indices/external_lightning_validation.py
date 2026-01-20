# -*- coding: utf-8 -*-
"""
Módulo de validación externa de rayos usando múltiples APIs públicas y gratuitas.
Incluye:
- OpenWeatherMap (requiere API key gratuita)
- Blitzortung/LightningMaps (requiere scraping o integración indirecta)
- NOAA (descarga de datos, cobertura USA/global)

La función principal consulta todas las fuentes posibles y devuelve True si al menos una confirma rayos recientes en la zona.
"""
import requests
import time
from typing import Optional, List

# Puedes añadir tu API key gratuita de OpenWeatherMap aquí o usar variable de entorno
import os
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", None)  # Migrado a variable de entorno

# Coordenadas por defecto (Madrid, España)
DEFAULT_LAT = 40.4168
DEFAULT_LON = -3.7038


def check_openweathermap_lightning(lat: float, lon: float, api_key: Optional[str] = None) -> bool:
    """
    Consulta OpenWeatherMap One Call API para alertas de rayos en la zona.
    Devuelve True si hay rayos recientes.
    """
    key = api_key or OPENWEATHER_API_KEY
    if not key:
        return False
    url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={key}&units=metric&lang=es"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return False
        data = resp.json()
        # Buscar eventos de rayos en 'alerts' o 'current.weather'
        if 'alerts' in data:
            for alert in data['alerts']:
                if 'ray' in alert.get('event', '').lower() or 'lightning' in alert.get('event', '').lower():
                    return True
        if 'current' in data and 'weather' in data['current']:
            for w in data['current']['weather']:
                if w.get('id') == 95 or w.get('id') == 96 or w.get('id') == 99:
                    # Códigos de tormenta eléctrica
                    return True
        return False
    except Exception:
        return False


def check_blitzortung_lightning(lat: float, lon: float, radius_km: float = 30) -> bool:
    """
    Consulta Blitzortung/LightningMaps vía scraping JSON público (si disponible).
    Devuelve True si hay rayos recientes cerca.
    """
    # Blitzortung/LightningMaps no tiene API pública oficial, pero hay endpoints JSON usados por el mapa
    # Ejemplo: https://api.lightningmaps.org/v2/strikes/geo?lat=40.4&lon=-3.7&radius=30&timestamp=now
    # Si no funciona, devolver False
    try:
        url = f"https://api.lightningmaps.org/v2/strikes/geo?lat={lat}&lon={lon}&radius={radius_km}&timestamp=now"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return False
        data = resp.json()
        # Si hay strikes recientes, la lista no estará vacía
        if isinstance(data, list) and len(data) > 0:
            return True
        return False
    except Exception:
        return False


def check_noaa_lightning(lat: float, lon: float) -> bool:
    """
    Consulta NOAA (solo USA, experimental, requiere parsing de datos).
    Devuelve True si hay rayos recientes cerca.
    """
    # NOAA: https://www.ncdc.noaa.gov/data-access/quick-links#lightning
    # Integración real pendiente
    return False


def validar_rayo_externo(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON, api_key: Optional[str] = None) -> bool:
    """
    Consulta todas las fuentes externas posibles. Si alguna confirma rayo, devuelve True.
    """
    fuentes = [
        lambda: check_openweathermap_lightning(lat, lon, api_key),
        lambda: check_blitzortung_lightning(lat, lon),
        lambda: check_noaa_lightning(lat, lon),
    ]
    for f in fuentes:
        try:
            if f():
                return True
        except Exception:
            continue
    return False
