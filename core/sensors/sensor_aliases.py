from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

ALIASES_PATH = Path(__file__).resolve().parents[2] / "data" / "sensor_aliases.json"


def _normalize_key(name: str | None) -> str | None:
    if not name:
        return None
    return name.strip().lower().replace(" ", "_")


def _load_alias_data() -> dict[str, Iterable[str]]:
    if not ALIASES_PATH.exists():
        return {}
    try:
        with ALIASES_PATH.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if isinstance(raw, dict):
            return raw
    except Exception:
        pass
    return {}


@lru_cache(maxsize=1)
def _alias_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    raw = _load_alias_data()
    for canonical, aliases in raw.items():
        key = _normalize_key(canonical)
        if not key:
            continue
        lookup[key] = key
        if isinstance(aliases, Iterable):
            for alias in aliases:
                alias_key = _normalize_key(alias)
                if alias_key:
                    lookup[alias_key] = key
    return lookup


@lru_cache(maxsize=1)
def _canonical_alias_groups() -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    raw = _load_alias_data()
    for canonical, aliases in raw.items():
        key = _normalize_key(canonical)
        if not key:
            continue
        members: list[str] = [key]
        if isinstance(aliases, Iterable):
            for alias in aliases:
                alias_key = _normalize_key(alias)
                if alias_key and alias_key not in members:
                    members.append(alias_key)
        groups[key] = members
    return groups


def canonical_sensor_name(name: str | None) -> str | None:
    normalized = _normalize_key(name)
    if not normalized:
        return None
    return _alias_lookup().get(normalized, normalized)


def sensor_candidate_names(name: str | None) -> list[str]:
    if name is None:
        return []
    canonical = canonical_sensor_name(name)
    normalized = _normalize_key(name)
    canonical_key = _normalize_key(canonical)
    candidates: list[str] = []
    for member in _canonical_alias_groups().get(canonical_key or normalized or "", []):
        if member and member not in candidates:
            candidates.append(member)
    if normalized and normalized not in candidates:
        candidates.append(normalized)
    if name and name not in candidates:
        candidates.append(name)
    return candidates
