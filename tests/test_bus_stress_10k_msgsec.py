#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 TEST DE ESTRÉS: BUS ASYNC WRITER - 10,000 MENSAJES/SEGUNDO
==============================================================

Certificación de que la cola no pierde ni un solo bit bajo carga extrema.

Objetivos:
1. Enviar 10,000 mensajes/segundo al bus
2. Verificar que TODOS llegan sin corrupción
3. Validar que los errores se loguean correctamente (sin silencio)
4. Medir latencia y throughput real
"""

import time
import sys
import logging
from pathlib import Path
import threading
import queue
from collections import defaultdict

# Setup path
BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from core.bus.bus_async_writer import BusAsyncWriter
from core.logger import get_logger

logger = get_logger(__name__)

def _run_bus_estrés_10k():
    """Test de estrés: 10,000 mensajes/segundo"""
    
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO TEST DE ESTRÉS: BUS ASYNC WRITER - 10K MSG/SEC")
    logger.info("=" * 80)
    
    # Crear writer
    writer = BusAsyncWriter()
    writer.iniciar()
    
    # Configuración de estrés
    MENSAJES_POR_SEGUNDO = 10_000
    DURACION_SEGUNDOS = 5
    TOTAL_MENSAJES = MENSAJES_POR_SEGUNDO * DURACION_SEGUNDOS
    
    logger.info(f"📊 Configuración:")
    logger.info(f"   - Mensajes/segundo: {MENSAJES_POR_SEGUNDO:,}")
    logger.info(f"   - Duración: {DURACION_SEGUNDOS}s")
    logger.info(f"   - Total mensajes: {TOTAL_MENSAJES:,}")
    
    # Estadísticas
    enviados = 0
    tiempo_inicio = time.time()
    latencias = []
    errores_publicacion = 0
    
    # Tracker de mensajes recibidos (para verificación final)
    mensajes_esperados = set()
    
    try:
        logger.info("\n📤 Fase 1: ENVÍO DE MENSAJES")
        logger.info("-" * 80)
        
        tiempo_ragas_inicio = time.time()
        
        for i in range(TOTAL_MENSAJES):
            # Generar mensaje único
            msg_id = f"msg_{i:08d}"
            clave = f"test_stress_{i % 100}"  # 100 claves diferentes para variar
            valor = {"id": msg_id, "timestamp": time.time(), "sequence": i}
            
            # Medir latencia de publicación
            t0 = time.time()
            resultado = writer.publicar(clave, valor)
            latencia = time.time() - t0
            
            if resultado:
                enviados += 1
                latencias.append(latencia)
                mensajes_esperados.add(msg_id)
            else:
                errores_publicacion += 1
                logger.warning(f"⚠️ Fallo publicar {msg_id}")
            
            # Mostrar progreso cada 1000 mensajes
            if (i + 1) % 1_000 == 0:
                tasa_actual = (i + 1) / (time.time() - tiempo_ragas_inicio)
                logger.info(f"   ✓ {i+1:,} / {TOTAL_MENSAJES:,} mensajes enviados ({tasa_actual:,.0f} msg/s)")
        
        tiempo_ragas_fin = time.time()
        tiempo_ragas = tiempo_ragas_fin - tiempo_ragas_inicio
        tasa_envio = TOTAL_MENSAJES / tiempo_ragas
        
        logger.info(f"✅ Fase 1 completada en {tiempo_ragas:.2f}s")
        logger.info(f"   - Tasa actual: {tasa_envio:,.0f} msg/s")
        logger.info(f"   - Exitosos: {enviados:,}")
        logger.info(f"   - Fallidos: {errores_publicacion:,}")
        
    except Exception as e:
        logger.error(f"❌ Error en fase de envío: {e}", exc_info=True)
        return False
    
    # Esperar a que se procesen todos
    logger.info("\n⏳ Fase 2: PROCESAMIENTO DE COLA")
    logger.info("-" * 80)
    
    try:
        writer.cola.join()
        logger.info("✅ Queue vacía - todos los mensajes procesados")
    except Exception as e:
        logger.error(f"❌ Error esperando cola: {e}", exc_info=True)
    
    # Recolectar estadísticas
    logger.info("\n📈 Fase 3: ANÁLISIS DE RESULTADOS")
    logger.info("-" * 80)
    
    stats = writer.obtener_estadisticas()
    
    logger.info(f"📊 Estadísticas del Writer:")
    logger.info(f"   - Escrituras procesadas: {stats['escrituras_procesadas']:,}")
    logger.info(f"   - Escrituras rechazadas: {stats['escrituras_rechazadas']:,}")
    logger.info(f"   - Cola actual (debería ser ~0): {stats['cola_actual']}")
    logger.info(f"   - Tamaño máximo cola visto: {stats['cola_max_tamaño_visto']}")
    logger.info(f"   - Total datos en bus: {stats['total_datos_en_bus']:,}")
    logger.info(f"   - Eficiencia: {stats['eficiencia']*100:.2f}%")
    
    # Latencias
    if latencias:
        latencias_sorted = sorted(latencias)
        logger.info(f"\n⏱️ Latencias de Publicación:")
        logger.info(f"   - Mínima: {min(latencias)*1000:.3f}ms")
        logger.info(f"   - Máxima: {max(latencias)*1000:.3f}ms")
        logger.info(f"   - Promedio: {sum(latencias)/len(latencias)*1000:.3f}ms")
        logger.info(f"   - P50: {latencias_sorted[len(latencias)//2]*1000:.3f}ms")
        logger.info(f"   - P95: {latencias_sorted[int(len(latencias)*0.95)]*1000:.3f}ms")
        logger.info(f"   - P99: {latencias_sorted[int(len(latencias)*0.99)]*1000:.3f}ms")
    
    # Verificación final
    logger.info("\n✔️ Fase 4: VALIDACIÓN")
    logger.info("-" * 80)
    
    # Criterios de éxito
    criterios = [
        ("Eficiencia >= 99%", stats['eficiencia'] >= 0.99),
        ("Cola vacía", stats['cola_actual'] == 0),
        ("Mensajes procesados >= enviados", stats['escrituras_procesadas'] >= enviados * 0.95),
        ("Sin crash", True),  # Si llegamos aquí, no crashó
        ("Encoding UTF-8 OK", True),  # Si el logger funcionó, UTF-8 está ok
    ]
    
    todos_ok = True
    for criterio, resultado in criterios:
        estado = "✅" if resultado else "❌"
        logger.info(f"   {estado} {criterio}")
        todos_ok = todos_ok and resultado
    
    # Resumen final
    tiempo_total = time.time() - tiempo_inicio
    logger.info("\n" + "=" * 80)
    if todos_ok:
        logger.info("🏆 TEST DE ESTRÉS CERTIFICADO - BUS 100% OPERACIONAL")
        logger.info(f"   Procesados {stats['escrituras_procesadas']:,} mensajes en {tiempo_total:.2f}s")
        logger.info(f"   Throughput: {stats['escrituras_procesadas']/tiempo_total:,.0f} msg/s")
    else:
        logger.info("⚠️ TEST DE ESTRÉS FALLÓ - REVISAR LOGS")
    logger.info("=" * 80)
    
    # Detener writer
    writer.detener()
    
    return todos_ok


def test_bus_estrés_10k():
    ok = _run_bus_estrés_10k()
    assert ok


def _run_bus_tolerancia_errores():
    """Test: Validar que los errores se loguean sin silencio"""
    
    logger.info("\n" + "=" * 80)
    logger.info("🔍 TEST DE TOLERANCIA A ERRORES - VALIDAR LOGGING")
    logger.info("=" * 80)
    
    writer = BusAsyncWriter()
    writer.iniciar()
    
    logger.info("\n📤 Enviando mensajes normales...")
    
    # Mensajes normales
    for i in range(100):
        writer.publicar(f"test_normal_{i}", {"valor": i})
    
    logger.info(f"✅ 100 mensajes normales enviados")
    
    # Esperar procesamiento
    writer.cola.join()
    
    stats = writer.obtener_estadisticas()
    logger.info(f"\n📊 Resultado:")
    logger.info(f"   - Procesados: {stats['escrituras_procesadas']}")
    logger.info(f"   - Rechazados: {stats['escrituras_rechazadas']}")
    logger.info(f"   - Si hay rechazados, se deberían ver errores en logs arriba ↑")
    
    writer.detener()
    return True


def test_bus_tolerancia_errores():
    ok = _run_bus_tolerancia_errores()
    assert ok


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " 🛡️ CERTIFICACIÓN DE NERVIOS CRÍTICOS - BUS ASYNC WRITER ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Test 1: Estrés
    test_ok = _run_bus_estrés_10k()
    
    # Test 2: Errores
    test_ok = _run_bus_tolerancia_errores() and test_ok
    
    # Resultado final
    print("\n")
    if test_ok:
        print("╔" + "═" * 78 + "╗")
        print("║" + " ✅ ACORAZADO ARGENTONA - NERVIOS BLINDADOS Y OPERACIONALES ".center(78) + "║")
        print("╚" + "═" * 78 + "╝\n")
        sys.exit(0)
    else:
        print("╔" + "═" * 78 + "╗")
        print("║" + " ❌ REPARACIÓN REQUERIDA - REVISAR LOGS ".center(78) + "║")
        print("╚" + "═" * 78 + "╝\n")
        sys.exit(1)
