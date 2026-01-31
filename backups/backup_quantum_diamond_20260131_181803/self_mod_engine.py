# ============================================================
# MÓDULO 6 — AUTO‑MODIFICACIÓN INTERNA (CONTROLADA)
# Archivo: core/modification/self_mod_engine.py
# ============================================================
"""
Motor seguro de auto‑modificación controlada.
- Opera en modo sandbox por defecto (no ejecuta cambios reales).
- Crea backups/versiones antes de aplicar cambios.
- Valida cambios con reglas y pruebas básicas.
- Permite aplicar, confirmar y hacer rollback de cambios.
- Registra todas las propuestas y acciones en un log.
No ejecuta código arbitrario automáticamente; requiere confirmación explícita
para aplicar cambios fuera de sandbox.
"""

import os
import shutil
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple

LOG_FILE = "self_mod_log.json"
BACKUP_DIR = "mod_backups"
VERSIONS_FILE = "mod_versions.json"


def _now_ts() -> float:
    return time.time()


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


class SelfModEngine:
    """
    Engine para proponer, validar, aplicar y revertir cambios en el código.
    - base_path: ruta raíz del proyecto (ej: meteoserV3/meteoser_ia)
    - sandbox: True = solo previsualiza; False = aplica cambios reales
    """

    def __init__(self, base_path: str, sandbox: bool = True):
        self.base_path = base_path.rstrip("/")
        self.sandbox = sandbox
        _ensure_dir(self.base_path)
        self.log_path = os.path.join(self.base_path, LOG_FILE)
        self.backup_path = os.path.join(self.base_path, BACKUP_DIR)
        self.versions_path = os.path.join(self.base_path, VERSIONS_FILE)
        _ensure_dir(self.backup_path)
        self._load_state()

    # -------------------------
    # Estado y persistencia
    # -------------------------
    def _load_state(self):
        self.log: List[Dict[str, Any]] = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    self.log = json.load(f)
            except Exception:
                self.log = []

        self.versions: Dict[str, Dict[str, Any]] = {}
        if os.path.exists(self.versions_path):
            try:
                with open(self.versions_path, "r", encoding="utf-8") as f:
                    self.versions = json.load(f)
            except Exception:
                self.versions = {}

    def _persist_log(self):
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(self.log, f, indent=2)
        except Exception:
            pass

    def _persist_versions(self):
        try:
            with open(self.versions_path, "w", encoding="utf-8") as f:
                json.dump(self.versions, f, indent=2)
        except Exception:
            pass

    def _append_log(self, entry: Dict[str, Any]):
        entry["ts"] = _now_ts()
        self.log.append(entry)
        if not self.sandbox:
            self._persist_log()

    # -------------------------
    # Propuesta de cambio
    # -------------------------
    def propose_change(self, description: str, changes: List[Dict[str, Any]]) -> str:
        """
        Proponer un conjunto de cambios.
        changes: lista de dicts con:
          - action: "create" | "update" | "delete" | "move"
          - path: ruta relativa (ej: core/sensors/virtual_sensors.py)
          - content: (para create/update) nuevo contenido como string
          - dst: (para move) destino relativo
        Devuelve proposal_id.
        """
        proposal_id = hashlib.sha1(f"{description}{time.time()}".encode()).hexdigest()[:12]
        proposal = {
            "id": proposal_id,
            "description": description,
            "changes": changes,
            "status": "proposed",
            "sandbox": self.sandbox
        }
        self._append_log({"event": "proposed", "proposal": proposal})
        return proposal_id

    # -------------------------
    # Validación básica
    # -------------------------
    def validate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validaciones:
         - rutas dentro de base_path
         - no sobrescribir archivos fuera del proyecto
         - comprobación sintáctica básica para .py (intentar compile)
         - crear backup previo si se aplicara
        Devuelve dict con 'ok':bool y 'issues':list
        """
        issues = []
        changes = proposal.get("changes", [])
        for ch in changes:
            action = ch.get("action")
            path = ch.get("path", "")
            full = os.path.join(self.base_path, path)
            # seguridad: path must be inside base_path
            if not os.path.abspath(full).startswith(os.path.abspath(self.base_path)):
                issues.append({"path": path, "issue": "path_outside_base"})
                continue
            if action == "create":
                # ok
                pass
            elif action == "update":
                if not os.path.exists(full):
                    issues.append({"path": path, "issue": "target_not_found"})
                else:
                    # basic python syntax check if .py
                    if path.endswith(".py"):
                        try:
                            compile(ch.get("content", ""), path, "exec")
                        except Exception as e:
                            issues.append({"path": path, "issue": f"syntax_error: {e}"})
            elif action == "delete":
                if not os.path.exists(full):
                    issues.append({"path": path, "issue": "target_not_found"})
            elif action == "move":
                dst = ch.get("dst", "")
                full_dst = os.path.join(self.base_path, dst)
                if not os.path.abspath(full_dst).startswith(os.path.abspath(self.base_path)):
                    issues.append({"path": dst, "issue": "dst_outside_base"})
            else:
                issues.append({"action": action, "issue": "unknown_action"})
        ok = len(issues) == 0
        result = {"ok": ok, "issues": issues}
        self._append_log({"event": "validated", "proposal_id": proposal.get("id"), "result": result})
        return result

    # -------------------------
    # Backups y versiones
    # -------------------------
    def _create_backup_for_path(self, rel_path: str) -> Optional[str]:
        full = os.path.join(self.base_path, rel_path)
        if not os.path.exists(full):
            return None
        ts = int(_now_ts())
        sha = _sha256_of_file(full)
        backup_name = f"{rel_path.replace('/', '__')}.{ts}.{sha}.bak"
        backup_full = os.path.join(self.backup_path, backup_name)
        _ensure_dir(os.path.dirname(backup_full) or ".")
        try:
            shutil.copy2(full, backup_full)
            # registrar versión
            self.versions.setdefault(rel_path, {})
            self.versions[rel_path][str(ts)] = {"backup": backup_name, "sha": sha}
            if not self.sandbox:
                self._persist_versions()
            return backup_full
        except Exception:
            return None

    # -------------------------
    # Aplicar propuesta (requiere confirmación explícita)
    # -------------------------
    def apply_proposal(self, proposal: Dict[str, Any], allow_overwrite: bool = False) -> Dict[str, Any]:
        """
        Aplica los cambios. Si sandbox=True, solo previsualiza y crea backups en preview.
        Devuelve resumen con resultados por cambio.
        """
        results = []
        changes = proposal.get("changes", [])
        for ch in changes:
            action = ch.get("action")
            path = ch.get("path", "")
            full = os.path.join(self.base_path, path)
            try:
                if action in ("update", "delete", "move"):
                    # crear backup si existe
                    if os.path.exists(full):
                        self._create_backup_for_path(path)
                if action == "create":
                    content = ch.get("content", "")
                    if self.sandbox:
                        results.append({"action": action, "path": path, "result": "preview_created"})
                    else:
                        _ensure_dir(os.path.dirname(full) or ".")
                        with open(full, "w", encoding="utf-8") as f:
                            f.write(content)
                        results.append({"action": action, "path": path, "result": "created"})
                elif action == "update":
                    content = ch.get("content", "")
                    if self.sandbox:
                        results.append({"action": action, "path": path, "result": "preview_updated"})
                    else:
                        if not os.path.exists(full) and not allow_overwrite:
                            results.append({"action": action, "path": path, "result": "target_missing"})
                        else:
                            _ensure_dir(os.path.dirname(full) or ".")
                            with open(full, "w", encoding="utf-8") as f:
                                f.write(content)
                            results.append({"action": action, "path": path, "result": "updated"})
                elif action == "delete":
                    if self.sandbox:
                        results.append({"action": action, "path": path, "result": "preview_deleted"})
                    else:
                        if os.path.isdir(full):
                            shutil.rmtree(full)
                        elif os.path.exists(full):
                            os.remove(full)
                        results.append({"action": action, "path": path, "result": "deleted"})
                elif action == "move":
                    dst = ch.get("dst", "")
                    full_dst = os.path.join(self.base_path, dst)
                    if self.sandbox:
                        results.append({"action": action, "src": path, "dst": dst, "result": "preview_moved"})
                    else:
                        _ensure_dir(os.path.dirname(full_dst) or ".")
                        shutil.move(full, full_dst)
                        results.append({"action": action, "src": path, "dst": dst, "result": "moved"})
                else:
                    results.append({"action": action, "path": path, "result": "unknown_action"})
            except Exception as e:
                results.append({"action": action, "path": path, "result": "exception", "error": str(e)})
        # registrar resultado
        self._append_log({"event": "applied", "proposal_id": proposal.get("id"), "results": results, "sandbox": self.sandbox})
        # persistir versiones/log si no sandbox
        if not self.sandbox:
            self._persist_versions()
            self._persist_log()
        return {"proposal_id": proposal.get("id"), "results": results, "sandbox": self.sandbox}

    # -------------------------
    # Rollback / Restauración
    # -------------------------
    def list_backups(self, rel_path: str) -> List[Dict[str, Any]]:
        """
        Lista backups disponibles para una ruta relativa.
        """
        entries = []
        versions = self.versions.get(rel_path, {})
        for ts, md in versions.items():
            entries.append({"ts": ts, "backup": md.get("backup"), "sha": md.get("sha")})
        return entries

    def restore_backup(self, rel_path: str, ts: str) -> Dict[str, Any]:
        """
        Restaura un backup identificado por timestamp para rel_path.
        """
        versions = self.versions.get(rel_path, {})
        md = versions.get(str(ts))
        if not md:
            return {"ok": False, "reason": "version_not_found"}
        backup_name = md.get("backup")
        backup_full = os.path.join(self.backup_path, backup_name)
        target_full = os.path.join(self.base_path, rel_path)
        if not os.path.exists(backup_full):
            return {"ok": False, "reason": "backup_missing"}
        if self.sandbox:
            self._append_log({"event": "restore_preview", "rel_path": rel_path, "ts": ts})
            return {"ok": True, "preview": True}
        try:
            _ensure_dir(os.path.dirname(target_full) or ".")
            shutil.copy2(backup_full, target_full)
            self._append_log({"event": "restored", "rel_path": rel_path, "ts": ts})
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "reason": "exception", "error": str(e)}

    # -------------------------
    # Utilidades de inspección
    # -------------------------
    def recent_actions(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.log[-limit:])

    def set_sandbox(self, sandbox: bool):
        self.sandbox = sandbox
        self._append_log({"event": "sandbox_changed", "sandbox": sandbox})
        # persist immediately if disabling sandbox
        if not sandbox:
            self._persist_log()
            self._persist_versions()

# ============================================================
# FIN DEL MÓDULO
# ============================================================