# -*- coding: utf-8 -*-
"""
temperatura_radiante_dinamica.py

Cálculo de Temperatura Radiante Media (MRT - Mean Radiant Temperature)
para confort térmico humano REALISTA.

PROBLEMA RESUELTO:
- PMV Fanger asumía tr = ta (temperatura radiante = temperatura aire)
- ERROR: Al sol directo, tr puede ser 10-20°C mayor que ta
- IMPACTO: PMV subestima sensación térmica en 0.5-1.5 puntos

SOLUCIÓN:
Calcular tr real considerando:
1. Radiación solar directa/difusa (W/m²)
2. Radiación IR del cielo (modelo Swinbank)
3. Radiación reflejada del suelo/paredes (albedo)
4. Geometría de exposición humana (Fanger body factor)

Referencias:
- ISO 7726:1998. Ergonomics of thermal environment - Instruments for measuring
- Fanger, P.O. (1972). Thermal Comfort. McGraw-Hill.
- Höppe, P. (1992). "A new procedure to determine the mean radiant temperature
  outdoors". Wetter und Leben, 44, 147-151.
- Thorsson et al. (2007). "Different methods for estimating the mean radiant
  temperature in an outdoor urban setting". Int J Climatology, 27, 1983-1993.

FASE FINAL V28.0 - Febrero 2026
Implementación: Post-Unificación de Hierro, Mejora Crítica #1
"""

import math
from typing import Dict, Optional


# Constantes físicas
STEFAN_BOLTZMANN = 5.67e-8  # W/(m²·K⁴)
ABSORPTIVIDAD_PIEL = 0.7  # Absorptividad piel humana (Fanger 1972)
EMISIVIDAD_PIEL = 0.95  # Emisividad piel humana (ISO 7726)


def calcular_temperatura_cielo_swinbank(
    temp_aire_c: float,
    nubosidad_pct: float = 0.0
) -> float:
    """
    Temperatura efectiva del cielo según modelo Swinbank (1963).
    
    El cielo irradia como cuerpo negro a temperatura efectiva menor que el aire:
    - Cielo despejado: T_cielo ≈ T_aire - 10 a 20°C
    - Cielo nublado: T_cielo ≈ T_aire - 2 a 5°C (nubes actúan como manta térmica)
    
    Args:
        temp_aire_c: Temperatura del aire (°C)
        nubosidad_pct: Nubosidad (0-100%)
    
    Returns:
        Temperatura efectiva del cielo (°C)
    
    Referencias:
        - Swinbank, W.C. (1963). "Long-wave radiation from clear skies".
          Quarterly Journal of the Royal Meteorological Society, 89(381), 339-348.
        - Martin & Berdahl (1984). "Characteristics of infrared sky radiation
          in the United States". Solar Energy, 33(3-4), 321-336.
    """
    T_aire_k = temp_aire_c + 273.15
    
    # Modelo Swinbank para cielo despejado
    # T_cielo = 0.0552 * T_aire^1.5 (empírico, válido para latitudes medias)
    T_cielo_despejado_k = 0.0552 * (T_aire_k ** 1.5)
    
    # Corrección por nubosidad (Martin & Berdahl 1984)
    # Nubes aumentan radiación IR del cielo → T_cielo sube
    fraccion_nubes = nubosidad_pct / 100.0
    
    # Con nubes totales, T_cielo → T_aire (nubes bajas a temp ambiente)
    T_cielo_nublado_k = T_aire_k - 5.0  # Aproximación nubes a ~5°C debajo aire
    
    # Interpolación lineal según fracción nubosa
    T_cielo_k = (1 - fraccion_nubes) * T_cielo_despejado_k + fraccion_nubes * T_cielo_nublado_k
    
    T_cielo_c = T_cielo_k - 273.15
    
    return T_cielo_c


def calcular_temperatura_radiante_media(
    temp_aire_c: float,
    radiacion_solar_w_m2: float,
    nubosidad_pct: float = 0.0,
    albedo_entorno: float = 0.2,
    velocidad_viento_ms: float = 1.0,
    elevacion_solar_deg: float = 45.0,
    temp_suelo_c: Optional[float] = None
) -> Dict[str, float]:
    """
    Calcula la Temperatura Radiante Media (MRT) para confort térmico humano.
    
    MRT es la temperatura uniforme de un recinto negro que daría la misma
    transferencia de calor radiante que el entorno real (Fanger 1972).
    
    Para exterior:
    MRT = f(T_sol, T_cielo, T_suelo, geometría_exposición)
    
    Args:
        temp_aire_c: Temperatura del aire (°C)
        radiacion_solar_w_m2: Radiación solar global horizontal (W/m²)
        nubosidad_pct: Nubosidad (0-100%)
        albedo_entorno: Albedo superficies circundantes (0-1, típico 0.15-0.25)
        velocidad_viento_ms: Velocidad del viento (m/s, afecta convección forzada)
        elevacion_solar_deg: Elevación solar (grados, afecta geometría exposición)
        temp_suelo_c: Temperatura del suelo (°C, opcional, si None = temp_aire)
    
    Returns:
        Dict con:
        - mrt: Temperatura radiante media (°C)
        - t_cielo: Temperatura efectiva del cielo (°C)
        - t_suelo: Temperatura del suelo (°C)
        - q_solar: Flujo radiante solar absorbido (W/m²)
        - q_cielo: Flujo radiante del cielo (W/m²)
        - q_suelo: Flujo radiante del suelo (W/m²)
        - q_total: Flujo radiante total (W/m²)
        - delta_mrt_aire: Diferencia MRT - T_aire (°C)
    
    Referencias:
        - Höppe, P. (1992). Procedure for MRT outdoors
        - Thorsson et al. (2007). MRT estimation methods comparison
        - ISO 7726:1998. Thermal environment instruments
    """
    T_aire_k = temp_aire_c + 273.15
    
    # 1. TEMPERATURA DEL CIELO (Swinbank 1963 + corrección nubes)
    # ============================================================
    T_cielo_c = calcular_temperatura_cielo_swinbank(temp_aire_c, nubosidad_pct)
    T_cielo_k = T_cielo_c + 273.15
    
    # 2. TEMPERATURA DEL SUELO
    # ============================================================
    if temp_suelo_c is None:
        # Si no se mide, asumir ≈ T_aire durante el día
        # (en realidad, suelo está 2-5°C más caliente al sol, pero es conservador)
        temp_suelo_c = temp_aire_c
    
    T_suelo_k = temp_suelo_c + 273.15
    
    # 3. RADIACIÓN SOLAR ABSORBIDA
    # ============================================================
    # Factor de proyección de área humana según elevación solar (Höppe 1992)
    # Persona de pie: área proyectada varía con ángulo solar
    # - Sol en cenit (90°): área proyectada = área cabeza/hombros (~0.08 m²)
    # - Sol en horizonte (0°): área proyectada = área frontal completa (~0.7 m²)
    # - Promedio cuerpo humano: 1.8 m² superficie total (DuBois formula)
    
    # Factor de forma solar-persona (Höppe 1992, simplificado)
    if elevacion_solar_deg < 5:
        # Sol muy bajo, casi toda la radiación es lateral
        f_p_solar = 0.35  # ~35% área expuesta
    elif elevacion_solar_deg > 80:
        # Sol casi en cenit, solo cabeza/hombros
        f_p_solar = 0.06  # ~6% área expuesta
    else:
        # Interpolación no lineal (modelo Höppe)
        # f_p = 0.308 * cos(θ_zenital)  para persona de pie
        theta_zenital = 90.0 - elevacion_solar_deg
        f_p_solar = 0.308 * math.cos(math.radians(theta_zenital))
    
    # Radiación solar absorbida por el cuerpo
    # Q_solar = α * I * f_p
    # α = absorptividad piel/ropa (~0.7 para piel, 0.6-0.8 ropa clara)
    Q_solar = ABSORPTIVIDAD_PIEL * radiacion_solar_w_m2 * f_p_solar
    
    # 4. RADIACIÓN DEL CIELO (IR térmico)
    # ============================================================
    # Factor de forma cielo-persona (mitad superior hemisferio visual)
    # Para persona de pie en espacio abierto: f_p_cielo ≈ 0.5
    f_p_cielo = 0.5
    
    # Flujo radiante del cielo (Stefan-Boltzmann)
    Q_cielo = EMISIVIDAD_PIEL * STEFAN_BOLTZMANN * (T_cielo_k ** 4) * f_p_cielo
    
    # 5. RADIACIÓN DEL SUELO (IR térmico + reflejada)
    # ============================================================
    # Factor de forma suelo-persona (mitad inferior hemisferio visual)
    f_p_suelo = 0.5
    
    # Radiación térmica del suelo
    Q_suelo_termica = EMISIVIDAD_PIEL * STEFAN_BOLTZMANN * (T_suelo_k ** 4) * f_p_suelo
    
    # Radiación solar reflejada por el suelo (albedo)
    Q_suelo_reflejada = ABSORPTIVIDAD_PIEL * radiacion_solar_w_m2 * albedo_entorno * f_p_suelo
    
    Q_suelo = Q_suelo_termica + Q_suelo_reflejada
    
    # 6. FLUJO RADIANTE TOTAL ABSORBIDO
    # ============================================================
    Q_total = Q_solar + Q_cielo + Q_suelo
    
    # 7. TEMPERATURA RADIANTE MEDIA EQUIVALENTE
    # ============================================================
    # Resolver: Q_total = ε·σ·(T_mrt⁴ - T_aire⁴)
    # Simplificación: Q_total ≈ ε·σ·T_mrt⁴ (asumiendo Q_emitida_cuerpo se cancela)
    
    # Aproximación lineal (válida para ΔT < 30°C):
    # T_mrt ≈ T_aire + Q_total / (4·ε·σ·T_aire³)
    
    # Aproximación exacta (resolver T_mrt⁴):
    # Q_neto = Q_total - ε·σ·T_aire⁴  (asumiendo cuerpo irradia a T_aire)
    Q_neto = Q_total - EMISIVIDAD_PIEL * STEFAN_BOLTZMANN * (T_aire_k ** 4)
    
    # T_mrt⁴ = T_aire⁴ + Q_neto / (ε·σ)
    T_mrt_k4 = (T_aire_k ** 4) + (Q_neto / (EMISIVIDAD_PIEL * STEFAN_BOLTZMANN))
    
    # Asegurar no negativo (puede pasar si Q_total muy bajo)
    if T_mrt_k4 < 0:
        T_mrt_k = T_aire_k  # Fallback
    else:
        T_mrt_k = T_mrt_k4 ** 0.25
    
    T_mrt_c = T_mrt_k - 273.15
    
    # Diferencia MRT - T_aire (indicador de carga radiante)
    delta_mrt = T_mrt_c - temp_aire_c
    
    return {
        "mrt": round(T_mrt_c, 2),
        "t_cielo": round(T_cielo_c, 2),
        "t_suelo": round(temp_suelo_c, 2),
        "q_solar": round(Q_solar, 1),
        "q_cielo": round(Q_cielo, 1),
        "q_suelo": round(Q_suelo, 1),
        "q_total": round(Q_total, 1),
        "delta_mrt_aire": round(delta_mrt, 2),
        "elevacion_solar": round(elevacion_solar_deg, 1),
        "f_p_solar": round(f_p_solar, 3)
    }


def interpretar_delta_mrt(delta_mrt_c: float) -> str:
    """
    Interpreta la diferencia MRT - T_aire.
    
    Args:
        delta_mrt_c: Diferencia MRT - T_aire (°C)
    
    Returns:
        Interpretación textual de la carga radiante
    """
    if delta_mrt_c < -5:
        return "Enfriamiento radiativo intenso (cielo despejado nocturno)"
    elif delta_mrt_c < 0:
        return "Enfriamiento radiativo leve"
    elif delta_mrt_c < 2:
        return "Carga radiante mínima (nublado/sombra)"
    elif delta_mrt_c < 5:
        return "Carga radiante moderada (sol parcial)"
    elif delta_mrt_c < 10:
        return "Carga radiante alta (sol directo)"
    elif delta_mrt_c < 15:
        return "Carga radiante muy alta (sol intenso)"
    else:
        return "Carga radiante extrema (sol + reflexión intensa)"


# ══════════════════════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Caso 1: Argentona, día soleado de verano
    print("="*78)
    print("CASO 1: Argentona, día soleado verano (30°C, sol directo)")
    print("="*78)
    
    resultado1 = calcular_temperatura_radiante_media(
        temp_aire_c=30.0,
        radiacion_solar_w_m2=800.0,  # Sol fuerte
        nubosidad_pct=10.0,
        albedo_entorno=0.2,
        elevacion_solar_deg=60.0
    )
    
    for k, v in resultado1.items():
        print(f"  {k}: {v}")
    
    print(f"\n  → {interpretar_delta_mrt(resultado1['delta_mrt_aire'])}")
    print(f"  → Sensación térmica: {resultado1['mrt']:.1f}°C (vs aire {30.0}°C)")
    print(f"  → Impacto PMV: +{resultado1['delta_mrt_aire']/10:.1f} puntos estimado")
    
    # Caso 2: Argentona, noche despejada invierno
    print("\n" + "="*78)
    print("CASO 2: Argentona, noche despejada invierno (5°C, sin sol)")
    print("="*78)
    
    resultado2 = calcular_temperatura_radiante_media(
        temp_aire_c=5.0,
        radiacion_solar_w_m2=0.0,  # Noche
        nubosidad_pct=0.0,  # Despejado
        albedo_entorno=0.15,
        elevacion_solar_deg=0.0
    )
    
    for k, v in resultado2.items():
        print(f"  {k}: {v}")
    
    print(f"\n  → {interpretar_delta_mrt(resultado2['delta_mrt_aire'])}")
    print(f"  → Sensación térmica: {resultado2['mrt']:.1f}°C (vs aire {5.0}°C)")
    print(f"  → Enfriamiento radiativo: {abs(resultado2['delta_mrt_aire']):.1f}°C")
    
    # Caso 3: Argentona, día nublado (neutralidad radiativa)
    print("\n" + "="*78)
    print("CASO 3: Argentona, día nublado (20°C, sin sol directo)")
    print("="*78)
    
    resultado3 = calcular_temperatura_radiante_media(
        temp_aire_c=20.0,
        radiacion_solar_w_m2=150.0,  # Solo radiación difusa
        nubosidad_pct=90.0,  # Muy nublado
        albedo_entorno=0.2,
        elevacion_solar_deg=40.0
    )
    
    for k, v in resultado3.items():
        print(f"  {k}: {v}")
    
    print(f"\n  → {interpretar_delta_mrt(resultado3['delta_mrt_aire'])}")
    print(f"  → Sensación térmica: {resultado3['mrt']:.1f}°C (vs aire {20.0}°C)")
    print(f"  → Nubes actúan como manta térmica (MRT ≈ T_aire)")
