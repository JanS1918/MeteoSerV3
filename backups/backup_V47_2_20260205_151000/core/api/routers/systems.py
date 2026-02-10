"""
Router de sistemas auto-organizados
"""
from fastapi import APIRouter, Query
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


@router.get("/vanguard/alertas")
async def vanguard_alertas(offset: int = Query(0, ge=0), limit: int = Query(5, ge=1, le=20)):
    """Top alertas del ojeador semanal."""
    from main_asgi import system
    if system and hasattr(system, "ojeador"):
        return system.ojeador.get_top_alerts(offset, limit)
    return {"total": 0, "offset": offset, "limit": limit, "items": []}


@router.get("/vanguard/resumen")
async def vanguard_resumen():
    """Resumen del ojeador."""
    from main_asgi import system
    if system and hasattr(system, "ojeador"):
        return system.ojeador.resumen()
    return {"last_run": None, "total_alertas": 0}


@router.post("/feedback_prediccion")
async def prediction_feedback(datos: dict):
    """Feedback para predicciones"""
    from main_asgi import system
    
    if hasattr(system, 'registrar_feedback_prediccion'):
        system.registrar_feedback_prediccion(datos)
        return {"status": "OK"}
    return {"error": "Feedback no disponible"}
