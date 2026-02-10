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
# REGISTRO MAESTRO V30.1 - AUTOREPARADO 2026-02-05
# Eliminados: 14 registros FANTASMA (funciones no existían en código)
# Agregados: 2 funciones OCULTAS que ahora se registran
# ═══════════════════════════════════════════════════════════════════════════════

FORMULA_HIERARCHY = {
    
    # ─────────────────────────────────────────────────────────────────────────
    # SENSACIÓN TÉRMICA - REPARADA
    # (Eliminada: wind_chill - función no existe)
    # (Agregada: indice_wbgt - función oculta)
    # (Agregada: utci_v2_blazejczyk - función oculta)
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
        NivelElite.PROFESIONAL: Fórmula(
            nivel=NivelElite.PROFESIONAL,
            nombre_tecnico="indice_wbgt",
            nombre_legible="Wet Bulb Globe Temperature (OSHA)",
            módulo="core.indices.environmental_indices",
            referencia="Yaglou & Minard (1957) - NOAA/US Military",
            precisión="±1°C",
            velocidad=5,
            rango_validez=(-10, 55),
            requisitos_datos=["temperatura", "humedad", "radiacion", "viento"],
            notas="Estándar OSHA para ambientes ocupacionales [PREVIAMENTE OCULTA - AUTOREPARADA]"
        ),
        NivelElite.BÁSICO: Fórmula(
            nivel=NivelElite.BÁSICO,
            nombre_tecnico="utci_v2_blazejczyk",
            nombre_legible="UTCI v2 (Blazejczyk 2013) - Extremos térmicos",
            módulo="core.indices.utci_v2_blazejczyk",
            referencia="Blazejczyk et al. (2013)",
            precisión="±0.2°C",
            velocidad=9,
            rango_validez=(-40, 50),
            requisitos_datos=["temperatura", "humedad", "viento", "radiacion"],
            notas="Mejoras para zonas extremas [PREVIAMENTE OCULTA - AUTOREPARADA]"
        ),
    },
    
    # RADIACIÓN SOLAR - REPARADA
    # (Eliminada: rest2_irradiancia_global_horizontal - módulo incorrecto)
    # (Eliminada: radiacion_ineichen - no funciona con SRTM)
    # ─────────────────────────────────────────────────────────────────────────
    "radiacion_solar": {
        NivelElite.ELITE: Fórmula(
            nivel=NivelElite.ELITE,
            nombre_tecnico="calcular_radiacion_extraterrestre_rest2",
            nombre_legible="Gueymard REST2 + SRTM Ocaso Topográfico",
            módulo="core.indices.rest2_gueymard_radiacion",
            referencia="Gueymard (2008) REST2 + SRTM topografía",
            precisión="±1.5%",
            velocidad=7,
            rango_validez=(0, 1200),
            requisitos_datos=["datetime", "latitud", "longitud", "altitud", "uso_horario"],
            notas="Radiación extraterrestre con filtrado por ocaso topográfico"
        ),
    },
    
    # NOTA: Otros parámetros (punto_rocio, presion_vapor, evapotranspiracion, 
    # densidad_aire, radiacion_solar_teorica) ELIMINADOS porque sus registros 
    # eran FANTASMA (funciones no existían en código).
    # Se restaurarán cuando haya implementaciones verificadas en código.
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
            f"[OK] Para '{parametro}': Elegida {formula.nombre_legible} "
            f"(Nivel {nivel.name})"
        )
        return formula
    
    logger.warning(
        f"[WARNING] Ninguna fórmula viable para '{parametro}' con datos {datos_disponibles.keys()}"
    )
    return None


def listar_jerarquia(parametro: str) -> str:
    """Retorna lista formateada de todas las fórmulas disponibles para un parámetro"""
    jerarquia = FORMULA_HIERARCHY.get(parametro)
    if not jerarquia:
        return f"Parámetro '{parametro}' no existe en Registro"
    
    lineas = [f"\n[STATS] JERARQUÍA DE '{parametro.upper()}':"]
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
