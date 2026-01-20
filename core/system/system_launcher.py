# ============================================================
# MÓDULO E — SYSTEM LAUNCHER (ORQUESTADOR DE ARRANQUE)
# ============================================================

from core.system.system_core import SystemCore
from core.indices.environmental_indices import EnvironmentalIndices
from core.recommendations.unified_recommendation_engine import UnifiedRecommendationEngine
from core.architecture.open_architecture import OpenArchitecture
from core.auto.auto_improvement_engine import AutoImprovementEngine
from core.engines.autoimprovement_engine import AutoImprovementSystem
from core.ideas_master_blocks import (
    bloque_a, bloque_b, bloque_c, bloque_d, bloque_e, bloque_f, bloque_g, bloque_h, inicializar_bloque_total
)

EXTERNAL_INTEGRATION_MODE = "live"  # Solo datos reales

class SystemLauncher:
    """
    Orquestador principal del sistema.
    Ensambla todos los módulos y devuelve un sistema listo para usar.
    """

    def __init__(self):
        self.system = None
        self.indices = None
        self.recommendations = None
        self.architecture = None

    # --------------------------------------------------------
    # ARRANQUE COMPLETO
    # --------------------------------------------------------
    def launch(self):
        """
        Ensambla todos los componentes del sistema en orden correcto.
        """

        # 1. Núcleo
        self.system = SystemCore()

        # 2. Índices
        self.indices = EnvironmentalIndices(self.system)

        # 3. Motor de recomendaciones
        self.recommendations = UnifiedRecommendationEngine(self.system, self.indices)
        self.system.conectar_recommendation_engine(self.recommendations)

        # 4. Arquitectura unificada
        self.architecture = OpenArchitecture(self.system)

        # 5. Auto-mejora
        auto_improvement = AutoImprovementEngine()
        self.system.conectar_auto_improvement_engine(auto_improvement)

        # 6. Auto-mejora/expansión (sistema existente)
        auto_system = AutoImprovementSystem()
        self.system.conectar_auto_improvement_system(auto_system)

        # 7. Conectar bloques funcionales A-H
        self.system.bloque_a = bloque_a
        self.system.bloque_b = bloque_b
        self.system.bloque_c = bloque_c
        self.system.bloque_d = bloque_d
        self.system.bloque_e = bloque_e
        self.system.bloque_f = bloque_f
        self.system.bloque_g = bloque_g
        self.system.bloque_h = bloque_h

        # 8. Activar funcionalidades principales de todos los bloques
        self.system.activar_bloques_funcionales()

        # 9. Inicializar bloque total funcional
        inicializar_bloque_total(self.system)

        return self.system

    # --------------------------------------------------------
    # SNAPSHOT COMPLETO
    # --------------------------------------------------------
    def obtener_estado(self):
        if not self.system:
            return {"estado": "Sistema no iniciado."}
        return self.system.obtener_estado_completo()
