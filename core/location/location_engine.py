import json
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class LocationEngine:
    def __init__(self, base_dir: Optional[Path] = None):
        self.lat = None
        self.lon = None
        self.manual = False
        self.label = None
        self.elevation = None
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self._data_path = base_dir / "data" / "last_location.json"
        self._data_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if not self._data_path.exists():
            return
        try:
            data = json.loads(self._data_path.read_text(encoding="utf-8"))
            self.lat = data.get("lat")
            self.lon = data.get("lon")
            self.manual = bool(data.get("manual", False))
            self.label = data.get("label")
            self.elevation = data.get("elevation")
        except Exception:
            pass

    def _save(self):
        try:
            payload = {
                "lat": self.lat,
                "lon": self.lon,
                "manual": self.manual,
                "label": self.label,
                "elevation": self.elevation,
            }
            self._data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    
    def set_manual_coordinates(self, lat: float, lon: float, label: str | None = None):
        self.lat = float(lat)
        self.lon = float(lon)
        self.manual = True
        self.label = label
        # elevation can be set later via attribute; keep for compatibility
        self._save()

    def set_manual_coordinates_with_elevation(self, lat: float, lon: float, elevation: Optional[float] = None, label: str | None = None):
        self.lat = float(lat)
        self.lon = float(lon)
        self.manual = True
        self.label = label
        try:
            self.elevation = float(elevation) if elevation is not None else None
        except Exception:
            self.elevation = None
        self._save()

    def clear_manual(self):
        self.manual = False
        self.label = None
        self._save()

    def _estimate_lat_from_radiation(self, rad_max: float) -> float:
        if rad_max > 950:
            return 0
        if rad_max > 850:
            return 10
        if rad_max > 750:
            return 25
        if rad_max > 650:
            return 40
        if rad_max > 550:
            return 50
        return 60

    def _estimate_lon_from_peak_hour(self, hour_peak: float) -> float:
        diff = hour_peak - 12.0
        lon_est = diff * 15.0
        if lon_est > 180:
            lon_est -= 360
        if lon_est < -180:
            lon_est += 360
        return lon_est

    def estimate_coordinates(self, system) -> Optional[Dict[str, float]]:
        historial_rad = system.obtener_historial_sensor("radiacion")
        if not historial_rad:
            return None
        try:
            t_peak, rad_max = max(historial_rad, key=lambda x: x[1])
        except Exception:
            return None
        if rad_max is None:
            return None
        try:
            hour_peak = datetime.fromtimestamp(t_peak).hour + (datetime.fromtimestamp(t_peak).minute / 60.0)
        except Exception:
            hour_peak = datetime.now().hour

        lat_est = self._estimate_lat_from_radiation(float(rad_max))
        lon_est = self._estimate_lon_from_peak_hour(float(hour_peak))

        self.lat = round(lat_est, 4)
        self.lon = round(lon_est, 4)
        self.manual = False
        self._save()
        return {"lat": self.lat, "lon": self.lon, "origen": "estimada"}

    def get_coordinates(self, system) -> Optional[Dict[str, float]]:
        if self.manual and self.lat is not None and self.lon is not None:
            payload = {"lat": self.lat, "lon": self.lon, "origen": "manual"}
            if self.label:
                payload["ubicacion"] = self.label
            if self.elevation is not None:
                payload["elevation"] = self.elevation
            return payload
        estimated = self.estimate_coordinates(system)
        if estimated:
            return estimated
        if self.lat is not None and self.lon is not None:
            payload = {"lat": self.lat, "lon": self.lon, "origen": "estimada"}
            if self.label:
                payload["ubicacion"] = self.label
            return payload
        return None
