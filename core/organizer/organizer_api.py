from fastapi import APIRouter, HTTPException
from core.organizer.organizer_model import (
    crear_elemento,
    obtener_elemento,
    listar_elementos,
    actualizar_elemento,
    borrar_elemento,
    ElementoTipo,
)
from core.engines.communication_engine import CommunicationEngine
from typing import List, Optional, Dict, Any


router = APIRouter()
comm_engine = CommunicationEngine()


@router.post("/elementos", response_model=Dict[str, Any])
def crear(data: Dict[str, Any]):
    elem = crear_elemento(data)
    # Si es un recordatorio pendiente, avisar por voz
    if elem.tipo == ElementoTipo.RECORDATORIO and elem.estado == "pendiente":
        comm_engine.responder(
            f"Tienes un nuevo recordatorio: {elem.titulo}",
            {"recordatorio": elem.to_dict()},
        )
    return elem.to_dict()


@router.get("/elementos", response_model=List[Dict[str, Any]])
def listar(tipo: Optional[str] = None):
    return listar_elementos(tipo)


@router.get("/elementos/{eid}", response_model=Dict[str, Any])
def obtener(eid: str):
    elem = obtener_elemento(eid)
    if not elem:
        raise HTTPException(status_code=404, detail="Elemento no encontrado")
    return elem.to_dict()


@router.put("/elementos/{eid}", response_model=Dict[str, Any])
def actualizar(eid: str, data: Dict[str, Any]):
    elem = actualizar_elemento(eid, data)
    if not elem:
        raise HTTPException(status_code=404, detail="Elemento no encontrado")
    # Si es un recordatorio pendiente, avisar por voz
    if elem.tipo == ElementoTipo.RECORDATORIO and elem.estado == "pendiente":
        comm_engine.responder(
            f"Tienes un recordatorio actualizado: {elem.titulo}",
            {"recordatorio": elem.to_dict()},
        )
    return elem.to_dict()


@router.delete("/elementos/{eid}")
def borrar(eid: str):
    ok = borrar_elemento(eid)
    if not ok:
        raise HTTPException(status_code=404, detail="Elemento no encontrado")
    return {"ok": True}
