import asyncio
import time
from typing import Callable, Dict, Optional

from core.logger import get_logger
from core.indices.environmental_indices import EnvironmentalIndices
from core.recommendations.unified_recommendation_engine import UnifiedRecommendationEngine
from core.auto.auto_improvement_engine import AutoImprovementEngine
from core.engines.autoimprovement_engine import AutoImprovementSystem


class AutoRepairEngine:
    """
    Motor de auto-reparación y auto-configuración.
    Solo opera con componentes internos y datos propios.
    """

    def __init__(self, system, discovery_factory: Callable[[], object], stale_minutes: int = 15):
        self.system = system
        self.discovery_factory = discovery_factory
        self.stale_seconds = stale_minutes * 60
        self.log = get_logger("AutoRepairEngine")
        self.last_report: Dict[str, object] = {}
        self._lock = asyncio.Lock()

    def _sensor_staleness(self) -> Dict[str, float]:
        now = time.time()
        staleness = {}
        for nombre, ts in getattr(self.system, "sensores_timestamp", {}).items():
            try:
                if ts is None:
                    continue
                staleness[nombre] = now - float(ts)
            except Exception:
                continue
        return staleness

    def _stale_sensors(self) -> Dict[str, float]:
        staleness = self._sensor_staleness()
        return {k: v for k, v in staleness.items() if v >= self.stale_seconds}

    async def check_and_repair(self) -> Dict[str, object]:
        async with self._lock:
            report = {
                "ts": time.time(),
                "stale_sensors": self._stale_sensors(),
                "actions": [],
                "status": "ok",
            }

            # Asegurar motor de índices
            try:
                if not isinstance(self.system.indices, EnvironmentalIndices):
                    self.system.indices = EnvironmentalIndices(self.system)
                    report["actions"].append("reconectar_indices")
            except Exception:
                report["status"] = "degraded"

            # Asegurar motor de recomendaciones
            try:
                if not getattr(self.system, "recommendation_engine", None):
                    self.system.conectar_recommendation_engine(
                        UnifiedRecommendationEngine(self.system, self.system.indices)
                    )
                    report["actions"].append("reconectar_recomendaciones")
            except Exception:
                report["status"] = "degraded"

            # Asegurar motor de auto-mejora
            try:
                if not getattr(self.system, "auto_improvement_engine", None):
                    self.system.conectar_auto_improvement_engine(AutoImprovementEngine())
                    report["actions"].append("reconectar_auto_mejora")
            except Exception:
                report["status"] = "degraded"

            # Asegurar sistema de auto-mejora/expansión
            try:
                if not getattr(self.system, "auto_improvement_system", None):
                    self.system.conectar_auto_improvement_system(AutoImprovementSystem())
                    report["actions"].append("reconectar_auto_mejora_sistema")
            except Exception:
                report["status"] = "degraded"

            # Reintentar autodetección si hay muchos sensores caducados
            try:
                stale = report["stale_sensors"]
                if stale and len(stale) >= 3:
                    engine = self.discovery_factory()
                    if engine is not None:
                        try:
                            engine.stop()
                        except Exception:
                            pass
                        await engine.start()
                        report["actions"].append("reiniciar_autodeteccion")
            except Exception:
                report["status"] = "degraded"

            self.last_report = report
            return report
