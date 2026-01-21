import argparse
from typing import List, Tuple

from core.calibration.cetreria_weights import (
    build_cetreria_weights,
    load_feedback,
    save_cetreria_weights,
)


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
    parser = argparse.ArgumentParser(description="Calibración de pesos para índices de cetrería.")
    parser.add_argument("--min-muestras", type=int, default=8)
    parser.add_argument("--solo", type=str, default=None)
    parser.add_argument("--modo", choices=["pesos", "lineal"], default="pesos")
    parser.add_argument("--guardar", action="store_true")
    args = parser.parse_args()

    rows = load_feedback()
    if not rows:
        print("No hay feedback en data/feedback_registros.jsonl")
        return

    if args.modo == "lineal":
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
        return

    print("Calibración de pesos (cetrería):")
    resultados = build_cetreria_weights(rows, min_samples=args.min_muestras, only=args.solo)
    for nombre, meta in resultados.items():
        print(f"- {nombre}: muestras={meta.get('muestras')}, MAE={meta.get('mae'):.2f}, bias={meta.get('bias'):.3f}")

    if not resultados:
        print("No hay suficientes muestras para calibrar.")
        return

    if args.guardar:
        save_cetreria_weights(resultados)
        print("Pesos guardados en data/cetreria_calibracion.json")


if __name__ == "__main__":
    main()
