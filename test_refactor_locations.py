#!/usr/bin/env python3
"""
Test: Validación de que las refactorizaciones específicas están en lugar correcto
"""

import re
import sys

def check_refactoring():
    """Verifica que los helpers se usen en las líneas refacturizadas"""
    
    with open('core/system/bus_expander.py', 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    print("\n=== VALIDACIÓN DE REFACTORIZACIÓN ===\n")
    
    # Definimos las líneas y patrones esperados
    validations = [
        (2881, "get_float(loc,", "Line 2881: altitud extraction"),
        (2893, "get_float(cape_result,", "Line 2893: CAPE extraction"),
        (2982, "clamp_percent(get_float(sev,", "Line 2982: Storm probability"),
        (2998, "clamp_percent(get_float(sundq,", "Line 2998: Rain probability"),
        (5269, "get_float(uv_result,", "Line 5269: UV index extraction"),
    ]
    
    all_passed = True
    
    for line_num, expected_pattern, description in validations:
        actual_line = lines[line_num - 1].strip()  # -1 porque arrays son 0-indexed
        
        if expected_pattern in actual_line:
            print(f"[✅] {description}")
            print(f"     {actual_line[:80]}...")
        else:
            print(f"[❌] {description}")
            print(f"     Expected pattern: {expected_pattern}")
            print(f"     Found: {actual_line[:80]}...")
            all_passed = False
        print()
    
    # Verificar que los helpers existen
    print("=== VALIDACIÓN DE HELPERS ===\n")
    
    helpers_to_find = [
        ("def get_float", "Helper: get_float()"),
        ("def get_int", "Helper: get_int()"),
        ("def clamp_percent", "Helper: clamp_percent()"),
        ("def clamp_unit", "Helper: clamp_unit()"),
    ]
    
    content = ''.join(lines)
    
    for pattern, description in helpers_to_find:
        if pattern in content:
            print(f"[✅] {description} encontrado")
        else:
            print(f"[❌] {description} NO encontrado")
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ TODAS LAS REFACTORIZACIONES VALIDADAS CORRECTAMENTE")
        print("="*70)
        return 0
    else:
        print("❌ ERRORES EN VALIDACIÓN")
        print("="*70)
        return 1

if __name__ == "__main__":
    exit(check_refactoring())
