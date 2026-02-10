#!/usr/bin/env python3
"""
TEST: Validar decisiones de duelos contra datos históricos reales (VERSIÓN CORREGIDA)

Este test:
1. Lee duelos ejecutados del histórico
2. Verifica que los scores sean coherentes (ganador > perdedor)
3. Si no, corrige los datos
4. Luego valida las decisiones
"""

import json
import statistics
from pathlib import Path
from datetime import datetime

def cargar_duelos_historicos():
    """Carga registros de duelos ejecutados."""
    duelos_path = Path("data/duelos_historico.jsonl")
    if not duelos_path.exists():
        print("❌ No hay histórico de duelos")
        return []
    
    duelos = []
    with open(duelos_path, "r", encoding="utf-8") as f:
        for linea in f:
            try:
                duelos.append(json.loads(linea))
            except:
                continue
    
    return duelos


def verificar_integridad_duelos():
    """Verifica que el histórico de duelos sea correcto."""
    print("\n" + "="*70)
    print("VERIFICACIÓN DE INTEGRIDAD: HISTÓRICO DE DUELOS")
    print("="*70)
    
    duelos = cargar_duelos_historicos()
    
    if not duelos:
        print("\n❌ No hay duelos en histórico")
        return False
    
    print(f"\n✅ {len(duelos)} duelos cargados")
    
    print("\n📋 ANÁLISIS DETALLADO:")
    
    errores = []
    correctos = 0
    
    for i, duelo in enumerate(duelos, 1):
        parametro = duelo.get("parametro", "?")
        ganador_nombre = duelo.get("formula_a", {}).get("nombre", "?")
        perdedor_nombre = duelo.get("formula_b", {}).get("nombre", "?")
        
        resultado_a = duelo.get("formula_a", {}).get("resultado")
        resultado_b = duelo.get("formula_b", {}).get("resultado")
        
        ganador_declarado = duelo.get("ganador", "?")
        
        print(f"\n  [{i}] {parametro.upper():20} | Ganador: {ganador_nombre}")
        print(f"      A ({ganador_nombre:35}): {resultado_a:.4f}")
        print(f"      B ({perdedor_nombre:35}): {resultado_b:.4f}")
        
        if resultado_a is not None and resultado_b is not None:
            if resultado_a > resultado_b:
                print(f"      ✅ CORRECTO - A > B")
                correctos += 1
            else:
                print(f"      ❌ ERROR - A <= B (SCORES INVERTIDOS)")
                errores.append({
                    "index": i - 1,
                    "duelo": duelo,
                    "razon": "Scores invertidos"
                })
        else:
            print(f"      ⚠️  No hay scores")
    
    # Resumen
    print(f"\n{'='*70}")
    print("RESUMEN:")
    print(f"{'='*70}")
    print(f"\n✅ Duelos correctos: {correctos}/{len(duelos)}")
    
    if errores:
        print(f"❌ Duelos con error: {len(errores)}/{len(duelos)}")
        print(f"\nDuelos problemáticos:")
        for err in errores:
            print(f"  - [{err['index']+1}] {err['duelo'].get('parametro')}: {err['razon']}")
        
        return False
    else:
        print(f"\n✅ TODOS LOS DUELOS SON COHERENTES")
        return True


def validar_decisiones():
    """Valida si las decisiones de duelos son razonables."""
    print("\n" + "="*70)
    print("VALIDACIÓN DE DECISIONES: ¿SON CORRECTAS LAS ELECCIONES?")
    print("="*70)
    
    duelos = cargar_duelos_historicos()
    
    if not duelos:
        return
    
    print(f"\n📊 ANÁLISIS DE DECISIONES:")
    
    estadisticas = {
        "total": len(duelos),
        "diferencias": [],
        "confianzas": []
    }
    
    for duelo in duelos:
        resultado_a = duelo.get("formula_a", {}).get("resultado", 0)
        resultado_b = duelo.get("formula_b", {}).get("resultado", 0)
        
        diferencia = abs(resultado_a - resultado_b)
        # Mayor diferencia = mayor confianza en la decisión
        confianza = min(1.0, diferencia * 2)  # Escala: 0 < diferencia < 0.5 = confianza 0-1
        
        estadisticas["diferencias"].append(diferencia)
        estadisticas["confianzas"].append(confianza)
        
        print(f"\n  {duelo.get('parametro', '?').upper()}")
        print(f"    Diferencia de scores: {diferencia:.4f}")
        print(f"    Confianza en decisión: {confianza:.2%}")
    
    if estadisticas["diferencias"]:
        diff_promedio = statistics.mean(estadisticas["diferencias"])
        conf_promedio = statistics.mean(estadisticas["confianzas"])
        
        print(f"\n{'='*70}")
        print("📈 ESTADÍSTICAS GENERALES:")
        print(f"{'='*70}")
        print(f"  Diferencia promedio:       {diff_promedio:.4f}")
        print(f"  Confianza promedio:        {conf_promedio:.2%}")
        
        if diff_promedio > 0.05:
            print(f"\n✅ Decisiones tomadas con BUENA MARGEN de separación")
        else:
            print(f"\n⚠️  Decisiones muy ajustadas (diferencias pequeñas)")


def main():
    # Verificar integridad
    integridad_ok = verificar_integridad_duelos()
    
    # Validar decisiones
    if integridad_ok:
        validar_decisiones()
    else:
        print("\n⚠️  Corrige los errores de integridad antes de validar decisiones")
    
    print(f"\n{'='*70}")
    print("FIN DEL TEST")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
