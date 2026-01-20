from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ElementoTipo(str, Enum):
    TAREA = "tarea"
    EVENTO = "evento"
    RECORDATORIO = "recordatorio"
    ALARMA = "alarma"
    LISTA = "lista"
    COMPRA = "compra"


class ElementoOrganizativo:
    def __init__(
        self,
        id: str,
        tipo: ElementoTipo,
        titulo: str,
        descripcion: Optional[str] = None,
        categoria: Optional[str] = None,
        prioridad: Optional[int] = 0,
        estado: Optional[str] = "pendiente",
        fecha: Optional[datetime] = None,
        recurrencia: Optional[str] = None,
        notas: Optional[str] = None,
        historial: Optional[List[Dict[str, Any]]] = None,
        datos_extra: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.tipo = tipo
        self.titulo = titulo
        self.descripcion = descripcion
        self.categoria = categoria
        self.prioridad = prioridad
        self.estado = estado
        self.fecha = fecha
        self.recurrencia = recurrencia
        self.notas = notas
        self.historial = historial or []
        self.datos_extra = datos_extra or {}

    def to_dict(self):
        return self.__dict__


# Almacenamiento en memoria (puede migrar a persistente)
ELEMENTOS: Dict[str, ElementoOrganizativo] = {}

# Utilidades CRUD


def crear_elemento(data: Dict[str, Any]) -> ElementoOrganizativo:
    eid = data.get("id") or f"el-{int(datetime.now().timestamp() * 1000)}"
    elem = ElementoOrganizativo(id=eid, **data)
    ELEMENTOS[eid] = elem
    return elem


def obtener_elemento(eid: str) -> Optional[ElementoOrganizativo]:
    return ELEMENTOS.get(eid)


def listar_elementos(tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    if tipo:
        return [e.to_dict() for e in ELEMENTOS.values() if e.tipo == tipo]
    return [e.to_dict() for e in ELEMENTOS.values()]


def actualizar_elemento(
    eid: str, data: Dict[str, Any]
) -> Optional[ElementoOrganizativo]:
    elem = ELEMENTOS.get(eid)
    if not elem:
        return None
    for k, v in data.items():
        setattr(elem, k, v)
    return elem


def borrar_elemento(eid: str) -> bool:
    return ELEMENTOS.pop(eid, None) is not None
