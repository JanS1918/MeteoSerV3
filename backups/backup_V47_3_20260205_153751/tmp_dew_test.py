import json
from core.indices.environmental_indices import _dew_point
from core.monitoring.sensor_data_bridge import SensorDataBridge

hist = json.loads(open('data/sensores_historico.json','r',encoding='utf-8').read())
bridge = SensorDataBridge(None)

ok = False
for fila in hist[-50:]:
    sensores_raw = fila.get('sensores', {}) or {}
    norm = bridge._normalizar_datos({'sensores': sensores_raw, 'timestamps': {}})
    s = norm.get('sensores', {}) or {}
    t = s.get('temperatura')
    h = s.get('humedad')
    if t is not None and h is not None:
        v = _dew_point(t, h)
        print('T', t, 'H', h, 'dew', v)
        ok = True
        break
print('ok', ok)
