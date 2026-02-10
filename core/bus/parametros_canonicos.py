"""
Normalización de parámetros CANÓNICOS del sistema.

Objetivo:
- Unificar lenguaje entre Bus, Optimizador, Validador, Motores y Sensores.
- Evitar divergencias tipo: temp_c vs temperatura, rh vs humedad, presion_pa vs presion.
- Garantizar que TODO hable el mismo idioma canónico.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Any
from pathlib import Path
import json
import threading


# ─────────────────────────────────────────────────────────────────────────────
# Parámetros de ENTRADA (para firmas de funciones y requisitos de datos)
# ─────────────────────────────────────────────────────────────────────────────
INPUT_PARAM_ALIASES: Dict[str, List[str]] = {
    "temperatura": [
        "temp", "temp_c", "temp_celsius", "temperature", "temperature_c",
        "t", "ta", "t_c", "tair", "air_temp", "temperatura_c", "temperatura_celsius",
    ],
    "humedad": [
        "hum", "humedad_rel", "humedad_relativa", "humedad_relativa_pct",
        "humedad_pct", "rh", "relhum", "relative_humidity", "relative_humidity_pct",
    ],
    "presion": [
        "presion_pa", "presion_hpa", "pressure", "pressure_pa", "pressure_hpa",
        "p", "patm", "atm_pressure", "presion_atm", "baro", "barometro", "barometer",
    ],
    "viento": [
        "viento_m_s", "viento_ms", "wind", "wind_speed", "wind_ms", "wind_m_s",
        "vel_viento", "velocidad_viento", "velocidad_viento_m_s", "u", "u10",
    ],
    "radiacion": [
        "rad", "rad_w_m2", "radiacion_w_m2", "radiacion_solar",
        "solar_radiation", "rs", "rs_w_m2",
    ],
    "co2": ["co2", "carbon_dioxide", "dioxido_carbono", "ndir", "meter_co2", "icasa_co2"],
    "pm25": ["pm25", "pm2_5", "pm2.5", "pm2", "pm_2_5", "pm_2_5_ugm3"],
    "pm10": ["pm10", "pm_10", "pm10_ugm3"],
    "pm1": ["pm1", "pm_1", "pm1_ugm3"],
    "uv": ["uv", "ultravioleta", "ultraviolet"],
    "luz": ["luz", "light", "luminosidad", "irradiance"],
    "ruido": ["ruido", "noise", "sonido"],
    "voc": ["voc", "volatil", "compuestos_volatiles"],
    "lluvia": ["lluvia", "rain", "precipitacion", "precip"],
    "wh51": ["wh51", "soil", "suelo", "hum_suelo", "humedad_suelo"],
    "altitud": [
        "altura", "elevacion", "elevation", "altitude", "altitud_m", "altura_m",
    ],
    "latitud": ["latitude", "lat"],
    "longitud": ["longitude", "lon", "lng"],
    "datetime": ["fecha_hora", "timestamp", "time", "fecha", "hora", "datetime_utc", "fecha_hora_utc"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Parámetros del BUS (clave lógica en FORMULA_HIERARCHY)
# ─────────────────────────────────────────────────────────────────────────────
BUS_PARAM_ALIASES: Dict[str, List[str]] = {
    "punto_rocio": ["punto_de_rocio", "temp_rocio", "dew_point", "dewpoint"],
    "presion_vapor": ["vapor_pressure", "vapour_pressure", "presion_de_vapor"],
    "sensacion_termica": [
        "apparent_temperature", "thermal_sensation", "feels_like",
        "sensacion", "indice_sensacion_termica",
    ],
    "evapotranspiracion": ["evapotranspiration", "eto", "et0", "evapo_transpiracion"],
    "densidad_aire": ["air_density", "densidad_del_aire"],
}


def _build_reverse_map(mapping: Dict[str, List[str]]) -> Dict[str, str]:
    reverse: Dict[str, str] = {}
    for canonical, aliases in mapping.items():
        reverse[canonical.lower()] = canonical
        for alias in aliases:
            reverse[alias.lower()] = canonical
    return reverse


_INPUT_ALIAS_TO_CANONICAL = _build_reverse_map(INPUT_PARAM_ALIASES)
_BUS_ALIAS_TO_CANONICAL = _build_reverse_map(BUS_PARAM_ALIASES)

_PERSISTED_ALIAS_LOCK = threading.RLock()
_PERSISTED_ALIAS_TO_CANONICAL: Dict[str, str] = {}
_PERSISTED_ALIAS_PATH = Path(__file__).resolve().parents[2] / "data" / "param_aliases.json"


def _load_persisted_aliases() -> None:
    if not _PERSISTED_ALIAS_PATH.exists():
        return
    try:
        raw = json.loads(_PERSISTED_ALIAS_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            for alias, canonical in raw.items():
                if not isinstance(alias, str) or not isinstance(canonical, str):
                    continue
                _PERSISTED_ALIAS_TO_CANONICAL[alias.lower()] = canonical
    except Exception:
        return


def _save_persisted_aliases() -> None:
    try:
        _PERSISTED_ALIAS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _PERSISTED_ALIAS_PATH.write_text(
            json.dumps(_PERSISTED_ALIAS_TO_CANONICAL, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        return


def _register_persisted_alias(alias: str, canonical: str) -> None:
    if not alias or not canonical:
        return
    alias_key = alias.strip().lower()
    canonical_key = canonical.strip().lower()
    if alias_key == canonical_key:
        return
    with _PERSISTED_ALIAS_LOCK:
        if alias_key in _INPUT_ALIAS_TO_CANONICAL:
            return
        _PERSISTED_ALIAS_TO_CANONICAL[alias_key] = canonical
        _INPUT_ALIAS_TO_CANONICAL[alias_key] = canonical
        _save_persisted_aliases()


_load_persisted_aliases()
if _PERSISTED_ALIAS_TO_CANONICAL:
    _INPUT_ALIAS_TO_CANONICAL.update(_PERSISTED_ALIAS_TO_CANONICAL)


def normalizar_parametro_entrada(nombre: str) -> str:
    if not nombre:
        return nombre
    key = nombre.strip().lower()
    return _INPUT_ALIAS_TO_CANONICAL.get(key, key)


def normalizar_lista_parametros_entrada(params: Iterable[str]) -> List[str]:
    return [normalizar_parametro_entrada(p) for p in (params or [])]


def normalizar_parametro_bus(nombre: str) -> str:
    if not nombre:
        return nombre
    key = nombre.strip().lower()
    return _BUS_ALIAS_TO_CANONICAL.get(key, key)


def normalizar_lista_parametros_bus(params: Iterable[str]) -> List[str]:
    return [normalizar_parametro_bus(p) for p in (params or [])]


def normalizar_dict_parametros_entrada(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return data
    normalized: Dict[str, Any] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            normalized[key] = value
            continue
        canonical = normalizar_parametro_entrada(key)
        if canonical in normalized:
            # preferir clave canónica si ya existe
            if canonical == key:
                normalized[canonical] = value
            continue
        normalized[canonical] = value
    return normalized


def obtener_valor_parametro_entrada(data: Dict[str, Any], canonico: str, default: Any = None) -> Any:
    if not isinstance(data, dict):
        return default
    if canonico in data:
        return data.get(canonico)
    alias_list = INPUT_PARAM_ALIASES.get(canonico, [])
    for alias in alias_list:
        if alias in data:
            return data.get(alias)
    # fallback case-insensitive
    lower_map = {str(k).lower(): k for k in data.keys()}
    if canonico.lower() in lower_map:
        return data.get(lower_map[canonico.lower()])
    for alias in alias_list:
        key = lower_map.get(alias.lower())
        if key is not None:
            return data.get(key)
    return default


def resolver_parametro_entrada(nombre: str) -> str | None:
    """Resuelve un nombre a canónico usando alias y heurística suave."""
    if not nombre:
        return None
    key = nombre.strip().lower().replace("-", "_")
    # 1) alias directos
    direct = _INPUT_ALIAS_TO_CANONICAL.get(key)
    if direct:
        _register_persisted_alias(nombre, direct)
        return direct
    # 2) heurística (contiene)
    if "co2" in key or ("carbon" in key and "dioxide" in key) or "ndir" in key:
        _register_persisted_alias(nombre, "co2")
        return "co2"
    if "temp" in key or "temperatura" in key:
        _register_persisted_alias(nombre, "temperatura")
        return "temperatura"
    if "hum" in key or "humidity" in key:
        _register_persisted_alias(nombre, "humedad")
        return "humedad"
    if "pres" in key or "pressure" in key or "baro" in key:
        _register_persisted_alias(nombre, "presion")
        return "presion"
    if "pm25" in key or "pm2" in key:
        _register_persisted_alias(nombre, "pm25")
        return "pm25"
    if "pm10" in key:
        _register_persisted_alias(nombre, "pm10")
        return "pm10"
    if "pm1" in key:
        _register_persisted_alias(nombre, "pm1")
        return "pm1"
    if "wind" in key or "viento" in key:
        _register_persisted_alias(nombre, "viento")
        return "viento"
    if "rain" in key or "lluv" in key:
        _register_persisted_alias(nombre, "lluvia")
        return "lluvia"
    if "uv" in key:
        _register_persisted_alias(nombre, "uv")
        return "uv"
    if "light" in key or "luz" in key:
        _register_persisted_alias(nombre, "luz")
        return "luz"
    if "noise" in key or "ruido" in key:
        _register_persisted_alias(nombre, "ruido")
        return "ruido"
    if "voc" in key:
        _register_persisted_alias(nombre, "voc")
        return "voc"
    if "soil" in key or "suelo" in key or "hum_suelo" in key or "humedad_suelo" in key:
        _register_persisted_alias(nombre, "wh51")
        return "wh51"
    return None
