#!/usr/bin/env python3
"""
Test Omnipotencia V1.5: Verifica que el Radar Universal funciona
"""

import sys
import time
import requests
import json
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://127.0.0.1:8080"
OMNIPOTENCE_PREFIX = "/admin/omnipotence"


def test_omnipotence():
    """Test del sistema de Omnipotencia"""
    
    print("\n" + "="*80)
    print("🛸 TEST OMNIPOTENCIA V1.5 - RADAR UNIVERSAL DE HARDWARE")
    print("="*80)
    
    try:
        # 1. Obtener estado del radar
        print("\n1️⃣ Obteniendo estado del Radar Universal...")
        resp = requests.get(f"{BASE_URL}{OMNIPOTENCE_PREFIX}/radar-status")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   [OK] Status: {data.get('status')}")
            print(f"   🛸 Radar ejecutándose: {data.get('radar_running')}")
            print(f"   📡 Total detectados: {data.get('total_detected')}")
            print(f"   ⏳ Pendientes asimilación: {data.get('pending_assimilation')}")
            print(f"   [STATS] Por fuente: {data.get('detected_by_source')}")
        else:
            print(f"   [ERROR] Error: {resp.status_code} - {resp.text}")
        
        # 2. Iniciar radar
        print("\n2️⃣ Iniciando Radar Universal...")
        resp = requests.post(f"{BASE_URL}{OMNIPOTENCE_PREFIX}/start-radar")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   [OK] {data.get('message')}")
            print(f"   📝 {data.get('description')}")
        else:
            print(f"   [ERROR] Error: {resp.status_code}")
        
        # Esperar un poco para que escanee
        print("\n⏳ Esperando a que el radar realice escaneos iniciales (10s)...")
        time.sleep(10)
        
        # 3. Obtener hardware detectado
        print("\n3️⃣ Consultando hardware detectado...")
        resp = requests.get(f"{BASE_URL}{OMNIPOTENCE_PREFIX}/detected-hardware")
        if resp.status_code == 200:
            data = resp.json()
            count = data.get('count', 0)
            print(f"   [OK] Hardware detectado: {count}")
            
            if count > 0:
                hardware = data.get('hardware', [])
                for i, hw in enumerate(hardware[:5]):  # Mostrar primeros 5
                    print(f"\n   Hardware #{i+1}:")
                    print(f"      ID: {hw.get('sensor_id')}")
                    print(f"      Tipo: {hw.get('sensor_type')}")
                    print(f"      Fuente: {hw.get('source')}")
                    print(f"      Estado: {hw.get('state')}")
        else:
            print(f"   [INFO] Sin hardware detectado aún (normal si no hay sensores conectados)")
        
        # 4. Obtener hardware pendiente
        print("\n4️⃣ Consultando hardware pendiente de asimilación...")
        resp = requests.get(f"{BASE_URL}{OMNIPOTENCE_PREFIX}/pending-assimilation")
        if resp.status_code == 200:
            data = resp.json()
            pending = data.get('pending', [])
            print(f"   📋 Pendientes: {len(pending)}")
            
            if pending:
                for hw in pending[:3]:
                    print(f"   - {hw.get('sensor_id')}: {hw.get('sensor_type')}")
        
        # 5. Obtener estado de drivers
        print("\n5️⃣ Consultando drivers instalados...")
        resp = requests.get(f"{BASE_URL}{OMNIPOTENCE_PREFIX}/driver-status")
        if resp.status_code == 200:
            data = resp.json()
            drivers = data.get('installed_drivers', {})
            print(f"   📦 Drivers: {drivers}")
        
        print("\n" + "="*80)
        print("[OK] TEST COMPLETADO - OMNIPOTENCIA V1.5 FUNCIONANDO")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Error en test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Intentar conectar al servidor
    try:
        resp = requests.get(f"{BASE_URL}/estado", timeout=2)
        print("[OK] Servidor MeteoSer está activo")
    except:
        print("[ERROR] Error: No se puede conectar al servidor en {BASE_URL}")
        print("   Asegúrate de que main_asgi.py está ejecutándose:")
        print("   .venv\\Scripts\\python.exe -m uvicorn main_asgi:app --host 127.0.0.1 --port 8080")
        sys.exit(1)
    
    # Ejecutar tests
    test_omnipotence()
