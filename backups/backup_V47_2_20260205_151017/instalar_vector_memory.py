#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
        INSTALADOR DE MEMORIA VECTORIAL - METEOSERV3 V24.0
================================================================================

Instala ChromaDB y dependencias necesarias para la memoria episodica.

NOTA: ChromaDB puede requerir compilacion de numpy. Si falla:
      1. Actualizar pip: python -m pip install --upgrade pip
      2. Instalar desde binarios: python -m pip install --only-binary :all: numpy
      3. Alternativa SQLite: usar solo SQLite sin ChromaDB (mas simple)

================================================================================
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Ejecuta comando y muestra salida."""
    print(f"\n> {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    print(result.stdout)
    return True

def main():
    print("="*80)
    print("INSTALADOR DE MEMORIA VECTORIAL")
    print("="*80)
    
    # Verificar Python
    print(f"\nPython: {sys.version}")
    print(f"Ejecutable: {sys.executable}")
    
    # Actualizar pip
    print("\n[1/4] Actualizando pip...")
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"]):
        print("⚠️ Advertencia: No se pudo actualizar pip")
    
    # Intentar instalar numpy desde binarios
    print("\n[2/4] Instalando numpy...")
    if not run_command([sys.executable, "-m", "pip", "install", "numpy"]):
        print("⚠️ Numpy falló. Intentando desde binarios...")
        run_command([sys.executable, "-m", "pip", "install", "--only-binary", ":all:", "numpy"])
    
    # Instalar ChromaDB
    print("\n[3/4] Instalando ChromaDB...")
    chroma_ok = run_command([sys.executable, "-m", "pip", "install", "chromadb"])
    
    # Instalar sentence-transformers
    print("\n[4/4] Instalando sentence-transformers...")
    st_ok = run_command([sys.executable, "-m", "pip", "install", "sentence-transformers"])
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE INSTALACION")
    print("="*80)
    
    if chroma_ok and st_ok:
        print("✅ INSTALACION COMPLETA")
        print("\nPuedes ejecutar la demo:")
        print("  python core/learning/vector_memory.py")
    else:
        print("⚠️ INSTALACION PARCIAL")
        print("\nAlgunos paquetes fallaron. Alternativas:")
        print("1. Usar SQLite simple (sin embeddings)")
        print("2. Instalar manualmente desde binarios precompilados")
        print("3. Usar WSL (Windows Subsystem for Linux)")
    
    print("="*80)

if __name__ == "__main__":
    main()
