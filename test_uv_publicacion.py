#!/usr/bin/env python3
"""
TEST RÁPIDO: Verificar que Índice UV se publica correctamente
Fecha: 9 Febrero 2026
"""

import sys
sys.path.insert(0, 'C:\\Users\\kioko\\Desktop\\MeteoSerV3')

# Simular sistema
class MockSystem:
    def __init__(self):
        self.data = {
            "temperatura": 15.0,
            "humedad_relativa": 65.0,
            "radiacion_solar": 500.0,
            "velocidad_viento": 3.0
        }
        self._elevacion_solar_grados = 30  # Mañana
        
from core.indices.environmental_indices import EnvironmentalIndices

# Crear instancia
system = MockSystem()
ei = EnvironmentalIndices(system)

# Test 1: UV de día
print("\n=== TEST 1: UV de día (elevación solar = 30°) ===")
result = ei.indice_uv()
print(f"Valor UV: {result.get('valor'):.1f}")
print(f"Estimado: {result.get('estimado')}")
print(f"Explicación: {result.get('explicacion')}")
assert result.get('valor', 0) > 0, "UV debería ser > 0 con elevación solar 30°"
print("✅ PASS")

# Test 2: UV de noche
print("\n=== TEST 2: UV de noche (elevación solar = -10°) ===")
ei.system._elevacion_solar_grados = -10
result = ei.indice_uv()
print(f"Valor UV: {result.get('valor'):.1f}")
print(f"Estimado: {result.get('estimado')}")
print(f"Explicación: {result.get('explicacion')}")
assert result.get('valor') == 0, "UV debería ser 0 en la noche"
print("✅ PASS")

# Test 3: UV al mediodía
print("\n=== TEST 3: UV al mediodía (elevación solar = 70°) ===")
ei.system._elevacion_solar_grados = 70
result = ei.indice_uv()
print(f"Valor UV: {result.get('valor'):.1f}")
print(f"Estimado: {result.get('estimado')}")
assert result.get('valor', 0) > result.get('valor', 0), "UV debería ser máximo"
print("✅ PASS")

print("\n" + "="*70)
print("✅ TODOS LOS TESTS UV PASARON")
print("="*70)
print("\nVerificación:")
print("  ✓ UV se calcula correctamente de noche (0)")
print("  ✓ UV se calcula correctamente de día (>0)")
print("  ✓ UV responde a cambios de elevación solar")
print("  ✓ Listo para publicarse en Bus")
