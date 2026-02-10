import json
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class LocationEngine:
    def __init__(self, base_dir: Optional[Path] = None):
        self.lat = None
        self.lon = None
        self.altitud = 0.0  # NEW: Altitude in meters (default sea level)
        self.manual = False
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
            self.altitud = float(data.get("altitud", 0.0))  # NEW: Load altitude
            self.manual = bool(data.get("manual", False))
        except Exception:
            logging.exception("Silent except at 29 - revisar contexto")

    def _save(self):
        try:
            payload = {"lat": self.lat, "lon": self.lon, "altitud": self.altitud, "manual": self.manual}  # NEW: Save altitude
            self._data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            logging.exception("Silent except at 36 - revisar contexto")

    def set_manual_coordinates(self, lat: float, lon: float, altitud: float = 0.0):  # NEW: altitude param
        self.lat = float(lat)
        self.lon = float(lon)
        self.altitud = float(altitud)  # NEW: Set altitude
        self.manual = True
        self._save()

    def clear_manual(self):
        self.manual = False
        self._save()

    def estimate_coordinates(self, system) -> Optional[Dict[str, float]]:
        """
        DEPRECATED: Estimación geográfica movida al BusExpander.
        Este método se mantiene por compatibilidad pero ya no calcula.
        Los subfactores ahora se publican en bus_expander._publish_estimacion_geografica()
        """
        # Coordenadas ya deben estar establecidas manualmente o por otro medio
        if self.lat is not None and self.lon is not None:
            return {"lat": self.lat, "lon": self.lon, "altitud": self.altitud, "origen": "estimada"}
        return None

    def get_coordinates(self, system) -> Optional[Dict[str, float]]:
        if self.manual and self.lat is not None and self.lon is not None:
            return {"lat": self.lat, "lon": self.lon, "altitud": self.altitud, "origen": "manual"}  # NEW: Include altitude
        estimated = self.estimate_coordinates(system)
        if estimated:
            return estimated
        if self.lat is not None and self.lon is not None:
            return {"lat": self.lat, "lon": self.lon, "altitud": self.altitud, "origen": "estimada"}  # NEW: Include altitude
        return None

    # NEW: Dict-like access for bus_expander compatibility
    def get(self, key: str, default=None):
        """Allow LocationEngine to be accessed like a dict (bus_expander compatibility)"""
        if key == "altitud":
            return self.altitud if self.altitud is not None else (default if default is not None else 0.0)
        elif key == "lat":
            return self.lat if self.lat is not None else default
        elif key == "lon":
            return self.lon if self.lon is not None else default
        elif key == "manual":
            return self.manual if self.manual is not None else default
        return default

    # NEW: Load altitude from SRTM (simple version - returns default for now)
    def load_altitude_srtm(self, force: bool = False) -> float:
        """
        Load altitude from SRTM database. 
        For now returns stored altitud. In future: integrate with SRTM API.
        
        Args:
            force: If True, reload from SRTM even if already set
        
        Returns:
            Altitude in meters
        """
        if force or self.altitud is None or self.altitud == 0.0:
            if self.lat is not None and self.lon is not None:
                # TODO: Call real SRTM API here
                # For now: use stored value or default
                return self.altitud if self.altitud else 0.0
        return self.altitud
