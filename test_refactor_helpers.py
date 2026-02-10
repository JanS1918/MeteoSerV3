#!/usr/bin/env python3
"""
Test: Validación de helpers de conversión robustos (get_float, clamp_percent, etc)
"""

import sys
sys.path.insert(0, 'c:\\Users\\kioko\\Desktop\\MeteoSerV3')

from core.system.bus_expander import get_float, get_int, clamp_percent, clamp_unit


def test_get_float():
    """Test conversión float robusto"""
    print("\n=== TEST: get_float() ===")
    
    # Caso 1: Dict con valor válido
    assert get_float({"temp": 25.5}, "temp") == 25.5
    print("[OK] Dict con valor float")
    
    # Caso 2: String convertible
    assert get_float({"temp": "25.5"}, "temp") == 25.5
    print("[OK] String convertible a float")
    
    # Caso 3: Default cuando falta
    assert get_float({}, "temp", default=20.0) == 20.0
    print("[OK] Default cuando falta clave")
    
    # Caso 4: Clamping
    assert get_float({"val": 150}, "val", min_val=0, max_val=100) == 100.0
    print("[OK] Clamping a rango")
    
    # Caso 5: Conversión fallida
    assert get_float({"bad": "xyz"}, "bad", default=-1) == -1.0
    print("[OK] Conversión fallida retorna default")
    
    # Caso 6: None value
    assert get_float({"val": None}, "val", default=42.0) == 42.0
    print("[OK] None value retorna default")
    
    # Caso 7: Objeto con atributos
    class Obj:
        temp = 18.5
    
    assert get_float(Obj(), "temp") == 18.5
    print("[OK] Extrae de objeto (atributo)")


def test_clamp_percent():
    """Test clamping a 0-100%"""
    print("\n=== TEST: clamp_percent() ===")
    
    assert clamp_percent(50.0) == 50.0
    print("[OK] Valor en rango")
    
    assert clamp_percent(-10.0) == 0.0
    print("[OK] Clamp inferior")
    
    assert clamp_percent(150.0) == 100.0
    print("[OK] Clamp superior")
    
    assert clamp_percent(100.5) == 100.0
    print("[OK] Clamp flotante")


def test_clamp_unit():
    """Test clamping a [0-1]"""
    print("\n=== TEST: clamp_unit() ===")
    
    assert clamp_unit(0.5) == 0.5
    print("[OK] Valor en rango")
    
    assert clamp_unit(1.5) == 1.0
    print("[OK] Clamp superior")
    
    assert clamp_unit(-0.5) == 0.0
    print("[OK] Clamp inferior")


def test_refactor_real_world():
    """Test casos del mundo real extraídos de bus_expander"""
    print("\n=== TEST: Casos del mundo real ===")
    
    # Caso 1: Resultado CAPE típico
    cape_result = {"cape_jkg": 1500.5, "lcl_m": 2500}
    cape = get_float(cape_result, "cape_jkg", default=0.0)
    assert cape == 1500.5
    print(f"[OK] CAPE={cape}")
    
    # Caso 2: Probabilidad Sundqvist
    sundq = {"prob_lluvia_pct": "85.3"}
    prob = clamp_percent(get_float(sundq, "prob_lluvia_pct", default=0.0))
    assert 84 < prob <= 86  # Permitir pequeño error float
    print(f"[OK] Prob lluvia={prob}%")
    
    # Caso 3: Severidad tormenta (puede venir como None)
    sev = {"riesgo_tormenta_severa_pct": None}
    risk = clamp_percent(get_float(sev, "riesgo_tormenta_severa_pct", default=0.0))
    assert risk == 0.0
    print(f"[OK] Riesgo tormenta={risk}% (None → default)")
    
    # Caso 4: Índice UV
    uv_result = {"valor": "7.2", "estimado": True}
    uv = get_float(uv_result, "valor", default=0.0)
    assert 7.1 < uv < 7.3
    print(f"[OK] UV index={uv}")


if __name__ == "__main__":
    try:
        test_get_float()
        test_clamp_percent()
        test_clamp_unit()
        test_refactor_real_world()
        
        print("\n" + "="*70)
        print("TODOS LOS TESTS PASARON")
        print("="*70)
        print("\nRefactorización validada:")
        print("✅ get_float() convierte robustamente")
        print("✅ clamp_percent() limita 0-100%")
        print("✅ clamp_unit() limita 0-1")
        print("✅ Casos reales funcionan correctamente")
        
        exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
