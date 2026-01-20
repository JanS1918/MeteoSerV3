import json
import time
from pathlib import Path
from typing import Dict, List, Optional


class HabitLearningEngine:
    def __init__(self, base_path: Path, min_samples: int = 20):
        self.base_path = Path(base_path)
        self.min_samples = min_samples
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._profile_path = self.base_path / "habits_profile.json"
        self.profile: Dict[str, Optional[dict]] = {
            "horario_ventilacion": None,
            "preferencias_confort": None,
            "horario_actividad": None,
            "updated_at": None,
        }
        self._load()

    def _load(self) -> None:
        if not self._profile_path.exists():
            return
        try:
            data = json.loads(self._profile_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.profile.update(data)
        except Exception:
            pass

    def _save(self) -> None:
        try:
            self._profile_path.write_text(
                json.dumps(self.profile, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    @staticmethod
    def _percentile(values: List[float], p: float) -> Optional[float]:
        if not values:
            return None
        values = sorted(values)
        k = (len(values) - 1) * p
        f = int(k)
        c = min(f + 1, len(values) - 1)
        if f == c:
            return values[f]
        return values[f] + (values[c] - values[f]) * (k - f)

    def _extract_values(self, history: List[tuple]) -> List[float]:
        vals: List[float] = []
        for _, v in history:
            try:
                vals.append(float(v))
            except Exception:
                continue
        return vals

    def _ventilation_events(self, history: List[tuple], drop_threshold: float, max_dt: int = 1800) -> List[int]:
        events: List[int] = []
        for i in range(1, len(history)):
            t_prev, v_prev = history[i - 1]
            t_now, v_now = history[i]
            try:
                v_prev = float(v_prev)
                v_now = float(v_now)
                t_prev = float(t_prev)
                t_now = float(t_now)
            except Exception:
                continue
            if t_now <= t_prev:
                continue
            if (t_now - t_prev) > max_dt:
                continue
            if (v_prev - v_now) >= drop_threshold:
                hour = time.localtime(t_now).tm_hour
                events.append(hour)
        return events

    def _hourly_histogram(self, hours: List[int]) -> Optional[Dict[str, float]]:
        if not hours:
            return None
        counts = {h: 0 for h in range(24)}
        for h in hours:
            if 0 <= h <= 23:
                counts[h] += 1
        total = sum(counts.values())
        if total == 0:
            return None
        top_hours = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        top = [h for h, c in top_hours if c > 0][:6]
        return {
            "top_horas": top,
            "distribucion": {str(h): round(c / total, 3) for h, c in counts.items()},
            "eventos": total,
        }

    def _activity_hours(self, history: List[tuple]) -> Optional[Dict[str, float]]:
        if not history:
            return None
        buckets = {h: [] for h in range(24)}
        for ts, v in history:
            try:
                v = float(v)
                ts = float(ts)
            except Exception:
                continue
            h = time.localtime(ts).tm_hour
            buckets[h].append(v)
        hourly_avg = {h: (sum(vals) / len(vals)) if vals else None for h, vals in buckets.items()}
        values = [v for v in hourly_avg.values() if v is not None]
        if not values:
            return None
        threshold = self._percentile(values, 0.7)
        if threshold is None:
            return None
        active_hours = [h for h, v in hourly_avg.items() if v is not None and v >= threshold]
        return {
            "horas_activas": sorted(active_hours),
            "promedios": {str(h): (round(v, 2) if v is not None else None) for h, v in hourly_avg.items()},
            "umbral": round(threshold, 2),
        }

    def update_from_system(self, system) -> Dict[str, Optional[dict]]:
        history = getattr(system, "historial_sensores", {}) or {}

        ventilation = None
        source = None
        co2_hist = history.get("co2") or []
        if len(co2_hist) >= self.min_samples:
            events = self._ventilation_events(co2_hist, drop_threshold=150.0)
            ventilation = self._hourly_histogram(events)
            source = "co2"

        if ventilation is None:
            hum_hist = history.get("humedad_interior") or []
            if len(hum_hist) >= self.min_samples:
                events = self._ventilation_events(hum_hist, drop_threshold=7.0)
                ventilation = self._hourly_histogram(events)
                source = "humedad_interior"

        if ventilation is not None:
            ventilation["sensor_base"] = source

        preferencias = None
        temp_hist = self._extract_values(history.get("temperatura_interior") or [])
        hum_int_hist = self._extract_values(history.get("humedad_interior") or [])
        if len(temp_hist) >= self.min_samples or len(hum_int_hist) >= self.min_samples:
            preferencias = {
                "temperatura": {
                    "media": round(sum(temp_hist) / len(temp_hist), 2) if temp_hist else None,
                    "p20": self._percentile(temp_hist, 0.2),
                    "p80": self._percentile(temp_hist, 0.8),
                    "muestras": len(temp_hist),
                },
                "humedad": {
                    "media": round(sum(hum_int_hist) / len(hum_int_hist), 2) if hum_int_hist else None,
                    "p20": self._percentile(hum_int_hist, 0.2),
                    "p80": self._percentile(hum_int_hist, 0.8),
                    "muestras": len(hum_int_hist),
                },
            }

        actividad = None
        luz_hist = history.get("luz") or []
        ruido_hist = history.get("ruido") or []
        if len(luz_hist) >= self.min_samples:
            actividad = self._activity_hours(luz_hist)
            if actividad is not None:
                actividad["sensor_base"] = "luz"
        elif len(ruido_hist) >= self.min_samples:
            actividad = self._activity_hours(ruido_hist)
            if actividad is not None:
                actividad["sensor_base"] = "ruido"

        self.profile = {
            "horario_ventilacion": ventilation,
            "preferencias_confort": preferencias,
            "horario_actividad": actividad,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save()
        return self.profile

    def status(self) -> Dict[str, Optional[dict]]:
        return self.profile
