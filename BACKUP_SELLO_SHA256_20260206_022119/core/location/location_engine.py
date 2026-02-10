import json
import logging
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class LocationEngine:
    def __init__(self, base_dir: Optional[Path] = None):
        self.lat = 41.553267
        self.lon = 2.396845
        self.altitud = 118.0  # Altitud total (suelo + mástil)
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
            self.lat = data.get("lat", self.lat)
            self.lon = data.get("lon", self.lon)
            self.altitud = float(data.get("altitud", self.altitud))  # NEW: Load altitude
            self.manual = bool(data.get("manual", self.manual))
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

    def load_altitude_srtm(self, force: bool = False) -> float:
        """
        Load altitude from SRTM database using Open-Elevation API.
        
        Args:
            force: If True, reload from SRTM even if already set
        
        Returns:
            Altitude in meters (from real satellite data)
        """
        if force or self.altitud is None or self.altitud == 0.0:
            if self.lat is not None and self.lon is not None:
                try:
                    import requests
                    url = self._build_srtm_url()
                    headers = self._build_srtm_headers()
                    response = requests.get(url, headers=headers, timeout=8)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("results"):
                            elevation_real = data["results"][0].get("elevation")
                            if elevation_real is not None:
                                self.altitud = float(elevation_real)
                                self._save()
                                logging.info(f"[OK] SRTM API: Altitud real para ({self.lat}, {self.lon}) = {self.altitud}m")
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
                                    logging.info(f"[OK] Altitud desde config file: {valor}m")
                                    return valor
                                except Exception:
                                    continue
                except Exception:
                    pass
                return 0.0
            self._log_error("SRTM sin lat/lon configuradas")
        return self.altitud

    def _build_srtm_url(self) -> str:
        base_url = os.getenv(
            "METEOSER_SRTM_API_URL",
            "https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}",
        )
        # Obtener API key del vault cifrado
        if _HAS_VAULT:
            vault = get_vault()
            api_key = vault.get_srtm_key() or ""
        else:
            api_key = os.getenv("METEOSER_SRTM_API_KEY", "").strip()
        
        url = base_url.replace("{lat}", str(self.lat)).replace("{lon}", str(self.lon))
        if "{api_key}" in url:
            url = url.replace("{api_key}", api_key)
        elif api_key:
            joiner = "&" if "?" in url else "?"
            param_name = os.getenv("METEOSER_SRTM_API_KEY_PARAM", "key").strip() or "key"
            url = f"{url}{joiner}{param_name}={api_key}"
        return url

    def _build_srtm_headers(self) -> Dict[str, str]:
        # Obtener API key del vault cifrado
        if _HAS_VAULT:
            vault = get_vault()
            api_key = vault.get_srtm_key() or ""
        else:
            api_key = os.getenv("METEOSER_SRTM_API_KEY", "").strip()
        
        header_name = os.getenv("METEOSER_SRTM_API_KEY_HEADER", "").strip()
        headers: Dict[str, str] = {}
        if api_key and header_name:
            headers[header_name] = api_key
        return headers

    def _log_error(self, message: str) -> None:
        logging.error(message)
