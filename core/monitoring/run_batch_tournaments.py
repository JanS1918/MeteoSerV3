#!/usr/bin/env python3
"""
Ejecuta torneos por lotes lógicos: compara todas las fórmulas que calculan el mismo parámetro (X, Y, Z, ...), una a una.
Genera un reporte por parámetro.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.monitoring.duel_round_robin import run_round_robin
import json

def main():
    # Cargar todos los parámetros del auto-registro
    auto_registry_path = Path.cwd() / "data" / "auto_formula_registry.json"
    with open(auto_registry_path, encoding="utf-8") as f:
        auto_registry = json.load(f)
    parametros = list(auto_registry["parameters"].keys())
    print(f"[LOG] Ejecutando torneos por lotes para {len(parametros)} parámetros...")
    out_path = Path.cwd() / "data" / "duel_torneos_lote.json"
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            resultados = json.load(f)
    else:
        resultados = {}
    procesados = set(resultados.keys())
    for param in parametros:
        if param in procesados:
            print(f"[SKIP] {param} ya procesado, saltando...")
            continue
        print(f"[LOG] Torneo para: {param}")
        try:
            report = run_round_robin(
                samples_per_param=5,
                seed=42,
                output_path=None,
                include_discovered=True,
                max_combination_size=None,
                max_total_combinations=100,
                use_tournament=True,
                tournament_group_size=4,
                parametros=[param],
            )
            resultados[param] = report
            print(f"[OK] {param} guardado en lote")
            # Guardar progreso tras cada parámetro
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(resultados, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ERROR] {param}: {e}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"[LOG] Torneos completados. Resultados en: {out_path}")

if __name__ == "__main__":
    main()
