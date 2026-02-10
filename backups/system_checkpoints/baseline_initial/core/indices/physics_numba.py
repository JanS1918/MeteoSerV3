"""
PHYSICS ENGINE COMPILADO - Versión Numba (10-100x más rápido)
===============================================================
Reescribe cálculos físicos con compilación JIT de Numba.
Compatible con versión original, drop-in replacement.

Uso:
    from core.indices.physics_numba import PhysicsEngineNumba
    
    engine = PhysicsEngineNumba()
    constantes = engine.calcular_constantes(T=25, P=1013.25, HR=60)
    # → 10-100x más rápido que versión Python pura
"""

import numpy as np
from typing import Dict, Optional

try:
    import numba
    from numba import jit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    print("⚠️  Numba no disponible. Instalar con: pip install numba")
    # Define dummy decorator si no está
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


# ============================================================================
# CONSTANTES FÍSICAS
# ============================================================================
G = 9.80665  # Gravedad m/s²
R_SPECIFIC_DRY = 287.05  # J/(kg·K) - Constante gas seco
R_SPECIFIC_VAPOR = 461.5  # J/(kg·K) - Constante vapor agua
CP_AIR = 1005.0  # J/(kg·K) - Calor específico aire
CP_VAPOR = 1846.0  # J/(kg·K) - Calor específico vapor
L_VAPORIZATION = 2.5e6  # J/kg - Calor latente vaporización
EPSILON = 0.622  # Relación masas moleculares agua/aire
STEFAN_BOLTZMANN = 5.670374419e-8  # W/(m²·K⁴)
KARMAN = 0.41  # Constante de von Kármán


# ============================================================================
# FUNCIONES COMPILADAS CON NUMBA
# ============================================================================

@jit(nopython=True)
def presion_vapor_saturacion_numba(T_celsius: float) -> float:
    """Presión vapor saturación (Magnus-Tetens) [hPa]"""
    return 6.1094 * np.exp(17.625 * T_celsius / (T_celsius + 243.04))


@jit(nopython=True)
def presion_vapor_actual_numba(T_celsius: float, HR_pct: float) -> float:
    """Presión vapor actual [hPa]"""
    es = presion_vapor_saturacion_numba(T_celsius)
    return (HR_pct / 100.0) * es


@jit(nopython=True)
def densidad_aire_numba(T_celsius: float, P_hpa: float, HR_pct: float) -> float:
    """Densidad del aire [kg/m³]"""
    T_kelvin = T_celsius + 273.15
    e = presion_vapor_actual_numba(T_celsius, HR_pct)
    
    # Ley gases ideales con humedad
    rho = (P_hpa * 100.0 - 0.3783 * e * 100.0) / (R_SPECIFIC_DRY * T_kelvin)
    return rho


@jit(nopython=True)
def viscosidad_aire_numba(T_celsius: float) -> float:
    """Viscosidad dinámica aire (Sutherland) [Pa·s]"""
    T_kelvin = T_celsius + 273.15
    T0 = 273.15
    mu0 = 1.716e-5
    S = 110.4
    
    mu = mu0 * (T_kelvin / T0)**1.5 * (T0 + S) / (T_kelvin + S)
    return mu


@jit(nopython=True)
def conductividad_termica_aire_numba(T_celsius: float) -> float:
    """Conductividad térmica aire [W/(m·K)]"""
    T_kelvin = T_celsius + 273.15
    # Aproximación lineal
    return 0.024 + 7.0e-5 * (T_kelvin - 273.15)


@jit(nopython=True)
def velocidad_sonido_numba(T_celsius: float) -> float:
    """Velocidad del sonido en aire [m/s]"""
    T_kelvin = T_celsius + 273.15
    gamma = 1.4  # Razón calores específicos
    return np.sqrt(gamma * R_SPECIFIC_DRY * T_kelvin)


@jit(nopython=True)
def numero_reynolds_numba(velocidad: float, longitud: float, viscosidad: float, densidad: float) -> float:
    """Número de Reynolds (adimensional)"""
    if viscosidad == 0:
        return 0.0
    return densidad * velocidad * longitud / viscosidad


@jit(nopython=True)
def numero_prandtl_numba(cp: float, mu: float, k: float) -> float:
    """Número de Prandtl (adimensional)"""
    if k == 0:
        return 0.0
    return cp * mu / k


@jit(nopython=True)
def escala_logaritmica_viento_numba(z: float, z0: float, u_star: float) -> float:
    """Perfil logarítmico de viento [m/s]"""
    if z <= z0 or u_star == 0:
        return 0.0
    return (u_star / KARMAN) * np.log(z / z0)


@jit(nopython=True)
def temperatura_punto_rocio_numba(T_celsius: float, HR_pct: float) -> float:
    """Temperatura punto de rocío [°C]"""
    a = 17.27
    b = 237.7
    
    alpha = (a * T_celsius) / (b + T_celsius) + np.log(HR_pct / 100.0)
    Td = (b * alpha) / (a - alpha)
    
    return Td


# ============================================================================
# VECTORIZACIÓN (para procesamiento en batch)
# ============================================================================

@jit(nopython=True)
def densidad_aire_vectorizado(T_array, P_array, HR_array):
    """
    Versión vectorizada: calcula densidad para arrays enteros
    
    Args:
        T_array: array de temperaturas [°C]
        P_array: array de presiones [hPa]
        HR_array: array de humedades [%]
    
    Returns:
        array de densidades [kg/m³]
    """
    n = len(T_array)
    densidades = np.zeros(n)
    
    for i in range(n):
        densidades[i] = densidad_aire_numba(T_array[i], P_array[i], HR_array[i])
    
    return densidades


@jit(nopython=True)
def velocidad_sonido_vectorizado(T_array):
    """Velocidad sonido vectorizada"""
    n = len(T_array)
    velocidades = np.zeros(n)
    
    for i in range(n):
        velocidades[i] = velocidad_sonido_numba(T_array[i])
    
    return velocidades


# ============================================================================
# CLASE PRINCIPAL
# ============================================================================

class PhysicsEngineNumba:
    """
    Motor de física compilado con Numba
    Drop-in replacement de PhysicsEngine2026
    """
    
    def __init__(self):
        """Inicializa motor compilado"""
        if not NUMBA_AVAILABLE:
            print("⚠️  Numba no disponible, funcionará en modo Python puro (más lento)")
    
    def calcular_constantes(self, T: float, P: float, HR: float) -> Dict[str, float]:
        """
        Calcula todas las constantes físicas
        
        Args:
            T: Temperatura [°C]
            P: Presión [hPa]
            HR: Humedad relativa [%]
        
        Returns:
            Diccionario con constantes
        """
        # Conversión
        T_k = T + 273.15
        P_pa = P * 100.0
        
        # Básicas
        es = presion_vapor_saturacion_numba(T)
        e = presion_vapor_actual_numba(T, HR)
        rho = densidad_aire_numba(T, P, HR)
        mu = viscosidad_aire_numba(T)
        k_air = conductividad_termica_aire_numba(T)
        c_sound = velocidad_sonido_numba(T)
        
        # Derivadas
        nu = mu / rho if rho > 0 else 0  # Viscosidad cinemática
        Pr = numero_prandtl_numba(CP_AIR, mu, k_air)
        Td = temperatura_punto_rocio_numba(T, HR)
        
        return {
            'temperatura_k': T_k,
            'presion_pa': P_pa,
            'presion_vapor_sat_hpa': es,
            'presion_vapor_act_hpa': e,
            'densidad_aire_kg_m3': rho,
            'viscosidad_din_pa_s': mu,
            'viscosidad_cin_m2_s': nu,
            'conductividad_termica_w_mk': k_air,
            'velocidad_sonido_ms': c_sound,
            'numero_prandtl': Pr,
            'punto_rocio_c': Td,
            'gravedad_ms2': G,
            'cp_aire_j_kgk': CP_AIR,
            'calor_latente_j_kg': L_VAPORIZATION,
            'constante_karman': KARMAN
        }
    
    def calcular_batch(self, T_array: np.ndarray, P_array: np.ndarray, HR_array: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Versión VECTORIZADA: calcula para arrays enteros
        
        Args:
            T_array: Temperaturas [°C]
            P_array: Presiones [hPa]
            HR_array: Humedades [%]
        
        Returns:
            Dict con arrays de resultados
        """
        densidades = densidad_aire_vectorizado(T_array, P_array, HR_array)
        velocidades_sonido = velocidad_sonido_vectorizado(T_array)
        
        return {
            'densidad_aire_kg_m3': densidades,
            'velocidad_sonido_ms': velocidades_sonido
        }


if __name__ == "__main__":
    import time
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        PHYSICS ENGINE NUMBA - Compilado (10-100x faster)      ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    if NUMBA_AVAILABLE:
        # Benchmark simple
        engine = PhysicsEngineNumba()
        
        print("\n📊 BENCHMARK: PhysicsEngineNumba")
        print("   " + "-"*60)
        
        # Scalar
        inicio = time.perf_counter()
        for _ in range(10000):
            engine.calcular_constantes(25.0, 1013.25, 60.0)
        tiempo_scalar = time.perf_counter() - inicio
        
        print(f"   10.000 cálculos escalares: {tiempo_scalar*1000:.2f} ms")
        print(f"   Cada uno: {tiempo_scalar/10000*1e6:.2f} microsegundos")
        
        # Vectorizado
        T_batch = np.random.uniform(15, 35, 10000)
        P_batch = np.random.uniform(980, 1040, 10000)
        HR_batch = np.random.uniform(30, 90, 10000)
        
        inicio = time.perf_counter()
        engine.calcular_batch(T_batch, P_batch, HR_batch)
        tiempo_batch = time.perf_counter() - inicio
        
        print(f"\n   10.000 cálculos vectorizados: {tiempo_batch*1000:.2f} ms")
        print(f"   Cada uno: {tiempo_batch/10000*1e6:.2f} microsegundos")
        print(f"\n   ✅ Aceleración: {tiempo_scalar/tiempo_batch:.1f}x más rápido")
    else:
        print("\n❌ Numba no disponible. Instalarlo con: pip install numba")
