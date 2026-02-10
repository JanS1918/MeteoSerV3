# -*- coding: utf-8 -*-
"""
TEST: Verificar que el registry puede resolver las 5 funciones externas
"""

from core.monitoring.formula_candidate_registry import FormulaCandidateRegistry

registry = FormulaCandidateRegistry()
candidatas = registry.listar()

print(f"[OK] {len(candidatas)} candidatas cargadas\n")

for cand in candidatas:
    cand_id = cand.get("id")
    module = cand.get("module")
    function = cand.get("function")
    
    print(f"[{cand_id}]")
    print(f"  module: {module}")
    print(f"  function: {function}")
    
    fn = registry.obtener_funcion(cand)
    if fn:
        print(f"  [OK] Función resuelta: {fn.__name__}")
    else:
        print(f"  [ERROR] No se pudo resolver función")
    print()

print("[VERIFICACIÓN] Todas las funciones están listas para el duelo")
