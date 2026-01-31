#!/usr/bin/env python3
"""
Forzar valores redondos directamente en el sistema y verificar la Ley del Entero.
"""

import json
import sys
sys.path.insert(0, 'c:/Users/kioko/Desktop/MeteoSerV3')

from core.system.system_manager import SystemManager

# Inicializar el sistema
manager = SystemManager()
system = manager.iniciar()

# Forzar valores redondos manualmente
print("🔧 INYECTANDO VALORES REDONDOS DIRECTAMENTE EN EL SISTEMA...")
print("   - viento: 0.0 → esperamos 0 (INT)")
print("   - humedad: 100.0 → esperamos 100 (INT)")
print()

# Forzar en system.sensores
system.sensores['viento'] = {'valor': 0.0, 'unidad': 'km/h', 'timestamp': '2026-01-31T02:00:00'}
system.sensores['humedad'] = {'valor': 100.0, 'unidad': '%', 'timestamp': '2026-01-31T02:00:00'}

# Guardar en el snapshot para que persista
import pathlib
snapshot_path = pathlib.Path('data/last_sensores.json')
snapshot_path.parent.mkdir(parents=True, exist_ok=True)
snapshot_path.write_text(json.dumps({
    'sensores': system.sensores,
    'timestamps': getattr(system, 'sensores_timestamp', {})
}, ensure_ascii=False, indent=2), encoding='utf-8')

print("✅ Valores inyectados y persistidos en data/last_sensores.json")
print(f"   - viento: {system.sensores['viento']}")
print(f"   - humedad: {system.sensores['humedad']}")
print()
print("💡 Ahora arranca el servidor y haz un curl a /api/panel/central para verificar el INT puro.")
