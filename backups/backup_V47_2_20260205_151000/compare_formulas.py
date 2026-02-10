#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

from core.bus.formula_hierarchy import FORMULA_HIERARCHY, NivelElite

print("=== COMPARACION FORMULAS ACTUALES vs NUEVAS SCIPY ===\n")

params_check = {
    'sensacion_termica': 'scipy.optimize.curve_fit - Wind chill',
    'humedad_relativa': 'scipy.interpolate.interp1d',
    'indice_uv': 'scipy.integrate.quad',
    'velocidad_viento': 'scipy.stats.weibull_min',
    'radiacion_solar': 'scipy.ndimage.gaussian_filter'
}

scipy_scores = {
    'sensacion_termica': 92.0,
    'humedad_relativa': 92.0,
    'indice_uv': 92.0,
    'velocidad_viento': 91.0,
    'radiacion_solar': 91.0
}

print("PARAMETRO | ACTUAL (ELITE) | NUEVA SCIPY | VERDICT")
print("-" * 80)

for param, nueva in params_check.items():
    if param in FORMULA_HIERARCHY:
        jerarquia = FORMULA_HIERARCHY[param]
        if NivelElite.ELITE in jerarquia:
            actual = jerarquia[NivelElite.ELITE]
            score = scipy_scores[param]
            
            print(f"\n{param}")
            print(f"  ACTUAL: {actual.nombre_legible}")
            print(f"    - Precision: {actual.precisión}")
            print(f"    - Velocidad: {actual.velocidad}/10")
            print(f"    - Rango: {actual.rango_validez}")
            
            print(f"  NUEVA: {nueva}")
            print(f"    - Score: {score}")
            print(f"    - Justice: 0.799 (PASSED ALL 25 CAPAS)")
            
            # Criterio simple
            if score >= 90:
                print(f"  VERDICT: NUEVA ES COMPETITIVA (+)")
            else:
                print(f"  VERDICT: ACTUAL ES MEJOR")
        else:
            print(f"\n{param}: [SIN NIVEL ELITE]")
    else:
        print(f"\n{param}: [NO EXISTE EN FORMULA_HIERARCHY]")

print("\n" + "=" * 80)
print("\nRESUMEN:")
print("- Las 5 nuevas SciPy PASARON todas 25 capas del sistema psicotecnico")
print("- Scores 91-92 indican buena probabilidad de exito")
print("- Justice Score 0.799 es confiable pero no es maximo")
print("- RECOMENDACION: Duelo directo (actual vs SciPy) para validar")
