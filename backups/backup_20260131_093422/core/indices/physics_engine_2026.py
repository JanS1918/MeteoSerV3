"""
Physics Engine 2026 - Constantes Dinámicas de Precisión Extrema.
Sustituye 'constantes muertas' por 'funciones vivas' basadas en condiciones reales.

ARQUITECTURA DE SINTONIZACIÓN DINÁMICA:
- Todas las constantes físicas se recalculan en cada ciclo según condiciones ambientales
- Integración total con el sistema de resiliencia (fallback a valores ISA)
- Trazabilidad científica completa (cada valor sabe de dónde viene)
"""

import math
from typing import Dict, Tuple, Optional
from core.context.fallback_universal import obtener_fallback_universal, EstadoFisico


class PhysicsEngine2026:
    """
    Motor de física 2026: Constantes dinámicas que respiran con el ambiente.
    """
    
    # Constantes ISA para fallback
    LATITUD_ISA = 45.0  # grados (latitud media)
    TEMPERATURA_ISA_K = 288.15  # 15°C en Kelvin
    PRESION_ISA_PA = 101325.0  # Pa
    HUMEDAD_ISA = 0.5  # fracción
    
    def __init__(self, latitud: float = None, temperatura_k: float = None, 
                 presion_pa: float = None, humedad_fraccion: float = None):
        """
        Inicializa el motor con condiciones ambientales.
        Si faltan datos, usa valores ISA con el sistema de resiliencia.
        """
        self.fallback = obtener_fallback_universal()
        
        # Aplicar fallback a parámetros de entrada
        self.latitud, self.estado_lat = self.fallback.aplicar_fallback(
            latitud, 'latitud', 'latitud'
        )
        self.temperatura_k, self.estado_temp = self.fallback.aplicar_fallback(
            temperatura_k if temperatura_k is not None else self.TEMPERATURA_ISA_K,
            'temperatura',
            'temperatura'
        )
        self.presion_pa, self.estado_pres = self.fallback.aplicar_fallback(
            presion_pa if presion_pa is not None else self.PRESION_ISA_PA,
            'presion',
            'presion_barometrica'
        )
        self.humedad_fraccion, self.estado_hr = self.fallback.aplicar_fallback(
            humedad_fraccion if humedad_fraccion is not None else self.HUMEDAD_ISA,
            'humedad_relativa',
            'humedad'
        )
    
    def gravedad_somigliana(self) -> Tuple[float, EstadoFisico]:
        """
        Gravedad según Somigliana (WGS-84).
        Depende de la latitud geográfica real.
        
        Formula:
        g(φ) = 9.780327 * (1 + 0.0053024*sin²(φ) - 0.0000058*sin²(2φ))
        
        Returns:
            (g_ms2, estado)
        """
        lat_rad = math.radians(self.latitud)
        sin_lat = math.sin(lat_rad)
        sin_2lat = math.sin(2 * lat_rad)
        
        # Fórmula de Somigliana WGS-84
        g = 9.780327 * (1 + 0.0053024 * sin_lat**2 - 0.0000058 * sin_2lat**2)
        
        return g, self.estado_lat
    
    def viscosidad_sutherland(self) -> Tuple[float, EstadoFisico]:
        """
        Viscosidad dinámica del aire según Ley de Sutherland.
        Depende de la temperatura absoluta.
        
        Formula:
        μ = μ₀ * (T/T₀)^(3/2) * (T₀ + S)/(T + S)
        
        Donde:
        - μ₀ = 1.716e-5 Pa·s (viscosidad de referencia a 273.15 K)
        - T₀ = 273.15 K
        - S = 110.4 K (constante de Sutherland para aire)
        
        Returns:
            (mu_pas, estado)
        """
        mu_0 = 1.716e-5  # Pa·s
        T_0 = 273.15  # K
        S = 110.4  # K (constante de Sutherland para aire)
        
        T = self.temperatura_k
        
        # Ley de Sutherland
        mu = mu_0 * (T / T_0)**(3/2) * (T_0 + S) / (T + S)
        
        return mu, self.estado_temp
    
    def conductividad_mason_saxena(self) -> Tuple[float, EstadoFisico]:
        """
        Conductividad térmica del aire húmedo según Mason-Saxena.
        Depende de temperatura y humedad.
        
        Formula (simplificada para aire húmedo):
        k = k_aire_seco * (1 + 0.01 * humedad_relativa)
        
        Donde k_aire_seco sigue:
        k_seco = 0.02414 * (T/273.15)^0.9
        
        Returns:
            (k_wmk, estado)
        """
        T = self.temperatura_k
        
        # Conductividad del aire seco (Sutherland simplificado)
        k_seco = 0.02414 * (T / 273.15)**0.9
        
        # Corrección por humedad (Mason-Saxena)
        # El vapor de agua incrementa la conductividad
        k_humedo = k_seco * (1 + 0.01 * self.humedad_fraccion * 100)
        
        # Estado es el peor entre temperatura y humedad
        estado = (EstadoFisico.ESTIMADO 
                 if self.estado_temp == EstadoFisico.ESTIMADO or self.estado_hr == EstadoFisico.ESTIMADO
                 else EstadoFisico.REAL)
        
        return k_humedo, estado
    
    def factor_compresibilidad_virial(self) -> Tuple[float, EstadoFisico]:
        """
        Factor de compresibilidad Z para aire húmedo (gas real).
        Usa segundo coeficiente del Virial.
        
        Formula:
        Z = 1 + B(T)*ρ
        
        Donde B(T) es el segundo coeficiente virial (función de T).
        Para aire húmedo:
        B(T) ≈ -0.00021 + 1.2e-7*T
        
        Returns:
            (Z_adimensional, estado)
        """
        T = self.temperatura_k
        P = self.presion_pa
        
        # Densidad molar aproximada
        R = 8.314472  # J/(mol·K)
        rho_molar = P / (R * T)  # mol/m³
        
        # Segundo coeficiente del Virial para aire húmedo
        B = -0.00021 + 1.2e-7 * T  # m³/mol
        
        # Factor de compresibilidad
        Z = 1 + B * rho_molar
        
        # Estado es el peor entre temperatura y presión
        estado = (EstadoFisico.ESTIMADO 
                 if self.estado_temp == EstadoFisico.ESTIMADO or self.estado_pres == EstadoFisico.ESTIMADO
                 else EstadoFisico.REAL)
        
        return Z, estado
    
    def difusividad_schirmer(self) -> Tuple[float, EstadoFisico]:
        """
        Difusividad del vapor de agua en aire según Schirmer.
        Depende de presión y temperatura.
        
        Formula:
        D_v = D_0 * (T/T_0)^1.81 * (P_0/P)
        
        Donde:
        - D_0 = 2.16e-5 m²/s (a 273.15 K, 101325 Pa)
        - T_0 = 273.15 K
        - P_0 = 101325 Pa
        
        Returns:
            (Dv_m2s, estado)
        """
        D_0 = 2.16e-5  # m²/s
        T_0 = 273.15  # K
        P_0 = 101325.0  # Pa
        
        T = self.temperatura_k
        P = self.presion_pa
        
        # Ecuación de Schirmer
        D_v = D_0 * (T / T_0)**1.81 * (P_0 / P)
        
        # Estado es el peor entre temperatura y presión
        estado = (EstadoFisico.ESTIMADO 
                 if self.estado_temp == EstadoFisico.ESTIMADO or self.estado_pres == EstadoFisico.ESTIMADO
                 else EstadoFisico.REAL)
        
        return D_v, estado
    
    def temperatura_virtual(self, humedad_especifica: float = None) -> Tuple[float, EstadoFisico]:
        """
        Temperatura virtual para corrección de densidad por humedad.
        
        Formula:
        T_v = T * (1 + 0.61 * q)
        
        Donde q es la humedad específica (kg_agua/kg_aire).
        
        Returns:
            (Tv_K, estado)
        """
        # Si no se proporciona humedad específica, estimarla desde humedad relativa
        if humedad_especifica is None:
            # Aproximación: q ≈ 0.622 * e / P
            # donde e = presión de vapor = HR * e_sat
            # Usar una aproximación simple para e_sat
            e_sat = 611.2 * math.exp(17.67 * (self.temperatura_k - 273.15) / 
                                      (self.temperatura_k - 273.15 + 243.5))
            e = self.humedad_fraccion * e_sat
            humedad_especifica = 0.622 * e / self.presion_pa
        
        T_v = self.temperatura_k * (1 + 0.61 * humedad_especifica)
        
        estado = (EstadoFisico.ESTIMADO 
                 if self.estado_temp == EstadoFisico.ESTIMADO or self.estado_hr == EstadoFisico.ESTIMADO
                 else EstadoFisico.REAL)
        
        return T_v, estado
    
    def calor_especifico_dinamico(self) -> Tuple[float, EstadoFisico]:
        """
        Calor específico del aire húmedo (dinámico según humedad).
        
        Formula:
        c_p = c_p_seco * (1 + 0.84 * q)
        
        Donde:
        - c_p_seco = 1005 J/(kg·K) para aire seco
        - q es la humedad específica
        
        Returns:
            (cp_jkgk, estado)
        """
        c_p_seco = 1005.0  # J/(kg·K)
        
        # Estimar humedad específica
        e_sat = 611.2 * math.exp(17.67 * (self.temperatura_k - 273.15) / 
                                  (self.temperatura_k - 273.15 + 243.5))
        e = self.humedad_fraccion * e_sat
        q = 0.622 * e / self.presion_pa
        
        c_p = c_p_seco * (1 + 0.84 * q)
        
        estado = (EstadoFisico.ESTIMADO 
                 if self.estado_hr == EstadoFisico.ESTIMADO
                 else EstadoFisico.REAL)
        
        return c_p, estado
    
    def obtener_todas_constantes(self) -> Dict:
        """
        Retorna todas las constantes dinámicas en un diccionario con metadata.
        """
        g, estado_g = self.gravedad_somigliana()
        mu, estado_mu = self.viscosidad_sutherland()
        k, estado_k = self.conductividad_mason_saxena()
        Z, estado_Z = self.factor_compresibilidad_virial()
        Dv, estado_Dv = self.difusividad_schirmer()
        Tv, estado_Tv = self.temperatura_virtual()
        cp, estado_cp = self.calor_especifico_dinamico()
        
        return {
            "gravedad_somigliana": {
                "valor": g,
                "unidad": "m/s²",
                "status": estado_g.value if hasattr(estado_g, 'value') else str(estado_g),
                "latitud": self.latitud
            },
            "viscosidad_sutherland": {
                "valor": mu,
                "unidad": "Pa·s",
                "status": estado_mu.value if hasattr(estado_mu, 'value') else str(estado_mu),
                "temperatura_k": self.temperatura_k
            },
            "conductividad_mason_saxena": {
                "valor": k,
                "unidad": "W/(m·K)",
                "status": estado_k.value if hasattr(estado_k, 'value') else str(estado_k),
                "temperatura_k": self.temperatura_k,
                "humedad_fraccion": self.humedad_fraccion
            },
            "factor_compresibilidad_virial": {
                "valor": Z,
                "unidad": "adimensional",
                "status": estado_Z.value if hasattr(estado_Z, 'value') else str(estado_Z),
                "temperatura_k": self.temperatura_k,
                "presion_pa": self.presion_pa
            },
            "difusividad_schirmer": {
                "valor": Dv,
                "unidad": "m²/s",
                "status": estado_Dv.value if hasattr(estado_Dv, 'value') else str(estado_Dv),
                "temperatura_k": self.temperatura_k,
                "presion_pa": self.presion_pa
            },
            "temperatura_virtual": {
                "valor": Tv,
                "unidad": "K",
                "status": estado_Tv.value if hasattr(estado_Tv, 'value') else str(estado_Tv),
                "temperatura_k": self.temperatura_k,
                "humedad_fraccion": self.humedad_fraccion
            },
            "calor_especifico_dinamico": {
                "valor": cp,
                "unidad": "J/(kg·K)",
                "status": estado_cp.value if hasattr(estado_cp, 'value') else str(estado_cp),
                "humedad_fraccion": self.humedad_fraccion
            }
        }


# Funciones de conveniencia para acceso rápido
def obtener_constantes_dinamicas(latitud: float = None, temp_c: float = None,
                                 presion_hpa: float = None, humedad_rel: float = None) -> Dict:
    """
    Función de conveniencia para obtener todas las constantes dinámicas.
    
    Parámetros:
    -----------
    latitud : float, opcional
        Latitud en grados
    temp_c : float, opcional
        Temperatura en °C
    presion_hpa : float, opcional
        Presión en hPa
    humedad_rel : float, opcional
        Humedad relativa en %
    
    Returns:
    --------
    Dict con todas las constantes dinámicas y su metadata
    """
    temp_k = (temp_c + 273.15) if temp_c is not None else None
    presion_pa = (presion_hpa * 100.0) if presion_hpa is not None else None
    humedad_frac = (humedad_rel / 100.0) if humedad_rel is not None else None
    
    engine = PhysicsEngine2026(latitud, temp_k, presion_pa, humedad_frac)
    return engine.obtener_todas_constantes()
