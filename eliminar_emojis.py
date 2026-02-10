# -*- coding: utf-8 -*-
"""
Script para eliminar TODOS los emojis de archivos .py
Política 0 fallos: Consola debe funcionar sin restricciones
"""

import re
from pathlib import Path

# Mapeo emojis → texto equivalente
EMOJI_MAPPING = {
    '[GUARDIAN]': '[GUARDIAN]',
    '[BUSCAR]': '[BUSCAR]',
    '[OK]': '[OK]',
    '[ERROR]': '[ERROR]',
    '[WARNING]': '[WARNING]',
    '[CRITICAL]': '[CRITICAL]',
    '[CLEANUP]': '[CLEANUP]',
    '[BLOQUEADO]': '[BLOQUEADO]',
    '[TARGET]': '[TARGET]',
    '[FAST]': '[FAST]',
    '[FECHA]': '[FECHA]',
    '[STATS]': '[STATS]',
    '[PARTICULAS]': '[PARTICULAS]',
    '[REINICIO]': '[REINICIO]',
    '[LAUNCH]': '[LAUNCH]',
    '[INFO]': '[INFO]',
    '[GUARDAR]': '[GUARDAR]',
}

def limpiar_archivo(ruta: Path) -> bool:
    """Elimina emojis de un archivo .py"""
    try:
        contenido = ruta.read_text(encoding='utf-8')
        contenido_original = contenido
        
        # Reemplazar cada emoji
        for emoji, texto in EMOJI_MAPPING.items():
            contenido = contenido.replace(emoji, texto)
        
        # Si cambió algo, guardar
        if contenido != contenido_original:
            ruta.write_text(contenido, encoding='utf-8')
            return True
        return False
    except Exception as e:
        print(f"[ERROR] {ruta}: {e}")
        return False

def main():
    raiz = Path('.')
    archivos_modificados = 0
    
    # Buscar todos los .py excepto en backups, .venv, __pycache__
    for archivo in raiz.rglob('*.py'):
        if any(p in str(archivo) for p in ['backups', '.venv', '__pycache__', 'tests']):
            continue
        
        if limpiar_archivo(archivo):
            print(f"[LIMPIADO] {archivo}")
            archivos_modificados += 1
    
    print(f"\n[RESUMEN] {archivos_modificados} archivos modificados")

if __name__ == '__main__':
    main()
