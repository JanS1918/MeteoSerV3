═════════════════════════════════════════════════════════════════════════════════
CHECKLIST DE VERIFICACION - INTEGRACION V51
═════════════════════════════════════════════════════════════════════════════════

Uso: Ejecute este checklist para verificar que la integración V51 está correcta.

═════════════════════════════════════════════════════════════════════════════════
PASO 1: VERIFICAR ARCHIVOS CORE EXISTEN
═════════════════════════════════════════════════════════════════════════════════

[ ] core/radiation/__init__.py (debe ser vacío)
[ ] core/radiation/clasificador_contexto_radiativo.py (~280 líneas)
[ ] core/radiation/estrategias_aprendizaje.py (~300 líneas)
[ ] core/radiation/publicador_radiacion_robusto.py (~290 líneas)
[ ] core/radiation/controlador_radiacion_robusto.py (~380 líneas)
[ ] core/radiation/wrapper_integracion.py (~230 líneas)

Verificar: $ ls -la core/radiation/
Esperar: 6 archivos .py

═════════════════════════════════════════════════════════════════════════════════
PASO 2: VERIFICAR INTEGRACION EN RADIACION_HIBRIDA.PY
═════════════════════════════════════════════════════════════════════════════════

[ ] Línea 40-50: Import try/except para WrapperRadiacionRobusta
    Buscar: "from core.radiation.wrapper_integracion import WrapperRadiacionRobusta"

[ ] Línea 77-87: Inicialización self._wrapper_radiacion_v51
    Buscar: "self._wrapper_radiacion_v51 = WrapperRadiacionRobusta("

[ ] Línea 100-170: Método procesar_radiacion_con_wrapper_v51()
    Buscar: "def procesar_radiacion_con_wrapper_v51(self,"

[ ] Línea 456-656: Método procesar_radiacion_hibrida() adaptado
    Buscar: "# TRY 1: Usar arquitectura robusta V51"

[ ] Línea 658-750: Función procesar_radiacion_sistema() mejorada
    Buscar: "velocidad_viento = sensores.get("

Verificar: $ grep -n "wrapper_radiacion_v51" core/indices/radiacion_hibrida.py
Esperar: 4+ resultados

═════════════════════════════════════════════════════════════════════════════════
PASO 3: EJECUTAR UNIT TESTS
═════════════════════════════════════════════════════════════════════════════════

Comando: cd core/radiation && python -m pytest test_arquitectura_radiacion_v51.py -v

Esperar:
  test_importaciones PASSED
  test_instanciacion_componentes PASSED
  test_clasificador_funciona PASSED
  test_aprendizaje_correctivo_procesa PASSED
  test_aprendizaje_diagnostico_procesa PASSED
  test_publicador_publica_consume PASSED
  test_validador_cruzado_valida PASSED
  test_controlador_ciclo_completo PASSED
  test_wrapper_activo_deshabilitado PASSED

Resultado esperado: 9 passed in X.XXs

═════════════════════════════════════════════════════════════════════════════════
PASO 4: EJECUTAR INTEGRATION TESTS
═════════════════════════════════════════════════════════════════════════════════

Comando: cd . && python test_integracion_final_v51.py

Esperar línea por línea:
  [ ] Tests PASADOS: 13
  [ ] Tests FALLIDOS: 0
  [ ] Tasa exito: 100.0%
  [ ] [RESULTADO] INTEGRACION V51 EXITOSA
  [ ] [OK] Modulo radiacion_hibrida.py completamente integrado
  [ ] [OK] Wrapper V51 inicializa correctamente
  [ ] [OK] Parametros nuevos (viento, lluvia, visibilidad) soportados
  [ ] [OK] Procesamiento con V51 activo
  [ ] [OK] Fallback automatico a REST2 funciona
  [ ] [OK] Datos publicados en formato correcto

═════════════════════════════════════════════════════════════════════════════════
PASO 5: VERIFICAR RADIACION_HIBRIDA IMPORTA SIN ERRORES
═════════════════════════════════════════════════════════════════════════════════

Comando: python -c "from core.indices.radiacion_hibrida import PiranometroHibrido; print('OK')"

Esperar: OK (sin errores)

Comando: python -c "from core.indices.radiacion_hibrida import procesar_radiacion_sistema; print('OK')"

Esperar: OK (sin errores)

═════════════════════════════════════════════════════════════════════════════════
PASO 6: VERIFICAR WRAPPER V51 SE INICIALIZA
═════════════════════════════════════════════════════════════════════════════════

Comando:
python -c "
from core.indices.radiacion_hibrida import PiranometroHibrido
p = PiranometroHibrido(latitud=41.3, longitud=2.1)
if p._wrapper_radiacion_v51:
    print('V51 ACTIVO')
else:
    print('V51 NO DISPONIBLE - fallback a REST2')
"

Esperar: V51 ACTIVO

═════════════════════════════════════════════════════════════════════════════════
PASO 7: VERIFICAR PROCESAMIENTO V51
═════════════════════════════════════════════════════════════════════════════════

Comando:
python -c "
from core.indices.radiacion_hibrida import PiranometroHibrido
from datetime import datetime
p = PiranometroHibrido(latitud=41.3, longitud=2.1)
r = p.procesar_radiacion_hibrida(
    radiacion_medida=750.0, temp_wh65_c=22.5, temp_wh31_c=21.0,
    presion_hpa=1013.25, humedad_rel=55.0, velocidad_viento_ms=3.5,
    precipitacion_mm=0.0, visibilidad_km=10.0, fecha_hora=datetime.now()
)
print(f'GHI={r[\"ghi_final_w_m2\"]:.1f} V51={r[\"arquitectura_v51\"]}')
"

Esperar: GHI=XXX.X V51=True

═════════════════════════════════════════════════════════════════════════════════
PASO 8: VERIFICAR FALLBACK REST2
═════════════════════════════════════════════════════════════════════════════════

Comando:
python -c "
from core.indices.radiacion_hibrida import PiranometroHibrido
from datetime import datetime
p = PiranometroHibrido(latitud=41.3, longitud=2.1)
p._wrapper_radiacion_v51 = None  # Deshabilitar V51
r = p.procesar_radiacion_hibrida(
    radiacion_medida=750.0, temp_wh65_c=22.5, temp_wh31_c=21.0,
    presion_hpa=1013.25, humedad_rel=55.0, velocidad_viento_ms=3.5,
    precipitacion_mm=0.0, visibilidad_km=10.0, fecha_hora=datetime.now()
)
print(f'GHI={r[\"ghi_final_w_m2\"]:.1f} V51={r[\"arquitectura_v51\"]}')
"

Esperar: GHI=XXX.X V51=False (usa REST2 fallback)

═════════════════════════════════════════════════════════════════════════════════
PASO 9: VALIDAR DATOS PUBLICADOS
═════════════════════════════════════════════════════════════════════════════════

[ ] GHI final está en rango [0, 1500] W/m²
[ ] Confianza está en rango [0, 100]%
[ ] DNI <= GHI (relación física válida)
[ ] DHI estimado es razonable
[ ] Timestamp es actual

═════════════════════════════════════════════════════════════════════════════════
PASO 10: VERIFICAR PARAMETROS NUEVOS SE ACEPTAN
═════════════════════════════════════════════════════════════════════════════════

Comando:
python -c "
from core.indices.radiacion_hibrida import procesar_radiacion_sistema
r = procesar_radiacion_sistema({
    'temperatura': 25.0, 'temperatura_wh31': 23.0, 'humedad': 60.0,
    'presion': 1013.25, 'solarradiation_original': 800.0,
    'windspeed': 3.5, 'precipitacion_hora': 0.0, 'visibilidad': 10.0,
    'latitud_estimada': 41.3, 'longitud_estimada': 2.1
}, None)
print(f'OK: GHI={r[\"ghi_final_w_m2\"]:.1f}')
"

Esperar: OK: GHI=XXX.X (sin errores)

═════════════════════════════════════════════════════════════════════════════════
PASO 11: VERIFICAR CONTEXTO BLOQUEADO FUNCIONA
═════════════════════════════════════════════════════════════════════════════════

Comando:
python -c "
from core.indices.radiacion_hibrida import PiranometroHibrido
from datetime import datetime
p = PiranometroHibrido(latitud=41.3, longitud=2.1)
# Con lluvia y niebla → Contexto bloqueado
r = p.procesar_radiacion_hibrida(
    radiacion_medida=600.0, temp_wh65_c=20.0, temp_wh31_c=19.0,
    presion_hpa=1013.25, humedad_rel=80.0, velocidad_viento_ms=5.0,
    precipitacion_mm=2.5, visibilidad_km=3.0, fecha_hora=datetime.now()
)
print(f'Advertencias: {r[\"advertencias\"]}')
"

Esperar: Advertencias con lluvia, niebla, etc. (contexto bloqueado)

═════════════════════════════════════════════════════════════════════════════════
PASO 12: VERIFICAR LOGS CONTIENEN V51
═════════════════════════════════════════════════════════════════════════════════

Buscar en logs del sistema:
  "[RADIACION] Arquitectura radiativa robusta V51 ACTIVADA"
  "[WRAPPER] Nueva arquitectura radiativa robusta V51 ACTIVADA"
  "[CONTROLADOR] Iniciando ciclo radiación"
  "[RADIACION] Publicado 'radiacion_ghi_w_m2'"

Si ve "REST2_FALLBACK" → V51 falló pero sistema rescatable

═════════════════════════════════════════════════════════════════════════════════
PASO 13: VERIFICAR INTEGRACION CON ENDPOINTS
═════════════════════════════════════════════════════════════════════════════════

[ ] routers/fusion_endpoints.py línea 357: "from core.indices.radiacion_hibrida import PiranometroHibrido"
[ ] routers/fusion_endpoints.py línea 358: "pir = PiranometroHibrido()"

Cuando se llama endpoint de radiación, debe usar V51 automáticamente.

═════════════════════════════════════════════════════════════════════════════════
RESUMEN CHECKLIST
═════════════════════════════════════════════════════════════════════════════════

Si TODOS los pasos pasan:

    ✓✓✓ INTEGRACION V51 COMPLETADA Y FUNCIONANDO ✓✓✓

Si algunos fallan:
    
    → Revisar logs detallados en test_integracion_final_v51.py
    → Asegurar que core/radiation/ existe con 5 archivos .py
    → Verificar que radiacion_hibrida.py tiene todas las modificaciones
    → Fallback a REST2 debe siempre funcionar

═════════════════════════════════════════════════════════════════════════════════
FECHA DE VERIFICACION
═════════════════════════════════════════════════════════════════════════════════

Fecha: _______________
Verificador: _______________
Resultado: [ ] COMPLETADO  [ ] FALLIDO
Observaciones: _______________________________________________________________

═════════════════════════════════════════════════════════════════════════════════
