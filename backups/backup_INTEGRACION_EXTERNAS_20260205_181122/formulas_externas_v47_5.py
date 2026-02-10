# -*- coding: utf-8 -*-
"""
IMPLEMENTACIÓN DE FÓRMULAS EXTERNAS - V47.5

Módulo que proporciona las 5 fórmulas externas COMO FUNCIONES DIRECTAS
para que el duelo pueda evaluarlas.
"""

import logging
import math
from typing import Optional

logger = logging.getLogger("meteoser.formulas_externas_v47_5")

# Constantes físicas
sigma_sb = 5.67e-8  # Stefan-Boltzmann [W/(m²·K⁴)]
emitancia = 0.95    # Emisividad humana típica


def utci_v4_02_fiala(
    temperatura_bulbo_seco: float,
    humedad_relativa: float,
    velocidad_viento_10m: float,
    radiacion_solar_global: float,
    **kwargs
) -> Optional[float]:
    """UTCI v4.02 - Unified Thermal Comfort Index (simplificado)"""
    try:
        T = temperatura_bulbo_seco
        RH = max(0, min(100, humedad_relativa))
        v = max(0.5, velocidad_viento_10m)
        Rad = max(0, radiacion_solar_global)
        
        # Presión de vapor (Magnus)
        e_s = 6.112 * math.exp((17.62 * T) / (243.12 + T))
        e = (RH / 100.0) * e_s
        T_d = (243.12 * math.log(e / 6.112)) / (17.62 - math.log(e / 6.112))
        
        # Efecto de radiación solar (normalizado: 0-1000 W/m² → 0-5°C)
        efecto_radiacion = (Rad / 200.0) if Rad > 0 else 0  # ~5°C a 1000 W/m²
        
        # UTCI aproximado: Temperatura + correcciones
        # Factor viento (enfría)
        factor_viento = -0.5 * math.log10(max(0.5, v))
        
        # UTCI simplificado
        utci_valor = T + efecto_radiacion + factor_viento + (0.1 * (RH - 50) / 100)
        
        return round(utci_valor, 1)
    except Exception as e:
        logger.warning(f"Error en UTCI: {e}")
        return None


def realfeel_steadman_twc(
    temperatura_bulbo_seco: float,
    humedad_relativa: float,
    velocidad_viento: float,
    radiacion_solar_global: float,
    nubosidad: float = 0.5,
    **kwargs
) -> Optional[float]:
    """RealFeel Temperature"""
    try:
        T = temperatura_bulbo_seco
        RH = max(0, min(100, humedad_relativa))
        v = max(0.1, velocidad_viento)
        N = max(0, min(1, nubosidad))
        
        Rad_eff = radiacion_solar_global * (1 - 0.5 * N)
        humedad_factor = 1 + (RH - 50) / 100
        viento_factor = 1 - 0.1 * math.log(max(1, v)) if v > 0.1 else 1
        radiacion_factor = 1 + (Rad_eff / 500) if Rad_eff > 0 else 1
        
        RF = T * humedad_factor * viento_factor * radiacion_factor
        return round(RF, 1)
    except Exception as e:
        logger.warning(f"Error en RealFeel: {e}")
        return None


def humidex_eccc_canada(
    temperatura_bulbo_seco: float,
    humedad_relativa: float,
    **kwargs
) -> Optional[float]:
    """Humidex - ECCC Canada"""
    try:
        T = temperatura_bulbo_seco
        RH = max(0, min(100, humedad_relativa))
        e = RH * 6.112 * math.exp((17.67 * T) / (T + 243.5)) / 100
        Humidex = T + (5.555 / 1000) * e * (math.exp(0.05555 * e) - 1)
        return round(Humidex, 1)
    except Exception as e:
        logger.warning(f"Error en Humidex: {e}")
        return None


def wbgt_yaglou_osha(
    temperatura_globo_negro: float,
    temperatura_bulbo_humedo: float,
    temperatura_bulbo_seco: float,
    **kwargs
) -> Optional[float]:
    """WBGT - Wet Bulb Globe Temperature"""
    try:
        T_bh = temperatura_bulbo_humedo
        T_bg = temperatura_globo_negro
        T_bs = temperatura_bulbo_seco
        WBGT = 0.7 * T_bh + 0.2 * T_bg + 0.1 * T_bs
        return round(WBGT, 1)
    except Exception as e:
        logger.warning(f"Error en WBGT: {e}")
        return None


def mrt_tg_iso7726(
    temperatura_globo_negro: float,
    velocidad_viento: float,
    emitancia_ropa: float = 0.95,
    radiacion_solar_global: float = 0,
    **kwargs
) -> Optional[float]:
    """MRT + Tg (ISO 7726:2002)"""
    try:
        T_g = temperatura_globo_negro
        v = max(0.1, velocidad_viento)
        eps = max(0.5, min(1.0, emitancia_ropa))
        Rad = radiacion_solar_global
        h_c = 10.45 - v + 10 * math.sqrt(v)
        MRT = T_g + (Rad / (eps * h_c))
        return round(MRT, 1)
    except Exception as e:
        logger.warning(f"Error en MRT: {e}")
        return None


# Mapping directo a funciones
FORMULAS_EXTERNAS_MAP = {
    "utci_v4_02_fiala": utci_v4_02_fiala,
    "realfeel_steadman_twc": realfeel_steadman_twc,
    "humidex_eccc_canada": humidex_eccc_canada,
    "wbgt_yaglou_osha": wbgt_yaglou_osha,
    "mrt_tg_iso7726": mrt_tg_iso7726,
}


def obtener_formula_externa(id_formula: str):
    """Resuelve una fórmula externa por ID"""
    return FORMULAS_EXTERNAS_MAP.get(id_formula)
