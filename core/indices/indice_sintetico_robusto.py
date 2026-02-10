"""
MÓDULO: Índice Sintético Robusto Dinámico v1.0

Propósito:
  Crear un "promedio inteligente" de múltiples índices que:
  1. Nunca se rompe aunque falten sensores (maneja None gracefully)
  2. Renormaliza pesos dinámicamente según qué índices estén disponibles
  3. Reutilizable en cetrería, lluvia, confort, deporte, etc.

Arquitectura:
  - Entrada: Dict[nombreIndice] = valor (0-100) o None
  - Entrada: Dict[nombreIndice] = peso (0-1)
  - Proceso: Filtra None, renormaliza pesos, promedia
  - Salida: Índice sintético 0-100 (nunca None si hay ≥1 índice válido)

Fecha: 10 de febrero de 2026
Autor: MeteoSerV3 Core
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


def _clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    """Acotar valor entre min y max."""
    return max(min(value, max_value), min_value)


def calcular_indice_sintetico(
    indices: Dict[str, Optional[float]],
    pesos: Dict[str, float],
    nombre_contexto: str = "índice",
    min_indices_validos: int = 1
) -> Optional[float]:
    """
    Calcula promedio ponderado robusto dinámico.
    
    Args:
        indices: Dict con nombres de índices (e.g., "viento_cetreria", "visibilidad")
                 Valores: 0-100 o None
        pesos: Dict con pesos (0-1) para cada índice
               CONSTRAINTS: sum(pesos) ≈ 1.0 (se renormaliza automáticamente)
        nombre_contexto: Para logging (e.g., "cetrería", "lluvia")
        min_indices_validos: Mínimo de índices no-None requeridos
    
    Returns:
        Índice sintético 0-100, o None si no hay suficientes datos válidos
    
    Examples:
        >>> indices = {
        ...     "viento": 75.0,
        ...     "visibilidad": 80.0,
        ...     "barro": None,  # Sensor roto
        ...     "confort": 70.0
        ... }
        >>> pesos = {
        ...     "viento": 0.4,
        ...     "visibilidad": 0.3,
        ...     "barro": 0.2,
        ...     "confort": 0.1
        ... }
        >>> resultado = calcular_indice_sintetico(indices, pesos, "cetrería")
        # Toma 3 válidos, renormaliza pesos a {v:0.4/0.8, vi:0.3/0.8, c:0.1/0.8}
        # Retorna: (75*0.5 + 80*0.375 + 70*0.125) = 75.625
    """
    
    # Filtrar índices válidos (no None)
    indices_validos = {
        nombre: valor 
        for nombre, valor in indices.items() 
        if valor is not None
    }
    
    if len(indices_validos) < min_indices_validos:
        logger.warning(
            f"[{nombre_contexto.upper()}] Insuficientes índices válidos: "
            f"{len(indices_validos)}/{len(indices)} disponibles. "
            f"Mínimo requerido: {min_indices_validos}"
        )
        return None
    
    # Extraer pesos de índices válidos
    pesos_activos = {
        nombre: pesos.get(nombre, 0.0)
        for nombre in indices_validos
    }
    
    peso_total = sum(pesos_activos.values())
    
    if peso_total <= 0:
        logger.warning(
            f"[{nombre_contexto.upper()}] Suma de pesos = 0. "
            f"Verificar diccionario de pesos."
        )
        return None
    
    # Renormalizar pesos a suma=1.0
    pesos_renormalizados = {
        nombre: peso / peso_total
        for nombre, peso in pesos_activos.items()
    }
    
    # Calcular promedio ponderado
    resultado = sum(
        indices_validos[nombre] * pesos_renormalizados[nombre]
        for nombre in indices_validos
    )
    
    # Logging info
    indices_rotos = set(indices.keys()) - set(indices_validos.keys())
    if indices_rotos:
        logger.debug(
            f"[{nombre_contexto.upper()}] Índices unavailable: {', '.join(indices_rotos)}"
        )
    
    return _clamp(resultado, 0.0, 100.0)


def calcular_multiples_sinteticos(
    indices_por_area: Dict[str, Dict[str, Optional[float]]],
    pesos_por_area: Dict[str, Dict[str, float]],
    min_indices_validos: int = 1
) -> Dict[str, Optional[float]]:
    """
    Calcula múltiples índices sintéticos en paralelo (e.g., cetrería + lluvia + confort).
    
    Args:
        indices_por_area: 
            {
                "cetreria": {"viento": 75, "visibilidad": 80, ...},
                "lluvia": {"riesgo_inundacion": 30, "visibilidad_carretera": 90, ...},
                "confort": {"temperatura": 70, "humedad": 75, ...}
            }
        pesos_por_area:
            {
                "cetreria": {"viento": 0.4, "visibilidad": 0.3, ...},
                "lluvia": {"riesgo_inundacion": 0.5, "visibilidad_carretera": 0.5},
                ...
            }
        min_indices_validos: Mínimo por área
    
    Returns:
        Dict[area] = índice_sintetico (0-100 o None)
    """
    
    resultados = {}
    
    for area, indices in indices_por_area.items():
        pesos = pesos_por_area.get(area, {})
        
        if not pesos:
            logger.warning(f"[{area.upper()}] No hay pesos definidos")
            resultados[area] = None
            continue
        
        indice = calcular_indice_sintetico(
            indices,
            pesos,
            nombre_contexto=area,
            min_indices_validos=min_indices_validos
        )
        
        resultados[area] = indice
    
    return resultados


def diagnostico_indices(
    indices: Dict[str, Optional[float]],
    nombre_contexto: str = "índice"
) -> Dict[str, any]:
    """
    Análisis diagnóstico de qué índices están disponibles/rompidos.
    
    Returns:
        {
            "disponibles": [...],          # Índices con valor válido
            "rotos": [...],                # Índices con None
            "num_disponibles": int,
            "num_rotos": int,
            "porcentaje_cobertura": float  # % disponibles
        }
    """
    
    disponibles = [n for n, v in indices.items() if v is not None]
    rotos = [n for n, v in indices.items() if v is None]
    total = len(indices)
    
    return {
        "contexto": nombre_contexto,
        "disponibles": disponibles,
        "rotos": rotos,
        "num_disponibles": len(disponibles),
        "num_rotos": len(rotos),
        "total": total,
        "porcentaje_cobertura": 100.0 * len(disponibles) / total if total > 0 else 0.0
    }


# ============================================================================
# CONFIGURACIONES PREDEFINIDAS (Pesos estándar recomendados)
# ============================================================================

PESOS_CETRERIA = {
    "viento_cetreria": 0.25,
    "visibilidad_terreno": 0.25,
    "termales_probabilidad": 0.15,
    "barro_campo": 0.15,
    "confort_ave": 0.20
}

PESOS_LLUVIA = {
    "riesgo_inundacion": 0.30,
    "visibilidad_carretera": 0.25,
    "adherencia_terreno": 0.25,
    "probabilidad_rayos": 0.20
}

PESOS_CONFORT = {
    "temperatura_ideal": 0.35,
    "humedad_ideal": 0.25,
    "indice_uvi": 0.20,
    "sensacion_termica": 0.20
}

PESOS_DEPORTE = {
    "adherencia_terreno": 0.30,
    "visibilidad": 0.25,
    "viento_juego": 0.20,
    "confort_atletas": 0.25
}

PESOS_PREDEFINIDOS = {
    "cetreria": PESOS_CETRERIA,
    "lluvia": PESOS_LLUVIA,
    "confort": PESOS_CONFORT,
    "deporte": PESOS_DEPORTE
}

# ============================================================================
# FUSION DE INDICES SINTETICOS (ponderado por precision y relevancia)
# ============================================================================

PESOS_FUSION_BASE = {
    "indice_cetreria_sintetico": 0.25,
    "indice_lluvia_sintetico": 0.25,
    "indice_confort_sintetico": 0.25,
    "indice_deporte_sintetico": 0.25
}

# Precision base por calidad de formula (conservador, ajustar con validacion real)
PRECISION_FORMULA_BASE = {
    "indice_cetreria_sintetico": 0.45,
    "indice_lluvia_sintetico": 0.35,
    "indice_confort_sintetico": 0.50,
    "indice_deporte_sintetico": 0.45
}

# Relevancia base por dominio (1.0 = neutral)
RELEVANCIA_BASE = {
    "indice_cetreria_sintetico": 1.0,
    "indice_lluvia_sintetico": 1.0,
    "indice_confort_sintetico": 1.0,
    "indice_deporte_sintetico": 1.0
}


def calcular_indice_fusion_sinteticos(
    indices: Dict[str, Optional[float]],
    pesos_base: Optional[Dict[str, float]] = None,
    precision_base: Optional[Dict[str, float]] = None,
    relevancia_base: Optional[Dict[str, float]] = None,
    nombre_contexto: str = "fusion"
) -> Dict[str, Optional[float]]:
    """
    Fusiona indices sinteticos aplicando pesos por precision y relevancia.

    peso_final = peso_base * precision_base * relevancia_base

    Returns:
        {
            "indice_fusion": float | None,
            "confianza": float | None,
            "pesos_ajustados": Dict[str, float]
        }
    """
    pesos_base = pesos_base or PESOS_FUSION_BASE
    precision_base = precision_base or PRECISION_FORMULA_BASE
    relevancia_base = relevancia_base or RELEVANCIA_BASE

    pesos_ajustados = {}
    for key, peso in pesos_base.items():
        p = precision_base.get(key, 1.0)
        r = relevancia_base.get(key, 1.0)
        pesos_ajustados[key] = float(peso) * float(p) * float(r)

    indice_fusion = calcular_indice_sintetico(
        indices,
        pesos_ajustados,
        nombre_contexto=nombre_contexto,
        min_indices_validos=1
    )

    # Confianza = precision media ponderada de los indices disponibles
    indices_validos = {k: v for k, v in indices.items() if v is not None}
    if not indices_validos:
        confianza = None
    else:
        peso_total = sum(pesos_ajustados.get(k, 0.0) for k in indices_validos)
        if peso_total <= 0:
            confianza = None
        else:
            confianza = 100.0 * sum(
                (pesos_ajustados.get(k, 0.0) / peso_total) * precision_base.get(k, 1.0)
                for k in indices_validos
            )

    return {
        "indice_fusion": indice_fusion,
        "confianza": _clamp(confianza, 0.0, 100.0) if confianza is not None else None,
        "pesos_ajustados": pesos_ajustados
    }
