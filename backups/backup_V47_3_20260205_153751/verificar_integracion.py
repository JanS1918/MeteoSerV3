#!/usr/bin/env python3
"""Verificar que el integrador se puede importar correctamente"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.integration.integrador_always_on import ejecutar_integrador_automatico
    print("✅ Integrador importado correctamente")
    print(f"   Función: {ejecutar_integrador_automatico.__name__}")
    print(f"   Es async: {asyncio.iscoroutinefunction(ejecutar_integrador_automatico)}")
except ImportError as e:
    print(f"❌ Error al importar integrador: {e}")
    sys.exit(1)

try:
    from core.indices.deardorff_v46_5_final_sentencia import calcular_temperatura_minima_v46_5_final
    print("✅ Deardorff V46.5 FINAL importado correctamente")
except ImportError as e:
    print(f"❌ Error al importar Deardorff V46.5 FINAL: {e}")
    sys.exit(1)


print("\n✅ Todas las dependencias están disponibles")
print("   Sistema listo para integración")
