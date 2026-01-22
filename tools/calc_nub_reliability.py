import json
from pathlib import Path

p = Path('data/last_ecowitt_payload.json')
loc = Path('data/last_location.json')
if not p.exists():
    print('No last payload')
    raise SystemExit(1)
raw = json.loads(p.read_text(encoding='utf-8'))
data = raw.get('data') or raw
loc_data = None
if loc.exists():
    try:
        loc_data = json.loads(loc.read_text(encoding='utf-8'))
    except Exception:
        loc_data = None

# sensors we care about
s_temp = data.get('tempf') or data.get('temp')
s_hum = data.get('humidity') or data.get('rh')
s_rad = data.get('solarradiation')
s_uv = data.get('uv') or data.get('uvi')
s_wind = data.get('windspeedmph') or data.get('wind')

score = 0.0
weights = {
    'temp': 25,
    'hum': 25,
    'rad': 20,
    'rad_teor': 10,
    'uv': 5,
    'wind': 5,
}

# temp
if s_temp is not None:
    score += weights['temp']
# hum
if s_hum is not None:
    score += weights['hum']
# rad
rad_present = s_rad is not None
if rad_present:
    try:
        rv = float(s_rad)
        if rv > 0:
            score += weights['rad']
        else:
            # solarradiation=0 may be night; give partial credit
            score += weights['rad'] * 0.4
    except Exception:
        score += weights['rad'] * 0.4
# rad_teor
if loc_data and loc_data.get('lat') is not None and loc_data.get('lon') is not None:
    score += weights['rad_teor']
# uv
if s_uv is not None:
    try:
        uvv = float(s_uv)
        if uvv > 0:
            score += weights['uv']
        else:
            score += weights['uv'] * 0.3
    except Exception:
        score += weights['uv'] * 0.3
# wind
if s_wind is not None:
    score += weights['wind']

# adjust for night: if rad_teor exists and rad is near zero AND time likely night, reduce reliability
# crude check: if solarradiation == 0 and uv == 0
is_night = False
try:
    if (s_rad in (None, '0.00', '0', 0, '0.0') or float(s_rad or 0) == 0.0) and (s_uv in (None, '0', 0, '0.0') or float(s_uv or 0) == 0.0):
        is_night = True
except Exception:
    pass
if is_night:
    score *= 0.8

final = max(0.0, min(100.0, score))
print('Reliability_percent', round(final,1))
print('Details: temp', bool(s_temp), 'hum', bool(s_hum), 'rad', s_rad, 'uv', s_uv, 'wind', bool(s_wind), 'loc', bool(loc_data))
