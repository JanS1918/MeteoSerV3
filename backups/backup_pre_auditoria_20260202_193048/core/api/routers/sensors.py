"""
Router de sensores y datos
"""
from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sensores", tags=["sensors"])


@router.get("/historial")
async def get_sensor_history():
    """Historial de sensores"""
    from main_asgi import system
    if not system or not hasattr(system, 'sensores'):
        return {"error": "Sistema no inicializado"}
    
    historial_data = {}
    if hasattr(system, 'historial_sensores'):
        for nombre_sensor, valores in system.historial_sensores.items():
            historial_data[nombre_sensor] = [
                {"timestamp": ts.isoformat(), "valor": v}
                for ts, v in valores
            ]
    
    return {
        "historial": historial_data,
        "sensores_actuales": system.sensores
    }


@router.post("/sensor_virtual")
async def create_virtual_sensor(
    nombre: str = Body(...),
    formula: str = Body(...),
    unidad: str = Body("unidad"),
    descripcion: str = Body("")
):
    """Crea un sensor virtual con fórmula"""
    from main_asgi import system
    
    try:
        if hasattr(system, 'agregar_sensor_virtual'):
            system.agregar_sensor_virtual(nombre, formula, unidad, descripcion)
            return {"status": "OK", "mensaje": f"Sensor virtual '{nombre}' creado"}
        else:
            return {"error": "Sistema no soporta sensores virtuales"}
    except Exception as e:
        logger.error(f"Error creando sensor virtual: {e}")
        return {"error": str(e)}
