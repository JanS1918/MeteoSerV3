import argparse
import json
import os
import time
from typing import List, Dict


def _load_history(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _moving_average(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def main():
    parser = argparse.ArgumentParser(description="Monitor simple de degradación de predicciones")
    parser.add_argument("--history", default=os.path.join("data", "metrics_history.jsonl"))
    parser.add_argument("--window", type=int, default=10)
    parser.add_argument("--threshold", type=float, default=0.2, help="Umbral relativo de degradación (0.2 = +20%%)")
    args = parser.parse_args()

    rows = _load_history(args.history)
    maes = [float(r.get("resumen", {}).get("mae_promedio")) for r in rows if r.get("resumen", {}).get("mae_promedio") is not None]
    if len(maes) < max(3, args.window):
        print(json.dumps({"ok": True, "msg": "No hay suficientes muestras para monitorizar"}, ensure_ascii=False))
        return

    last = maes[-1]
    baseline = _moving_average(maes[-args.window:-1])
    degradado = baseline > 0 and last > baseline * (1.0 + args.threshold)

    payload: Dict[str, object] = {
        "timestamp": time.time(),
        "mae_actual": round(last, 4),
        "mae_base": round(baseline, 4),
        "degradado": degradado,
        "threshold": args.threshold,
    }

    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "alerts_predicciones.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
