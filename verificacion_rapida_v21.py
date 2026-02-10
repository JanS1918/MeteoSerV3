#!/usr/bin/env python3
"""
VERIFICACIÓN RÁPIDA V21: Compilación + Imports de nuevas funciones
Fecha: 9 Febrero 2026
"""

import sys
sys.path.insert(0, '/c/Users/kioko/Desktop/MeteoSerV3')

def test_imports():
    """Verifica que las 3 funciones nuevas se importan correctamente."""
    print("\n" + "="*70)
    print("TEST IMPORTS: Verificar que funciones V21 existen")
    print("="*70)
    
    try:
        from core.indices.environmental_indices import (
            balance_hidrico_diario,
            estres_hidrico_cultivo,
            disponibilidad_agua_cultivable
        )
        print("\n✅ IMPORT 1: balance_hidrico_diario")
        print(f"   Función: {balance_hidrico_diario.__name__}")
        print(f"   Docstring: {balance_hidrico_diario.__doc__[:100]}...")
        
        print("\n✅ IMPORT 2: estres_hidrico_cultivo")
        print(f"   Función: {estres_hidrico_cultivo.__name__}")
        
        print("\n✅ IMPORT 3: disponibilidad_agua_cultivable")
        print(f"   Función: {disponibilidad_agua_cultivable.__name__}")
        
        return True
    except ImportError as e:
        print(f"\n❌ ERROR IMPORT: {e}")
        return False


def test_compilacion():
    """Verifica que environmental_indices.py compila sin errores."""
    print("\n" + "="*70)
    print("TEST COMPILACIÓN: environmental_indices.py")
    print("="*70)
    
    try:
        import py_compile
        resultado = py_compile.compile(
            '/c/Users/kioko/Desktop/MeteoSerV3/core/indices/environmental_indices.py',
            doraise=True
        )
        print(f"\n✅ COMPILACIÓN EXITOSA: {resultado}")
        return True
    except py_compile.PyCompileError as e:
        print(f"\n❌ ERROR COMPILACIÓN: {e}")
        return False


def test_execution():
    """Ejecuta un caso simple de cada función."""
    print("\n" + "="*70)
    print("TEST EJECUCIÓN: Funciones V21")
    print("="*70)
    
    try:
        from core.indices.environmental_indices import (
            balance_hidrico_diario,
            estres_hidrico_cultivo,
            disponibilidad_agua_cultivable
        )
        
        # Test 1: balance_hidrico_diario
        print("\n[1] balance_hidrico_diario(lluvia=10mm, et0=5mm, escor=1mm, infiltr=1mm)")
        result = balance_hidrico_diario(10.0, 5.0, 1.0, 1.0)
        print(f"    Result: {result}")
        print(f"    Delta: {result['delta_h']:.2f} mm")
        assert result['delta_h'] == 3.0, "Delta debe ser 3.0"
        print("    ✅ PASS")
        
        # Test 2: estres_hidrico_cultivo
        print("\n[2] estres_hidrico_cultivo(humedad=25%, et0=6mm, cultivo='general')")
        result = estres_hidrico_cultivo(25.0, 6.0, "general")
        print(f"    Factor: {result['factor']:.3f}")
        print(f"    Nivel: {result['nivel']}")
        assert 0 <= result['factor'] <= 1.0, "Factor debe estar entre 0-1"
        print("    ✅ PASS")
        
        # Test 3: disponibilidad_agua_cultivable
        print("\n[3] disponibilidad_agua_cultivable(humedad=25%, et0_prom=5mm, cultivo='general')")
        result = disponibilidad_agua_cultivable(25.0, 5.0, "general")
        print(f"    Días disponibles: {result['dias_hasta_sequia']:.1f}")
        print(f"    Urgencia: {result['urgencia']}")
        assert result['dias_hasta_sequia'] > 0, "Días debe ser positivo"
        print("    ✅ PASS")
        
        return True
    except Exception as e:
        print(f"\n❌ ERROR EJECUCIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "█"*70)
    print(" VERIFICACIÓN RÁPIDA SISTEMA HÍDRICO V21")
    print("█"*70)
    
    results = []
    
    # Test 1: Imports
    success = test_imports()
    results.append(("Imports", success))
    
    if not success:
        print("\n⚠️  No se pueden hacer más tests sin imports")
        return False
    
    # Test 2: Compilación
    success = test_compilacion()
    results.append(("Compilación", success))
    
    # Test 3: Ejecución
    success = test_execution()
    results.append(("Ejecución", success))
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN:")
    print("="*70)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:30} {status}")
    
    total_pass = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nResultado: {total_pass}/{total} tests pasaron")
    
    if total_pass == total:
        print("\n✅ V21 LISTO PARA FUNCIONAR")
        return True
    else:
        print("\n❌ V21 TIENE PROBLEMAS")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
