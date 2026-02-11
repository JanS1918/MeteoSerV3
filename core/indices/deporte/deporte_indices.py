"""
DEPORTE INDICES v1.0 - Robusto + Sintético

Índices para condiciones de deporte (fútbol, tenis, atletismo, etc.):
  1. Adherencia terreno (0=mojado, 100=seco)
  2. Visibilidad (0=niebla, 100=clara)
  3. Viento juego limpio (0=viento excesivo, 100=ideal)
  4. Confort atletas (0=extremo, 100=ideal)

Fecha: 10 de febrero de 2026
"""

from typing import Dict, Optional
import logging
import math

logger = logging.getLogger(__name__)


def _clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min(value, max_value), min_value)


# ============================================================================
# ÍNDICES ROBUSTOS DE DEPORTE
# ============================================================================

def adherencia_terreno_deporte_robusto(
    lluvia_24h: Optional[float],
    lluvia_1h: Optional[float],
    viento: Optional[float],
    temp: Optional[float],
    historico: float = 75.0
) -> float:
    """
    Adherencia terreno para deporte (0-100).
    
    100 = terreno seco (agarre óptimo), 0 = encharcado (resbaladizo).
    Deportes requieren buen agarre para evitar lesiones.
    
    Robusto: nunca None.
    """
    if all(v is None for v in [lluvia_24h, viento, temp]):
        return _clamp(historico, 0, 100)
    
    lluvia_24 = lluvia_24h if lluvia_24h is not None else 0.0
    lluvia_1 = lluvia_1h if lluvia_1h is not None else 0.0
    v = viento if viento is not None else 5.0
    t = temp if temp is not None else 15.0
    
    # Lluvia penaliza
    lluvia_factor = _clamp(lluvia_24 / 25.0)  # >25mm = muy mojado
    reciente_factor = _clamp(lluvia_1 / 3.0)  # lluvia muy reciente
    
    # Secado por viento
    secado_factor = _clamp(v / 12.0)
    
    score = 100.0 * (
        0.5 * (1.0 - lluvia_factor) +
        0.3 * (1.0 - reciente_factor) +
        0.2 * secado_factor
    )
    return _clamp(score, 0, 100)


def visibilidad_deporte_robusto(
    nubosidad: Optional[float],
    lluvia: Optional[float],
    humedad: Optional[float],
    historico: float = 85.0
) -> float:
    """
    Visibilidad para deporte (0-100).
    
    100 = excelente (ver bien el balón), 0 = muy mala (lluvia + niebla).
    
    Importante para seguridad (evitar colisiones) y calidad de juego.
    
    Robusto: nunca None.
    """
    if all(v is None for v in [nubosidad, lluvia, humedad]):
        return _clamp(historico, 0, 100)
    
    nub = nubosidad if nubosidad is not None else 30.0
    lluv = lluvia if lluvia is not None else 0.0
    hum = humedad if humedad is not None else 70.0
    
    # Lluvia reduce visibilidad
    lluvia_factor = 1.0 - _clamp(lluv / 3.0)  # >3mm/h = muy mala
    
    # Nubosidad (más importante que en carretera para ver balón)
    nub_factor = 1.0 - _clamp(nub / 100.0)
    
    # Humedad/niebla
    hum_factor = 1.0 - _clamp((hum - 85.0) / 15.0)
    
    score = 100.0 * (
        0.5 * lluvia_factor +
        0.35 * nub_factor +
        0.15 * hum_factor
    )
    return _clamp(score, 0, 100)


def viento_juego_limpio_robusto(
    viento_medio: Optional[float],
    rachas: Optional[float],
    historico: float = 80.0
) -> float:
    """
    Viento juego limpio (0-100).
    
    100 = viento ideal (1-3 m/s), penaliza extremos.
    Viento muy alto afecta la precisión del juego (pases, tiros).
    
    Robusto: nunca None.
    """
    if viento_medio is None and rachas is None:
        return _clamp(historico, 0, 100)
    
    v = viento_medio if viento_medio is not None else (rachas if rachas is not None else 2.0)
    r = rachas if rachas is not None else v
    
    # Viento ideal es 1-3 m/s
    ideal_viento = 2.0
    max_viento_aceptable = 10.0
    
    # Penalizar desviación del ideal
    v_factor = 1.0 - _clamp(abs(v - ideal_viento) / 5.0)
    
    # Penalizar rachas excesivas (>15 m/s imposible jugar)
    r_factor = 1.0 - _clamp(r / max_viento_aceptable)
    
    score = 100.0 * (
        0.6 * v_factor +
        0.4 * r_factor
    )
    return _clamp(score, 0, 100)


def confort_atletas_robusto(
    temp_c: Optional[float],
    humedad: Optional[float],
    radiacion: Optional[float],
    historico: float = 70.0
) -> float:
    """
    Confort para atletas en ejercicio (0-100).
    
    100 = condiciones ideales para entrenar sin sobrecalentarse.
    Atletas toleran rango más amplio que población general.
    
    Ideal: 12-18°C (fresco para actividad física)
    
    Robusto: nunca None.
    """
    if all(v is None for v in [temp_c, humedad, radiacion]):
        return _clamp(historico, 0, 100)
    
    t = temp_c if temp_c is not None else 15.0
    h = humedad if humedad is not None else 60.0
    r = radiacion if radiacion is not None else 500.0
    
    # Temperatura ideal para atletas: 12-18°C (más fresco que población general)
    # (<5°C o >25°C = incómodo)
    temp_ideal = 15.0
    temp_factor = _clamp(1.0 - abs(t - temp_ideal) / 15.0)
    
    # Humedad alta = sofocación (>80% es mala)
    hum_factor = _clamp(1.0 - abs(h - 60.0) / 30.0)
    
    # Radiación excesiva = insolación
    rad_factor = _clamp(1.0 - (r / 1000.0))
    
    score = 100.0 * (
        0.5 * temp_factor +
        0.3 * hum_factor +
        0.2 * rad_factor
    )
    return _clamp(score, 0, 100)


# ============================================================================
# ÍNDICE SINTÉTICO DEPORTE
# ============================================================================

def indice_deporte_sintetico(
    adherencia_terreno: float,
    visibilidad: float,
    viento_juego: float,
    confort_atletas: float,
    lluvia_1h: Optional[float] = None,
    riesgo_escorrentia: Optional[float] = None,
    amplitud_termica: Optional[float] = None
) -> float:
    """
    Índice sintético deporte 0-100 - SUMA PONDERADA DE 4 COMPONENTES + CONTEXTOS.
    
    PESOS EXPLÍCITOS:
    - adherencia_terreno: 30% - Fundamental para evitar caídas
    - visibilidad: 25% - Crítica para ver el juego
    - viento_juego: 20% - Afecta trayectorias/pelotas
    - confort_atletas: 25% - Capacidad física del jugador
    
    CONTEXTOS:
    - lluvia_1h: Lluvia penaliza fuerte (especialmente adherencia)
    - riesgo_escorrentia: Terreno intransitable/embarrado
    - amplitud_termica: Variación extrema = estrés físico
    """
    
    if lluvia_1h is None:
        lluvia_1h = 0.0
    if riesgo_escorrentia is None:
        riesgo_escorrentia = 0.0
    if amplitud_termica is None:
        amplitud_termica = 50.0
    
    # ESCENARIO 1: LLUVIA EN PROGRESO (lluvia_1h > 0.1 mm)
    if lluvia_1h > 0.1:
        logger.debug(f"LLUVIA EN PROGRESO ({lluvia_1h:.2f}mm): Deporte DIFICULTA")
        
        # Lluvia afecta principalmente adherencia (terreno mojado) y confort
        adher_lluvia = _clamp(adherencia_terreno * (1.0 - (lluvia_1h / 3.0)))
        visib_lluvia = _clamp(visibilidad * (1.0 - (lluvia_1h / 5.0)))
        viento_lluvia = _clamp(viento_juego * (1.0 - (lluvia_1h / 10.0)))  # Viento no tan afectado
        confort_lluvia = _clamp(confort_atletas * (1.0 - (lluvia_1h / 4.0)))
        
        # SUMA PONDERADA de los 4 componentes penalizados
        indice_lluvia = _clamp(
            0.30 * adher_lluvia +      # adherencia: 30%
            0.25 * visib_lluvia +      # visibilidad: 25%
            0.20 * viento_lluvia +     # viento: 20%
            0.25 * confort_lluvia      # confort: 25%
        )
        
        # Penalización por lluvia (lluvia reduce condiciones deportivas)
        penalizacion = 1.0 - ((lluvia_1h / 50.0) ** 0.7)
        indice_final = indice_lluvia * penalizacion
        
        logger.debug(
            f"Deporte con lluvia: adher={adher_lluvia:.1f}, visib={visib_lluvia:.1f}, "
            f"viento={viento_lluvia:.1f}, confort={confort_lluvia:.1f} -> final={indice_final:.1f}"
        )
        
        return _clamp(indice_final)
    
    # ESCENARIO 2: ESCORRENTIA EXTREMA (terreno intransitable)
    elif riesgo_escorrentia > 75.0:
        logger.debug(f"ESCORRENTIA EXTREMA ({riesgo_escorrentia:.0f}%): Deporte CANCELA (terreno embarrado)")
        
        # Terreno muy mojado/embarrado = inaplayable
        adher_escor = _clamp(adherencia_terreno * (1.0 - ((riesgo_escorrentia - 75.0) / 25.0) * 0.9))
        
        indice_escor = _clamp(
            0.30 * adher_escor +       # adherencia: MUY REDUCIDA
            0.25 * visibilidad +       # visibilidad: normal
            0.20 * viento_juego +      # viento: normal
            0.25 * confort_atletas     # confort: normal
        )
        
        logger.debug(f"Deporte con escorrentía: {indice_escor:.1f}%")
        return _clamp(indice_escor)
    
    # ESCENARIO 3: AMPLITUD TÉRMICA EXTREMA (variación día-noche)
    elif amplitud_termica > 75.0:
        logger.debug(f"AMPLITUD TÉRMICA EXTREMA ({amplitud_termica:.0f}%): Deporte INESTABLE (estrés térmico)")
        
        # Variación extrema = cuerpo no se adapta bien
        penalizacion_ampl = ((amplitud_termica - 75.0) / 25.0) * 0.25  # Max -25%
        factor_ampl = 1.0 - penalizacion_ampl
        
        indice_ampl = _clamp(
            0.30 * adherencia_terreno * factor_ampl +  # Todos reducidos por estrés
            0.25 * visibilidad * factor_ampl +
            0.20 * viento_juego * factor_ampl +
            0.25 * confort_atletas * factor_ampl
        )
        
        logger.debug(f"Deporte con amplitud térmica extrema: {indice_ampl:.1f}%")
        return _clamp(indice_ampl)
    
    # ESCENARIO 4: SIN LLUVIA - SUMA PONDERADA estándar
    else:
        indice_normal = _clamp(
            0.30 * adherencia_terreno +  # adherencia: 30%
            0.25 * visibilidad +         # visibilidad: 25%
            0.20 * viento_juego +        # viento: 20%
            0.25 * confort_atletas       # confort: 25%
        )
        
        logger.debug(
            f"Deporte sin lluvia: adher={adherencia_terreno:.1f}, visib={visibilidad:.1f}, "
            f"viento={viento_juego:.1f}, confort={confort_atletas:.1f} -> indice={indice_normal:.1f}"
        )
        
        return indice_normal
        
        logger.debug(
            f"Deporte sin lluvia: adher={adherencia_terreno:.1f}, visib={visibilidad:.1f}, "
            f"viento={viento_juego:.1f}, confort={confort_atletas:.1f} -> indice={indice_normal:.1f}"
        )
        
        return indice_normal


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def calcular_deporte_completa(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Calcula TODOS los índices de deporte.
    
    Entrada: Dict con sensores clima
    Salida: 5 índices (4 componentes + 1 sintético)
    """
    
    lluvia_24h = data.get("lluvia_24h")
    lluvia_1h = data.get("lluvia_1h")
    lluvia_horaria = data.get("lluvia_horaria", lluvia_1h)
    nubosidad = data.get("nubosidad_estimada")
    humedad = data.get("humedad")
    viento_medio = data.get("viento_medio")
    rachas = data.get("rachas")
    temp_c = data.get("temperatura")
    radiacion = data.get("radiacion_global")
    
    # Calcular índices robustos
    adher_terr = adherencia_terreno_deporte_robusto(lluvia_24h, lluvia_1h, viento_medio, temp_c)
    visib = visibilidad_deporte_robusto(nubosidad, lluvia_horaria, humedad)
    viento_j = viento_juego_limpio_robusto(viento_medio, rachas)
    conf_atl = confort_atletas_robusto(temp_c, humedad, radiacion)
    
    # Índice sintético = valoración integral (lluvia incorporada)
    indice_sint = indice_deporte_sintetico(adher_terr, visib, viento_j, conf_atl, lluvia_1h=lluvia_1h, riesgo_escorrentia=data.get("riesgo_escorrentia"), amplitud_termica=data.get("amplitud_termica_tendencial"))
    
    return {
        "adherencia_terreno": adher_terr,
        "visibilidad": visib,
        "visibilidad_deporte": visib,
        "viento_juego": viento_j,
        "viento_juego_limpio": viento_j,
        "confort_atletas": conf_atl,
        "indice_deporte_sintetico": indice_sint,
        "indice_deporte": indice_sint  # Compatibilidad
    }
