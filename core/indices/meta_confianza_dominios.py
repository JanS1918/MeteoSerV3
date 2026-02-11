"""
META-CONFIANZA POR DOMINIO V1.0
═════════════════════════════════════════════════════════════════════════════

Calcula confianza (0-100%) de cada índice sintético basándose en:
1. Disponibilidad de subíndices requeridos
2. Calidad de datos de entrada
3. Consistencia interna
4. Cross-domain validation

Fecha: 11 de febrero de 2026
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


# Subíndices REQUERIDOS para cada dominio (sin estos, confianza < 50%)
SUBINDICES_CRITICOS = {
    "cetreria": ["viento_cetreria", "visibilidad_terreno", "termales_probabilidad"],
    "lluvia": ["riesgo_inundacion", "visibilidad_carretera", "adherencia_terreno"],
    "confort": ["temperatura_ideal", "humedad_ideal", "indice_uvi"],
    "deporte": ["adherencia_terreno", "visibilidad", "viento_juego"],
    "riego": ["balance_hidrico_neto", "estres_hidrico_cultivo", "disponibilidad_agua_cultivable"],
    "astronomia": ["horas_luz", "disponibilidad_obs_nocturna", "indice_claridad_kt"],
    "salud": ["indice_uvi", "riesgo_calor_extremo", "riesgo_frio_extremo"],
    "hidrologia": ["tasa_infiltracion_potencial", "riesgo_escorrentia", "estado_humedad_tendencial"],
}

# Contextos que MEJORAN confianza si están presentes
CONTEXTOS_MEJORADORES = {
    "cetreria": ["riesgo_escorrentia", "comfort_universal", "contexto_lluvia_global"],
    "lluvia": ["capacidad_infiltracion_compartida", "contexto_lluvia_global"],
    "confort": ["amplitud_termica_tendencial", "contexto_lluvia_global", "comfort_universal"],
    "deporte": ["riesgo_escorrentia", "amplitud_termica_tendencial", "contexto_lluvia_global"],
    "riego": ["humedad_suelo_integrada", "probabilidad_lluvia_sundqvist"],
    "astronomia": ["lluvia_1h", "probabilidad_lluvia_sundqvist", "visibilidad_km"],
    "salud": ["lluvia_1h", "amplitud_termica_tendencial"],
    "hidrologia": ["humedad_suelo_integrada", "capacidad_infiltracion_compartida"],
}


def calcular_confianza_dominio(
    dominio: str,
    indice_sintetico: Optional[float],
    subindices_disponibles: Dict[str, Optional[float]],
    contextos_disponibles: Dict[str, Optional[float]],
    rango_normal_min: float = 20.0,
    rango_normal_max: float = 80.0
) -> Dict[str, float]:
    """
    Calcula confianza (0-100) del índice sintético de un dominio.
    
    Criterios:
    1. Completitud de subíndices críticos (50% base)
    2. Disponibilidad de contextos mejoradores (+5% cada uno)
    3. Coherencia interna (índice dentro de rango normal: +10%)
    4. Cross-domain validation (contextos de otros dominios: +5%)
    
    Args:
        dominio: "cetreria", "lluvia", "confort", etc.
        indice_sintetico: Valor final 0-100
        subindices_disponibles: Dict con todos los subíndices
        contextos_disponibles: Dict con contextos compartidos
        rango_normal_min/max: Rango donde índice es "normal" (sin alertas)
    
    Returns:
        {
            'confianza': float 0-100,
            'completitud_subindices': float 0-100,
            'contextos_presentes': float 0-100,
            'consistencia_interna': float 0-100,
            'razon_baja_confianza': str (si aplica),
            'recomendacion': str
        }
    """
    
    if not dominio.lower() in SUBINDICES_CRITICOS:
        return {
            "confianza": 50.0,
            "completitud_subindices": 0.0,
            "contextos_presentes": 0.0,
            "consistencia_interna": 50.0,
            "razon_baja_confianza": f"Dominio '{dominio}' no reconocido",
            "recomendacion": "Verificar nombre de dominio"
        }
    
    dominio = dominio.lower()
    
    # ═══════════════════════════════════════════════════════════════════════
    # 1. COMPLETITUD DE SUBÍNDICES CRÍTICOS (50% base)
    # ═══════════════════════════════════════════════════════════════════════
    criticos = SUBINDICES_CRITICOS[dominio]
    criticos_presentes = sum(
        1 for c in criticos 
        if subindices_disponibles.get(c) is not None
    )
    completitud_subindices = (criticos_presentes / len(criticos)) * 100.0
    confianza = completitud_subindices * 0.5  # 50% de los puntos
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. CONTEXTOS MEJORADORES (+5% cada uno disponible, máx 25%)
    # ═══════════════════════════════════════════════════════════════════════
    mejoradores = CONTEXTOS_MEJORADORES.get(dominio, [])
    mejoradores_presentes = sum(
        1 for m in mejoradores 
        if contextos_disponibles.get(m) is not None
    )
    contextos_presentes = (mejoradores_presentes / max(len(mejoradores), 1)) * 100.0
    confianza += min(mejoradores_presentes * 5.0, 25.0)  # Máximo +25%
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. CONSISTENCIA INTERNA (±10%)
    # ═══════════════════════════════════════════════════════════════════════
    consistencia_interna = 50.0  # Neutral por defecto
    razon_baja = ""
    
    if indice_sintetico is not None:
        if rango_normal_min <= indice_sintetico <= rango_normal_max:
            # Índice en rango normal: +10% confianza (datos coherentes)
            confianza += 10.0
            consistencia_interna = 100.0
        else:
            # Índice fuera de rango normal: -5% confianza (posible anomalía)
            confianza -= 5.0
            consistencia_interna = 40.0
            if indice_sintetico < rango_normal_min:
                razon_baja = f"Índice anormalmente BAJO ({indice_sintetico:.0f}%)"
            else:
                razon_baja = f"Índice anormalmente ALTO ({indice_sintetico:.0f}%)"
    else:
        # Sin índice sintético: -15% confianza (fallo crítico)
        confianza -= 15.0
        razon_baja = "Índice sintético NO calculado"
        consistencia_interna = 0.0
    
    # ═══════════════════════════════════════════════════════════════════════
    # 4. VALIDACIÓN CROSS-DOMAIN (±10%)
    # ═══════════════════════════════════════════════════════════════════════
    # Si lluvia está presente en TODOS los dominios que lo necesitan → +5%
    # Si amplitud está presente en dominio que la necesita → +5%
    cross_domain_bonus = 0.0
    
    if dominio in ["cetreria", "deporte", "confort", "astronomia"] and contextos_disponibles.get("contexto_lluvia_global"):
        cross_domain_bonus += 5.0
    
    if dominio in ["cetreria", "astronomia"] and contextos_disponibles.get("estabilidad_atmosferica"):
        cross_domain_bonus += 5.0
    
    confianza += min(cross_domain_bonus, 10.0)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CLAMP final [0, 100]
    # ═══════════════════════════════════════════════════════════════════════
    confianza_final = max(0.0, min(100.0, confianza))
    
    # RECOMENDACIÓN según confianza
    if confianza_final >= 85:
        recomendacion = "✓ Confianza ALTA: índice confiable para toma de decisiones"
    elif confianza_final >= 70:
        recomendacion = "⚠ Confianza MEDIA: considerar contexto local"
    elif confianza_final >= 50:
        recomendacion = "⚠ Confianza BAJA: usar como referencia, verificar manualmente"
    else:
        recomendacion = "❌ Confianza CRÍTICA: datos insuficientes, no recomendar acciones críticas"
    
    logger.debug(
        f"[CONFIANZA] {dominio.upper()}: {confianza_final:.0f}% "
        f"(subind={completitud_subindices:.0f}%, contextos={contextos_presentes:.0f}%, coherencia={consistencia_interna:.0f}%)"
    )
    
    return {
        "confianza": round(confianza_final, 1),
        "completitud_subindices": round(completitud_subindices, 1),
        "contextos_presentes": round(contextos_presentes, 1),
        "consistencia_interna": round(consistencia_interna, 1),
        "razon_baja_confianza": razon_baja,
        "recomendacion": recomendacion,
        "subindices_criticos_presentes": f"{criticos_presentes}/{len(criticos)}",
        "contextos_mejoradores_presentes": f"{mejoradores_presentes}/{len(mejoradores)}"
    }


def calcular_confianza_multiples_dominios(
    indices_sinteticos: Dict[str, Optional[float]],
    subindices: Dict[str, Optional[float]],
    contextos: Dict[str, Optional[float]]
) -> Dict[str, Dict]:
    """
    Calcula confianza para TODOS los dominios.
    
    Returns:
        {
            'confianzas': {'cetreria': {...}, 'lluvia': {...}, ...},
            'confianza_promedio': float,
            'confianza_minima': float,
            'dominios_problematicos': [str, ...],
            'resumen': str
        }
    """
    
    confianzas = {}
    valores_confianza = []
    problematicos = []
    
    for dominio in SUBINDICES_CRITICOS.keys():
        conf = calcular_confianza_dominio(
            dominio=dominio,
            indice_sintetico=indices_sinteticos.get(dominio),
            subindices_disponibles=subindices,
            contextos_disponibles=contextos,
            rango_normal_min=20.0,
            rango_normal_max=80.0
        )
        confianzas[dominio] = conf
        valores_confianza.append(conf["confianza"])
        
        if conf["confianza"] < 60:
            problematicos.append(dominio)
    
    confianza_promedio = sum(valores_confianza) / len(valores_confianza) if valores_confianza else 0.0
    confianza_minima = min(valores_confianza) if valores_confianza else 0.0
    
    if problematicos:
        resumen = f"⚠️ {len(problematicos)} dominios con baja confianza: {', '.join(problematicos)}"
    elif confianza_promedio >= 80:
        resumen = f"✓ Sistema íntegro: confianza promedio {confianza_promedio:.0f}%"
    else:
        resumen = f"⚠️ Sistema parcialmente degradado: confianza promedio {confianza_promedio:.0f}%"
    
    return {
        "confianzas": confianzas,
        "confianza_promedio": round(confianza_promedio, 1),
        "confianza_minima": round(confianza_minima, 1),
        "dominios_problematicos": problematicos,
        "resumen": resumen
    }
