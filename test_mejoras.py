#!/usr/bin/env python3
"""
TEST: Validación de mejoras de rocío dinámico y balance hídrico
"""

import sys
sys.path.insert(0, 'c:\\Users\\kioko\\Desktop\\MeteoSerV3')

from core.indices.environmental_indices import (
    deposicion_rocio_prediccion,
    estres_hidrico_cultivo,
    disponibilidad_agua_cultivable
)


def test_rocio():
    """Test: Rocío dinámico por cultivo"""
    print("\n" + "="*70)
    print("TEST 1: ROCIO DINAMICO POR CULTIVO")
    print("="*70)
    
    params = {
        "temp_c": 12.0,
        "humedad_pct": 96.0,  # > 95 para generar rocío
        "velocidad_viento_ms": 0.3,
        "radiacion_neta_wm2": -50.0,
        "presion_hpa": 1013.25
    }
    
    print("\nTest con T=12°C, HR=96% (noche)")
    
    rocio_vitis = deposicion_rocio_prediccion(**params, cultivo_tipo="vitis")
    mildiu_v = rocio_vitis["plagas_riesgo"]["mildiu_pct"]
    rocio_mm_v = rocio_vitis["rocio_mm_hora"]
    
    rocio_malus = deposicion_rocio_prediccion(**params, cultivo_tipo="malus")
    mildiu_m = rocio_malus["plagas_riesgo"]["mildiu_pct"]
    rocio_mm_m = rocio_malus["rocio_mm_hora"]
    
    print(f"\nVitis (optimo T=14): rocio={rocio_mm_v:.3f}mm/h, mildiu={mildiu_v:.1f}%")
    print(f"Malus (optimo T=16): rocio={rocio_mm_m:.3f}mm/h, mildiu={mildiu_m:.1f}%")
    
    if rocio_mm_v < 0.01:
        print("ERROR: No hay rocio generado, revisar parametros")
        return False
    
    print(f"Diferencia mildiu: {abs(mildiu_v - mildiu_m):.1f}%")
    return True


def test_balance_estres():
    """Test: Balance hídrico - estrés"""
    print("\n" + "="*70)
    print("TEST 2: BALANCE HIDRICO - ESTRES")
    print("="*70)
    
    humedad = 25.0
    et0 = 4.5
    cultivo = "general"  # Usar "general" que siempre existe
    
    print(f"\nHumedad={humedad}%, ET0={et0}mm, Cultivo={cultivo}")
    
    est_arenoso = estres_hidrico_cultivo(humedad, et0, cultivo, "arenoso")
    est_franco = estres_hidrico_cultivo(humedad, et0, cultivo, "franco")
    est_arcilla = estres_hidrico_cultivo(humedad, et0, cultivo, "arcilla")
    
    f_a = est_arenoso["factor"]
    f_f = est_franco["factor"]
    f_c = est_arcilla["factor"]
    
    print(f"\nArenoso (cc=18%): factor={f_a:.3f}")
    print(f"Franco (cc=35%): factor={f_f:.3f}")
    print(f"Arcilla (cc=48%): factor={f_c:.3f}")
    
    delta_pct = abs(f_a - f_c) / max(f_a, f_c) * 100
    print(f"\nDiferencia: {delta_pct:.1f}%")
    
    if delta_pct > 8.0:
        print("VALIDADO: mejora > piso ruido")
        return True
    else:
        print("NO validado: mejora < piso ruido")
        return False


def test_balance_dias():
    """Test: Balance hídrico - días disponibles"""
    print("\n" + "="*70)
    print("TEST 3: BALANCE HIDRICO - DIAS DISPONIBLES")
    print("="*70)
    
    et0_7d = 4.5
    cultivo = "trigo"
    
    # Humedad cercana a capacidad para cada tipo
    dias_arenoso = disponibilidad_agua_cultivable(17.5, et0_7d, cultivo, "arenoso")
    dias_arcilla = disponibilidad_agua_cultivable(48.0, et0_7d, cultivo, "arcilla")
    
    agua_a = dias_arenoso['agua_total_disponible_mm']
    agua_c = dias_arcilla['agua_total_disponible_mm']
    
    print(f"\nArenoso (cc=18%): agua_total={agua_a:.1f}mm")
    print(f"Arcilla (cc=48%): agua_total={agua_c:.1f}mm")
    
    delta_pct = (agua_c - agua_a) / agua_a * 100
    print(f"\nDiferencia: {delta_pct:.1f}%")
    
    if delta_pct > 8.0:
        print("VALIDADO: mejora >> piso ruido")
        return True
    else:
        print("NO validado")
        return False


if __name__ == "__main__":
    results = []
    
    try:
        results.append(("Rocio dinamico", test_rocio()))
    except Exception as e:
        print(f"ERROR: {e}")
        results.append(("Rocio dinamico", False))
    
    try:
        results.append(("Balance estres", test_balance_estres()))
    except Exception as e:
        print(f"ERROR: {e}")
        results.append(("Balance estres", False))
    
    try:
        results.append(("Balance dias", test_balance_dias()))
    except Exception as e:
        print(f"ERROR: {e}")
        results.append(("Balance dias", False))
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    
    for name, passed in results:
        status = "PASADO" if passed else "FALLÓ"
        print(f"[{status}] {name}")
    
    all_passed = all(r[1] for r in results)
    print(f"\n{'Todas las mejoras validadas' if all_passed else 'Algunas mejoras fallaron'}")
    
    exit(0 if all_passed else 1)
