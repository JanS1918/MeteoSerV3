#!/usr/bin/env python3
"""
Prueba de Ignición: Ley del Entero
Forzar viento=0.0 y humedad=100.0 manualmente y verificar que la salida JSON sea INT puro.
"""

import json
import requests
import time

# Primero, inyectar valores manuales en el sistema
print("🔧 INYECTANDO VALORES MANUALES DE PRUEBA...")
print("   - viento: 0.0 → esperamos 0 (INT)")
print("   - humedad: 100.0 → esperamos 100 (INT)")
print()

# Forzar valores en el sistema mediante POST al endpoint de sensores
try:
    # Inyectar viento=0.0
    response_viento = requests.post(
        "http://localhost:8080/sensor_input",
        json={"sensor": "viento", "value": 0.0},
        timeout=5
    )
    print(f"   Viento inyectado: {response_viento.status_code}")
    
    # Inyectar humedad=100.0
    response_humedad = requests.post(
        "http://localhost:8080/sensor_input",
        json={"sensor": "humedad", "value": 100.0},
        timeout=5
    )
    print(f"   Humedad inyectada: {response_humedad.status_code}")
    print()
    
    # Esperar a que el sistema procese
    time.sleep(2)
    
    # Obtener el JSON del endpoint central
    print("📡 CAPTURANDO JSON DEL ENDPOINT /api/panel/central...")
    response = requests.get("http://localhost:8080/api/panel/central", timeout=5)
    data = response.json()
    
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print()
    
    # Verificar la Ley del Entero
    print("=" * 80)
    print("✅ VERIFICACIÓN DE LA LEY DEL ENTERO")
    print("=" * 80)
    
    viento_val = data.get("viento", {}).get("valor")
    humedad_val = data.get("humedad", {}).get("valor")
    
    print(f"   Viento: {viento_val} (tipo: {type(viento_val).__name__})")
    print(f"   Humedad: {humedad_val} (tipo: {type(humedad_val).__name__})")
    print()
    
    # Verificar si son INT puros (sin .0)
    viento_es_int = isinstance(viento_val, int)
    humedad_es_int = isinstance(humedad_val, int)
    
    if viento_es_int and viento_val == 0:
        print("   ✅ VIENTO: 0 (INT puro, sin .0) - LEY DEL ENTERO CUMPLIDA")
    else:
        print(f"   ❌ VIENTO: {viento_val} (tipo {type(viento_val).__name__}) - LEY DEL ENTERO VIOLADA")
    
    if humedad_es_int and humedad_val == 100:
        print("   ✅ HUMEDAD: 100 (INT puro, sin .0) - LEY DEL ENTERO CUMPLIDA")
    else:
        print(f"   ❌ HUMEDAD: {humedad_val} (tipo {type(humedad_val).__name__}) - LEY DEL ENTERO VIOLADA")
    
    print()
    print("=" * 80)
    
    if viento_es_int and humedad_es_int:
        print("🎯 VISTO BUENO: La Ley del Entero está SELLADA en el sistema.")
        print("   El JSON de salida NO contiene paja digital (.0) en valores redondos.")
    else:
        print("❌ ERROR: La Ley del Entero NO está aplicada correctamente.")
        print("   El JSON de salida aún contiene .0 en valores redondos.")
    
    print("=" * 80)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
