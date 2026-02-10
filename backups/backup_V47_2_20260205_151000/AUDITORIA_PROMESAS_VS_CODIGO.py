#!/usr/bin/env python3
"""
AUDITORIA TOTAL: Busca promesas sin código en TODOS los archivos
Identifica funciones/métodos que dicen qué hacen pero no lo hacen
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = r"C:\Users\kioko\Desktop\MeteoSerV3"
IGNORE_DIRS = {'.venv', '__pycache__', '.git', 'backups', 'logs', 'data', 'static', 'docs', '.pytest_cache'}

class PromiseDetector:
    def __init__(self):
        self.findings = defaultdict(list)
        self.promises_without_code = []
        
    def is_stub_or_incomplete(self, func_body):
        """Detecta si una función es stub (sin código real)"""
        # Solo tiene pass, docstring, o raise NotImplementedError
        non_doc_lines = [
            line.strip() for line in func_body.split('\n') 
            if line.strip() and not line.strip().startswith('#')
        ]
        
        stub_indicators = [
            any('pass' in line for line in non_doc_lines),
            any('NotImplementedError' in line for line in non_doc_lines),
            any('TODO' in line.upper() for line in non_doc_lines),
            any('FIXME' in line.upper() for line in non_doc_lines),
            len([l for l in non_doc_lines if l and not l.startswith('"""') and not l.startswith("'''")]) <= 2
        ]
        return any(stub_indicators)
    
    def analyze_file(self, filepath):
        """Analiza un archivo Python en busca de promesas sin código"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"[!] Error leyendo {filepath}: {e}")
            return
        
        # Buscar patterns de promesas
        promises = [
            r'def\s+(\w+)\s*\([^)]*\)[^:]*:.*?"""([^"]{10,})"""',  # Funciones con docstring promesa
            r'def\s+(\w+)\s*\([^)]*\)[^:]*:.*?\'\'\'([^\']{{10,}})\'\'\'',  # Con triple comillas simples
            r'raise\s+NotImplementedError\(["\']([^"\']+)',  # NotImplementedError con mensaje
            r'#\s*TODO[:\s]+([^\n]+)',  # TODOs
            r'#\s*FIXME[:\s]+([^\n]+)',  # FIXMEs
        ]
        
        # Buscar funciones que son solo pass o docstring
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Obtener el cuerpo de la función
                    if len(node.body) <= 2:  # Solo docstring + pass
                        docstring = ast.get_docstring(node)
                        if docstring and len(docstring) > 20:
                            self.promises_without_code.append({
                                'file': filepath,
                                'function': node.name,
                                'type': 'stub_with_docstring',
                                'docstring': docstring[:100]
                            })
                    
                    # Verificar si tiene NotImplementedError
                    for child in ast.walk(node):
                        if isinstance(child, ast.Raise):
                            if isinstance(child.exc, ast.Call):
                                if hasattr(child.exc.func, 'id'):
                                    if 'NotImplementedError' in child.exc.func.id:
                                        self.promises_without_code.append({
                                            'file': filepath,
                                            'function': node.name,
                                            'type': 'not_implemented',
                                            'docstring': ast.get_docstring(node) or 'Sin docstring'
                                        })
        except SyntaxError as e:
            self.promises_without_code.append({
                'file': filepath,
                'type': 'syntax_error',
                'message': str(e)
            })
        
        # Buscar TODOs y FIXMEs
        for match in re.finditer(r'#\s*(TODO|FIXME)[:\s]+([^\n]+)', content):
            marker, message = match.groups()
            self.promises_without_code.append({
                'file': filepath,
                'marker': marker,
                'type': 'comment_marker',
                'message': message.strip()
            })
    
    def scan_project(self):
        """Escanea TODO el proyecto"""
        print("[*] Escaneando proyecto completo...")
        file_count = 0
        
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, PROJECT_ROOT)
                    file_count += 1
                    self.analyze_file(filepath)
        
        print(f"[OK] Escaneados {file_count} archivos Python")
        return self.promises_without_code
    
    def report(self):
        """Genera reporte de hallazgos"""
        if not self.promises_without_code:
            print("[OK] No se encontraron promesas sin código")
            return
        
        print(f"\n[!] TOTAL DE PROMESAS SIN CÓDIGO: {len(self.promises_without_code)}")
        print("=" * 80)
        
        # Agrupar por tipo
        by_type = defaultdict(list)
        for item in self.promises_without_code:
            by_type[item.get('type', 'unknown')].append(item)
        
        for typ, items in by_type.items():
            print(f"\n[{typ.upper()}] {len(items)} hallazgos:")
            for item in items[:5]:  # Mostrar primeros 5
                filepath = os.path.relpath(item['file'], PROJECT_ROOT)
                if 'function' in item:
                    print(f"  - {filepath}::{item['function']}")
                    print(f"    -> {item.get('docstring', item.get('message', ''))[:80]}")
                else:
                    print(f"  - {filepath}")
                    print(f"    -> {item.get('message', '')[:80]}")
            if len(items) > 5:
                print(f"  ... y {len(items) - 5} más")

if __name__ == '__main__':
    detector = PromiseDetector()
    detector.scan_project()
    detector.report()
    
    # Exportar resultados a archivo
    with open('PROMESAS_SIN_CODIGO.txt', 'w', encoding='utf-8') as f:
        for item in detector.promises_without_code:
            f.write(f"{item['file']}\n")
            f.write(f"  Tipo: {item.get('type')}\n")
            if 'function' in item:
                f.write(f"  Función: {item['function']}\n")
            if 'message' in item:
                f.write(f"  Mensaje: {item['message']}\n")
            f.write(f"  Details: {item.get('docstring', '')}\n\n")
    
    print("\n[*] Resultados guardados en PROMESAS_SIN_CODIGO.txt")
