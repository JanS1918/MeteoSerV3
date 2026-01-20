import json
import os
from typing import List, Tuple

FEEDBACK_PATH = os.path.join("data", "feedback_registros.jsonl")


def _load_feedback() -> List[dict]:
    if not os.path.exists(FEEDBACK_PATH):
        return []
    rows = []
    with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _extract_pairs(rows: List[dict], nombre: str) -> List[Tuple[float, float]]:
    pairs = []
    for row in rows:
        if row.get("nombre") != nombre:
            continue
        valor = row.get("valor")
        real = row.get("valor_real")
        try:
            if valor is None or real is None:
                continue
            x = float(valor)
            y = float(real)
            pairs.append((x, y))
        except Exception:
            continue
    return pairs


def _linear_fit(pairs: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not pairs:
        return 1.0, 0.0
    n = len(pairs)
    sx = sum(x for x, _ in pairs)
    sy = sum(y for _, y in pairs)
    sxx = sum(x * x for x, _ in pairs)
    sxy = sum(x * y for x, y in pairs)
    denom = n * sxx - sx * sx
    if denom == 0:
        return 1.0, 0.0
    a = (n * sxy - sx * sy) / denom
    b = (sy - a * sx) / n
    return a, b


def _mae(pairs: List[Tuple[float, float]]) -> float:
    if not pairs:
        return 0.0
    return sum(abs(x - y) for x, y in pairs) / len(pairs)


def main():
    rows = _load_feedback()
    if not rows:
        print("No hay feedback en data/feedback_registros.jsonl")
        return

    targets = [
        "termales_probabilidad",
        "indice_cetreria",
        "riesgo_niebla",
        "barro_campo",
        "riesgo_helada_local",
    ]
    print("Calibración cetrería (lineal simple):")
    for nombre in targets:
        pairs = _extract_pairs(rows, nombre)
        if not pairs:
            continue
        a, b = _linear_fit(pairs)
        mae = _mae(pairs)
        print(
            f"- {nombre}: muestras={len(pairs)}, MAE={mae:.2f}, ajuste sugerido y=({a:.3f}*x + {b:.3f})"
        )


if __name__ == "__main__":
    main()
