#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARDRAIL AUTOMÁTICO - Verificación de Integridad
Se ejecuta ANTES de cualquier operación principal
Verifica: ¿Está TODO código funcional? ¿O hay promesas falsas?
"""

import sys
import os
from pathlib import Path

# Encoding fix
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

PROJECT_ROOT = Path(__file__).parent.parent.parent

print("\n" + "="*80)
print("GUARDRAIL DE INTEGRIDAD - Verificación Rápida".center(80))
print("="*80 + "\n")

# Conceptos críticos que NUNCA pueden estar solo documentados
CONCEPTOS_CRITICOS = {
    "consumir_elite": "Bus Omnisciente",
    "punto_rocio": "Índice Científico",
    "sensacion_termica": "Índice Científico",
    "UTCI": "Índice Científico",
    "formula_hierarchy": "Jerarquía de Fórmulas",
    "SRTM": "Ubicación",
    "learning_engine": "IA",
}

# Cargar archivos Python
py_content = {}
for py_file in PROJECT_ROOT.glob("**/*.py"):
    if '__pycache__' in str(py_file) or '.venv' in str(py_file):
        continue
    try:
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            py_content[str(py_file.relative_to(PROJECT_ROOT))] = f.read().lower()
    except:
        pass

# Verificar
print(f"Verificando {len(CONCEPTOS_CRITICOS)} conceptos críticos...\n")

todos_ok = True
for concepto, categoria in CONCEPTOS_CRITICOS.items():
    encontrado = any(concepto.lower() in content for content in py_content.values())
    
    if encontrado:
        print(f"[OK] {concepto:<20} ({categoria})")
    else:
        print(f"[ERROR] {concepto:<20} ({categoria}) - ¡NO ENCONTRADO EN CÓDIGO!")
        todos_ok = False

print("\n" + "="*80)

if todos_ok:
    print("[OK] GUARDRAIL PASADO - Sistema íntegro, listo para operar")
    print("="*80 + "\n")
    sys.exit(0)
else:
    print("[CRITICAL] GUARDRAIL FALLIDO - PROMESAS DETECTADAS SIN CÓDIGO")
    print("="*80)
    print("""
ACCIÓN INMEDIATA REQUERIDA:

1. Ejecuta: python SCRIPTS_PATRULLA/AUDITORIA_EXHAUSTIVA_V3.py
2. Identifica qué está documentado sin código
3. Opción A: Implementa el código
4. Opción B: Borra la documentación falsa
5. Reintenta guardrail

El sistema NO puede operar si hay promesas sin cumplir.
""")
    print("="*80 + "\n")
    sys.exit(1)
