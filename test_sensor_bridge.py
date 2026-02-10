#!/usr/bin/env python3
"""
Test rápido del puente de datos: Verificar que motor puede acceder a datos reales.
Ejecutar: python test_sensor_bridge.py
"""

import sys
import json
import time
from pathlib import Path

# Agregar ruta del proyecto
sys.path.insert(0, str(Path(__file__).parent))

from core.monitoring.sensor_data_bridge import SensorDataBridge


class MockSystem:
    """Sistema simulado para testing."""
    def __init__(self):
        self.historial_sensores = {}
        self.sensores = {}
        self.sensores_alertas = {}
        self.sensores_metadata = {}


def _run_sensor_bridge():
    """Prueba el puente de datos completo."""
    print("🧪 TEST: SensorDataBridge")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    bridge = SensorDataBridge(base_dir)
    system = MockSystem()
    
    # Test 1: Cargar y llenar
    print("\n[TEST 1] Cargar last_sensores.json y llenar historial...")
    rellenados = bridge.cargar_y_llenar(system)
    print(f"[OK] {rellenados} parámetros rellenados")
    
    if rellenados == 0:
        print("[ERROR] ERROR: No se cargaron parámetros. ¿last_sensores.json existe?")
        return False
    
    # Test 2: Verificar estructura
    print("\n[TEST 2] Verificar estructura del historial...")
    if not system.historial_sensores:
        print("[ERROR] ERROR: historial_sensores está vacío")
        return False
    
    print(f"[OK] Parámetros en historial: {len(system.historial_sensores)}")
    
    # Test 3: Ver algunos parámetros cargados
    print("\n[TEST 3] Parámetros cargados (primeros 5):")
    for i, (param, datos) in enumerate(system.historial_sensores.items()):
        if i >= 5:
            break
        if datos:
            ts, val = datos[-1]  # Último valor
            print(f"  • {param:30} = {val:10} (ts: {time.ctime(ts)})")
    
    # Test 4: Persistencia
    print("\n[TEST 4] Verificar persistencia (sensores_historico.json)...")
    historico_path = base_dir / "data" / "sensores_historico.json"
    if historico_path.exists():
        tamaño = historico_path.stat().st_size
        print(f"[OK] Archivo creado: {historico_path}")
        print(f"   Tamaño: {tamaño} bytes")
        
        # Contar registros
        try:
            data = json.loads(historico_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                print(f"   Registros: {len(data)}")
        except Exception as e:
            print(f"   [WARNING] No se pudo leer: {e}")
    else:
        print("[WARNING] sensores_historico.json no existe aún")
    
    # Test 5: Estadísticas
    print("\n[TEST 5] Calcular estadísticas de parámetros...")
    parametros_test = ["temperatura_interior", "humedad_interior", "presion"]
    for param in parametros_test:
        stats = bridge.estadisticas_parametro(param)
        if stats:
            print(f"[OK] {param}:")
            print(f"   Count: {stats['count']}, Mean: {stats['mean']:.2f}, "
                  f"Stdev: {stats['stdev']:.2f}, Range: [{stats['min']:.2f}, {stats['max']:.2f}]")
        else:
            print(f"[WARNING] {param}: sin datos")
    
    # Test 6: Cache
    print("\n[TEST 6] Probar cache (segunda llamada debe ser más rápida)...")
    ts_inicio = time.time()
    rellenados2 = bridge.cargar_y_llenar(system)
    ts_fin = time.time()
    tiempo = (ts_fin - ts_inicio) * 1000
    print(f"[OK] Segunda carga en {tiempo:.2f} ms ({rellenados2} parámetros)")
    
    print("\n" + "=" * 60)
    print("[OK] TODOS LOS TESTS PASARON")
    print("=" * 60)
    return True


def test_sensor_bridge():
    success = _run_sensor_bridge()
    assert success


if __name__ == "__main__":
    success = _run_sensor_bridge()
    sys.exit(0 if success else 1)
