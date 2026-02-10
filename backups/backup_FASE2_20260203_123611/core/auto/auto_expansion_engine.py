from typing import Dict, List

from core.indices.index_catalog import INDEX_CATALOG


class AutoExpansionEngine:
    """
    Motor de auto-expansión: analiza sensores disponibles y sugiere índices posibles.
    """

    def __init__(self, system):
        self.system = system

    def report(self) -> Dict[str, List[str]]:
        disponibles = set(self.system.sensores.keys())
        disponibles.update(getattr(self.system, "sensores_derivados", {}).keys())
        ready = []
        missing = {}
        for nombre, meta in INDEX_CATALOG.items():
            req = set(meta.get("sensores", []))
            faltan = sorted(list(req - disponibles))
            if not faltan:
                ready.append(nombre)
            else:
                missing[nombre] = faltan
        return {
            "indices_listos": sorted(ready),
            "indices_pendientes": missing,
        }
