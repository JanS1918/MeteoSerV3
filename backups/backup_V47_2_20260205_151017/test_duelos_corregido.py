#!/usr/bin/env python3
"""
TEST: Ejecutar duelos reales y validar sus decisiones

Este test:
1. Ejecuta el motor de duelos con datos reales
2. Genera histórico de duelos (con BUG FIJO)
3. Valida que las decisiones sean correctas
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.system_manager import SystemManager
from core.monitoring.formula_duel_engine import FormulaDuelEngine


def main():
    print("\n" + "="*70)
    print("TEST: DUELOS REALES CON VALIDACIÓN")
    print("="*70)
    
    # 1. Inicializar sistema
    print("\n[1/3] Inicializando sistema...")
    manager = SystemManager()
    print(f"✅ Sistema inicializado")
    
    # 2. Ejecutar motor de duelos
    print("\n[2/3] Ejecutando motor de duelos con datos reales...")
    engine = FormulaDuelEngine()
    
    duelos_ejecutados = engine.run(manager)
    print(f"✅ {len(duelos_ejecutados) if duelos_ejecutados else 0} duelos ejecutados")
    
    if duelos_ejecutados:
        for duelo in duelos_ejecutados:
            print(f"   - {duelo['parametro']}: {duelo['ganador']} gana")
    
    # 3. Validar histórico
    print("\n[3/3] Validando histórico de duelos (FIJO)...")
    
    import json
    duelos_path = Path("data/duelos_historico.jsonl")
    
    if duelos_path.exists():
        duelos = []
        with open(duelos_path, "r", encoding="utf-8") as f:
            for linea in f:
                try:
                    duelos.append(json.loads(linea))
                except:
                    continue
        
        print(f"✅ {len(duelos)} duelos en histórico")
        
        print("\n📋 VERIFICACIÓN DE INTEGRIDAD:")
        errores = 0
        for i, duelo in enumerate(duelos, 1):
            formula_a_resultado = duelo.get("formula_a", {}).get("resultado")
            formula_b_resultado = duelo.get("formula_b", {}).get("resultado")
            ganador = duelo.get("ganador")
            
            print(f"\n  Duelo {i}: {duelo.get('parametro', '?').upper()}")
            print(f"    A: {duelo.get('formula_a', {}).get('nombre')} = {formula_a_resultado:.2f}")
            print(f"    B: {duelo.get('formula_b', {}).get('nombre')} = {formula_b_resultado:.2f}")
            print(f"    Ganador declarado: {ganador}")
            
            # Verificar que A tiene mayor score que B
            if formula_a_resultado and formula_b_resultado:
                if formula_a_resultado > formula_b_resultado:
                    print(f"    ✅ CORRECTO - A > B ({formula_a_resultado:.2f} > {formula_b_resultado:.2f})")
                else:
                    print(f"    ❌ ERROR - A <= B ({formula_a_resultado:.2f} <= {formula_b_resultado:.2f})")
                    errores += 1
        
        if errores == 0:
            print(f"\n✅ TODOS LOS DUELOS SON CORRECTOS - Histórico integro")
        else:
            print(f"\n❌ {errores} ERRORES ENCONTRADOS")
    else:
        print("⚠️  No hay histórico de duelos")


if __name__ == "__main__":
    main()
