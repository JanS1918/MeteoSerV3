from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from . import block_a
from . import block_b
from . import block_c
from . import block_d
from . import block_e
from . import block_f

logger = logging.getLogger("meteoser_ia.block_h")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [BLOQUE H] [%(levelname)s] %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

EXTERNAL_INTEGRATION_MODE = block_a.EXTERNAL_INTEGRATION_MODE

BASE_DIR = os.path.join(os.path.dirname(__file__), "ia_integration")
os.makedirs(BASE_DIR, exist_ok=True)

BACKUP_DIR = os.path.join(BASE_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

METADATA_FILE = os.path.join(BASE_DIR, "integration_metadata.json")

TARGET_MAIN_FILENAME = "meteoser.py"


@dataclass
class BackupRecord:
    id: str
    timestamp: float
    source_path: str
    backup_path: str
    sha256: str
    note: str = ""


@dataclass
class IntegrationMetadata:
    live_enabled: bool = False
    last_backup: Optional[str] = None
    deployed_version: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _secure_copy(src: str, dst: str) -> None:
    tmp = f"{dst}.{int(time.time() * 1000)}.tmp"
    with open(src, "rb") as fr, open(tmp, "wb") as fw:
        shutil.copyfileobj(fr, fw)
        fw.flush()
        os.fsync(fw.fileno())
    os.replace(tmp, dst)
    try:
        os.chmod(dst, 0o600)
    except Exception:
        logger.warning(
            "No se pudieron fijar permisos en backup; comprobar manualmente."
        )


def _persist_metadata(meta: IntegrationMetadata) -> None:
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "live_enabled": meta.live_enabled,
                    "last_backup": meta.last_backup,
                    "deployed_version": meta.deployed_version,
                    "history": meta.history,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
    except Exception as e:
        logger.warning(f"No se pudo persistir metadata: {e}")


def _load_metadata() -> IntegrationMetadata:
    if not os.path.exists(METADATA_FILE):
        return IntegrationMetadata()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return IntegrationMetadata(
            live_enabled=data.get("live_enabled", False),
            last_backup=data.get("last_backup"),
            deployed_version=data.get("deployed_version"),
            history=data.get("history", []),
        )
    except Exception:
        logger.warning("Metadata corrupta o inaccesible; iniciando metadata vacía.")
        return IntegrationMetadata()


def create_backup(source_path: str, note: str = "") -> BackupRecord:
    timestamp = time.time()
    bid = f"bk_{int(timestamp*1000)}"
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source file not found: {source_path}")
    backup_path = os.path.join(BACKUP_DIR, f"{bid}.bak")
    _secure_copy(source_path, backup_path)
    sha = _sha256_of_file(backup_path)
    logger.info(f"Backup creado: {backup_path} sha256={sha}")

    record = BackupRecord(
        id=bid,
        timestamp=timestamp,
        source_path=source_path,
        backup_path=backup_path,
        sha256=sha,
        note=note,
    )
    meta = _load_metadata()
    meta.last_backup = bid
    meta.history.append({"type": "backup", "id": bid, "ts": timestamp, "note": note})
    _persist_metadata(meta)
    return record


def list_backups() -> List[BackupRecord]:
    records: List[BackupRecord] = []
    for fname in os.listdir(BACKUP_DIR):
        path = os.path.join(BACKUP_DIR, fname)
        ts = os.path.getmtime(path)
        records.append(
            BackupRecord(
                id=os.path.splitext(fname)[0],
                timestamp=ts,
                source_path="unknown",
                backup_path=path,
                sha256="unknown",
            )
        )
    return records


def restore_backup(backup_id: str, target_path: str) -> bool:
    meta = _load_metadata()
    candidate = None
    for fname in os.listdir(BACKUP_DIR):
        if fname.startswith(backup_id):
            candidate = os.path.join(BACKUP_DIR, fname)
            break
    if not candidate:
        logger.warning(f"Backup {backup_id} no encontrado en disco.")
        return False
    _secure_copy(candidate, target_path)
    meta.history.append({"type": "restore", "id": backup_id, "ts": time.time()})
    _persist_metadata(meta)
    logger.info(f"Backup {backup_id} restaurado sobre {target_path}")
    return True


def run_predeployment_checks() -> Tuple[bool, List[str]]:
    issues: List[str] = []

    meta = _load_metadata()
    if not meta.last_backup:
        issues.append(
            "No existe backup previo. Crear al menos uno antes de activar LIVE."
        )

    health = block_d.get_system_health_report()
    statuses = health.get("statuses", {})
    for module, s in statuses.items():
        if not s.get("healthy", False):
            issues.append(f"Health check: módulo {module} no saludable.")

    try:
        if not block_e.SECRETS_MANAGER._master_key:
            issues.append("SecretsManager: clave maestra no establecida en memoria.")
    except Exception:
        issues.append(
            "SecretsManager: no accesible o error al comprobar clave maestra."
        )

    recs = block_e.get_hardening_recommendations()
    if not recs:
        issues.append("No se han cargado recomendaciones de hardening.")

    try:
        versions = block_c.ALGO_REPO.list_versions()
        validated = [v for v in versions if v.status in ("validated", "deployed")]
        if not validated:
            issues.append("Repositorio IA: no hay versiones validadas o desplegadas.")
    except Exception:
        issues.append("Repositorio IA: error al listar versiones.")

    ok = len(issues) == 0
    logger.info(f"Predeployment checks completed: ok={ok} issues={len(issues)}")
    return ok, issues


def enable_live_mode(operator_note: str = "") -> bool:
    ok, issues = run_predeployment_checks()
    if not ok:
        logger.warning(f"No se puede activar LIVE: issues={issues}")
        return False

    meta = _load_metadata()
    meta.live_enabled = True
    meta.history.append(
        {"type": "enable_live", "ts": time.time(), "note": operator_note}
    )
    _persist_metadata(meta)
    logger.info("Modo LIVE marcado en metadata. Swap físico habilitado.")
    return True


def disable_live_mode(operator_note: str = "") -> None:
    meta = _load_metadata()
    meta.live_enabled = False
    meta.history.append(
        {"type": "disable_live", "ts": time.time(), "note": operator_note}
    )
    _persist_metadata(meta)
    logger.info("Modo LIVE desactivado en metadata.")


def perform_controlled_swap(
    backup_id: str, target_main_path: str, operator: str = "operator"
) -> bool:
    meta = _load_metadata()
    if not meta.live_enabled:
        logger.warning("Swap rechazado: LIVE no está activado en metadata.")
        return False

    if not os.path.exists(target_main_path):
        logger.warning(f"Ruta objetivo no existe: {target_main_path}")
        return False

    if not meta.last_backup:
        create_backup(target_main_path, note=f"Auto-backup before swap by {operator}")

    if not backup_id:
        backup_id = meta.last_backup

    candidate = None
    for fname in os.listdir(BACKUP_DIR):
        if fname.startswith(backup_id):
            candidate = os.path.join(BACKUP_DIR, fname)
            break
    if not candidate:
        logger.warning(f"Backup {backup_id} no encontrado; abortando swap.")
        return False

    try:
        _secure_copy(candidate, target_main_path)
        meta.deployed_version = backup_id
        meta.history.append({"type": "swap", "ts": time.time(), "backup_id": backup_id, "operator": operator})
        _persist_metadata(meta)
        logger.info(f"Swap físico completado: {backup_id} -> {target_main_path}")
        return True
    except Exception as e:
        logger.error(f"Swap físico falló: {e}")
        return False


def run_integration_tests(timeout: float = 10.0) -> Dict[str, Any]:
    start = time.time()
    report: Dict[str, Any] = {"steps": [], "ok": True}

    try:
        snap = block_a.discover_all_sensors()
        report["steps"].append({"step": "discover_sensors", "count": len(snap.sensors)})

        block_b.register_default_rules()
        report["steps"].append({"step": "register_rules", "ok": True})

        spec = {"objective": "integration_test_avg_temp", "inputs": ["temps"]}
        v = block_c.generate_algorithm_from_spec(spec)
        report["steps"].append({"step": "generate_algorithm", "version": v.id})

        metrics = block_c.evaluate_algorithm_version(v.id, [{"temps": [10, 12, 11]}])
        report["steps"].append({"step": "evaluate_algorithm", "metrics": metrics})

        ext = block_c.validate_with_external_services(v.id)
        report["steps"].append({"step": "external_validation", "result": ext})

        ok_deploy = block_c.deploy_algorithm(v.id)
        report["steps"].append({"step": "deploy_logical", "ok": ok_deploy})

        sid = block_f.start_session(user_id="integration_test")
        resp = block_f.handle_user_text(sid, "¿Qué me pongo hoy?")
        report["steps"].append({"step": "dialog_test", "response": resp["text"]})

    except Exception as e:
        report["ok"] = False
        report["error"] = str(e)
        report["trace"] = traceback.format_exc()
    elapsed = time.time() - start
    report["elapsed"] = elapsed
    logger.info(
        f"Integration tests completed in {elapsed:.2f}s ok={report.get('ok', False)}"
    )
    return report


def record_operation(op_type: str, details: Dict[str, Any]) -> None:
    meta = _load_metadata()
    entry = {"type": op_type, "ts": time.time(), "details": details}
    meta.history.append(entry)
    _persist_metadata(meta)
    logger.info(f"Operación registrada: {op_type}")


def get_integration_history() -> List[Dict[str, Any]]:
    meta = _load_metadata()
    return meta.history


def smoke_test() -> None:
    logger.info("SMOKE TEST Bloque H: integración, backup/restore y swap.")

    try:
        bk = create_backup(TARGET_MAIN_FILENAME, note="Smoke test backup")
        print("Backup creado:", bk.id)
    except Exception as e:
        print("Error creando backup:", e)
        return

    ok, issues = run_predeployment_checks()
    print("Predeployment checks OK:", ok)
    if issues:
        print("Issues encontrados:")
        for it in issues:
            print(" -", it)

    report = run_integration_tests()
    print("Integration test report:", json.dumps(report, indent=2, ensure_ascii=False))

    enabled = enable_live_mode(operator_note="Smoke test enable")
    print("Enable LIVE:", enabled)

    swap_ok = perform_controlled_swap(bk.id, TARGET_MAIN_FILENAME, operator="smoke_test")
    print("Swap:", swap_ok)

    hist = get_integration_history()
    print("\nHistorial de integración (últimos 5):")
    for h in hist[-5:]:
        print("-", h)


if __name__ == "__main__":
    smoke_test()
