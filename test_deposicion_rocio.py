#!/usr/bin/env python3
"""
Test: deposicion_rocio_prediccion()
Verifica: formación rocío, escarcha, riesgo plagas fungosas
"""

import sys
sys.path.insert(0, r'c:\Users\kioko\Desktop\MeteoSerV3')

from core.indices.environmental_indices import deposicion_rocio_prediccion

def test_1_noche_normal():
    """Noche sin rocío (HR 80%, viento normal)"""
    resultado = deposicion_rocio_prediccion(
        temp_c=15.0,
        humedad_pct=80.0,
        velocidad_viento_ms=1.0,
        radiacion_neta_wm2=-30.0,
        presion_hpa=1013.0
    )
    print("\n✓ TEST 1: Noche normal (sin rocío esperado)")
    print(f"  Rocío: {resultado['rocio_mm_hora']} mm/h (esperado <0.05)")
    print(f"  Riesgo: {resultado['riesgo_nivel']}")
    print(f"  Escarcha: {resultado['escarcha_si_no']}")
    
    assert resultado['rocio_mm_hora'] < 0.05, f"Rocío muy alto: {resultado['rocio_mm_hora']}"
    assert resultado['riesgo_nivel'] == "Sin riesgo", f"Riesgo incorrecto: {resultado['riesgo_nivel']}"
    print("  ✅ PASS")

def test_2_rocio_moderado():
    """Rocío moderado (HR 97%, sin viento)"""
    resultado = deposicion_rocio_prediccion(
        temp_c=12.0,
        humedad_pct=97.0,
        velocidad_viento_ms=0.3,
        radiacion_neta_wm2=-40.0,
        presion_hpa=1013.0
    )
    print("\n✓ TEST 2: Rocío moderado (HR 97%, viento bajo)")
    print(f"  Rocío: {resultado['rocio_mm_hora']} mm/h (esperado 0.05-0.15)")
    print(f"  Riesgo: {resultado['riesgo_nivel']}")
    print(f"  T rocío: {resultado['temperatura_rocio_c']}°C")
    
    assert 0.05 < resultado['rocio_mm_hora'] < 0.25, f"Rocío fuera rango: {resultado['rocio_mm_hora']}"
    assert resultado['riesgo_nivel'] in ["Débil", "Moderado"], f"Riesgo incorrecto: {resultado['riesgo_nivel']}"
    print("  ✅ PASS")

def test_3_escarcha():
    """Escarcha (T < 0°C + HR 98%)"""
    resultado = deposicion_rocio_prediccion(
        temp_c=-2.0,
        humedad_pct=98.0,
        velocidad_viento_ms=0.5,
        radiacion_neta_wm2=-50.0,
        presion_hpa=1013.0
    )
    print("\n✓ TEST 3: Escarcha (T=-2°C, HR 98%)")
    print(f"  Rocío: {resultado['rocio_mm_hora']} mm/h")
    print(f"  Escarcha: {resultado['escarcha_si_no']} (esperado True)")
    print(f"  Probabilidad: {resultado['escarcha_prob_pct']}%")
    
    assert resultado['escarcha_si_no'] == True, "Escarcha debería ser True"
    assert resultado['escarcha_prob_pct'] > 50, "Probabilidad escarcha baja"
    print("  ✅ PASS")

def test_4_riesgo_mildiu():
    """Riesgo mildiu (HR 98%, T 15°C, mucho rocío)"""
    resultado = deposicion_rocio_prediccion(
        temp_c=15.0,
        humedad_pct=98.0,
        velocidad_viento_ms=0.2,
        radiacion_neta_wm2=-50.0,
        presion_hpa=1013.0
    )
    print("\n✓ TEST 4: Riesgo mildiu alto (HR 98%, T 15°C, viento bajo)")
    print(f"  Rocío: {resultado['rocio_mm_hora']} mm/h")
    print(f"  Mildiu riesgo: {resultado['plagas_riesgo']['mildiu_pct']}%")
    print(f"  Oídio riesgo: {resultado['plagas_riesgo']['oidio_pct']}%")
    print(f"  Roya riesgo: {resultado['plagas_riesgo']['roya_pct']}%")
    
    assert resultado['plagas_riesgo']['mildiu_pct'] > 20, f"Mildiu bajo: {resultado['plagas_riesgo']['mildiu_pct']}"
    assert resultado['rocio_mm_hora'] > 0.05, "Rocío muy bajo para condiciones"
    print("  ✅ PASS")

def test_5_riesgo_bajo():
    """Riesgo de plagas bajo (T 25°C, HR normal)"""
    resultado = deposicion_rocio_prediccion(
        temp_c=25.0,
        humedad_pct=60.0,
        velocidad_viento_ms=2.0,
        radiacion_neta_wm2=50.0,
        presion_hpa=1013.0
    )
    print("\n✓ TEST 5: Riesgo bajo (T 25°C, HR 60%, radiación positiva)")
    print(f"  Rocío: {resultado['rocio_mm_hora']} mm/h (esperado 0)")
    print(f"  Mildiu: {resultado['plagas_riesgo']['mildiu_pct']}%")
    print(f"  Condiciones rocío: {resultado['condiciones']}")
    
    assert resultado['rocio_mm_hora'] == 0.0, "No debería haber rocío"
    assert resultado['plagas_riesgo']['mildiu_pct'] < 10, "Riesgo mildiu debería ser bajo"
    print("  ✅ PASS")

if __name__ == "__main__":
    print("="*60)
    print("TEST SUITE: deposicion_rocio_prediccion()")
    print("="*60)
    
    try:
        test_1_noche_normal()
        test_2_rocio_moderado()
        test_3_escarcha()
        test_4_riesgo_mildiu()
        test_5_riesgo_bajo()
        
        print("\n" + "="*60)
        print("✅ ALL 5 TESTS PASSED")
        print("="*60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
