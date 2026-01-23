"""Auto-updater para índices.

Este módulo arranca una tarea en segundo plano que periódicamente:
- ejecuta la auditoría (`tools/indices_audit.py`) para regenerar el informe
- llama a `core.indices.registry.update_registry_and_write_status`

La periodicidad se configura con la variable de entorno `METEOSER_INDEX_AUDIT_INTERVAL` (segundos).
"""
import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from . import registry

LOG = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"


async def _loop(interval: int) -> None:
    while True:
        try:
            LOG.info("Indices auto-updater: ejecutando auditoría y actualización de registro.")
            # Ejecutar el script de auditoría (genera data/indices_audit.md)
            try:
                # Use subprocess to avoid import side-effects
                subprocess.run(["python", str(TOOLS / "indices_audit.py")], check=False)
            except Exception as exc:
                LOG.warning("No se pudo ejecutar tools/indices_audit.py: %s", exc)

            try:
                registry.update_registry_and_write_status()
            except Exception as exc:
                LOG.warning("Error actualizando registry: %s", exc)

            LOG.info("Indices auto-updater: terminado, próxima ejecución en %s segundos.", interval)
        except Exception:
            LOG.exception("Error no esperado en el auto-updater de índices")
        await asyncio.sleep(interval)


def start_auto_index_updater(app: Optional[object] = None) -> None:
    """Iniciar la tarea de auto-actualización en segundo plano.

    Si se llama desde un entorno ASGI, debe llamarse durante el evento de startup.
    """
    interval = int(os.environ.get("METEOSER_INDEX_AUDIT_INTERVAL", "3600"))
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # programar tarea en el bucle existente
        asyncio.create_task(_loop(interval))
    else:
        # no hay loop en ejecución (p. ej. pruebas) — arrancar uno en un hilo
        import threading

        def _runner():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.create_task(_loop(interval))
            new_loop.run_forever()

        t = threading.Thread(target=_runner, daemon=True)
        t.start()
