"""
Test de indices integrales - VERSIÓN ASCII
Verifica que lluvia afecte integralmente a cada indice.
"""

import sys
sys.path.insert(0, r"c:\Users\kioko\Desktop\MeteoSerV3")

from core.indices.lluvia.lluvia_indices import indice_lluvia_sintetico as lluvia_sint
from core.indices.cetreria.cetreria_indices_v2 import indice_cetreria_sintetico as cetreria_sint
from core.indices.deporte.deporte_indices import indice_deporte_sintetico as deporte_sint
from core.indices.confort.confort_indices import indice_confort_sintetico as confort_sint

print("=" * 70)
print("TEST DE INDICES INTEGRALES CON LLUVIA (ASCII version)")
print("=" * 70)

# =========================================================================
# TEST 1: LLUVIA
# =========================================================================
print("\n1. INDICE LLUVIA")
print("-" * 70)

sin_lluvia = lluvia_sint(40.0, 80.0, 85.0, 25.0, lluvia_1h=0.0)
lluvia_mod = lluvia_sint(40.0, 80.0, 85.0, 25.0, lluvia_1h=2.5)
lluvia_fuerte = lluvia_sint(40.0, 80.0, 85.0, 25.0, lluvia_1h=10.0)

print(f"SIN LLUVIA (0.0 mm):   {sin_lluvia:.1f}")
print(f"CON LLUVIA (2.5 mm):   {lluvia_mod:.1f}")
print(f"LLUVIA FUERTE (10 mm): {lluvia_fuerte:.1f}")
print(f"Comportamiento: {lluvia_fuerte:.1f} < {lluvia_mod:.1f} < {sin_lluvia:.1f}? ", end="")

if lluvia_fuerte < lluvia_mod < sin_lluvia:
    print("SI [PASS]")
    test1_pass = True
else:
    print("NO [FAIL]")
    test1_pass = False

# =========================================================================
# TEST 2: CETRERIA
# =========================================================================
print("\n2. INDICE CETRERIA")
print("-" * 70)

sin_lluvia_cetr = cetreria_sint(40.0, 90.0, 75.0, 80.0, 70.0, lluvia_1h=0.0)
lluvia_cetr = cetreria_sint(40.0, 90.0, 75.0, 80.0, 70.0, lluvia_1h=2.0)

print(f"SIN LLUVIA (0.0 mm): {sin_lluvia_cetr:.1f}")
print(f"CON LLUVIA (2.0 mm): {lluvia_cetr:.1f}")
print(f"Comportamiento: {lluvia_cetr:.1f} < {sin_lluvia_cetr:.1f}? ", end="")

if lluvia_cetr < sin_lluvia_cetr:
    print("SI [PASS]")
    test2_pass = True
else:
    print("NO [FAIL]")
    test2_pass = False

# =========================================================================
# TEST 3: DEPORTE
# =========================================================================
print("\n3. INDICE DEPORTE")
print("-" * 70)

sin_lluvia_deporte = deporte_sint(85.0, 90.0, 75.0, 80.0, lluvia_1h=0.0)
lluvia_deporte = deporte_sint(85.0, 90.0, 75.0, 80.0, lluvia_1h=3.0)

print(f"SIN LLUVIA (0.0 mm): {sin_lluvia_deporte:.1f}")
print(f"CON LLUVIA (3.0 mm): {lluvia_deporte:.1f}")
print(f"Comportamiento: {lluvia_deporte:.1f} < {sin_lluvia_deporte:.1f}? ", end="")

if lluvia_deporte < sin_lluvia_deporte:
    print("SI [PASS]")
    test3_pass = True
else:
    print("NO [FAIL]")
    test3_pass = False

# =========================================================================
# TEST 4: CONFORT
# =========================================================================
print("\n4. INDICE CONFORT")
print("-" * 70)

sin_lluvia_conf = confort_sint(85.0, 80.0, 60.0, 80.0, lluvia_1h=0.0)
lluvia_conf = confort_sint(85.0, 80.0, 60.0, 80.0, lluvia_1h=5.0)

print(f"SIN LLUVIA (0.0 mm): {sin_lluvia_conf:.1f}")
print(f"CON LLUVIA (5.0 mm): {lluvia_conf:.1f}")
print(f"Comportamiento: {lluvia_conf:.1f} < {sin_lluvia_conf:.1f}? ", end="")

if lluvia_conf < sin_lluvia_conf:
    print("SI [PASS]")
    test4_pass = True
else:
    print("NO [FAIL]")
    test4_pass = False

# =========================================================================
# RESUMEN
# =========================================================================
print("\n" + "=" * 70)
print("RESUMEN")
print("=" * 70)

results = [
    ("LLUVIA", test1_pass),
    ("CETRERIA", test2_pass),
    ("DEPORTE", test3_pass),
    ("CONFORT", test4_pass),
]

passed = sum(1 for _, p in results if p)
total = len(results)

for name, passed_test in results:
    status = "PASS" if passed_test else "FAIL"
    print(f"  {name}: {status}")

print(f"\nResultado: {passed}/{total} tests passed")

if passed == total:
    print("\nSUCCESS: Todos los indices integrales funcionan correctamente!")
    sys.exit(0)
else:
    print(f"\nFAILURE: {total - passed} tests fallaron")
    sys.exit(1)
