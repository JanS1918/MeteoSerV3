import math


def declinacion_solar(dia_del_ano: int) -> float:
    """
    Declination solar (δ) en radianes.
    Fórmula NOAA.
    """
    return 0.409 * math.sin(2 * math.pi * (dia_del_ano - 81) / 368)


def angulo_horario_amanecer(lat_rad: float, decl_rad: float) -> float:
    """
    Ángulo horario del amanecer/atardecer (H0) en radianes.
    """
    return math.acos(-math.tan(lat_rad) * math.tan(decl_rad))


def arco_solar(latitud_deg: float, dia_del_ano: int) -> float:
    """
    Cálculo del ARCO SOLAR en grados.
    Fórmula:
        ArcoSolar = 2 * H0
    donde H0 es el ángulo horario del amanecer/atardecer.

    Resultado:
        - 0° = noche polar
        - 180° = día completo (sol de medianoche)
        - valores intermedios = día normal
    """
    lat_rad = math.radians(latitud_deg)
    decl_rad = declinacion_solar(dia_del_ano)
    H0 = angulo_horario_amanecer(lat_rad, decl_rad)
    return math.degrees(2 * H0)


# EJEMPLO DE USO:
if __name__ == "__main__":
    # Latitud de Argentona (aprox)
    lat = 41.55
    # Día del año (ej: 1 enero = 1)
    n = 17
    arco = arco_solar(lat, n)
    print("Arco solar:", arco, "grados")
