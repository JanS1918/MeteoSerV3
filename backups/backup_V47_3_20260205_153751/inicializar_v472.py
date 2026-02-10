"""
═══════════════════════════════════════════════════════════════════════════════
🚀 INICIALIZAR V47.2 - ACORAZADO CON CEREBRO EVOLUTIVO
═══════════════════════════════════════════════════════════════════════════════

Script de inicialización del sistema V47.2 SUMMUM.
Integra MOS Clustering + Feedback Learning en MeteoSerV3.

Ejecución:
    python inicializar_v472.py

Fecha: 2026-02-05
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import logging
import time
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/v472_inicializacion.log')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Inicializa V47.2 en MeteoSerV3."""
    
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO V47.2 SUMMUM - ACORAZADO CON CEREBRO EVOLUTIVO")
    logger.info("=" * 80)
    
    try:
        # 1. Verificar directorios
        logger.info("\n📁 Verificando estructura de directorios...")
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("backups").mkdir(exist_ok=True)
        logger.info("✅ Directorios verificados")
        
        # 2. Importar módulos necesarios
        logger.info("\n📦 Importando módulos V47.2...")
        from core.system.bus import Bus
        from core.integration.integrador_v472 import IntegradorV472
        logger.info("✅ Módulos importados correctamente")
        
        # 3. Inicializar Bus
        logger.info("\n🚌 Inicializando Bus de datos...")
        bus = Bus()
        logger.info("✅ Bus inicializado")
        
        # 4. Inicializar Integrador V47.2
        logger.info("\n🔗 Inicializando Integrador V47.2...")
        integrador = IntegradorV472(bus=bus, data_path="data")
        logger.info("✅ Integrador V47.2 inicializado")
        
        # 5. Verificar componentes
        logger.info("\n🔍 Verificando componentes...")
        logger.info(f"  • MOS Clustering: {integrador.mos.__class__.__name__}")
        logger.info(f"  • Feedback Learning: {integrador.feedback.__class__.__name__}")
        logger.info(f"  • Callbacks registrados: {len(integrador.feedback.callbacks_sensores)}")
        logger.info(f"  • Modelos activos: {len([m for m in integrador.feedback.modelos.values() if m.get('activo', False)])}")
        logger.info("✅ Componentes verificados")
        
        # 6. Ejemplo de uso
        logger.info("\n📊 Ejecutando predicción de ejemplo...")
        
        # Condiciones de ejemplo
        condiciones_ejemplo = {
            "viento": 1.2,
            "hr": 55,
            "cobertura_nubes": 10,
            "hora": 22,
        }
        
        # Predicción de ejemplo (Deardorff)
        resultado = integrador.predecir_con_correccion(
            modelo="deardorff_v47",
            parametro="temperatura_minima",
            valor_teorico=8.5,
            condiciones=condiciones_ejemplo,
            ventana_validacion_h=12
        )
        
        logger.info(f"  Resultado ejemplo:")
        logger.info(f"    • Valor teórico: {resultado['valor_teorico']:.2f}°C")
        logger.info(f"    • Valor corregido: {resultado['valor_corregido']:.2f}°C")
        logger.info(f"    • BIAS aplicado: {resultado['bias_aplicado']:.3f}°C")
        logger.info(f"    • Confianza MOS: {resultado['confianza_mos']:.1f}%")
        logger.info(f"    • Confianza modelo: {resultado['confianza_modelo']:.1f}%")
        logger.info(f"    • Escenario: {resultado['escenario']}")
        logger.info(f"    • Estado MOS: {resultado['estado_mos']}")
        logger.info("✅ Predicción ejecutada correctamente")
        
        # 7. Estadísticas del sistema
        logger.info("\n📈 Obteniendo estadísticas del sistema...")
        estadisticas = integrador.obtener_estadisticas()
        logger.info(f"  • Parámetros MOS activos: {len(estadisticas['mos'])}")
        logger.info(f"  • Parámetros Feedback activos: {len(estadisticas['feedback'])}")
        logger.info("✅ Estadísticas obtenidas")
        
        # 8. Instrucciones de uso
        logger.info("\n" + "=" * 80)
        logger.info("✅ V47.2 INICIALIZADO CORRECTAMENTE")
        logger.info("=" * 80)
        logger.info("\n📝 INSTRUCCIONES DE USO:")
        logger.info("\n1. Integración en MeteoSerV3:")
        logger.info("   from core.integration.integrador_v472 import IntegradorV472")
        logger.info("   integrador = IntegradorV472(bus=bus)")
        logger.info("\n2. Realizar predicción con corrección:")
        logger.info("   resultado = integrador.predecir_con_correccion(")
        logger.info("       modelo='deardorff_v47',")
        logger.info("       parametro='temperatura_minima',")
        logger.info("       valor_teorico=8.5,")
        logger.info("       condiciones={'viento': 1.2, 'hr': 55, ...}")
        logger.info("   )")
        logger.info("\n3. Validar predicciones periódicamente (cada 5 min):")
        logger.info("   integrador.validar_predicciones_pendientes()")
        logger.info("\n4. Registrar sensor nuevo:")
        logger.info("   integrador.registrar_sensor_nuevo(")
        logger.info("       parametro='pm25_aire',")
        logger.info("       sensor='PMS5003',")
        logger.info("       frecuencia_h=0.083,")
        logger.info("       umbral_acierto=5.0,")
        logger.info("       unidad='µg/m³',")
        logger.info("       callback_sensor=lambda: bus.obtener('pm25', 0.0)")
        logger.info("   )")
        logger.info("\n5. Obtener estadísticas:")
        logger.info("   stats = integrador.obtener_estadisticas()")
        logger.info("\n" + "=" * 80)
        logger.info("🛡️ ACORAZADO LISTO PARA APRENDER DE ARGENTONA")
        logger.info("=" * 80)
        
        return integrador
        
    except Exception as e:
        logger.error(f"\n❌ ERROR FATAL: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    integrador = main()
    
    logger.info("\n✅ Script completado. Integrador disponible en variable 'integrador'")
    logger.info("💡 Tip: Ejecutar validar_predicciones_pendientes() cada 5 minutos")
