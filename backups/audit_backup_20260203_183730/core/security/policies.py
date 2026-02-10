"""
SEGURIDAD: Gestión de secretos y políticas de retención
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path


class SecretsManager:
    """Gestiona secretos y variables sensibles."""
    
    def __init__(self):
        self.env_file = Path(".env.local")
        self.secrets = {}
        self._load_from_env()
    
    def _load_from_env(self):
        """Carga secretos desde .env.local (nunca versionado)."""
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, val = line.strip().split("=", 1)
                        self.secrets[key] = val
    
    def get_secret(self, key: str, default=None) -> str:
        """Retorna un secreto de forma segura."""
        return self.secrets.get(key, default or os.environ.get(key))
    
    def set_secret(self, key: str, value: str):
        """Establece un secreto (no versionado)."""
        self.secrets[key] = value
        # Guardar a archivo local (nunca versionado)
        with open(self.env_file, "a") as f:
            f.write(f"{key}={value}\n")


class DataRetentionPolicy:
    """Define y aplica políticas de retención de datos."""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.policies = {
            "logs": 30,  # días
            "anomalies": 90,
            "metrics": 365,
            "backups": 7,
            "audit_trail": 180
        }
    
    def cleanup_old_data(self) -> dict:
        """Limpia archivos más antiguos que la política."""
        results = {"cleaned": 0, "errors": 0}
        
        cleanup_dirs = {
            "logs": self.workspace / "logs",
            "data": self.workspace / "data"
        }
        
        for dir_name, policy_days in self.policies.items():
            dir_path = cleanup_dirs.get(
                "logs" if dir_name in ["logs", "anomalies", "audit_trail"] else "data"
            )
            
            if not dir_path or not dir_path.exists():
                continue
            
            cutoff_date = datetime.now() - timedelta(days=policy_days)
            
            for file_path in dir_path.glob("*"):
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_date:
                        try:
                            file_path.unlink()
                            results["cleaned"] += 1
                        except Exception:
                            results["errors"] += 1
        
        return results
    
    def get_policy(self) -> dict:
        """Retorna la política de retención actual."""
        return self.policies.copy()


class AccessControl:
    """Control de acceso basado en roles."""
    
    ROLES = {
        "admin": ["read", "write", "delete", "config"],
        "operator": ["read", "write", "approve_suggestions"],
        "viewer": ["read"],
        "api": ["read", "write"]
    }
    
    @staticmethod
    def check_permission(role: str, action: str) -> bool:
        """Verifica si un rol puede hacer una acción."""
        permissions = AccessControl.ROLES.get(role, [])
        return action in permissions
    
    @staticmethod
    def audit_access(user: str, resource: str, action: str, result: str):
        """Registra un acceso para auditoría."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "resource": resource,
            "action": action,
            "result": result
        }
        
        log_file = Path("logs") / "access_audit.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
