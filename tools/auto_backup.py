import os
import shutil
import datetime
import time

# Configuración
SOURCE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKUP_ROOT = os.path.join(SOURCE_DIR, "backups")
MAX_BACKUPS = 10  # Número máximo de copias a conservar
INTERVAL_MINUTES = 60  # Intervalo entre copias automáticas


def make_backup():
    if not os.path.exists(BACKUP_ROOT):
        os.makedirs(BACKUP_ROOT)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BACKUP_ROOT, f"backup_{timestamp}")
    exclude = {"__pycache__", "backups", ".git", ".venv", ".env"}
    print(f"[Backup] Creando copia en: {backup_dir}")
    shutil.copytree(SOURCE_DIR, backup_dir, ignore=shutil.ignore_patterns(*exclude))
    # Limitar número de copias
    backups = sorted([d for d in os.listdir(BACKUP_ROOT) if d.startswith("backup_")])
    while len(backups) > MAX_BACKUPS:
        to_remove = os.path.join(BACKUP_ROOT, backups.pop(0))
        print(f"[Backup] Eliminando copia antigua: {to_remove}")
        shutil.rmtree(to_remove)
    print("[Backup] Copia completada.")


def auto_backup_loop():
    print(f"[Backup] Iniciando copias automáticas cada {INTERVAL_MINUTES} minutos...")
    while True:
        make_backup()
        time.sleep(INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    auto_backup_loop()
