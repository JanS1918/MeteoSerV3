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
            "dateutc": "2026-02-01 17:10:00",
            "pm25_ch1": 548,
            "sensor_radon": 12,
        }
        resp = requests.post("http://127.0.0.1:8080/ecowitt", data=payload, timeout=5)
        print("POST /ecowitt:", resp.status_code, resp.text)
        estado = requests.get("http://127.0.0.1:8080/estado", timeout=5).json()
        eventos = requests.get("http://127.0.0.1:8080/asistente/eventos", timeout=5).json()
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

        indices = find_key(estado, "indices") or {}
        hw_eventos = []
        if isinstance(eventos, dict):
            hw_eventos = [e for e in eventos.get("eventos", []) if isinstance(e, dict) and e.get("tipo") == "hardware_nuevo"]
        print("co2:", find_key(estado, "co2"))
        print("pm25:", find_key(estado, "pm25"))
        print("sensor_radon:", find_key(estado, "sensor_radon"))
        print("visibilidad_local:", indices.get("visibilidad_local"))
        print("visibilidad_terreno:", indices.get("visibilidad_terreno"))
        print("hardware_nuevo_eventos:", json.dumps(hw_eventos, ensure_ascii=False))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
