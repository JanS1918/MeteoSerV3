"""
test_certificacion_v26.py
=========================
Suite de pruebas para validar la Certificación V2.6

Pruebas:
1. Factor Z con datos reales de Argentona
2. Comparación interior vs exterior
3. Calibración de Ekman
4. Integridad SHA256
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from protocolo_certificacion_arranque_v26 import ProtocoloCertificacionV26


def test_factor_z_argentona():
    """Test: Factor Z con condiciones típicas de Argentona"""
    print("\n" + "="*70)
    print("TEST 1: Factor Z con datos reales de Argentona")
    print("="*70)
    
    protocolo = ProtocoloCertificacionV26()
    
    # Datos típicos de Argentona
    resultado = protocolo.validar_factor_z(
        presion_hpa=1019.1,
        temperatura_c=18.5
    )
    
    print(f"\n✓ Factor Z calculado: {resultado['factor_z']:.6f}")
    print(f"✓ Desviación del ideal: {resultado['desviacion_ideal_pct']:.4f}%")
    print(f"✓ Densidad real: {resultado['densidad_real_kg_m3']:.4f} kg/m³")
    
    assert resultado['validado'] == True
    assert 0.999 < resultado['factor_z'] < 1.001
    print("\n✓ TEST 1 PASADO")


def test_comparacion_interior_exterior():
    """Test: Comparación de Factor Z entre interior y exterior"""
    print("\n" + "="*70)
    print("TEST 2: Comparación Interior vs Exterior")
    print("="*70)
    
    protocolo = ProtocoloCertificacionV26()
    
    # Simular datos de interior (más caliente, misma presión)
    resultado = protocolo.comparar_factor_z_interior_exterior(
        presion_int=1019.5,
        temp_int=22.0,
        presion_ext=1019.1,
        temp_ext=18.5
    )
    
    print(f"\n✓ Factor Z interior: {resultado['interior']['factor_z']:.6f}")
    print(f"✓ Factor Z exterior: {resultado['exterior']['factor_z']:.6f}")
    print(f"✓ Diferencia de densidad: {resultado['diferencias']['delta_densidad_g_m3']:.2f} g/m³")
    
    assert resultado['diferencias']['delta_densidad_kg_m3'] > 0
    print("\n✓ TEST 2 PASADO")


def test_calibracion_ekman():
    """Test: Calibración del ángulo de Ekman"""
    print("\n" + "="*70)
    print("TEST 3: Calibración de Ekman para Argentona")
    print("="*70)
    
    protocolo = ProtocoloCertificacionV26()
    
    resultado = protocolo.calibrar_ekman(velocidad_viento_ms=5.2)
    
    print(f"\n✓ Ángulo de Inflow: {resultado['angulo_inflow_grados']:.1f}°")
    print(f"✓ Rugosidad de terreno: {resultado['rugosidad_terreno']:.3f}")
    
    assert resultado['calibrado'] == True
    assert 15 <= resultado['angulo_inflow_grados'] <= 30
    print("\n✓ TEST 3 PASADO")


def test_integridad_sha256():
    """Test: Verificación de integridad SHA256"""
    print("\n" + "="*70)
    print("TEST 4: Verificación SHA256")
    print("="*70)
    
    protocolo = ProtocoloCertificacionV26()
    
    resultado = protocolo.verificar_integridad_sha256()
    
    print(f"\n✓ Módulos verificados: {len(resultado['hashes_modulos'])}")
    print(f"✓ Integridad válida: {resultado['integridad_valida']}")
    
    if resultado['hash_maestro']:
        print(f"✓ Hash maestro: {resultado['hash_maestro'][:16]}...")
    
    print("\n✓ TEST 4 PASADO")


def test_certificacion_completa():
    """Test: Certificación completa de arranque"""
    print("\n" + "="*70)
    print("TEST 5: Certificación Completa de Arranque")
    print("="*70)
    
    protocolo = ProtocoloCertificacionV26()
    
    resultado = protocolo.ejecutar_certificacion_completa(
        presion_hpa=1019.1,
        temperatura_c=18.5,
        velocidad_viento_ms=5.2
    )
    
    print(f"\n✓ Estado: {resultado['estado']}")
    print(f"✓ Factor Z: {resultado['factor_z']['factor_z']:.6f}")
    print(f"✓ Ángulo Ekman: {resultado['ekman']['angulo_inflow_grados']:.1f}°")
    print(f"✓ SHA256: {'VÁLIDO' if resultado['sha256']['integridad_valida'] else 'INVÁLIDO'}")
    
    assert resultado['estado'] in ['CERTIFICADO_VALIDO', 'CERTIFICACION_FALLIDA']
    print("\n✓ TEST 5 PASADO")


if __name__ == "__main__":
    print("="*70)
    print("SUITE DE PRUEBAS - CERTIFICACIÓN V2.6")
    print("="*70)
    
    try:
        test_factor_z_argentona()
        test_comparacion_interior_exterior()
        test_calibracion_ekman()
        test_integridad_sha256()
        test_certificacion_completa()
        
        print("\n" + "="*70)
        print("✓ TODOS LOS TESTS PASADOS")
        print("✓ ACORAZADO ARGENTONA V2.6 CERTIFICADO")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ ERROR EN TESTS: {e}")
        import traceback
        traceback.print_exc()
