from fastapi import APIRouter
from core.system.system_manager import SystemManager

router = APIRouter()
manager = SystemManager()
system = manager.iniciar()


@router.get("/estado")
def obtener_estado():
    return system.obtener_estado_completo()
