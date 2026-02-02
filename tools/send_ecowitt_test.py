import requests
import json
import sys

URL = 'http://127.0.0.1:8080'

def main():
    payload = {
        'pm25_ch1': 548,
        'dateutc': '2026-02-01 00:00:00'
    }
    try:
        print('POST /ecowitt ->', payload)
        r = requests.post(f'{URL}/ecowitt', data=payload, timeout=5)
        print('POST status:', r.status_code)
        try:
            print('POST response json:', r.json())
        except Exception:
            print('POST response text:', r.text)
    except Exception as e:
        print('POST failed:', e)

    try:
        r = requests.get(f'{URL}/estado', timeout=5)
        print('\nGET /estado status:', r.status_code)
        try:
            print(json.dumps(r.json(), indent=2, ensure_ascii=False))
        except Exception:
            print('GET /estado text:', r.text)
    except Exception as e:
        print('GET /estado failed:', e)

if __name__ == '__main__':
    main()
