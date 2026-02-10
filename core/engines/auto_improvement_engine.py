"""
AutoImprovementSystem (compatibilidad)
======================================

Adaptador para módulos que esperan core.engines.auto_improvement_engine.
Reexpone AutoImprovementSystem desde core.engines.autoimprovement_engine.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from core.engines.autoimprovement_engine import AutoImprovementSystem  # type: ignore
except Exception:
    class AutoImprovementSystem:  # fallback mínimo
        def __init__(self, *args, **kwargs):
            logger.info("[OK] AutoImprovementSystem initialized (fallback)")
            self.enabled = False

        def start(self):
            pass

        def stop(self):
            pass

        def run_optimization_cycle(self):
            return None

        def registrar_evento(self, *args, **kwargs):
            return None

        def ciclo(self):
            return {}

        def reporte(self):
            return {}
