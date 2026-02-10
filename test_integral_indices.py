"""
Test rápido: Verificar que índices integrales funcionan correctamente.
Prueba lluvia EN PROGRESO vs SIN LLUVIA en cada dominio.
"""

import sys
sys.path.insert(0, r"c:\Users\kioko\Desktop\MeteoSerV3")

from core.indices.lluvia.lluvia_indices import indice_lluvia_sintetico as lluvia_sint
from core.indices.cetreria.cetreria_indices_v2 import indice_cetreria_sintetico as cetreria_sint
from core.indices.deporte.deporte_indices import indice_deporte_sintetico as deporte_sint
from core.indices.confort.confort_indices import indice_confort_sintetico as confort_sint

print("=" * 70)
print("TEST DE ÍNDICES INTEGRALES CON LLUVIA")
print("=" * 70)

# =========================================================================
# TEST 1: LLUVIA (Índice de Lluvia)
# =========================================================================
print("\n1. ÍNDICE LLUVIA")
print("-" * 70)

# Sin lluvia: condiciones normales
sin_lluvia = lluvia_sint(
    riesgo_inundacion=40.0,
    visibilidad_carretera=80.0,
    adherencia_terreno=85.0,
    probabilidad_rayos=25.0,
    lluvia_1h=0.0
)
print(f"SIN LLUVIA (0.0 mm): índice = {sin_lluvia:.1f}")

# Con lluvia moderada
lluvia_mod = lluvia_sint(
    riesgo_inundacion=40.0,
    visibilidad_carretera=80.0,
    adherencia_terreno=85.0,
    probabilidad_rayos=25.0,
    lluvia_1h=2.5
)
print(f"CON LLUVIA (2.5 mm): índice = {lluvia_mod:.1f} (esperado: << sin_lluvia)")

# Con lluvia fuerte
lluvia_fuerte = lluvia_sint(
    riesgo_inundacion=40.0,
    visibilidad_carretera=80.0,
    adherencia_terreno=85.0,
    probabilidad_rayos=25.0,
    lluvia_1h=10.0
)
print(f"LLUVIA FUERTE (10.0 mm): índice = {lluvia_fuerte:.1f} (esperado: muy bajo)")

# =========================================================================
# TEST 2: CETRERÍA
# =========================================================================
print("\n2. ÍNDICE CETRERÍA")
print("-" * 70)

# Sin lluvia: buen día para cetrería
sin_lluvia_cetr = cetreria_sint(
    viento=40.0,
    visibilidad=90.0,
    termales=75.0,
    barro=80.0,
    confort=70.0,
    lluvia_1h=0.0
)
print(f"SIN LLUVIA (0.0 mm): índice = {sin_lluvia_cetr:.1f}")

# Con lluvia: MAL día para cetrería
lluvia_cetr = cetreria_sint(
    viento=40.0,
    visibilidad=90.0,
    termales=75.0,
    barro=80.0,
    confort=70.0,
    lluvia_1h=2.0
)
print(f"CON LLUVIA (2.0 mm): índice = {lluvia_cetr:.1f} (esperado: << {sin_lluvia_cetr:.1f})")

# =========================================================================
# TEST 3: DEPORTE
# =========================================================================
print("\n3. ÍNDICE DEPORTE")
print("-" * 70)

# Sin lluvia: buenas condiciones deportivas
sin_lluvia_deporte = deporte_sint(
    adherencia_terreno=85.0,
    visibilidad=90.0,
    viento_juego=75.0,
    confort_atletas=80.0,
    lluvia_1h=0.0
)
print(f"SIN LLUVIA (0.0 mm): índice = {sin_lluvia_deporte:.1f}")

# Con lluvia: peor adherencia, visibilidad, confort
lluvia_deporte = deporte_sint(
    adherencia_terreno=85.0,
    visibilidad=90.0,
    viento_juego=75.0,
    confort_atletas=80.0,
    lluvia_1h=3.0
)
print(f"CON LLUVIA (3.0 mm): índice = {lluvia_deporte:.1f} (esperado: << {sin_lluvia_deporte:.1f})")

# =========================================================================
# TEST 4: CONFORT
# =========================================================================
print("\n4. ÍNDICE CONFORT")
print("-" * 70)

# Sin lluvia: confortable
sin_lluvia_conf = confort_sint(
    temperatura_ideal=85.0,
    humedad_ideal=80.0,
    indice_uvi=60.0,
    sensacion_termica=80.0,
    lluvia_1h=0.0
)
print(f"SIN LLUVIA (0.0 mm): índice = {sin_lluvia_conf:.1f}")

# Con lluvia: ligeramente menos confortable (menor efecto que cetrería)
lluvia_conf = confort_sint(
    temperatura_ideal=85.0,
    humedad_ideal=80.0,
    indice_uvi=60.0,
    sensacion_termica=80.0,
    lluvia_1h=5.0
)
print(f"CON LLUVIA (5.0 mm): índice = {lluvia_conf:.1f} (esperado: moderadamente < {sin_lluvia_conf:.1f})")

# =========================================================================
# RESUMEN
# =========================================================================
print("\n" + "=" * 70)
print("RESUMEN DE VALIDACIÓN")
print("=" * 70)

tests_passed = 0
tests_total = 4

# Test 1: Lluvia index baja con lluvia
if lluvia_mod < sin_lluvia and lluvia_fuerte < lluvia_mod:
    print("✓ Test 1 PASSED: Índice lluvia disminuye con lluvia")
    tests_passed += 1
else:
    print("✗ Test 1 FAILED: Índice lluvia no behaves correctly")

# Test 2: Cetrería index baja con lluvia
if lluvia_cetr < sin_lluvia_cetr:
    print("✓ Test 2 PASSED: Índice cetrería disminuye con lluvia")
    tests_passed += 1
else:
    print("✗ Test 2 FAILED: Índice cetrería no behaves correctly")

# Test 3: Deporte index baja con lluvia
if lluvia_deporte < sin_lluvia_deporte:
    print("✓ Test 3 PASSED: Índice deporte disminuye con lluvia")
    tests_passed += 1
else:
    print("✗ Test 3 FAILED: Índice deporte no behaves correctly")

# Test 4: Confort index baja con lluvia (pero menos que otros)
if lluvia_conf < sin_lluvia_conf:
    print("✓ Test 4 PASSED: Índice confort disminuye con lluvia")
    tests_passed += 1
else:
    print("✗ Test 4 FAILED: Índice confort no behaves correctly")

print(f"\nResultado: {tests_passed}/{tests_total} tests passed")

if tests_passed == tests_total:
    print("\n✓✓✓ TODOS LOS TESTS PASARON ✓✓✓")
    print("Los índices integrales funcionan correctamente.")
else:
    print(f"\n✗✗✗ {tests_total - tests_passed} TESTS FALLARON ✗✗✗")
    sys.exit(1)
