"""
Router de administración
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check del sistema"""
    return {"status": "OK", "service": "meteoser_v3"}


@router.post("/brain/force_save")
async def force_brain_save():
    """Fuerza guardado del cerebro estadístico"""
    from main_asgi import system
    
    try:
        if hasattr(system, 'statistical_brain') and system.statistical_brain:
            system.statistical_brain.save()
            return {"status": "OK", "mensaje": "Cerebro guardado"}
        return {"error": "Cerebro no disponible"}
    except Exception as e:
        logger.error(f"Error guardando cerebro: {e}")
        return {"error": str(e)}


@router.get("/brain/status")
async def brain_status():
    """Estado del cerebro estadístico"""
    from main_asgi import system
    
    try:
        if hasattr(system, 'statistical_brain') and system.statistical_brain:
            brain = system.statistical_brain
            return {
                "activo": True,
                "observaciones": len(brain.observations) if hasattr(brain, 'observations') else 0,
                "modelos": list(brain.models.keys()) if hasattr(brain, 'models') else [],
                "ultimo_entrenamiento": getattr(brain, 'last_training', None)
            }
        return {"activo": False}
    except Exception as e:
        logger.error(f"Error obteniendo estado del cerebro: {e}")
        return {"error": str(e)}


@router.get("/omnipotencia/status")
async def omnipotence_status():
    """Estado del sistema de descubrimiento universal"""
    from main_asgi import omnipotence_manager
    
    if not omnipotence_manager:
        return {"error": "Omnipotencia no disponible"}
    return omnipotence_manager.get_status()


@router.get("/omnipotencia/dispositivos")
async def omnipotence_devices():
    """Dispositivos detectados por omnipotencia"""
    from main_asgi import omnipotence_manager
    
    if not omnipotence_manager:
        return {"error": "Omnipotencia no disponible", "dispositivos": []}
    
    devices = omnipotence_manager.scanner.get_devices()
    return {
        "total": len(devices),
        "dispositivos": [
            {
                "id": d.id,
                "nombre": d.name,
                "tipo": d.type,
                "direccion": d.address,
                "detectado": d.detected_at.isoformat(),
                "metadata": d.metadata
            }
            for d in devices
        ]
    }
