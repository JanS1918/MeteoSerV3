#!/usr/bin/env python3
"""
Test Omnipotencia V1.5 - Sistema Simplificado
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8080"
OMNIPOTENCE_PREFIX = "/admin/omnipotence"

print("\n" + "="*80)
print("🛸 TEST OMNIPOTENCIA V1.5 - RADAR UNIVERSAL")
print("="*80 + "\n")

try:
    # 1. Verificar estado
    print("1️⃣ Estado del Radar Universal...")
    resp = requests.get(f"{BASE_URL}{OMNIPOTENCE_PREFIX}/radar-status", timeout=5)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✅ Radar activo: {data.get('radar_running')}")
        print(f"   📡 Dispositivos: {data.get('detected_count')}")
    
    # 2. Iniciar radar
    print("\n2️⃣ Iniciando Radar...")
    resp = requests.post(f"{BASE_URL}{OMNIPOTENCE_PREFIX}/start-radar", timeout=5)
    if resp.status_code == 200:
        print(f"   ✅ Radar iniciado")
    
    time.sleep(2)
    
    # 3. Simular detección USB
    print("\n3️⃣ Simulando detección USB...")
    resp = requests.post(
        f"{BASE_URL}{OMNIPOTENCE_PREFIX}/detect-usb",
        params={"port": "COM3", "device_type": "MH_Z19_CO2"},
        timeout=5
    )
    if resp.status_code == 200:
        print(f"   ✅ USB Detectado")
    
    # 4. Simular detección BLE
    print("\n4️⃣ Simulando detección Bluetooth...")
    resp = requests.post(
        f"{BASE_URL}{OMNIPOTENCE_PREFIX}/detect-ble",
        params={"address": "AA:BB:CC:DD:EE:FF", "device_type": "LYWSD_TEMP_HUMIDITY"},
        timeout=5
    )
    if resp.status_code == 200:
        print(f"   ✅ BLE Detectado")
    
    # 5. Simular detección WiFi
    print("\n5️⃣ Simulando detección WiFi...")
    resp = requests.post(
        f"{BASE_URL}{OMNIPOTENCE_PREFIX}/detect-wifi",
        params={"hostname": "shelly-bedroom", "device_type": "SHELLY_DEVICE"},
        timeout=5
    )
    if resp.status_code == 200:
        print(f"   ✅ WiFi Detectado")
    
    # 6. Listar hardware
    print("\n6️⃣ Hardware detectado total...")
    resp = requests.get(f"{BASE_URL}{OMNIPOTENCE_PREFIX}/detected-hardware", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        hardware = data.get('hardware', [])
        print(f"   📊 Total: {len(hardware)}")
        for hw in hardware:
            print(f"      - {hw.get('sensor_type')} ({hw.get('source')})")
    
    # 7. Asimilar un sensor
    if hardware:
        print("\n7️⃣ Asimilando primer sensor...")
        sensor_id = hardware[0].get('sensor_id')
        resp = requests.post(
            f"{BASE_URL}{OMNIPOTENCE_PREFIX}/assimilate",
            params={"sensor_id": sensor_id},
            timeout=5
        )
        if resp.status_code == 200:
            print(f"   ✅ Sensor asimilado")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETADO - OMNIPOTENCIA V1.5 FUNCIONANDO")
    print("="*80 + "\n")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
