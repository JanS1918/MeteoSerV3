"""
Test del sistema AUTO-DISCOVERY V19.0 HÍBRIDO
Verifica que el sistema pueda escanear múltiples módulos y publicar sus subfactores automáticamente.

V19.0: Expansión controlada a prediction, virtual, sensors + decorador selectivo
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test_auto_discovery_v19")


class MockBus:
    """Bus simulado para testing."""
    def __init__(self):
        self.published = {}
        self.count = 0
    
    def publicar(self, key: str, value: Any, unit: str = None):
        """Registra publicación."""
        self.published[key] = {"value": value, "unit": unit}
        self.count += 1
        if self.count <= 20 or self.count % 100 == 0:
            logger.info(f"📊 Publicado #{self.count}: {key} = {value} {unit if unit else ''}")


class MockSystem:
    """Sistema simulado para testing."""
    def __init__(self):
        self.data = {
            "temperatura": 20.0,
            "humedad": 60.0,
            "presion_barometrica": 101325.0,
            "radiacion_solar": 500.0,
            "viento_velocidad": 10.0,
            "co2": 420.0,
            "pm25": 15.0
        }
        self.location = {
            "latitud": 40.0,
            "longitud": -3.0,
            "altitud": 600.0
        }


async def test_auto_discovery():
    """Test completo del auto-discovery."""
    
    logger.info("=" * 80)
    logger.info("🧪 TEST AUTO-DISCOVERY V18.0 - Sistema Automático de Captura")
    logger.info("=" * 80)
    
    # Crear mocks
    bus = MockBus()
    system = MockSystem()
    
    # Crear BusExpander
    try:
        from core.system.bus_expander import BusExpander
        expander = BusExpander(bus, system)
        
        logger.info("✅ BusExpander creado correctamente")
    except Exception as e:
        logger.error(f"❌ Error creando BusExpander: {e}")
        return
    
    # Ejecutar solo el auto-discovery
    logger.info("\n" + "=" * 80)
    logger.info("🔍 Ejecutando AUTO-DISCOVERY (Sección 41)...")
    logger.info("=" * 80 + "\n")
    
    count_before = bus.count
    
    try:
        await expander._publish_auto_discovery_subfactors()
        count_after = bus.count
        discovered = count_after - count_before
        
        logger.info("\n" + "=" * 80)
        logger.info(f"✅ AUTO-DISCOVERY COMPLETADO!")
        logger.info("=" * 80)
        logger.info(f"📊 Subfactores descubiertos automáticamente: {discovered}")
        logger.info(f"📦 Total acumulado en Bus: {count_after}")
        
        # Mostrar ejemplos de valores descubiertos
        logger.info("\n" + "=" * 80)
        logger.info("🔍 MUESTRA DE VALORES AUTO-DESCUBIERTOS (primeros 30):")
        logger.info("=" * 80)
        
        auto_keys = [k for k in list(bus.published.keys())[:30] if k.startswith(('motor_', 'brain_', 'elite_'))]
        for i, key in enumerate(auto_keys[:30], 1):
            entry = bus.published[key]
            logger.info(f"{i:2d}. {key} = {entry['value']} {entry['unit'] if entry['unit'] else ''}")
        
        if discovered > 30:
            logger.info(f"... y {discovered - 30} subfactores más")
        
        # Estadísticas por tipo
        logger.info("\n" + "=" * 80)
        logger.info("📈 ESTADÍSTICAS POR TIPO:")
        logger.info("=" * 80)
        
        motor_count = len([k for k in bus.published.keys() if k.startswith('motor_')])
        brain_count = len([k for k in bus.published.keys() if k.startswith('brain_')])
        elite_count = len([k for k in bus.published.keys() if k.startswith('elite_')])
        
        logger.info(f"  🤖 Motores ambientales: {motor_count} subfactores")
        logger.info(f"  🧠 StatisticalBrain: {brain_count} subfactores")
        logger.info(f"  ⭐ Elite Motors: {elite_count} subfactores")
        
        logger.info("\n" + "=" * 80)
        logger.info("✨ PROYECCIÓN FINAL:")
        logger.info("=" * 80)
        logger.info(f"  Manual implementadas: ~1180 constantes")
        logger.info(f"  Auto-descubiertas: {discovered} constantes")
        logger.info(f"  TOTAL ESTIMADO: {1180 + discovered} constantes")
        logger.info("=" * 80)
        
        # Verificar que se encontraron subfactores
        if discovered < 50:
            logger.warning(f"⚠️  ADVERTENCIA: Solo se encontraron {discovered} subfactores.")
            logger.warning("    Se esperaban 500-1500. Posibles causas:")
            logger.warning("    - Módulos no disponibles")
            logger.warning("    - Errores en instantiación de motores")
            logger.warning("    - Contexto insuficiente para analizar()")
        elif discovered < 500:
            logger.warning(f"⚠️  Se encontraron {discovered} subfactores (menos de lo esperado 500-1500)")
            logger.warning("    Es posible que algunos motores no pudieran instanciarse.")
        else:
            logger.info(f"✅ Cantidad de subfactores dentro del rango esperado (500-1500)")
        
        return discovered
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando auto-discovery: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def test_full_expansion():
    """Test de expansión completa (toma más tiempo)."""
    
    logger.info("\n" + "=" * 80)
    logger.info("🧪 TEST COMPLETO - Todas las secciones + AUTO-DISCOVERY")
    logger.info("=" * 80)
    
    bus = MockBus()
    system = MockSystem()
    
    try:
        from core.system.bus_expander import BusExpander
        expander = BusExpander(bus, system)
        
        logger.info("⏳ Ejecutando todas las secciones (esto puede tomar 1-2 minutos)...")
        start_time = datetime.now()
        
        await expander.publish_all_subfactors()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ EXPANSIÓN COMPLETA TERMINADA")
        logger.info("=" * 80)
        logger.info(f"⏱️  Tiempo de ejecución: {duration:.2f} segundos")
        logger.info(f"📊 Total constantes publicadas: {bus.count}")
        logger.info(f"🎯 Promedio: {bus.count / duration:.0f} constantes/segundo")
        logger.info("=" * 80)
        
        # Verificar meta de 2000+
        if bus.count >= 2000:
            logger.info("🎉 ¡META ALCANZADA! 2000+ constantes en el Bus")
        else:
            logger.warning(f"⚠️  Aún no se alcanza la meta de 2000 (actual: {bus.count})")
        
        return bus.count
        
    except Exception as e:
        logger.error(f"❌ Error en test completo: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    logger.info("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  TEST AUTO-DISCOVERY V19.0 HÍBRIDO                           ║
║                  MeteoSerV3 - Sistema Expandido                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Opción 1: Test rápido solo auto-discovery
    logger.info("Opción 1: Test rápido (solo auto-discovery V19.0)")
    logger.info("Opción 2: Test completo (todas las secciones)\n")
    
    # Por defecto ejecutar test rápido
    discovered = asyncio.run(test_auto_discovery())
    
    if discovered > 0:
        logger.info("\n💡 Para ejecutar el test completo, descomenta la línea en el código.")
        # Descomentar para test completo:
        # total = asyncio.run(test_full_expansion())
