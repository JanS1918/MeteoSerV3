"""
ai_endpoints.py - Endpoints de IA para FastAPI
===============================================

Expone funcionalidad de IA vía API REST.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Router de FastAPI
router = APIRouter(prefix="/ai", tags=["AI"])


class DialogMessage(BaseModel):
    """Modelo para mensajes de diálogo"""
    session_id: Optional[str] = None
    message: str


class ExplainRequest(BaseModel):
    """Modelo para solicitudes de explicación"""
    query: str


class GenerateCodeRequest(BaseModel):
    """Modelo para generación de código"""
    prompt: str
    context: Optional[Dict[str, Any]] = None


@router.get("/status")
async def get_ai_status():
    """
    Obtiene el estado completo del sistema de IA.
    
    Returns:
        Estado de todos los subsistemas
    """
    from ai_controller import get_ai_controller
    
    controller = get_ai_controller()
    
    if not controller:
        raise HTTPException(status_code=503, detail="AI Controller not initialized")
    
    try:
        status = controller.get_status()
        return status
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dialog")
async def process_dialog(data: DialogMessage):
    """
    Procesa un mensaje de diálogo con la IA.
    
    Args:
        data: Mensaje del usuario y session_id opcional
    
    Returns:
        Respuesta de la IA con intención detectada
    """
    from ai_controller import get_ai_controller
    
    controller = get_ai_controller()
    
    if not controller or not controller.dialog:
        raise HTTPException(status_code=503, detail="Dialog Manager not initialized")
    
    try:
        # Crear sesión si no existe
        session_id = data.session_id
        if not session_id:
            session_id = controller.dialog.create_session()
        
        response = controller.dialog.process_message(session_id, data.message)
        
        return response
    
    except Exception as e:
        logger.error(f"❌ Error en diálogo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain")
async def explain(data: ExplainRequest):
    """
    Genera una explicación sobre cualquier concepto de MeteoSer.
    
    Args:
        data: Query a explicar
    
    Returns:
        Explicación en lenguaje natural
    """
    from ai_controller import get_ai_controller
    
    controller = get_ai_controller()
    
    if not controller or not controller.explainer:
        raise HTTPException(status_code=503, detail="Explainer not initialized")
    
    try:
        explanation = controller.explainer.explain(data.query, controller.bus)
        
        return {
            "query": data.query,
            "explanation": explanation
        }
    
    except Exception as e:
        logger.error(f"❌ Error generando explicación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts")
async def list_contracts():
    """
    Lista todos los contratos de componentes registrados.
    
    Returns:
        Lista de contratos
    """
    from ai_controller import get_ai_controller
    
    controller = get_ai_controller()
    
    if not controller or not controller.knowledge:
        raise HTTPException(status_code=503, detail="Knowledge Manager not initialized")
    
    try:
        contracts = controller.knowledge.list_contracts()
        
        return {
            "count": len(contracts),
            "contracts": contracts
        }
    
    except Exception as e:
        logger.error(f"❌ Error listando contratos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str):
    """
    Obtiene un contrato específico por ID.
    
    Args:
        contract_id: ID del contrato
    
    Returns:
        Contrato completo
    """
    from ai_controller import get_ai_controller
    
    controller = get_ai_controller()
    
    if not controller or not controller.knowledge:
        raise HTTPException(status_code=503, detail="Knowledge Manager not initialized")
    
    try:
        contract = controller.knowledge.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
        
        return contract
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo contrato: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_code(data: GenerateCodeRequest):
    """
    Genera código usando IA.
    
    Args:
        data: Prompt y contexto opcional
    
    Returns:
        Código generado y validación
    """
    from ai_controller import get_ai_controller
    
    controller = get_ai_controller()
    
    if not controller or not controller.codegen:
        raise HTTPException(status_code=503, detail="Code Generator not initialized")
    
    try:
        # Generar código
        code = controller.codegen.generate_code(data.prompt, context=data.context)
        
        # Validar sintaxis
        is_valid, error = controller.codegen.validate_syntax(code)
        
        return {
            "prompt": data.prompt,
            "code": code,
            "valid": is_valid,
            "error": error if not is_valid else None
        }
    
    except Exception as e:
        logger.error(f"❌ Error generando código: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/autoheal/scan")
async def trigger_autoheal_scan():
    """
    Dispara un escaneo de auto-curación.
    
    Returns:
        Problemas detectados
    """
    from ai_controller import get_ai_controller
    
    controller = get_ai_controller()
    
    if not controller:
        raise HTTPException(status_code=503, detail="AI Controller not initialized")
    
    try:
        task_id = controller.schedule_autoheal_scan()
        
        return {
            "task_id": task_id,
            "message": "Autoheal scan scheduled"
        }
    
    except Exception as e:
        logger.error(f"❌ Error programando scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics():
    """
    Obtiene métricas del orchestrator.
    
    Returns:
        Métricas de ejecución
    """
    from ai_controller import get_ai_controller
    
    controller = get_ai_controller()
    
    if not controller or not controller.orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        metrics = controller.orchestrator.get_metrics()
        
        return metrics
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(limit: int = 100):
    """
    Obtiene historial de cambios.
    
    Args:
        limit: Número máximo de entradas
    
    Returns:
        Historial
    """
    from ai_controller import get_ai_controller
    
    controller = get_ai_controller()
    
    if not controller or not controller.knowledge:
        raise HTTPException(status_code=503, detail="Knowledge Manager not initialized")
    
    try:
        history = controller.knowledge.get_history(limit=limit)
        
        return {
            "count": len(history),
            "history": history
        }
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo historial: {e}")
        raise HTTPException(status_code=500, detail=str(e))
