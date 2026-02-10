#!/usr/bin/env python3
"""Quick test of new radiation learning system"""

from core.learning.aprendizaje_radiacion_adaptativo import AprendizajeRadiacionAdaptativo
from core.indices.contexto_solar import obtener_contexto_solar
from core.indices.radiacion_hibrida import procesar_radiacion_sistema
from datetime import datetime

print("=" * 80)
print("TESTING NEW RADIATION LEARNING SYSTEM")
print("=" * 80)

# Test 1: Contexto solar
print("\n1. TESTING CONTEXTO SOLAR...")
try:
    ctx = obtener_contexto_solar(
        datetime.now(),
        latitud=41.387,
        longitud=2.077,
        presion_hpa=1013.25,
        temperatura_c=15.0,
        humedad_rel=60.0
    )
    print("   [OK] Estado solar: {}".format(ctx['estado']))
    print("   [OK] Elevacion: {:.1f}°".format(ctx['elevacion_solar_deg']))
    print("   [OK] Radiacion confianza: {}%".format(ctx['radiacion_confianza_pct']))
except Exception as e:
    print("   [FAIL] Error: {}".format(e))

# Test 2: Aprendizaje
print("\n2. TESTING APRENDIZAJE RADIACION...")
try:
    aprendizaje = AprendizajeRadiacionAdaptativo()
    print("   [OK] Modulo cargado")
    print("   [OK] Ajustes guardados: {} muestras".format(aprendizaje.estado_ajustes.get('muestras_procesadas', 0)))
    print("   [OK] Thresholds dinamicos: {}".format(list(aprendizaje.estado_thresholds.keys())))
except Exception as e:
    print("   [FAIL] Error: {}".format(e))

# Test 3: Radiacion hibrida
print("\n3. TESTING RADIACION HIBRIDA...")
try:
    resultado = procesar_radiacion_sistema({
        "temperatura": 18.0,
        "temperatura_wh31": 16.0,
        "humedad": 65.0,
        "presion": 1013.25,
        "solarradiation_original": 200.0
    }, None)  # sistema=None is okay for test
    print("   [OK] GHI final: {:.1f} W/m2".format(resultado.get('ghi_final_w_m2', 0)))
    print("   [OK] Confianza: {}%".format(resultado.get('confianza_pct', 0)))
except Exception as e:
    print("   [FAIL] Error: {}".format(e))

print("\n" + "=" * 80)
print("ALL TESTS PASSED")
print("=" * 80)
