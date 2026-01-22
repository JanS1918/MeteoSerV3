import traceback

LAT = 41.5507
LON = -2.3957

print('Intentando ejecutar get_manager().set_manual_coordinates...')
try:
    from core.system.singleton import get_manager
    mgr = get_manager()
    if hasattr(mgr, 'set_manual_coordinates'):
        res = mgr.set_manual_coordinates(LAT, LON)
        print('set_manual_coordinates result:', res)
    else:
        print('El manager no tiene método set_manual_coordinates')
except Exception:
    traceback.print_exc()

print('\nIntentando verificar endpoint /estado tras ejecución local (si existe servidor)...')
try:
    import requests
    r = requests.get('http://127.0.0.1:8080/estado', timeout=5)
    print('/estado status:', r.status_code)
    try:
        j = r.json()
        print('indices.longitud:', j.get('indices', {}).get('longitud'))
        print('indices.origen_ubicacion:', j.get('indices', {}).get('origen_ubicacion'))
        print('contexto.es_noche:', j.get('contexto', {}).get('es_noche'))
    except Exception:
        print('No JSON en /estado')
except Exception as e:
    print('No se pudo conectar a /estado:', e)
