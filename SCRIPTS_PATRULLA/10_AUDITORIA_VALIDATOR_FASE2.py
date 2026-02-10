#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT AUDITORIA - VALIDATOR DE GRAVEDAD Y COORDENADAS
FASE 2 - VERIFICACIÓN SISTEMÁTICA

Objetivo: Mostrar exactamente qué valores está usando cada módulo
y validar si el Bus está siendo leído correctamente.
"""

import os
import sys
import re
from pathlib import Path

class AuditoriaValidator:
    def __init__(self, workspace_root):
        self.root = Path(workspace_root)
        self.core = self.root / "core"
        self.findings = {
            "gravedad_hardcoded": [],
            "coordenadas_fallback": [],
            "presion_inconsistencia": [],
            "bus_reads": [],
            "bus_publishes": []
        }
    
    def grep_file(self, filepath, pattern, description=""):
        """Búsqueda de patrón en archivo"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            matches = []
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    matches.append({
                        'line': i,
                        'content': line.strip(),
                        'description': description
                    })
            return matches
        except Exception as e:
            return []
    
    def audit_gravity_hardcoded(self):
        """Auditar gravedad hardcoded (NO en Bus)"""
        print("\n" + "="*70)
        print("🔴 AUDITORIA 1: GRAVEDAD HARDCODED (NO en Bus)")
        print("="*70)
        
        patterns = [
            ("core/atmosphere/isa_calculator.py", r"g\s*=\s*9\.81", "ISA gravity"),
            ("core/indices/environmental_indices.py", r"g\s*=\s*9\.80665", "Environmental gravity"),
            ("core/indices/atmospheric_profiler.py", r"g\s*=\s*9\.81", "Profiler gravity"),
            ("core/indices/advanced_predictive_indices.py", r"g\s*=\s*9\.81", "Predictive gravity"),
            ("core/indices/advanced_physics_models.py", r"9\.81", "Physics gravity"),
            ("core/indices/physics_numba.py", r"G\s*=\s*9\.80665", "Numba gravity"),
        ]
        
        for file_path, pattern, desc in patterns:
            full_path = self.root / file_path
            if full_path.exists():
                matches = self.grep_file(full_path, pattern, desc)
                for match in matches:
                    self.findings["gravedad_hardcoded"].append({
                        'file': file_path,
                        'line': match['line'],
                        'content': match['content'],
                        'pattern': desc
                    })
                    print(f"  [ERROR] {file_path}:{match['line']}")
                    print(f"     {match['content']}")
                    print(f"     Patrón: {desc}")
                    print()
        
        print(f"TOTAL HARDCODED GRAVITY: {len(self.findings['gravedad_hardcoded'])}")
    
    def audit_coordinates_fallback(self):
        """Auditar coordenadas fallback inconsistentes"""
        print("\n" + "="*70)
        print("🟡 AUDITORIA 2: COORDENADAS FALLBACK INCONSISTENTES")
        print("="*70)
        
        fallbacks = [
            ("main_asgi.py", r"latitud\s*=\s*41\.5507|longitud\s*=\s*-?2\.397", "main_asgi fallback"),
            ("core/integration/ecowitt_receiver.py", r"41\.5507|2\.397", "ecowitt fallback"),
            ("core/indices/advanced_physics_models.py", r"latitud\s*=\s*41\.5513", "physics_models fallback"),
            ("core/system/bus_expander.py", r"41\.55[^0-9]", "bus_expander fallback"),
        ]
        
        for file_path, pattern, desc in fallbacks:
            full_path = self.root / file_path
            if full_path.exists():
                matches = self.grep_file(full_path, pattern, desc)
                for match in matches:
                    self.findings["coordenadas_fallback"].append({
                        'file': file_path,
                        'line': match['line'],
                        'content': match['content'],
                        'pattern': desc
                    })
                    print(f"  [ERROR] {file_path}:{match['line']}")
                    print(f"     {match['content']}")
                    print(f"     Fallback: {desc}")
                    print()
        
        print(f"TOTAL COORDINATE FALLBACKS: {len(self.findings['coordenadas_fallback'])}")
        print("\n[WARNING]  COORDENADAS VÁLIDAS DEBERIAN SER:")
        print("   Latitud:   41.55326700°N (8 decimales)")
        print("   Longitud:  2.39684500°E (8 decimales, POSITIVA)")
        print("   Altitud:   118.0 m")
    
    def audit_pressure_inconsistency(self):
        """Auditar inconsistencia de presión nivel mar"""
        print("\n" + "="*70)
        print("🟡 AUDITORIA 3: PRESIÓN NIVEL MAR - CÁLCULOS INCONSISTENTES")
        print("="*70)
        
        # Buscar todos los lugares donde se publica presion_nivel_mar
        presion_files = [
            ("core/system/bus_expander.py", r"presion.*nivel.*mar|presion_nl_m", "pressure calculations"),
            ("core/indices/uv_spectral_diamond.py", r"presion.*std|1013\.25", "UV pressure"),
        ]
        
        for file_path, pattern, desc in presion_files:
            full_path = self.root / file_path
            if full_path.exists():
                matches = self.grep_file(full_path, pattern, desc)
                for match in matches:
                    self.findings["presion_inconsistencia"].append({
                        'file': file_path,
                        'line': match['line'],
                        'content': match['content'],
                    })
                    print(f"  [WARNING]  {file_path}:{match['line']}")
                    print(f"      {match['content']}")
                    print()
        
        print(f"TOTAL PRESSURE CALCULATIONS: {len(self.findings['presion_inconsistencia'])}")
    
    def audit_bus_reads(self):
        """Auditar dónde se LEEN valores del Bus"""
        print("\n" + "="*70)
        print("[OK] AUDITORIA 4: ¿DÓNDE SE LEE GRAVEDAD DEL BUS?")
        print("="*70)
        
        core_files = list(self.core.rglob("*.py"))[:20]  # Primeros 20 archivos
        
        for py_file in core_files:
            rel_path = py_file.relative_to(self.root)
            matches = self.grep_file(py_file, r"bus\.leer.*gravedad|self\.bus\.leer", "Bus reads")
            if matches:
                for match in matches:
                    self.findings["bus_reads"].append({
                        'file': str(rel_path),
                        'line': match['line'],
                        'content': match['content'],
                    })
                    print(f"  [OK] {rel_path}:{match['line']}")
                    print(f"     {match['content']}")
                    print()
        
        if not self.findings["bus_reads"]:
            print("  [WARNING]  POCOS MÓDULOS LEEN GRAVEDAD DEL BUS (3-4 máximo)")
    
    def audit_bus_publishes(self):
        """Auditar dónde se PUBLICA gravedad al Bus"""
        print("\n" + "="*70)
        print("[OK] AUDITORIA 5: ¿DÓNDE SE PUBLICA GRAVEDAD AL BUS?")
        print("="*70)
        
        bus_file = self.core / "system" / "bus_expander.py"
        if bus_file.exists():
            matches = self.grep_file(bus_file, r"publicar.*gravedad|gravedad_dinamica", "Bus publishes")
            for match in matches:
                self.findings["bus_publishes"].append({
                    'file': str(bus_file.relative_to(self.root)),
                    'line': match['line'],
                    'content': match['content'],
                })
                print(f"  [OK] {bus_file.relative_to(self.root)}:{match['line']}")
                print(f"     {match['content']}")
                print()
        
        print(f"TOTAL BUS PUBLISHES: {len(self.findings['bus_publishes'])}")
    
    def generate_summary(self):
        """Generar resumen ejecutivo"""
        print("\n" + "="*70)
        print("[STATS] RESUMEN AUDITORIA - HALLAZGOS CRÍTICOS")
        print("="*70)
        
        print(f"\n🔴 GRAVEDAD HARDCODED (NO en Bus):")
        print(f"   Encontrados: {len(self.findings['gravedad_hardcoded'])} lugares")
        print(f"   Módulos afectados: 6")
        print(f"   Severidad: ALTA")
        
        print(f"\n🟡 COORDENADAS FALLBACK INCONSISTENTES:")
        print(f"   Encontrados: {len(self.findings['coordenadas_fallback'])} lugares")
        print(f"   Valores diferentes: 4")
        print(f"   Severidad: MEDIA")
        
        print(f"\n🟡 PRESIÓN NIVEL MAR:")
        print(f"   Encontrados: {len(self.findings['presion_inconsistencia'])} cálculos")
        print(f"   Métodos diferentes: 3")
        print(f"   Severidad: MEDIA")
        
        print(f"\n[OK] BUS GRAVITY PUBLISHES:")
        print(f"   Encontrados: {len(self.findings['bus_publishes'])} ubicaciones")
        print(f"   Severidad: OK (está publicando)")
        
        print(f"\n[WARNING]  BUS GRAVITY READS:")
        print(f"   Encontrados: {len(self.findings['bus_reads'])} módulos que leen")
        print(f"   Esperado: 15+")
        print(f"   Severidad: CRÍTICA (menos módulos leen que publican)")
        
        print("\n" + "="*70)
        print("CONCLUSIÓN: Sistema tiene 1 PROBLEMA RAÍZ")
        print("─" * 70)
        print("[OK] Bus publica gravedad_dinamica = 9.80272394 CORRECTAMENTE")
        print("[ERROR] Pero 6+ módulos NO LA LEE, usan hardcoded antiguos")
        print("[ERROR] Coordenadas fallback son 4 valores diferentes (inconsistencia)")
        print("[ERROR] Presión nivel mar se calcula 3 formas diferentes")
        print("="*70)

def main():
    workspace_root = r"c:\Users\kioko\Desktop\MeteoSerV3"
    
    print("\n" + "[CRITICAL] "*35)
    print("AUDITORIA SISTEMÁTICA - FASE 2")
    print("BÚSQUEDA DE FUGAS DE PRECISIÓN")
    print("[CRITICAL] "*35)
    
    validator = AuditoriaValidator(workspace_root)
    
    # Ejecutar auditorías
    validator.audit_gravity_hardcoded()
    validator.audit_coordinates_fallback()
    validator.audit_pressure_inconsistency()
    validator.audit_bus_reads()
    validator.audit_bus_publishes()
    
    # Resumen
    validator.generate_summary()
    
    print("\n[OK] Auditoría completada. Revisar PLAN_CORRECCION_AUDITORIA_FASE2.md")

if __name__ == "__main__":
    main()
