import math


def declinacion_solar(dia_del_ano: int) -> float:
    return 0.409 * math.sin(2 * math.pi * (dia_del_ano - 81) / 368)


def angulo_horario_amanecer(lat_rad: float, decl_rad: float) -> float:
    return math.acos(-math.tan(lat_rad) * math.tan(decl_rad))


def calcular_amanecer_atardecer(
    latitud_deg: float,
    longitud_deg: float,
    dia_del_ano: int,
    utc_offset: int = 1,
) -> dict:
    """
    Devuelve horas locales de amanecer y atardecer (HH:MM) para lat/lon y día.
    """
    lat_rad = math.radians(latitud_deg)
    decl_rad = declinacion_solar(dia_del_ano)
    H0 = angulo_horario_amanecer(lat_rad, decl_rad)
    H0_horas = math.degrees(H0) / 15.0

    mediodia = 12 - (longitud_deg / 15.0) + utc_offset
    amanecer = (mediodia - H0_horas + 24) % 24
    atardecer = (mediodia + H0_horas + 24) % 24

    def hhmm(h: float) -> str:
        h_int = int(h)
        m = int(round((h - h_int) * 60))
        if m == 60:
            h_int += 1
            m = 0
        return f"{h_int:02d}:{m:02d}"

    return {"amanecer": hhmm(amanecer), "atardecer": hhmm(atardecer)}
