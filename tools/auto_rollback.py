"""
AUTO-ROLLBACK SYSTEM
Monitorea cambios y revierte automáticamente si los tests fallan.
Garantiza 0 downtime y máxima autonomía.
"""

import os
import sys
import time
import subprocess
import logging
import json
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
logger = logging.getLogger(__name__)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(WORKSPACE / "logs" / "auto_rollback.log"),
        logging.StreamHandler()
    ]
)


def run_command(cmd: list, timeout: int = 300) -> tuple:
    """Ejecuta un comando y retorna (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORKSPACE)
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout: {' '.join(cmd)}")
        return -1, "", "Timeout"
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return -1, "", str(e)


def run_tests() -> bool:
    """Ejecuta suite de tests críticos."""
    logger.info("Running critical tests...")
    
    # Test 1: Syntax check
    logger.info("→ Checking Python syntax...")
    returncode, _, stderr = run_command(
        [sys.executable, str(WORKSPACE / "tools" / "backup_and_ci.py"), "test"]
    )
    
    if returncode != 0:
        logger.error(f"✗ Syntax check failed: {stderr}")
        return False
    
    logger.info("✓ Syntax check passed")
    
    # Test 2: Import critical modules
    logger.info("→ Testing critical imports...")
    test_imports = [
        "core.bus.bus_capas_informacion",
        "core.system.bus_expander",
        "core.indices.environmental_indices",
        "main_asgi"
    ]
    
    for module in test_imports:
        returncode, stdout, stderr = run_command(
            [sys.executable, "-c", f"import {module}"]
        )
        if returncode != 0:
            logger.error(f"✗ Failed to import {module}: {stderr}")
            return False
        logger.info(f"✓ Successfully imported {module}")
    
    logger.info("✓ All critical tests passed")
    return True


def detect_recent_changes(checkpoint_name: str = None) -> bool:
    """
    Detecta cambios en archivos críticos desde el último checkpoint.
    Si se detectan cambios inesperados, retorna True.
    """
    logger.info("Checking for recent file changes...")

    try:
        from tools.backup_and_ci import BACKUPS_DIR, CRITICAL_FILES, compute_file_hash
    except Exception as e:
        logger.error(f"No se pudo cargar backup_and_ci: {e}")
        return False

    if checkpoint_name is None:
        if not BACKUPS_DIR.exists():
            return False
        recent = sorted(BACKUPS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
        if not recent:
            return False
        checkpoint_name = recent[0].name

    checkpoint_dir = BACKUPS_DIR / checkpoint_name
    meta_file = checkpoint_dir / "metadata.json"
    if not meta_file.exists():
        logger.warning(f"Metadata no encontrada para checkpoint {checkpoint_name}")
        return False

    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Error leyendo metadata: {e}")
        return False

    files_meta = meta.get("files", {})
    for file_rel in CRITICAL_FILES:
        entry = files_meta.get(file_rel, {})
        expected_hash = entry.get("hash")
        file_path = WORKSPACE / file_rel
        if not file_path.exists():
            logger.warning(f"Archivo crítico faltante: {file_rel}")
            return True
        if expected_hash:
            current_hash = compute_file_hash(file_path)
            if current_hash and current_hash != expected_hash:
                logger.warning(f"Cambio detectado en {file_rel}")
                return True

    return False


def auto_rollback_if_needed(checkpoint_name: str = None) -> bool:
    """
    Verifica si el sistema debe hacer rollback.
    Si los tests fallan, revierte automáticamente al último checkpoint.
    """
    logger.info("=" * 60)
    logger.info("AUTO-ROLLBACK MONITOR STARTED")
    logger.info("=" * 60)
    
    if not run_tests():
        logger.error("✗ Tests failed. Initiating automatic rollback...")
        
        if checkpoint_name is None:
            # Usar el checkpoint más reciente
            checkpoints_dir = WORKSPACE / "backups" / "system_checkpoints"
            if checkpoints_dir.exists():
                recent = sorted(checkpoints_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
                if recent:
                    checkpoint_name = recent[0].name
                else:
                    logger.error("✗ No checkpoints available for rollback")
                    return False
            else:
                logger.error("✗ No backups directory found")
                return False
        
        returncode, _, stderr = run_command(
            [sys.executable, str(WORKSPACE / "tools" / "backup_and_ci.py"), "restore", checkpoint_name]
        )
        
        if returncode == 0:
            logger.error("✓ Automatic rollback successful")
            logger.error(f"✓ System reverted to checkpoint: {checkpoint_name}")
            return True
        else:
            logger.error(f"✗ Rollback failed: {stderr}")
            return False
    
    logger.info("✓ Tests passed. System is healthy.")
    return True


def watch_mode(checkpoint_interval: int = 3600):
    """
    Modo watch: monitorea el sistema continuamente y crea checkpoints periódicamente.
    checkpoint_interval: segundos entre checkpoints automáticos
    """
    logger.info(f"Entering watch mode. Checkpoint interval: {checkpoint_interval}s")
    
    try:
        while True:
            # Verificar integridad
            auto_rollback_if_needed()
            
            # Crear checkpoint periódico
            logger.info(f"Creating periodic checkpoint...")
            run_command(
                [sys.executable, str(WORKSPACE / "tools" / "backup_and_ci.py"), "checkpoint"]
            )
            
            # Limpiar checkpoints antiguos
            logger.info("Cleaning up old checkpoints...")
            run_command(
                [sys.executable, "-c",
                 f"from tools.backup_and_ci import cleanup_old_checkpoints; cleanup_old_checkpoints()"]
            )
            
            logger.info(f"Next checkpoint in {checkpoint_interval}s...")
            time.sleep(checkpoint_interval)
    
    except KeyboardInterrupt:
        logger.info("Watch mode interrupted by user")
    except Exception as e:
        logger.error(f"Error in watch mode: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python auto_rollback.py test                - Run tests and auto-rollback if needed")
        print("  python auto_rollback.py watch [interval]    - Watch mode (create checkpoints periodically)")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "test":
        success = auto_rollback_if_needed()
        sys.exit(0 if success else 1)
    elif command == "watch":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 3600
        watch_mode(interval)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
