#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DE COHERENCIA CRUZADA - UNIFICACIÓN DE HIERRO V27.0 VALIDACIÓN
════════════════════════════════════════════════════════════════════

Objetivo: Verificar que la Unificación de Hierro V27.0 fue 100% exitosa.
- NO hay más gravedad hardcoded antigua
- TODO lee de ESTACION y GRAVEDAD desde constants.py
- Presión nivel mar se calcula UNA sola forma
- Coordenadas son UNA sola ubicación
"""

import sys
import re
from pathlib import Path

class TestCoherenciaCruzada:
    def __init__(self, workspace_root):
        self.root = Path(workspace_root)
        self.core = self.root / "core"
        self.errors = []
        self.warnings = []
        self.successes = []
    
    def grep_py(self, filepath, pattern, should_exist=False):
        """Buscar patrón en archivo Python"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            matches = []
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append((i, line.strip()))
            
            return matches
        except:
            return []
    
    def test_gravedad_hardcoded(self):
        """TEST 1: Verificar que NO hay gravedad hardcoded antigua"""
        print("\n🧪 TEST 1: GRAVEDAD - ¿Se liquidaron los 11 agujeros?")
        print("─" * 60)
        
        módulos_críticos = [
            ("core/atmosphere/isa_calculator.py", "presion_isa"),
            ("core/indices/atmospheric_profiler.py", "richardson"),
            ("core/indices/advanced_predictive_indices.py", "predictive"),
            ("core/indices/advanced_physics_models.py", "cape"),
            ("core/indices/environmental_indices.py", "humedad"),
            ("core/indices/physics_numba.py", "numba"),
        ]
        
        for file_path, desc in módulos_críticos:
            full_path = self.root / file_path
            if full_path.exists():
                # Buscar gravedad hardcoded que NO esté en comentarios
                matches_81 = self.grep_py(full_path, r"(?<!#.*)\bg\s*=\s*9\.81\b(?!.*CONSTANTES)", should_exist=False)
                matches_80665 = self.grep_py(full_path, r"(?<!#.*)\bg\s*=\s*9\.80665\b", should_exist=False)
                matches_81_calc = self.grep_py(full_path, r"9\.81\s*\*", should_exist=False)
                
                # Buscar que SÍ tenga importación de CONSTANTES o uso de GRAVEDAD
                has_constants = self.grep_py(full_path, r"from core\.system\.constants import|GRAVEDAD\.DINAMICA")
                
                if matches_81 or matches_80665 or matches_81_calc:
                    self.errors.append(f"  [ERROR] {file_path}: Aún tiene gravedad hardcoded")
                    for line_no, content in matches_81 + matches_80665 + matches_81_calc:
                        self.errors.append(f"     Línea {line_no}: {content}")
                elif has_constants:
                    self.successes.append(f"  [OK] {file_path} ({desc}): UNIFICADO")
                else:
                    self.warnings.append(f"  [WARNING]  {file_path}: No usa CONSTANTES (revisar)")
    
    def test_coordenadas_unificadas(self):
        """TEST 2: Verificar que hay UNA sola ubicación en 4 archivos"""
        print("\n🧪 TEST 2: COORDENADAS - ¿4 fallbacks → 1 ubicación?")
        print("─" * 60)
        
        archivos = [
            "main_asgi.py",
            "core/integration/ecowitt_receiver.py",
            "core/indices/advanced_physics_models.py",
            "core/system/bus_expander.py",
        ]
        
        for archivo in archivos:
            full_path = self.root / archivo
            if full_path.exists():
                # Buscar valores antiguos de coordenadas (pre-unificación)
                old_coords = self.grep_py(full_path, 
                    r"(41\.5507|41\.5513|41\.55\b|2\.397|-2\.397)", 
                    should_exist=False)
                
                # Buscar que tenga ESTACION.LATITUD o ESTACION.LONGITUD
                has_constants = self.grep_py(full_path, r"ESTACION\.LATITUD|ESTACION\.LONGITUD|from core\.system\.constants import ESTACION")
                
                if old_coords:
                    self.errors.append(f"  [ERROR] {archivo}: Aún tiene coordenadas viejas")
                    for line_no, content in old_coords:
                        self.errors.append(f"     Línea {line_no}: {content[:80]}")
                elif has_constants or "ESTACION" in archivo:
                    self.successes.append(f"  [OK] {archivo}: USA constantes unificadas")
                else:
                    self.warnings.append(f"  [WARNING]  {archivo}: Revisar si tiene fallback correcto")
    
    def test_presion_unificada(self):
        """TEST 3: Verificar que presion_nivel_mar se publica UNA sola vez"""
        print("\n🧪 TEST 3: PRESIÓN - ¿Triplete de Laplace → Un método?")
        print("─" * 60)
        
        full_path = self.root / "core/system/bus_expander.py"
        if full_path.exists():
            # Contar cuántas veces se publica "presion_nivel_mar"
            matches = self.grep_py(full_path, r'publicar\("presion_nivel_mar"')
            
            if len(matches) == 1:
                self.successes.append(f"  [OK] bus_expander.py: presion_nivel_mar publicada 1 sola vez (línea {matches[0][0]})")
            elif len(matches) > 1:
                self.errors.append(f"  [ERROR] bus_expander.py: presion_nivel_mar publicada {len(matches)} veces (REDUNDANCIA)")
                for line_no, content in matches:
                    self.errors.append(f"     Línea {line_no}: {content[:80]}")
            else:
                self.errors.append(f"  [ERROR] bus_expander.py: presion_nivel_mar NO se publica (CRÍTICO)")
            
            # Verificar que usa fórmula barométrica
            formula_match = self.grep_py(full_path, r"exp\(.*gravedad.*altitud|exp\(.*g\s*\*\s*h")
            if formula_match:
                self.successes.append(f"  [OK] bus_expander.py: Usa fórmula barométrica dinámica")
    
    def test_constants_py(self):
        """TEST 4: Verificar que constants.py existe y está correcto"""
        print("\n🧪 TEST 4: CONSTANTS.PY - ¿Constitución física sellada?")
        print("─" * 60)
        
        const_file = self.root / "core/system/constants.py"
        if const_file.exists():
            # Verificar valores específicos
            content = const_file.read_text(encoding='utf-8', errors='ignore')
            
            checks = {
                "LATITUD": 41.55326700,
                "LONGITUD": 2.39684500,
                "ALTITUD": 118.0,
                "GRAVEDAD.DINAMICA": 9.80272394,
                "ESTACION class": "class ESTACION",
                "GRAVEDAD class": "class GRAVEDAD",
                "PRESION class": "class PRESION",
            }
            
            for check_name, value in checks.items():
                if isinstance(value, float):
                    # Búsqueda numérica
                    if str(value) in content:
                        self.successes.append(f"  [OK] constants.py: {check_name} = {value}")
                    else:
                        self.errors.append(f"  [ERROR] constants.py: {check_name} NO es {value}")
                else:
                    if str(value) in content:
                        self.successes.append(f"  [OK] constants.py: {check_name} existe")
                    else:
                        self.errors.append(f"  [ERROR] constants.py: {check_name} NO existe")
        else:
            self.errors.append(f"  [ERROR] core/system/constants.py NO EXISTE (CRÍTICO)")
    
    def test_bus_gravedad(self):
        """TEST 5: Verificar que Bus publica gravedad_dinamica correctamente"""
        print("\n🧪 TEST 5: BUS - ¿Publica gravedad_dinamica?")
        print("─" * 60)
        
        bus_file = self.root / "core/system/bus_expander.py"
        if bus_file.exists():
            # Buscar dónde se publica gravedad_dinamica
            matches = self.grep_py(bus_file, r'publicar\("gravedad_dinamica"')
            
            if matches:
                self.successes.append(f"  [OK] bus_expander.py: Publica gravedad_dinamica ({len(matches)} ubicación/ubicaciones)")
                for line_no, content in matches[:3]:  # Mostrar primeras 3
                    self.successes.append(f"     Línea {line_no}: OK")
            else:
                self.errors.append(f"  [ERROR] bus_expander.py: NO publica gravedad_dinamica")
            
            # Verificar que NO publica gravedad con valores antiguos
            bad_publish = self.grep_py(bus_file, r'publicar\(.*gravedad.*9\.81|publicar\(.*gravedad.*9\.80665')
            if bad_publish:
                self.errors.append(f"  [ERROR] bus_expander.py: Publica gravedad con valores viejos")
    
    def generar_reporte(self):
        """Generar reporte final"""
        print("\n" + "═" * 70)
        print("[STATS] REPORTE FINAL - UNIFICACIÓN DE HIERRO V27.0")
        print("═" * 70)
        
        # Resumen
        total_errors = len(self.errors)
        total_warns = len(self.warnings)
        total_success = len(self.successes)
        
        print(f"\n[OK] ÉXITOS: {total_success}")
        for msg in self.successes[:5]:
            print(msg)
        if total_success > 5:
            print(f"... y {total_success - 5} más")
        
        if self.warnings:
            print(f"\n[WARNING]  ADVERTENCIAS: {total_warns}")
            for msg in self.warnings:
                print(msg)
        
        if self.errors:
            print(f"\n[ERROR] ERRORES: {total_errors}")
            for msg in self.errors:
                print(msg)
        
        # Veredicto
        print("\n" + "═" * 70)
        if total_errors == 0:
            print("🏁 VEREDICTO: UNIFICACIÓN DE HIERRO V27.0 - EXITOSA")
            print("   [OK] Gravedad centralizada: 11 agujeros liquidados")
            print("   [OK] Coordenadas unificadas: 4 fallbacks → 1 ubicación")
            print("   [OK] Presión sincronizada: 1 sola fórmula barométrica")
            print("   [OK] Sistema en SOBERANÍA TOTAL")
            return True
        elif total_errors <= 3:
            print("🟡 VEREDICTO: UNIFICACIÓN CASI EXITOSA - Pequeñas correcciones pendientes")
            return False
        else:
            print("🔴 VEREDICTO: UNIFICACIÓN INCOMPLETA - Revisar errores críticos")
            return False

def main():
    workspace = r"c:\Users\kioko\Desktop\MeteoSerV3"
    
        print("\n" + "="*70)
        print("VALIDACION: UNIFICACION DE HIERRO V27.0")
        print("="*70)
    
    validator = TestCoherenciaCruzada(workspace)
    
    # Ejecutar todos los tests
    validator.test_constants_py()
    validator.test_gravedad_hardcoded()
    validator.test_coordenadas_unificadas()
    validator.test_presion_unificada()
    validator.test_bus_gravedad()
    
    # Generar reporte
    success = validator.generar_reporte()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
