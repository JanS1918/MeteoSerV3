import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


class OrografiaEngine:
    """Motor orográfico basado en SRTM (Open-Elevation) con cache local."""

    def __init__(self, cache_path: Optional[Path] = None, ttl_hours: int = 168):
        base = Path(__file__).resolve().parents[2]
        if cache_path is None:
            cache_path = base / "data" / "orografia_cache.json"
        self.cache_path = cache_path
        self.ttl_seconds = ttl_hours * 3600
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_path.exists():
            try:
                return json.loads(self.cache_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_cache(self, cache: Dict[str, Any]) -> None:
        try:
            self.cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _cache_key(self, lat: float, lon: float, radius_km: float, step_m: int, azimuth_step: int) -> str:
        return f"{lat:.5f},{lon:.5f},r{radius_km:.1f},s{step_m},a{azimuth_step}"

    def _fetch_elevations(self, points: List[Tuple[float, float]]) -> List[Optional[float]]:
        if not points:
            return []
        results: List[Optional[float]] = []
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            locs = "|".join([f"{lat},{lon}" for lat, lon in batch])
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={locs}"
            try:
                resp = requests.get(url, timeout=8)
                if resp.status_code != 200:
                    results.extend([None] * len(batch))
                    continue
                data = resp.json()
                elevs = [r.get("elevation") for r in data.get("results", [])]
                if len(elevs) != len(batch):
                    results.extend([None] * len(batch))
                    continue
                results.extend([float(e) if e is not None else None for e in elevs])
            except Exception:
                results.extend([None] * len(batch))
        return results

    def _generate_grid(self, lat: float, lon: float, radius_km: float, step_m: int) -> List[Tuple[int, int, float, float]]:
        radius_m = radius_km * 1000.0
        steps = int(radius_m // step_m)
        lat_rad = math.radians(lat)
        grid: List[Tuple[int, int, float, float]] = []
        for dy in range(-steps, steps + 1):
            for dx in range(-steps, steps + 1):
                dist_m = math.hypot(dx * step_m, dy * step_m)
                if dist_m > radius_m:
                    continue
                dlat = (dy * step_m) / 111320.0
                dlon = (dx * step_m) / (111320.0 * math.cos(lat_rad))
                grid.append((dx, dy, lat + dlat, lon + dlon))
        return grid

    def _slope_aspect(self, z_center: float, z_e: float, z_w: float, z_n: float, z_s: float, step_m: int) -> Tuple[float, float]:
        dzdx = (z_e - z_w) / (2.0 * step_m)
        dzdy = (z_n - z_s) / (2.0 * step_m)
        slope = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
        aspect = (math.degrees(math.atan2(dzdy, -dzdx)) + 360.0) % 360.0
        return slope, aspect

    def _horizon_profile(self, points: List[Tuple[int, int, float]], z0: float, step_m: int, azimuth_step: int) -> List[Dict[str, float]]:
        bins = int(360 / azimuth_step)
        max_angles = [-90.0] * bins
        for dx, dy, z in points:
            if dx == 0 and dy == 0:
                continue
            dist_m = math.hypot(dx * step_m, dy * step_m)
            if dist_m <= 0:
                continue
            az = (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0
            idx = int(az // azimuth_step)
            angle = math.degrees(math.atan2(z - z0, dist_m))
            if angle > max_angles[idx]:
                max_angles[idx] = angle
        profile = []
        for i in range(bins):
            profile.append({"azimut_deg": i * azimuth_step, "elevacion_deg": max_angles[i]})
        return profile

    def get_horizon_at(self, profile: List[Dict[str, float]], azimut_deg: float) -> float:
        if not profile:
            return 0.0
        azimut_deg = azimut_deg % 360.0
        step = profile[1]["azimut_deg"] - profile[0]["azimut_deg"] if len(profile) > 1 else 1.0
        idx = int(azimut_deg // step) % len(profile)
        return float(profile[idx].get("elevacion_deg", 0.0))

    def compute(self, lat: float, lon: float, radius_km: float = 8.0, step_m: int = 500, azimuth_step: int = 5) -> Dict[str, Any]:
        key = self._cache_key(lat, lon, radius_km, step_m, azimuth_step)
        cache = self._load_cache()
        item = cache.get(key)
        if item and (time.time() - item.get("timestamp", 0)) < self.ttl_seconds:
            return item.get("data", {})

        grid = self._generate_grid(lat, lon, radius_km, step_m)
        points_latlon = [(g[2], g[3]) for g in grid]
        elevs = self._fetch_elevations(points_latlon)

        grid_elev: List[Tuple[int, int, float]] = []
        z0 = None
        for (dx, dy, _, _), z in zip(grid, elevs):
            if z is None:
                continue
            zf = float(z)
            if dx == 0 and dy == 0:
                z0 = zf
            grid_elev.append((dx, dy, zf))
        if z0 is None:
            z0 = 0.0

        elev_map = {(dx, dy): z for dx, dy, z in grid_elev}
        z_e = elev_map.get((1, 0), z0)
        z_w = elev_map.get((-1, 0), z0)
        z_n = elev_map.get((0, 1), z0)
        z_s = elev_map.get((0, -1), z0)
        slope_deg, aspect_deg = self._slope_aspect(z0, z_e, z_w, z_n, z_s, step_m)

        max_elev = z0
        max_az = 0.0
        max_dist_km = 0.0
        for dx, dy, z in grid_elev:
            if z > max_elev:
                max_elev = z
                dist_m = math.hypot(dx * step_m, dy * step_m)
                max_dist_km = dist_m / 1000.0
                max_az = (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0

        profile = self._horizon_profile(grid_elev, z0, step_m, azimuth_step)

        data = {
            "latitud": lat,
            "longitud": lon,
            "altitud_centro_m": z0,
            "radio_km": radius_km,
            "paso_m": step_m,
            "pendiente_media_deg": slope_deg,
            "orientacion_pendiente_deg": aspect_deg,
            "elevacion_maxima_local_m": max_elev,
            "azimut_maximo_relieve_deg": max_az,
            "distancia_maximo_relieve_km": max_dist_km,
            "perfil_horizonte": profile,
        }

        cache[key] = {"timestamp": time.time(), "data": data}
        self._save_cache(cache)
        return data
