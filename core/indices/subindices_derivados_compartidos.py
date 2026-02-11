"""
SUBÍNDICES DERIVADOS COMPARTIDOS v1.0

Propósito: Crear índices que se usan SIMULTÁNEAMENTE en múltiples dominios.
Esto asegura CONSISTENCIA y COHERENCIA entre dominios.

Índices compartidos:
1. comfort_universal() → Cetrería, Deporte, Confort
2. riesgo_termico_integrado() → Salud, Confort
3. estabilidad_atmosferica() → Confort, desde Astronomía
4. humedad_suelo_integrada() → Riego, Hidrología
5. capacidad_infiltracion_compartida() → Lluvia, Hidrología
6. radiacion_compuesta() → Astronomía, Salud
7. contexto_lluvia_global() → TODOS (salvo Riego/Hidrología)
"""

from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def _clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Limita valor entre mín y máx."""
    return max(min_val, min(max_val, value))


# ============================================================================
# 1. COMFORT UNIVERSAL (Cetrería + Deporte + Confort)
# ============================================================================

def comfort_universal(
    temperatura: Optional[float] = None,
    humedad: Optional[float] = None,
    sensacion_termica: Optional[float] = None,
    velocidad_viento: Optional[float] = None,
    radiacion: Optional[float] = None
) -> float:
    """
    SUBÍNDICE COMPARTIDO: Confort térmico universal (0-100).
    
    Usado por:
    - CETRERÍA: como confort_ave (20%)
    - DEPORTE: como confort_atletas (25%)
    - CONFORT: como base para temperatura_ideal + sensacion (55% combinado)
    
    Calcula comfort térmico PURO sin lluvia (lluvia se aplica FUERA).
    
    Componentes:
    - 40%: Temperatura (ideal 18-22°C)
    - 30%: Humedad relativa (ideal 50-60%)
    - 20%: Sensación térmica (percepción real)
    - 10%: Viento (1-3 m/s es agradable)
    """
    t = temperatura if temperatura is not None else 20.0
    h = humedad if humedad is not None else 55.0
    s = sensacion_termica if sensacion_termica is not None else 50.0
    v = velocidad_viento if velocidad_viento is not None else 2.0
    
    # Temperatura: ideal 18-22°C
    temp_factor = _clamp(1.0 - abs(t - 20.0) / 20.0)
    
    # Humedad: ideal 50-60%
    hum_factor = _clamp(1.0 - abs(h - 55.0) / 40.0)
    
    # Sensación térmica: usar directamente
    sens_factor = _clamp(s)
    
    # Viento: 1-3 m/s es ideal
    viento_factor = _clamp(1.0 - abs(v - 2.0) / 5.0)
    
    score = (
        temp_factor * 0.40 +    # temperatura: 40%
        hum_factor * 0.30 +     # humedad: 30%
        sens_factor * 0.20 +    # sensación: 20%
        viento_factor * 0.10    # viento: 10%
    )
    
    return _clamp(score * 100.0)


# ============================================================================
# 2. RIESGO TÉRMICO INTEGRADO (Salud + Confort)
# ============================================================================

def riesgo_termico_integrado(
    riesgo_calor: Optional[float] = None,
    riesgo_frio: Optional[float] = None,
    temperatura: Optional[float] = None
) -> float:
    """
    SUBÍNDICE COMPARTIDO: Riesgo térmico (0-100, donde alto = RIESGO).
    
    Usado por:
    - SALUD: para ponderar UV + riesgos térmicos
    - CONFORT: como inverso (100 - riesgo = confort)
    
    Integra:
    - Riesgo de calor extremo
    - Riesgo de frío extremo
    - Temperatura actual como contexto
    
    Lógica: suma de riesgos, pero contextualizada en estación.
    """
    calor = riesgo_calor if riesgo_calor is not None else 20.0
    frio = riesgo_frio if riesgo_frio is not None else 20.0
    temp = temperatura if temperatura is not None else 15.0
    
    # Peso dinámico según estación (temperatura como proxy)
    if temp > 25:
        # Verano: calor es más crítico
        peso_calor = 0.70
        peso_frio = 0.30
    elif temp < 5:
        # Invierno: frío es más crítico
        peso_calor = 0.30
        peso_frio = 0.70
    else:
        # Primavera/Otoño: balanceado
        peso_calor = 0.50
        peso_frio = 0.50
    
    riesgo_ponderado = (calor * peso_calor) + (frio * peso_frio)
    
    return _clamp(riesgo_ponderado)


# ============================================================================
# 3. ESTABILIDAD ATMOSFÉRICA (Confort desde Astronomía)
# ============================================================================

def estabilidad_atmosferica(
    amplitud_termica: Optional[float] = None,
    humedad: Optional[float] = None
) -> float:
    """
    SUBÍNDICE COMPARTIDO: Estabilidad atmosférica = CONFORT AMBIENTAL (0-100).
    
    Usado por:
    - CONFORT: para mejorar sensación (añade +5% si estable)
    - ASTRONOMÍA: para validar calidad óptica
    
    Lógica:
    - Amplitud térmica BAJA (diferencia día-noche pequeña) = ESTABLE = CONFORT
    - Amplitud térmica ALTA (variación extrema) = INESTABLE = INCÓMODO
    
    Inverso de amplitud_termica.
    """
    amp = amplitud_termica if amplitud_termica is not None else 50.0
    hum = humedad if humedad is not None else 60.0
    
    # Inversión: baja amplitud = forma alta estabilidad
    # Si amp=100 (muy variable) → estabilidad=0
    # Si amp=0 (muy estable) → estabilidad=100
    estabilidad_amp = (1.0 - (amp / 100.0)) * 100.0
    
    # Humedad extrema (muy seca o muy húmeda) reduce estabilidad
    if hum < 30 or hum > 85:
        penalizacion_hum = 0.8  # 20% reducción
    else:
        penalizacion_hum = 1.0
    
    score = estabilidad_amp * penalizacion_hum
    
    return _clamp(score)


# ============================================================================
# 4. HUMEDAD SUELO INTEGRADA (Riego + Hidrología)
# ============================================================================

def humedad_suelo_integrada(
    humedad_cultivo: Optional[float] = None,
    humedad_tendencial: Optional[float] = None
) -> float:
    """
    SUBÍNDICE COMPARTIDO: Estado humedad suelo integrado (0-100).
    
    Usado por:
    - RIEGO: para aumentar peso de humedad (35% en vez de 30%)
    - HIDROLOGÍA: para aumentar peso de humedad (25% en vez de 20%)
    
    Combina:
    - Humedad actual del cultivo (RIEGO)
    - Tendencia de humedad del suelo (HIDROLOGÍA)
    
    Resultado: medida más robusta de "cuánta agua hay disponible".
    """
    cult = humedad_cultivo if humedad_cultivo is not None else 50.0
    tend = humedad_tendencial if humedad_tendencial is not None else 50.0
    
    # Ponderación: 60% actual, 40% tendencia
    score = (cult * 0.60) + (tend * 0.40)
    
    return _clamp(score)


# ============================================================================
# 5. CAPACIDAD INFILTRACIÓN COMPARTIDA (Lluvia + Hidrología)
# ============================================================================

def capacidad_infiltracion_compartida(
    tipo_suelo: Optional[str] = None,
    pendiente_pct: Optional[float] = None,
    humedad_actual: Optional[float] = None
) -> float:
    """
    SUBÍNDICE COMPARTIDO: Capacidad del suelo para infiltrar agua (0-100).
    
    Usado por:
    - LLUVIA: para calcular riesgo_inundacion más preciso
    - HIDROLOGÍA: para mejorar tasa_infiltración
    
    Considera:
    - Tipo de suelo (arenoso → buena infiltración, arcilla → mala)
    - Pendiente (muy inclinado → escorrentía)
    - Humedad actual (saturado → no infiltra)
    
    Resultado: capacidad REAL del suelo en AHORA.
    """
    suelo = tipo_suelo if tipo_suelo is not None else "franco"
    pend = pendiente_pct if pendiente_pct is not None else 5.0
    hum = humedad_actual if humedad_actual is not None else 50.0
    
    # Capacidad base por tipo suelo (mm/h)
    infiltr_base = {
        'arenoso': 25.0,
        'franco_arenoso': 10.0,
        'franco': 6.0,
        'franco_arcilloso': 2.0,
        'arcilla': 0.3
    }
    ks = infiltr_base.get(suelo, 6.0)
    
    # Reducción por pendiente (agua escurre)
    pendiente_factor = max(0.3, 1.0 - (pend / 100.0) * 0.7)
    
    # Reducción por saturación (sobre 80% = casi no infiltra)
    if hum > 85:
        saturacion_factor = 0.2
    elif hum > 75:
        saturacion_factor = 0.5
    else:
        saturacion_factor = 1.0
    
    # Score: normalizado 0-100 (considerando ks máximo ~25)
    score = (ks / 25.0) * pendiente_factor * saturacion_factor * 100.0
    
    return _clamp(score)


# ============================================================================
# 6. RADIACIÓN COMPUESTA (Astronomía + Salud)
# ============================================================================

def radiacion_compuesta(
    indice_claridad_kt: Optional[float] = None,
    indice_uvi: Optional[float] = None
) -> float:
    """
    SUBÍNDICE COMPARTIDO: Radiación solar compuesta (0-100).
    
    Usado por:
    - ASTRONOMÍA: para mejorar predicción de calidad solar
    - SALUD: para mejorar cálculo de UV real
    
    Combina:
    - K_t (claridad: radiación global / extraterrestre)
    - UV (radiación UV específica)
    
    Resultado: medida integral de radiación solar.
    """
    kt = indice_claridad_kt if indice_claridad_kt is not None else 50.0
    uvi = indice_uvi if indice_uvi is not None else 5.0
    
    # Normalizar UVI (0-12) a 0-100
    uvi_norm = min(uvi / 12.0, 1.0) * 100.0
    
    # Combinación: 60% K_t (radiación total), 40% UV (específico)
    score = (kt * 0.60) + (uvi_norm * 0.40)
    
    return _clamp(score)


# ============================================================================
# 7. CONTEXTO LLUVIA GLOBAL (Afecta a TODOS excepto Riego/Hidrología)
# ============================================================================

def contexto_lluvia_global(
    lluvia_1h: Optional[float] = None,
    probabilidad_lluvia_sundqvist: Optional[float] = None
) -> Dict[str, float]:
    """
    CONTEXTO GLOBAL: Evalúa si hay lluvia actual o predicha.
    
    Propósito: Generar OVERRIDE GLOBAL que afecte a:
    - CETRERÍA: penalización fuerte
    - DEPORTE: penalización fuerte
    - CONFORT: penalización moderada
    - ASTRONOMÍA: penalización CRÍTICA
    - SALUD: penalización moderada
    
    Retorna:
    - factor_penalizacion_lluvia (0.0 = lluvia extrema, 1.0 = sin lluvia)
    - es_lluvia_actual (bool)
    - es_lluvia_predicha (bool)
    - severidad_lluvia (0-100)
    
    Lógica:
    1. Si lluvia_1h > 0.5mm → LLUVIA ACTUAL (penalización inmediata)
    2. Si sundqvist > 70% → LLUVIA PREDICHA (precaución)
    3. Combinación = severidad global
    """
    lluvia = lluvia_1h if lluvia_1h is not None else 0.0
    sundq = probabilidad_lluvia_sundqvist if probabilidad_lluvia_sundqvist is not None else 0.0
    
    # Detectar lluvia actual
    es_lluvia_actual = lluvia > 0.5
    
    # Detectar precipitación predicha
    es_lluvia_predicha = sundq > 70.0
    
    # Severidad general (0-100)
    if es_lluvia_actual:
        # Lluvia actual: escalada exponencial
        severidad = min(100.0, (lluvia / 50.0) ** 0.8 * 100.0)
    elif es_lluvia_predicha:
        # Lluvia predicha: moderada
        severidad = (sundq - 70.0) / 30.0 * 50.0  # Max 50%
    else:
        severidad = 0.0
    
    # Factor de penalización (0.0 = penalización máxima, 1.0 = sin penalización)
    if severidad > 0:
        # Exponencial inverso: grave lluvia → factor cercano a 0
        penalizacion = (1.0 - (severidad / 100.0)) ** 1.2
    else:
        penalizacion = 1.0
    
    return {
        "factor_penalizacion_lluvia": _clamp(penalizacion),
        "es_lluvia_actual": es_lluvia_actual,
        "es_lluvia_predicha": es_lluvia_predicha,
        "severidad_lluvia": _clamp(severidad),
    }


# ============================================================================
# FUNCIONES DE VALIDACIÓN / DEBUG
# ============================================================================

def validar_subindices(datos: Dict[str, float]) -> Dict[str, float]:
    """
    Computa todos los sub-índices derivados dados unos datos.
    Útil para DEBUG y testing.
    """
    return {
        "comfort_universal": comfort_universal(
            datos.get("temperatura"),
            datos.get("humedad"),
            datos.get("sensacion_termica"),
            datos.get("viento_medio")
        ),
        "riesgo_termico": riesgo_termico_integrado(
            datos.get("riesgo_calor_extremo"),
            datos.get("riesgo_frio_extremo"),
            datos.get("temperatura")
        ),
        "estabilidad_atmosferica": estabilidad_atmosferica(
            datos.get("amplitud_termica"),
            datos.get("humedad")
        ),
        "humedad_suelo_integrada": humedad_suelo_integrada(
            datos.get("humedad_cultivo"),
            datos.get("humedad_tendencial")
        ),
        "infiltracion_compartida": capacidad_infiltracion_compartida(
            datos.get("tipo_suelo"),
            datos.get("pendiente_pct"),
            datos.get("humedad_actual")
        ),
        "radiacion_compuesta": radiacion_compuesta(
            datos.get("indice_claridad_kt"),
            datos.get("indice_uvi")
        ),
        "contexto_lluvia": contexto_lluvia_global(
            datos.get("lluvia_1h"),
            datos.get("probabilidad_lluvia_sundqvist")
        )
    }
