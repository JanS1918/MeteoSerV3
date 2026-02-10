import math
from datetime import datetime, timezone, timedelta

from core.system.constants import ESTACION

try:
    from core.arcos_solares import calcular_eventos_solares
except Exception:
    calcular_eventos_solares = None


def arco_solar(latitud_deg: float, dia_del_ano: int) -> float:
    """
    Arco solar en grados usando el motor astronómico central si está disponible.

    Mantiene la firma antigua `(latitud_deg, dia_del_ano)` para compatibilidad.
    Si `core.arcos_solares.calcular_eventos_solares` no está disponible,
    cae en la implementación NOAA simplificada.
    """
    # Construir una fecha aproximada (mediodía UTC del día solicitado)
    hoy = datetime.now(timezone.utc)
    año = hoy.year
    fecha = datetime(año, 1, 1, 12, 0, tzinfo=timezone.utc) + timedelta(days=dia_del_ano - 1)

    if calcular_eventos_solares:
        try:
            amanecer, anochecer, duracion_min = calcular_eventos_solares(latitud_deg, 0.0, fecha)
            if duracion_min is None:
                duracion_min = 0.0
            # Convertir duración (minutos) a grados de arco: 360° * (minutos / 1440)
            arco_deg = duracion_min * 0.25
            return float(arco_deg)
        except Exception:
            pass

    # Fallback: NOAA-like simplificado
    def declinacion_solar(dia_del_ano: int) -> float:
        return 0.409 * math.sin(2 * math.pi * (dia_del_ano - 81) / 368)

    def angulo_horario_amanecer(lat_rad: float, decl_rad: float) -> float:
        return math.acos(-math.tan(lat_rad) * math.tan(decl_rad))

    lat_rad = math.radians(latitud_deg)
    decl_rad = declinacion_solar(dia_del_ano)
    H0 = angulo_horario_amanecer(lat_rad, decl_rad)
    return math.degrees(2 * H0)


if __name__ == "__main__":
    lat = ESTACION.LATITUD
    n = 17
    arco = arco_solar(lat, n)
    print("Arco solar:", arco, "grados")
