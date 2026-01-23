from fastapi.testclient import TestClient

from main_asgi import app


def test_estado_endpoint_responde():
    client = TestClient(app)
    resp = client.get("/estado")
    assert resp.status_code == 200
    data = resp.json()
    assert "sensores" in data
    assert "indices" in data
