import math
import datetime

def declinacion_solar(dia_del_ano: int) -> float:
    return 0.409 * math.sin(2 * math.pi * (dia_del_ano - 81) / 368)

def angulo_horario_amanecer(lat_rad: float, decl_rad: float) -> float:
    return math.acos(-math.tan(lat_rad) * math.tan(decl_rad))

def calcular_amanecer_atardecer(latitud_deg: float, longitud_deg: float, dia_del_ano: int, utc_offset: int = 1) -> dict:
    """
    Devuelve las horas (HH:MM) locales de amanecer y atardecer para la latitud/longitud y día del año dados.
    utc_offset: desfase horario respecto a UTC (España peninsular = 1 o 2)
    """
    lat_rad = math.radians(latitud_deg)
    decl_rad = declinacion_solar(dia_del_ano)
    H0 = angulo_horario_amanecer(lat_rad, decl_rad)  # en radianes
    H0_horas = math.degrees(H0) / 15  # 15° = 1h
    # Mediodía solar local
    mediodia = 12 - (longitud_deg / 15) + utc_offset
    amanecer = mediodia - H0_horas
    atardecer = mediodia + H0_horas
    # Ajustar a 0-24
    amanecer = (amanecer + 24) % 24
    atardecer = (atardecer + 24) % 24
    def hhmm(h):
        h_ = int(h)
        m = int(round((h - int(h)) * 60))
        if m == 60:
            h_ += 1
            m = 0
        return f"{h_:02d}:{m:02d}"
    return {"amanecer": hhmm(amanecer), "atardecer": hhmm(atardecer)}
