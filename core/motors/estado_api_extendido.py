from fastapi import APIRouter
from core.system.system_manager import SystemManager
from core.meteo.meteo_engine import get_full_meteo_snapshot

router = APIRouter()
manager = SystemManager()
system = manager.iniciar()

@router.get("/estado")
def obtener_estado():
    # Estado clásico
    estado = system.obtener_estado_completo()
    # Añadir snapshot meteorológico completo (sensores normalizados y métricas derivadas)
    try:
        snapshot = get_full_meteo_snapshot(system)
        estado["meteo"] = snapshot
    except Exception as e:
        estado["meteo"] = {"error": str(e)}
    return estado
