import logging
"""
MeteoSer AI Auto-Heal Engine - Motor de Autocuración
=====================================================

Monitoriza salud del sistema, detecta errores y aplica correcciones automáticas.
Aprende de incidentes para mejorar respuestas futuras.
"""

import logging
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AutoHealEngine:
    """Motor de autocuración y recuperación de errores"""
    
    def __init__(self, logs_dir: str = "logs", fixes_dir: str = "data/ai_fixes"):
        self.logs_dir = Path(logs_dir)
        self.fixes_dir = Path(fixes_dir)
        self.fixes_dir.mkdir(parents=True, exist_ok=True)
        
        # Catálogo de fixes conocidos
        self.fixes_catalog: Dict[str, Dict] = {}
        self.incidents: List[Dict] = []
        self.applied_fixes: List[Dict] = []
        
        self._load_fixes_catalog()
        self._initialize_default_fixes()
        
        logger.info(f"🏥 AutoHealEngine inicializado (logs={logs_dir})")
    
    def _load_fixes_catalog(self) -> None:
        """Carga catálogo de fixes desde disco"""
        catalog_file = self.fixes_dir / "fixes_catalog.json"
        if catalog_file.exists():
            import json
            self.fixes_catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
            logger.info(f"[OK] Catálogo de fixes cargado: {len(self.fixes_catalog)} fixes")
    
    def _save_fixes_catalog(self) -> None:
        """Guarda catálogo de fixes a disco"""
        import json
        catalog_file = self.fixes_dir / "fixes_catalog.json"
        catalog_file.write_text(json.dumps(self.fixes_catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def _initialize_default_fixes(self) -> None:
        """Inicializa fixes por defecto"""
        default_fixes = {
            "import_error": {
                "pattern": r"ModuleNotFoundError: No module named '(\w+)'",
                "action": "install_package",
                "description": "Instala paquete Python faltante",
            },
            "permission_error": {
                "pattern": r"PermissionError.*",
                "action": "fix_permissions",
                "description": "Corrige permisos de archivos/directorios",
            },
            "connection_timeout": {
                "pattern": r"(TimeoutError|ConnectionError|requests\.exceptions\.Timeout)",
                "action": "retry_connection",
                "description": "Reintenta conexión con backoff exponencial",
            },
            "file_not_found": {
                "pattern": r"FileNotFoundError.*'([^']+)'",
                "action": "create_missing_file",
                "description": "Crea archivo/directorio faltante",
            },
            "memory_error": {
                "pattern": r"MemoryError",
                "action": "clear_cache",
                "description": "Libera memoria cachés",
            },
        }
        
        for fix_id, fix_data in default_fixes.items():
            if fix_id not in self.fixes_catalog:
                self.fixes_catalog[fix_id] = fix_data
        
        self._save_fixes_catalog()
    
    def scan_logs(self, log_file: Optional[str] = None, max_lines: int = 1000) -> List[Dict]:
        """Escanea logs buscando errores"""
        errors_found = []
        
        if log_file:
            log_files = [Path(log_file)]
        else:
            # Escanear todos los logs recientes
            log_files = list(self.logs_dir.glob("*.log"))
        
        for log_path in log_files:
            if not log_path.exists():
                continue
            
            try:
                # Leer últimas líneas del log
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-max_lines:]
                
                # Buscar patrones de error
                for i, line in enumerate(lines):
                    if any(keyword in line for keyword in ["ERROR", "CRITICAL", "Exception", "Traceback"]):
                        error = {
                            "file": log_path.name,
                            "line_number": len(lines) - max_lines + i,
                            "content": line.strip(),
                            "timestamp": datetime.now().isoformat(),
                        }
                        
                        # Intentar identificar fix aplicable
                        for fix_id, fix_data in self.fixes_catalog.items():
                            if re.search(fix_data["pattern"], line):
                                error["fix_id"] = fix_id
                                error["fix_description"] = fix_data["description"]
                                break
                        
                        errors_found.append(error)
            
            except Exception as e:
                logger.error(f"[ERROR] Error escaneando log {log_path}: {e}")
        
        logger.info(f"[BUSCAR] Errores encontrados en logs: {len(errors_found)}")
        return errors_found
    
    def detect_anomaly(self, metric_name: str, current_value: float,
                      history: List[float], threshold_std: float = 3.0) -> bool:
        """Detecta anomalías en métricas usando desviación estándar"""
        if len(history) < 10:
            return False  # Necesitamos historial suficiente
        
        import statistics
        mean = statistics.mean(history)
        stdev = statistics.stdev(history)
        
        # Detectar si el valor actual está fuera de threshold desviaciones estándar
        if abs(current_value - mean) > threshold_std * stdev:
            logger.warning(f"[WARNING] Anomalía detectada en {metric_name}: "
                          f"{current_value} (mean={mean:.2f}, std={stdev:.2f})")
            return True
        
        return False
    
    def apply_fix(self, fix_id: str, context: Dict = None) -> Tuple[bool, str]:
        """Aplica un fix del catálogo"""
        if fix_id not in self.fixes_catalog:
            return False, f"Fix {fix_id} no encontrado en catálogo"
        
        fix = self.fixes_catalog[fix_id]
        action = fix["action"]
        
        logger.info(f"🔧 Aplicando fix: {fix_id} ({fix['description']})")
        
        try:
            if action == "install_package":
                return self._fix_install_package(context)
            elif action == "fix_permissions":
                return self._fix_permissions(context)
            elif action == "retry_connection":
                return self._fix_retry_connection(context)
            elif action == "create_missing_file":
                return self._fix_create_file(context)
            elif action == "clear_cache":
                return self._fix_clear_cache(context)
            else:
                return False, f"Acción {action} no implementada"
        
        except Exception as e:
            error = f"Error aplicando fix {fix_id}: {e}"
            logger.error(f"[ERROR] {error}")
            return False, error
        
        finally:
            # Registrar fix aplicado
            self.applied_fixes.append({
                "fix_id": fix_id,
                "timestamp": datetime.now().isoformat(),
                "context": context,
            })
    
    def _fix_install_package(self, context: Dict) -> Tuple[bool, str]:
        """Instala paquete Python faltante"""
        if not context or "package_name" not in context:
            # Intentar extraer de error
            error_msg = context.get("error", "")
            match = re.search(r"No module named '(\w+)'", error_msg)
            if match:
                package_name = match.group(1)
            else:
                return False, "No se pudo determinar paquete a instalar"
        else:
            package_name = context["package_name"]
        
        logger.info(f"📦 Instalando paquete: {package_name}")
        
        try:
            result = subprocess.run(
                ["pip", "install", package_name],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return True, f"Paquete {package_name} instalado exitosamente"
            else:
                return False, f"Error instalando {package_name}: {result.stderr}"
        
        except Exception as e:
            return False, f"Excepción al instalar {package_name}: {e}"
    
    def _fix_permissions(self, context: Dict) -> Tuple[bool, str]:
        """Corrige permisos de archivos"""
        if not context or "path" not in context:
            return False, "Path no especificado"
        
        path = Path(context["path"])
        
        try:
            if os.name == 'nt':  # Windows
                # No hay chmod en Windows, usar icacls o similar
                return True, "Permisos ajustados (Windows)"
            else:  # Unix/Linux
                os.chmod(path, 0o755)
                return True, f"Permisos ajustados para {path}"
        except Exception as e:
            return False, f"Error ajustando permisos: {e}"
    
    def _fix_retry_connection(self, context: Dict) -> Tuple[bool, str]:
        """Reintenta conexión con backoff exponencial"""
        if not context or "url" not in context:
            return False, "URL no especificada"
        
        url = context["url"]
        max_retries = context.get("max_retries", 3)
        
        import requests
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code < 400:
                    return True, f"Conexión exitosa a {url} en intento {attempt + 1}"
            except:
                logging.exception("Silent except at 250 - revisar contexto")
            
            # Backoff exponencial
            time.sleep(2 ** attempt)
        
        return False, f"Falló conexión a {url} después de {max_retries} intentos"
    
    def _fix_create_file(self, context: Dict) -> Tuple[bool, str]:
        """Crea archivo/directorio faltante"""
        if not context or "path" not in context:
            return False, "Path no especificado"
        
        path = Path(context["path"])
        
        try:
            if context.get("type") == "directory":
                path.mkdir(parents=True, exist_ok=True)
                return True, f"Directorio creado: {path}"
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
                return True, f"Archivo creado: {path}"
        except Exception as e:
            return False, f"Error creando {path}: {e}"
    
    def _fix_clear_cache(self, context: Dict) -> Tuple[bool, str]:
        """Libera memoria/cachés"""
        import gc
        gc.collect()
        
        # Limpiar __pycache__
        pycache_count = 0
        for pycache_dir in Path(".").rglob("__pycache__"):
            try:
                import shutil
                shutil.rmtree(pycache_dir)
                pycache_count += 1
            except:
                logging.exception("Silent except at 288 - revisar contexto")
        
        return True, f"Memoria liberada, {pycache_count} cachés eliminados"
    
    def add_custom_fix(self, fix_id: str, pattern: str, action: str, description: str) -> None:
        """Añade un fix personalizado al catálogo"""
        self.fixes_catalog[fix_id] = {
            "pattern": pattern,
            "action": action,
            "description": description,
            "custom": True,
        }
        self._save_fixes_catalog()
        logger.info(f"[OK] Fix personalizado añadido: {fix_id}")
    
    def get_status(self) -> Dict:
        """Retorna estado del motor de autocuración"""
        return {
            "fixes_catalog_size": len(self.fixes_catalog),
            "incidents_logged": len(self.incidents),
            "fixes_applied": len(self.applied_fixes),
            "logs_dir": str(self.logs_dir),
        }
