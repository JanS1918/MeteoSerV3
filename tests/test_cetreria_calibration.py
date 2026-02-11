from core.calibration.cetreria_weights import build_cetreria_weights


def _row(nombre, valor_real, snapshot):
    return {
        "nombre": nombre,
        "valor_real": valor_real,
        "snapshot": snapshot,
    }


def test_build_cetreria_weights_min_samples():
    rows = []
    for i in range(10):
        snapshot = {
            "sensores": {
                "temperatura": 18.0 + i * 0.1,
                "humedad": 55.0,
                "viento": 6.0 + i * 0.2,
                "rachas": 9.0 + i * 0.2,
                "radiacion": 600.0,
                "lluvia_1h": 0.2,
                "lluvia_24h": 1.0,
                "lluvia_rate": 0.1,
                "pm25": 20.0,
                "humedad_suelo": 35.0,
                "uv": 3.0,
            },
            "indices": {
                "sensacion_termica": 17.0,
                "nubosidad_estimada": 35.0,
                "variabilidad_viento_30m": 0.8,
            },
        }
        rows.append(_row("viento_cetreria", 70.0 - i, snapshot))

    resultados = build_cetreria_weights(rows, min_samples=5)
    assert "viento_cetreria" in resultados
    meta = resultados["viento_cetreria"]
    assert meta.get("muestras") >= 5
    assert "weights" in meta
