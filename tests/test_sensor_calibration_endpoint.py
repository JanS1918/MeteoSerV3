from fastapi.testclient import TestClient
from main_asgi import app

def test_sensor_calibration_endpoint():
    client = TestClient(app)
    r = client.get('/internal/sensor_calibration')
    assert r.status_code == 200
    data = r.json()
    assert 'sensores_metadata' in data
    assert 'sensor_ewma_state' in data
    assert 'sensor_calibration_info' in data
