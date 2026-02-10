#!/usr/bin/env python3
"""Script para mostrar un ejemplo real de duelo sin implementar"""

import sys
sys.path.insert(0, '.')

import json
from pathlib import Path
from core.bus.formula_hierarchy import FORMULA_HIERARCHY
from core.monitoring.formula_duel_engine import FormulaDuelEngine

data_dir = Path('data')

# Revisar qué datos tenemos
print("="*70)
print("ESTADO DE DATOS DEL SISTEMA")
print("="*70)

# Sensores metadata
metadata_file = data_dir / 'sensores_metadata.json'
if metadata_file.exists():
    with open(metadata_file, 'r', encoding='utf-8') as f:
        sensores = json.load(f)
    print(f"\n1. Sensores actuales: {len(sensores)} registros")
    if sensores:
        for key, val in list(sensores.items())[:2]:
            print(f"   - {key}: {val.get('valor', 'N/A')} ({val.get('sensor_id', 'N/A')})")
else:
    print("\n1. Sensores actuales: NO HAY ARCHIVO")

# Históricos
historico_file = data_dir / 'sensores_historico.json'
if historico_file.exists():
    with open(historico_file, 'r', encoding='utf-8') as f:
        hist = json.load(f)
    print(f"\n2. Históricos: {len(hist)} parámetros")
    for param, datos in list(hist.items())[:3]:
        num_muestras = len(datos.get('muestras', []))
        print(f"   - {param}: {num_muestras} muestras")
else:
    print("\n2. Históricos: NO HAY ARCHIVO")

# Estado del motor de duelos
state_file = Path('data/formula_duel_state.json')
if state_file.exists():
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
    print(f"\n3. Motor de duelos: Último run = {state.get('last_run', 'Nunca')}")
else:
    print("\n3. Motor de duelos: Sin estado anterior")

# Resultados anteriores
results_file = Path('data/formula_duel_results.json')
if results_file.exists():
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    print(f"\n4. Resultados previos: {len(results)} duelos completados")
    if results:
        for r in results[-3:]:
            print(f"   - {r.get('parametro', '?')}: {r.get('ganador', '?')} vs {r.get('perdedor', '?')}")
else:
    print("\n4. Resultados previos: NO HAY ARCHIVO")

# Mostrar fórmulas disponibles en jerarquía
print("\n" + "="*70)
print("FORMULAS DISPONIBLES EN LA JERARQUIA")
print("="*70)

for param, niveles in FORMULA_HIERARCHY.items():
    print(f"\n{param}:")
    for nivel in niveles[:3]:  # Mostrar primeras 3
        print(f"  - {nivel.nombre} (Elite {nivel.elite}): {nivel.formula.nombre if hasattr(nivel.formula, 'nombre') else 'Unnamed'}")
    if len(niveles) > 3:
        print(f"  ... y {len(niveles) - 3} más")

# Intentar ejecutar el motor una vez
print("\n" + "="*70)
print("EJECUTANDO MOTOR DE DUELOS...")
print("="*70)

engine = FormulaDuelEngine()
print(f"\nDry-run mode: {engine.dry_run}")
print(f"Min clean samples: {engine.min_clean_samples}")
print(f"Clean window: {engine.clean_window_seconds}s")

# Intentar duelo
duelos = engine.run_if_due()
print(f"\nDuelos ejecutados: {len(duelos)} parámetros evaluados")

if duelos:
    print("\n" + "="*70)
    print("RESULTADOS DEL DUELO")
    print("="*70)
    for d in duelos:
        print(f"\nParámetro: {d['parametro']}")
        print(f"  Ganador: {d['ganador']} (score: {d['score_actual']:.4f})")
        print(f"  Actual:  {d['perdedor']} (score: {d['score_alt']:.4f})")
        print(f"  Mejora: +{(d['score_actual'] - d['score_alt'])*100:.1f}%")
        print(f"  Dry-run: {d['dry_run']}")
        if 'escenarios' in d:
            print(f"  Escenarios probados: {d['escenarios']}")
else:
    print("\nNo se ejecutaron duelos. Motivos posibles:")
    print("  - Históricos vacíos o contaminados")
    print("  - Menos de 30 muestras limpias")
    print("  - Última ejecución muy reciente (< 24h)")
    print("  - Sistema detectó alertas recientes")

print("\n" + "="*70)
