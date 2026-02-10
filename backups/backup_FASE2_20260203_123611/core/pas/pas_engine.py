import json
import time
from pathlib import Path
from typing import Dict, Optional


class PASEngine:
    """
    Huella atmosférica personal (PAS) basada en sensores propios.
    Guarda promedios por hora para comparar desviaciones.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._data_path = base_dir / "data" / "pas_profiles.json"
        self._data_path.parent.mkdir(parents=True, exist_ok=True)
        self._profiles: Dict[str, Dict[str, float]] = {}
        self._last_update: Optional[float] = None
        self._load()

    def _load(self):
        if not self._data_path.exists():
            return
        try:
            data = json.loads(self._data_path.read_text(encoding="utf-8"))
            self._profiles = data.get("profiles", {}) or {}
            self._last_update = data.get("last_update")
        except Exception:
            logging.exception("Silent except at 29 - revisar contexto")

    def _save(self):
        try:
            payload = {
                "profiles": self._profiles,
                "last_update": self._last_update,
            }
            self._data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            logging.exception("Silent except at 39 - revisar contexto")

    def _hour_key(self, ts: float) -> str:
        hour = time.localtime(ts).tm_hour
        return f"h{hour:02d}"

    def update(self, sensores: Dict[str, object]) -> None:
        ts = time.time()
        key = self._hour_key(ts)
        current = self._profiles.get(key, {"n": 0})

        def _acc(name: str, value):
            if value is None:
                return
            try:
                v = float(value)
            except Exception:
                return
            n = current.get("n", 0)
            avg = current.get(name, v)
            avg = (avg * n + v) / (n + 1)
            current[name] = round(avg, 3)

        _acc("temperatura", sensores.get("temperatura_interior") or sensores.get("temperatura"))
        _acc("humedad", sensores.get("humedad_interior") or sensores.get("humedad"))
        _acc("co2", sensores.get("co2"))
        _acc("pm25", sensores.get("pm25"))
        _acc("ruido", sensores.get("ruido"))
        _acc("luz", sensores.get("luz"))

        current["n"] = int(current.get("n", 0)) + 1
        self._profiles[key] = current
        self._last_update = ts
        self._save()

    def score(self, sensores: Dict[str, object]) -> Dict[str, float]:
        if not self._profiles:
            return {"score": 0.0}
        key = self._hour_key(time.time())
        profile = self._profiles.get(key)
        if not profile:
            return {"score": 0.0}

        def _dist(name: str, value):
            if value is None or name not in profile:
                return 0.0
            try:
                v = float(value)
            except Exception:
                return 0.0
            return abs(v - float(profile.get(name, v)))

        total = 0.0
        total += _dist("temperatura", sensores.get("temperatura_interior") or sensores.get("temperatura"))
        total += _dist("humedad", sensores.get("humedad_interior") or sensores.get("humedad"))
        total += _dist("co2", sensores.get("co2")) * 0.02
        total += _dist("pm25", sensores.get("pm25")) * 0.1
        total += _dist("ruido", sensores.get("ruido")) * 0.1
        total += _dist("luz", sensores.get("luz")) * 0.1
        score = max(0.0, min(100.0, 100.0 - total))
        return {"score": round(score, 2), "base": profile}

    def status(self, sensores: Dict[str, object]) -> Dict[str, object]:
        return {
            "last_update": self._last_update,
            "profile_count": len(self._profiles),
            "score": self.score(sensores),
        }
