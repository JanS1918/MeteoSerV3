"""
Aliases de nombres de sensores para normalización de entrada.
Mapea nombres alternativos a nombres canónicos internos.
"""

SENSOR_ALIASES = {
    # Temperatura
    'temperatura': ['temp', 't', 'temperature', 'temp_c', 'celsius'],
    'temperatura_aparente': ['apparent_temp', 'sensible_temp', 'feel'],
    
    # Humedad
    'humedad': ['hr', 'rh', 'relative_humidity', 'humidity', 'humedad_relativa', 'humidity_%'],
    'humedad_absoluta': ['vapor_density', 'absolute_humidity'],
    
    # Presión
    'presion': ['pressure', 'pres', 'presion_atm', 'presion_barometrica', 'hpa', 'mbar'],
    
    # Radiación solar
    'radiacion': ['rad', 'radiacion_solar', 'solar_radiation', 'rad_w_m2', 'sw_in'],
    'radiacion_neta': ['net_radiation', 'rn', 'rad_neta'],
    'radiacion_infrarroja': ['ir', 'infrared_radiation', 'lw_in'],
    
    # UV
    'uv': ['uv_index', 'uvi', 'indice_uv', 'uv_intensity'],
    'uvb': ['ultraviolet_b', 'uvb_radiation'],
    
    # Viento
    'viento': ['wind_speed', 'velocidad_viento', 'ws', 'wind_vel', 'viento_vel'],
    'viento_direccion': ['wind_direction', 'wind_dir', 'dir_viento', 'wd', 'bearing'],
    'viento_ráfaga': ['wind_gust', 'wind_max', 'gust_speed', 'rafaga'],
    
    # Precipitación
    'lluvia': ['rain', 'precipitation', 'precip', 'precip_rate', 'rain_rate', 'rainfall'],
    'lluvia_acumulada': ['rain_total', 'cumulative_rain', 'total_precip'],
    
    # Punto de rocío
    'punto_rocio': ['dew_point', 'td', 'dew_temp', 'dewpoint'],
    
    # Visibilidad
    'visibilidad': ['visibility', 'vis', 'alcance_visual'],
    
    # PM2.5 y calidad del aire
    'pm25': ['pm_2_5', 'pm2.5', 'pm_2.5', 'pm25_concentration'],
    'pm10': ['pm_10', 'pm10_concentration'],
    'pm_generica': ['pm_generic', 'pm_general', 'pm_otros'],
    'aqi': ['air_quality_index', 'indice_calidad_aire'],
    
    # Sismógrafo
    'sismografo': ['seismic', 'earthquake', 'sismo', 'seism', 'accelerometer'],
    'aceleracion': ['acceleration', 'accel', 'aceleracion_sismo'],
    
    # Geomagnético
    'geomagnetico': ['geomagnetic', 'magnetic_field', 'magnetometer'],
    'campo_magnetico': ['magnetic_field_intensity', 'bfield'],
    
    # Sensores especializados (mapeos renovados tras eutanasia técnica 2026)
    'sensacion_calor': ['heat_index', 'hi', 'indice_calor_aparente', 'indice_calor'],
    'sensacion_frio': ['wind_chill', 'wc', 'chill_factor', 'sensacion_termica', 'sensacion_frio'],
    'humedad_bulbo_humedo': ['wet_bulb', 'bulbo_humedo', 'bulbo_wet'],
    'potencial_evapotranspiracion': ['pet', 'evapotranspiration', 'et'],
    
    # Variables derivadas/internas
    'vapor_pressure': ['pressure_vapor', 'vapor_p', 'e'],
    'saturation_vapor_pressure': ['presion_vapor_saturacion', 'es'],
    'vpd': ['vapor_pressure_deficit', 'deficit_presion_vapor'],
    'velocidad_friccion': ['friction_velocity', 'u_star', 'u*'],
    'longitud_monin_obukhov': ['monin_obukhov_length', 'L_mo', 'L_ob'],
    'estabilidad_atmosferica': ['atmospheric_stability', 'clase_estabilidad'],
    'altura_capa_mezcla': ['mixing_height', 'h_mix', 'boundary_layer_height'],
}


def sensor_candidate_names(sensor_name: str) -> list[str]:
    """
    Retorna lista de nombres candidatos para un sensor dado.
    Incluye el nombre original y sus aliases.
    
    Parámetros:
    -----------
    sensor_name : str
        Nombre del sensor a buscar
        
    Retorna:
    --------
    list[str]
        Lista de nombres candidatos (nombre original + aliases)
    """
    if not isinstance(sensor_name, str):
        return [str(sensor_name)]
    
    sensor_lower = sensor_name.lower().strip()
    
    # Buscar en aliases directos
    if sensor_lower in SENSOR_ALIASES:
        return [sensor_lower] + SENSOR_ALIASES[sensor_lower]
    
    # Buscar si el nombre es un alias de algo
    for canonical, aliases in SENSOR_ALIASES.items():
        if sensor_lower in aliases:
            return [canonical] + aliases
    
    # Si no encuentra, retornar el nombre original
    return [sensor_lower]


def normalizar_nombre_sensor(sensor_name: str) -> str:
    """
    Normaliza un nombre de sensor a su forma canónica.
    
    Parámetros:
    -----------
    sensor_name : str
        Nombre del sensor a normalizar
        
    Retorna:
    --------
    str
        Nombre canónico del sensor
    """
    candidates = sensor_candidate_names(sensor_name)
    return candidates[0] if candidates else sensor_name.lower()


def es_alias_de(sensor_name: str, canonical_name: str) -> bool:
    """
    Verifica si un nombre es alias de otro.
    
    Parámetros:
    -----------
    sensor_name : str
        Nombre a verificar
    canonical_name : str
        Nombre canónico de referencia
        
    Retorna:
    --------
    bool
        True si sensor_name es un alias o el nombre de canonical_name
    """
    canonical_lower = canonical_name.lower().strip()
    if canonical_lower in SENSOR_ALIASES:
        return sensor_name.lower() in SENSOR_ALIASES[canonical_lower] or \
               sensor_name.lower() == canonical_lower
    return False
