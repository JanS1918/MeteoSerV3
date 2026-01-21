from core.indices.cetreria.cetreria_indices import calcular_cetreria


def test_cetreria_indices_basic():
    data = {
        "viento_medio": 8.0,
        "rachas": 12.0,
        "temperatura": 18.0,
        "punto_rocio": 10.0,
        "humedad": 60.0,
        "nubosidad_estimada": 30.0,
        "radiacion": 650.0,
        "var_t_5min": 0.2,
        "lluvia_24h": 1.5,
        "lluvia_1h": 0.2,
        "lluvia_rate": 0.4,
        "pm25": 25.0,
        "humedad_suelo": 35.0,
        "temp_tendencia_30m": 0.4,
        "uv": 3.0,
        "sensacion_termica": 17.0,
    }
    out = calcular_cetreria(data)
    assert out["indice_cetreria"] is not None
    assert 0.0 <= out["indice_cetreria"] <= 100.0
    assert 0.0 <= out["viento_cetreria"] <= 100.0
    assert 0.0 <= out["visibilidad_terreno"] <= 100.0
