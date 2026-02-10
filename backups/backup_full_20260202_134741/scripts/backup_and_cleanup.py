import os
import shutil
from datetime import datetime

# Directorios
ROOT_DIR = os.getcwd()
BACKUP_DIR = os.path.join(ROOT_DIR, 'backups')
NEW_BACKUP = os.path.join(BACKUP_DIR, f'backup_{datetime.now().strftime("%Y%m%d")}')

# Directorios y archivos a EXCLUIR del backup
EXCLUDE = {
    '.git', '.venv', '__pycache__', '.pytest_cache', 
    'backups', 'logs', 'data', '.backup', 'archive',
    '__purge__', '.vscode', '.github',
    'meteoser_backend.log', 'uvicorn.log', 'proceso_monitor.log',
    'startup_log.txt', 'ventanas_eliminadas.log'
}

def should_exclude(name):
    """Verifica si un archivo o carpeta debe excluirse del backup."""
    return name in EXCLUDE or name.endswith('.log') or name.endswith('.bak')

def backup_full():
    """Crea una copia exacta del sistema completo (excepto exclusiones)."""
    if os.path.exists(NEW_BACKUP):
        shutil.rmtree(NEW_BACKUP)
    os.makedirs(NEW_BACKUP)
    
    for item in os.listdir(ROOT_DIR):
        if should_exclude(item):
            continue
        
        src = os.path.join(ROOT_DIR, item)
        dst = os.path.join(NEW_BACKUP, item)
        
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*EXCLUDE))
            elif os.path.isfile(src):
                shutil.copy2(src, dst)
        except Exception as e:
            print(f"Error copiando {item}: {e}")
    
    print(f"Backup completo realizado en: {NEW_BACKUP}")

def cleanup_old_backups():
    """Elimina todos los backups antiguos."""
    for item in os.listdir(BACKUP_DIR):
        item_path = os.path.join(BACKUP_DIR, item)
        if item.startswith('backup_') and item != os.path.basename(NEW_BACKUP) and os.path.isdir(item_path):
            shutil.rmtree(item_path)
            print(f"Backup antiguo eliminado: {item_path}")

if __name__ == "__main__":
    backup_full()
    cleanup_old_backups()
