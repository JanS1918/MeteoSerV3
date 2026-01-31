import argparse
from core.calibration.calibration_engine import build_calibration_factors, save_factors


def main():
    parser = argparse.ArgumentParser(description="Calibración global de índices por feedback.")
    parser.add_argument("--min-muestras", type=int, default=5)
    parser.add_argument("--solo", type=str, default=None, help="Nombre exacto a calibrar")
    parser.add_argument("--guardar", action="store_true", help="Guardar factores en data/calibration_factors.json")
    args = parser.parse_args()

    factors = build_calibration_factors(min_muestras=args.min_muestras)
    if not factors:
        print("No hay feedback suficiente en data/feedback_registros.jsonl")
        return

    nombres = sorted(factors.keys())
    print("Calibración global (lineal simple):")
    for nombre in nombres:
        if args.solo and nombre != args.solo:
            continue
        meta = factors.get(nombre, {})
        print(
            f"- {nombre}: muestras={meta.get('muestras')}, MAE={meta.get('mae'):.2f}, "
            f"ajuste sugerido y=({meta.get('a'):.3f}*x + {meta.get('b'):.3f})"
        )

    if args.guardar:
        save_factors(factors)
        print("Factores guardados en data/calibration_factors.json")


if __name__ == "__main__":
    main()
