# ============================================================
# MÓDULO 10 — CONFIG MANAGER
# Archivo: core/config/config_manager.py
# ============================================================

import os
import json
from typing import Any, Dict, Optional


class ConfigManager:
    def __init__(
        self, base_path: str, env_file: str = ".env", json_file: str = "settings.json"
    ):
        self.base_path = base_path
        self.env_path = os.path.join(base_path, env_file)
        self.json_path = os.path.join(base_path, json_file)

        self.env: Dict[str, str] = {}
        self.json_cfg: Dict[str, Any] = {}

        self._load_env()
        self._load_json()

    # ------------------------------------------------------------
    # ENV
    # ------------------------------------------------------------

    def _load_env(self):
        if not os.path.exists(self.env_path):
            return
        try:
            with open(self.env_path, "r", encoding="utf-8") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln or ln.startswith("#") or "=" not in ln:
                        continue
                    k, v = ln.split("=", 1)
                    self.env[k.strip()] = v.strip()
        except (OSError, ValueError):
            pass

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.env.get(key, default)

    def set_env(self, key: str, value: str):
        self.env[key] = value
        self._save_env()

    def _save_env(self):
        try:
            with open(self.env_path, "w", encoding="utf-8") as f:
                for k, v in self.env.items():
                    f.write(f"{k}={v}\n")
        except OSError:
            pass

    # ------------------------------------------------------------
    # JSON SETTINGS
    # ------------------------------------------------------------

    def _load_json(self):
        if not os.path.exists(self.json_path):
            return
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.json_cfg = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.json_cfg = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.json_cfg.get(key, default)

    def set(self, key: str, value: Any):
        self.json_cfg[key] = value
        self._save_json()

    def _save_json(self):
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.json_cfg, f, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------
    # MERGE
    # ------------------------------------------------------------

    def merged(self) -> Dict[str, Any]:
        out = {}
        out.update(self.json_cfg)
        out.update(self.env)
        return out


# ============================================================
# FIN DEL MÓDULO
# ============================================================
