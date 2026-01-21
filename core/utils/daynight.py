from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from math import radians, sin, cos, tan, asin, acos, pi
from datetime import timezone


def _hhmm_to_minutes(hhmm: Optional[str]) -> Optional[int]:
    try:
        if not hhmm or ":" not in hhmm:
            return None
        h, m = hhmm.split(":")[:2]
        return int(h) * 60 + int(m)
    except Exception:
        return None


def estado_dia_hibrido(indices: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Optional[Any]]:
    # Preferir timestamp cliente si viene en indices
    now = now or None
    if now is None:
        ts = indices.get("hora_cliente_iso") or indices.get("hora_cliente")
        if ts:
            try:
                if isinstance(ts, str):
                    now = datetime.fromisoformat(ts)
                elif isinstance(ts, datetime):
                    now = ts
            except Exception:
                now = None
    now = now or datetime.now(timezone.utc).astimezone()
    minuto_actual = now.hour * 60 + now.minute
    fecha = now.date()
    mes = now.month
    amanecer = indices.get("amanecer")
    atardecer = indices.get("atardecer")
    amanecer_min = _hhmm_to_minutes(amanecer)
    atardecer_min = _hhmm_to_minutes(atardecer)
    es_dia = None
    if amanecer_min is not None and atardecer_min is not None:
        if amanecer_min <= atardecer_min:
            es_dia = amanecer_min <= minuto_actual <= atardecer_min
        else:
            es_dia = (minuto_actual >= amanecer_min) or (minuto_actual <= atardecer_min)
    if es_dia is None:
        es_dia_sensor = indices.get("es_dia_sensor")
        if es_dia_sensor is not None:
            try:
                es_dia = bool(es_dia_sensor)
            except Exception:
                es_dia = None
    es_noche = None if es_dia is None else not es_dia
    # Coordenadas y arco solar / elevación solar
    lat = indices.get("latitud") or indices.get("latitude") or indices.get("lat")
    lon = indices.get("longitud") or indices.get("longitude") or indices.get("lon")
    solar_elevation = None
    arc_solar_deg = None
    es_noche_astronomico = None
    estacion = None
    try:
        if lat is not None:
            lat_f = float(lat)
        else:
            lat_f = None
        if lon is not None:
            lon_f = float(lon)
        else:
            lon_f = None
    except Exception:
        lat_f = lon_f = None

    # calcular día del año y declinación solar
    try:
        doy = now.timetuple().tm_yday
    except Exception:
        doy = None

    if lat_f is not None and doy is not None:
        try:
            # declinación solar aproximada (radianes)
            solar_decl = 0.409 * sin(2 * pi * doy / 365 - 1.39)
            lat_rad = radians(lat_f)
            # hora solar aproximada: convertir now a UTC then corregir por longitud
            utc = now.astimezone(timezone.utc)
            utc_hours = utc.hour + utc.minute / 60.0 + utc.second / 3600.0
            # longitud en horas
            lon_hours = lon_f / 15.0 if lon_f is not None else 0.0
            solar_time = utc_hours + lon_hours
            # hora angular H (radianes)
            H = radians((solar_time - 12.0) * 15.0)
            sin_elev = sin(lat_rad) * sin(solar_decl) + cos(lat_rad) * cos(solar_decl) * cos(H)
            solar_elevation = asin(max(-1.0, min(1.0, sin_elev))) * 180.0 / pi
            # arco solar (duración del día) via ángulo horario en amanecer/ws
            tmp = -tan(lat_rad) * tan(solar_decl)
            ws = acos(min(max(tmp, -1.0), 1.0))
            arc_solar_deg = 2.0 * ws * 180.0 / pi
            # decidir noche astronómico: umbral civil twilight -6°
            es_noche_astronomico = solar_elevation < -6.0
        except Exception:
            solar_elevation = None
            arc_solar_deg = None
            es_noche_astronomico = None

    # estación del año por mes e hemisferio
    try:
        if lat_f is None:
            hemi = 'N'
        else:
            hemi = 'N' if lat_f >= 0 else 'S'
        if hemi == 'N':
            if mes in (12, 1, 2):
                estacion = 'invierno'
            elif mes in (3, 4, 5):
                estacion = 'primavera'
            elif mes in (6, 7, 8):
                estacion = 'verano'
            else:
                estacion = 'otono'
        else:
            # hemisferio sur invertido
            if mes in (12, 1, 2):
                estacion = 'verano'
            elif mes in (3, 4, 5):
                estacion = 'otono'
            elif mes in (6, 7, 8):
                estacion = 'invierno'
            else:
                estacion = 'primavera'
    except Exception:
        estacion = None
    return {
        "es_dia": es_dia,
        "es_noche": es_noche,
        "amanecer": amanecer,
        "atardecer": atardecer,
        "amanecer_min": amanecer_min,
        "atardecer_min": atardecer_min,
        "hora_actual_min": minuto_actual,
        "fecha": fecha,
        "mes": mes,
        "estacion": estacion,
        "solar_elevation": solar_elevation,
        "arco_solar_deg": arc_solar_deg,
        "es_noche_astronomico": es_noche_astronomico,
    }
