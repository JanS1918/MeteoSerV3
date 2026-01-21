from fastapi import APIRouter
from core.system.singleton import get_manager, get_system

router = APIRouter()
manager = get_manager()
system = get_system()

@router.get("/estado")
def obtener_estado():
    return system.obtener_estado_completo()
