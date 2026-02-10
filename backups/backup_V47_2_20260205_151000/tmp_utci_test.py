import json
from core.indices.environmental_indices import indice_utci
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
    v = s.get('viento')
    r = s.get('radiacion')
    if t is not None and h is not None and v is not None and r is not None:
        try:
            utci = indice_utci(t, h, v, r, None)
            print('T', t, 'H', h, 'V', v, 'R', r, 'UTCI', utci)
            ok = True
            break
        except Exception as e:
            print('err', e)
            ok = False
            break
print('ok', ok)
