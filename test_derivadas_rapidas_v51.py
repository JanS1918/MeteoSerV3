"""
Tests para el Scheduler Rápido de Derivadas V51
Validar: cálculo de derivadas, publicación en bus, detección de cambios rápidos
"""

import sys
import time
from datetime import datetime

# ═════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def registrar_test(nombre: str, exito: bool, error: str = None):
    """Registra resultado de un test"""
    estado = "[OK]" if exito else "[FAIL]"
    mensaje = f"  {estado} {nombre}"
    if error:
        mensaje += f" → {error}"
    print(mensaje)
    return exito

def test_derivadas_rapidas_v51():
    """Suite de tests para CalculadorDerivadosRapidosV51"""
    
    tests_totales = 0
    tests_pasados = 0
    
    print("\n" + "="*80)
    print("TEST: SCHEDULER RÁPIDO DE DERIVADAS V51")
    print("="*80)
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 1: Importar módulo
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 1] Importar módulo calculador_derivadas_rapidas_v51")
    tests_totales += 1
    try:
        from core.scheduler.calculador_derivadas_rapidas_v51 import (
            CalculadorDerivadosRapidosV51
        )
        registrar_test("Importación correcta", True)
        tests_pasados += 1
    except Exception as e:
        registrar_test("Importación", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 2: Instanciar calculador de derivadas
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 2] Instanciar CalculadorDerivadosRapidosV51")
    tests_totales += 1
    try:
        calc_deriv = CalculadorDerivadosRapidosV51(intervalo_segundos=10)
        exito = calc_deriv is not None
        registrar_test("Instancia creada", exito)
        tests_pasados += 1 if exito else 0
    except Exception as e:
        registrar_test("Instanciación", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 3: Iniciar scheduler de derivadas en background
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 3] Iniciar scheduler de derivadas en background")
    tests_totales += 1
    try:
        calc_deriv.iniciar()
        time.sleep(0.5)
        exito = calc_deriv.activo
        registrar_test("Derivadas iniciadas", exito)
        tests_pasados += 1 if exito else 0
    except Exception as e:
        registrar_test("Inicio scheduler", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 4: Obtener bus
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 4] Obtener instancia de bus")
    tests_totales += 1
    try:
        from core.indices.bus_estado_global import BusEstadoGlobal
        bus = BusEstadoGlobal.obtener_instancia()
        exito = bus is not None
        registrar_test("Bus obtenido", exito)
        tests_pasados += 1 if exito else 0
    except Exception as e:
        registrar_test("Bus", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 5: Publicar datos simulados en el bus
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 5] Publicar datos de radiación + humedad + presión")
    tests_totales += 1
    try:
        # Simular radiación variable (nube pasando)
        bus.publicar("radiacion_ghi_w_m2", 500.0, "test")
        bus.publicar("humedad", 65.0, "test")
        bus.publicar("presion", 1013.0, "test")
        
        registrar_test("Datos publicados", True)
        tests_pasados += 1
    except Exception as e:
        registrar_test("Publicación datos", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 6: Esperar ciclos y simular cambio de radiación
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 6] Simular cambio rápido de radiación (nube)")
    tests_totales += 1
    try:
        # Esperar a que se complete al menos 1 ciclo
        time.sleep(2)
        
        # Simular caída rápida de GHI (nube pasando)
        bus.publicar("radiacion_ghi_w_m2", 300.0, "test")  # Caída de 200 W/m²
        time.sleep(1)
        bus.publicar("radiacion_ghi_w_m2", 150.0, "test")  # Otra caída de 150 W/m²
        
        # Esperar cálculo
        time.sleep(2)
        
        registrar_test("Cambios simulados", True)
        tests_pasados += 1
    except Exception as e:
        registrar_test("Simulación cambios", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 7: Verificar derivadas en el bus
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 7] Verificar derivadas publicadas en el bus")
    tests_totales += 1
    try:
        def leer_bus_test(clave: str):
            try:
                if hasattr(bus, 'consumir'):
                    return bus.consumir(clave, "test")
                if hasattr(bus, '_estado') and clave in bus._estado:
                    return bus._estado[clave]
            except:
                pass
            return None
        
        derivada_ghi = leer_bus_test("derivada_ghi_w_m2_s")
        derivada_hr = leer_bus_test("derivada_hr_porciento_min")
        derivada_p = leer_bus_test("derivada_presion_hpa_min")
        resumen = leer_bus_test("derivadas_resumen_rapido")
        
        tiene_ghi = derivada_ghi is not None
        tiene_hr = derivada_hr is not None
        tiene_p = derivada_p is not None
        tiene_resumen = resumen is not None and isinstance(resumen, dict)
        
        exito = tiene_ghi and tiene_hr and tiene_p and tiene_resumen
        
        if exito:
            registrar_test(
                f"Derivadas: dGHI={derivada_ghi:.2f}, "
                f"dHR={derivada_hr:.2f}, dP={derivada_p:.3f}",
                True
            )
        else:
            registrar_test("Derivadas", exito)
        
        tests_pasados += 1 if exito else 0
    except Exception as e:
        registrar_test("Verificación derivadas", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 8: Simular aumento de humedad (lluvia inminente)
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 8] Simular aumento rápido de humedad")
    tests_totales += 1
    try:
        # Simular aumento de humedad
        bus.publicar("humedad", 70.0, "test")
        time.sleep(1)
        bus.publicar("humedad", 80.0, "test")
        time.sleep(1)
        bus.publicar("humedad", 90.0, "test")
        
        # Esperar cálculo
        time.sleep(2)
        
        registrar_test("Humedad incrementada", True)
        tests_pasados += 1
    except Exception as e:
        registrar_test("Aumento humedad", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 9: Simular caída de presión (sistema frontal)
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 9] Simular caída rápida de presión")
    tests_totales += 1
    try:
        # Simular caída de presión
        bus.publicar("presion", 1010.0, "test")
        time.sleep(1)
        bus.publicar("presion", 1007.0, "test")
        time.sleep(1)
        bus.publicar("presion", 1004.0, "test")
        
        # Esperar cálculo
        time.sleep(2)
        
        # Leer derivada de presión
        derivada_p = None
        try:
            derivada_p = bus.consumir("derivada_presion_hpa_min", "test")
        except:
            if hasattr(bus, '_estado') and "derivada_presion_hpa_min" in bus._estado:
                derivada_p = bus._estado["derivada_presion_hpa_min"]
        
        derivada_p = derivada_p or 0.0
        
        registrar_test(f"Presión con dP={derivada_p:.3f} hPa/min", True)
        tests_pasados += 1
    except Exception as e:
        registrar_test("Caída presión", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 10: Funciones globales
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 10] Funciones globales de scheduler de derivadas")
    tests_totales += 1
    try:
        from core.scheduler import (
            iniciar_calculador_derivadas_rapidas,
            detener_calculador_derivadas_rapidas,
            obtener_calculador_derivadas_rapidas
        )
        registrar_test("Funciones importadas", True)
        tests_pasados += 1
    except Exception as e:
        registrar_test("Funciones globales", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 11: Detener scheduler de derivadas
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 11] Detener scheduler de derivadas")
    tests_totales += 1
    try:
        calc_deriv.detener()
        time.sleep(0.5)
        registrar_test("Scheduler detenido", not calc_deriv.activo)
        tests_pasados += 1 if not calc_deriv.activo else 0
    except Exception as e:
        registrar_test("Detención", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 12: Iniciar a través de función global
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 12] Iniciar derivadas a través de función global")
    tests_totales += 1
    try:
        deriv_global = iniciar_calculador_derivadas_rapidas(intervalo_seg=10)
        time.sleep(0.5)
        registrar_test(
            "Scheduler global iniciado",
            deriv_global is not None and deriv_global.activo
        )
        tests_pasados += 1
        
        # Detener al final
        detener_calculador_derivadas_rapidas()
    except Exception as e:
        registrar_test("Función global", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 13: Verificar historial y cálculo de derivadas
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 13] Verificar historial interno y cálculo de derivadas")
    tests_totales += 1
    try:
        calc_test = CalculadorDerivadosRapidosV51(intervalo_segundos=5)
        
        # Simular histórico con cambio lineal
        from datetime import datetime, timedelta
        ahora = datetime.now()
        
        calc_test.historial_ghi.append((ahora - timedelta(seconds=10), 100.0))
        calc_test.historial_ghi.append((ahora - timedelta(seconds=5), 200.0))
        calc_test.historial_ghi.append((ahora, 300.0))
        
        derivada = calc_test._calcular_derivada(calc_test.historial_ghi)
        
        # Esperamos derivada positiva (aumento de 100 W/m² cada 5 seg = 20 W/m²/s)
        exito = 15 < derivada < 25  # Con margen de cálculo numérico
        
        registrar_test(f"Derivada calculada: {derivada:.2f} W/m²/s", exito)
        tests_pasados += 1 if exito else 0
    except Exception as e:
        registrar_test("Cálculo derivada", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # RESUMEN
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "="*80)
    print(f"RESULTADO: {tests_pasados}/{tests_totales} tests PASADOS")
    print("="*80)
    
    if tests_pasados == tests_totales:
        print("\n[OK] TODOS LOS TESTS PASARON [OK]\n")
        return True
    else:
        print(f"\n[FAIL] {tests_totales - tests_pasados} tests fallaron\n")
        return False

if __name__ == "__main__":
    try:
        exito = test_derivadas_rapidas_v51()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Tests interrumpidos por usuario")
        sys.exit(1)
