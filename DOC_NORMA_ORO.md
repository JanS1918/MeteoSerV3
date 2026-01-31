DOC - NORMA DE ORO (METEOSER V3)

Resumen
------
Esta norma establece la regla de oro para la selección automática del "mejor" índice en todo MeteoSer: siempre usar la fórmula de mayor fidelidad científica aplicable al contexto de medida y al objetivo del índice.

Principios generales
-------------------
- Prioridad por calidad científica: cuando existan múltiples índices que midan un mismo fenómeno, elegir siempre el de mayor validez física (modelo de primer principio > modelo empírico mejorado > proxy derivado).
- Uso de datos reales: preferir entradas con `EstadoFisico.REAL` (barómetro real, humedad real). Los fallbacks usan ISA y deben registrarse.
- Robustez: toda selección se debe realizar mediante helpers centralizados (`core.indices.index_selection`) para evitar dispersión de lógica.
- Trazabilidad: cada decisión debe ser rastreable en los `indices` (campo `estimado` / `explicacion`).
- Compatibilidad: endpoints y alias conservan claves legadas, pero mapearán a la mejor opción disponible (no a valores arbitrarios).

Orden de prioridad (por caso de uso)
-----------------------------------
1) Bochorno / Estrés por calor ("bochorno_real")
   - Prioridad: `wbgt_liljegren` (modelo científico) -> `wbgt` (aproximado) -> `sensacion_calor` (fórmulas consolidadas) -> `utci` -> temperatura.
   - Razonamiento: WBGT Liljegren modela radiación y humedad con mayor fidelidad para estrés por calor.

2) Aire pegajoso / Sensación de bochorno ("aire_pegajoso")
   - Prioridad: `vpd` (déficit de presión de vapor, métrica física) -> `sensacion_calor` -> proxy calculado si faltan anteriores.
   - Razonamiento: VPD es físicamente superior a Humidex para evaluar potencial de evaporación y sensación.

3) Frío incómodo ("frio_incomodo")
   - Prioridad: `utci` (cobertura térmica integral) -> `sensacion_frio` -> temperatura.
   - Razonamiento: UTCI incorpora radiación, viento y humedad en una medida de estrés térmico más completa.

4) Saturación / Psicrometría
   - Prioridad de cascada: `virial_greenspan` -> `hyland_wexler` -> (ISA fallback).
   - Razonamiento: virial+Greenspan corrige el comportamiento a presiones y composiciones reales; Hyland-Wexler es el respaldo ASHRAE.

5) Endpoints y compatibilidad
   - Las claves legadas (`heat_index`, `humidex`, `wind_chill`) se mantienen en la API por compatibilidad, pero su contenido será un mapeo al "mejor índice disponible" según las reglas anteriores.

Implementación
---------------
- Helpers centrales: `core/indices/index_selection.py` contiene `mejor_valor_indices` y `mejor_entrada_indices`.
- Todos los módulos deben usar estos helpers; no replicar lógica en archivos aislados.
- `core/context/fallback_universal.py` contiene la cascada de degradación (tetens eliminado).

Trazado y auditabilidad
-----------------------
- Añadir en el `indices[...]` campos `estimado` (bool) y `explicacion` (texto) siempre que se aplique fallback o se elija un proxy.
- Los backups deben incluir las cabeceras científicas ("FÍSICA SELLADA") en `core/indices/environmental_indices.py`.

Sello de Diamante
-----------------
- El archivo `core/indices/environmental_indices.py` contiene la cabecera de "FÍSICA SELLADA" que certifica los estándares. El backup único creado ahora contiene esa cabecera.

Mantenimiento
-------------
- Para añadir excepciones o cambiar prioridades, editar `DOC_NORMA_ORO.md` y `core/indices/index_selection.py`.
- Revisiones mayores deben incluir tests que verifiquen que la prioridad aplicada en ejemplos conocidos produce el índice esperado.

Fecha: 2026-01-31
Autor: Equipo MeteoSer (Automatización)
