#!/usr/bin/env python3
"""
Wrapper para fórmula externa: scipy.special.erf - Sensación Térmica
ID: external_sensacion_termica_scipy_sensacion_termica_0
Ref: scipy.special.erf

GANADORA del duelo para parámetro: sensacion_termica
Score: 0.00/100
Integrada: 2026-02-07T13:59:23.794429+00:00
"""

import logging

logger = logging.getLogger(__name__)


def external_sensacion_termica_scipy_sensacion_termica_0(temperatura) -> dict:
    """
    Wrapper de fórmula externa ganadora.
    
    Entrada compatible con bus de parámetros.
    Salida: dict con 'valor' y 'metadata'.
    """
    try:
        # Importar función externa
        from scipy.special import erf
        fn = erf
        
        # Ejecutar con inputs
        resultado = fn(temperatura)
        
        # Normalizar resultado
        if isinstance(resultado, dict):
            valor = resultado.get("valor") or list(resultado.values())[0]
        else:
            valor = resultado
            
        return {
            "valor": float(valor),
            "metadata": {
                "fuente": "externa",
                "wrapper": "external_sensacion_termica_scipy_sensacion_termica_0",
                "parametro": "sensacion_termica"
            }
        }
    
    except Exception as e:
        logger.error(f"Error en external_sensacion_termica_scipy_sensacion_termica_0: {e}")
        return {
            "valor": None,
            "metadata": {"error": str(e)}
        }


# === Para compatibilidad con FORMULA_HIERARCHY ===
__formula_id__ = "external_sensacion_termica_scipy_sensacion_termica_0"
__nombre__ = "scipy.special.erf - Sensación Térmica"
__parametro__ = "sensacion_termica"
__inputs__ = ['temperatura']
__score__ = 0.0
__status__ = "integrated_external"
