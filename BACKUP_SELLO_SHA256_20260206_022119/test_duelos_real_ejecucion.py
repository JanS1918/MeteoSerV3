#!/usr/bin/env python3
"""
TEST REAL: Ejecutar duelos REALES con datos históricos

Este test:
1. Ejecuta el motor de duelos CON DATOS REALES
2. Valida que los scores sean diferenciados
3. Valida que la lógica de decisión sea correcta
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from core.system_manager import SystemManager
from core.monitoring.formula_duel_engine import FormulaDuelEngine


def main():
    print("\n" + "="*70)
    print("TEST REAL: MOTOR DE DUELOS CON DATOS HISTÓRICOS")
    print("="*70)
    
    # 1. Inicializar sistema
    print("\n[1/4] Inicializando sistema...")
    try:
        manager = SystemManager()
        print(f"[OK] Sistema inicializado")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return
    
    # 2. Ejecutar motor de duelos
    print("\n[2/4] Ejecutando motor de duelos con datos reales...")
    try:
        engine = FormulaDuelEngine()
        print(f"   - Modo: dry_run={engine.dry_run}")
        print(f"   - Pesos: precision={engine.peso_precision}, estab={engine.peso_estabilidad}, efic={engine.peso_eficiencia}")
        
        # Ejecutar duelos
        duelos = engine.run(manager)
        
        if duelos:
            print(f"[OK] {len(duelos)} duelos ejecutados")
            
            for i, duelo in enumerate(duelos, 1):
                param = duelo.get("parametro", "?")
                ganador = duelo.get("ganador", "?")
                score_actual = duelo.get("score_actual", 0)
                score_alt = duelo.get("score_alt", 0)
                diff = abs(score_actual - score_alt)
                
                print(f"   [{i}] {param:25} | Ganador: {ganador:30} | Diferencia: {diff:.4f}")
        else:
            print("[WARNING]  No se ejecutaron duelos (¿datos insuficientes?)")
            return
    
    except Exception as e:
        print(f"[ERROR] Error ejecutando duelos: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Validar histórico guardado
    print("\n[3/4] Validando histórico de duelos guardado...")
    
    duelos_path = Path("data/duelos_historico.jsonl")
    if not duelos_path.exists():
        print("[WARNING]  No hay histórico (¿recorders deshabilitados?)")
        return
    
    duelos_guardados = []
    with open(duelos_path, "r", encoding="utf-8") as f:
        for linea in f:
            try:
                duelos_guardados.append(json.loads(linea))
            except:
                continue
    
    print(f"[OK] {len(duelos_guardados)} duelos en histórico")
    
    # 4. Verificar integridad
    print("\n[4/4] Verificación de integridad:")
    
    errores = 0
    correctos = 0
    
    for duelo in duelos_guardados:
        param = duelo.get("parametro", "?")
        ganador = duelo.get("ganador", "?")
        score_a = duelo.get("formula_a", {}).get("resultado")
        score_b = duelo.get("formula_b", {}).get("resultado")
        
        if score_a is None or score_b is None:
            print(f"   [WARNING]  {param}: Sin scores")
            continue
        
        # Validación: A debe ser > B (A = ganador)
        if score_a > score_b:
            correctos += 1
            print(f"   [OK] {param:25} | A({score_a:.4f}) > B({score_b:.4f}) | {ganador}")
        elif score_a == score_b:
            print(f"   [WARNING]  {param:25} | A({score_a:.4f}) == B({score_b:.4f}) | Empatado")
            errores += 1
        else:
            print(f"   [ERROR] {param:25} | A({score_a:.4f}) < B({score_b:.4f}) | ERROR INVERTIDO")
            errores += 1
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN:")
    print(f"{'='*70}")
    
    total = len(duelos_guardados)
    if total > 0:
        pct = (correctos * 100) // total
        print(f"\n[OK] Duelos correctos: {correctos}/{total} ({pct}%)")
        print(f"[ERROR] Duelos con error: {errores}/{total}")
        
        if errores == 0:
            print(f"\n[OK] PERFECTO - Todos los duelos son coherentes")
        else:
            print(f"\n[WARNING]  REVISAR - Hay duelos con problemas")
    else:
        print("[WARNING]  No hay duelos para validar")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
