import argparse
import json
import os
import time
from typing import Dict, List, Tuple


def _as_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _is_binary(value: float) -> bool:
    return value in (0.0, 1.0)


def _normalize_prob(p: float) -> float:
    if p <= 1.0:
        return max(0.0, min(1.0, p))
    return max(0.0, min(1.0, p / 100.0))


def load_feedback(path: str) -> List[dict]:
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


def backtest(rows: List[dict]) -> Dict[str, dict]:
    per_name: Dict[str, dict] = {}
    for row in rows:
        nombre = row.get("nombre")
        if not nombre:
            continue
        valor = _as_float(row.get("valor"))
        real = _as_float(row.get("valor_real"))
        if valor is None or real is None:
            continue
        info = per_name.setdefault(nombre, {"count": 0, "mae_sum": 0.0, "brier_sum": 0.0, "brier_count": 0})
        info["count"] += 1
        info["mae_sum"] += abs(valor - real)
        if _is_binary(real):
            p = _normalize_prob(valor)
            info["brier_sum"] += (p - real) ** 2
            info["brier_count"] += 1
    resultados: Dict[str, dict] = {}
    for nombre, info in per_name.items():
        count = info["count"]
        mae = info["mae_sum"] / count if count else 0.0
        brier = None
        if info["brier_count"] > 0:
            brier = info["brier_sum"] / info["brier_count"]
        resultados[nombre] = {
            "muestras": count,
            "mae": round(mae, 4),
            "brier": round(brier, 4) if brier is not None else None,
        }
    return resultados


def resumen_global(resultados: Dict[str, dict]) -> Dict[str, float]:
    maes: List[float] = []
    briers: List[float] = []
    for info in resultados.values():
        if info.get("muestras", 0) > 0 and info.get("mae") is not None:
            maes.append(float(info["mae"]))
        if info.get("brier") is not None:
            briers.append(float(info["brier"]))
    avg_mae = sum(maes) / len(maes) if maes else 0.0
    avg_brier = sum(briers) / len(briers) if briers else None
    return {
        "mae_promedio": round(avg_mae, 4),
        "brier_promedio": round(avg_brier, 4) if avg_brier is not None else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Backtest rápido con feedback local")
    parser.add_argument("--path", default=os.path.join("data", "feedback_registros.jsonl"))
    parser.add_argument("--save", action="store_true", help="Guardar resultados en data/metrics_predicciones.json")
    args = parser.parse_args()

    rows = load_feedback(args.path)
    resultados = backtest(rows)
    resumen = resumen_global(resultados)

    payload = {
        "timestamp": time.time(),
        "resumen": resumen,
        "resultados": resultados,
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.save:
        os.makedirs("data", exist_ok=True)
        out_path = os.path.join("data", "metrics_predicciones.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        hist_path = os.path.join("data", "metrics_history.jsonl")
        with open(hist_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": payload["timestamp"], "resumen": resumen}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
