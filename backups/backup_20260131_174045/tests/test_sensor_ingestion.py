from fastapi.testclient import TestClient
from main_asgi import app

client = TestClient(app)


def test_sensor_virtual_ingestion():
    payload = {"name": "unittest_sensor", "value": "7.5"}
    resp = client.post("/sensor_virtual", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("status") == "OK"
    assert data.get("sensor") in ("unittest_sensor", "unittest_sensor")
    assert float(data.get("value")) == 7.5
