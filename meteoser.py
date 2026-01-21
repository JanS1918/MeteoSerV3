# ============================================================
# MÓDULO H — PUNTO DE ENTRADA PRINCIPAL (meteoser.py)
# ============================================================

from core.system.system_manager import SystemManager
from core.indices.environmental_indices import EnvironmentalIndices
from core.recommendations.unified_recommendation_engine import (
    UnifiedRecommendationEngine,
)
from core.meteo_interface import MeteoSerInterface

EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales


def main():
    """
    Punto de entrada principal del sistema MeteoSer.
    Expone la interfaz universal MeteoSerInterface con datos reales.
    """
    # Motores reales
    system_manager = SystemManager()
    system = system_manager.iniciar()
    indices_engine = EnvironmentalIndices(system)
    recommendation_engine = UnifiedRecommendationEngine(system, indices_engine)

    # Interfaz universal
    meteo = MeteoSerInterface(
        system_manager=system_manager,
        index_engine=indices_engine,
        recommendation_engine=recommendation_engine,
    )

    print("\n=== METEOSER — INTERFAZ UNIVERSAL ===\n")

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
