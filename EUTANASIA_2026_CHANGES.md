EUTANASIA 2026 - Cambios aplicados automáticamente

Resumen rápido:
- Eliminado uso de Tetens (`tetens_simple`) en cascada de saturación.
- Reemplazadas llamadas a funciones obsoletas (`indice_heat_index_c`, `indice_humidex`, `indice_wind_chill_c`) por accesos seguros a índices unificados (`sensacion_calor`, `sensacion_frio`) o proxies.
- Actualizados aliases en `core/sensors/sensor_aliases.py` para mapear `heat_index`/`wind_chill` a `sensacion_calor`/`sensacion_frio`.
- Eliminada entrada `humidex` del `core/indices/index_catalog.py` (nota de eliminación añadida).
- Endpoints en `main_asgi.py` devuelven `sensacion_calor` para la clave `humidex` por compatibilidad.
- Eliminado bloque residual mal indentado en `core/indices/environmental_indices.py` que causaba errores de importación.

Archivos modificados:
- core/sensors/sensor_aliases.py
- core/context/fallback_universal.py
- core/indices/environmental_indices.py
- core/indices/index_catalog.py
- main_asgi.py

Notas:
- Se ejecutaron comprobaciones de sintaxis y un chequeo de humo local; los tests completos fallan en la recopilación debido a archivos duplicados en `backups/`.
- Recomendado: crear commit y limpiar `.pyc` / `__pycache__` y backups antes de ejecutar la batería completa de tests.
