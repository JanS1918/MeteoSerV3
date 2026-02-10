#!/usr/bin/env python3
"""
EJECUTOR RÁPIDO: Prueba el motor de duelos en 30 segundos.
Uso: python run_duel_test.py
"""

import json
import sys
from pathlib import Path

# Configurar ruta
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("\n" + "=" * 70)
    print("PRUEBA DEL MOTOR DE DUELOS")
    print("=" * 70)
    
    try:
        from core.monitoring.sensor_data_bridge import SensorDataBridge
        from core.monitoring.formula_duel_engine import FormulaDuelEngine
        from core.bus.formula_hierarchy import FORMULA_HIERARCHY
        
        print("\n[PASO 1] Verificar datos disponibles...")
        
        base_dir = Path(__file__).parent
        bridge = SensorDataBridge(base_dir)
        
        # Mock system para llenar datos
        class System:
            def __init__(self):
                self.historial_sensores = {}
                self.sensores = {}
                self.sensores_alertas = {}
                self.sensores_metadata = {}
        
        system = System()
        parametros_cargados = bridge.cargar_y_llenar(system)
        
        print(f"   - Parametros cargados: {parametros_cargados}")
        print(f"   - Historico del sistema: {len(system.historial_sensores)} parametros")
        
        print("\n[PASO 2] Verificar jerarquia de formulas...")
        print(f"   - Parametros en jerarquia: {len(FORMULA_HIERARCHY)}")
        
        if len(FORMULA_HIERARCHY) < 2:
            print("   ERROR: Muy pocos parametros en jerarquia para duelos")
            return False
        
        print("\n[PASO 3] Inicializar motor...")
        engine = FormulaDuelEngine(base_dir)
        print(f"   - Modo: dry_run={engine.dry_run}")
        print(f"   - Max parametros: {engine.max_parametros_por_run}")
        print(f"   - Sample size: {engine.sample_size}")
        
        print("\n[PASO 4] Ejecutar duelos (esto toma un momento)...")
        engine.run(system)
        
        print("   - Duelos completados")
        
        print("\n[PASO 5] Mostrar resultados...")
        results_path = base_dir / "data" / "formula_duel_results.json"
        
        if results_path.exists():
            with open(results_path, 'r', encoding='utf-8') as f:
                resultados = json.load(f)
            
            print(f"   - Total de duelos: {len(resultados)}")
            
            if resultados:
                print("\n   RESULTADOS:")
                for i, duel in enumerate(resultados):
                    print(f"\n   [{i+1}] {duel['parametro']}")
                    print(f"       Ganador: {duel['ganador']}")
                    print(f"       Score: {duel['score_alt']:.3f} vs {duel['score_actual']:.3f}")
                    if duel.get('escenarios'):
                        print(f"       Escenarios: SI")
            else:
                print("   (Sin resultados - puede ser que no haya datos suficientes)")
        
        print("\n" + "=" * 70)
        print("OK: MOTOR FUNCIONANDO CORRECTAMENTE")
        print("=" * 70)
        print("\nProximos pasos:")
        print("  1. Revisar INVENTARIO_DISENO_IMPLEMENTACION.md")
        print("  2. Si resultados son coherentes -> cambiar dry_run=False")
        print("  3. Crear dashboard con streamlit_duel_results.py")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
