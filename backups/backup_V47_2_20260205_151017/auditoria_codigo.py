import logging
#!/usr/bin/env python
"""Auditoría exhaustiva de errores de código - Busca rutas, imports, nombres indefinidos"""

import os
import re
from pathlib import Path
from collections import defaultdict

def audit_code():
    """Ejecuta auditoría completa"""
    issues = {
        "archivos_corruptos": [],
        "imports_invalidos": [],
        "rutas_incorrectas": [],
        "nombres_indefinidos": [],
        "duplicados": defaultdict(list),
    }
    
    # 1. Buscar archivos con problemas obvios
    for py_file in Path(".").glob("*.py"):
        if py_file.name.startswith("CAMBIOS_") or "EXACTOS" in py_file.name:
            try:
                with open(py_file) as f:
                    content = f.read()
                    # Detectar sintaxis corrupta
                    if '"""' in content and not content.count('"""') % 2 == 0:
                        issues["archivos_corruptos"].append(str(py_file))
                    # Detectar docstrings sin función
                    if re.search(r'^\s+"""[^"]*"""$', content, re.MULTILINE):
                        issues["archivos_corruptos"].append(str(py_file))
            except:
                logging.exception("Silent except at 31 - revisar contexto")
    
    # 2. Auditar imports en tests
    test_file = Path("tests/test_auto_audit_startup.py")
    if test_file.exists():
        with open(test_file) as f:
            content = f.read()
            # Buscar imports que no existen
            imports = re.findall(r'from core\.engines\.\w+ import', content)
            for imp in imports:
                module_name = re.search(r'from core\.engines\.(\w+)', imp).group(1)
                # Verificar si existe
                if not Path(f"core/engines/{module_name}.py").exists():
                    issues["imports_invalidos"].append({
                        "file": str(test_file),
                        "import": imp,
                        "module": module_name,
                        "exists_in_root": Path(f"{module_name}.py").exists()
                    })
    
    # 3. Buscar rutas hardcodeadas inconsistentes
    for py_file in Path("core").glob("**/*.py"):
        with open(py_file) as f:
            content = f.read()
            # Buscar paths
            paths = re.findall(r'["\']([a-z_/\.]+\.py)["\']', content)
            for path in paths:
                if not Path(path).exists() and not Path("." / path).exists():
                    issues["rutas_incorrectas"].append({
                        "file": str(py_file),
                        "path": path
                    })
    
    # 4. Buscar imports duplicados
    all_imports = defaultdict(list)
    for py_file in Path(".").glob("*.py"):
        if py_file.name.startswith("test_") or py_file.name.startswith("CAMBIOS"):
            continue
        with open(py_file) as f:
            for line_no, line in enumerate(f, 1):
                if line.strip().startswith("from ") or line.strip().startswith("import "):
                    imp = line.strip()
                    all_imports[imp].append(str(py_file))
    
    for imp, files in all_imports.items():
        if len(files) > 1:
            issues["duplicados"][imp] = files
    
    return issues

if __name__ == "__main__":
    issues = audit_code()
    
    print("\n" + "="*70)
    print("AUDITORIA DE CODIGO - RESUMEN")
    print("="*70)
    
    if issues["archivos_corruptos"]:
        print(f"\n[CRITICO] Archivos corruptos: {len(issues['archivos_corruptos'])}")
        for f in issues["archivos_corruptos"]:
            print(f"  - {f}")
    
    if issues["imports_invalidos"]:
        print(f"\n[ERROR] Imports inválidos: {len(issues['imports_invalidos'])}")
        for item in issues["imports_invalidos"]:
            print(f"  - {item['file']}: {item['import']}")
            print(f"    Módulo '{item['module']}' no existe en core/engines/")
            if item['exists_in_root']:
                print(f"    Sugerencia: El módulo está en raíz como {item['module']}.py")
    
    if issues["rutas_incorrectas"]:
        print(f"\n[WARNING] Rutas incorrectas: {len(issues['rutas_incorrectas'])}")
        for item in issues["rutas_incorrectas"][:5]:
            print(f"  - {item['file']}: {item['path']}")
    
    if issues["duplicados"]:
        print(f"\n[INFO] Imports duplicados: {len(issues['duplicados'])}")
        for imp, files in list(issues["duplicados"].items())[:3]:
            print(f"  - {imp}")
            for f in files:
                print(f"    en {f}")
    
    print("\n" + "="*70)
    print("Total de issues encontrados:", sum(len(v) if isinstance(v, list) else len(v) for v in issues.values() if v))
    print("="*70)
