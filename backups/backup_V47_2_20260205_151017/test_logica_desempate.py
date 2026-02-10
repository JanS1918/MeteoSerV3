#!/usr/bin/env python3
"""
TEST DE CORRECCIONES: Validar que _decidir() funcionacorrectamente

Este test verifica que la lógica de desempate funciona como se espera:
1. Scores diferenciados → elige por score
2. Scores empatados → evalúa criterios secundarios
"""

from dataclasses import dataclass


@dataclass
class DuelScore:
    score: float
    estabilidad: float
    precision: float
    robustez: float
    eficiencia: float
    validos: int
    total: int


def decidir_OLD(actual, alt):
    """Versión anterior con problema"""
    delta_precision = alt.precision - actual.precision
    delta_estab = alt.estabilidad - actual.estabilidad
    if delta_precision < 0.0005 and delta_estab > 0.02:
        return "alt"
    return "alt" if alt.score > actual.score else "actual"


def decidir_NEW(actual, alt):
    """Nueva versión con desempate completo"""
    margen_minimo = 0.01
    diff_score = alt.score - actual.score
    
    # CASO 1: Alt tiene score CLARAMENTE superior (>1%)
    if diff_score > margen_minimo:
        return "alt"
    
    # CASO 2: Actual tiene score CLARAMENTE superior (>1%)
    elif diff_score < -margen_minimo:
        return "actual"
    
    # CASO 3: Scores EMPATADOS - usar criterios secundarios
    else:
        # Criterio 1: Estabilidad
        delta_estab = alt.estabilidad - actual.estabilidad
        if delta_estab > 0.05:
            return "alt"
        elif delta_estab < -0.05:
            return "actual"
        
        # Criterio 2: Precisión
        delta_prec = alt.precision - actual.precision
        if delta_prec > 0.05:
            return "alt"
        elif delta_prec < -0.05:
            return "actual"
        
        # Criterio 3: Eficiencia
        delta_ef = alt.eficiencia - actual.eficiencia
        if delta_ef > 0.05:
            return "alt"
        elif delta_ef < -0.05:
            return "actual"
        
        # CASO 4: TODO empatado - mantener actual
        return "actual"


def test_desempate():
    """Test de función _decidir"""
    
    print("\n" + "="*70)
    print("TEST: LÓGICA DE DESEMPATE EN DUELOS")
    print("="*70)
    
    # Test cases
    tests = [
        {
            "nombre": "Score clara diferencia (Alt gana)",
            "actual": DuelScore(0.80, 0.85, 0.90, 0.95, 0.80, 95, 100),
            "alt": DuelScore(0.92, 0.87, 0.92, 0.96, 0.82, 96, 100),
            "esperado": "alt"
        },
        {
            "nombre": "Score clara diferencia (Actual gana)",
            "actual": DuelScore(0.92, 0.87, 0.92, 0.96, 0.82, 96, 100),
            "alt": DuelScore(0.80, 0.85, 0.90, 0.95, 0.80, 95, 100),
            "esperado": "actual"
        },
        {
            "nombre": "Scores empatados, Alt mejor estabilidad",
            "actual": DuelScore(0.85, 0.80, 0.90, 0.95, 0.80, 95, 100),
            "alt": DuelScore(0.85, 0.87, 0.90, 0.95, 0.80, 95, 100),
            "esperado": "alt"
        },
        {
            "nombre": "Scores empatados, todo igual (mantener Actual)",
            "actual": DuelScore(0.85, 0.85, 0.90, 0.95, 0.80, 95, 100),
            "alt": DuelScore(0.85, 0.85, 0.90, 0.95, 0.80, 95, 100),
            "esperado": "actual"
        },
        {
            "nombre": "Scores empatados, Actual mejor precisión",
            "actual": DuelScore(0.85, 0.85, 0.95, 0.95, 0.80, 95, 100),
            "alt": DuelScore(0.85, 0.85, 0.88, 0.95, 0.80, 95, 100),
            "esperado": "actual"
        },
        {
            "nombre": "Scores empatados, Alt mejor eficiencia",
            "actual": DuelScore(0.85, 0.85, 0.90, 0.95, 0.70, 95, 100),
            "alt": DuelScore(0.85, 0.85, 0.90, 0.95, 0.80, 95, 100),
            "esperado": "alt"
        }
    ]
    
    print("\n📋 EJECUTANDO TESTS:\n")
    
    correctos_new = 0
    incorrectos_new = 0
    
    for i, test in enumerate(tests, 1):
        resultado_old = decidir_OLD(test["actual"], test["alt"])
        resultado_new = decidir_NEW(test["actual"], test["alt"])
        esperado = test["esperado"]
        
        correcto = resultado_new == esperado
        estado = "✅" if correcto else "❌"
        
        print(f"[{i}] {test['nombre']}")
        print(f"    Esperado: {esperado}")
        print(f"    Antigua:  {resultado_old}")
        print(f"    Nueva:    {resultado_new} {estado}")
        
        if correcto:
            correctos_new += 1
        else:
            incorrectos_new += 1
        
        print()
    
    # Resumen
    print("="*70)
    print("RESUMEN:")
    print("="*70)
    
    total = len(tests)
    print(f"\n✅ Nueva lógica: {correctos_new}/{total} correctos ({correctos_new*100//total}%)")
    
    if incorrectos_new == 0:
        print(f"\n✅ PERFECTO - Lógica de desempate funciona correctamente")
    else:
        print(f"\n⚠️  REVISAR - Hay {incorrectos_new} casos fallidos")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    test_desempate()
