"""
GOBERNANZA ML: Versionado de modelos y pipeline de retraining
"""

import json
from datetime import datetime
from pathlib import Path


class ModelRegistry:
    """Registro de versiones de modelos."""
    
    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.models_dir = self.workspace / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.models_dir / "registry.json"
        self.registry = self._load_registry()
    
    def _load_registry(self) -> dict:
        """Carga el registro de modelos."""
        if self.registry_file.exists():
            with open(self.registry_file) as f:
                return json.load(f)
        return {"models": []}
    
    def register_model(self, model_name: str, version: str, metadata: dict) -> dict:
        """Registra un nuevo modelo."""
        entry = {
            "name": model_name,
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "status": "active"
        }
        self.registry["models"].append(entry)
        self._save_registry()
        return entry
    
    def get_active_model(self, model_name: str) -> dict:
        """Retorna el modelo activo de un nombre."""
        active = [m for m in self.registry["models"] 
                 if m["name"] == model_name and m["status"] == "active"]
        return active[-1] if active else None
    
    def _save_registry(self):
        """Guarda el registro de modelos."""
        with open(self.registry_file, "w") as f:
            json.dump(self.registry, f, indent=2)


class RetrainingPipeline:
    """Pipeline de retraining de modelos."""
    
    def __init__(self, feature_store, model_registry):
        self.feature_store = feature_store
        self.model_registry = model_registry
        self.retrain_history = []
    
    async def schedule_retrain(self, model_name: str, trigger: str = "manual") -> dict:
        """
        Programa un retraining.
        trigger: 'manual', 'periodic', 'drift_detected'
        """
        retrain_job = {
            "id": f"retrain_{model_name}_{int(__import__('time').time())}",
            "model": model_name,
            "trigger": trigger,
            "status": "pending",
            "started_at": None,
            "completed_at": None
        }
        
        self.retrain_history.append(retrain_job)
        return retrain_job
    
    async def execute_retrain(self, job_id: str) -> bool:
        """Ejecuta un job de retraining."""
        job = next((j for j in self.retrain_history if j["id"] == job_id), None)
        if not job:
            return False
        
        job["status"] = "running"
        job["started_at"] = datetime.now().isoformat()
        
        # Simulación: en producción aquí iría el retraining real
        # Por ahora: marcar como completado
        job["status"] = "completed"
        job["completed_at"] = datetime.now().isoformat()
        
        return True
    
    def get_retrain_status(self, model_name: str) -> dict:
        """Retorna estado del último retraining."""
        jobs = [j for j in self.retrain_history if j["model"] == model_name]
        return jobs[-1] if jobs else None
