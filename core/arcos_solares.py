# Calculador de arcos solar y lunar
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timezone
import math

from core.system.constants import ESTACION

def _spencer_declinacion(dia_del_ano: int) -> float:
    """Declinación solar (rad) según Spencer (1971)."""
    B = 2.0 * math.pi * (dia_del_ano - 1) / 365.25
    return (
        0.006918
        - 0.399912 * math.cos(B)
        + 0.070257 * math.sin(B)
        - 0.006758 * math.cos(2 * B)
        + 0.000907 * math.sin(2 * B)
        - 0.002697 * math.cos(3 * B)
        + 0.00111 * math.sin(3 * B)
    )


def _ecuacion_tiempo_min(dia_del_ano: int) -> float:
    """Ecuación del tiempo (min) Spencer (1971)."""
    B = 2.0 * math.pi * (dia_del_ano - 1) / 365.25
    return 229.2 * (
        0.000075
        + 0.001868 * math.cos(B)
        - 0.032077 * math.sin(B)
        - 0.014615 * math.cos(2 * B)
        - 0.040849 * math.sin(2 * B)
    )


def calcular_eventos_solares(
    lat: float,
    lon: float,
    fecha: datetime,
    altura_sol_deg: float = -0.833,
    zona_horaria: Optional[int] = None,
) -> Tuple[Optional[datetime], Optional[datetime], Optional[float]]:
    """Calcula amanecer/anochecer para una altura solar dada (°)."""
    dia_del_ano = fecha.timetuple().tm_yday
    lat_rad = math.radians(lat)
    dec_rad = _spencer_declinacion(dia_del_ano)
    h0 = math.radians(altura_sol_deg)

    cos_omega = (math.sin(h0) - math.sin(lat_rad) * math.sin(dec_rad)) / (
        math.cos(lat_rad) * math.cos(dec_rad)
    )

    if cos_omega > 1:
        return None, None, 0.0
    if cos_omega < -1:
        amanecer = datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0)
        anochecer = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
        return amanecer, anochecer, 24 * 60.0

    omega = math.degrees(math.acos(cos_omega))
    eqt_min = _ecuacion_tiempo_min(dia_del_ano)
    if zona_horaria is None:
        zona_horaria = int(round(lon / 15.0))
    lon_huso = 15 * zona_horaria
    correccion_min = 4 * (lon_huso - lon) + eqt_min
    mediodia_solar = 12.0 + correccion_min / 60.0

    hora_amanecer = mediodia_solar - omega / 15.0
    hora_anochecer = mediodia_solar + omega / 15.0

    amanecer = datetime(
        fecha.year, fecha.month, fecha.day, int(hora_amanecer), int((hora_amanecer % 1) * 60)
    )
    anochecer = datetime(
        fecha.year, fecha.month, fecha.day, int(hora_anochecer), int((hora_anochecer % 1) * 60)
    )
    duracion_dia = (anochecer - amanecer).total_seconds() / 60.0
    return amanecer, anochecer, max(0.0, duracion_dia)


def radiacion_teorica(
    lat_deg: float,
    dia_del_ano: int,
    hora_decimal: float,
    elevacion_solar_deg: Optional[float] = None,
) -> float:
    """Radiación solar teórica extraterrestre sobre horizontal (W/m²)."""
    I_sc = 1367.0
    B = 2.0 * math.pi * (dia_del_ano - 1) / 365.25
    E0 = 1.00011 + 0.034221 * math.cos(B) + 0.00128 * math.sin(B) + 0.000719 * math.cos(2 * B) + 0.000077 * math.sin(2 * B)

    if elevacion_solar_deg is None:
        dec = _spencer_declinacion(dia_del_ano)
        lat_rad = math.radians(lat_deg)
        omega = math.radians(15.0 * (hora_decimal - 12.0))
        cos_theta_z = math.sin(lat_rad) * math.sin(dec) + math.cos(lat_rad) * math.cos(dec) * math.cos(omega)
    else:
        cos_theta_z = math.sin(math.radians(elevacion_solar_deg))

    cos_theta_z = max(0.0, cos_theta_z)
    return I_sc * E0 * cos_theta_z


def determinar_dia_hibrido(
    elevacion_solar_deg: float,
    radiacion_sensor_wm2: Optional[float],
    uv_index: Optional[float],
    radiacion_teorica_wm2: float,
) -> Dict[str, Any]:
    """Determina día/noche con validación física (astronomía + sensores)."""
    es_de_dia_astro = elevacion_solar_deg > -0.833
    es_de_dia_sensor = False
    if radiacion_sensor_wm2 is not None:
        es_de_dia_sensor = radiacion_sensor_wm2 > 0.0
    if uv_index is not None:
        es_de_dia_sensor = es_de_dia_sensor or uv_index > 0.0

    inconsistencia = es_de_dia_astro != es_de_dia_sensor
    ratio = None
    if radiacion_sensor_wm2 is not None and radiacion_teorica_wm2 > 0:
        ratio = radiacion_sensor_wm2 / radiacion_teorica_wm2

    return {
        "es_de_dia_hibrido": es_de_dia_astro and not (radiacion_sensor_wm2 == 0 and (uv_index or 0) == 0),
        "es_de_dia_astronomico": es_de_dia_astro,
        "es_de_dia_sensor": es_de_dia_sensor,
        "inconsistencia_luz": inconsistencia,
        "ratio_radiacion": ratio,
    }


def _horizonte_orografico_deg(perfil_horizonte: Optional[List[Dict[str, float]]], azimut_deg: float) -> Optional[float]:
    if not perfil_horizonte:
        return None
    if len(perfil_horizonte) == 1:
        return float(perfil_horizonte[0].get("elevacion_deg", 0.0))
    step = perfil_horizonte[1].get("azimut_deg", 0.0) - perfil_horizonte[0].get("azimut_deg", 0.0)
    if step <= 0:
        return None
    idx = int((azimut_deg % 360.0) // step) % len(perfil_horizonte)
    return float(perfil_horizonte[idx].get("elevacion_deg", 0.0))


def calcular_ventana_observacion_nocturna(
    lat: float,
    lon: float,
    fecha: datetime,
    zona_horaria: Optional[int] = None,
) -> Dict[str, Any]:
    """Ventana astronómica (sol por debajo de -18°)."""
    inicio, fin, _ = calcular_eventos_solares(lat, lon, fecha, altura_sol_deg=-18.0, zona_horaria=zona_horaria)
    if inicio is None or fin is None:
        return {"inicio": None, "fin": None, "duracion_min": 0.0}

    if fin < inicio:
        fin = fin.replace(day=fin.day + 1)

    duracion = (fin - inicio).total_seconds() / 60.0
    return {
        "inicio": inicio.strftime('%H:%M'),
        "fin": fin.strftime('%H:%M'),
        "duracion_min": max(0.0, duracion),
    }


def calcular_posicion_sol(
    lat: float,
    lon: float,
    fecha: datetime,
    presion_hpa: Optional[float] = None,
    temperatura_c: Optional[float] = None,
    humedad_rel: Optional[float] = None,
    altitud_m: Optional[float] = None,
    zona_horaria: Optional[int] = None,
    perfil_horizonte: Optional[List[Dict[str, float]]] = None,
) -> Dict[str, Any]:
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
    hora_amanecer, hora_anochecer, duracion_dia = calcular_eventos_solares(
        lat, lon, fecha, altura_sol_deg=-0.833, zona_horaria=zona_horaria
    )
    if duracion_dia is None:
        duracion_dia = 0.0
    
    # Determinar si es de día
    es_de_dia = False
    posicion_sol = 0.0
    
    elevacion_solar = None
    azimut_solar = None
    
    # ⚛️ BUS-FIRST: Intentar obtener del bus
    try:
        from core.system.bus import obtener_bus
        bus = obtener_bus()
        if bus:
            elevacion_solar_bus = bus.leer("elevacion_solar_deg")
            azimut_solar_bus = bus.leer("azimut_solar_deg")
            if elevacion_solar_bus is not None and azimut_solar_bus is not None:
                elevacion_solar = float(elevacion_solar_bus)
                azimut_solar = float(azimut_solar_bus)
    except Exception:
        pass
    
    # Fallback: calcular localmente
    if elevacion_solar is None or azimut_solar is None:
        try:
            from core.indices.astronomia_recursiva import AstronomiaRecursiva
            altitud_val = altitud_m if altitud_m is not None else 0.0
            astro = AstronomiaRecursiva(lat, lon, altitud_val)
            fecha_utc = fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)
            presion_val = presion_hpa if presion_hpa is not None else 1013.25
            temp_val = temperatura_c if temperatura_c is not None else 15.0
            humedad_val = (humedad_rel / 100.0) if humedad_rel is not None and humedad_rel > 1 else (humedad_rel if humedad_rel is not None else 0.5)
            resultado = astro.calcular_posicion_solar_nrel_spa(fecha_utc, presion_val, temp_val, humedad_val)
            elevacion_solar = resultado.get("elevacion_aparente_deg")
            azimut_solar = resultado.get("azimut_deg")
        except Exception:
            elevacion_solar = None
            azimut_solar = None

    horizonte_orografico_deg = None
    sombra_orografica = False

    if hora_amanecer and hora_anochecer:
        if fecha.tzinfo is not None:
            if hora_amanecer.tzinfo is None:
                hora_amanecer = hora_amanecer.replace(tzinfo=fecha.tzinfo)
            if hora_anochecer.tzinfo is None:
                hora_anochecer = hora_anochecer.replace(tzinfo=fecha.tzinfo)
        else:
            if hora_amanecer.tzinfo is not None:
                hora_amanecer = hora_amanecer.replace(tzinfo=None)
            if hora_anochecer.tzinfo is not None:
                hora_anochecer = hora_anochecer.replace(tzinfo=None)
        es_de_dia = hora_amanecer <= fecha <= hora_anochecer
        if elevacion_solar is not None:
            es_de_dia = elevacion_solar > -0.833

        if elevacion_solar is not None and azimut_solar is not None and perfil_horizonte:
            horizonte_orografico_deg = _horizonte_orografico_deg(perfil_horizonte, azimut_solar)
            if horizonte_orografico_deg is not None and elevacion_solar <= horizonte_orografico_deg:
                sombra_orografica = True
                es_de_dia = False

        if es_de_dia:
            tiempo_desde_amanecer = (fecha - hora_amanecer).total_seconds()
            duracion_dia_segundos = max(1.0, (hora_anochecer - hora_amanecer).total_seconds())
            posicion_sol = min(1.0, max(0.0, tiempo_desde_amanecer / duracion_dia_segundos))
    
    duracion_noche = (24 * 60) - duracion_dia
    
    return {
        'amanecer': hora_amanecer.strftime('%H:%M') if hora_amanecer else 'N/A',
        'anochecer': hora_anochecer.strftime('%H:%M') if hora_anochecer else 'N/A',
        'posicion_sol': posicion_sol,
        'duracion_dia': duracion_dia,
        'duracion_noche': duracion_noche,
        'es_de_dia': es_de_dia,
        'elevacion_solar_deg': elevacion_solar,
        'azimut_solar_deg': azimut_solar,
        'horizonte_orografico_deg': horizonte_orografico_deg,
        'sombra_orografica': sombra_orografica,
    }

def calcular_fase_lunar(
    fecha: datetime,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    altitud_m: Optional[float] = None,
    presion_hpa: Optional[float] = None,
    temperatura_c: Optional[float] = None,
    humedad_rel: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calcula la fase lunar preferentemente con Meeus/ELP2000.

    Args:
        fecha: Fecha y hora actual
        lat/lon/altitud_m: Coordenadas para cálculo Meeus
        presion_hpa/temperatura_c/humedad_rel: Refracción y correcciones
    """
    try:
        from core.indices.astronomia_recursiva import AstronomiaRecursiva

        lat_val = ESTACION.LATITUD if lat is None else lat
        lon_val = ESTACION.LONGITUD if lon is None else lon
        alt_val = ESTACION.ALTITUD if altitud_m is None else altitud_m
        presion_val = 1013.25 if presion_hpa is None else presion_hpa
        temp_val = 15.0 if temperatura_c is None else temperatura_c
        if humedad_rel is None:
            humedad_frac = 0.5
        elif humedad_rel > 1:
            humedad_frac = humedad_rel / 100.0
        else:
            humedad_frac = humedad_rel

        fecha_utc = fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)
        astro = AstronomiaRecursiva(lat_val, lon_val, alt_val)
        resultado = astro.calcular_posicion_lunar_meeus(
            fecha_utc,
            presion_val,
            temp_val,
            humedad_frac,
        )

        fase = resultado["fase_lunar"]
    except Exception:
        # Fallback aproximado si Meeus no está disponible
        fecha_ref = datetime(2000, 1, 6, tzinfo=timezone.utc)
        fecha_utc = fecha.replace(tzinfo=timezone.utc)
        ciclo_lunar = 29.530588853
        dias_desde_ref = (fecha_utc - fecha_ref).total_seconds() / (24 * 3600)
        fase = (dias_desde_ref % ciclo_lunar) / ciclo_lunar
        resultado = None

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

    salida = {
        'fase': fase,
        'nombre': nombre,
        'icono': icono,
    }
    if resultado:
        salida.update({
            'iluminacion_lunar_pct': resultado.get('iluminacion_lunar_pct'),
            'edad_lunar_dias': resultado.get('edad_lunar_dias'),
            'elevacion_lunar_deg': resultado.get('elevacion_aparente_deg'),
            'azimut_lunar_deg': resultado.get('azimut_deg'),
        })
    return salida

def calcular_posicion_luna(
    fecha: datetime,
    amanecer_str: str,
    anochecer_str: str,
    es_de_dia: bool,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    altitud_m: Optional[float] = None,
    presion_hpa: Optional[float] = None,
    temperatura_c: Optional[float] = None,
    humedad_rel: Optional[float] = None,
) -> float:
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
