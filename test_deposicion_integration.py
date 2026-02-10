#!/usr/bin/env python3
"""
Test integrado: Verificar que deposicion_rocio_prediccion() está accesible
desde el sistema y compila correctamente.
"""

import sys
sys.path.insert(0, r'c:\Users\kioko\Desktop\MeteoSerV3')

def test_import_and_compile():
    """Verificar que se puede importar correctamente"""
    print("\n✓ TEST 1: Importación de módulos")
    
    # Importe base
    from core.indices.environmental_indices import deposicion_rocio_prediccion
    print("  ✅ deposicion_rocio_prediccion importada correctamente")
    
    # Verificar compilación de bus_expander
    import py_compile
    try:
        py_compile.compile(r'c:\Users\kioko\Desktop\MeteoSerV3\core\system\bus_expander.py', doraise=True)
        print("  ✅ bus_expander.py compila sin errores")
    except py_compile.PyCompileError as e:
        print(f"  ❌ Error compilación bus_expander: {e}")
        raise

def test_function_callable():
    """Verificar que la función es callable y devuelve dict"""
    print("\n✓ TEST 2: Función callable")
    
    from core.indices.environmental_indices import deposicion_rocio_prediccion
    
    # Test call
    resultado = deposicion_rocio_prediccion(
        temp_c=10.0,
        humedad_pct=90.0,
        velocidad_viento_ms=0.5
    )
    
    assert isinstance(resultado, dict), f"Resultado no es dict: {type(resultado)}"
    assert 'rocio_mm_hora' in resultado, "Falta 'rocio_mm_hora' en resultado"
    assert 'escarcha_si_no' in resultado, "Falta 'escarcha_si_no' en resultado"
    assert 'riesgo_nivel' in resultado, "Falta 'riesgo_nivel' en resultado"
    
    print(f"  Resultado: {resultado}")
    print("  ✅ Función devuelve dict correctamente")

def test_bus_expander_has_method():
    """Verificar que bus_expander tiene la nueva función"""
    print("\n✓ TEST 3: Método en bus_expander")
    
    # Verificar que la función existe en el código
    with open(r'c:\Users\kioko\Desktop\MeteoSerV3\core\system\bus_expander.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    assert 'async def _publish_deposicion_rocio' in code, "Función no encontrada en bus_expander.py"
    assert 'await self._publish_deposicion_rocio()' in code, "Llamada a la función no encontrada en bus_expander.py"
    
    print("  ✅ Función _publish_deposicion_rocio() está en bus_expander.py")
    print("  ✅ Llamada a await self._publish_deposicion_rocio() presente")

if __name__ == "__main__":
    print("="*60)
    print("TEST INTEGRACIÓN: Deposición Rocío")
    print("="*60)
    
    try:
        test_import_and_compile()
        test_function_callable()
        test_bus_expander_has_method()
        
        print("\n" + "="*60)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("="*60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
