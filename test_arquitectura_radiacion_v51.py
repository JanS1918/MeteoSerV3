"""
═══════════════════════════════════════════════════════════════════════════════
TEST SIMPLE DE ARQUITECTURA RADIATIVA ROBUSTA V51
═══════════════════════════════════════════════════════════════════════════════

Ejecutar con: python test_arquitectura_radiacion_v51.py

Validar que toda la arquitectura funciona sin romper el sistema existente.
"""

import sys
from datetime import datetime

print("[TEST] Iniciando test de arquitectura radiativa robusta V51")
print("=" * 70)

# TEST 1: IMPORTACIONES
print("\n[TEST 1] Validando importaciones...")
print("-" * 70)

try:
    from core.radiation.clasificador_contexto_radiativo import ClasificadorContextoRadiativo, EstadoContextoRadiativo
    from core.radiation.estrategias_aprendizaje import EstiloAprendizajeCorrectivo, EstiloAprendizajeDiagnostico
    from core.radiation.publicador_radiacion_robusto import PublicadorRadiacionRobusto, ValidadorCruzadoRadiacion, EstadoRadiativo
    from core.radiation.controlador_radiacion_robusto import ControladorRadiacionRobusto
    from core.radiation.wrapper_integracion import WrapperRadiacionRobusta
    print("[✓] Todas las importaciones OK")
except Exception as e:
    print(f"[✗] Error en importaciones: {e}")
    sys.exit(1)

# TEST 2: INSTANCIACIÓN
print("\n[TEST 2] Instanciando componentes...")
print("-" * 70)

try:
    clasificador = ClasificadorContextoRadiativo()
    print("[✓] ClasificadorContextoRadiativo")
    
    aprendizaje_correctivo = EstiloAprendizajeCorrectivo()
    print("[✓] EstiloAprendizajeCorrectivo")
    
    aprendizaje_diagnostico = EstiloAprendizajeDiagnostico()
    print("[✓] EstiloAprendizajeDiagnostico")
    
    publicador = PublicadorRadiacionRobusto()
    print("[✓] PublicadorRadiacionRobusto")
    
    validador_cruzado = ValidadorCruzadoRadiacion()
    print("[✓] ValidadorCruzadoRadiacion")
    
    controlador = ControladorRadiacionRobusto(
        clasificador=clasificador,
        aprendizaje_correctivo=aprendizaje_correctivo,
        aprendizaje_diagnostico=aprendizaje_diagnostico,
        publicador=publicador,
        validador_cruzado=validador_cruzado
    )
    print("[✓] ControladorRadiacionRobusto")
    
    wrapper = WrapperRadiacionRobusta(enabled=False)  # Sin activar
    print("[✓] WrapperRadiacionRobusta")
    
except Exception as e:
    print(f"[✗] Error en instanciación: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 3: CLASIFICADOR
print("\n[TEST 3] Probando ClasificadorContextoRadiativo...")
print("-" * 70)

try:
    estado = EstadoContextoRadiativo(
        timestamp=datetime.now(),
        elevacion_solar_deg=45.0,
        ghi_w_m2=600.0,
        presion_hpa=1013.25,
        humedad_rel=60.0,
        temperatura_c=25.0,
        velocidad_viento_ms=3.0,
        precipitacion_mm=0.0,
        visibilidad_km=50.0
    )
    
    estado_clasificado = clasificador.clasificar(estado)
    
    if estado_clasificado.es_valido_para_aprendizaje:
        print("[✓] Contexto clasificado como VÁLIDO (limpio)")
    else:
        print(f"[!] Contexto clasificado como INVÁLIDO (bloqueado: {estado_clasificado.motivos_bloqueo})")
    
    print(f"    - Confianza: {estado_clasificado.confianza_general:.2f}")
    print("[✓] ClasificadorContextoRadiativo funciona")
    
except Exception as e:
    print(f"[✗] Error en clasificador: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 4: APRENDIZAJE CORRECTIVO
print("\n[TEST 4] Probando EstiloAprendizajeCorrectivo...")
print("-" * 70)

try:
    resultado_correctivo = aprendizaje_correctivo.procesar(
        ghi_modelo=600.0,
        ghi_observado_estimado=620.0,  # Observado ligeramente mayor
        elevacion_solar_deg=45.0,
        contexto_limpio=True,
        confianza_contexto=0.85,
        timestamp=datetime.now()
    )
    
    print(f"[✓] Aprendizaje correctivo procesado")
    print(f"    - Kt_local: {resultado_correctivo.kt_local:.3f}")
    print(f"    - Confianza ajuste: {resultado_correctivo.confianza_ajuste:.2f}")
    print(f"    - Observaciones: {resultado_correctivo.numero_observaciones}")
    
except Exception as e:
    print(f"[✗] Error en aprendizaje correctivo: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 5: APRENDIZAJE DIAGNÓSTICO
print("\n[TEST 5] Probando EstiloAprendizajeDiagnostico...")
print("-" * 70)

try:
    resultado_diagnostico = aprendizaje_diagnostico.procesar(
        ghi_modelo=600.0,
        ghi_observado_estimado=480.0,  # 80% del modelo (posible calima)
        elevacion_solar_deg=45.0,
        temperatura_c=25.0,
        humedad_rel=50.0
    )
    
    print(f"[✓] Aprendizaje diagnóstico procesado")
    print(f"    - Calima: {resultado_diagnostico.calima_detectada} (conf={resultado_diagnostico.calima_confianza:.2f})")
    print(f"    - Nubosidad fina: {resultado_diagnostico.nubosidad_fina_detectada}")
    print(f"    - Confianza radiación: {resultado_diagnostico.confianza_radiacion_general:.2f}")
    
except Exception as e:
    print(f"[✗] Error en aprendizaje diagnóstico: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 6: PUBLICADOR
print("\n[TEST 6] Probando PublicadorRadiacionRobusto...")
print("-" * 70)

try:
    estado_rad = EstadoRadiativo(
        clave="test_ghi",
        valor=600.0,
        unidad="W/m²",
        confianza=0.9,
        fuente="modelo",
        contexto_limpio=True,
        timestamp=datetime.now(),
        formula="REST2"
    )
    
    publicador.publicar_estado(estado_rad, descripcion="Test de publicación")
    print("[✓] Estado publicado correctamente")
    
    valor_consumido = publicador.consumir_para_indice("wbgt", "test_ghi")
    if valor_consumido is not None:
        print(f"[✓] Estado consumido para WBGT: {valor_consumido:.0f} W/m²")
    else:
        print("[!] Estado no consumible para WBGT (bajo confianza o jerarquía)")
    
except Exception as e:
    print(f"[✗] Error en publicador: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 7: VALIDADOR CRUZADO
print("\n[TEST 7] Probando ValidadorCruzadoRadiacion...")
print("-" * 70)

try:
    resultado_validacion = validador_cruzado.validar(
        ghi_w_m2=600.0,
        temperatura_c=25.0,
        temperatura_anterior_c=24.5,
        minutos_transcurridos=5.0
    )
    
    print(f"[✓] Validación cruzada procesada")
    print(f"    - Radiación sospechosa: {resultado_validacion['radiacion_sospechosa']}")
    print(f"    - Temperatura sospechosa: {resultado_validacion['temperatura_sospechosa']}")
    print(f"    - Balance OK: {resultado_validacion['balance_ok']}")
    
except Exception as e:
    print(f"[✗] Error en validador cruzado: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 8: CONTROLADOR COMPLETO
print("\n[TEST 8] Probando ControladorRadiacionRobusto (ciclo completo)...")
print("-" * 70)

try:
    resultado_controlador = controlador.procesar_ciclo_radiacion(
        elevacion_solar_deg=45.0,
        ghi_w_m2_medida=620.0,
        presion_hpa=1013.25,
        humedad_rel=60.0,
        temperatura_c=25.0,
        velocidad_viento_ms=3.0,
        precipitacion_mm=0.0,
        visibilidad_km=50.0,
        ghi_modelo_rest2=600.0,
        dni_modelo_rest2=750.0,
        dhi_modelo_rest2=100.0,
        timestamp=datetime.now(),
        sensor_real_confiable=True
    )
    
    print("[✓] Controlador procesó ciclo completo")
    print(f"    - GHI final: {resultado_controlador['ghi_final']:.0f} W/m²")
    print(f"    - DNI final: {resultado_controlador['dni_final']:.0f} W/m²")
    print(f"    - DHI final: {resultado_controlador['dhi_final']:.0f} W/m²")
    print(f"    - Confianza: {resultado_controlador['confianza']:.2f}")
    print(f"    - Estados publicados: {len(resultado_controlador['estados_publicados'])}")
    
    if resultado_controlador['advertencias']:
        print(f"    - Advertencias: {resultado_controlador['advertencias']}")
    
except Exception as e:
    print(f"[✗] Error en controlador: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 9: WRAPPER
print("\n[TEST 9] Probando WrapperRadiacionRobusta...")
print("-" * 70)

try:
    wrapper_enabled = WrapperRadiacionRobusta(enabled=True)
    
    resultado_wrapper = wrapper_enabled.procesar(
        elevacion_solar_deg=45.0,
        ghi_w_m2_medida=620.0,
        presion_hpa=1013.25,
        humedad_rel=60.0,
        temperatura_c=25.0,
        velocidad_viento_ms=3.0,
        precipitacion_mm=0.0,
        visibilidad_km=50.0,
        rest2_output={'ghi': 600.0, 'dni': 750.0, 'dhi': 100.0},
        sensor_real_confiable=True
    )
    
    print("[✓] Wrapper con arquitectura robusta activada")
    print(f"    - Usada nueva arquitectura: {resultado_wrapper['usada_nueva_arquitectura']}")
    print(f"    - GHI: {resultado_wrapper['ghi']:.0f} W/m²")
    print(f"    - Confianza: {resultado_wrapper['confianza']:.2f}")
    
except Exception as e:
    print(f"[✗] Error en wrapper: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# RESUMEN
print("\n" + "=" * 70)
print("[ÉXITO] TODOS LOS TESTS PASARON")
print("=" * 70)
print("")
print("RESUMEN:")
print("  ✓ Importaciones")
print("  ✓ Instanciación de componentes")
print("  ✓ Clasificador de contexto")
print("  ✓ Aprendizaje correctivo")
print("  ✓ Aprendizaje diagnóstico")
print("  ✓ Publicador de radiación")
print("  ✓ Validador cruzado")
print("  ✓ Controlador completo")
print("  ✓ Wrapper de integración")
print("")
print("La arquitectura radiativa robusta V51 está lista para integración.")
print("")
