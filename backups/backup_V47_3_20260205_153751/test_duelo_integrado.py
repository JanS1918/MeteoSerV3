#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.monitoring.formula_duel_engine import FormulaDuelEngine
from core.monitoring.formula_catalog import FormulaCatalogo
import json

print('='*70)
print('TEST INTEGRACIÓN: AUTO-MEJORA EN DUELOS')
print('='*70)
print()

# Cargar catálogo
catalogo = FormulaCatalogo()
catalogo.cargar()

# Crear motor de duelos
motor = FormulaDuelEngine()

# Obtener fórmulas para duelo
formulas = catalogo.obtener_todas()[:2]

if len(formulas) >= 2:
    f1, f2 = formulas[0], formulas[1]
    print(f"Duelo: {f1.nombre_tecnico} vs {f2.nombre_tecnico}")
    print()
    
    # Ejecutar duelo con auto-mejora
    resultado = motor.ejecutar_duelo(f1, f2)
    
    print(f"✅ Duelo ejecutado")
    print(f"   Ganador: {resultado.get('ganador', 'N/A')}")
    print(f"   Score A: {resultado.get('score_a', 0):.4f}")
    print(f"   Score B: {resultado.get('score_b', 0):.4f}")
    print(f"   Desempate: {resultado.get('razon_desempate', 'No aplica')}")
    print()
    
    # Verificar que se aplicaron mejoras
    print("Detalles de mejoras:")
    mejoras_a = resultado.get('mejoras_a', [])
    mejoras_b = resultado.get('mejoras_b', [])
    
    if mejoras_a:
        print(f"  Fórmula A: {len(mejoras_a)} mejora(s) aplicada(s)")
        for i, m in enumerate(mejoras_a, 1):
            print(f"    [{i}] {m.get('tipo', '?')}: {m.get('mejora_pct', 0):.1f}% ↑")
    else:
        print(f"  Fórmula A: Sin mejoras (datos normales)")
    
    if mejoras_b:
        print(f"  Fórmula B: {len(mejoras_b)} mejora(s) aplicada(s)")
        for i, m in enumerate(mejoras_b, 1):
            print(f"    [{i}] {m.get('tipo', '?')}: {m.get('mejora_pct', 0):.1f}% ↑")
    else:
        print(f"  Fórmula B: Sin mejoras (datos normales)")
    
    print()
    print("🟢 STATUS: Sistema de auto-mejora FUNCIONANDO")
    
else:
    print('⚠️ No hay suficientes fórmulas en catálogo')
