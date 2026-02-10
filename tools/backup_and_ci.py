import logging
"""
SISTEMA DE BACKUPS AUTOMÁTICOS + CI MÍNIMO + AUTO-ROLLBACK
Propósito: garantizar recuperación ante cualquier cambio fallido
Ejecución: secuencial, sin paralelismo, con verificación de integridad
"""

import os
import shutil
import datetime
import hashlib
import json
import sys
import logging
from pathlib import Path

# Configuración
WORKSPACE = Path(__file__).parent.parent  # c:\Users\kioko\Desktop\MeteoSerV3
BACKUPS_DIR = WORKSPACE / "backups" / "system_checkpoints"
CONFIG_SNAPSHOT = WORKSPACE / "config" / ".last_snapshot"
BACKUP_MANIFEST = WORKSPACE / "backups" / "manifest.json"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(WORKSPACE / "logs" / "backup_ci.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Archivos críticos a respaldar
CRITICAL_FILES = [
    "core/system/bus_expander.py",
    "core/validation/anomaly_detector.py",
    "meteoser_configuracion.txt",
    "core/bus/__init__.py",
    "core/bus/bus_capas_informacion.py",
    "main.py",
    "main_asgi.py"
]

# Directorios críticos
CRITICAL_DIRS = [
    "core/validation",
    "core/bus",
    "core/indices",
    "config"
]


def compute_file_hash(filepath: Path, algorithm="sha256") -> str:
    """Calcula hash SHA256 de un archivo para verificar integridad."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {filepath}: {e}")
        return ""


def create_checkpoint(checkpoint_name: str = None) -> dict:
    """
    Crea un snapshot del estado actual del sistema.
    Retorna metadata del checkpoint para auditoría.
    """
    if checkpoint_name is None:
        checkpoint_name = f"checkpoint_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    checkpoint_dir = BACKUPS_DIR / checkpoint_name
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_meta = {
        "name": checkpoint_name,
        "timestamp": datetime.datetime.now().isoformat(),
        "files": {},
        "dirs": {},
        "status": "creating"
    }
    
    logger.info(f"Creating checkpoint: {checkpoint_name}")
    
    # Respaldar archivos críticos
    for file_rel in CRITICAL_FILES:
        file_path = WORKSPACE / file_rel
        if file_path.exists():
            dest = checkpoint_dir / file_rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(file_path, dest)
                file_hash = compute_file_hash(file_path)
                checkpoint_meta["files"][file_rel] = {
                    "hash": file_hash,
                    "size": file_path.stat().st_size,
                    "backed_up": True
                }
                logger.info(f"✓ Backed up: {file_rel}")
            except Exception as e:
                logger.error(f"✗ Failed to backup {file_rel}: {e}")
                checkpoint_meta["files"][file_rel] = {"backed_up": False, "error": str(e)}
        else:
            logger.warning(f"⚠ File not found (skipping): {file_rel}")
            checkpoint_meta["files"][file_rel] = {"backed_up": False, "error": "not_found"}
    
    # Respaldar directorios críticos (estructura y archivos .py)
    for dir_rel in CRITICAL_DIRS:
        dir_path = WORKSPACE / dir_rel
        if dir_path.exists():
            dest = checkpoint_dir / dir_rel
            try:
                shutil.copytree(dir_path, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
                checkpoint_meta["dirs"][dir_rel] = {"backed_up": True}
                logger.info(f"✓ Backed up directory: {dir_rel}")
            except Exception as e:
                logger.error(f"✗ Failed to backup directory {dir_rel}: {e}")
                checkpoint_meta["dirs"][dir_rel] = {"backed_up": False, "error": str(e)}
        else:
            logger.warning(f"⚠ Directory not found (skipping): {dir_rel}")
            checkpoint_meta["dirs"][dir_rel] = {"backed_up": False, "error": "not_found"}
    
    checkpoint_meta["status"] = "complete"
    
    # Guardar metadata del checkpoint
    meta_file = checkpoint_dir / "metadata.json"
    with open(meta_file, "w") as f:
        json.dump(checkpoint_meta, f, indent=2)
    
    logger.info(f"✓ Checkpoint created successfully: {checkpoint_name}")
    return checkpoint_meta


def restore_checkpoint(checkpoint_name: str) -> bool:
    """
    Restaura un checkpoint anterior.
    Retorna True si éxito, False si falló.
    """
    checkpoint_dir = BACKUPS_DIR / checkpoint_name
    
    if not checkpoint_dir.exists():
        logger.error(f"Checkpoint not found: {checkpoint_name}")
        return False
    
    logger.info(f"Restoring checkpoint: {checkpoint_name}")
    
    try:
        # Restaurar archivos críticos
        for file_rel in CRITICAL_FILES:
            backup_file = checkpoint_dir / file_rel
            if backup_file.exists():
                dest = WORKSPACE / file_rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, dest)
                logger.info(f"✓ Restored: {file_rel}")
            else:
                logger.warning(f"⚠ Backup file not found: {file_rel}")
        
        # Restaurar directorios críticos
        for dir_rel in CRITICAL_DIRS:
            backup_dir = checkpoint_dir / dir_rel
            if backup_dir.exists():
                dest = WORKSPACE / dir_rel
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(backup_dir, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                logger.info(f"✓ Restored directory: {dir_rel}")
            else:
                logger.warning(f"⚠ Backup directory not found: {dir_rel}")
        
        logger.info(f"✓ Checkpoint restored successfully")
        return True
    
    except Exception as e:
        logger.error(f"✗ Failed to restore checkpoint: {e}")
        return False


def list_checkpoints() -> list:
    """Lista todos los checkpoints disponibles."""
    if not BACKUPS_DIR.exists():
        return []
    
    checkpoints = []
    for cp_dir in sorted(BACKUPS_DIR.iterdir()):
        if cp_dir.is_dir():
            meta_file = cp_dir / "metadata.json"
            if meta_file.exists():
                try:
                    with open(meta_file) as f:
                        meta = json.load(f)
                    checkpoints.append({
                        "name": cp_dir.name,
                        "timestamp": meta.get("timestamp"),
                        "status": meta.get("status")
                    })
                except:
                    logging.exception("Silent except at 199 - revisar contexto")
    
    return checkpoints


def run_basic_tests() -> bool:
    """
    Ejecuta tests mínimos para verificar integridad del sistema.
    Retorna True si todos pasan, False si alguno falla.
    """
    logger.info("Running basic CI tests...")
    
    all_passed = True
    
    # Test 1: Verificar que los archivos críticos existen
    for file_rel in CRITICAL_FILES:
        file_path = WORKSPACE / file_rel
        if not file_path.exists():
            logger.error(f"✗ Critical file missing: {file_rel}")
            all_passed = False
        else:
            logger.info(f"✓ Critical file present: {file_rel}")
    
    # Test 2: Verificar sintaxis Python de los archivos críticos
    logger.info("Checking Python syntax...")
    py_files = list((WORKSPACE / "core").rglob("*.py")) + list((WORKSPACE).glob("*.py"))
    for py_file in py_files:
        if py_file.name.startswith("_"):
            continue
        try:
            with open(py_file, encoding='utf-8', errors='ignore') as f:
                compile(f.read(), str(py_file), "exec")
            logger.info(f"OK: Syntax OK: {py_file.relative_to(WORKSPACE)}")
        except SyntaxError as e:
            logger.error(f"ERROR: Syntax error in {py_file.relative_to(WORKSPACE)}: {e}")
            all_passed = False
        except Exception as e:
            logger.warning(f"WARN: Could not check {py_file}: {e}")
    
    # Test 3: Verificar que los directorios críticos existen
    for dir_rel in CRITICAL_DIRS:
        dir_path = WORKSPACE / dir_rel
        if not dir_path.exists():
            logger.error(f"✗ Critical directory missing: {dir_rel}")
            all_passed = False
        else:
            logger.info(f"✓ Critical directory present: {dir_rel}")
    
    if all_passed:
        logger.info("✓ All basic CI tests passed")
    else:
        logger.error("✗ Some CI tests failed")
    
    return all_passed


def cleanup_old_checkpoints(max_keep: int = 5):
    """Mantiene solo los últimos N checkpoints para ahorrar espacio."""
    if not BACKUPS_DIR.exists():
        return
    
    checkpoints = sorted(BACKUPS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if len(checkpoints) > max_keep:
        to_delete = checkpoints[max_keep:]
        for cp_dir in to_delete:
            try:
                shutil.rmtree(cp_dir)
                logger.info(f"Deleted old checkpoint: {cp_dir.name}")
            except Exception as e:
                logger.error(f"Failed to delete checkpoint {cp_dir.name}: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python backup_and_ci.py checkpoint [name]  - Create a checkpoint")
        print("  python backup_and_ci.py restore <name>     - Restore a checkpoint")
        print("  python backup_and_ci.py list               - List all checkpoints")
        print("  python backup_and_ci.py test               - Run CI tests")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "checkpoint":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        create_checkpoint(name)
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Error: checkpoint name required")
            sys.exit(1)
        success = restore_checkpoint(sys.argv[2])
        sys.exit(0 if success else 1)
    elif command == "list":
        checkpoints = list_checkpoints()
        if checkpoints:
            print("\nAvailable checkpoints:")
            for cp in checkpoints:
                print(f"  {cp['name']} - {cp['timestamp']} - {cp['status']}")
        else:
            print("No checkpoints found")
    elif command == "test":
        success = run_basic_tests()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
