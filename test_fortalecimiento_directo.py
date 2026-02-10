#!/usr/bin/env python
"""Test directo del fortalecimiento sin servidor"""

from core.integration.fortalecimiento_captura import fortalecer_captura_ecowitt

# Crear un sistema mock
class MockSystem:
    def __init__(self):
        self.sensores = {}
    
    def actualizar_sensor(self, id, valor):
        self.sensores[id] = valor
        print(f'  ✅ Updated: {id} = {valor}')

system = MockSystem()

# Datos reales que recibimos
data = {
    'tempf': '65.8',
    'humidity': '70',
    'temp1f': '63.5',
    'humidity1': '68',
    'baromrelin': '29.590'
}

print("\n" + "="*80)
print("[TEST] Ejecutando fortalecimiento con datos de prueba")
print("="*80)

resultado = fortalecer_captura_ecowitt(data, system)

print("\n" + "="*80)
print("[RESULTADO] Datos capturados:")
print("="*80)
for key, val in resultado.get("datos_capturados", {}).items():
    print(f"  {key}: {val}")

print("\n[SISTEMA] Sensores actualizados:")
for key, val in system.sensores.items():
    print(f"  {key}: {val}")

print("\n[ERRORES]")
for err in resultado.get("errores", []):
    print(f"  ❌ {err}")

print("\n[FALLBACKS]")
for fallback in resultado.get("fallbacks_usados", []):
    print(f"  ⚠️  {fallback}")
