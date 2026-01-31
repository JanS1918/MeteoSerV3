# Calculador de arcos solar y lunar
from typing import Dict, Any, Tuple
from datetime import datetime, timezone
import math

def calcular_posicion_sol(lat: float, lon: float, fecha: datetime) -> Dict[str, Any]:
    """
    Calcula la posición del sol, horas de amanecer/anochecer y duración del día.
    
    Args:
        lat: Latitud en grados
        lon: Longitud en grados
        fecha: Fecha y hora actual
    
    Returns:
        Dict con: amanecer, anochecer, posicion_sol (0-1), duracion_dia, es_de_dia
    """
    # Simplificación: cálculo astronómico básico
    # En producción, usar librerías como astral o pyephem
    
    dia_del_ano = fecha.timetuple().tm_yday
    declinacion = 23.45 * math.sin(math.radians((360 / 365) * (dia_del_ano - 81)))
    
    lat_rad = math.radians(lat)
    dec_rad = math.radians(declinacion)
    
    # Ángulo horario del amanecer/anochecer
    try:
        cos_hora = -math.tan(lat_rad) * math.tan(dec_rad)
        if cos_hora > 1:
            # Sol nunca sale (noche polar)
            hora_amanecer = None
            hora_anochecer = None
            duracion_dia = 0
        elif cos_hora < -1:
            # Sol nunca se pone (día polar)
            hora_amanecer = datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0)
            hora_anochecer = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
            duracion_dia = 24 * 60
        else:
            angulo_hora = math.degrees(math.acos(cos_hora))
            
            # Hora solar del amanecer y anochecer
            hora_solar_amanecer = 12 - (angulo_hora / 15)
            hora_solar_anochecer = 12 + (angulo_hora / 15)
            
            # Convertir a hora local (simplificado, sin zona horaria precisa)
            hora_amanecer = datetime(fecha.year, fecha.month, fecha.day, 
                                    int(hora_solar_amanecer), 
                                    int((hora_solar_amanecer % 1) * 60))
            hora_anochecer = datetime(fecha.year, fecha.month, fecha.day, 
                                     int(hora_solar_anochecer), 
                                     int((hora_solar_anochecer % 1) * 60))
            
            duracion_dia = (hora_anochecer - hora_amanecer).total_seconds() / 60
    except Exception as e:
        # Valores por defecto en caso de error
        hora_amanecer = datetime(fecha.year, fecha.month, fecha.day, 7, 0, 0)
        hora_anochecer = datetime(fecha.year, fecha.month, fecha.day, 19, 0, 0)
        duracion_dia = 12 * 60
    
    # Determinar si es de día
    es_de_dia = False
    posicion_sol = 0.0
    
    if hora_amanecer and hora_anochecer:
        es_de_dia = hora_amanecer <= fecha <= hora_anochecer
        
        if es_de_dia:
            # Posición del sol en el arco (0 = amanecer, 1 = anochecer)
            tiempo_desde_amanecer = (fecha - hora_amanecer).total_seconds()
            duracion_dia_segundos = (hora_anochecer - hora_amanecer).total_seconds()
            posicion_sol = min(1.0, max(0.0, tiempo_desde_amanecer / duracion_dia_segundos))
    
    duracion_noche = (24 * 60) - duracion_dia
    
    return {
        'amanecer': hora_amanecer.strftime('%H:%M') if hora_amanecer else 'N/A',
        'anochecer': hora_anochecer.strftime('%H:%M') if hora_anochecer else 'N/A',
        'posicion_sol': posicion_sol,
        'duracion_dia': duracion_dia,
        'duracion_noche': duracion_noche,
        'es_de_dia': es_de_dia
    }

def calcular_fase_lunar(fecha: datetime) -> Dict[str, Any]:
    """
    Calcula la fase lunar aproximada.
    
    Args:
        fecha: Fecha y hora actual
    
    Returns:
        Dict con: fase (0-1), nombre_fase, icono
    """
    # Fecha de referencia (luna nueva conocida): 2000-01-06
    fecha_ref = datetime(2000, 1, 6, tzinfo=timezone.utc)
    fecha_utc = fecha.replace(tzinfo=timezone.utc)
    
    # Ciclo lunar: aproximadamente 29.53 días
    ciclo_lunar = 29.530588853
    
    dias_desde_ref = (fecha_utc - fecha_ref).total_seconds() / (24 * 3600)
    fase = (dias_desde_ref % ciclo_lunar) / ciclo_lunar
    
    # Determinar nombre de la fase
    if fase < 0.0625:
        nombre = 'Luna Nueva'
        icono = 'new_moon'
    elif fase < 0.1875:
        nombre = 'Creciente'
        icono = 'waxing_crescent'
    elif fase < 0.3125:
        nombre = 'Cuarto Creciente'
        icono = 'first_quarter'
    elif fase < 0.4375:
        nombre = 'Creciente Gibosa'
        icono = 'waxing_gibbous'
    elif fase < 0.5625:
        nombre = 'Luna Llena'
        icono = 'full_moon'
    elif fase < 0.6875:
        nombre = 'Menguante Gibosa'
        icono = 'waning_gibbous'
    elif fase < 0.8125:
        nombre = 'Cuarto Menguante'
        icono = 'last_quarter'
    else:
        nombre = 'Menguante'
        icono = 'waning_crescent'
    
    return {
        'fase': fase,
        'nombre': nombre,
        'icono': icono
    }

def calcular_posicion_luna(fecha: datetime, amanecer_str: str, anochecer_str: str, es_de_dia: bool) -> float:
    """
    Calcula la posición de la luna en el arco lunar (0 = anochecer, 1 = amanecer).
    
    Args:
        fecha: Fecha y hora actual
        amanecer_str: Hora de amanecer en formato 'HH:MM'
        anochecer_str: Hora de anochecer en formato 'HH:MM'
        es_de_dia: Si actualmente es de día
    
    Returns:
        Posición de la luna (0-1)
    """
    if es_de_dia:
        return 0.0  # Luna no visible durante el día
    
    try:
        # Parsear horas
        hora_amanecer = datetime.strptime(amanecer_str, '%H:%M').replace(
            year=fecha.year, month=fecha.month, day=fecha.day
        )
        hora_anochecer = datetime.strptime(anochecer_str, '%H:%M').replace(
            year=fecha.year, month=fecha.month, day=fecha.day
        )
        
        # Si es después de medianoche pero antes del amanecer
        if fecha.hour < hora_amanecer.hour:
            # Tiempo desde el anochecer del día anterior
            hora_anochecer_ayer = hora_anochecer.replace(day=fecha.day - 1)
            tiempo_desde_anochecer = (fecha - hora_anochecer_ayer).total_seconds()
        else:
            # Tiempo desde el anochecer de hoy
            tiempo_desde_anochecer = (fecha - hora_anochecer).total_seconds()
        
        # Duración de la noche
        if fecha.hour < hora_amanecer.hour:
            duracion_noche = (hora_amanecer - hora_anochecer.replace(day=fecha.day - 1)).total_seconds()
        else:
            hora_amanecer_manana = hora_amanecer.replace(day=fecha.day + 1)
            duracion_noche = (hora_amanecer_manana - hora_anochecer).total_seconds()
        
        # Posición de la luna (0 = anochecer, 1 = amanecer)
        posicion_luna = min(1.0, max(0.0, tiempo_desde_anochecer / duracion_noche))
        
        return posicion_luna
    except Exception:
        return 0.0
