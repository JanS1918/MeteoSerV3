#!/usr/bin/env python3
"""
FORMULA_BLOCKER_INYECTADO.py

Bloqueador que se inyecta en external_formula_discoverer para evitar
que candidatas conocidas como FALLIDAS sean descubiertas nuevamente.

Se auto-aplica cada vez que se corre el discoverer.
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("meteoser.formula_blocker")

# LISTA NEGRA PERMANENTE - Formulas que NUNCA deben descubrirse
FORMULA_BLACKLIST = {
    "scipy.optimize.curve_fit": {
        "parametro": "sensacion_termica",
        "razon": "NaN collapse en Mathematical Physics Layer",
        "severidad": "CRITICA",
        "score_maxima_alcanzada": 0.0,
        "tests_fallidos": ["PSICOTECNICO_MAESTRO_25_CAPAS", "QUICK_DUEL", "TIPO_ESPECIFICO"],
        "bloqueado_desde": "2025-01-27",
        "permanente": True
    },
    
    "scipy.integrate.quad": {
        "parametro": "indice_uv",
        "razon": "No converge - NaN en integral numerica",
        "severidad": "CRITICA",
        "score_maxima_alcanzada": 0.0,
        "tests_fallidos": ["PSICOTECNICO_MAESTRO_25_CAPAS", "QUICK_DUEL"],
        "bloqueado_desde": "2025-01-27",
        "permanente": True
    },
    
    "scipy.stats.weibull_min": {
        "parametro": "velocidad_viento",
        "razon": "Perdida de precision 3.4% - mata ráfagas de viento",
        "severidad": "ALTA",
        "score_maxima_alcanzada": 0.779,  # Actual score (mejor)
        "score_candidata": 0.752,
        "tests_fallidos": ["QUICK_DUEL", "TIPO_ESPECIFICO"],
        "bloqueado_desde": "2025-01-27",
        "permanente": True
    },
    
    "scipy.interpolate.interp1d": {
        "parametro": "humedad_relativa",
        "razon": "Latencia +3.6ms - doble suavizado artificial",
        "severidad": "ALTA",
        "score_maxima_alcanzada": 0.868,  # Actual score (mejor)
        "latencia_anadida_ms": 3.6,
        "tests_fallidos": ["QUICK_DUEL", "TIPO_ESPECIFICO"],
        "bloqueado_desde": "2025-01-27",
        "permanente": True
    },
    
    "scipy.ndimage.gaussian_filter": {
        "parametro": "radiacion_solar",
        "razon": "Latencia +27.1ms inaceptable - mata variabilidad real",
        "severidad": "ALTA",
        "score_maxima_alcanzada": 0.823,  # Actual score (mejor)
        "latencia_anadida_ms": 27.1,
        "tests_fallidos": ["QUICK_DUEL", "TIPO_ESPECIFICO"],
        "bloqueado_desde": "2025-01-27",
        "permanente": True
    }
}


class FormulaBlocker:
    """Bloqueador que previene descubrimiento de formulas fallidas"""
    
    def __init__(self):
        self.blocked = 0
        self.attempted = 0
        
    def is_blocked(self, formula_ref: str, parametro: str = None) -> bool:
        """
        Verifica si una formula esta bloqueada.
        
        Args:
            formula_ref: Referencia a la formula (p.ej., "scipy.optimize.curve_fit")
            parametro: Parametro objetivo (opcional, para doble verificacion)
        
        Returns:
            True si esta bloqueada, False si es segura
        """
        self.attempted += 1
        
        # Buscar en blacklist
        for blocked_ref, blocked_data in FORMULA_BLACKLIST.items():
            if formula_ref == blocked_ref or formula_ref.endswith(blocked_ref.split('.')[-1]):
                # Double-check: si parametro especificado, verificar coincidencia
                if parametro and blocked_data.get("parametro") != parametro:
                    logger.warning(
                        f"Formula {formula_ref} esta bloqueada pero para diferente parametro. "
                        f"Bloqueada para {blocked_data.get('parametro')}, se intento para {parametro}"
                    )
                    return True  # Bloqueada de todas formas por seguridad
                
                self.blocked += 1
                logger.warning(
                    f"[BLOCKED] {formula_ref} ({blocked_data['razon']}) - "
                    f"Severidad: {blocked_data['severidad']}"
                )
                return True
        
        return False
    
    def get_razon_bloqueo(self, formula_ref: str) -> str:
        """Obtiene la razon del bloqueo"""
        for blocked_ref, blocked_data in FORMULA_BLACKLIST.items():
            if formula_ref == blocked_ref:
                return blocked_data.get("razon", "Bloqueada")
        return "Desconocida"
    
    def get_estadisticas(self) -> Dict[str, Any]:
        """Retorna estadisticas del bloqueador"""
        return {
            "intentos": self.attempted,
            "bloqueadas": self.blocked,
            "tasa_bloqueo": f"{(self.blocked/self.attempted*100 if self.attempted > 0 else 0):.1f}%",
            "total_en_lista_negra": len(FORMULA_BLACKLIST)
        }
    
    def print_blacklist(self):
        """Imprime la lista negra"""
        print("\n" + "="*80)
        print("LISTA NEGRA DE FORMULAS (PERMANENTE)")
        print("="*80 + "\n")
        
        for i, (ref, data) in enumerate(FORMULA_BLACKLIST.items(), 1):
            print(f"[{i}] {ref}")
            print(f"    Parametro: {data.get('parametro')}")
            print(f"    Razon: {data.get('razon')}")
            print(f"    Severidad: {data.get('severidad')}")
            print(f"    Bloqueado desde: {data.get('bloqueado_desde')}")
            print()


# Instancia global que se usa en el discoverer
_blocker = FormulaBlocker()


def get_blocker() -> FormulaBlocker:
    """Obtiene la instancia del bloqueador"""
    return _blocker


def should_skip_candidate(candidate_dict: Dict[str, Any]) -> bool:
    """
    Verifica si un candidato debe ser saltado.
    Se llama ANTES de intentar validar/descubrir.
    
    Args:
        candidate_dict: Dict con info del candidato
        
    Returns:
        True si debe saltarse, False si es seguro procesar
    """
    ref = candidate_dict.get("ref") or candidate_dict.get("formula_ref")
    parametro = candidate_dict.get("parametro")
    
    if not ref:
        return False
    
    return _blocker.is_blocked(ref, parametro)


def init_blocker_logging(logger_obj):
    """Inicializa logging para el bloqueador"""
    logger_obj.info(f"FORMULA_BLOCKER inicializado con {len(FORMULA_BLACKLIST)} formulas bloqueadas")
    for ref, data in FORMULA_BLACKLIST.items():
        logger_obj.debug(f"  - {ref}: {data['razon']}")


if __name__ == "__main__":
    blocker = get_blocker()
    blocker.print_blacklist()
    print("\n" + "="*80)
    print(f"Total bloqueadas: {len(FORMULA_BLACKLIST)}")
    print("="*80)
