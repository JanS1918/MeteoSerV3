"""
Router del asistente IA
"""
from fastapi import APIRouter, Body
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/asistente", tags=["assistant"])


@router.get("/estado")
async def get_assistant_state():
    """Estado del asistente"""
    from main_asgi import assistant_brain
    
    if assistant_brain and hasattr(assistant_brain, 'get_estado'):
        return assistant_brain.get_estado()
    return {"error": "Asistente no disponible"}


@router.post("/noticias")
async def add_news(titulo: str = Body(...), contenido: str = Body(...)):
    """Agrega noticia al asistente"""
    from main_asgi import assistant_brain
    
    if assistant_brain and hasattr(assistant_brain, 'agregar_noticia'):
        assistant_brain.agregar_noticia(titulo, contenido)
        return {"status": "OK"}
    return {"error": "Asistente no disponible"}


@router.post("/alarmas/ack")
async def acknowledge_alarm(alarma_id: str = Body(...)):
    """Reconoce una alarma"""
    from main_asgi import assistant_brain
    
    if assistant_brain and hasattr(assistant_brain, 'reconocer_alarma'):
        assistant_brain.reconocer_alarma(alarma_id)
        return {"status": "OK"}
    return {"error": "Asistente no disponible"}


@router.post("/alarmas/update")
async def update_alarm(
    alarma_id: str = Body(...),
    enabled: bool = Body(None),
    threshold: float = Body(None)
):
    """Actualiza configuración de alarma"""
    from main_asgi import assistant_brain
    
    if assistant_brain and hasattr(assistant_brain, 'actualizar_alarma'):
        assistant_brain.actualizar_alarma(alarma_id, enabled=enabled, threshold=threshold)
        return {"status": "OK"}
    return {"error": "Asistente no disponible"}


@router.post("/alarmas/toggle")
async def toggle_alarm(alarma_id: str = Body(...)):
    """Activa/desactiva alarma"""
    from main_asgi import assistant_brain
    
    if assistant_brain and hasattr(assistant_brain, 'toggle_alarma'):
        assistant_brain.toggle_alarma(alarma_id)
        return {"status": "OK"}
    return {"error": "Asistente no disponible"}


@router.get("/compra/sugerencias")
async def get_shopping_suggestions():
    """Sugerencias de compra del asistente"""
    from main_asgi import assistant_brain
    
    if assistant_brain and hasattr(assistant_brain, 'obtener_sugerencias_compra'):
        return {"sugerencias": assistant_brain.obtener_sugerencias_compra()}
    return {"sugerencias": []}


@router.post("/recomendaciones")
async def get_recommendations(contexto: dict = Body(...)):
    """Obtiene recomendaciones del asistente"""
    from main_asgi import assistant_brain
    
    if assistant_brain and hasattr(assistant_brain, 'generar_recomendaciones'):
        return {"recomendaciones": assistant_brain.generar_recomendaciones(contexto)}
    return {"recomendaciones": []}


@router.post("/comunicacion")
async def assistant_communication(mensaje: str = Body(...), canal: str = Body("usuario")):
    """Comunicación con el asistente"""
    from main_asgi import assistant_brain
    
    if assistant_brain and hasattr(assistant_brain, 'procesar_mensaje'):
        respuesta = assistant_brain.procesar_mensaje(mensaje, canal)
        return {"respuesta": respuesta}
    return {"error": "Asistente no disponible"}
