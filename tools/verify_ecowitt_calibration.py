from pathlib import Path
import json
from typing import Any

from fastapi.testclient import TestClient
from main_asgi import app, system


PAYLOAD_PATH = Path("data/last_ecowitt_payload.json")
RESULT_PATH = Path("data/ewma_test_results.json")


def main() -> None:
    if not PAYLOAD_PATH.exists():
        raise FileNotFoundError("last_ecowitt_payload.json not found")
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    data = payload.get("data") or {}
    if not data:
        print("No se encontró un payload válido en", PAYLOAD_PATH)
        return

    client = TestClient(app)
    response = client.post("/ecowitt", data=data)
    print(f"POST /ecowitt -> {response.status_code} {response.json()}")

    summary: dict[str, dict[str, Any]] = {}
    for key in sorted(data.keys()):
        calib = system.obtener_sensor_calibration_info(key)
        summary[key] = {
            "valor_crudo": calib.get("valor_crudo"),
            "valor_final": system.sensores.get(key),
            "offset": calib.get("offset"),
            "scale": calib.get("scale"),
            "ewma_alpha": calib.get("ewma_alpha"),
            "aplicado_ewma": calib.get("aplicado_ewma"),
        }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps({"status": response.status_code, "summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resumen guardado en {RESULT_PATH}")


if __name__ == "__main__":
    main()
