#!/usr/bin/env python3
"""
AutoChangeWatchdog

Watchdog de cambios con auditoría temporal y rollback automático.
- Registra baseline de métricas por cambio.
- Almacena métricas en ventana temporal.
- Si hay degradación superior a umbrales -> rollback automático.

Diseñado para minimizar intervención humana.
"""

from __future__ import annotations

import json
import logging
import time
import inspect
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

from self_mod_engine import SelfModEngine
from core.bus.parametros_canonicos import (
    normalizar_parametro_entrada,
    normalizar_lista_parametros_entrada,
)

logger = logging.getLogger("meteoser.auto_change_watchdog")


@dataclass
class ChangePolicy:
    window_seconds: int = 6 * 3600
    min_samples: int = 12
    # thresholds como degradación permitida (ej: 0.03 = -3%)
    thresholds: Dict[str, float] = None
    # circuit breaker
    rollback_window_seconds: int = 6 * 3600
    max_rollbacks_in_window: int = 2
    freeze_seconds: int = 12 * 3600

    def __post_init__(self):
        if self.thresholds is None:
            self.thresholds = {
                "precision": 0.03,
                "stability": 0.05,
                "efficiency": 0.08,
                "score": 0.02,
            }


@dataclass
class ChangeRecord:
    change_id: str
    paths: List[str]
    baseline_metrics: Dict[str, float]
    policy: ChangePolicy
    status: str = "active"  # active | reverted | ignored
    created_ts: float = 0.0
    last_eval_ts: Optional[float] = None
    revert_ts: Optional[float] = None
    revert_reason: Optional[str] = None


class AutoChangeWatchdog:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._state_path = base_dir / "data" / "auto_change_watchdog.json"
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state: Dict[str, Any] = {
            "changes": {},
            "metrics": {},
            "safety": {
                "frozen": False,
                "freeze_until": None,
                "reason": None,
                "rollback_events": [],
            },
        }
        self._load_state()

    def _load_state(self) -> None:
        if not self._state_path.exists():
            return
        try:
            self._state = json.loads(self._state_path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("No se pudo cargar auto_change_watchdog.json")
            self._state = {"changes": {}, "metrics": {}, "safety": {"frozen": False, "freeze_until": None, "reason": None, "rollback_events": []}}
        # asegurar claves
        self._state.setdefault("changes", {})
        self._state.setdefault("metrics", {})
        self._state.setdefault("safety", {})
        self._state["safety"].setdefault("frozen", False)
        self._state["safety"].setdefault("freeze_until", None)
        self._state["safety"].setdefault("reason", None)
        self._state["safety"].setdefault("rollback_events", [])

    def _save_state(self) -> None:
        try:
            self._state_path.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("No se pudo guardar auto_change_watchdog.json")

    def _cleanup_rollback_events(self, window_seconds: int) -> None:
        now = time.time()
        events = self._state.get("safety", {}).get("rollback_events", [])
        self._state["safety"]["rollback_events"] = [e for e in events if (now - e.get("ts", 0)) <= window_seconds]

    def _record_rollback_event(self, change_id: str) -> None:
        self._state.setdefault("safety", {}).setdefault("rollback_events", [])
        self._state["safety"]["rollback_events"].append({"ts": time.time(), "change_id": change_id})

    def is_frozen(self) -> bool:
        safety = self._state.get("safety", {})
        if not safety.get("frozen"):
            return False
        freeze_until = safety.get("freeze_until")
        if freeze_until is None:
            return True
        if time.time() >= freeze_until:
            safety["frozen"] = False
            safety["freeze_until"] = None
            safety["reason"] = None
            self._save_state()
            return False
        return True

    def freeze(self, reason: str, freeze_seconds: int) -> None:
        safety = self._state.setdefault("safety", {})
        safety["frozen"] = True
        safety["freeze_until"] = time.time() + freeze_seconds
        safety["reason"] = reason
        self._save_state()

    def can_accept_new_change(self) -> Dict[str, Any]:
        if self.is_frozen():
            safety = self._state.get("safety", {})
            return {"ok": False, "reason": "frozen", "freeze_until": safety.get("freeze_until")}
        return {"ok": True}

    def register_change(
        self,
        change_id: str,
        paths: List[str],
        baseline_metrics: Dict[str, float],
        policy: Optional[ChangePolicy] = None,
    ) -> None:
        if policy is None:
            policy = ChangePolicy()
        record = ChangeRecord(
            change_id=change_id,
            paths=paths,
            baseline_metrics=baseline_metrics,
            policy=policy,
            created_ts=time.time(),
        )
        self._state["changes"][change_id] = asdict(record)
        self._state["metrics"].setdefault(change_id, [])
        self._save_state()

    def record_metrics(self, change_id: str, metrics: Dict[str, float], ts: Optional[float] = None) -> None:
        if ts is None:
            ts = time.time()
        self._state["metrics"].setdefault(change_id, [])
        self._state["metrics"][change_id].append({"ts": ts, "metrics": metrics})
        self._save_state()

    def evaluate(self, change_id: str, self_mod_engine: SelfModEngine) -> Dict[str, Any]:
        record_raw = self._state["changes"].get(change_id)
        if not record_raw:
            return {"ok": False, "reason": "change_not_found"}
        record = self._from_dict(record_raw)
        if record.status != "active":
            return {"ok": True, "status": record.status}

        history = self._state["metrics"].get(change_id, [])
        if not history:
            return {"ok": False, "reason": "no_metrics"}

        now = time.time()
        window_start = now - record.policy.window_seconds
        window_samples = [h for h in history if h["ts"] >= window_start]

        if len(window_samples) < record.policy.min_samples:
            return {"ok": False, "reason": "insufficient_samples", "samples": len(window_samples)}

        avg_metrics: Dict[str, float] = {}
        for k in record.baseline_metrics.keys():
            vals = [h["metrics"].get(k) for h in window_samples if h["metrics"].get(k) is not None]
            if vals:
                avg_metrics[k] = sum(vals) / len(vals)

        degraded = []
        for k, baseline in record.baseline_metrics.items():
            if k not in avg_metrics:
                continue
            threshold = record.policy.thresholds.get(k, 0.0)
            if avg_metrics[k] < baseline * (1.0 - threshold):
                degraded.append({
                    "metric": k,
                    "baseline": baseline,
                    "avg": avg_metrics[k],
                    "threshold": threshold,
                })

        record.last_eval_ts = now

        if degraded:
            # rollback automático
            results = []
            for rel_path in record.paths:
                backups = self_mod_engine.list_backups(rel_path)
                if not backups:
                    results.append({"path": rel_path, "result": "no_backups"})
                    continue
                latest = max(backups, key=lambda b: int(b["ts"]))
                results.append({"path": rel_path, "restore": self_mod_engine.restore_backup(rel_path, latest["ts"])})

            record.status = "reverted"
            record.revert_ts = now
            record.revert_reason = "metric_degradation"
            self._state["changes"][change_id] = asdict(record)

            # circuit breaker
            self._record_rollback_event(change_id)
            self._cleanup_rollback_events(record.policy.rollback_window_seconds)
            rollbacks = self._state.get("safety", {}).get("rollback_events", [])
            if len(rollbacks) >= record.policy.max_rollbacks_in_window:
                self.freeze("rollback_threshold_exceeded", record.policy.freeze_seconds)

            self._save_state()

            return {
                "ok": True,
                "status": record.status,
                "degraded": degraded,
                "rollback": results,
            }

        self._state["changes"][change_id] = asdict(record)
        self._save_state()
        return {"ok": True, "status": record.status, "avg_metrics": avg_metrics}

    def evaluate_all(self, self_mod_engine: SelfModEngine) -> Dict[str, Any]:
        summary = {"evaluated": 0, "reverted": 0, "details": []}
        for change_id in list(self._state.get("changes", {}).keys()):
            res = self.evaluate(change_id, self_mod_engine)
            summary["evaluated"] += 1
            if res.get("status") == "reverted":
                summary["reverted"] += 1
            summary["details"].append({"change_id": change_id, "result": res})
        return summary

    @staticmethod
    def _from_dict(data: Dict[str, Any]) -> ChangeRecord:
        policy_raw = data.get("policy") or {}
        policy = ChangePolicy(
            window_seconds=policy_raw.get("window_seconds", 6 * 3600),
            min_samples=policy_raw.get("min_samples", 12),
            thresholds=policy_raw.get("thresholds", None),
        )
        return ChangeRecord(
            change_id=data.get("change_id"),
            paths=data.get("paths", []),
            baseline_metrics=data.get("baseline_metrics", {}),
            policy=policy,
            status=data.get("status", "active"),
            created_ts=data.get("created_ts", 0.0),
            last_eval_ts=data.get("last_eval_ts"),
            revert_ts=data.get("revert_ts"),
            revert_reason=data.get("revert_reason"),
        )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MÉTODOS PROACTIVOS - Validación de Especificación
    # ═══════════════════════════════════════════════════════════════════════════
    
    def validate_spec_compliance(
        self,
        formula_name: str,
        impl_func,
        spec_required_params: List[str],
        strict: bool = False,
    ) -> tuple:
        """
        PROACTIVO: Valida que una fórmula cumpla su especificación ANTES de aplicarla.
        Modo no estricto: nunca bloquea, solo reporta issues para corrección.
        
        Returns:
            (is_compliant: bool, issues: List[str])
        """
        issues = []
        
        # 1. ¿Acepta todos los parámetros requeridos?
        try:
            sig = inspect.signature(impl_func)
            impl_params = list(sig.parameters.keys())
        except Exception as e:
            return False, [f"No se puede inspeccionar: {e}"]
        
        normalized_impl_params = normalizar_lista_parametros_entrada(impl_params)
        normalized_spec_params = normalizar_lista_parametros_entrada(spec_required_params)

        impl_params_set = set(normalized_impl_params)
        spec_params_set = set(normalized_spec_params)
        
        missing = list(spec_params_set - impl_params_set)
        if missing:
            issues.append(f"WARN: Falta parámetros: {missing}")
        
        # 2. ¿Tiene documentación?
        doc = (impl_func.__doc__ or "").strip()
        if not doc:
            issues.append("WARN: Sin documentación")
        
        # 3. Validaciones específicas por tipo de fórmula
        if "vapor" in formula_name.lower() and "saturacion" not in formula_name.lower():
            # Presión vapor real DEBE tener Enhancement Factor
            if "enhancement" not in doc.lower() and "factor" not in doc.lower():
                issues.append("WARN: Presión vapor real sin mención de Enhancement Factor")

        # 4. Advertir si la firma no usa lenguaje canónico (no bloquea)
        non_canonical_spec = [p for p in spec_required_params if normalizar_parametro_entrada(p) != p]
        non_canonical_impl = [p for p in impl_params if normalizar_parametro_entrada(p) != p]
        if non_canonical_spec:
            logger.warning(
                "[WARNING] Spec con parámetros no canónicos para %s: %s",
                formula_name,
                non_canonical_spec,
            )
        if non_canonical_impl:
            logger.warning(
                "[WARNING] Implementación con parámetros no canónicos para %s: %s",
                formula_name,
                non_canonical_impl,
            )
        
        is_compliant = True if not strict else (len(issues) == 0)
        if issues:
            for issue in issues:
                logger.warning(
                    "[WARNING] MAXIMA: No auto-corregible en %s → %s",
                    formula_name,
                    issue,
                )
        return is_compliant, issues
    
    def block_noncompliant_change(self, formula_name: str, reason: str) -> bool:
        """
        PROACTIVO: Bloquea un cambio si incumple especificación.
        Congela el watchdog para evitar más intentos.
        
        Returns:
            True si fue bloqueado exitosamente
        """
        logger.critical(f"🚫 BLOQUEADO: {formula_name}")
        logger.critical(f"   Razón: {reason}")
        
        # Congelar watchdog
        self._freeze_watchdog(
            reason=f"Fórmula incompleta detectada: {formula_name}. {reason}",
            duration_seconds=24 * 3600  # 24 horas
        )
        
        # Registrar en safety
        self._state["safety"]["rollback_events"].append({
            "timestamp": time.time(),
            "type": "specification_violation",
            "formula": formula_name,
            "reason": reason
        })
        self._save_state()
        
        return True
    
    def _freeze_watchdog(self, reason: str, duration_seconds: int = 12 * 3600):
        """Congela el watchdog por seguridad"""
        freeze_until = time.time() + duration_seconds
        self._state["safety"]["frozen"] = True
        self._state["safety"]["freeze_until"] = freeze_until
        self._state["safety"]["reason"] = reason
        self._save_state()
        
        logger.warning(f"[BLOQUEADO] WATCHDOG CONGELADO por {duration_seconds}s")
        logger.warning(f"   Razón: {reason}")
