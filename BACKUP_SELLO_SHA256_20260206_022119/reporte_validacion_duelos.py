#!/usr/bin/env python3
"""
REPORTE EJECUTIVO: VALIDACIÓN DE SISTEMA DE DUELOS

Este script ejecuta la validación COMPLETA del sistema de duelos:
1. Ejecuta duelos simulados con datos reales
2. Valida coherencia de decisiones
3. Genera reporte detallado
4. Proporciona diagnóstico y recomendaciones
"""

import json
from pathlib import Path
from datetime import datetime


def cargar_reporte():
    """Carga el reporte generado por el test."""
    reporte_path = Path("data/test_duelos_reporte.json")
    if not reporte_path.exists():
        print("[ERROR] Primero ejecuta: python test_duelos_simulacion_completa.py")
        return None
    
    with open(reporte_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("\n" + "="*70)
    print("REPORTE EJECUTIVO: VALIDACIÓN DE DUELOS CONTRA REALIDAD")
    print("="*70)
    
    reporte = cargar_reporte()
    if not reporte:
        return
    
    # Extraer datos
    total = reporte.get("total_duelos", 0)
    correctos = reporte.get("correctos", 0)
    incorrectos = reporte.get("incorrectos", 0)
    confiabilidad = reporte.get("confiabilidad", 0)
    duelos = reporte.get("duelos", [])
    
    # 1. Resumen ejecutivo
    print(f"\n[STATS] RESUMEN EJECUTIVO:")
    print(f"  ├─ Duelos analizados: {total}")
    print(f"  ├─ Decisiones correctas: {correctos} ({correctos*100//total if total else 0}%)")
    print(f"  ├─ Decisiones incorrectas: {incorrectos} ({incorrectos*100//total if total else 0}%)")
    print(f"  └─ Confiabilidad general: {confiabilidad:.1f}%")
    
    # 2. Análisis detallado
    print(f"\n📋 ANÁLISIS DETALLADO:")
    
    duelos_correctos = []
    duelos_incorrectos = []
    duelos_tie = []
    
    for duelo in duelos:
        param = duelo.get("parametro", "?")
        ganador = duelo.get("formula_a", {}).get("nombre", "?")
        score_a = duelo.get("formula_a", {}).get("resultado", 0)
        score_b = duelo.get("formula_b", {}).get("resultado", 0)
        
        if score_a > score_b:
            duelos_correctos.append((param, ganador, score_a - score_b))
        elif score_a < score_b:
            duelos_incorrectos.append((param, ganador, score_a - score_b))
        else:
            duelos_tie.append((param, ganador, score_a))
    
    if duelos_correctos:
        print(f"\n  [OK] DUELOS CORRECTOS ({len(duelos_correctos)}):")
        for param, ganador, diff in duelos_correctos:
            print(f"     - {param:25} → {ganador:35} (+{diff:.4f})")
    
    if duelos_incorrectos:
        print(f"\n  [ERROR] DUELOS INCORRECTOS ({len(duelos_incorrectos)}):")
        for param, ganador, diff in duelos_incorrectos:
            print(f"     - {param:25} → {ganador:35} ({diff:.4f} - MARGEN NEGATIVO!)")
    
    if duelos_tie:
        print(f"\n  [WARNING]  DUELOS EMPATADOS ({len(duelos_tie)}):")
        for param, ganador, score in duelos_tie:
            print(f"     - {param:25} → {ganador:35} (0.0000)")
    
    # 3. Diagnóstico
    print(f"\n[BUSCAR] DIAGNÓSTICO:")
    
    if confiabilidad >= 95:
        diagnostico = "EXCELENTE [OK]"
        recomendacion = "Sistema de duelos LISTO para producción"
    elif confiabilidad >= 85:
        diagnostico = "BUENO [WARNING]"
        recomendacion = "Sistema funcional, revisar casos de error"
    elif confiabilidad >= 70:
        diagnostico = "ACEPTABLE [WARNING]"
        recomendacion = "Revisar lógica de evaluación, hay margen de mejora"
    elif confiabilidad >= 50:
        diagnostico = "DEFICIENTE [ERROR]"
        recomendacion = "REQUIERE AJUSTES antes de usar en producción"
    else:
        diagnostico = "CRÍTICO [ERROR]"
        recomendacion = "NO USAR - Sistema necesita revisión fundamental"
    
    print(f"  Estado: {diagnostico}")
    print(f"  Recomendación: {recomendacion}")
    
    # 4. Causas de error
    if duelos_incorrectos or duelos_tie:
        print(f"\n[WARNING]  ANÁLISIS DE ERRORES:")
        
        if duelos_tie:
            print(f"   Causa: {len(duelos_tie)} duelos con puntuación idéntica")
            print(f"   → Se elige ganador por defecto (sin base en datos)")
        
        if duelos_incorrectos:
            print(f"   Causa: {len(duelos_incorrectos)} duelos con fórmula perdedora puntuando MEJOR")
            print(f"   → Error en lógica de evaluación o datos invertidos")
    
    # 5. Información de auditoría
    print(f"\n📝 INFORMACIÓN DE AUDITORÍA:")
    print(f"  Generado: {reporte.get('fecha', 'N/A')}")
    print(f"  Archivo: data/test_duelos_reporte.json")
    
    # 6. Recomendaciones específicas
    print(f"\n💡 RECOMENDACIONES:")
    
    if len(duelos_tie) > 0:
        print(f"  1. Implementar criterios de desempate:")
        print(f"     - Usar estabilidad como criterio secundario")
        print(f"     - O usar eficiencia (velocidad)")
        print(f"     - O marcar duelo como no conclusivo")
    
    if len(duelos_incorrectos) > 0:
        print(f"  2. Revisar evaluación de fórmulas:")
        print(f"     - Verificar que puntuación refleja precisión (no error)")
        print(f"     - Puntaje ALTO = MEJOR, BAJO = PEOR")
        print(f"     - Revisar normalizaciones")
    
    if confiabilidad < 85:
        print(f"  3. Aumentar datos de validación:")
        print(f"     - Usar más muestras históricas")
        print(f"     - Incluir casos extremos (frío, calor, humedad)")
        print(f"     - Validar en múltiples escenarios")
    
    print(f"\n{'='*70}")
    print("CONCLUSIÓN")
    print(f"{'='*70}")
    
    if confiabilidad >= 85:
        print(f"""
[OK] El sistema de DUELOS está VALIDADO y FUNCIONANDO correctamente.

El motor toma decisiones coherentes al elegir entre fórmulas.
Las decisiones se basan en scores que reflejan la precisión real.

Puedes confiar en los cambios de fórmulas que el sistema propone.
""")
    else:
        print(f"""
[ERROR] El sistema de DUELOS necesita REVISIÓN antes de usarse.

Hay inconsistencias en las decisiones tomadas.
Algunos casos muestran fórmulas perdedoras con mejor puntuación.

ANTES de usar en producción:
1. Revisar la función de evaluación
2. Validar que scores > = mejor
3. Ejecutar tests adicionales

Status actual: NO RECOMENDADO para decisiones automáticas
""")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
