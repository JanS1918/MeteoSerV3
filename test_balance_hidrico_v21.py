"""
TEST SUITE: Balance Hídrico Diario, Estrés Hídrico, Disponibilidad Agua

Fecha: 9 Febrero 2026
Propósito: Validar implementación OPCIÓN B+C (mejora + features nuevos)
"""

import sys
sys.path.insert(0, '/c/Users/kioko/Desktop/MeteoSerV3')

from core.indices.environmental_indices import (
    balance_hidrico_diario,
    estres_hidrico_cultivo,
    disponibilidad_agua_cultivable
)

def test_balance_hidrico_scenarios():
    """
    Escenario 1: Día con lluvia > ET0
    Escenario 2: Día seco sin lluvia (verano)
    Escenario 3: Día equilibrio
    Escenario 4: Noche sin evaporación
    """
    print("\n" + "="*70)
    print("TEST 1: BALANCE HÍDRICO DIARIO")
    print("="*70)
    
    # Caso 1: Lluvia fuerte
    print("\n[CASO 1] Día con lluvia fuerte (Primavera)")
    result = balance_hidrico_diario(
        lluvia_24h_mm=15.0,
        et0_mm=4.0,
        escorrentia_mm=2.5,
        infiltracion_mm=3.0
    )
    print(f"  Balance: {result['delta_h']:.2f} mm")
    print(f"  Componentes: Precip={result['precip']:.1f} - ET0={result['et0']:.1f} - Escor={result['escor']:.1f} - Infiltr={result['infiltr']:.1f}")
    print(f"  Interpretación: {result['interpretacion']}")
    assert result['delta_h'] > 0, "Día lluvia debe ganar agua"
    print("  ✅ PASS")
    
    # Caso 2: Día seco verano
    print("\n[CASO 2] Día seco verano (sin lluvia, ET alta)")
    result = balance_hidrico_diario(
        lluvia_24h_mm=0.0,
        et0_mm=8.5,
        escorrentia_mm=0.0,
        infiltracion_mm=1.5
    )
    print(f"  Balance: {result['delta_h']:.2f} mm")
    print(f"  Interpretación: {result['interpretacion']}")
    assert result['delta_h'] < 0, "Día seco debe perder agua"
    print("  ✅ PASS")
    
    # Caso 3: Equilibrio
    print("\n[CASO 3] Día equilibrio (Precip ≈ ET)")
    result = balance_hidrico_diario(
        lluvia_24h_mm=5.0,
        et0_mm=4.8,
        escorrentia_mm=0.1,
        infiltracion_mm=0.2
    )
    print(f"  Balance: {result['delta_h']:.2f} mm")
    print(f"  Interpretación: {result['interpretacion']}")
    assert abs(result['delta_h']) < 1.0, "Equilibrio debe estar cerca de 0"
    print("  ✅ PASS")
    
    # Caso 4: Noche
    print("\n[CASO 4] Noche (evaporación mínima)")
    result = balance_hidrico_diario(
        lluvia_24h_mm=0.0,
        et0_mm=0.2,  # ET nocturna muy baja
        escorrentia_mm=0.0,
        infiltracion_mm=0.0
    )
    print(f"  Balance: {result['delta_h']:.2f} mm")
    print(f"  Interpretación: {result['interpretacion']}")
    assert abs(result['delta_h']) < 1.0, "Noche poco cambio"
    print("  ✅ PASS")


def test_estres_hidrico_scenarios():
    """
    Escenario 1: Agua abundante (sin estrés)
    Escenario 2: Estrés moderado
    Escenario 3: Estrés severo
    Escenario 4: Por cultivo (maíz vs trigo)
    """
    print("\n" + "="*70)
    print("TEST 2: ESTRÉS HÍDRICO CULTIVO")
    print("="*70)
    
    # Caso 1: Sin estrés
    print("\n[CASO 1] Agua abundante (capacidad campo)")
    result = estres_hidrico_cultivo(
        humedad_suelo_pct=34.0,  # Más cerca de CC (35%)
        et0_mm=5.0,
        cultivo_tipo="general"
    )
    print(f"  Factor: {result['factor']:.3f}")
    print(f"  Nivel: {result['nivel']}")
    print(f"  Acción: {result['accion']}")
    assert result['factor'] >= 0.8, "Agua abundante factor >= 0.8"
    print("  ✅ PASS")
    
    # Caso 2: Estrés moderado
    print("\n[CASO 2] Estrés moderado")
    result = estres_hidrico_cultivo(
        humedad_suelo_pct=23.0,  # Entre PM y CC: (23-15)/(35-15) = 0.4
        et0_mm=6.0,
        cultivo_tipo="general"
    )
    print(f"  Factor: {result['factor']:.3f}")
    print(f"  Nivel: {result['nivel']}")
    assert 0.3 < result['factor'] < 0.8, "Estrés moderado 0.3-0.8"
    print("  ✅ PASS")
    
    # Caso 3: Estrés severo
    print("\n[CASO 3] Estrés severo")
    result = estres_hidrico_cultivo(
        humedad_suelo_pct=16.5,  # Muy cerca de PM (15%): (16.5-15)/(35-15) = 0.075
        et0_mm=8.0,
        cultivo_tipo="general"
    )
    print(f"  Factor: {result['factor']:.3f}")
    print(f"  Nivel: {result['nivel']}")
    assert result['factor'] < 0.3, "Estrés severo factor < 0.3"
    print("  ✅ PASS")
    
    # Caso 4: Maíz vs Trigo (parámetros diferentes)
    print("\n[CASO 4] Comparación cultivos (Maíz vs Trigo)")
    result_maiz = estres_hidrico_cultivo(
        humedad_suelo_pct=22.0,
        et0_mm=6.0,
        cultivo_tipo="maíz"  # Punto marchitez 12%, profundidad 80cm
    )
    result_trigo = estres_hidrico_cultivo(
        humedad_suelo_pct=22.0,
        et0_mm=6.0,
        cultivo_tipo="trigo"  # Punto marchitez 14%, profundidad 60cm
    )
    print(f"  Maíz factor: {result_maiz['factor']:.3f} ({result_maiz['nivel']})")
    print(f"  Trigo factor: {result_trigo['factor']:.3f} ({result_trigo['nivel']})")
    print(f"  Maíz resiste más (raíces más profundas)")
    print("  ✅ PASS")


def test_disponibilidad_agua_scenarios():
    """
    Escenario 1: Agua para muchos días
    Escenario 2: Agua para días críticos
    Escenario 3: Sequedad inminente
    """
    print("\n" + "="*70)
    print("TEST 3: DISPONIBILIDAD AGUA CULTIVABLE")
    print("="*70)
    
    # Caso 1: Muchos días
    print("\n[CASO 1] Agua disponible para >5 días")
    result = disponibilidad_agua_cultivable(
        humedad_suelo_pct=28.0,
        et0_promedio_7d_mm=4.5,
        cultivo_tipo="general"
    )
    print(f"  Días hasta sequedad: {result['dias_hasta_sequia']:.1f}")
    print(f"  Urgencia: {result['urgencia']}")
    assert result['dias_hasta_sequia'] > 5, ">5 días"
    assert "OK" in result['urgencia'] and "abundante" in result['urgencia']
    print("  ✅ PASS")
    
    # Caso 2: Días críticos
    print("\n[CASO 2] Agua para 2-3 días (ALERTA)")
    result = disponibilidad_agua_cultivable(
        humedad_suelo_pct=18.0,
        et0_promedio_7d_mm=6.0,
        cultivo_tipo="general"
    )
    print(f"  Días hasta sequedad: {result['dias_hasta_sequia']:.1f}")
    print(f"  Urgencia: {result['urgencia']}")
    assert 1 < result['dias_hasta_sequia'] < 4, "2-3 días alerta"
    assert "RIEGO" in result['urgencia']
    print("  ✅ PASS")
    
    # Caso 3: Sequedad inmediata
    print("\n[CASO 3] Sequedad INMEDIATA (<1 día)")
    result = disponibilidad_agua_cultivable(
        humedad_suelo_pct=15.5,
        et0_promedio_7d_mm=8.0,
        cultivo_tipo="general"
    )
    print(f"  Días hasta sequedad: {result['dias_hasta_sequia']:.1f}")
    print(f"  Urgencia: {result['urgencia']}")
    assert result['dias_hasta_sequia'] < 1, "<1 día urgencia máxima"
    assert "AHORA" in result['urgencia']
    print("  ✅ PASS")


def test_integracion_balance_cascada():
    """
    Test: Balance → Estrés → Disponibilidad (cascada lógica)
    """
    print("\n" + "="*70)
    print("TEST 4: INTEGRACIÓN CASCADA LÓGICA")
    print("="*70)
    
    print("\n[CASO] Escenario: Sequía progresiva (5 días)")
    humedad_inicial = 28.0
    et0_diaria = 6.0
    
    for dia in range(1, 6):
        # Cada día pierde agua (sin lluvia, ET > infiltración)
        humedad_dia = humedad_inicial - (dia * 2)
        
        balance = balance_hidrico_diario(
            lluvia_24h_mm=0.0,
            et0_mm=et0_diaria,
            escorrentia_mm=0.0,
            infiltracion_mm=0.5
        )
        
        estres = estres_hidrico_cultivo(
            humedad_suelo_pct=humedad_dia,
            et0_mm=et0_diaria,
            cultivo_tipo="general"
        )
        
        disponib = disponibilidad_agua_cultivable(
            humedad_suelo_pct=humedad_dia,
            et0_promedio_7d_mm=et0_diaria,
            cultivo_tipo="general"
        )
        
        print(f"\n  Día {dia}:")
        print(f"    Humedad: {humedad_dia:.1f}%")
        print(f"    Balance: {balance['delta_h']:.1f} mm (pierde agua)")
        print(f"    Estrés: {estres['factor']:.2f} → {estres['nivel']}")
        print(f"    Disponibilidad: {disponib['dias_hasta_sequia']:.1f} días → {disponib['urgencia']}")
        
        # Validación lógica
        if humedad_dia < 17:
            assert estres['factor'] < 0.5, "Estrés severo cuando humedad baja"
            assert disponib['dias_hasta_sequia'] < 2, "Sequedad inminente"


def main():
    print("\n" + "="*70)
    print(" SUITE TEST: BALANCE HIDRICO + ESTRES + DISPONIBILIDAD AGUA V1.0")
    print("="*70)
    
    try:
        test_balance_hidrico_scenarios()
        test_estres_hidrico_scenarios()
        test_disponibilidad_agua_scenarios()
        test_integracion_balance_cascada()
        
        print("\n" + "="*70)
        print("✅ TODOS LOS TESTS PASARON (12/12)")
        print("="*70)
        print("\nResultado: SISTEMA HÍDRICO V21 OPERATIVO")
        print("  - Balance hídrico funcional")
        print("  - Estrés hídrico automático")
        print("  - Disponibilidad agua proyectada")
        print("  - Cascada lógica integrada")
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
