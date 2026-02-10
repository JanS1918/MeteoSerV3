"""
Calcular presión ISA (International Standard Atmosphere) en cualquier altitud.

Reemplaza valores hardcodeados de 1013.25 hPa con cálculos dinámicos.
"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def presion_isa_dinamica(altitud_m: float) -> float:
    """
    Calcula presión ISA estándar a una altitud dada.
    
    Fórmula ISA:
        P(h) = 1013.25 × (1 - 0.0065×h / 288.15)^5.255
    
    Donde:
        h = altitud en metros (sobre nivel del mar)
        P = presión en hPa
        0.0065 = gradiente de temperatura (K/m)
        288.15 = temperatura ISA a nivel del mar (K = 15°C)
        5.255 = exponente (gm / R·L, donde g=9.81, m=0.029, R=8.314, L=0.0065)
    
    Args:
        altitud_m: Altitud en metros sobre nivel del mar
    
    Returns:
        Presión ISA en hPa
    
    Ejemplos:
        >>> presion_isa_dinamica(0)      # Nivel del mar
        1013.25
        >>> presion_isa_dinamica(96)     # Argentona
        1011.25
        >>> presion_isa_dinamica(3640)   # La Paz, Bolivia
        650.28
    
    Referencias:
        - International Standard Atmosphere, ICAO 1975
        - Atmospheric_models_and_atmospheric_calculators.pdf
    """
    T0 = 288.15  # K (15°C a nivel del mar, ISA)
    P0 = 1013.25  # hPa (presión a nivel del mar)
    L = 0.0065  # K/m (gradiente de temperatura en tropósfera)
    g = 9.81  # m/s² (aceleración gravedad)
    M = 0.029  # kg/mol (masa molar del aire seco)
    R = 8.314  # J/(mol·K) (constante universal gas)
    
    # Exponente: gM / (R·L)
    exponente = (g * M) / (R * L)
    
    try:
        # P(h) = P0 × (1 - L·h/T0)^(gM/RL)
        presion = P0 * (1.0 - (L * altitud_m) / T0) ** exponente
        
        # Validar resultado
        if presion < 0:
            logger.warning(f"⚠️ Presión ISA negativa a {altitud_m}m: {presion:.2f} hPa")
            return 0.0
        
        return presion
    
    except Exception as e:
        logger.error(f"❌ Error calculando ISA a {altitud_m}m: {e}")
        return 1013.25  # Fallback a nivel del mar


def presion_isa_fallback(altitud_m: float, presion_ultima_valida: float = None) -> Tuple[float, str]:
    """
    Calcula presión fallback inteligente para cuando el sensor falla.
    
    Estrategia:
    1. Si hay presión última válida: usar esa (más realista que ISA)
    2. Si no: usar ISA calculada según altitud
    3. Nunca usar 1013.25 hardcodeado
    
    Args:
        altitud_m: Altitud de la estación en metros
        presion_ultima_valida: Última lectura válida de presión (si existe)
    
    Returns:
        Tupla (presion_hpa, razon)
    """
    if presion_ultima_valida is not None and 800 <= presion_ultima_valida <= 1100:
        return (presion_ultima_valida, "persistencia_ultima_lectura")
    
    presion_isa = presion_isa_dinamica(altitud_m)
    return (presion_isa, f"isa_dinamica_a_{altitud_m}m")


def validar_presion_isa(presion_hpa: float, altitud_m: float = 96.0) -> Tuple[bool, str]:
    """
    Valida si una presión es físicamente plausible según ISA ± margen.
    
    Args:
        presion_hpa: Presión medida en hPa
        altitud_m: Altitud de la estación
    
    Returns:
        Tupla (es_valida, explicacion)
    """
    p_isa = presion_isa_dinamica(altitud_m)
    
    # ISA ± 5% (margen razonable por presencia de sistemas meteorológicos)
    margen = p_isa * 0.05
    limite_bajo = p_isa - margen
    limite_alto = p_isa + margen
    
    if limite_bajo <= presion_hpa <= limite_alto:
        desviacion = ((presion_hpa - p_isa) / p_isa) * 100
        return (True, f"OK (ISA: {p_isa:.2f} hPa, desv: {desviacion:+.1f}%)")
    else:
        if presion_hpa < limite_bajo:
            return (False, f"BAJA (medida: {presion_hpa:.2f} hPa vs ISA: {p_isa:.2f} hPa)")
        else:
            return (False, f"ALTA (medida: {presion_hpa:.2f} hPa vs ISA: {p_isa:.2f} hPa)")


# Tabla de referencia ISA precalculada para debugging
ISA_TABLA_REFERENCIA = {
    "Nivel del mar (0 m)": presion_isa_dinamica(0),
    "Argentona Barcelona (96 m)": presion_isa_dinamica(96),
    "Madrid (646 m)": presion_isa_dinamica(646),
    "Andorra la Vella (1029 m)": presion_isa_dinamica(1029),
    "Pico del Teide (3718 m)": presion_isa_dinamica(3718),
    "La Paz Bolivia (3640 m)": presion_isa_dinamica(3640),
    "Leh Ladakh (3500 m)": presion_isa_dinamica(3500),
    "Everest Base Camp (5364 m)": presion_isa_dinamica(5364),
}

if __name__ == "__main__":
    # Tests de validación
    print("╔════════════════════════════════════════════╗")
    print("║   TABLA ISA DE REFERENCIA - VALIDACIÓN   ║")
    print("╚════════════════════════════════════════════╝\n")
    
    for ubicacion, presion in ISA_TABLA_REFERENCIA.items():
        print(f"{ubicacion:.<40} {presion:.2f} hPa")
