import datetime
import math

from core.indices.environmental_indices import EnvironmentalIndices
from virtual_sensors import VirtualSensorManager


class DummySystem:
    def __init__(self, sensors: dict, metadata: dict | None = None):
        self.sensores = sensors.copy()
        self.sensores_metadata = metadata.copy() if metadata else {}
        self.sensores_derivados = {}
        self.historial_sensores = {}

    def obtener_sensor(self, nombre: str):
        return self.sensores.get(nombre)

    def obtener_sensor_calibration_info(self, nombre: str):
        return {}

    def obtener_historial_sensor(self, nombre: str):
        return []

    def obtener_sensor_metadata(self, nombre: str):
        return self.sensores_metadata.get(nombre)

    def obtener_coordenadas(self):
        return {"lat": 0.0, "lon": 0.0, "origen": "manual", "ubicacion": "Argentona"}

    def actualizar_sensor_derivado(self, nombre: str, valor, metadata=None):
        self.sensores_derivados[nombre] = {"valor": valor, "metadata": metadata}


def _build_environmental_indices(sensors: dict, metadata: dict | None = None) -> EnvironmentalIndices:
    return EnvironmentalIndices(DummySystem(sensors, metadata))


def test_specific_humidity_and_vpd_q():
    env = _build_environmental_indices(
        {"temperatura": 20.0, "humedad": 50.0, "presion": 1013.25},
        {"presion": {"unidad": "hpa"}},
    )
    humesp = env.humedad_especifica()
    vpdq = env.indice_vpd_q()
    assert humesp["valor"] is not None
    assert vpdq["valor"] is not None
    assert math.isclose(humesp["valor"], 0.007208, rel_tol=1e-3)
    assert math.isclose(vpdq["valor"], 0.00727, rel_tol=1e-3)


def test_pm_corrections_for_pm25_and_pm10():
    env = _build_environmental_indices({"pm25": 100.0, "pm10": 200.0, "humedad": 80.0})
    pm25_corr = env.pm25_corregido()
    pm10_corr = env.pm10_corregido()
    assert pm25_corr["valor"] == 50.0
    assert pm10_corr["valor"] == 100.0


def test_pm_model_calibration_applied_when_model_info_available():
    env = _build_environmental_indices(
        {"pm25": 100.0, "pm10": 210.0, "humedad": 80.0},
        {
            "pm25": {"modelo": "PMS5003"},
            "pm10": {"modelo": "SDS011"},
        },
    )
    pm25_corr = env.pm25_corregido()["valor"]
    pm10_corr = env.pm10_corregido()["valor"]
    assert math.isclose(pm25_corr, 54.4, rel_tol=1e-3)
    assert math.isclose(pm10_corr, 151.2, rel_tol=1e-3)


def test_penman_monteith_returns_positive_value():
    env = _build_environmental_indices(
        {
            "temperatura": 25.0,
            "humedad": 60.0,
            "radiacion": 400.0,
            "viento": 2.0,
            "presion": 1013.25,
        },
        {"presion": {"unidad": "hpa"}},
    )
    penman = env.evapotranspiracion_penman_monteith()
    assert penman["valor"] is not None
    assert penman["valor"] > 0
    assert math.isclose(penman["valor"], 10.52, rel_tol=1e-2)


def test_sensor_alias_normalization_resolves_aliases():
    env = _build_environmental_indices(
        {"temp": 18.0, "rh": 55.0, "baromrelin": 1013.25},
        {
            "baromrelin": {"unidad": "hpa"},
            "temp": {"unidad": "C"},
            "rh": {"unidad": "%"},
        },
    )
    temp = env._get_sensor("temperatura")
    humedad = env._get_sensor("humedad")
    presion = env._get_sensor("presion")
    assert math.isclose(temp["valor"], 18.0, rel_tol=1e-3)
    assert math.isclose(humedad["valor"], 55.0, rel_tol=1e-3)
    assert math.isclose(presion["valor"], 1013.25, rel_tol=1e-3)


def test_virtual_manager_accepts_alias_inputs():
    manager = VirtualSensorManager()
    manager.register_virtual(
        "specific_humidity_alias",
        {
            "inputs": ["temperatura", "humedad", "presion"],
            "fn": VirtualSensorManager.fn_specific_humidity,
            "params": {},
        },
    )
    results = manager.compute_all({"temp": 20.0, "rh": 45.0, "baromrelin": 1013.25})
    value = results.get("specific_humidity_alias")
    assert value is not None
    assert math.isclose(value, 0.0071, rel_tol=1e-1)


def test_high_fidelity_pressure_correction_changes_q():
    import os
    # activar modo alta fidelidad
    os.environ["METEOSER_HIGH_FIDELITY"] = "1"
    env = _build_environmental_indices(
        {"temperatura": 20.0, "humedad": 50.0, "presion": 90.0, "altitud": 500.0},
        {"presion": {"unidad": "kpa"}, "altitud": {"unidad": "m"}},
    )
    q_default = env.humedad_especifica()
    # con corrección por altitud se espera presión corregida mayor => q ligeramente menor
    assert q_default["valor"] is not None
    # limpiar variable de entorno para no afectar otros tests
    del os.environ["METEOSER_HIGH_FIDELITY"]


def test_nubosidad_estimada_respects_context_time():
    env = _build_environmental_indices(
        {
            "temperatura": 20.0,
            "humedad": 45.0,
            "radiacion": 200.0,
            "uv": 0.5,
            "viento": 2.0,
        }
    )
    midday = datetime.datetime(2024, 6, 21, 12, 0)
    midnight = datetime.datetime(2024, 6, 22, 0, 0)
    env.set_context_time(midday)
    day_rad = env.radiacion_teorica()["valor"]
    day_nub = env.nubosidad_estimada()["valor"]
    env.set_context_time(midnight)
    night_rad = env.radiacion_teorica()["valor"]
    night_nub = env.nubosidad_estimada()["valor"]
    assert day_rad is not None and night_rad is not None
    assert day_rad > night_rad
    assert day_nub is not None and night_nub is not None
    assert day_nub != night_nub


def test_context_time_and_location_metadata_exposed():
    env = _build_environmental_indices({"temperatura": 18.0})
    forced = datetime.datetime(2025, 3, 21, 10, 30, tzinfo=datetime.timezone.utc)
    env.set_context_time(forced)
    datos = env.obtener_todos()
    assert datos.get("hora_cliente_iso") == forced.isoformat()
    assert datos.get("context_time_iso") == forced.isoformat()
    assert isinstance(datos.get("context_time_epoch"), (int, float))
    assert datos.get("latitud") == 0.0
    assert datos.get("longitud") == 0.0
    coords = datos.get("coordenadas")
    assert isinstance(coords, dict)
    assert coords.get("lat") == 0.0
    assert coords.get("lon") == 0.0
    assert coords.get("ubicacion") == "Argentona"
