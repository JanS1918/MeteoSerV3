from fastapi import APIRouter
from core.system.system_manager import SystemManager
from core.motors.ambiental_motor import MotorAmbiental
from core.motors.confort_motor import MotorConfort
from core.motors.edificio_motor import MotorEdificio
from core.motors.meteorologico_motor import MotorMeteorologico
from core.motors.recomendaciones_motor import MotorRecomendaciones
from core.motors.automejora_motor import MotorAutoMejora
from core.motors.submenu_motor import MotorSubmenu
from core.motors.impresion_motor import MotorImpresion
from core.motors.calendario_motor import MotorCalendario
from core.motors.tareas_motor import MotorTareas
from core.motors.lista_compra_motor import MotorListaCompra
from core.motors.eventos_motor import MotorEventos
from core.motors.alarmas_motor import MotorAlarmas
from core.motors.comunicacion_motor import MotorComunicacion
from core.motors.huellas_motor import GestorHuellasAtmosfericas

router = APIRouter()
manager = SystemManager()
system = manager.iniciar()

@router.post("/motor/ambiental")
def motor_ambiental(datos: dict):
    payload = datos or {"sensores": system.sensores, "indices": system.indices.obtener_todos()}
    return MotorAmbiental().analizar(payload)

@router.post("/motor/confort")
def motor_confort(datos: dict):
    payload = datos or {"sensores": system.sensores, "indices": system.indices.obtener_todos()}
    return MotorConfort().calcular_indice(payload)

@router.post("/motor/edificio")
def motor_edificio(datos: dict):
    payload = datos or {"sensores": system.sensores, "indices": system.indices.obtener_todos()}
    return MotorEdificio().diagnosticar(payload)

@router.post("/motor/meteorologico")
def motor_meteorologico(datos: dict):
    payload = datos or {"sensores": system.sensores, "indices": system.indices.obtener_todos()}
    return MotorMeteorologico().calcular_indices(payload)

@router.post("/motor/recomendaciones")
def motor_recomendaciones(datos: dict):
    payload = datos or {"recomendacion": system.obtener_recomendacion()}
    return MotorRecomendaciones().generar_aviso(payload)

@router.post("/motor/automejora")
def motor_automejora(datos: dict):
    return MotorAutoMejora().mejorar(datos)

@router.post("/motor/submenu")
def motor_submenu(datos: dict):
    payload = datos or {
        "sensores": system.sensores,
        "indices": system.indices.obtener_todos(),
        "predicciones": {},
        "auto_mejora": system.auto_improvement_engine.reporte() if system.auto_improvement_engine else {},
    }
    return MotorSubmenu().obtener_detalle(payload)

@router.post("/motor/impresion")
def motor_impresion(datos: dict):
    payload = datos or {"cola_impresion": []}
    return MotorImpresion().imprimir(payload)

@router.post("/motor/calendario")
def motor_calendario(datos: dict):
    payload = datos or {"calendario": []}
    return MotorCalendario().gestionar(payload)

@router.post("/motor/tareas")
def motor_tareas(datos: dict):
    payload = datos or {"tareas": []}
    return MotorTareas().gestionar(payload)

@router.post("/motor/lista_compra")
def motor_lista_compra(datos: dict):
    payload = datos or {"lista_compra": []}
    return MotorListaCompra().gestionar(payload)

@router.post("/motor/eventos")
def motor_eventos(datos: dict):
    payload = datos or {"eventos": []}
    return MotorEventos().consultar(payload)

@router.post("/motor/alarmas")
def motor_alarmas(datos: dict):
    payload = datos or {"alarmas": []}
    return MotorAlarmas().gestionar(payload)

@router.post("/motor/comunicacion")
def motor_comunicacion(datos: dict):
    texto = datos.get("texto", "")
    return MotorComunicacion().responder(texto, datos)

@router.post("/motor/huellas")
def motor_huellas(datos: dict):
    return GestorHuellasAtmosfericas().analizar(datos)
