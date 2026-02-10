import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class LocationEngine:
    def __init__(self, base_dir: Optional[Path] = None):
        self.lat = 41.55
        self.lon = 2.4
        self.altitud = 81.0  # Altitud real Argentona
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
            logging.exception("Error cargando ubicación persistida")

    def _save(self):
        try:
            payload = {"lat": self.lat, "lon": self.lon, "altitud": self.altitud, "manual": self.manual}  # NEW: Save altitude
            self._data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            logging.exception("Error guardando ubicación persistida")

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
        elif key in ("lat", "latitud"):
            return self.lat if self.lat is not None else default
        elif key in ("lon", "longitud"):
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
                try:
                    import requests
                    url = f"https://api.open-elevation.com/api/v1/lookup?locations={self.lat},{self.lon}"
                    response = requests.get(url, timeout=8)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("results"):
                            elevation_real = data["results"][0].get("elevation")
                            if elevation_real is not None:
                                self.altitud = float(elevation_real)
                                self._save()
                                return self.altitud
                    else:
                        self._log_error(f"SRTM API status {response.status_code}: {response.text}")
                except Exception as e:
                    self._log_error(f"Error llamando SRTM API: {e}")

                # Si la altitud no se pudo obtener, intentar leer de meteoser_configuracion.txt
                if self.altitud:
                    return self.altitud
                try:
                    with open("meteoser_configuracion.txt", "r", encoding="utf-8") as f:
                        for line in f:
                            if "altitud" in line.lower() or "elevacion" in line.lower():
                                # Permite: altitud: 96
                                try:
                                    valor = float(line.split(":")[-1].strip())
                                    return valor
                                except Exception:
                                    continue
                except Exception:
                    pass
                return 0.0
            self._log_error("SRTM sin lat/lon configuradas")
        return self.altitud

    def _log_error(self, message: str) -> None:
        logging.error(message)
