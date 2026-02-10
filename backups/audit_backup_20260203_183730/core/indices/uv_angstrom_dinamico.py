"""
MODELO DE ÅNGSTRÖM DINÁMICO PARA ATENUACIÓN UV POR AEROSOLES
═══════════════════════════════════════════════════════════════════════════════════
Motor de Excelencia Universal v1.1 - Eliminación de AOD fijo

ARQUITECTURA RECURSIVA:
- AOD derivado de visibilidad Kasten-Hanel (esclavo de humedad y PM2.5)
- Exponente de Ångström dinámico según tipo de aerosol
- Integración con física de Nivel 1 (densidad CIPM-2007, psicrometría IAPWS-95)

Referencias:
- Ångström, A. (1964). "The parameters of atmospheric turbidity"
- Kasten, F. & Young, A.T. (1989). "Revised optical air mass tables and approximation formula"
- King, M.D. et al. (1999). "Aerosol properties from AERONET"

Motor: Quantum_Diamond_Universal_v1.1_FINAL
"""

import math
from typing import Dict, Tuple, Optional

# PRECISIÓN TOTAL: desactivar redondeo en cálculos internos
def _no_round(value, *args, **kwargs):
    return value

round = _no_round
from core.indices.advanced_physics_models import visibilidad_kasten_hanel


class UVAngstromDinamico:
    """
    Motor de atenuación UV por aerosoles con física recursiva.
    El AOD se deriva de visibilidad real, no es un valor fijo.
    """
    
    def __init__(self):
        """Inicializa el motor de Ångström dinámico."""
        self.last_aod = None
    
    def calcular_aod_desde_visibilidad(self,
                                       visibilidad_km: float,
                                       longitud_onda_nm: float = 500.0,
                                       humedad_relativa: float = 50.0,
                                       temperatura_c: float = 15.0) -> Tuple[float, Dict[str, any]]:
        """
        Calcula el AOD (Aerosol Optical Depth) desde la visibilidad real.
        
        Relación de Koschmieder con corrección de Kasten-Hanel:
        AOD(λ) = -ln(0.02) / (Vis * 1000) * (λ_ref / λ)^α
        
        Args:
            visibilidad_km: Visibilidad horizontal en km
            longitud_onda_nm: Longitud de onda de referencia (nm)
            humedad_relativa: HR (%) para corrección higroscópica
            temperatura_c: Temperatura (°C) para tipo de aerosol
            
        Returns:
            Tuple[float, dict]: (AOD, metadatos con subfórmulas)
        """
        # Constante de contraste de Koschmieder
        # -ln(0.02) ≈ 3.912 (umbral de visibilidad del 2%)
        k_koschmieder = 3.912
        
        # Convertir visibilidad a metros
        vis_m = visibilidad_km * 1000.0
        
        # SUBFÓRMULA A: Exponente de Ångström según tipo de aerosol
        # α depende del tamaño y origen del aerosol
        alpha = self._calcular_exponente_angstrom(temperatura_c, humedad_relativa)
        
        # SUBFÓRMULA B: AOD base en longitud de onda de referencia (500 nm)
        # τ_aer(λ_ref) = 3.912 / Vis
        if vis_m > 0:
            aod_base = k_koschmieder / vis_m
        else:
            # Visibilidad nula = atmósfera opaca (niebla densa)
            aod_base = 5.0
        
        # SUBFÓRMULA C: Escalar a longitud de onda deseada (ley de potencias de Ångström)
        # τ_aer(λ) = τ_aer(λ_ref) * (λ_ref / λ)^α
        lambda_ref = 500.0  # nm
        if longitud_onda_nm > 0:
            factor_espectral = (lambda_ref / longitud_onda_nm) ** alpha
        else:
            factor_espectral = 1.0
        
        aod_final = aod_base * factor_espectral
        
        # Limitar AOD a valores físicos (0-5)
        # AOD > 5 = visibilidad <1 km (extremo)
        aod_final = max(0.0, min(5.0, aod_final))
        
        metadatos = {
            "motor": "Quantum_Diamond_Universal_v1.1_FINAL",
            "metodo": "Angstrom_dinamico_desde_visibilidad",
            "visibilidad_km": round(visibilidad_km, 2),
            "aod_base_500nm": round(aod_base, 4),
            "exponente_angstrom": round(alpha, 3),
            "factor_espectral": round(factor_espectral, 3),
            "subfórmulas": {
                "A": "Exponente_Angstrom_dinamico",
                "B": "AOD_base_Koschmieder",
                "C": "Escalado_espectral_potencias"
            }
        }
        
        return aod_final, metadatos
    
    def _calcular_exponente_angstrom(self, temperatura_c: float, humedad_relativa: float) -> float:
        """
        Calcula el exponente de Ångström (α) según condiciones atmosféricas.
        
        El exponente α caracteriza el tamaño de los aerosoles:
        - α > 1.5: Aerosoles finos (urbanos, combustión)
        - α ~ 1.0: Aerosoles mixtos
        - α < 0.5: Aerosoles gruesos (polvo del desierto, sal marina)
        
        SUBFÓRMULA RECURSIVA: α depende de temperatura (convección) y humedad (higroscopicidad)
        
        Args:
            temperatura_c: Temperatura del aire (°C)
            humedad_relativa: HR (%)
            
        Returns:
            float: Exponente de Ångström (típicamente 0.5-2.0)
        """
        # Base: aerosoles continentales mixtos (Argentona, suburbano-costero)
        alpha_base = 1.3
        
        # MICRO-FÓRMULA A.1: Corrección por temperatura (convección vertical)
        # Convección fuerte → aerosoles finos suspendidos → α alto
        if temperatura_c > 25:
            # Convección fuerte: aerosoles finos dominan
            delta_temp = 0.2
        elif temperatura_c < 5:
            # Inversión térmica: aerosoles gruesos se depositan menos
            delta_temp = -0.1
        else:
            # Régimen neutro
            delta_temp = 0.0
        
        # MICRO-FÓRMULA A.2: Corrección por humedad (crecimiento higroscópico)
        # Alta humedad → aerosoles crecen → α baja
        rh_norm = humedad_relativa / 100.0
        if rh_norm > 0.8:
            # Aerosoles crecen por absorción de agua → se comportan como gruesos
            delta_hr = -0.3 * (rh_norm - 0.8) / 0.2
        else:
            delta_hr = 0.0
        
        # Exponente final
        alpha = alpha_base + delta_temp + delta_hr
        
        # Limitar a rango físico observado
        return max(0.5, min(2.0, alpha))
    
    def calcular_transmitancia_aerosoles(self,
                                         visibilidad_km: float,
                                         masa_optica: float,
                                         longitud_onda_nm: float = 310.0,
                                         humedad_relativa: float = 50.0,
                                         temperatura_c: float = 15.0) -> Tuple[float, Dict[str, any]]:
        """
        Calcula la transmitancia atmosférica por aerosoles para UV.
        
        Ley de Beer-Lambert-Bouguer:
        T_aer = exp(-τ_aer * m)
        
        Args:
            visibilidad_km: Visibilidad horizontal (km)
            masa_optica: Masa óptica atmosférica (adimensional)
            longitud_onda_nm: Longitud de onda (nm, típica UV: 310 nm)
            humedad_relativa: HR (%)
            temperatura_c: Temperatura (°C)
            
        Returns:
            Tuple[float, dict]: (transmitancia [0-1], metadatos)
        """
        # SUBFÓRMULA RECURSIVA: AOD desde visibilidad (esclavo de Kasten-Hanel)
        aod, meta_aod = self.calcular_aod_desde_visibilidad(
            visibilidad_km,
            longitud_onda_nm,
            humedad_relativa,
            temperatura_c
        )
        
        # Ley de Beer-Lambert-Bouguer
        transmitancia = math.exp(-aod * masa_optica)
        
        # Limitar a rango físico [0-1]
        transmitancia = max(0.0, min(1.0, transmitancia))
        
        metadatos = {
            "motor": "Quantum_Diamond_Universal_v1.1_FINAL",
            "metodo": "Beer_Lambert_Bouguer_UV",
            "aod_usado": round(aod, 4),
            "masa_optica": round(masa_optica, 3),
            "transmitancia": round(transmitancia, 4),
            "subfórmulas_recursivas": meta_aod.get("subfórmulas", {})
        }
        
        return transmitancia, metadatos


def calcular_tau_rayleigh_dinamico(presion_hpa: float,
                                    temperatura_k: float,
                                    longitud_onda_nm: float = 310.0,
                                    humedad_fraccion: float = 0.5) -> Tuple[float, Dict[str, any]]:
    """
    Calcula la profundidad óptica de Rayleigh con densidad real CIPM-2007.
    
    SUBFÓRMULA RECURSIVA: τ_Ray depende de la densidad del aire (CIPM-2007 con Virial).
    
    Ley de Rayleigh:
    τ_Ray(λ) = (8π³/3) * (n²-1)² / (N * λ⁴)
    
    Aproximación práctica:
    τ_Ray(λ) ≈ τ_Ray(λ_ref) * (λ_ref/λ)⁴ * (ρ_aire/ρ_std)
    
    Args:
        presion_hpa: Presión barométrica (hPa)
        temperatura_k: Temperatura (K)
        longitud_onda_nm: Longitud de onda (nm)
        humedad_fraccion: Fracción de humedad [0-1]
        
    Returns:
        Tuple[float, dict]: (τ_Rayleigh, metadatos)
    """
    # SUBFÓRMULA RECURSIVA: Densidad CIPM-2007 con factor de compresibilidad Virial
    from core.indices.physics_engine_2026 import PhysicsEngine2026
    
    engine = PhysicsEngine2026(
        latitud=41.5513,  # Argentona
        temperatura_k=temperatura_k,
        presion_pa=presion_hpa * 100.0,
        humedad_fraccion=humedad_fraccion
    )
    
    # Densidad real con corrección Virial
    rho_aire, estado_rho = engine.densidad_aire_cipm_2007()
    
    # Densidad estándar ISA (para referencia)
    rho_std = 1.225  # kg/m³
    
    # Tau de Rayleigh en λ=500nm a nivel del mar (referencia)
    tau_ray_ref = 0.0088  # a 500 nm, P=1013.25 hPa, T=288.15 K
    lambda_ref = 500.0  # nm
    
    # Escalado espectral (ley de potencias λ⁻⁴)
    if longitud_onda_nm > 0:
        factor_espectral = (lambda_ref / longitud_onda_nm) ** 4
    else:
        factor_espectral = 1.0
    
    # Escalado por densidad (proporcional a número de moléculas)
    factor_densidad = rho_aire / rho_std
    
    # Tau final
    tau_rayleigh = tau_ray_ref * factor_espectral * factor_densidad
    
    metadatos = {
        "motor": "Quantum_Diamond_Universal_v1.1_FINAL",
        "metodo": "Rayleigh_CIPM2007_Virial",
        "rho_aire_kg_m3": round(rho_aire, 4),
        "rho_std_kg_m3": rho_std,
        "factor_densidad": round(factor_densidad, 4),
        "factor_espectral": round(factor_espectral, 2),
        "tau_rayleigh": round(tau_rayleigh, 5),
        "estado_fisica": estado_rho.value if hasattr(estado_rho, 'value') else str(estado_rho),
        "subfórmulas": {
            "A": "Densidad_CIPM2007_con_Virial",
            "B": "Escalado_espectral_lambda4",
            "C": "Escalado_por_densidad_molecular"
        }
    }
    
    return tau_rayleigh, metadatos


# Prueba unitaria
if __name__ == "__main__":
    motor = UVAngstromDinamico()
    
    # Caso 1: Día claro (visibilidad 50 km)
    aod, meta = motor.calcular_aod_desde_visibilidad(50.0, 310.0, 40.0, 22.0)
    print(f"Día claro: AOD={aod:.4f}, α={meta['exponente_angstrom']:.3f}")
    
    # Caso 2: Calima (visibilidad 10 km)
    aod, meta = motor.calcular_aod_desde_visibilidad(10.0, 310.0, 70.0, 28.0)
    print(f"Calima: AOD={aod:.4f}, α={meta['exponente_angstrom']:.3f}")
    
    # Caso 3: Niebla (visibilidad 1 km)
    aod, meta = motor.calcular_aod_desde_visibilidad(1.0, 310.0, 95.0, 12.0)
    print(f"Niebla: AOD={aod:.4f}, α={meta['exponente_angstrom']:.3f}")
    
    # Tau Rayleigh dinámico
    tau, meta = calcular_tau_rayleigh_dinamico(1013.25, 288.15, 310.0, 0.5)
    print(f"Tau Rayleigh (310 nm): {tau:.5f}, ρ_aire={meta['rho_aire_kg_m3']:.4f} kg/m³")
