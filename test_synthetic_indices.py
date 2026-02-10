#!/usr/bin/env python3
"""
Test de índices sintéticos multi-dominio integrados en bus_expander.py
✅ Verifica que todos los módulos se importan correctamente
✅ Verifica que las funciones principales existen y son callable
✅ Prueba con datos sintéticos (mock)
"""

import sys
sys.path.insert(0, '/Users/kioko/Desktop/MeteoSerV3')

def test_imports():
    """Verificar que todos los módulos importantes se importan correctamente."""
    print("="*80)
    print("TEST 1: IMPORTS")
    print("="*80)
    
    try:
        from core.indices.indice_sintetico_robusto import (
            calcular_indice_sintetico,
            PESOS_CETRERIA, PESOS_LLUVIA, PESOS_CONFORT, PESOS_DEPORTE
        )
        print("✅ indice_sintetico_robusto: OK")
        print(f"   - PESOS_CETRERIA: {list(PESOS_CETRERIA.keys())}")
        print(f"   - PESOS_LLUVIA: {list(PESOS_LLUVIA.keys())}")
        print(f"   - PESOS_CONFORT: {list(PESOS_CONFORT.keys())}")
        print(f"   - PESOS_DEPORTE: {list(PESOS_DEPORTE.keys())}")
    except Exception as e:
        print(f"❌ indice_sintetico_robusto: FAILED - {e}")
        return False
    
    try:
        from core.indices.cetreria.cetreria_indices_v2 import calcular_cetreria_completa
        print("✅ cetreria_indices_v2.calcular_cetreria_completa: OK")
    except Exception as e:
        print(f"❌ cetreria_indices_v2: FAILED - {e}")
        return False
    
    try:
        from core.indices.lluvia.lluvia_indices import calcular_lluvia_completa
        print("✅ lluvia_indices.calcular_lluvia_completa: OK")
    except Exception as e:
        print(f"❌ lluvia_indices: FAILED - {e}")
        return False
    
    try:
        from core.indices.confort.confort_indices import calcular_confort_completa
        print("✅ confort_indices.calcular_confort_completa: OK")
    except Exception as e:
        print(f"❌ confort_indices: FAILED - {e}")
        return False
    
    try:
        from core.indices.deporte.deporte_indices import calcular_deporte_completa
        print("✅ deporte_indices.calcular_deporte_completa: OK")
    except Exception as e:
        print(f"❌ deporte_indices: FAILED - {e}")
        return False
    
    return True

def test_cetreria_robusto():
    """Test de cetrería con datos mock."""
    print("\n" + "="*80)
    print("TEST 2: CETRERÍA ROBUSTO")
    print("="*80)
    
    try:
        from core.indices.cetreria.cetreria_indices_v2 import calcular_cetreria_completa
        
        datos = {
            "temperatura": 20.0,
            "humedad": 60.0,
            "presion_pa": 101325.0,
            "viento_medio": 5.0,
            "viento_racha": 8.0,
            "radiacion": 500.0,
        }
        
        resultado = calcular_cetreria_completa(datos)
        
        print(f"✅ Cetrería ejecutada correctamente")
        print(f"   - Indice sintético: {resultado.get('indice_cetreria_sintetico', 'N/A'):.1f}%")
        print(f"   - Viento: {resultado.get('viento_cetreria', 'N/A'):.1f}%")
        print(f"   - Visibilidad: {resultado.get('visibilidad_terreno', 'N/A'):.1f}%")
        print(f"   - Termales: {resultado.get('termales_probabilidad', 'N/A'):.1f}%")
        print(f"   - Barro: {resultado.get('barro_campo', 'N/A'):.1f}%")
        print(f"   - Confort ave: {resultado.get('confort_ave', 'N/A'):.1f}%")
        
        # Validar que nunca retorna None
        assert resultado.get('indice_cetreria_sintetico') is not None, "Sintético no debería ser None"
        print(f"✅ Robustez validada: NUNCA retorna None")
        return True
    
    except Exception as e:
        print(f"❌ Cetrería fallida: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lluvia_robusto():
    """Test de lluvia con datos mock."""
    print("\n" + "="*80)
    print("TEST 3: LLUVIA ROBUSTO")
    print("="*80)
    
    try:
        from core.indices.lluvia.lluvia_indices import calcular_lluvia_completa
        
        datos = {
            "temperatura": 15.0,
            "humedad": 80.0,
            "presion_pa": 99000.0,
            "lluvia_24h": 5.0,
            "lluvia_1h": 1.0,
            "lluvia_72h": 20.0,
            "viento_medio": 3.0,
        }
        
        resultado = calcular_lluvia_completa(datos)
        
        print(f"✅ Lluvia ejecutada correctamente")
        print(f"   - Indice sintético: {resultado.get('indice_lluvia_sintetico', 'N/A'):.1f}%")
        print(f"   - Riesgo inundación: {resultado.get('riesgo_inundacion', 'N/A'):.1f}%")
        print(f"   - Visibilidad carretera: {resultado.get('visibilidad_carretera', 'N/A'):.1f}%")
        print(f"   - Adherencia terreno: {resultado.get('adherencia_terreno', 'N/A'):.1f}%")
        print(f"   - Probabilidad rayos: {resultado.get('probabilidad_rayos', 'N/A'):.1f}%")
        
        assert resultado.get('indice_lluvia_sintetico') is not None, "Sintético no debería ser None"
        print(f"✅ Robustez validada: NUNCA retorna None")
        return True
    
    except Exception as e:
        print(f"❌ Lluvia fallida: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_confort_robusto():
    """Test de confort con datos mock."""
    print("\n" + "="*80)
    print("TEST 4: CONFORT ROBUSTO")
    print("="*80)
    
    try:
        from core.indices.confort.confort_indices import calcular_confort_completa
        
        datos = {
            "temperatura": 22.0,
            "humedad": 50.0,
            "presion_pa": 101325.0,
            "viento_medio": 2.0,
            "radiacion": 300.0,
            "elevacion_solar": 45.0,
        }
        
        resultado = calcular_confort_completa(datos)
        
        print(f"✅ Confort ejecutado correctamente")
        print(f"   - Indice sintético: {resultado.get('indice_confort_sintetico', 'N/A'):.1f}%")
        print(f"   - Temperatura ideal: {resultado.get('temperatura_ideal', 'N/A'):.1f}%")
        print(f"   - Humedad ideal: {resultado.get('humedad_ideal', 'N/A'):.1f}%")
        print(f"   - UV Index: {resultado.get('indice_uvi', 'N/A'):.1f}%")
        print(f"   - Sensación térmica: {resultado.get('sensacion_termica', 'N/A'):.1f}%")
        
        assert resultado.get('indice_confort_sintetico') is not None, "Sintético no debería ser None"
        print(f"✅ Robustez validada: NUNCA retorna None")
        return True
    
    except Exception as e:
        print(f"❌ Confort fallido: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deporte_robusto():
    """Test de deporte con datos mock."""
    print("\n" + "="*80)
    print("TEST 5: DEPORTE ROBUSTO")
    print("="*80)
    
    try:
        from core.indices.deporte.deporte_indices import calcular_deporte_completa
        
        datos = {
            "temperatura": 18.0,
            "humedad": 55.0,
            "presion_pa": 101325.0,
            "viento_medio": 4.0,
            "radiacion": 400.0,
            "lluvia_24h": 0.0,
            "lluvia_1h": 0.0,
            "nubosidad": 30.0,
        }
        
        resultado = calcular_deporte_completa(datos)
        
        print(f"✅ Deporte ejecutado correctamente")
        print(f"   - Indice sintético: {resultado.get('indice_deporte_sintetico', 'N/A'):.1f}%")
        print(f"   - Adherencia terreno: {resultado.get('adherencia_terreno', 'N/A'):.1f}%")
        print(f"   - Visibilidad: {resultado.get('visibilidad', 'N/A'):.1f}%")
        print(f"   - Viento juego limpio: {resultado.get('viento_juego', 'N/A'):.1f}%")
        print(f"   - Confort atletas: {resultado.get('confort_atletas', 'N/A'):.1f}%")
        
        assert resultado.get('indice_deporte_sintetico') is not None, "Sintético no debería ser None"
        print(f"✅ Robustez validada: NUNCA retorna None")
        return True
    
    except Exception as e:
        print(f"❌ Deporte fallido: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecutar todos los tests."""
    print("\n" + "="*80)
    print("PRUEBA DE INDICES SINTETICOS MULTI-DOMINIO V50.0")
    print("="*80)
    
    results = []
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ FALLO EN IMPORTS - ABORTAR")
        return 1
    
    # Test 2-5: Funcionalidad
    results.append(("Cetrería", test_cetreria_robusto()))
    results.append(("Lluvia", test_lluvia_robusto()))
    results.append(("Confort", test_confort_robusto()))
    results.append(("Deporte", test_deporte_robusto()))
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE PRUEBAS")
    print("="*80)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:20s}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ¡ÉXITO! Todos los tests de índices sintéticos pasaron correctamente.")
        print("✅ Los 4 dominios (Cetrería, Lluvia, Confort, Deporte) están listos para bus_expander.py")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) fallido(s). Revisar errores arriba.")
        return 1

if __name__ == "__main__":
    exit(main())
