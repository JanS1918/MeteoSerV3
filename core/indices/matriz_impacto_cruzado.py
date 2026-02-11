"""
MATRIZ IMPACTO CRUZADO V1.0
═════════════════════════════════════════════════════════════════════════════

Mapeo de cómo eventos en un dominio afectan a otros:
- Lluvia: impacta TODOS
- Amplitud térmica: impacta térmicos (CETRERÍA, DEPORTE, SALUD, CONFORT, ASTRONOMÍA)
- Escorrentía: impacta CETRERÍA, DEPORTE, RIEGO, HIDROLOGÍA
- Humedad de suelo: impacta RIEGO, HIDROLOGÍA

Fecha: 11 de febrero de 2026
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


# Matriz de impacto: Si X sube, cómo afecta a Y
# Valores: -100 (destruye), -50 (reduce seriamente), 0 (sin efecto), +50 (mejora), +100 (excelente)

MATRIZ_IMPACTO_LLUVIA = {
    "cetreria": -80,      # Lluvia DESTRUYE cetrería (no se puede volar)
    "deporte": -70,       # Lluvia cancela deporte
    "confort": -30,       # Lluvia reduce confort (ropa mojada, frío)
    "riego": +50,         # Lluvia beneficia riego (no hay que regar)
    "hidrologia": +40,    # Lluvia beneficia hidrología (infiltración)
    "salud": -20,         # Lluvia puede aumentar frío/hipotermia
    "astronomia": -90,    # Lluvia DESTRUYE astronomía
    "lluvia": 0,          # Lluvia es el propio dominio
}

MATRIZ_IMPACTO_AMPLITUD_TERMICA = {
    "cetreria": -40,      # Amplitud extrema reduce termales, vientos erráticos
    "deporte": -25,       # Atletas estresados térmicamente
    "confort": -15,       # Confort reducido por variactividad
    "salud": +30,         # AUMENTA riesgo (estrés térmico)
    "riego": -20,         # ET aumenta, más riego necesario
    "astronomia": +20,    # Amplitud = noches claras (buena for obs)
    "hidrologia": -10,    # Variabilidad afecta balance
    "lluvia": 5,          # Amplitud extrema PUEDE indicar tormentas
}

MATRIZ_IMPACTO_ESCORRENTIA = {
    "cetreria": -60,      # Barro, campo anegado
    "deporte": -90,       # Campo inaplayable
    "confort": 0,         # Sin efecto directo
    "riego": -40,         # Agua se escurre, sin infiltración
    "hidrologia": +50,    # Escorrentía alta = actividad hídrica
    "salud": 0,           # Sin efecto directo
    "astronomia": 0,      # Sin efecto directo
    "lluvia": +30,        # Escorrentía = lluvia ocurrió
}

MATRIZ_IMPACTO_HUMEDAD_SUELO_BAJA = {
    "riego": -80,         # URGENTE riego (sequedad crítica)
    "hidrologia": -50,    # Suelo seco
    "cetreria": -20,      # Polvo, visibilidad reducida
    "deporte": -10,       # Polvo, menos tracción
    "confort": +10,       # Menos huedad = confort
    "salud": -30,         # Más polvo = peor aire
    "astronomia": +30,    # Humedad baja = cielo claro
    "lluvia": -40,        # Suelo seco = más evapoación
}

MATRIZ_IMPACTO_CAPACIDAD_INFILTRACION_BAJA = {
    "lluvia": +50,        # Baja infiltración = riesgo inundación
    "hidrologia": -70,    # Suelo impermeable = problema
    "riego": -40,         # Agua no infiltra = escorrentía
    "confort": 0,
    "cetreria": 0,
    "deporte": -30,       # Suelo anegado = inaplayable
    "salud": 0,
    "astronomia": 0,
}


def calcular_impacto_evento(
    evento: str,
    valor_evento: float,  # 0-100
    dominios_afectados: Optional[list] = None
) -> Dict[str, float]:
    """
    Simula cómo un evento (lluvia, amplitud, etc.) afecta a todos los dominios.
    
    Args:
        evento: "lluvia", "amplitud_termica", "escorrentia", "humedad_suelo_baja", "infiltracion_baja"
        valor_evento: Intensidad 0-100
        dominios_afectados: Si None, usa matriz predefinida
    
    Returns:
        {
            'cetreria_impacto': float (-100 a +100),
            'deporte_impacto': float,
            ... (todos los dominios)
            'resumen': str
        }
    """
    
    evento = evento.lower()
    
    if evento == "lluvia":
        matriz = MATRIZ_IMPACTO_LLUVIA
        descripcion = f"Lluvia intensidad {valor_evento:.0f}%"
    elif evento == "amplitud_termica":
        matriz = MATRIZ_IMPACTO_AMPLITUD_TERMICA
        descripcion = f"Amplitud térmica {valor_evento:.0f}%"
    elif evento == "escorrentia":
        matriz = MATRIZ_IMPACTO_ESCORRENTIA
        descripcion = f"Escorrentía riesgo {valor_evento:.0f}%"
    elif evento == "humedad_suelo_baja":
        matriz = MATRIZ_IMPACTO_HUMEDAD_SUELO_BAJA
        descripcion = f"Humedad suelo BAJA {100-valor_evento:.0f}%"
    elif evento == "infiltracion_baja":
        matriz = MATRIZ_IMPACTO_CAPACIDAD_INFILTRACION_BAJA
        descripcion = f"Infiltración baja {100-valor_evento:.0f}%"
    else:
        return {
            "error": f"Evento '{evento}' no reconocido",
            "resumen": "Evento inválido"
        }
    
    # Normalizar valor a factor [0, 1]
    factor = max(0.0, min(1.0, valor_evento / 100.0))
    
    # Aplicar impacto a cada dominio
    impactos = {}
    for dominio, impacto_base in matriz.items():
        impacto_final = impacto_base * factor
        impactos[f"{dominio}_impacto"] = round(impacto_final, 1)
    
    # Clasificar impacto
    max_impacto = max(abs(v) for v in impactos.values())
    if max_impacto > 80:
        clasificacion = "CRÍTICO"
    elif max_impacto > 50:
        clasificacion = "SEVERO"
    elif max_impacto > 20:
        clasificacion = "MODERADO"
    else:
        clasificacion = "LEVE"
    
    impactos["clasificacion"] = clasificacion
    impactos["descripcion"] = descripcion
    impactos["resumen"] = f"{clasificacion}: {descripcion}"
    
    logger.debug(f"[IMPACTO CRUZADO] {descripcion} → {clasificacion}")
    
    return impactos


def calcular_impacto_multiples_eventos(
    eventos: Dict[str, float]  # {'lluvia': 85, 'amplitud_termica': 60, ...}
) -> Dict:
    """
    Calcula impacto COMBINADO de múltiples eventos.
    
    Args:
        eventos: {'evento': valor_0_100, ...}
    
    Returns:
        {
            'dominios_impactados': {
                'cetreria': {'lluvia': -80, 'amplitud': -40, 'total': -120, 'estado': 'CRÍTICO'},
                ...
            },
            'evento_mas_destructivo': str,
            'resumen_general': str
        }
    """
    
    dominios_impactados = {
        'cetreria': {}, 'deporte': {}, 'confort': {}, 'riego': {},
        'hidrologia': {}, 'salud': {}, 'astronomia': {}, 'lluvia': {}
    }
    
    # Calcular cada evento
    impactos_por_evento = {}
    for evento, valor in eventos.items():
        impactos = calcular_impacto_evento(evento, valor)
        impactos_por_evento[evento] = impactos
        
        for dominio in dominios_impactados.keys():
            clave = f"{dominio}_impacto"
            if clave in impactos:
                dominios_impactados[dominio][evento] = impactos[clave]
    
    # Calcular impacto TOTAL por dominio
    for dominio in dominios_impactados.keys():
        total = sum(dominios_impactados[dominio].values())
        dominios_impactados[dominio]["total_impacto"] = round(total, 1)
        
        # Clasificar severidad
        if total < -80:
            estado = "❌ CRÍTICO"
        elif total < -50:
            estado = "⚠️ SEVERO"
        elif total < -20:
            estado = "⚠️ MODERADO"
        elif total > 50:
            estado = "✓ MEJORA"
        else:
            estado = "neutral"
        
        dominios_impactados[dominio]["estado"] = estado
    
    # Evento más destructivo
    evento_mas_destructivo = min(
        eventos.items(),
        key=lambda x: impactos_por_evento.get(x[0], {}).get("clasificacion", "")
        if "CRÍTICO" in str(impactos_por_evento.get(x[0], {}).get("clasificacion", ""))
        else float('inf')
    )[0] if eventos else "ninguno"
    
    resumen_criticos = [
        f"{d}: {v['estado']} (impacto={v['total_impacto']:.0f})"
        for d, v in dominios_impactados.items()
        if "CRÍTICO" in v.get("estado", "") or "SEVERO" in v.get("estado", "")
    ]
    
    return {
        "dominios_impactados": dominios_impactados,
        "evento_mas_destructivo": evento_mas_destructivo,
        "resumen_general": "; ".join(resumen_criticos) if resumen_criticos else "Sistema resiliente (sin impactos críticos)",
        "total_eventos_evaluados": len(eventos)
    }
