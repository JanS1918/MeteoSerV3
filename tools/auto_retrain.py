import argparse
import json
import os
import time

from core.calibration.calibration_engine import build_calibration_factors, save_factors
from core.calibration.cetreria_weights import build_cetreria_weights, load_feedback, save_cetreria_weights


def _load_alerts(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main():
    parser = argparse.ArgumentParser(description="Retraining local basado en métricas")
    parser.add_argument("--force", action="store_true", help="Forzar recalibración aunque no haya alerta")
    parser.add_argument("--min-samples", type=int, default=8)
    parser.add_argument("--alerts", default=os.path.join("data", "alerts_predicciones.json"))
    args = parser.parse_args()

    alert = _load_alerts(args.alerts)
    degradado = bool(alert.get("degradado"))
    if not args.force and not degradado:
        print(json.dumps({"ok": True, "msg": "Sin degradación detectada"}, ensure_ascii=False))
        return

    factors = build_calibration_factors(min_muestras=args.min_samples)
    if factors:
        save_factors(factors)

    rows = load_feedback()
    weights = build_cetreria_weights(rows, min_samples=args.min_samples)
    if weights:
        save_cetreria_weights(weights)

    payload = {
        "ok": True,
        "recalibrado": True,
        "timestamp": time.time(),
        "factors": len(factors or {}),
        "weights": len(weights or {}),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
