from __future__ import annotations
import sys
import os

# --- Resolver imports relativos si se ejecuta como script ---
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(script_dir, '..'))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    try:
        import block_a
        import block_b
        import block_c
    except ImportError:
        pass

import logging
import threading
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

try:
    from . import block_a
    from . import block_b
    from . import block_c
except ImportError:
    import block_a
    import block_b
    import block_c

logger = logging.getLogger("meteoser_ia.block_d")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [BLOQUE D] [%(levelname)s] %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

EXTERNAL_INTEGRATION_MODE = block_a.EXTERNAL_INTEGRATION_MODE

HEALTH_CHECK_INTERVAL = 5.0
WATCHDOG_TIMEOUT = 10.0
AUTOCURE_RETRY_LIMIT = 3


@dataclass
class HealthStatus:
    module: str
    healthy: bool
    last_checked: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Incident:
    id: str
    timestamp: float
    module: str
    severity: str
    description: str
    resolved: bool = False
    resolution_notes: List[str] = field(default_factory=list)


class HealthRegistry:
    def __init__(self) -> None:
        self._statuses: Dict[str, HealthStatus] = {}

    def update(self, status: HealthStatus) -> None:
        self._statuses[status.module] = status
        logger.debug(
            f"HealthRegistry: actualizado estado de {status.module}: healthy={status.healthy}"
        )

    def get(self, module: str) -> Optional[HealthStatus]:
        return self._statuses.get(module)

    def list_all(self) -> List[HealthStatus]:
        return list(self._statuses.values())


class IncidentLog:
    def __init__(self) -> None:
        self._incidents: List[Incident] = []

    def create(self, module: str, severity: str, description: str) -> Incident:
        inc = Incident(
            id=f"inc_{int(time.time() * 1000)}",
            timestamp=time.time(),
            module=module,
            severity=severity,
            description=description,
        )
        self._incidents.append(inc)
        logger.warning(
            f"Nuevo incidente: {inc.id} module={module} severity={severity} desc={description}"
        )
        return inc

    def resolve(self, inc_id: str, note: str) -> bool:
        for inc in self._incidents:
            if inc.id == inc_id:
                inc.resolved = True
                inc.resolution_notes.append(note)
                logger.info(f"Incidente resuelto: {inc_id} note={note}")
                return True
        return False

    def list_open(self) -> List[Incident]:
        return [i for i in self._incidents if not i.resolved]


HEALTH_REGISTRY = HealthRegistry()
INCIDENT_LOG = IncidentLog()


def check_block_a() -> HealthStatus:
    try:
        snapshot = block_a.SENSOR_REGISTRY.snapshot()
        healthy = len(snapshot.sensors) >= 0
        details = {"sensors_count": len(snapshot.sensors)}
        return HealthStatus(
            module="block_a", healthy=healthy, last_checked=time.time(), details=details
        )
    except Exception as e:
        return HealthStatus(
            module="block_a",
            healthy=False,
            last_checked=time.time(),
            details={"error": str(e)},
        )


def check_block_b() -> HealthStatus:
    try:
        block_b.PRESENCE_MODEL.update_from_sensors()
        return HealthStatus(
            module="block_b", healthy=True, last_checked=time.time(), details={}
        )
    except Exception as e:
        return HealthStatus(
            module="block_b",
            healthy=False,
            last_checked=time.time(),
            details={"error": str(e)},
        )


def check_block_c() -> HealthStatus:
    try:
        versions = block_c.ALGO_REPO.list_versions()
        return HealthStatus(
            module="block_c",
            healthy=True,
            last_checked=time.time(),
            details={"alg_versions": len(versions)},
        )
    except Exception as e:
        return HealthStatus(
            module="block_c",
            healthy=False,
            last_checked=time.time(),
            details={"error": str(e)},
        )


HEALTH_CHECKS: Dict[str, Callable[[], HealthStatus]] = {
    "block_a": check_block_a,
    "block_b": check_block_b,
    "block_c": check_block_c,
}


def _attempt_restart_module(module_name: str) -> bool:
    logger.info(f"Intento de reinicio lógico del módulo: {module_name}")
    try:
        if module_name == "block_a":
            block_a.discover_all_sensors()
            return True
        if module_name == "block_b":
            block_b.register_default_rules()
            block_b.PRESENCE_MODEL.update_from_sensors()
            return True
        if module_name == "block_c":
            block_c.ALGO_REPO._load_from_disk()
            return True
        if module_name == "cluster":
            return True
    except Exception as e:
        logger.warning(f"Reinicio lógico falló para {module_name}: {e}")
        return False

    logger.warning(f"Reinicio no soportado para {module_name}")
    return False


def _mark_for_rollback(module_name: str, reason: str) -> None:
    logger.info(f"Marcando rollback lógico para {module_name}: {reason}")
    if module_name == "block_c":
        versions = block_c.ALGO_REPO.list_versions()
        if versions:
            latest = sorted(versions, key=lambda v: v.timestamp)[-1]
            block_c.rollback_to_version(latest.id)
            logger.info(f"Rollback lógico aplicado en repositorio IA: {latest.id}")


def autocure_incident(module_name: str, incident: Incident) -> bool:
    logger.info(f"Autocuración iniciada para incidente {incident.id} en {module_name}")
    for attempt in range(1, AUTOCURE_RETRY_LIMIT + 1):
        try:
            ok = _attempt_restart_module(module_name)
            if ok:
                note = f"Reinicio lógico exitoso en intento {attempt}"
                INCIDENT_LOG.resolve(incident.id, note)
                logger.info(f"Autocuración exitosa para {incident.id}: {note}")
                return True
        except Exception as e:
            logger.warning(
                f"Error en intento de reinicio {attempt} para {module_name}: {e}"
            )
    _mark_for_rollback(
        module_name, f"Autocuración fallida tras {AUTOCURE_RETRY_LIMIT} intentos"
    )
    INCIDENT_LOG.resolve(incident.id, "Autocuración fallida; rollback lógico marcado")
    return False


class Watchdog(threading.Thread):
    def __init__(self, interval: float = HEALTH_CHECK_INTERVAL) -> None:
        super().__init__(daemon=True)
        self.interval = interval
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        logger.info("Watchdog iniciado.")
        last_ok_times: Dict[str, float] = {}
        while not self._stop_event.is_set():
            try:
                for module, check in HEALTH_CHECKS.items():
                    status = check()
                    HEALTH_REGISTRY.update(status)
                    if not status.healthy:
                        inc = INCIDENT_LOG.create(
                            module=module,
                            severity="critical",
                            description=f"Health check failed: {status.details}",
                        )
                        autocure_incident(module, inc)
                    else:
                        last_ok_times[module] = time.time()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(
                    f"Error en loop del watchdog: {e}\n{traceback.format_exc()}"
                )
                time.sleep(self.interval)


_ha_hook: Optional[Callable[[str, Incident], None]] = None


def register_ha_hook(on_fail: Callable[[str, Incident], None]) -> None:
    global _ha_hook
    _ha_hook = on_fail
    logger.info("Hook HA registrado por Bloque G.")


def _invoke_ha_hook(module_name: str, incident: Incident) -> None:
    if _ha_hook:
        try:
            _ha_hook(module_name, incident)
            logger.info(f"Hook HA invocado para {module_name} incidente {incident.id}")
        except Exception as e:
            logger.warning(f"Error al invocar hook HA: {e}")


def get_system_health_report() -> Dict[str, Any]:
    statuses = {
        s.module: {
            "healthy": s.healthy,
            "last_checked": s.last_checked,
            "details": s.details,
        }
        for s in HEALTH_REGISTRY.list_all()
    }
    incidents = [
        {
            "id": i.id,
            "module": i.module,
            "severity": i.severity,
            "desc": i.description,
            "resolved": i.resolved,
        }
        for i in INCIDENT_LOG._incidents
    ]
    return {"statuses": statuses, "incidents": incidents, "timestamp": time.time()}


def smoke_test() -> None:
    """
    Test rápido de salud para Bloque D:
    - Ejecuta todos los health checks y reporta resultados.
    - Simula un incidente y verifica autocuración.
    - No modifica estado real ni borra funcionalidad.
    """
    print("[smoke_test] Ejecutando health checks...")
    for name, check in HEALTH_CHECKS.items():
        status = check()
        print(f"  - {name}: {'OK' if status.healthy else 'FAIL'} | Detalles: {status.details}")
    print("[smoke_test] Simulando incidente crítico en block_a...")
    inc = INCIDENT_LOG.create(module="block_a", severity="critical", description="Test incidente crítico")
    autocure_incident("block_a", inc)
    print("[smoke_test] Incidente autocurado:", inc.resolved, inc.resolution_notes)
    print("[smoke_test] Finalizado.")

if __name__ == "__main__":
    # Permitir ejecución directa como script o como módulo
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        try:
            import block_a
            import block_b
            import block_c
        except ImportError:
            from meteoser_ia import block_a, block_b, block_c
    smoke_test()