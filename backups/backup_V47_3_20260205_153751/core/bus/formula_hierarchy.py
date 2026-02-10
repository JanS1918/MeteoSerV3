"""
═══════════════════════════════════════════════════════════════════════════════
REGISTRO DE ÉLITE V30.1 - JERARQUÍA OMNISCIENTE DE FÓRMULAS
═══════════════════════════════════════════════════════════════════════════════

Arquitectura de Grado Militar: Cada parámetro tiene una jerarquía explícita.
El Bus consulta este Registro para elegir SIEMPRE la mejor versión disponible.

FILOSOFÍA: No existe "calcular", existe "consultar qué versión de la verdad necesitas"

Fecha: 4 FEB 2026
Versión: V30.1 - Omnisciencia Real
Autor: Acorazado Argentona
Estado: PRODUCCIÓN

═══════════════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

from core.bus.parametros_canonicos import normalizar_dict_parametros_entrada

logger = logging.getLogger("formula_hierarchy")


class NivelElite(Enum):
    """Niveles de precisión absoluta del sistema"""
    ELITE = 10       # Trinity Elite (Hardy/OMM/REST2 validated)
    PROFESIONAL = 7  # NIST/IAPWS/ISO certified
    ESTÁNDAR = 5     # FAO/WMO standard
    BÁSICO = 3       # Proven approximation
    FALLBACK = 1     # Last resort


@dataclass
class Fórmula:
    """Descripción de una fórmula registrada"""
    nivel: NivelElite
    nombre_tecnico: str      # Como se publica en el bus (ej: "hardy_temperatura_rocio_c")
    nombre_legible: str      # Para logs (ej: "Hardy NIST Enhancement Factor")
    módulo: str              # Dónde está implementada
    referencia: str          # Paper/standard (ej: "NIST SR 3-73")
    precisión: str           # ±0.01°C
    velocidad: int           # ops relativas (1=lento, 10=rápido)
    rango_validez: Tuple[float, float]  # (min, max)
    requisitos_datos: List[str]  # ["temperatura", "humedad", "presion"]
    notas: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRO MAESTRO V30.1
# ═══════════════════════════════════════════════════════════════════════════════

FORMULA_HIERARCHY = {
    
    # ─────────────────────────────────────────────────────────────────────────
    # 1. PUNTO DE ROCÍO
    # ─────────────────────────────────────────────────────────────────────────
    "punto_rocio": {
        NivelElite.ELITE: Fórmula(
            nivel=NivelElite.ELITE,
            nombre_tecnico="hardy_temperatura_rocio_c",
            nombre_legible="Hardy NIST Enhancement Factor (1998)",
            módulo="core.indices.hardy_nist_psicrometria",
            referencia="Hardy et al. NIST SR3-73 (1972) + Enhancement Factor",
            precisión="±0.001°C",
            velocidad=3,
            rango_validez=(-50, 60),
            requisitos_datos=["temperatura", "humedad", "presion"],
            notas="Factor de mejora Alduchov & Eskridge 1996"
        ),
        NivelElite.ESTÁNDAR: Fórmula(
            nivel=NivelElite.ESTÁNDAR,
            nombre_tecnico="punto_rocio_wexler",
            nombre_legible="Wexler NIST Newton-Raphson Inverso",
            módulo="core.indices.environmental_indices._dew_point",
            referencia="Wexler A. (1976) J. Res. NBS 80A",
            precisión="±0.01°C",
            velocidad=2,
            rango_validez=(-50, 60),
            requisitos_datos=["temperatura", "humedad"],
            notas="Coeficientes polynomial NIST puro"
        ),
        NivelElite.FALLBACK: Fórmula(
            nivel=NivelElite.FALLBACK,
            nombre_tecnico="punto_rocio_magnus",
            nombre_legible="Magnus Simplified Approximation",
            módulo="core.indices.environmental_indices",
            referencia="Magnus (1844)",
            precisión="±0.5°C",
            velocidad=1,
            rango_validez=(-40, 50),
            requisitos_datos=["temperatura", "humedad"],
            notas="Aproximación rápida para dispositivos móviles"
        ),
    },
    
    # ─────────────────────────────────────────────────────────────────────────
    # 2. PRESIÓN DE VAPOR
    # ─────────────────────────────────────────────────────────────────────────
    "presion_vapor": {
        NivelElite.ELITE: Fórmula(
            nivel=NivelElite.ELITE,
            nombre_tecnico="hardy_e_pa",
            nombre_legible="Hardy Vapor Pressure with Enhancement Factor",
            módulo="core.indices.hardy_nist_psicrometria",
            referencia="Hardy et al. NIST (1998)",
            precisión="±0.1 Pa",
            velocidad=3,
            rango_validez=(-50, 60),
            requisitos_datos=["temperatura", "humedad", "presion"],
            notas="Computa presión vapor actual exacta con corrección de presión"
        ),
        NivelElite.PROFESIONAL: Fórmula(
            nivel=NivelElite.PROFESIONAL,
            nombre_tecnico="presion_vapor_iapws",
            nombre_legible="IAPWS-95 Formulation (Wagner & Pruß 2002)",
            módulo="core.indices.environmental_indices.saturacion_vapor_iapws_elite",
            referencia="IAPWS-IF97 (Wagner & Pruß)",
            precisión="±0.01 Pa",
            velocidad=4,
            rango_validez=(-50, 100),
            requisitos_datos=["temperatura", "presion"],
            notas="Ecuación de estado acuosa más precisa del mundo"
        ),
        NivelElite.ESTÁNDAR: Fórmula(
            nivel=NivelElite.ESTÁNDAR,
            nombre_tecnico="presion_vapor_hyland",
            nombre_legible="Hyland-Wexler NIST Polynomial",
            módulo="core.indices.environmental_indices.saturacion_vapor_hyland_wexler",
            referencia="Hyland & Wexler NIST (1983)",
            precisión="±1 Pa",
            velocidad=2,
            rango_validez=(-60, 60),
            requisitos_datos=["temperatura"],
            notas="Polinomio clásico NIST, rápido y fiable"
        ),
    },
    
    # ─────────────────────────────────────────────────────────────────────────
    # 3. SENSACIÓN TÉRMICA
    # ─────────────────────────────────────────────────────────────────────────
    "sensacion_termica": {
        NivelElite.ELITE: Fórmula(
            nivel=NivelElite.ELITE,
            nombre_tecnico="indice_utci",
            nombre_legible="Universal Thermal Climate Index (ISO 14505-2)",
            módulo="core.indices.environmental_indices",
            referencia="Fiala et al. (2012) ISO 14505-2",
            precisión="±0.1°C",
            velocidad=8,
            rango_validez=(-50, 60),
            requisitos_datos=["temperatura", "humedad", "viento", "radiacion"],
            notas="Modelo termorregulación 64-nodos, 45 científicos, 23 países"
        ),
        NivelElite.ESTÁNDAR: Fórmula(
            nivel=NivelElite.ESTÁNDAR,
            nombre_tecnico="indice_steadman_apparent_temperature",
            nombre_legible="Steadman Apparent Temperature (1984)",
            módulo="core.indices.environmental_indices",
            referencia="Steadman R.G. (1984)",
            precisión="±0.5°C",
            velocidad=2,
            rango_validez=(-40, 50),
            requisitos_datos=["temperatura", "humedad", "viento"],
            notas="Fórmula clásica, sin radiación neta"
        ),
        NivelElite.FALLBACK: Fórmula(
            nivel=NivelElite.FALLBACK,
            nombre_tecnico="wind_chill",
            nombre_legible="Wind Chill Temperature Index",
            módulo="core.indices.environmental_indices",
            referencia="Joint Action Group (2001)",
            precisión="±2°C",
            velocidad=1,
            rango_validez=(-50, 10),
            requisitos_datos=["temperatura", "viento"],
            notas="Válido solo para T<10°C"
        ),
    },
    
    # ─────────────────────────────────────────────────────────────────────────
    # 4. EVAPOTRANSPIRACIÓN
    # ─────────────────────────────────────────────────────────────────────────
    "evapotranspiracion": {
        NivelElite.ELITE: Fórmula(
            nivel=NivelElite.ELITE,
            nombre_tecnico="et0_asce_standardized",
            nombre_legible="ASCE Standardized Penman-Monteith (Standardized)",
            módulo="core.indices.environmental_indices",
            referencia="ASCE Task Committee (2005)",
            precisión="±5%",
            velocidad=7,
            rango_validez=(-10, 50),
            requisitos_datos=["temperatura", "humedad", "radiacion", "viento", "presion"],
            notas="Estándar profesional EEUU, resistencias variables"
        ),
        NivelElite.PROFESIONAL: Fórmula(
            nivel=NivelElite.PROFESIONAL,
            nombre_tecnico="et0_penman_fao56",
            nombre_legible="FAO-56 Penman-Monteith (Standard)",
            módulo="core.indices.environmental_indices.evapotranspiracion_penman_monteith",
            referencia="Allen et al. (1998) FAO56 Paper No. 56",
            precisión="±10%",
            velocidad=6,
            rango_validez=(-5, 50),
            requisitos_datos=["temperatura", "humedad", "radiacion", "viento"],
            notas="Biblia del riego, estándar FAO mundial"
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 5. DENSIDAD DEL AIRE
    # ─────────────────────────────────────────────────────────────────────────
    "densidad_aire": {
        NivelElite.ELITE: Fórmula(
            nivel=NivelElite.ELITE,
            nombre_tecnico="omm_densidad_temperatura_virtual",
            nombre_legible="OMM WMO Temperature Virtual (CIPM-2007)",
            módulo="core.indices.omm_wmo_indices",
            referencia="WMO Technical Regulations, CIPM-2007",
            precisión="±0.01%",
            velocidad=4,
            rango_validez=(-50, 60),
            requisitos_datos=["temperatura", "humedad", "presion"],
            notas="Utiliza temperatura virtual y densidad CIPM exacta"
        ),
        NivelElite.ESTÁNDAR: Fórmula(
            nivel=NivelElite.ESTÁNDAR,
            nombre_tecnico="densidad_aire_ideal",
            nombre_legible="Ideal Gas Approximation",
            módulo="core.indices.environmental_indices",
            referencia="Classical Physics",
            precisión="±0.5%",
            velocidad=1,
            rango_validez=(-40, 60),
            requisitos_datos=["temperatura", "presion"],
            notas="Fórmula simple, no incluye humedad"
        ),
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 6. RADIACIÓN SOLAR
    # ─────────────────────────────────────────────────────────────────────────
    "radiacion_solar_teorica": {
        NivelElite.ELITE: Fórmula(
            nivel=NivelElite.ELITE,
            nombre_tecnico="rest2_irradiancia_global_horizontal",
            nombre_legible="REST2 Clear-Sky Model (Gueymard 2008)",
            módulo="core.indices.rest2_gueymard",
            referencia="Gueymard C. (2008) Solar Energy 82(4)",
            precisión="±3%",
            velocidad=6,
            rango_validez=(-90, 90),
            requisitos_datos=["latitud", "longitud", "altitud", "datetime"],
            notas="Modelo transmitancia superior, validado WMO"
        ),
        NivelElite.PROFESIONAL: Fórmula(
            nivel=NivelElite.PROFESIONAL,
            nombre_tecnico="radiacion_ineichen",
            nombre_legible="Ineichen-Perez Clear-Sky Model",
            módulo="core.indices.environmental_indices",
            referencia="Ineichen & Perez (2002)",
            precisión="±5%",
            velocidad=4,
            rango_validez=(-90, 90),
            requisitos_datos=["latitud", "altitud", "datetime"],
            notas="Modelo rápido de transmitancia"
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONSULTA
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_mejor_formula(parametro: str, datos_disponibles: Dict[str, any]) -> Optional[Fórmula]:
    """
    Selecciona automáticamente la MEJOR fórmula disponible para un parámetro.
    
    Args:
        parametro: "punto_rocio", "presion_vapor", "sensacion_termica", etc.
        datos_disponibles: {"temperatura": 20.0, "humedad": 65.0, ...}
    
    Returns:
        Fórmula (mejor disponible) o None si no hay ninguna viable
    """
    datos_disponibles = normalizar_dict_parametros_entrada(datos_disponibles or {})
    jerarquia = FORMULA_HIERARCHY.get(parametro)
    if not jerarquia:
        logger.error(f"Parámetro '{parametro}' no está en Registro de Élite")
        return None
    
    # Ordenar por nivel descendente (ELITE primero)
    niveles_ordenados = sorted(jerarquia.keys(), 
                              key=lambda n: n.value, 
                              reverse=True)
    
    for nivel in niveles_ordenados:
        formula = jerarquia[nivel]
        
        # Verificar si tenemos todos los datos requeridos
        tiene_todos_datos = all(
            datos_disponibles.get(req) is not None 
            for req in formula.requisitos_datos
        )
        
        if not tiene_todos_datos:
            logger.debug(
                f"Fórmula {formula.nombre_legible} requiere "
                f"{formula.requisitos_datos}, pero solo tenemos "
                f"{list(datos_disponibles.keys())}"
            )
            continue
        
        # Verificar rango de validez (si es temperatura o similar)
        if "temperatura" in datos_disponibles:
            temp = datos_disponibles["temperatura"]
            if not (formula.rango_validez[0] <= temp <= formula.rango_validez[1]):
                logger.debug(
                    f"Temperatura {temp}°C fuera de rango para "
                    f"{formula.nombre_legible} ({formula.rango_validez})"
                )
                continue
        
        # ¡ENCONTRADA!
        logger.info(
            f"✅ Para '{parametro}': Elegida {formula.nombre_legible} "
            f"(Nivel {nivel.name})"
        )
        return formula
    
    logger.warning(
        f"⚠️ Ninguna fórmula viable para '{parametro}' con datos {datos_disponibles.keys()}"
    )
    return None


def listar_jerarquia(parametro: str) -> str:
    """Retorna lista formateada de todas las fórmulas disponibles para un parámetro"""
    jerarquia = FORMULA_HIERARCHY.get(parametro)
    if not jerarquia:
        return f"Parámetro '{parametro}' no existe en Registro"
    
    lineas = [f"\n📊 JERARQUÍA DE '{parametro.upper()}':"]
    lineas.append("=" * 80)
    
    for nivel in sorted(jerarquia.keys(), key=lambda n: n.value, reverse=True):
        formula = jerarquia[nivel]
        lineas.append(f"\n▶ NIVEL {nivel.value} ({nivel.name})")
        lineas.append(f"   Nombre: {formula.nombre_legible}")
        lineas.append(f"   Técnico: {formula.nombre_tecnico}")
        lineas.append(f"   Módulo: {formula.módulo}")
        lineas.append(f"   Precisión: {formula.precisión}")
        lineas.append(f"   Referencia: {formula.referencia}")
        lineas.append(f"   Rango: {formula.rango_validez}")
        lineas.append(f"   Requisitos: {formula.requisitos_datos}")
    
    return "\n".join(lineas)


def generar_certificado_jerarquia() -> Dict:
    """Genera certificado de todas las fórmulas registradas"""
    certificado = {
        "version": "V30.1",
        "fecha": "2026-02-04",
        "total_parametros": len(FORMULA_HIERARCHY),
        "total_formulas": sum(len(h) for h in FORMULA_HIERARCHY.values()),
        "parametros": {}
    }
    
    for parametro, jerarquia in FORMULA_HIERARCHY.items():
        certificado["parametros"][parametro] = {
            "niveles": len(jerarquia),
            "mejor": max(jerarquia.keys(), key=lambda n: n.value).name,
            "formulas": [
                f[1].nombre_legible 
                for f in sorted(jerarquia.items(), 
                              key=lambda x: x[0].value, 
                              reverse=True)
            ]
        }
    
    return certificado


if __name__ == "__main__":
    print(listar_jerarquia("punto_rocio"))
    print(listar_jerarquia("sensacion_termica"))
    print(listar_jerarquia("evapotranspiracion"))
    print("\nCERTIFICADO:")
    import json
    print(json.dumps(generar_certificado_jerarquia(), indent=2, ensure_ascii=False))
