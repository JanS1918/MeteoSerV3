from __future__ import annotations

import logging
import importlib.util
import inspect
import logging

import os

try:
    from core.config.secrets_vault import get_vault
    _HAS_VAULT = True
except ImportError:
    get_vault = None
    _HAS_VAULT = False
import shutil
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import block_a
from . import block_b

logger = logging.getLogger("meteoser_ia.block_c")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [BLOQUE C] [%(levelname)s] %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

EXTERNAL_INTEGRATION_MODE = block_a.EXTERNAL_INTEGRATION_MODE

REPO_DIR = os.path.join(os.path.dirname(__file__), "ia_algorithms_repo")
os.makedirs(REPO_DIR, exist_ok=True)

SANDBOX_TIMEOUT = 5.0


class SensorReputation:
    def __init__(self):
        self.reputation: Dict[str, float] = {}

    def update(self, sensor_id: str, score: float):
        self.reputation[sensor_id] = score
        logging.info(f"Reputación actualizada: {sensor_id} → {score}")

    def get(self, sensor_id: str) -> float:
        return self.reputation.get(sensor_id, 0.0)


class LearningEngine:
    def __init__(self):
        self.patterns: Dict[str, Any] = {}
        self.sensor_reputation = SensorReputation()

    def learn_pattern(self, sensor_id: str, data: Any):
        self.patterns[sensor_id] = data
        logging.info(f"Patrón aprendido para {sensor_id}")

    def update_reputation(self, sensor_id: str, score: float):
        self.sensor_reputation.update(sensor_id, score)

    def get_reputation(self, sensor_id: str) -> float:
        return self.sensor_reputation.get(sensor_id)

@dataclass
class AlgorithmVersion:
    id: str
    timestamp: float
    code: str
    description: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    status: str = "created"
    notes: List[str] = field(default_factory=list)

@dataclass
class AlgorithmRepositorySnapshot:
    versions: Dict[str, AlgorithmVersion] = field(default_factory=dict)

class AlgorithmRepository:
    def __init__(self, repo_dir: str = REPO_DIR) -> None:
        self.repo_dir = repo_dir
        self._versions: Dict[str, AlgorithmVersion] = {}
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        meta_path = os.path.join(self.repo_dir, "index.json")
        if os.path.exists(meta_path):
            try:
                import json
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for vid, v in data.items():
                    self._versions[vid] = AlgorithmVersion(
                        id=vid,
                        timestamp=v["timestamp"],
                        code=v["code"],
                        description=v.get("description", ""),
                        metrics=v.get("metrics", {}),
                        status=v.get("status", "created"),
                        notes=v.get("notes", []),
                    )
                logger.info(f"Repositorio IA: cargadas {len(self._versions)} versiones desde disco.")
            except Exception:
                logger.warning("Repositorio IA: fallo al cargar index.json, se ignora.")
        else:
            logger.info("Repositorio IA: index.json no encontrado, iniciando repositorio vacío.")

    def _persist_to_disk(self) -> None:
        import json
        meta_path = os.path.join(self.repo_dir, "index.json")
        data = {}
        for vid, v in self._versions.items():
            data[vid] = {
                "timestamp": v.timestamp,
                "code": v.code,
                "description": v.description,
                "metrics": v.metrics,
                "status": v.status,
                "notes": v.notes,
            }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_version(self, version: AlgorithmVersion) -> None:
        self._versions[version.id] = version
        self._persist_to_disk()
        logger.info(f"Repositorio IA: añadida versión {version.id}")

    def list_versions(self) -> List[AlgorithmVersion]:
        return list(self._versions.values())

    def get_version(self, vid: str) -> Optional[AlgorithmVersion]:
        return self._versions.get(vid)

    def snapshot(self) -> AlgorithmRepositorySnapshot:
        return AlgorithmRepositorySnapshot(versions=dict(self._versions))


LEARNING_ENGINE = LearningEngine()

ALGO_REPO = AlgorithmRepository()

def _generate_algorithm_id() -> str:
    return f"alg_{int(time.time() * 1000)}"

def generate_algorithm_from_spec(spec: Dict[str, Any]) -> AlgorithmVersion:
    logger.info("Generando algoritmo a partir de spec...")
    alg_id = _generate_algorithm_id()
    timestamp = time.time()

    objective = spec.get("objective", "procesar lecturas")
    inputs = spec.get("inputs", ["sensor_readings"])
    metrics = spec.get("metrics", {"score": "accuracy"})

    code_lines = [
        "def process(data):",
        "    '''",
        f"    Algoritmo generado: {objective}",
        "    data: dict con entradas esperadas",
        "    Retorna: dict con keys 'result' y 'meta'",
        "    '''",
        "    # Ejemplo simple: promedia temperaturas si existen",
        "    try:",
        "        temps = []",
        "        for v in data.get('temps', []):",
        "            temps.append(float(v))",
        "        if temps:",
        "            avg = sum(temps) / len(temps)",
        "        else:",
        "            avg = None",
        "        return {'result': {'avg_temp': avg}, 'meta': {'count': len(temps)}}",
        "    except Exception as e:",
        "        return {'result': None, 'meta': {'error': str(e)}}",
    ]
    code = "\n".join(code_lines)

    version = AlgorithmVersion(
        id=alg_id,
        timestamp=timestamp,
        code=code,
        description=f"Generado para: {objective}",
        metrics={"requested_metrics": metrics},
        status="created",
    )

    ALGO_REPO.add_version(version)
    logger.info(f"Algoritmo generado con id {alg_id}")
    return version

def _execute_in_sandbox(code: str, func_name: str = "process", input_data: Dict[str, Any] = None, timeout: float = SANDBOX_TIMEOUT) -> Tuple[bool, Dict[str, Any], str]:
    input_data = input_data or {}
    tmpdir = tempfile.mkdtemp(prefix="meteoser_sandbox_")
    module_path = os.path.join(tmpdir, "alg_module.py")
    try:
        with open(module_path, "w", encoding="utf-8") as f:
            f.write(code)

        spec = importlib.util.spec_from_file_location("alg_module", module_path)
        module = importlib.util.module_from_spec(spec)
        loader = spec.loader
        assert loader is not None
        loader.exec_module(module)

        func = getattr(module, func_name, None)
        if func is None or not callable(func):
            return False, {}, f"Función {func_name} no encontrada en el código."

        start = time.time()
        result = func(input_data)
        elapsed = time.time() - start
        if elapsed > timeout:
            return False, {}, f"Timeout: ejecución {elapsed:.2f}s > {timeout}s"

        if not isinstance(result, dict):
            return False, {}, "Resultado no es un dict."

        return True, result, ""
    except Exception as e:
        tb = traceback.format_exc()
        return False, {}, tb
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            logging.exception("Silent except at 222 - revisar contexto")

def evaluate_algorithm_version(vid: str, test_inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    version = ALGO_REPO.get_version(vid)
    if not version:
        raise ValueError(f"Versión {vid} no encontrada.")

    results = []
    errors = []
    successes = 0
    for inp in test_inputs:
        ok, out, err = _execute_in_sandbox(version.code, input_data=inp)
        if ok:
            successes += 1
            results.append(out)
        else:
            errors.append(err)

    success_rate = successes / max(1, len(test_inputs))
    metrics = {
        "success_rate": success_rate,
        "tests_run": len(test_inputs),
        "errors": errors[:5],
    }
    version.metrics.update(metrics)
    version.status = "tested"
    ALGO_REPO._persist_to_disk()
    logger.info(f"Evaluación completada para {vid}: success_rate={success_rate:.2f}")
    return metrics

def validate_with_external_services(vid: str) -> Dict[str, Any]:
    version = ALGO_REPO.get_version(vid)
    if not version:
        raise ValueError(f"Versión {vid} no encontrada.")


    # Usar vault cifrado para claves externas
    vault = get_vault() if _HAS_VAULT else None
    url = os.getenv("METEOSER_EXTERNAL_VALIDATION_URL")
    api_key = (vault.get_api_key("METEOSER_EXTERNAL_VALIDATION_KEY", "METEOSER_EXTERNAL_VALIDATION_KEY") if vault else None) or os.getenv("METEOSER_EXTERNAL_VALIDATION_KEY")

    payload = {
        "version_id": version.id,
        "timestamp": version.timestamp,
        "description": version.description,
        "metrics": version.metrics,
        "code": version.code,
    }

    if url:
        try:
            import requests
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                validation = {
                    "external_score": data.get("external_score"),
                    "approved": bool(data.get("approved")),
                    "notes": data.get("notes", []),
                }
                version.metrics.update(validation)
                version.status = "validated" if validation["approved"] else "rejected"
                ALGO_REPO._persist_to_disk()
                logger.info(f"Validación externa OK para {vid}")
                return validation
            logger.warning(f"Validación externa falló ({response.status_code}): {response.text}")
        except Exception as e:
            logger.warning(f"Error validando externamente: {e}")

    success_rate = version.metrics.get("success_rate")
    approved = success_rate is not None and float(success_rate) >= 0.7
    validation = {
        "external_score": success_rate,
        "approved": approved,
        "notes": ["validación local basada en métricas internas"],
    }
    version.metrics.update(validation)
    version.status = "validated" if approved else "rejected"
    ALGO_REPO._persist_to_disk()
    logger.info(f"Validación local completada para {vid}: approved={approved}")
    return validation

def deploy_algorithm(vid: str) -> bool:
    version = ALGO_REPO.get_version(vid)
    if not version:
        logger.warning(f"Intento de deploy de versión inexistente: {vid}")
        return False
    version.status = "deployed"
    version.notes.append(f"Deployed at {time.time()}")
    ALGO_REPO._persist_to_disk()
    logger.info(f"Versión {vid} marcada como deployed (no se toca meteoser.py).")
    return True

def rollback_to_version(vid: str) -> bool:
    target = ALGO_REPO.get_version(vid)
    if not target:
        logger.warning(f"Rollback: versión {vid} no encontrada.")
        return False

    for v in ALGO_REPO.list_versions():
        if v.timestamp > target.timestamp:
            v.status = "rejected"
    target.status = "deployed"
    ALGO_REPO._persist_to_disk()
    logger.info(f"Rollback lógico realizado: ahora {vid} es deployed.")
    return True

def create_and_test_algorithm(spec: Dict[str, Any], test_inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    version = generate_algorithm_from_spec(spec)
    metrics = evaluate_algorithm_version(version.id, test_inputs)
    ext = validate_with_external_services(version.id)
    return {
        "version_id": version.id,
        "metrics": metrics,
        "external_validation": ext,
    }

def smoke_test() -> None:
    logger.info("SMOKE TEST Bloque C: generación, sandbox y evaluación (modo mock).")

    spec = {"objective": "Promedio de temperaturas para recomendaciones", "inputs": ["temps"], "metrics": {"score": "success_rate"}}
    version = generate_algorithm_from_spec(spec)

    test_inputs = [
        {"temps": [20, 21, 19]},
        {"temps": [5, 7, 6]},
        {"temps": []},
    ]

    metrics = evaluate_algorithm_version(version.id, test_inputs)
    print("Evaluación metrics:", metrics)

    ext = validate_with_external_services(version.id)
    print("Validación externa (mock):", ext)

    ok, out, err = _execute_in_sandbox(version.code, input_data={"temps": [12, 14, 13]})
    print("Sandbox run ok:", ok, "output:", out, "err:", bool(err))

    for v in ALGO_REPO.list_versions():
        print(f"- {v.id} status={v.status} metrics={v.metrics}")

if __name__ == "__main__":
    smoke_test()