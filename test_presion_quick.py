#!/usr/bin/env python
"""Test rápido del bloque de presión"""

# Simular system.sensores
class MockSystem:
    def __init__(self):
        self.sensores = {}
        self.data = {}
        self.bus = MockBus()
    
    def actualizar_sensor(self, name, val):
        print(f"  actualizar_sensor('{name}', {val})")
    
    def registrar_sensor_metadata(self, name, **kwargs):
        print(f"  registrar_sensor_metadata('{name}', {kwargs})")

class MockBus:
    def publicar(self, key, val, unit=""):
        print(f"  bus.publicar('{key}', {val}, '{unit}')")

# Simular datos de Ecowitt
data = {
    "tempinf": 55.9,
    "humidityin": 79,
    "baromrelin": 29.673,
    "baromabsin": 29.318,
}

system = MockSystem()

# CÓDIGO DE PRESIÓN
baromrelint = data.get("baromrelin")  # HP2550A
baromabsint = data.get("baromabsin")  # HP2550A

print("=== PRESIÓN RELATIVA ===")
if baromrelint is not None:
    try:
        presion_relativa_hpa = float(baromrelint) * 33.8639  # inHg → hPa
        print(f"Conversión: {baromrelint} × 33.8639 = {presion_relativa_hpa:.2f} hPa")
        if presion_relativa_hpa > 900 and presion_relativa_hpa < 1100:
            system.sensores["presion"] = round(presion_relativa_hpa, 2)
            system.sensores["presion_status"] = "OK"
            system.sensores["presion_fuente"] = "HP2550A"
            
            system.data["presion"] = round(presion_relativa_hpa, 2)
            system.data["presion_relativa"] = round(presion_relativa_hpa, 2)
            
            presion_relativa_rounded = round(presion_relativa_hpa, 2)
            system.bus.publicar("presion", presion_relativa_rounded, "hPa")
            
            system.actualizar_sensor("presion", presion_relativa_rounded)
            system.actualizar_sensor("presion", presion_relativa_rounded)
            
            print(f"[INGESTA] Presión HP2550A RELATIVA (nivel mar): {presion_relativa_hpa:.2f} hPa → INTERIOR y EXTERIOR")
        else:
            system.sensores["presion_status"] = "OUT_OF_RANGE"
            print(f"[ADVERTENCIA] Presión relativa fuera de rango: {presion_relativa_hpa:.2f} hPa (rango válido: 900-1100)")
    except Exception as e:
        print(f"[ERROR] Error procesando presión relativa: {e}")
        system.sensores["presion_status"] = "ERROR"

print("\n=== PRESIÓN ABSOLUTA ===")
if baromabsint is not None:
    try:
        presion_absoluta_hpa = float(baromabsint) * 33.8639  # inHg → hPa
        print(f"Conversión: {baromabsint} × 33.8639 = {presion_absoluta_hpa:.2f} hPa")
        if presion_absoluta_hpa > 900 and presion_absoluta_hpa < 1100:
            system.data["presion_absoluta"] = round(presion_absoluta_hpa, 2)
            
            presion_absoluta_rounded = round(presion_absoluta_hpa, 2)
            system.bus.publicar("presion_absoluta_interior", presion_absoluta_rounded, "hPa")
            
            system.actualizar_sensor("presion_absoluta_interior", presion_absoluta_rounded)
            system.actualizar_sensor("presion_absoluta_interior", presion_absoluta_rounded)
            
            print(f"[INGESTA] Presión HP2550A ABSOLUTA (nivel sensor): {presion_absoluta_hpa:.2f} hPa → INTERIOR y EXTERIOR")
        else:
            print(f"[ADVERTENCIA] Presión absoluta fuera de rango: {presion_absoluta_hpa:.2f} hPa (rango válido: 900-1100)")
    except Exception as e:
        print(f"[ERROR] Error procesando presión absoluta: {e}")

print("\n=== RESULTADO ===")
print(f"system.sensores = {system.sensores}")
print(f"system.data = {system.data}")
