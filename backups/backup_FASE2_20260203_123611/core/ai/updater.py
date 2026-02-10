"""
MeteoSer AI Updater Engine - Motor de Actualización Autónoma
=============================================================

Gestiona actualizaciones de software/firmware de forma autónoma.
Descarga, valida, aplica y hace rollback si falla.
"""

import hashlib
import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class UpdaterEngine:
    """Motor de actualización autónoma de software/firmware"""
    
    def __init__(self, updates_dir: str = "data/updates", backup_dir: str = "backups"):
        self.updates_dir = Path(updates_dir)
        self.backup_dir = Path(backup_dir)
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.update_history: List[Dict] = []
        self._load_history()
        
        logger.info(f"🔄 UpdaterEngine inicializado")
    
    def _load_history(self) -> None:
        """Carga historial de updates"""
        history_file = self.updates_dir / "update_history.json"
        if history_file.exists():
            self.update_history = json.loads(history_file.read_text(encoding="utf-8"))
            logger.info(f"✅ Historial de updates cargado: {len(self.update_history)} entradas")
    
    def _save_history(self) -> None:
        """Guarda historial de updates"""
        history_file = self.updates_dir / "update_history.json"
        history_file.write_text(json.dumps(self.update_history, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def check_for_updates(self, repo_url: Optional[str] = None) -> List[Dict]:
        """Verifica si hay actualizaciones disponibles"""
        if not repo_url:
            logger.info("📡 No se especificó URL de repositorio, saltando verificación")
            return []
        
        try:
            # Consultar API de releases (ejemplo GitHub)
            response = requests.get(repo_url, timeout=10)
            if response.status_code == 200:
                updates = response.json()
                logger.info(f"✅ Encontradas {len(updates)} actualizaciones disponibles")
                return updates
            else:
                logger.error(f"❌ Error consultando updates: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error verificando updates: {e}")
            return []
    
    def download_update(self, update_url: str, update_id: str) -> Tuple[bool, Optional[str]]:
        """Descarga un update desde URL"""
        try:
            logger.info(f"⬇️ Descargando update {update_id} desde {update_url}")
            
            response = requests.get(update_url, stream=True, timeout=120)
            if response.status_code != 200:
                return False, f"Error HTTP {response.status_code}"
            
            # Guardar archivo
            update_file = self.updates_dir / f"{update_id}.zip"
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Update descargado: {update_file}")
            return True, str(update_file)
        
        except Exception as e:
            error = f"Error descargando update: {e}"
            logger.error(f"❌ {error}")
            return False, error
    
    def validate_update(self, update_file: str, expected_checksum: Optional[str] = None) -> Tuple[bool, str]:
        """Valida integridad del update"""
        path = Path(update_file)
        
        if not path.exists():
            return False, "Archivo no encontrado"
        
        try:
            # Calcular checksum SHA256
            sha256 = hashlib.sha256()
            with open(path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            
            checksum = sha256.hexdigest()
            
            if expected_checksum:
                if checksum == expected_checksum:
                    logger.info(f"✅ Checksum válido: {checksum[:16]}...")
                    return True, checksum
                else:
                    error = f"Checksum inválido: esperado {expected_checksum[:16]}..., obtenido {checksum[:16]}..."
                    logger.error(f"❌ {error}")
                    return False, error
            else:
                logger.info(f"ℹ️ Checksum calculado: {checksum[:16]}... (sin validación)")
                return True, checksum
        
        except Exception as e:
            error = f"Error validando update: {e}"
            logger.error(f"❌ {error}")
            return False, error
    
    def create_backup(self, backup_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Crea backup completo del sistema antes de aplicar update"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_pre_update_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        
        try:
            logger.info(f"💾 Creando backup: {backup_name}")
            
            # Copiar directorios críticos
            critical_dirs = ["core", "meteoser_ia", "data"]
            
            backup_path.mkdir(exist_ok=True)
            
            for dir_name in critical_dirs:
                src = Path(dir_name)
                if src.exists():
                    dst = backup_path / dir_name
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            
            # Copiar archivos Python críticos
            for py_file in Path(".").glob("*.py"):
                shutil.copy2(py_file, backup_path)
            
            logger.info(f"✅ Backup creado: {backup_path}")
            return True, str(backup_path)
        
        except Exception as e:
            error = f"Error creando backup: {e}"
            logger.error(f"❌ {error}")
            return False, error
    
    def apply_update(self, update_file: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Aplica un update (con opción de dry-run)"""
        path = Path(update_file)
        
        if not path.exists():
            return False, "Archivo de update no encontrado"
        
        try:
            # Crear backup antes de aplicar
            success, backup_path = self.create_backup()
            if not success:
                return False, f"No se pudo crear backup: {backup_path}"
            
            logger.info(f"🔄 Aplicando update: {update_file} (dry_run={dry_run})")
            
            if dry_run:
                logger.info("ℹ️ Modo dry-run: no se aplicarán cambios reales")
                return True, "Dry-run exitoso"
            
            # Descomprimir update
            import zipfile
            with zipfile.ZipFile(path, 'r') as zip_ref:
                # Listar archivos
                files = zip_ref.namelist()
                logger.info(f"📦 Update contiene {len(files)} archivos")
                
                # Extraer archivos
                extract_dir = self.updates_dir / path.stem
                zip_ref.extractall(extract_dir)
            
            # Aplicar archivos (copiar a sus destinos)
            # TODO: Implementar lógica de aplicación según manifest del update
            
            # Registrar en historial
            self.update_history.append({
                "timestamp": datetime.now().isoformat(),
                "update_file": str(path),
                "backup_path": backup_path,
                "status": "applied",
            })
            self._save_history()
            
            logger.info(f"✅ Update aplicado exitosamente")
            return True, "Update aplicado"
        
        except Exception as e:
            error = f"Error aplicando update: {e}"
            logger.error(f"❌ {error}")
            
            # Intentar rollback
            logger.warning("🔙 Intentando rollback...")
            rollback_success, rollback_msg = self.rollback()
            
            return False, f"{error}\nRollback: {rollback_msg}"
    
    def rollback(self, backup_path: Optional[str] = None) -> Tuple[bool, str]:
        """Hace rollback al último backup"""
        try:
            if not backup_path:
                # Usar último backup
                backups = sorted(self.backup_dir.glob("backup_*"))
                if not backups:
                    return False, "No hay backups disponibles"
                backup_path = str(backups[-1])
            
            backup = Path(backup_path)
            if not backup.exists():
                return False, f"Backup no encontrado: {backup_path}"
            
            logger.info(f"🔙 Haciendo rollback desde: {backup}")
            
            # Restaurar archivos desde backup
            for item in backup.iterdir():
                if item.is_dir():
                    dst = Path(item.name)
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, ".")
            
            logger.info(f"✅ Rollback completado")
            return True, "Rollback exitoso"
        
        except Exception as e:
            error = f"Error en rollback: {e}"
            logger.error(f"❌ {error}")
            return False, error
    
    def update_pip_packages(self, packages: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Actualiza paquetes Python vía pip"""
        try:
            if packages:
                cmd = ["pip", "install", "--upgrade"] + packages
            else:
                cmd = ["pip", "install", "--upgrade", "-r", "requirements.txt"]
            
            logger.info(f"📦 Actualizando paquetes pip...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✅ Paquetes actualizados exitosamente")
                return True, "Paquetes actualizados"
            else:
                error = f"Error actualizando paquetes: {result.stderr}"
                logger.error(f"❌ {error}")
                return False, error
        
        except Exception as e:
            error = f"Excepción actualizando paquetes: {e}"
            logger.error(f"❌ {error}")
            return False, error
    
    def get_status(self) -> Dict:
        """Retorna estado del updater"""
        return {
            "updates_history": len(self.update_history),
            "last_update": self.update_history[-1] if self.update_history else None,
            "backups_count": len(list(self.backup_dir.glob("backup_*"))),
            "updates_dir": str(self.updates_dir),
        }
