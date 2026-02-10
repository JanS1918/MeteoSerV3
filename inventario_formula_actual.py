#!/usr/bin/env python
"""
INVENTARIO REAL: BUS + FORMULAS + ÍNDICES

Genera un inventario trazable desde el Bus, el catálogo de fórmulas,
la jerarquía de fórmulas y los sensores virtuales.
"""

from core.monitoring.inventario_bus_formulas import generar_inventario

print("=" * 80)
print("INVENTARIO COMPLETO: BUS / FORMULAS / INDICES")
print("=" * 80)

inventario = generar_inventario()
stats = inventario.get("stats", {}) if isinstance(inventario, dict) else {}

print("\nRESUMEN")
for clave, valor in stats.items():
    print(f"- {clave}: {valor}")

print("\nArchivo generado: data/inventario_bus_formulas.json")
