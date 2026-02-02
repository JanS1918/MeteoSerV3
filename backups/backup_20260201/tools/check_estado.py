import requests, json
url = 'http://127.0.0.1:8080/estado'
try:
    r = requests.get(url, timeout=5)
    data = r.json()
except Exception as e:
    print('GET /estado failed:', e)
    raise SystemExit(1)

sensors = data.get('sensores', {})
keys = ['indoor_air_quality_status','indoor_air_quality_score','co2','pm25']
out = {}
for k in keys:
    v = sensors.get(k)
    out[k] = v if v is not None else 'NO HAY'

print(json.dumps(out, indent=2, ensure_ascii=False))
