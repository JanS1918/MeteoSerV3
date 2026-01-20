import json
import time
from pathlib import Path


class AutoImprovementEngine:
    def __init__(self, base_dir: Path | None = None):
        self.algoritmos = {}
        self.metricas = {}
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._data_path = base_dir / "data" / "auto_improvement_stats.json"
        self._data_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def registrar(self, nombre, funcion):
        versiones = self.algoritmos.get(nombre, [])
        versiones.append({
            "version": len(versiones) + 1,
            "funcion": funcion,
            "errores": [],
            "aciertos": []
        })
        self.algoritmos[nombre] = versiones

    def mejor(self, nombre):
        versiones = self.algoritmos.get(nombre)
        if not versiones:
            return None
        return versiones[-1]

    def ejecutar(self, nombre, *args, **kwargs):
        version = self.mejor(nombre)
        if not version:
            return None
        return version["funcion"](*args, **kwargs)

    def feedback(self, nombre, error, detalle):
        version = self.mejor(nombre)
        if not version:
            return
        if error:
            version["errores"].append(detalle)
        else:
            version["aciertos"].append(detalle)

    def _load(self):
        if not self._data_path.exists():
            return
        try:
            data = json.loads(self._data_path.read_text(encoding="utf-8"))
            self.metricas = data.get("metricas", {}) or {}
        except Exception:
            pass

    def _save(self):
        try:
            payload = {
                "metricas": self.metricas,
                "ts": time.time(),
            }
            self._data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def registrar_error(self, nombre: str, real: float, estimado: float) -> None:
        try:
            error = abs(real - estimado)
        except Exception:
            return
        stats = self.metricas.get(nombre, {"n": 0, "mae": 0.0, "last": None})
        n = stats.get("n", 0) + 1
        mae_prev = stats.get("mae", 0.0)
        mae = (mae_prev * (n - 1) + error) / n
        stats.update({"n": n, "mae": round(mae, 4), "last": error, "ts": time.time()})
        self.metricas[nombre] = stats
        self._save()

    def reporte(self) -> dict:
        return self.metricas