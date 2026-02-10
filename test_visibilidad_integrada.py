#!/usr/bin/env python3
"""
TEST RÁPIDO: Visibilidad integrada (4 métodos combinados)
Fecha: 9 Febrero 2026
"""

import sys
sys.path.insert(0, 'C:\\Users\\kioko\\Desktop\\MeteoSerV3')

from core.indices.environmental_indices import visibilidad_integrada_optima

print("\n" + "="*70)
print("TEST: VISIBILIDAD INTEGRADA (4 MÉTODOS)")
print("="*70)

# Test 1: Condiciones normales
print("\n[CASO 1] Condiciones normales (sin lluvia, PM bajo)")
result = visibilidad_integrada_optima(
    temp_c=15.0,
    humedad_pct=65.0,
    presion_hpa=1013.0,
    lluvia_rate_mm_h=0.0,
    pm25=12.0
)
print(f"  Visibilidad: {result['visibilidad_km']:.2f} km ({result['visibilidad_m']:.0f} m)")
print(f"  Método dominante: {result['método_dominante']}")
print(f"  Stoelinga: {result['desglose']['stoelinga_m']:.0f}m")
print(f"  Kneizys: {result['desglose']['kneizys_m']:.0f}m")
print(f"  Kasten: {result['desglose']['kasten_m']:.0f}m")
assert result['visibilidad_km'] > 0, "Visibilidad debe ser positiva"
print("  ✅ PASS")

# Test 2: Con lluvia
print("\n[CASO 2] Con lluvia activa (3 mm/h)")
result = visibilidad_integrada_optima(
    temp_c=15.0,
    humedad_pct=95.0,
    presion_hpa=1013.0,
    lluvia_rate_mm_h=3.0,
    pm25=15.0
)
print(f"  Visibilidad: {result['visibilidad_km']:.2f} km ({result['visibilidad_m']:.0f} m)")
print(f"  Método dominante: {result['método_dominante']}")
assert "Lluvia" in result['método_dominante'], "Con lluvia debe usar método lluvia"
print("  ✅ PASS")

# Test 3: Contaminación alta
print("\n[CASO 3] Contaminación alta (PM2.5 = 80 µg/m³)")
result = visibilidad_integrada_optima(
    temp_c=25.0,
    humedad_pct=60.0,
    presion_hpa=1010.0,
    lluvia_rate_mm_h=0.0,
    pm25=80.0
)
print(f"  Visibilidad: {result['visibilidad_km']:.2f} km ({result['visibilidad_m']:.0f} m)")
print(f"  Método dominante: {result['método_dominante']}")
assert "Contaminación" in result['método_dominante'], "Con PM alta debe usar Kneizys"
assert result['visibilidad_km'] < 10, "Con contaminación debe reducir visibilidad"
print("  ✅ PASS")

# Test 4: Niebla densa
print("\n[CASO 4] Niebla densa (humedad 99%, HR alta, lluvia)")
result = visibilidad_integrada_optima(
    temp_c=10.0,
    humedad_pct=99.0,
    presion_hpa=1013.0,
    lluvia_rate_mm_h=5.0,
    pm25=25.0
)
print(f"  Visibilidad: {result['visibilidad_km']:.2f} km ({result['visibilidad_m']:.0f} m)")
print(f"  Método dominante: {result['método_dominante']}")
assert result['visibilidad_km'] < 10, "Niebla debe dar < 10 km"
print("  ✅ PASS")

print("\n" + "="*70)
print("✅ TODOS LOS TESTS PASARON (VISIBILIDAD INTEGRADA FUNCIONANDO)")
print("="*70)
print("\nIntegración:")
print("  ✓ Combina 4 métodos: Stoelinga + Kneizys + Kasten + Higroscópica")
print("  ✓ Pesos dinámicos según lluvia, PM2.5 y humedad")
print("  ✓ Devuelve mejor estimado + método dominante")
print("  ✓ Fallback seguro a Stoelinga si hay error")
