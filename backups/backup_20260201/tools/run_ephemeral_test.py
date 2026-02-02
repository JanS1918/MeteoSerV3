import json
import subprocess
import time
import requests

CMD = [r".venv\Scripts\python.exe", "-m", "uvicorn", "main_asgi:app", "--host", "127.0.0.1", "--port", "8080"]


def main() -> None:
    proc = subprocess.Popen(CMD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(2)
        payload = {
            "passkey": "TEST",
            "stationtype": "TestDevice",
            "dateutc": "2026-02-01 16:57:30",
            "pm25_ch1": 548,
        }
        r = requests.post("http://127.0.0.1:8080/ecowitt", data=payload, timeout=5)
        r2 = requests.get("http://127.0.0.1:8080/estado", timeout=5)
        print("POST", r.status_code)
        print("GET", r2.status_code)
        try:
            data = r2.json()
        except Exception:
            data = r2.text

        def find_key(obj, key):
            if isinstance(obj, dict):
                if key in obj:
                    return obj[key]
                for value in obj.values():
                    found = find_key(value, key)
                    if found is not None:
                        return found
            elif isinstance(obj, list):
                for value in obj:
                    found = find_key(value, key)
                    if found is not None:
                        return found
            return None

        if isinstance(data, dict):
            co2 = find_key(data, "co2")
            pm25 = find_key(data, "pm25")
            print("co2:", co2)
            print("pm25:", pm25)
        else:
            print(data)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
