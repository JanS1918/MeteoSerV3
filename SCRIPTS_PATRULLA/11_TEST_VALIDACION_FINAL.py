#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DE COHERENCIA - UNIFICACION DE HIERRO V27.0 VALIDACION
"""

import sys
import re
from pathlib import Path

class TestCoherencia:
    def __init__(self, workspace_root):
        self.root = Path(workspace_root)
        self.errors = []
        self.successes = []
    
    def test_all(self):
        print("\n" + "="*70)
        print("VALIDACION: UNIFICACION DE HIERRO V27.0")
        print("="*70 + "\n")
        
        # Test 1: constants.py existe
        const_file = self.root / "core/system/constants.py"
        if const_file.exists():
            content = const_file.read_text(encoding='utf-8', errors='ignore')
            if "41.55326700" in content and "9.80272394" in content:
                self.successes.append("constants.py: Valores correctos")
            else:
                self.errors.append("constants.py: Valores incorrectos")
        else:
            self.errors.append("constants.py: NO EXISTE")
        
        # Test 2: No hay gravedad hardcoded antigua en módulos críticos
        files_to_check = [
            "core/atmosphere/isa_calculator.py",
            "core/indices/atmospheric_profiler.py",
            "core/indices/advanced_predictive_indices.py",
            "core/indices/advanced_physics_models.py",
            "core/indices/environmental_indices.py",
        ]
        
        for file_path in files_to_check:
            full_path = self.root / file_path
            if full_path.exists():
                content = full_path.read_text(encoding='utf-8', errors='ignore')
                # Buscar gravedad hardcoded antigua
                if re.search(r'\bg\s*=\s*9\.81\b', content) or re.search(r'\bg\s*=\s*9\.80665\b', content):
                    self.errors.append(f"{file_path}: Aun tiene gravedad hardcoded")
                else:
                    self.successes.append(f"{file_path}: UNIFICADO")
        
        # Test 3: Presion nivel mar publicada UNA sola vez
        bus_file = self.root / "core/system/bus_expander.py"
        if bus_file.exists():
            content = bus_file.read_text(encoding='utf-8', errors='ignore')
            count = content.count('publicar("presion_nivel_mar"')
            if count == 1:
                self.successes.append(f"bus_expander: presion_nivel_mar publicada 1 vez")
            else:
                self.errors.append(f"bus_expander: presion_nivel_mar publicada {count} veces")
        
        # Reporte final
        print("\n" + "="*70)
        print("REPORTE FINAL")
        print("="*70)
        
        print(f"\nEXITOS: {len(self.successes)}")
        for msg in self.successes:
            print(f"  [OK] {msg}")
        
        if self.errors:
            print(f"\nERRORES: {len(self.errors)}")
            for msg in self.errors:
                print(f"  [!!] {msg}")
            print("\nVERDICTO: FALLO")
            return False
        else:
            print("\n" + "="*70)
            print("VEREDICTO: UNIFICACION EXITOSA - SISTEMA EN SOBERANIA TOTAL")
            print("="*70)
            return True

def main():
    workspace = r"c:\Users\kioko\Desktop\MeteoSerV3"
    validator = TestCoherencia(workspace)
    success = validator.test_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
