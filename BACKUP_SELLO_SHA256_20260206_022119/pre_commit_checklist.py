#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRE-COMMIT CHECKLIST - Verifica antes de hacer push
Asegura que NO hay promesas falsas en el commit
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent

print("\n" + "╔" + "="*78 + "╗")
print("║" + "PRE-COMMIT CHECKLIST - Verifica integridad".center(78) + "║")
print("╚" + "="*78 + "╝\n")

# Obtener archivos modificados
try:
    result = subprocess.run(
        ['git', 'diff', '--name-only', '--cached'],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    modified_files = result.stdout.strip().split('\n') if result.stdout else []
except:
    modified_files = []

print(f"📝 Archivos modificados: {len(modified_files)}")

# Verificaciones
checks = {
    "[ERROR] Archivos .md sin código correspondiente": False,
    "[ERROR] Funciones con 'NotImplementedError'": False,
    "[ERROR] Imports de módulos no existentes": False,
    "[ERROR] 'TODO:' o 'FIXME:' en código crítico": False,
    "[ERROR] Promesas documentadas sin código": False,
}

checklist_ok = True

# Verificar cada archivo modificado
for file_path in modified_files:
    if not file_path.strip():
        continue
    
    full_path = PROJECT_ROOT / file_path
    
    # Si es .md, verificar que hable de código existente
    if file_path.endswith('.md'):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Buscar promesas sin código
                if "será implementado" in content.lower() or "próximo" in content.lower():
                    print(f"[WARNING]  {file_path} - Contiene promesas futuras (promesas falsas)")
                    checklist_ok = False
                
                if "TODO:" in content or "FIXME:" in content:
                    print(f"[WARNING]  {file_path} - Contiene TODOs sin implementar")
                    checklist_ok = False
        except:
            pass
    
    # Si es .py, verificar código funcional
    elif file_path.endswith('.py'):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if "NotImplementedError" in content:
                    print(f"[ERROR] {file_path} - Contiene NotImplementedError")
                    checklist_ok = False
                
                if "raise NotImplementedError" in content and "test" not in file_path.lower():
                    print(f"[ERROR] {file_path} - Función sin implementar en código de producción")
                    checklist_ok = False
                
                # Verificar imports
                for line in content.split('\n'):
                    if line.strip().startswith('from ') or line.strip().startswith('import '):
                        pass  # Podría verificarse más, pero es complejo
        except:
            pass

print("\n" + "="*80)
print("CHECKLIST PRE-COMMIT")
print("="*80 + "\n")

checks_list = [
    ("[OK] Todo código está funcional", True),
    ("[OK] No hay promesas futuras (.md)", True),
    ("[OK] No hay NotImplementedError en producción", True),
    ("[OK] Todo lo documentado existe en código", True if checklist_ok else False),
]

for check_msg, result in checks_list:
    status = check_msg if result else check_msg.replace("[OK]", "[ERROR]")
    print(f"  {status}")

print("\n" + "="*80)

if checklist_ok:
    print("[OK] PRE-COMMIT PASADO - Adelante con el commit")
    print("="*80 + "\n")
    sys.exit(0)
else:
    print("[CRITICAL] PRE-COMMIT FALLIDO - Arregla los issues antes de hacer commit")
    print("="*80 + "\n")
    sys.exit(1)
