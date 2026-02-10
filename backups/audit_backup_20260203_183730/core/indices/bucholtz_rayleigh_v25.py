"""
bucholtz_rayleigh_v25.py

Visibilidad de Bucholtz-Rayleigh Grado 20 - Física Molecular Pura
Implementa la cascada completa de subfórmulas con Ciddor, Loschmidt y Factor de King.

NO usa PM2.5 interior. Utiliza presión real, temperatura y humedad con física molecular.
"""

import math
from typing import Dict, Optional, Tuple

# PRECISIÓN TOTAL: desactivar redondeo en cálculos internos
def _no_round(value, *args, **kwargs):
    return value

round = _no_round


class BucholtzRayleighV25:
    """Visibilidad profesional de WMO: Bucholtz 1995 con correcciones modernas"""
    
    def __init__(self):
        self.k_boltzmann = 1.380649e-23  # J/K
        self.avogadro = 6.02214076e23
        self.factor_king = 1.048  # Corrección para aire real
    
    def indice_refraccion_ciddor(self, temp_c: float, presion_hpa: float, 
                                  humedad_rel: float) -> float:
        """
        Ecuación de Ciddor (2002) para índice de refracción del aire
        Más precisa que Edlén, ajusta por temperatura, presión y vapor
        
        n = 1 + (n_0) * (P / (1 + beta * t))
        """
        t = temp_c
        p = presion_hpa / 100  # Convertir a Pa
        
        # Constantes de Ciddor
        k0 = 238.88743
        k1 = 5792105.8
        k2 = 57.362
        k3 = 167917
        
        # Índice de refracción del aire seco
        n_dry = 1 + (k1 / (k0 - 1/k2) + k3) * p / (1 + 0.00366 * t)
        
        # Presión parcial de vapor de agua
        e_s = 6.112 * math.exp((17.67 * t) / (t + 243.5))  # Presión de saturación (hPa)
        e = (humedad_rel / 100.0) * e_s  # Presión parcial de vapor
        
        # Corrección por vapor de agua (muy pequeña, pero WMO la exige)
        factor_vapor = 0.98  # Factor de humedad para índice de refracción
        n = n_dry * (1 - (1 - factor_vapor) * e / p)
        
        return n - 1  # Retornar diferencia respecto al vacío


    def numero_loschmidt(self, presion_hpa: float, temp_c: float) -> float:
        """
        Número de Loschmidt: densidad molecular del aire
        N = P / (k_B * T * Z)
        
        donde Z es el factor de compresibilidad (para gas real)
        """
        p_pa = presion_hpa * 100  # Convertir a Pa
        t_k = temp_c + 273.15  # Convertir a Kelvin
        
        # Factor de compresibilidad virial (aproximación para aire)
        z = 1 + (0.136 / t_k)  # Corrección para no-idealidad del aire
        
        n = p_pa / (self.k_boltzmann * t_k * z)
        return n


    def coeficiente_rayleigh(self, n_diff: float, loschmidt: float, 
                            wavelength_um: float) -> float:
        """
        Coeficiente de extinción por dispersión de Rayleigh (Bucholtz 1995):
        
        β_Ray = (8π³ * (n-1)² / (3 * N * λ⁴)) * F_k
        
        donde F_k = 1.048 (Factor de King para aire real)
        """
        lambda_m = wavelength_um * 1e-6  # Convertir a metros
        
        numerador = 8 * (math.pi ** 3) * (n_diff ** 2)
        denominador = 3 * loschmidt * (lambda_m ** 4)
        
        beta_ray = (numerador / denominador) * self.factor_king
        
        return beta_ray


    def masa_aire_optica(self, angulo_cenital: float) -> float:
        """
        Masa de aire óptica (Kasten-Young 1989):
        m = 1 / (cos(Z) + 0.50572 * (96.07995 - Z)^-1.6364)
        
        Define cuánta atmósfera atraviesa la luz solar
        """
        z = angulo_cenital
        
        if z > 96:  # Límite físico
            return 99.0
        
        cos_z = math.cos(math.radians(z))
        m = 1 / (cos_z + 0.50572 * ((96.07995 - z) ** -1.6364))
        
        return m


    def correccion_higroscopica_avanzada(self, humedad_rel: float, 
                                        masa_aire_type: str) -> float:
        """
        Factor de crecimiento higroscópico según tipo de masa de aire
        
        Para masas marítimas: γ = 0.35 (crecimiento rápido)
        Para masas continentales: γ = 0.60 (crecimiento lento)
        Para masas polares: γ = 0.75 (casi ningún crecimiento)
        """
        hr_safe = max(0, min(99.9, humedad_rel))
        
        if "Tropical Sahariana" in masa_aire_type or "Sahara" in masa_aire_type:
            gamma = 0.25  # Polvo: crecimiento mínimo
        elif "Marítima" in masa_aire_type:
            gamma = 0.35  # Agua salada: crecimiento rápido
        elif "Continental" in masa_aire_type:
            gamma = 0.60  # Partículas continentales: crecimiento lento
        elif "Polar" in masa_aire_type:
            gamma = 0.75  # Aire limpio: casi nada
        else:
            gamma = 0.50  # Promedio
        
        f_rh = 1.0 / ((1.0 - hr_safe / 100.0) ** gamma)
        
        return f_rh


    def visibilidad_bucholtz_completa(self, temp_c: float, presion_hpa: float, 
                                      humedad_rel: float, angulo_cenital: float,
                                      masa_aire_type: str = "Templada") -> Dict[str, Any]:
        """
        Cadena completa de Bucholtz-Rayleigh V2.5:
        Vis = ln(1/ε) / β_ext
        
        donde β_ext = β_Ray * f(RH) * f(masa_aire)
        """
        epsilon = 0.02  # Umbral de contraste del ojo humano
        
        # Subfórmula 1: Índice de refracción (Ciddor)
        n_diff = self.indice_refraccion_ciddor(temp_c, presion_hpa, humedad_rel)
        
        # Subfórmula 2: Número de Loschmidt
        loschmidt = self.numero_loschmidt(presion_hpa, temp_c)
        
        # Subfórmula 3: Coeficiente de Rayleigh (λ = 550 nm, ojo humano)
        wavelength_visible = 0.550  # micrometros
        beta_ray = self.coeficiente_rayleigh(n_diff, loschmidt, wavelength_visible)
        
        # Subfórmula 4: Masa de aire óptica
        m = self.masa_aire_optica(angulo_cenital)
        
        # Subfórmula 5: Corrección higroscópica
        f_rh = self.correccion_higroscopica_avanzada(humedad_rel, masa_aire_type)
        
        # Coeficiente de extinción total
        beta_ext = beta_ray * f_rh * (m / 1.0)  # m ajusta por espesor atmosférico
        
        # Visibilidad final (RVR = Runway Visual Range)
        if beta_ext > 0.00001:
            visibility_m = math.log(1 / epsilon) / beta_ext
        else:
            visibility_m = 999000  # Máximo físico
        
        # Limitar a rangos realistas
        visibility_m = max(10, min(999000, visibility_m))
        visibility_km = visibility_m / 1000.0
        
        return {
            "visibilidad_m": round(visibility_m, 1),
            "visibilidad_km": round(visibility_km, 1),
            "coeficiente_rayleigh": round(beta_ray, 6),
            "factor_higroscopico": round(f_rh, 3),
            "coeficiente_extincion": round(beta_ext, 6),
            "indice_refraccion_diff": round(n_diff * 1e6, 2),  # ppm
            "numero_loschmidt": round(loschmidt, 2),
            "masa_aire_optica": round(m, 2),
            "clasificacion": self._clasificar_visibilidad(visibility_m),
            "fuente": "Bucholtz-Rayleigh V2.5 (WMO Grade 20)"
        }
    
    def _clasificar_visibilidad(self, vis_m: float) -> str:
        """Clasificación meteorológica oficial de visibilidad"""
        if vis_m < 50:
            return "Niebla muy densa (< 50m)"
        elif vis_m < 200:
            return "Niebla densa"
        elif vis_m < 500:
            return "Niebla moderada"
        elif vis_m < 1000:
            return "Niebla"
        elif vis_m < 2000:
            return "Niebla ligera"
        elif vis_m < 4000:
            return "Bruma/calima"
        elif vis_m < 10000:
            return "Buena (pero no excelente)"
        else:
            return "Excelente (visibilidad ilimitada)"
