#!/usr/bin/env python3
"""Test que helpers fueron agregados a environmental_indices.py"""

import sys
sys.path.insert(0, 'c:\\Users\\kioko\\Desktop\\MeteoSerV3')

try:
    from core.indices.environmental_indices import get_float, get_int, clamp_percent, clamp_unit
    
    print("✅ environmental_indices.py - Helpers importados exitosamente")
    
    # Tests rápidos
    assert get_float({"val": 50.5}, "val") == 50.5
    assert clamp_percent(250) == 100.0
    assert clamp_unit(1.5) == 1.0
    
    print("✅ Todos los helpers funcionan en environmental_indices")
    print("\n✅ REFACTORIZACIÓN FASE 2 COMPLETADA")
    print("   - Helpers agregados a environmental_indices.py")
    print("   - Compilación exitosa")
    
except ImportError as e:
    print(f"❌ Error: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
