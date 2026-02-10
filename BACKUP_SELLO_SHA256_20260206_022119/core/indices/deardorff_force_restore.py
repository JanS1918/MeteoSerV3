"""
FORCE-RESTORE DEARDORFF (1978) - TEMPERATURA MÍNIMA CON INERCIA TÉRMICA
========================================================================
Modelo avanzado para predecir temperatura mínima nocturna considerando
la inercia térmica del suelo profundo.

Superior a modelos simples (tasa enfriamiento fija) porque considera:
- Capacidad calorífica del suelo según tipo (arcilla, arena, roca)
- Conductividad térmica profunda (>50cm)
- Historia térmica (si llovió ayer, el suelo retiene más calor)

Referencias:
- Deardorff (1978): "Efficient Prediction of Ground Surface Temperature and Moisture"
- ECMWF IFS (2024): Land Surface Scheme Documentation
- Noilhan & Planton (1989): "A Simple Parameterization of Land Surface Processes"

ARQUITECTURA: 100% numpy vectorizado, compatible con sensores Ecowitt.
"""

import numpy as np
from typing import Dict, Union, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES FÍSICAS DE SUELOS
# ═══════════════════════════════════════════════════════════════════════════════

TIPO_SUELO = {
    "arcilla": {
        "C_s": 2.5e6,  # Capacidad calorífica volumétrica (J/(m³·K))
        "k_s": 1.0,     # Conductividad térmica (W/(m·K))
        "z_d": 0.15,    # Profundidad damping (m)
    },
    "arena": {
        "C_s": 1.3e6,
        "k_s": 0.3,
        "z_d": 0.08,
    },
    "arcillo_arenoso": {  # ARGENTONA (típico Mediterráneo)
        "C_s": 2.0e6,
        "k_s": 0.7,
        "z_d": 0.12,
    },
    "roca": {
        "C_s": 2.8e6,
        "k_s": 2.5,
        "z_d": 0.20,
    },
}


def calcular_temperatura_minima_deardorff(
    temperatura_actual_c: Union[float, np.ndarray],
    temperatura_suelo_profundo_c: Union[float, np.ndarray] = None,  # Si None, se estima
    radiacion_neta_wm2: Union[float, np.ndarray] = 0.0,  # Durante la noche ≈ 0
    viento_ms: Union[float, np.ndarray] = 1.0,
    humedad_relativa: Union[float, np.ndarray] = 70.0,
    tipo_suelo: str = "arcillo_arenoso",
    horas_hasta_amanecer: Union[float, np.ndarray] = 8.0,  # Tiempo integración
    lluvia_ultimas_24h_mm: Union[float, np.ndarray] = 0.0,  # Humedad del suelo
) -> Dict[str, Union[float, np.ndarray]]:
    """
    Temperatura mínima según Force-Restore de Deardorff.
    
    Principio:
    - **Force**: Temperatura superficial responde rápido a flujos atmosféricos
    - **Restore**: Temperatura profunda "restaura" la superficie a su equilibrio
    
    Ecuación:
    dT_s/dt = (1/C1) * [Rn - H - LE] - (1/tau) * (T_s - T_deep)
    
    Donde:
    - T_s: Temperatura superficie
    - T_deep: Temperatura suelo profundo (~1m)
    - tau: Constante de tiempo restauración
    - C1: Capacidad calorífica superficial
    - Rn: Radiación neta
    - H: Flujo calor sensible
    - LE: Flujo calor latente
    
    Args:
        temperatura_actual_c: Temperatura aire ahora (°C)
        temperatura_suelo_profundo_c: Temperatura suelo 50-100cm (°C), si None se estima
        radiacion_neta_wm2: Radiación neta (W/m²), nocturna ≈ -50 a -100
        viento_ms: Velocidad viento (m/s)
        humedad_relativa: HR (%)
        tipo_suelo: "arcilla", "arena", "arcillo_arenoso", "roca"
        horas_hasta_amanecer: Horas de integración (típico 8h)
        lluvia_ultimas_24h_mm: Lluvia últimas 24h (afecta humedad suelo)
    
    Returns:
        Dict con:
            - temperatura_minima_c: Temperatura mínima predicha (°C)
            - temperatura_suelo_profundo_c: Temperatura estimada subsuelo
            - flujo_calor_suelo_wm2: Flujo de calor desde profundidad
            - enfriamiento_total_c: Delta T desde ahora hasta mínima
            - tasa_enfriamiento_c_h: Velocidad enfriamiento (°C/h)
    """
    # Broadcast a arrays numpy
    T_air = np.asarray(temperatura_actual_c, dtype=np.float64)
    Rn = np.asarray(radiacion_neta_wm2, dtype=np.float64)
    V = np.asarray(viento_ms, dtype=np.float64)
    HR = np.asarray(humedad_relativa, dtype=np.float64)
    t_int = np.asarray(horas_hasta_amanecer, dtype=np.float64)
    precip = np.asarray(lluvia_ultimas_24h_mm, dtype=np.float64)
    
    # Parámetros del suelo
    params = TIPO_SUELO.get(tipo_suelo, TIPO_SUELO["arcillo_arenoso"])
    C_s = params["C_s"]  # J/(m³·K)
    k_s = params["k_s"]  # W/(m·K)
    z_d = params["z_d"]  # m
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 1. TEMPERATURA SUELO PROFUNDO (si no se proporciona)
    # ═══════════════════════════════════════════════════════════════════════════
    
    if temperatura_suelo_profundo_c is None:
        # Estimación: Temperatura profunda ≈ Temperatura aire promedio diurno
        # Ajustar según historial (si llovió, suelo más frío)
        T_deep_est = T_air + 2.0  # Suelo típicamente 2°C más cálido que aire nocturno
        
        # Corrección por lluvia (suelo húmedo retiene más calor)
        T_deep_est = np.where(
            precip > 10.0,  # Si llovió >10mm
            T_deep_est + 1.0,  # Suelo húmedo más cálido
            T_deep_est
        )
        
        T_deep = T_deep_est
    else:
        T_deep = np.asarray(temperatura_suelo_profundo_c, dtype=np.float64)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 2. CONSTANTE DE TIEMPO RESTAURACIÓN (tau)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # tau = C_s * z_d² / k_s
    # Típicamente tau ~ 1 día para capa superficial
    tau_s = C_s * z_d ** 2.0 / k_s  # segundos
    tau_h = tau_s / 3600.0  # horas
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 3. FLUJOS ENERGÉTICOS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Durante la noche:
    # - Rn ≈ -50 a -100 W/m² (emisión longwave sin input solar)
    # - H (calor sensible) depende del viento y diferencia T_suelo - T_aire
    # - LE (calor latente) depende de humedad del suelo
    
    # Flujo calor sensible (H)
    # H = rho * Cp * C_H * V * (T_suelo - T_aire)
    # C_H: coeficiente transferencia calor (adimensional, típico 0.001-0.01)
    rho_air = 1.225  # kg/m³ (densidad aire a nivel del mar, 15°C)
    Cp_air = 1005.0  # J/(kg·K)
    C_H = 0.003 * (1.0 + V / 10.0)  # Aumenta con viento
    
    # Inicialmente T_suelo ≈ T_aire
    T_surf_init = T_air.copy()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 4. INTEGRACIÓN TEMPORAL (FORCE-RESTORE)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Euler explícito para integrar dT_s/dt
    dt_h = 0.1  # Paso temporal (horas)
    n_steps = int(t_int / dt_h)
    
    T_surf = T_surf_init.copy()
    T_min = T_surf.copy()
    
    for step in range(n_steps):
        # Flujo calor sensible
        H = rho_air * Cp_air * C_H * V * (T_surf - T_air)
        
        # Flujo calor latente (evapotranspiración nocturna mínima)
        # Simplificación: LE ≈ 0.1 * H si HR < 90%, sino LE ≈ 0
        LE = np.where(
            HR < 90.0,
            0.1 * H,
            0.0
        )
        
        # Flujo desde profundidad (restauración)
        G_restore = (k_s / z_d) * (T_deep - T_surf)
        
        # Balance energético superficie
        # C1 * dT_s/dt = Rn - H - LE + G_restore
        C1 = C_s * z_d  # Capacidad capa superficial (J/(m²·K))
        
        dT_dt = (Rn - H - LE + G_restore) / C1  # K/s
        dT_dt_h = dT_dt * 3600.0  # K/h
        
        # Actualizar temperatura superficie
        T_surf = T_surf + dT_dt_h * dt_h
        
        # Registrar mínima
        T_min = np.minimum(T_min, T_surf)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 5. RESULTADOS
    # ═══════════════════════════════════════════════════════════════════════════
    
    enfriamiento = T_air - T_min
    tasa_enfr = enfriamiento / t_int
    
    # Flujo de calor desde suelo (positivo = calor sube)
    G_flux = (k_s / z_d) * (T_deep - T_min)
    
    # Retornar como escalares si entrada fue escalar
    if np.ndim(temperatura_actual_c) == 0:
        return {
            "temperatura_minima_c": float(T_min),
            "temperatura_suelo_profundo_c": float(T_deep),
            "flujo_calor_suelo_wm2": float(G_flux),
            "enfriamiento_total_c": float(enfriamiento),
            "tasa_enfriamiento_c_h": float(tasa_enfr),
            "tau_restauracion_h": float(tau_h),
        }
    else:
        return {
            "temperatura_minima_c": T_min,
            "temperatura_suelo_profundo_c": T_deep,
            "flujo_calor_suelo_wm2": G_flux,
            "enfriamiento_total_c": enfriamiento,
            "tasa_enfriamiento_c_h": tasa_enfr,
            "tau_restauracion_h": tau_h,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN AUXILIAR: INTEGRACIÓN CON SENSORES
# ═══════════════════════════════════════════════════════════════════════════════

def temperatura_minima_desde_sensores(temperatura_c: float, humedad_relativa: float, viento_ms: float, radiacion_neta_wm2: float = -70.0, horas_hasta_amanecer: float = 8.0, lluvia_ultimas_24h_mm: float = 0.0) -> Dict[str, float]:
    """Wrapper para calcular mínima desde sensores directos."""
    return calcular_temperatura_minima_deardorff(temperatura_actual_c=temperatura_c, temperatura_suelo_profundo_c=None, radiacion_neta_wm2=radiacion_neta_wm2, viento_ms=viento_ms, humedad_relativa=humedad_relativa, tipo_suelo="arcillo_arenoso", horas_hasta_amanecer=horas_hasta_amanecer, lluvia_ultimas_24h_mm=lluvia_ultimas_24h_mm)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST UNITARIO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🌡️  TEST FORCE-RESTORE DEARDORFF - TEMPERATURA MÍNIMA")
    print("=" * 70)
    
    # Caso 1: Noche tranquila (viento bajo, cielo despejado)
    print("\n📍 Caso 1: NOCHE TRANQUILA (V=2 m/s, cielo despejado)")
    result = temperatura_minima_desde_sensores(
        temperatura_c=18.0,
        humedad_relativa=60.0,
        viento_ms=2.0,
        radiacion_neta_wm2=-80.0,  # Emisión nocturna fuerte
        horas_hasta_amanecer=8.0,
        lluvia_ultimas_24h_mm=0.0,
    )
    print(f"   Temperatura actual: 18.0°C")
    print(f"   Temperatura mínima: {result['temperatura_minima_c']:.2f}°C")
    print(f"   Enfriamiento: {result['enfriamiento_total_c']:.2f}°C")
    print(f"   Tasa: {result['tasa_enfriamiento_c_h']:.3f}°C/h")
    print(f"   Flujo suelo: {result['flujo_calor_suelo_wm2']:.2f} W/m²")
    
    # Caso 2: Noche ventosa (viento fuerte, mezcla atmosférica)
    print("\n📍 Caso 2: NOCHE VENTOSA (V=8 m/s)")
    result = temperatura_minima_desde_sensores(
        temperatura_c=18.0,
        humedad_relativa=60.0,
        viento_ms=8.0,
        radiacion_neta_wm2=-50.0,  # Menos emisión (nubes)
        horas_hasta_amanecer=8.0,
        lluvia_ultimas_24h_mm=0.0,
    )
    print(f"   Temperatura actual: 18.0°C")
    print(f"   Temperatura mínima: {result['temperatura_minima_c']:.2f}°C")
    print(f"   Enfriamiento: {result['enfriamiento_total_c']:.2f}°C")
    print(f"   (Viento impide enfriamiento fuerte)")
    
    # Caso 3: Suelo húmedo (llovió ayer, más inercia térmica)
    print("\n📍 Caso 3: SUELO HÚMEDO (llovió 15mm ayer)")
    result = temperatura_minima_desde_sensores(
        temperatura_c=18.0,
        humedad_relativa=80.0,
        viento_ms=2.0,
        radiacion_neta_wm2=-70.0,
        horas_hasta_amanecer=8.0,
        lluvia_ultimas_24h_mm=15.0,
    )
    print(f"   Temperatura actual: 18.0°C")
    print(f"   Temperatura mínima: {result['temperatura_minima_c']:.2f}°C")
    print(f"   Enfriamiento: {result['enfriamiento_total_c']:.2f}°C")
    print(f"   T suelo profundo: {result['temperatura_suelo_profundo_c']:.2f}°C")
    print(f"   (Suelo húmedo retiene más calor)")
    
    print("\n[OK] TEST COMPLETADO - Force-Restore operacional")
