# ============================================================
# MÓDULO H — PUNTO DE ENTRADA PRINCIPAL (meteoser.py)
# ============================================================

from core.system.system_manager import SystemManager
from core.indices.environmental_indices import EnvironmentalIndices
from core.recommendations.unified_recommendation_engine import UnifiedRecommendationEngine
from core.meteo_interface import MeteoSerInterface
from core.system.auto_instrumentacion import instrumentar_sistema_completo
import logging

logger = logging.getLogger("meteoser.main")

EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales

def main():
    """
    Punto de entrada principal del sistema MeteoSer.
    """
    # Motores reales
    system_manager = SystemManager()
    system = system_manager.iniciar()
    
    # 🚀 AUTO-INSTRUMENTACIÓN V29.0: Activar captura automática de TODOS los subfactores
    logger.info("═" * 80)
    logger.info("🚀 AUTO-INSTRUMENTACIÓN V29.0: Activando captura automática...")
    logger.info("   TODOS los subfactores serán publicados automáticamente al Bus")
    logger.info("═" * 80)
    
    bus_instance = system.get("bus_global")  # Obtener instancia del Bus
    if bus_instance:
        stats = instrumentar_sistema_completo(bus_instance)
        logger.info(f"✅ Instrumentación completa: {sum(stats.values())} funciones activas")
    else:
        logger.warning("⚠️ Bus Global no encontrado, auto-instrumentación desactivada")
    
    indices_engine = EnvironmentalIndices(system)
    recommendation_engine = UnifiedRecommendationEngine(system, indices_engine)

    # Interfaz universal
    interface = MeteoSerInterface(
        system_manager=system_manager,
        index_engine=indices_engine,
        recommendation_engine=recommendation_engine
    )

    print("[Sensores]")
    sensores = meteo.obtener_sensores()
    for nombre, valor in sensores.items():
        print(f" - {nombre}: {valor}")

    print("\n[Índices]")
    indices = meteo.calcular_indices()
    for nombre, valor in indices.items():
        print(f" - {nombre}: {valor}")

    print("\n[Recomendación]")
    rec = meteo.obtener_recomendaciones()
    print(f" → {rec.get('estado')}")
    print(f"   Motivos: {rec.get('motivos')}")

if __name__ == "__main__":
    main()