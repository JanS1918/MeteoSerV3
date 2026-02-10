#!/usr/bin/env python
"""Test V48 Integration - UTCI v4.02 + WBGT + Auto-Selector"""

from core.indices.environmental_indices import utci_v4_02_fiala_completo, wbgt_liljegren_completo, FormulaAutoSelector

# Test conditions (realistic tropical scenario)
t = 28.0
rh = 65.0
v = 2.5
tmrt = 35.0
rad = 500.0
pa = 101.325

print("=" * 70)
print("TEST V48: UTCI v4.02 FIALA + WBGT LILJEGREN + AUTO-SELECTOR")
print("=" * 70)

# Test 1: UTCI v4.02 Fiala
print("\n[TEST 1] UTCI v4.02 Fiala (13 micro-valores):")
utci_result = utci_v4_02_fiala_completo(t, rh, v, tmrt, pa)
print(f"  UTCI: {utci_result['utci']:.2f}°C")
print(f"  Micro-valores: {len(utci_result)} campos totales")
for key, val in list(utci_result.items())[:5]:
    if key != "error":
        print(f"    - {key}: {val:.2f}")

# Test 2: WBGT Liljegren (20 micro-valores)
print("\n[TEST 2] WBGT Liljegren (20 micro-valores):")
wbgt_result = wbgt_liljegren_completo(t, rh, v, rad, pa)
print(f"  WBGT Outdoor: {wbgt_result['wbgt']:.2f}°C")
print(f"  Micro-valores: {len(wbgt_result)} campos totales")
for key, val in list(wbgt_result.items())[:5]:
    if key != "error":
        print(f"    - {key}: {val:.2f}")

# Test 3: Auto-Selector
print("\n[TEST 3] Auto-Selector Inteligente:")
selector = FormulaAutoSelector()
decision = selector.select_sensacion_termica(t, rh, v, tmrt, pa)
print(f"  Formula elegida (sensación térmica): {decision.formula_elegida}")
print(f"  Valor: {decision.valor:.2f}°C")
print(f"  Confianza: {decision.confianza}%")
print(f"  Razón: {decision.razon}")

estres_decision = selector.select_estres_termico(t, rh, v, rad, pa)
print(f"\n  Formula elegida (estrés térmico): {estres_decision.formula_elegida}")
print(f"  Valor: {estres_decision.valor:.2f}°C")
print(f"  Confianza: {estres_decision.confianza}%")
print(f"  Razón: {estres_decision.razon}")

print("\n" + "=" * 70)
print("[OK] V48 INTEGRATION TEST COMPLETADO EXITOSAMENTE")
print("=" * 70)
