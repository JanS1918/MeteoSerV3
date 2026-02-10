"""
Router de sistemas auto-organizados
"""
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["systems"])


@router.get("/auto_reparacion")
async def auto_repair_status():
    """Estado del sistema de auto-reparación"""
    from main_asgi import auto_repair_engine
    
    if auto_repair_engine:
        return auto_repair_engine.get_status()
    return {"error": "Auto-reparación no disponible"}


@router.get("/auto_expansion")
async def auto_expansion_status():
    """Estado del sistema de auto-expansión"""
    from main_asgi import habits_engine
    
    if habits_engine:
        return habits_engine.get_status()
    return {"error": "Auto-expansión no disponible"}


@router.get("/pas")
async def pas_status():
    """Estado del sistema PAS"""
    from main_asgi import pas_engine
    
    if pas_engine:
        return pas_engine.get_status()
    return {"error": "PAS no disponible"}


@router.post("/feedback_prediccion")
async def prediction_feedback(datos: dict):
    """Feedback para predicciones"""
    from main_asgi import system
    
    if hasattr(system, 'registrar_feedback_prediccion'):
        system.registrar_feedback_prediccion(datos)
        return {"status": "OK"}
    return {"error": "Feedback no disponible"}
