"""
TEST DEL MOTOR DE DUELOS CON DATOS REALES
Ejecutar duelo de ejemplo para verificar que funciona end-to-end
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from core.monitoring.formula_duel_engine import FormulaDuelEngine
from core.monitoring.sensor_data_bridge import SensorDataBridge


class MockSystem:
    """Sistema simulado con datos reales del puente."""
    def __init__(self):
        self.historial_sensores = {}
        self.sensores = {}
        self.sensores_alertas = {}
        self.sensores_metadata = {}


def test_motor_duelos_real():
    """Prueba el motor con datos reales."""
    print("=" * 70)
    print("TEST: MOTOR DE DUELOS CON DATOS REALES")
    print("=" * 70)
    
    base_dir = Path.cwd()
    
    # 1. Crear sistema
    print("\n[PASO 1] Crear sistema simulado...")
    system = MockSystem()
    
    # 2. Llenar datos
    print("[PASO 2] Llenar datos desde last_sensores.json...")
    bridge = SensorDataBridge(base_dir)
    rellenados = bridge.cargar_y_llenar(system)
    print(f"  OK: {rellenados} parametros cargados")
    print(f"  OK: Historico tiene {len(system.historial_sensores)} parametros")
    
    # 3. Crear motor
    print("\n[PASO 3] Inicializar FormulaDuelEngine...")
    engine = FormulaDuelEngine(base_dir)
    engine.dry_run = True  # Modo seguro
    print(f"  OK: Motor en modo dry_run={engine.dry_run}")
    print(f"  OK: Max parametros por run: {engine.max_parametros_por_run}")
    print(f"  OK: Tamaño de muestra: {engine.sample_size}")
    
    # 4. Ejecutar duelo
    print("\n[PASO 4] Ejecutar duelos...")
    try:
        engine.run(system)
        print("  OK: Duelos completados sin errores")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Ver resultados
    print("\n[PASO 5] Ver resultados de duelos...")
    results_path = base_dir / "data" / "formula_duel_results.json"
    
    if not results_path.exists():
        print("  ERROR: No se generó archivo de resultados")
        return False
    
    import json
    try:
        resultados = json.loads(results_path.read_text(encoding="utf-8"))
        print(f"  OK: {len(resultados)} duelos realizados")
        
        for duel in resultados[:3]:  # Ver primeros 3
            print(f"\n  Parametro: {duel['parametro']}")
            print(f"    Ganador: {duel['ganador']}")
            print(f"    Score actual: {duel['score_actual']:.3f}")
            print(f"    Score alternativo: {duel['score_alt']:.3f}")
            print(f"    Dry-run: {duel['dry_run']}")
        
        if len(resultados) > 3:
            print(f"\n  ... y {len(resultados) - 3} duelos mas")
    
    except Exception as e:
        print(f"  ERROR al leer resultados: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("OK: MOTOR FUNCIONANDO CORRECTAMENTE CON DATOS REALES")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_motor_duelos_real()
    sys.exit(0 if success else 1)
