#!/usr/bin/env python3
"""
AutoOptimizerController

Procesa una cola de propuestas de optimización y las aplica de forma segura
usando SelfModEngine + Watchdog.

- Lee data/auto_optimizer_queue.json
- Valida propuestas
- Aplica cambios con guardia
- Marca estados en la cola
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from self_mod_engine import SelfModEngine

logger = logging.getLogger("meteoser.auto_optimizer")


class AutoOptimizerController:
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._queue_path = base_dir / "data" / "auto_optimizer_queue.json"
        self._queue_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_queue(self) -> Dict[str, Any]:
        if not self._queue_path.exists():
            return {"items": []}
        try:
            return json.loads(self._queue_path.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("No se pudo cargar auto_optimizer_queue.json")
            return {"items": []}

    def _save_queue(self, queue: Dict[str, Any]) -> None:
        try:
            self._queue_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.exception("No se pudo guardar auto_optimizer_queue.json")

    def process_queue(self, engine: SelfModEngine) -> Dict[str, Any]:
        queue = self._load_queue()
        items = queue.get("items", [])
        processed = 0
        applied = 0
        blocked = 0
        rejected = 0

        for item in items:
            if item.get("status") not in (None, "pending"):
                continue
            processed += 1
            proposal = item.get("proposal")
            baseline_metrics = item.get("baseline_metrics")

            if not proposal:
                item["status"] = "rejected"
                item["reason"] = "missing_proposal"
                rejected += 1
                continue

            # validar
            validation = engine.validate_proposal(proposal)
            if not validation.get("ok"):
                item["status"] = "rejected"
                item["reason"] = "validation_failed"
                item["validation"] = validation
                rejected += 1
                continue

            # aplicar con guardia
            result = engine.apply_proposal_guarded(
                proposal,
                baseline_metrics=baseline_metrics,
                policy=None,
                allow_overwrite=False,
            )
            if not result.get("ok", True) and result.get("blocked"):
                item["status"] = "blocked"
                item["reason"] = result.get("reason", "blocked")
                blocked += 1
                continue

            item["status"] = "applied"
            item["applied_ts"] = time.time()
            item["result"] = result
            applied += 1

        queue["items"] = items
        self._save_queue(queue)

        return {
            "processed": processed,
            "applied": applied,
            "blocked": blocked,
            "rejected": rejected,
        }
