from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

CALIBRATIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "pm_sensor_calibrations.json"


def _normalize_key(name: str | None) -> str | None:
    if not name:
        return None
    return name.strip().lower().replace(" ", "_")


@lru_cache(maxsize=1)
def _load_calibrations() -> dict[str, dict]:
    if not CALIBRATIONS_PATH.exists():
        return {}
    try:
        with CALIBRATIONS_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


@lru_cache(maxsize=1)
def _normalize_model_map() -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    raw = _load_calibrations()
    for canonical, spec in raw.items():
        canon_key = _normalize_key(canonical)
        if not canon_key:
            continue
        lookup[canon_key] = spec
        aliases = spec.get("aliases")
        if isinstance(aliases, Iterable):
            for alias in aliases:
                ali_key = _normalize_key(alias)
                if ali_key:
                    lookup[ali_key] = spec
    return lookup


def get_calibration_for_model(model: str | None) -> dict | None:
    normalized = _normalize_key(model)
    if not normalized:
        return None
    return _normalize_model_map().get(normalized)


def apply_pm_calibration(pm_value: float, rh: float, model: str | None = None) -> float | None:
    spec = get_calibration_for_model(model)
    if spec is None:
        return None
    try:
        factors = spec.get("factors", {})
        scale = float(factors.get("scale", 1.0))
        rh_rate = float(factors.get("rh_rate", 0.0))
        baseline = float(spec.get("baseline_rh", 0.0))
        multiplier = scale + rh_rate * (rh - baseline)
        return max(0.0, pm_value * max(0.01, multiplier))
    except Exception:
        return None
