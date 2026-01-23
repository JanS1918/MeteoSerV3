import traceback
import sys
from pathlib import Path

# Ensure repo root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.system.singleton import get_manager, get_system

try:
    m = get_manager()
    s = get_system()
    print('System initialized: OK' if m else 'Manager not available')
    rec = getattr(s, 'recommendation_engine', None) if s else None
    print('recommendation_engine:', type(rec).__name__ if rec else None)
    try:
        estado = s.obtener_estado_completo()
        if isinstance(estado, dict):
            print('Keys in estado:', list(estado.keys()))
            print('\nrecomendacion value:\n')
            print(estado.get('recomendacion'))
        else:
            print('estado (non-dict):', estado)
    except Exception as e:
        print('Error obtaining estado_completo:')
        traceback.print_exc()
    # Print indices produced by EnvironmentalIndices
    try:
        inds = s.indices.obtener_todos()
        print('\nIndices computed (sample):')
        for k in sorted(list(inds.keys()))[:40]:
            print(k, ':', inds.get(k))
    except Exception:
        print('Error obtaining indices:')
        traceback.print_exc()
except Exception:
    print('Error initializing system:')
    traceback.print_exc()
