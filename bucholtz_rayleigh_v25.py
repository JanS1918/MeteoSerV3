"""
bucholtz_rayleigh_v25.py
========================
Visibilidad molecular con cascada de 5 niveles (WMO Grade 20)
Versión: 2.6 (con Factor Z integrado)

Cascada:
1. Índice de refracción (Ciddor 2002)
2. Número de Loschmidt
3. Coeficiente Rayleigh
4. Masa de aire óptica
5. Corrección higroscópica adaptativa
"""

import math
from core.correccion_geofisica_v26 import factor_compresibilidad_virial


class BucholtzRayleighV25:
    """Visibilidad molecular con física exacta"""
    
    def __init__(self):
        # Constantes de Ciddor 2002
        self.K0 = 7.7599e-3
        self.K1 = 2.1844e-4
        self.K2 = -7.9144e-7
        
        # Constantes físicas
        self.k_B = 1.380649e-23  # J/K (Boltzmann)
        self.F_K = 1.048  # King factor para aire
        
        # Corrección higroscópica por tipo de aire
        self.gamma_higroscopica = {
            "TROPICAL": 0.86,
            "SUBTROPICAL": 0.82,
            "TEMPLADA": 0.78,
            "POLAR": 0.62,
            "ÁRTICA": 0.55
        }
    
    def indice_refraccion_ciddor(self, temperatura_c, presion_hpa, humedad_relativa):
        """
        Nivel 1: Índice de refracción (Ciddor 2002)
        
        n = 1 + (P/T)[K₀ + K₁T + K₂T²](1 - 37e/P)
        """
        T_k = temperatura_c + 273.15
        P_pa = presion_hpa * 100
        
        # Presión de vapor
        e_sat = 611.2 * math.exp(17.67 * temperatura_c / (temperatura_c + 243.5))
        e = humedad_relativa * e_sat
        
        # Ciddor
        n = 1 + (P_pa / T_k) * (self.K0 + self.K1 * T_k + self.K2 * T_k**2) * (1 - 37 * e / P_pa)
        
        return n
    
    def numero_loschmidt(self, temperatura_c, presion_hpa):
        """
        Nivel 2: Número de Loschmidt con Factor Z
        
        N_L = (P / k_B·T) × Z
        """
        T_k = temperatura_c + 273.15
        P_pa = presion_hpa * 100
        
        # Aplicar Factor Z de compresibilidad
        Z = factor_compresibilidad_virial(presion_hpa, temperatura_c)
        
        N_L = (P_pa / (self.k_B * T_k)) * Z
        
        return N_L
    
    def coeficiente_rayleigh(self, longitud_onda_nm, n, N_L):
        """
        Nivel 3: Coeficiente Rayleigh
        
        β_R = (8π³/3)(n-1)²N_L·F_K/λ⁴
        """
        lambda_m = longitud_onda_nm * 1e-9  # Convertir a metros
        
        beta_R = (8 * math.pi**3 / 3) * (n - 1)**2 * N_L * self.F_K / lambda_m**4
        
        return beta_R
    
    def masa_aire_optica(self, elevacion_solar_grados):
        """
        Nivel 4: Masa de aire óptica (Kasten-Young 1989)
        
        m = 1 / cos(θ_zenital)
        """
        if elevacion_solar_grados <= 0:
            return 38  # Horizonte
        
        zenital = 90 - elevacion_solar_grados
        zenital_rad = math.radians(zenital)
        
        m = 1 / (math.cos(zenital_rad) + 0.50572 * (96.07995 - zenital)**(-1.6364))
        
        return m
    
    def correccion_higroscopica_avanzada(self, humedad_relativa, tipo_aire):
        """
        Nivel 5: Corrección higroscópica adaptativa
        
        γ(HR) = γ₀(1 - HR)^(-1)
        """
        gamma_0 = self.gamma_higroscopica.get(tipo_aire, 0.78)
        
        if humedad_relativa >= 0.95:
            humedad_relativa = 0.95  # Límite de saturación
        
        gamma = gamma_0 * (1 - humedad_relativa)**(-1)
        
        return gamma
    
    def visibilidad_bucholtz_completa(self, temperatura_c, presion_hpa, humedad_relativa,
                                     tipo_aire="TEMPLADA", elevacion_solar=45):
        """
        Cascada completa de 5 niveles
        
        Returns:
            (visibilidad_m, visibilidad_km, clasificacion)
        """
        # Nivel 1: Índice de refracción
        n = self.indice_refraccion_ciddor(temperatura_c, presion_hpa, humedad_relativa)
        
        # Nivel 2: Número de Loschmidt
        N_L = self.numero_loschmidt(temperatura_c, presion_hpa)
        
        # Nivel 3: Coeficiente Rayleigh (λ = 550 nm, luz verde)
        beta_R = self.coeficiente_rayleigh(550, n, N_L)
        
        # Nivel 4: Masa de aire óptica
        m = self.masa_aire_optica(elevacion_solar)
        
        # Nivel 5: Corrección higroscópica
        gamma = self.correccion_higroscopica_avanzada(humedad_relativa, tipo_aire)
        
        # Visibilidad (Koschmieder)
        V = 3.912 / (beta_R * m * gamma)
        
        # Clasificación
        V_km = V / 1000
        if V_km > 50:
            clasificacion = "Excelente"
        elif V_km > 20:
            clasificacion = "Muy buena"
        elif V_km > 10:
            clasificacion = "Buena"
        elif V_km > 4:
            clasificacion = "Regular"
        elif V_km > 2:
            clasificacion = "Bruma"
        elif V_km > 1:
            clasificacion = "Niebla"
        else:
            clasificacion = "Niebla densa"
        
        return V, V_km, clasificacion
    
    def comparar_con_sin_factor_z(self, temperatura_c, presion_hpa, humedad_relativa, tipo_aire="TEMPLADA"):
        """
        Compara visibilidad con y sin Factor Z para demostrar diferencia
        
        Returns:
            dict con ambas visibilidades y la diferencia
        """
        # Con Factor Z (real)
        V_con_z, V_km_con_z, _ = self.visibilidad_bucholtz_completa(
            temperatura_c, presion_hpa, humedad_relativa, tipo_aire
        )
        
        # Sin Factor Z (aproximado, guardamos el estado original)
        # Simular sin Z modificando temporalmente la función
        N_L_sin_z = (presion_hpa * 100) / (self.k_B * (temperatura_c + 273.15))  # Z=1
        n = self.indice_refraccion_ciddor(temperatura_c, presion_hpa, humedad_relativa)
        beta_R_sin_z = self.coeficiente_rayleigh(550, n, N_L_sin_z)
        m = self.masa_aire_optica(45)
        gamma = self.correccion_higroscopica_avanzada(humedad_relativa, tipo_aire)
        V_sin_z = 3.912 / (beta_R_sin_z * m * gamma)
        V_km_sin_z = V_sin_z / 1000
        
        diferencia_m = V_con_z - V_sin_z
        diferencia_pct = (diferencia_m / V_sin_z) * 100
        
        return {
            "visibilidad_con_z_km": V_km_con_z,
            "visibilidad_sin_z_km": V_km_sin_z,
            "diferencia_m": diferencia_m,
            "diferencia_pct": diferencia_pct,
            "mejora": "CON Factor Z" if V_con_z > V_sin_z else "SIN Factor Z"
        }
