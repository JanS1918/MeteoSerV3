"""
CONFORT INDICES v1.0 - Robusto + Sintético

Índices para confort humano (indoor/outdoor):
  1. Temperatura ideal (rango 18-24°C óptimo)
  2. Humedad ideal (rango 40-60% óptimo)
  3. Índice UV (peligro de radiación solar)
  4. Sensación térmica (temperatura sentida)

Fecha: 10 de febrero de 2026
"""

from typing import Dict, Optional
import logging
import math

logger = logging.getLogger(__name__)


def _clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min(value, max_value), min_value)


# ============================================================================
# ÍNDICES ROBUSTOS DE CONFORT
# ============================================================================

def temperatura_ideal_robusto(
    temp_c: Optional[float],
    historico: float = 70.0
) -> float:
    """
    Índice temperatura ideal (0-100).
    
    100 = 20°C (óptimo), degrada hacia extremos.
    Rango aceptable: 16-24°C (60% de satisfacción)
    
    Robusto: nunca None.
    """
    if temp_c is None:
        return _clamp(historico, 0, 100)
    
    # Función gaussiana centrada en 20°C
    ideal_temp = 20.0
    desv_std = 5.0
    
    diff = abs(temp_c - ideal_temp)
    score = 100.0 * math.exp(-0.5 * (diff / desv_std) ** 2)
    
    return _clamp(score, 0, 100)


def humedad_ideal_robusto(
    humedad: Optional[float],
    historico: float = 70.0
) -> float:
    """
    Índice humedad ideal (0-100).
    
    100 = 50% RH (óptimo para confort), degrada hacia extremos.
    Rango aceptable: 40-60% (mínimo 60% satisfacción)
    
    Robusto: nunca None.
    """
    if humedad is None:
        return _clamp(historico, 0, 100)
    
    # Función gaussiana centrada en 50%
    ideal_hum = 50.0
    desv_std = 15.0
    
    diff = abs(humedad - ideal_hum)
    score = 100.0 * math.exp(-0.5 * (diff / desv_std) ** 2)
    
    return _clamp(score, 0, 100)


def indice_uvi_robusto(
    radiacion_global: Optional[float],
    elevacion_solar: Optional[float],
    historico: float = 30.0
) -> float:
    """
    Índice UV (0-100, donde 100 = prohibido estar al sol sin protección).
    
    Basado en radiación solar global y elevación solar.
    
    0-25: Bajo
    26-50: Moderado (protección recomendada)
    51-75: Alto (evitar sol 10-16h)
    76-100: Muy alto (prohibido sin protección)
    
    Robusto: nunca None.
    """
    if all(v is None for v in [radiacion_global, elevacion_solar]):
        return _clamp(historico, 0, 100)
    
    rad = radiacion_global if radiacion_global is not None else 500.0
    elev = elevacion_solar if elevacion_solar is not None else 45.0
    
    # Radiación escalada a 0-100
    rad_factor = _clamp(rad / 1000.0)
    
    # Elevación solar (más alto = más peligroso)
    elev_factor = _clamp(elev / 90.0)
    
    # UVI combinado
    score = 100.0 * (
        0.7 * rad_factor +
        0.3 * elev_factor
    )
    
    return _clamp(score, 0, 100)


def sensacion_termica_confort_robusto(
    temp_c: Optional[float],
    humedad: Optional[float],
    viento: Optional[float],
    radiacion: Optional[float],
    historico: float = 50.0
) -> float:
    """
    Sensación térmica para confort humano (0-100).
    
    100 = confortable, 0 = muy frío o muy calor.
    
    Toma en cuenta:
      - Temperatura
      - Humedad (sofocación)
      - Viento (enfriamiento)
      - Radiación (calor)
    
    Robusto: nunca None.
    """
    if all(v is None for v in [temp_c, humedad, viento]):
        return _clamp(historico, 0, 100)
    
    t = temp_c if temp_c is not None else 18.0
    h = humedad if humedad is not None else 55.0
    v = viento if viento is not None else 0.0
    r = radiacion if radiacion is not None else 500.0
    
    # Componente temperatura (ideal 18-22°C)
    temp_factor = _clamp(1.0 - abs(t - 20.0) / 20.0)
    
    # Componente humedad (sofocación > 80%)
    hum_factor = _clamp(1.0 - abs(h - 50.0) / 40.0)
    
    # Componente viento (enfriamiento, pero también refresca)
    # Viento moderado (1-3 m/s) es agradable, extremos son malos
    viento_factor = _clamp(1.0 - abs(v - 2.0) / 5.0)
    
    # Componente radiación (exceso causa incomodidad)
    rad_factor = _clamp(1.0 - (r / 1000.0))
    
    score = 100.0 * (
        0.4 * temp_factor +
        0.3 * hum_factor +
        0.2 * viento_factor +
        0.1 * rad_factor
    )
    
    return _clamp(score, 0, 100)


# ============================================================================
# ÍNDICE SINTÉTICO CONFORT
# ============================================================================

def indice_confort_sintetico(
    temperatura_ideal: float,
    humedad_ideal: float,
    indice_uvi: float,
    sensacion_termica: float,
    lluvia_1h: Optional[float] = None,
    amplitud_termica: Optional[float] = None
) -> float:
    """
    Índice sintético confort 0-100 - SUMA PONDERADA DE 4 COMPONENTES.
    
    PESOS EXPLÍCITOS:
    - temperatura_ideal: 35% - Confort térmico principal
    - humedad_ideal: 25% - Sofocación/sequedad
    - indice_uvi: 20% - Protección solar
    - sensacion_termica: 20% - Percepción real del cuerpo
    
    CONTEXTOS INTEGRADOS:
    - Lluvia reduce confort MODERADAMENTE (menos que deporte/cetrería)
    - Amplitud térmica extrema (>75%) aumenta estrés térmico (-15% confort)
    """
    
    if lluvia_1h is None:
        lluvia_1h = 0.0
    if amplitud_termica is None:
        amplitud_termica = 0.0
        
    # ESCENARIO 1: AMPLITUD TÉRMICA EXTREMA (>75%) - Estrés térmico
    if amplitud_termica > 75.0:
        logger.debug(f"AMPLITUD TÉRMICA EXTREMA ({amplitud_termica:.1f}%): Estrés +20%")
        
        # Amplitud extrema aumenta estrés, reduce componente térmica
        temp_estres = _clamp(temperatura_ideal * 0.85)  # -15% por estrés
        hum_estres = _clamp(humedad_ideal * 0.90)       # -10% (deshidratación)
        uv_estres = indice_uvi  # UV no cambia
        sent_estres = _clamp(sensacion_termica * 0.85)  # -15% (se siente peor)
        
        indice_estres = _clamp(
            0.35 * temp_estres +
            0.25 * hum_estres +
            0.20 * uv_estres +
            0.20 * sent_estres
        )
        
        logger.debug(f"Confort con amplitud extrema: temp={temp_estres:.1f}, hum={hum_estres:.1f} -> {indice_estres:.1f}")
        
        # Si además lluvia, combinar penalizaciones
        if lluvia_1h > 0.1:
            penalizacion_lluvia = 1.0 - ((lluvia_1h / 100.0) ** 0.9)
            indice_final = indice_estres * penalizacion_lluvia
            logger.debug(f"Amplitud extrema + lluvia: {indice_estres:.1f} * {penalizacion_lluvia:.2f} = {indice_final:.1f}")
            return _clamp(indice_final)
        
        return _clamp(indice_estres)
    
    # ESCENARIO 2: LLUVIA EN PROGRESO (lluvia_1h > 0.1 mm)
    elif lluvia_1h > 0.1:
        logger.debug(f"LLUVIA EN PROGRESO ({lluvia_1h:.2f}mm): Confort LIGERAMENTE REDUCIDO")
        
        # Lluvia reduce confort pero NO DRASTICAMENTE (es menos crítico que física)
        # Penalización moderada: ropa mojada es incómoda pero no desastrosa
        temp_lluvia = _clamp(temperatura_ideal * (1.0 - (lluvia_1h / 50.0)))  # 2% por mm lluvia
        hum_lluvia = _clamp(humedad_ideal * (1.0 - (lluvia_1h / 100.0)))      # 1% por mm lluvia
        uv_lluvia = _clamp(indice_uvi * (1.0 - (lluvia_1h / 80.0)))          # UV protected by clouds
        sent_lluvia = _clamp(sensacion_termica * (1.0 - (lluvia_1h / 60.0))) # Sensación se reduce poco
        
        # SUMA PONDERADA de los 4 componentes penalizados
        indice_lluvia = _clamp(
            0.35 * temp_lluvia +       # temperatura: 35%
            0.25 * hum_lluvia +        # humedad: 25%
            0.20 * uv_lluvia +         # UV: 20%
            0.20 * sent_lluvia         # sensación: 20%
        )
        
        # Penalización MENOR que otros índices (confort es más robusto a lluvia)
        penalizacion = 1.0 - ((lluvia_1h / 100.0) ** 0.9)  # Exponencial muy suave
        indice_final = indice_lluvia * penalizacion
        
        logger.debug(
            f"Confort con lluvia: temp={temp_lluvia:.1f}, hum={hum_lluvia:.1f}, "
            f"uv={uv_lluvia:.1f}, sent={sent_lluvia:.1f} -> final={indice_final:.1f}"
        )
        
        return _clamp(indice_final)
    
    # ESCENARIO 3: SIN LLUVIA, SIN AMPLITUD EXTREMA - SUMA PONDERADA estándar
    else:
        indice_normal = _clamp(
            0.35 * temperatura_ideal +   # temperatura: 35%
            0.25 * humedad_ideal +       # humedad: 25%
            0.20 * indice_uvi +          # UV: 20%
            0.20 * sensacion_termica     # sensación: 20%
        )
        
        logger.debug(
            f"Confort sin lluvia: temp={temperatura_ideal:.1f}, hum={humedad_ideal:.1f}, "
            f"uv={indice_uvi:.1f}, sent={sensacion_termica:.1f} -> indice={indice_normal:.1f}"
        )
        
        return indice_normal


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def calcular_confort_completa(data: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Calcula TODOS los índices de confort.
    
    Entrada: Dict con sensores clima
    Salida: 5 índices (4 componentes + 1 sintético)
    """
    
    temp_c = data.get("temperatura")
    humedad = data.get("humedad")
    radiacion = data.get("radiacion_global")
    elevacion_solar = data.get("elevacion_solar")  # En grados
    viento = data.get("viento_medio")
    lluvia_1h = data.get("lluvia", 0.0)  # Lluvia en última hora
    
    # Calcular índices robustos
    temp_ideal = temperatura_ideal_robusto(temp_c)
    hum_ideal = humedad_ideal_robusto(humedad)
    uvi = indice_uvi_robusto(radiacion, elevacion_solar)
    sens_term = sensacion_termica_confort_robusto(temp_c, humedad, viento, radiacion)
    
    # Índice sintético = valoración integral (lluvia + amplitud térmica integradas)
    amplitud_term = data.get("amplitud_termica_tendencial", 0.0)
    indice_sint = indice_confort_sintetico(temp_ideal, hum_ideal, uvi, sens_term, lluvia_1h=lluvia_1h, amplitud_termica=amplitud_term)
    
    return {
        "temperatura_ideal": temp_ideal,
        "humedad_ideal": hum_ideal,
        "indice_uvi": uvi,
        "sensacion_termica": sens_term,
        "sensacion_termica_confort": sens_term,
        "indice_confort_sintetico": indice_sint,
        "indice_confort": indice_sint  # Compatibilidad
    }
