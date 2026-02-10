"""
VALIDACION RAPIDA: Indices Integrales MeteoSerV3 v2.0

Este script verifica que los indices integrales continuen funcionando
correctamente tras cambios en el codigo.

Uso: python quick_validation.py
"""

import sys
import logging

# Suppress debug logging for clean output
logging.getLogger().setLevel(logging.CRITICAL)

try:
    from core.indices.lluvia.lluvia_indices import indice_lluvia_sintetico
    from core.indices.cetreria.cetreria_indices_v2 import indice_cetreria_sintetico
    from core.indices.deporte.deporte_indices import indice_deporte_sintetico
    from core.indices.confort.confort_indices import indice_confort_sintetico
except ImportError as e:
    print(f"ERROR: No se pueden importar los modulos: {e}")
    sys.exit(1)

def validate():
    """Run validation checks"""
    checks = []
    
    # Check 1: LLUVIA - rainfall decreases index
    print("[1/4] Validating LLUVIA (rain decreases index)...", end=" ")
    idx_dry = indice_lluvia_sintetico(40, 80, 85, 25, lluvia_1h=0.0)
    idx_wet = indice_lluvia_sintetico(40, 80, 85, 25, lluvia_1h=5.0)
    if idx_wet < idx_dry:
        print("PASS")
        checks.append(True)
    else:
        print(f"FAIL (dry={idx_dry:.1f}, wet={idx_wet:.1f})")
        checks.append(False)
    
    # Check 2: CETRERIA - rainfall dramatically decreases index
    print("[2/4] Validating CETRERIA (rain hurts flying)...", end=" ")
    idx_dry = indice_cetreria_sintetico(40, 90, 75, 80, 70, lluvia_1h=0.0)
    idx_wet = indice_cetreria_sintetico(40, 90, 75, 80, 70, lluvia_1h=2.5)
    if idx_wet < idx_dry and (idx_dry - idx_wet) > 30:  # >30 point drop expected
        print("PASS")
        checks.append(True)
    else:
        print(f"FAIL (dry={idx_dry:.1f}, wet={idx_wet:.1f}, drop={(idx_dry-idx_wet):.1f})")
        checks.append(False)
    
    # Check 3: DEPORTE - rainfall significantly decreases index
    print("[3/4] Validating DEPORTE (rain harms sports)...", end=" ")
    idx_dry = indice_deporte_sintetico(85, 90, 75, 80, lluvia_1h=0.0)
    idx_wet = indice_deporte_sintetico(85, 90, 75, 80, lluvia_1h=3.0)
    if idx_wet < idx_dry and (idx_dry - idx_wet) > 30:  # >30 point drop expected
        print("PASS")
        checks.append(True)
    else:
        print(f"FAIL (dry={idx_dry:.1f}, wet={idx_wet:.1f}, drop={(idx_dry-idx_wet):.1f})")
        checks.append(False)
    
    # Check 4: CONFORT - rainfall slightly decreases index
    print("[4/4] Validating CONFORT (rain mildly affects comfort)...", end=" ")
    idx_dry = indice_confort_sintetico(85, 80, 60, 80, lluvia_1h=0.0)
    idx_wet = indice_confort_sintetico(85, 80, 60, 80, lluvia_1h=5.0)
    if idx_wet < idx_dry and (idx_dry - idx_wet) < 20:  # Small drop expected (<20)
        print("PASS")
        checks.append(True)
    else:
        print(f"FAIL (dry={idx_dry:.1f}, wet={idx_wet:.1f}, drop={(idx_dry-idx_wet):.1f})")
        checks.append(False)
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    print(f"\nResult: {passed}/{total} checks passed")
    
    if passed == total:
        print("SUCCESS: All integral indices are working correctly!")
        return 0
    else:
        print(f"FAILURE: {total - passed} check(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(validate())
