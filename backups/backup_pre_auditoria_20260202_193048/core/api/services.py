"""
Servicios compartidos del sistema MeteoSerV3
"""
import logging

logger = logging.getLogger(__name__)


def get_system():
    """Obtiene instancia del sistema principal"""
    from main_asgi import system
    return system


def get_omnipotence_manager():
    """Obtiene gestor de omnipotencia"""
    from main_asgi import omnipotence_manager
    return omnipotence_manager


def get_assistant_brain():
    """Obtiene cerebro asistente"""
    from main_asgi import assistant_brain
    return assistant_brain


def get_auto_repair_engine():
    """Obtiene motor de auto-reparación"""
    from main_asgi import auto_repair_engine
    return auto_repair_engine


def get_habits_engine():
    """Obtiene motor de hábitos"""
    from main_asgi import habits_engine
    return habits_engine


def get_pas_engine():
    """Obtiene motor PAS"""
    from main_asgi import pas_engine
    return pas_engine


def validate_system():
    """Valida que el sistema esté inicializado"""
    system = get_system()
    if not system:
        raise RuntimeError("Sistema no inicializado")
    return system
