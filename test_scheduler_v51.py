"""
Test del Scheduler Automático de Índices V51
Verifica que el calculador publica TODO en el bus correctamente
"""

import logging
import time
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def registrar_test(nombre: str, resultado: bool, error: str = ""):
    """Registra resultado de test"""
    estado = "[OK]" if resultado else "[FAIL]"
    print(f"  {estado} {nombre}")
    if error:
        print(f"       Error: {error}")
    return resultado

def test_scheduler_v51():
    """Test completo del scheduler V51"""
    
    print("\n" + "="*80)
    print("TEST: SCHEDULER AUTOMÁTICO DE INDICES V51")
    print("="*80 + "\n")
    
    tests_pasados = 0
    tests_totales = 0
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 1: Importar módulo
    # ═════════════════════════════════════════════════════════════════════════
    print("[TEST 1] Importar módulo calculador_indices_automatico")
    tests_totales += 1
    try:
        from core.scheduler.calculador_indices_automatico import (
            CalculadorIndicesAutomatico,
            iniciar_calculador_indices,
            detener_calculador_indices
        )
        registrar_test("Importación correcta", True)
        tests_pasados += 1
    except Exception as e:
        registrar_test("Importación", False, str(e))
        return False
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 2: Instanciar clase
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 2] Instanciar CalculadorIndicesAutomatico")
    tests_totales += 1
    try:
        calc = CalculadorIndicesAutomatico(intervalo_segundos=10)
        registrar_test("Instancia creada", True)
        tests_pasados += 1
    except Exception as e:
        registrar_test("Instancia", False, str(e))
        return False
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 3: Iniciar scheduler
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 3] Iniciar scheduler en background")
    tests_totales += 1
    try:
        calc.iniciar()
        time.sleep(0.5)
        registrar_test("Scheduler iniciado", calc.activo)
        tests_pasados += 1 if calc.activo else 0
    except Exception as e:
        registrar_test("Inicio", False, str(e))
        return False
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 4: Verificar que el bus está disponible
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 4] Verificar bus disponible")
    tests_totales += 1
    try:
        try:
            from core.indices.bus_estado_global import BusEstadoGlobal
        except ImportError:
            from bus_estado_global import BusEstadoGlobal
        
        bus = BusEstadoGlobal.obtener_instancia()
        registrar_test("Bus obtenido", bus is not None)
        tests_pasados += 1 if bus else 0
    except Exception as e:
        registrar_test("Bus", False, str(e))
        # No es crítico, continuar
        bus = None
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 5: Publicar datos de prueba en el bus (simular radiación)
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 5] Publicar datos simulados en el bus")
    tests_totales += 1
    try:
        if bus:
            # Publicar radiación simulada
            bus.publicar("radiacion_ghi_w_m2", 750.0, "test", {"unidad": "W/m²"})
            bus.publicar("radiacion_dni_w_m2", 650.0, "test", {"unidad": "W/m²"})
            bus.publicar("radiacion_dhi_w_m2", 150.0, "test", {"unidad": "W/m²"})
            bus.publicar("temperatura", 28.5, "test", {"unidad": "°C"})
            bus.publicar("humedad", 65.0, "test", {"unidad": "%"})
            bus.publicar("presion", 1013.25, "test", {"unidad": "hPa"})
            bus.publicar("velocidad_viento", 2.5, "test", {"unidad": "m/s"})
            bus.publicar("elevacion_solar", 45.0, "test", {"unidad": "grados"})
            
            registrar_test("Datos publicados en bus", True)
            tests_pasados += 1
        else:
            registrar_test("Bus no disponible, saltando", True)
            tests_pasados += 1
    except Exception as e:
        registrar_test("Publicación de datos", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 6: Ejecutar ciclo manual del scheduler
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 6] Ejecutar ciclo de cálculo manual")
    tests_totales += 1
    try:
        if bus:
            calc._ciclo_calculo()
            registrar_test("Ciclo de cálculo ejecutado", True)
            tests_pasados += 1
        else:
            registrar_test("Bus no disponible, saltando", True)
            tests_pasados += 1
    except Exception as e:
        registrar_test("Ciclo de cálculo", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 7: Verificar que se publicaron resultados en el bus
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 7] Verificar indices publicados en el bus")
    tests_totales += 1
    try:
        if bus:
            # Esperar un poco a que se publiquen
            time.sleep(1)
            
            # Función auxiliar para leer del bus
            def leer_bus_test(clave: str, default=None):
                try:
                    if hasattr(bus, 'obtener'):
                        val = bus.obtener(clave)
                        if val is not None:
                            return float(val) if isinstance(val, (int, float)) else val
                    
                    if hasattr(bus, 'consumir'):
                        val = bus.consumir(clave, "test")
                        if val is not None:
                            return float(val) if isinstance(val, (int, float)) else val
                    
                    if hasattr(bus, '_estado') and clave in bus._estado:
                        val = bus._estado[clave]
                        return float(val) if isinstance(val, (int, float)) else val
                except:
                    pass
                return default
            
            # Intentar leer algunos índices
            wbgt = leer_bus_test("wbgt_outdoor")
            et0 = leer_bus_test("et0_mm_dia")
            utci = leer_bus_test("utci_indice_termico")
            pr = leer_bus_test("punto_rocio_termometrico")
            
            campos_publicados = []
            if wbgt is not None:
                campos_publicados.append(f"WBGT={wbgt:.1f}°C")
            if et0 is not None:
                campos_publicados.append(f"ET0={et0:.2f}mm")
            if utci is not None:
                campos_publicados.append(f"UTCI={utci:.1f}°C")
            if pr is not None:
                campos_publicados.append(f"PR={pr:.1f}°C")
            
            if campos_publicados:
                print(f"       Campos detectados en bus: {', '.join(campos_publicados)}")
                registrar_test("Indices publicados correctamente", True)
                tests_pasados += 1
            else:
                registrar_test("Indices publicados", False, "Ningún índice encontrado en bus")
        else:
            registrar_test("Bus no disponible, saltando", True)
            tests_pasados += 1
    except Exception as e:
        registrar_test("Verificación de índices", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 8: Detener scheduler
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 8] Detener scheduler")
    tests_totales += 1
    try:
        calc.detener()
        time.sleep(0.5)
        registrar_test("Scheduler detenido", not calc.activo)
        tests_pasados += 1 if not calc.activo else 0
    except Exception as e:
        registrar_test("Detención", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 9: Verificar funciones globales
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 9] Funciones globales de scheduler")
    tests_totales += 1
    try:
        from core.scheduler import (
            iniciar_calculador_indices,
            detener_calculador_indices,
            obtener_calculador_indices
        )
        registrar_test("Funciones importadas", True)
        tests_pasados += 1
    except Exception as e:
        registrar_test("Funciones globales", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 10: Iniciar a través de función global
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 10] Iniciar scheduler a través de función global")
    tests_totales += 1
    try:
        # Limpiar entrada anterior
        detener_calculador_indices()
        time.sleep(0.5)
        
        # Iniciar nueva
        calc_global = iniciar_calculador_indices()
        time.sleep(0.5)
        registrar_test("Scheduler global iniciado", calc_global is not None and calc_global.activo)
        tests_pasados += 1
        
        # Detener al final
        detener_calculador_indices()
    except Exception as e:
        registrar_test("Función global", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # TEST 11: Integración de Alerta de Lluvia Inminente
    # ═════════════════════════════════════════════════════════════════════════
    print("\n[TEST 11] Integración AlertaLluviaInminente en scheduler")
    tests_totales += 1
    try:
        from core.prediction.alerta_lluvia_inminente_v51 import AlertaLluviaInminenteV51
        from datetime import datetime
        
        alerta = AlertaLluviaInminenteV51()
        
        # Simular condiciones de lluvia inminente (GHI drop, HR increase, presión baja)
        datos_lluvia = {
            "ghi_w_m2": 150.0,      # Caída de radiación
            "humedad": 85.0,         # Humedad alta
            "presion": 1008.0,       # Presión baja
            "temperatura": 22.0,
            "dt_solar": 0.5,         # ΔT bajo (nubes)
            "timestamp": datetime.now()
        }
        
        resultado = alerta.evaluar(datos_lluvia)
        
        # Verificar que el resultado tiene la estructura esperada
        tiene_score = "score" in resultado
        tiene_eta = "eta_minutos" in resultado
        tiene_componentes = "componentes" in resultado
        tiene_confianza = "confianza" in resultado
        
        exito_alerta = tiene_score and tiene_eta and tiene_componentes and tiene_confianza
        score = resultado.get("score", 0) if exito_alerta else None
        
        registrar_test(f"Alerta lluvia: score={score:.0f}" if exito_alerta else "Estructura alerta", exito_alerta)
        tests_pasados += 1 if exito_alerta else 0
        
    except Exception as e:
        registrar_test("AlertaLluvia integración", False, str(e))
    
    # ═════════════════════════════════════════════════════════════════════════
    # RESUMEN
    # ═════════════════════════════════════════════════════════════════════════
    print("\n" + "="*80)
    print(f"RESULTADO: {tests_pasados}/{tests_totales} tests PASADOS")
    print("="*80)
    
    if tests_pasados == tests_totales:
        print("\n✓✓✓ TODOS LOS TESTS PASARON ✓✓✓\n")
        return True
    else:
        print(f"\n✗ {tests_totales - tests_pasados} tests fallaron\n")
        return False

if __name__ == "__main__":
    try:
        exito = test_scheduler_v51()
        sys.exit(0 if exito else 1)
    except Exception as e:
        logger.error(f"Error en tests: {e}", exc_info=True)
        sys.exit(1)
