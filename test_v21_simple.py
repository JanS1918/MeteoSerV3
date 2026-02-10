import sys
sys.path.insert(0, 'C:\\Users\\kioko\\Desktop\\MeteoSerV3')

from core.indices.environmental_indices import (
    balance_hidrico_diario,
    estres_hidrico_cultivo,
    disponibilidad_agua_cultivable
)

print("\n✅ IMPORTS OK")

# Test 1
r = balance_hidrico_diario(10.0, 5.0, 1.0, 1.0)
print(f"✅ balance_hidrico_diario: {r['delta_h']:.1f} mm")

# Test 2
r2 = estres_hidrico_cultivo(25.0, 6.0, "general")
print(f"✅ estres_hidrico_cultivo: {r2['factor']:.3f} ({r2['nivel']})")

# Test 3
r3 = disponibilidad_agua_cultivable(25.0, 5.0, "general")
print(f"✅ disponibilidad_agua_cultivable: {r3['dias_hasta_sequia']:.1f} días")

print("\n✅ V21 COMPILACIÓN OK")
