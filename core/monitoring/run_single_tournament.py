#!/usr/bin/env python3
"""Run a single-parameter tournament duel (safe test run)."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.monitoring.duel_round_robin import run_round_robin


def main() -> None:
    import time
    print("[LOG] Iniciando torneo de sensacion_termica...")
    out_path = Path.cwd() / "data" / "duel_round_robin_report.json"
    t0 = time.time()
    try:
        print("[LOG] Llamando a run_round_robin...")
        report = run_round_robin(
            samples_per_param=5,
            seed=42,
            output_path=out_path,
            include_discovered=True,
            max_combination_size=None,
            max_total_combinations=100,
            use_tournament=True,
            tournament_group_size=4,
            parametros=["sensacion_termica"],
        )
        print(f"[LOG] run_round_robin completado en {time.time()-t0:.2f}s")
        print("Round-robin report written to:", out_path)
        print("parameters", list(report.get("parameters", {}).keys()))
    except Exception as e:
        print(f"[ERROR] Excepción detectada: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"[LOG] Tiempo total transcurrido: {time.time()-t0:.2f}s")


if __name__ == "__main__":
    main()
