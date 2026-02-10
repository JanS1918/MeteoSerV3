"""
Router de voz
"""
from fastapi import APIRouter, Body
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voz", tags=["voice"])


@router.post("/sesion")
async def create_voice_session(parametros: dict = Body(...)):
    """Crea sesión de voz"""
    from main_asgi import assistant_brain
    
    if assistant_brain and hasattr(assistant_brain, 'crear_sesion_voz'):
        sesion_id = assistant_brain.crear_sesion_voz(parametros)
        return {"status": "OK", "sesion_id": sesion_id}
    return {"error": "Asistente de voz no disponible"}


@router.post("/texto")
async def text_to_speech(texto: str = Body(...), sesion_id: str = Body(None)):
    """Convierte texto a voz"""
    from main_asgi import assistant_brain
    
    try:
        if assistant_brain and hasattr(assistant_brain, 'texto_a_voz'):
            resultado = assistant_brain.texto_a_voz(texto, sesion_id)
            return {"status": "OK", "resultado": resultado}
        return {"error": "TTS no disponible"}
    except Exception as e:
        logger.error(f"Error en TTS: {e}")
        return {"error": str(e)}
