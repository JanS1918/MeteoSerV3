"""
correccion_geofisica_v26.py
===========================
Módulo de Excelencia Geofísica V2.6
Incluye:
- Factor de Compresibilidad Real (Z) en densidad y presión
- Albedo Dinámico con sensor WH51
- Ángulo de Inflow de Ekman para Vector #26
"""
import math

def factor_compresibilidad_virial(P_hpa, T_c):
    """Calcula el factor Z usando ecuación virial simplificada (Nelson-Obert)"""
    # Constantes para aire seco
    T_k = T_c + 273.15
    P_atm = P_hpa / 1013.25
    B = -0.0001  # m3/mol (aprox)
    R = 0.08206  # L·atm/(mol·K)
    Z = 1 + (B * P_atm) / (R * T_k)
    return Z

def densidad_aire_real(P_hpa, T_c, Z=1.0):
    """Densidad del aire con corrección de compresibilidad"""
    R = 287.05  # J/(kg·K)
    T_k = T_c + 273.15
    P_pa = P_hpa * 100
    return (P_pa) / (Z * R * T_k)

def albedo_dinamico(humedad_suelo):
    """Albedo dinámico según humedad de suelo (WH51)"""
    # Albedo seco: 0.18, mojado: 0.08
    return 0.18 - 0.10 * min(1.0, humedad_suelo)

def angulo_inflow_ekman(velocidad_viento_ms, rugosidad_terreno):
    """Ángulo de inflow según rugosidad (Ekman)"""
    # Rugosidad típica: 0.03 (campo), 0.3 (urbano)
    # Ángulo inflow: 15° + 15° * (rugosidad/0.3)
    inflow = 15 + 15 * min(1.0, rugosidad_terreno / 0.3)
    return inflow

def corregir_vector_aproximacion(direccion_grados, inflow_ekman):
    """Corrige la dirección del vector #26 por inflow de Ekman"""
    return (direccion_grados + inflow_ekman) % 360
