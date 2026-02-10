#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

from core.system.system_manager import SystemManager
from core.monitoring.formula_duel_engine import FormulaDuelEngine
from core.monitoring.sensor_data_bridge import SensorDataBridge

print("=" * 80)
print("PRUEBA: 5 BATALLAS DE DUELOS (DRY RUN - SIN APLICAR GANADOR)")
print("=" * 80)

# Iniciar sistema
manager = SystemManager()
system = manager.iniciar()

# Cargar histórico real para alimentar duelos
hist_path = Path("data") / "sensores_historico.json"
if hist_path.exists():
    try:
        datos = json.loads(hist_path.read_text(encoding="utf-8"))
        # Inicializar estructuras si no existen
        system.historial_sensores = getattr(system, "historial_sensores", {}) or {}
        system.sensores_alertas = {}
        system.sensores_metadata = {}

        # Usar las últimas 300 entradas
        def _to_float(val):
            try:
                return float(val)
            except (TypeError, ValueError):
                return None

        bridge = SensorDataBridge(Path("."))
        for fila in datos[-300:]:
            ts = fila.get("timestamp")
            sensores_raw = fila.get("sensores", {}) or {}
            normalizado = bridge._normalizar_datos({"sensores": sensores_raw, "timestamps": {}})
            sensores = normalizado.get("sensores", {}) or {}
            for k, v in sensores.items():
                fv = _to_float(v)
                if fv is None:
                    continue
                system.historial_sensores.setdefault(k, []).append((ts, fv))

        # Definir sensores actuales con el último registro
        if datos:
            system.sensores = datos[-1].get("sensores", {}) or {}
    except Exception as e:
        print(f"[WARNING] No se pudo cargar histórico: {e}")
else:
    print("[WARNING] No existe data/sensores_historico.json")

# Configurar motor de duelos
engine = FormulaDuelEngine()
engine.dry_run = True
engine.max_parametros_por_run = 5
engine.min_clean_samples = 5
engine.sample_size = 50

# Ejecutar duelos
from core.bus.formula_hierarchy import FORMULA_HIERARCHY

# Seleccionar parámetros con fórmulas resolubles
params_validos = []
for parametro, niveles in FORMULA_HIERARCHY.items():
    if len(niveles) < 2:
        continue
    orden = sorted(niveles.keys(), key=lambda n: n.value, reverse=True)
    f1 = niveles[orden[0]]
    f2 = niveles[orden[1]]
    if engine._resolver_funcion(f1) and engine._resolver_funcion(f2):
        params_validos.append(parametro)
    if len(params_validos) >= 5:
        break

print(f"Parámetros con funciones resolubles: {params_validos}")

resultados = []
for parametro in params_validos[:5]:
    niveles = FORMULA_HIERARCHY.get(parametro, {})
    orden = sorted(niveles.keys(), key=lambda n: n.value, reverse=True)
    f1 = niveles[orden[0]]
    f2 = niveles[orden[1]]
    muestras = engine._build_samples(system, f1.requisitos_datos)
    if muestras:
        s1 = engine._evaluar_formula(f1, muestras, system)
        s2 = engine._evaluar_formula(f2, muestras, system)
        print(f"  Eval {parametro}: {f1.nombre_tecnico}={'OK' if s1 else 'SIN SCORE'} | {f2.nombre_tecnico}={'OK' if s2 else 'SIN SCORE'}")
    res = engine._duelo_parametro(system, parametro)
    if res:
        resultados.append(res)

# Persistir resultados como lo haría run()
from pathlib import Path
import json as _json
results_path = Path("data") / "formula_duel_results.json"
results_path.write_text(_json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")

# Mostrar resultados
print("\nResultados guardados en data/formula_duel_results.json")
print("Ganadores (dry-run, no aplicados):")

try:
    import json
    from pathlib import Path
    results_path = Path(__file__).resolve().parent / "data" / "formula_duel_results.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    for i, r in enumerate(results[:5], 1):
        print(f"{i}. {r.get('parametro')} -> ganador: {r.get('ganador')} | dry_run={r.get('dry_run')}")
except Exception as e:
    print(f"No se pudo leer resultados: {e}")
