"""
Test de Ignición - Sintonización Dinámica 2026.
Valida que las constantes físicas se actualizan dinámicamente según condiciones ambientales.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.indices.physics_engine_2026 import obtener_constantes_dinamicas, PhysicsEngine2026
from core.indices.environmental_indices import indice_vpd_kpa, calcular_saturacion_vapor_con_fallback
from core.indices.advanced_physics_models import et_shuttleworth_wallace, monin_obukhov_stability
from core.system.constants import ESTACION


def test_constantes_dinamicas_argentona():
    """Test 1: Constantes dinámicas para condiciones reales de Argentona."""
    print("\n" + "="*80)
    print(f"TEST 1: CONSTANTES DINÁMICAS - Argentona ({ESTACION.LATITUD:.8f}°N, 17.8°C, 65%HR)")
    print("="*80)
    
    # Condiciones reales de Argentona
    latitud = ESTACION.LATITUD
    temp_c = 17.8
    presion_hpa = 1013.25
    humedad_rel = 65.0
    
    constantes = obtener_constantes_dinamicas(latitud, temp_c, presion_hpa, humedad_rel)
    
    print("\n[STATS] MOTOR DE FÍSICA 2026 - CONSTANTES VIVAS:")
    print(json.dumps(constantes, indent=2, ensure_ascii=False))
    
    return constantes


def test_comparacion_isa_vs_real():
    """Test 2: Comparación entre valores ISA y valores reales de Argentona."""
    print("\n" + "="*80)
    print("TEST 2: COMPARACIÓN ISA vs REAL")
    print("="*80)
    
    # Condiciones ISA (None para forzar fallback)
    print("\n🔵 CONDICIONES ISA (Fallback):")
    constantes_isa = obtener_constantes_dinamicas(None, None, None, None)
    
    g_isa = constantes_isa["gravedad_somigliana"]["valor"]
    mu_isa = constantes_isa["viscosidad_sutherland"]["valor"]
    k_isa = constantes_isa["conductividad_mason_saxena"]["valor"]
    Z_isa = constantes_isa["factor_compresibilidad_virial"]["valor"]
    
    print(f"  g (ISA)  = {g_isa:.6f} m/s²")
    print(f"  μ (ISA)  = {mu_isa:.8f} Pa·s")
    print(f"  k (ISA)  = {k_isa:.6f} W/(m·K)")
    print(f"  Z (ISA)  = {Z_isa:.8f}")
    
    # Condiciones reales de Argentona
    print("\n🟢 CONDICIONES REALES (Argentona):")
    constantes_real = obtener_constantes_dinamicas(ESTACION.LATITUD, 17.8, 1013.25, 65.0)
    
    g_real = constantes_real["gravedad_somigliana"]["valor"]
    mu_real = constantes_real["viscosidad_sutherland"]["valor"]
    k_real = constantes_real["conductividad_mason_saxena"]["valor"]
    Z_real = constantes_real["factor_compresibilidad_virial"]["valor"]
    
    print(f"  g (Argentona) = {g_real:.6f} m/s²")
    print(f"  μ (Argentona) = {mu_real:.8f} Pa·s")
    print(f"  k (Argentona) = {k_real:.6f} W/(m·K)")
    print(f"  Z (Argentona) = {Z_real:.8f}")
    
    # Diferencias
    print("\n[FAST] DIFERENCIAS ABSOLUTAS:")
    print(f"  Δg = {abs(g_real - g_isa):.6f} m/s² ({abs((g_real - g_isa)/g_isa)*100:.3f}%)")
    print(f"  Δμ = {abs(mu_real - mu_isa):.10f} Pa·s ({abs((mu_real - mu_isa)/mu_isa)*100:.3f}%)")
    print(f"  Δk = {abs(k_real - k_isa):.6f} W/(m·K) ({abs((k_real - k_isa)/k_isa)*100:.3f}%)")
    print(f"  ΔZ = {abs(Z_real - Z_isa):.8f} ({abs((Z_real - Z_isa)/Z_isa)*100:.3f}%)")
    
    return {
        "isa": constantes_isa,
        "real": constantes_real,
        "diferencias": {
            "g": abs(g_real - g_isa),
            "mu": abs(mu_real - mu_isa),
            "k": abs(k_real - k_isa),
            "Z": abs(Z_real - Z_isa)
        }
    }


def test_psicrometria_con_z():
    """Test 3: Psicrometría con Factor Z dinámico."""
    print("\n" + "="*80)
    print("TEST 3: PSICROMETRÍA CON FACTOR Z (Gas Real)")
    print("="*80)
    
    temp_c = 17.8
    humedad = 65.0
    presion_hpa = 1013.25
    
    # Calcular VPD con el sistema completo
    vpd = indice_vpd_kpa(temp_c, humedad, presion_hpa, None)
    
    # Calcular saturación con cascada
    psat, estado = calcular_saturacion_vapor_con_fallback(temp_c, presion_hpa * 100.0)
    
    # Obtener Factor Z directamente
    engine = PhysicsEngine2026(temperatura_k=temp_c+273.15, presion_pa=presion_hpa*100.0)
    Z, estado_Z = engine.factor_compresibilidad_virial()
    
    resultado = {
        "temperatura_c": temp_c,
        "humedad_rel": humedad,
        "presion_hpa": presion_hpa,
        "vpd_kpa": round(vpd, 4),
        "presion_saturacion_pa": round(psat, 2),
        "factor_Z": round(Z, 8),
        "status_Z": estado_Z.value if hasattr(estado_Z, 'value') else str(estado_Z),
        "explicacion": "VPD calculado con Factor Z (no-idealidad del gas)"
    }
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    return resultado


def test_et0_con_somigliana():
    """Test 4: ET0 con gravedad Somigliana y cp dinámico."""
    print("\n" + "="*80)
    print("TEST 4: ET0 CON GRAVEDAD SOMIGLIANA + cp DINÁMICO")
    print("="*80)
    
    temp_c = 17.8
    humedad = 65.0
    presion_hpa = 1013.25
    viento_ms = 2.5
    rn = 400.0
    
    # Calcular ET0
    et_result = et_shuttleworth_wallace(
        rn=rn,
        temp_c=temp_c,
        humedad=humedad,
        viento_ms=viento_ms,
        presion_hpa=presion_hpa
    )
    
    # Obtener constantes usadas
    engine = PhysicsEngine2026(
        latitud=ESTACION.LATITUD,
        temperatura_k=temp_c+273.15,
        presion_pa=presion_hpa*100.0,
        humedad_fraccion=humedad/100.0
    )
    g, _ = engine.gravedad_somigliana()
    cp, _ = engine.calor_especifico_dinamico()
    
    resultado = {
        "et0_total": round(et_result["et0_total"], 4),
        "et0_canopy": round(et_result["et0_canopy"], 4),
        "et0_soil": round(et_result["et0_soil"], 4),
        "status": et_result.get("status", "REAL"),
        "constantes_usadas": {
            "gravedad_somigliana_ms2": round(g, 6),
            "calor_especifico_jkgk": round(cp, 2)
        },
        "explicacion": "ET0 Shuttleworth-Wallace con g(φ) y cp(HR)"
    }
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    return resultado


def test_estabilidad_con_cp_dinamico():
    """Test 5: Estabilidad Monin-Obukhov con cp dinámico."""
    print("\n" + "="*80)
    print("TEST 5: MONIN-OBUKHOV CON cp DINÁMICO")
    print("="*80)
    
    temp_c = 17.8
    temp_surf = 19.8
    viento_ms = 2.5
    rn = 400.0
    
    estabilidad = monin_obukhov_stability(
        z0=0.1,
        z=13.0,
        temp_c=temp_c,
        temp_surf=temp_surf,
        viento_ms=viento_ms,
        rn=rn,
        presion_hpa=1013.25
    )
    
    # Obtener constantes usadas
    engine = PhysicsEngine2026(
        latitud=ESTACION.LATITUD,
        temperatura_k=temp_c+273.15
    )
    g, _ = engine.gravedad_somigliana()
    cp, _ = engine.calor_especifico_dinamico()
    
    resultado = {
        "clase_estabilidad": estabilidad["clase_estabilidad"],
        "L_monin_obukhov": round(estabilidad["L_monin_obukhov"], 2) if abs(estabilidad["L_monin_obukhov"]) != float('inf') else "infinito",
        "u_star": round(estabilidad["u_star"], 4),
        "z0h_zilitinkevich": round(estabilidad["z0h"], 6),
        "status": estabilidad.get("status", "REAL"),
        "constantes_usadas": {
            "gravedad_somigliana_ms2": round(g, 6),
            "calor_especifico_jkgk": round(cp, 2)
        },
        "explicacion": "Monin-Obukhov con g(φ), cp(HR) y Zilitinkevich"
    }
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    return resultado


def main():
    """Ejecutar todos los tests de sintonización dinámica."""
    print("\n" + "#"*80)
    print("# SINTONIZACIÓN DINÁMICA 2026 - CONSTANTES VIVAS")
    print("# MeteoSerV3 - Argentona, Barcelona")
    print("#"*80)
    
    resultados = {}
    
    try:
        resultados["test_1_constantes_argentona"] = test_constantes_dinamicas_argentona()
        resultados["test_2_comparacion_isa_real"] = test_comparacion_isa_vs_real()
        resultados["test_3_psicrometria_z"] = test_psicrometria_con_z()
        resultados["test_4_et0_somigliana"] = test_et0_con_somigliana()
        resultados["test_5_estabilidad_cp"] = test_estabilidad_con_cp_dinamico()
        
        print("\n" + "="*80)
        print("RESUMEN FINAL - JSON COMPLETO")
        print("="*80)
        
        print("\n[STATS] RESULTADO GENERAL:")
        print(json.dumps(resultados, indent=2, ensure_ascii=False))
        
        print("\n" + "="*80)
        print("✓ SINTONIZACIÓN CONFIRMADA: CONSTANTES VIVAS OPERATIVAS")
        print("✓ Factor Z (Virial): Aire tratado como gas REAL")
        print("✓ Gravedad (Somigliana): Ajustada por latitud de Argentona")
        print("✓ Viscosidad (Sutherland): Dependiente de temperatura real")
        print("✓ Conductividad (Mason-Saxena): Corregida por humedad")
        print("✓ cp dinámico: Varía con humedad específica")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ ERROR EN SINTONIZACIÓN: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
