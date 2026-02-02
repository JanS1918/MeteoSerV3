# Endpoints y API para la nueva UI
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import traceback
import logging

from core.fiabilidad_manager import FiabilidadManager
from core.feedback_manager import FeedbackManager
from core.auditoria_manager import AuditoriaManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ui", tags=["ui"])

# Inicialización de managers
fiabilidad_mgr = FiabilidadManager()
feedback_mgr = FeedbackManager()
auditoria_mgr = AuditoriaManager()

# Modelos Pydantic para request/response
class FeedbackRequest(BaseModel):
    nombre_indice: str
    valor_predicho: float
    valor_real: float
    es_correcto: bool
    comentario: Optional[str] = None

class MovimientoRequest(BaseModel):
    valor: str
    origen: str
    destino: str
    usuario: Optional[str] = 'usuario'

class EdicionRequest(BaseModel):
    entidad: str
    campo: str
    valor_anterior: Any
    valor_nuevo: Any
    usuario: Optional[str] = 'usuario'

class CerrarAlertaRequest(BaseModel):
    nombre_sensor: str

class RestaurarRequest(BaseModel):
    numero_movimientos: int

# ============================================================
# ENDPOINTS UI - PANEL 2026 (CAJONES Y SUBMENÚ)
# ============================================================

@router.get("/cajones")
def obtener_cajones_ui() -> Dict[str, Any]:
    """
    Compatibilidad UI: cajones para Panel 2026.
    Endpoint simplificado que siempre devuelve JSON válido.
    """
    try:
        # Importar aquí para evitar circular imports
        from app.ui.router import obtener_contexto_sistema, obtener_cajones_cacheados
        
        contexto = obtener_contexto_sistema()
        if contexto and (contexto.get('sensores') or contexto.get('indices')):
            cajones = obtener_cajones_cacheados()
            cajones = _normalizar_cajones(cajones)
            return {"cajones": cajones, "total": len(cajones)}
        else:
            # Sin datos disponibles - devolver estructura vacía
            return {"cajones": [], "total": 0}
            
    except Exception as e:
        logger.error(f"[API CAJONES] Error: {str(e)}\n{traceback.format_exc()}")
        # SIEMPRE devolver JSON válido, NUNCA HTML de error
        return {"cajones": [], "total": 0}


def _normalizar_cajones(cajones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalizados: List[Dict[str, Any]] = []
    for cajon in cajones or []:
        valores_tapa = cajon.get("valores_tapa") or []
        valores_completos = cajon.get("valores_completos") or []

        def _normalizar_valor(valor: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "nombre": valor.get("nombre") or "",
                "valor": 0.0 if valor.get("valor") is None else valor.get("valor"),
                "unidad": valor.get("unidad") or "",
                "icono": valor.get("icono") or ""
            }

        normalizados.append({
            "id": cajon.get("id") or "",
            "nombre": cajon.get("nombre") or "",
            "icono": cajon.get("icono") or "",
            "prioridad": cajon.get("prioridad") or 0,
            "valores_tapa": [_normalizar_valor(v) for v in valores_tapa],
            "valores_completos": [_normalizar_valor(v) for v in valores_completos],
            "total_valores": cajon.get("total_valores") or len(valores_completos)
        })
    return normalizados


@router.get("/submenu/{nombre_valor}")
def obtener_submenu_ui(nombre_valor: str) -> Dict[str, Any]:
    """Compatibilidad UI: submenu para Panel 2026."""
    try:
        from app.ui.router import obtener_contexto_sistema, generar_grupos_desde_sistema, panel_vm
        
        contexto = obtener_contexto_sistema()
        if not contexto:
            return {"error": "Contexto no disponible", "nombre": nombre_valor}
        
        if not panel_vm.jerarquia:
            grupos = generar_grupos_desde_sistema(contexto)
            panel_vm.inicializar_jerarquia(grupos)
        
        return panel_vm.obtener_submenu_valor(nombre_valor, contexto)
    except Exception as e:
        logger.error(f"[API SUBMENU] Error: {str(e)}\n{traceback.format_exc()}")
        return {"error": f"Error cargando submenu", "nombre": nombre_valor}

# ============================================================
# ENDPOINTS DE FIABILIDAD Y ALERTAS
# ============================================================

@router.get("/fiabilidad/estado")
def obtener_estado_fiabilidad() -> Dict[str, Any]:
    """
    Obtiene el estado completo del sistema de fiabilidad.
    
    **Response:**
    ```json
    {
        "sensores": {
            "temperatura_interior": {
                "nombre": "temperatura_interior",
                "tipo": "sensor",
                "fiabilidad": "alta",
                "ultima_lectura": 21.5,
                "contador_errores": 0,
                "timestamp": "2026-01-30T10:30:00"
            }
        },
        "alertas_activas": [
            {
                "nombre": "sensor_viento",
                "mensaje": "Error de lectura",
                "gravedad": "media",
                "timestamp": "2026-01-30T10:25:00"
            }
        ],
        "total_sensores": 15,
        "total_alertas": 1
    }
    ```
    """
    return fiabilidad_mgr.obtener_estado_completo()

@router.get("/fiabilidad/alertas")
def obtener_alertas_activas() -> Dict[str, Any]:
    """
    Obtiene todas las alertas activas del sistema.
    
    **Response:**
    ```json
    {
        "alertas": [
            {
                "nombre": "sensor_viento",
                "mensaje": "Error de lectura",
                "gravedad": "media",
                "timestamp": "2026-01-30T10:25:00",
                "resuelta": false
            }
        ],
        "total": 1
    }
    ```
    """
    alertas = fiabilidad_mgr.obtener_alertas_activas()
    return {"alertas": alertas, "total": len(alertas)}

@router.post("/fiabilidad/cerrar_alerta")
def cerrar_alerta(request: CerrarAlertaRequest) -> Dict[str, Any]:
    """
    Cierra manualmente una alerta activa.
    
    **Request:**
    ```json
    {
        "nombre_sensor": "sensor_viento"
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "mensaje": "Alerta cerrada correctamente"
    }
    ```
    """
    exito = fiabilidad_mgr.cerrar_alerta_manual(request.nombre_sensor)
    if exito:
        auditoria_mgr.registrar_alerta_log(
            sensor=request.nombre_sensor,
            alerta={'accion': 'cerrada_manual'},
            usuario='usuario'
        )
        return {"success": True, "mensaje": "Alerta cerrada correctamente"}
    else:
        return {"success": False, "mensaje": "Alerta no encontrada"}

# ============================================================
# ENDPOINTS DE FEEDBACK
# ============================================================

@router.post("/feedback/registrar")
def registrar_feedback(request: FeedbackRequest) -> Dict[str, Any]:
    """
    Registra feedback del usuario sobre una predicción o índice.
    
    **Request:**
    ```json
    {
        "nombre_indice": "temperatura_maxima",
        "valor_predicho": 25.0,
        "valor_real": 23.5,
        "es_correcto": false,
        "comentario": "La predicción fue demasiado alta"
    }
    ```
    
    **Response:**
    ```json
    {
        "nombre_indice": "temperatura_maxima",
        "error": 1.5,
        "error_relativo": 0.064,
        "confianza_nueva": 0.72,
        "timestamp": "2026-01-30T10:30:00"
    }
    ```
    """
    registro = feedback_mgr.registrar_feedback(
        nombre_indice=request.nombre_indice,
        valor_predicho=request.valor_predicho,
        valor_real=request.valor_real,
        es_correcto=request.es_correcto,
        comentario=request.comentario
    )
    
    auditoria_mgr.registrar_feedback_log(
        indice=request.nombre_indice,
        detalles=registro,
        usuario='usuario'
    )
    
    return registro

@router.get("/feedback/estadisticas")
def obtener_estadisticas_feedback(nombre_indice: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene estadísticas de feedback.
    
    **Query params:**
    - nombre_indice (opcional): Filtrar por índice específico
    
    **Response:**
    ```json
    {
        "total": 50,
        "correctos": 38,
        "incorrectos": 12,
        "precision": 0.76,
        "confianza_actual": 0.82
    }
    ```
    """
    return feedback_mgr.obtener_estadisticas(nombre_indice)

@router.get("/feedback/reciente")
def obtener_feedback_reciente(limite: int = 20) -> Dict[str, Any]:
    """
    Obtiene los registros de feedback más recientes.
    
    **Query params:**
    - limite: Número de registros a devolver (default: 20)
    
    **Response:**
    ```json
    {
        "feedback": [
            {
                "nombre_indice": "temperatura_maxima",
                "valor_predicho": 25.0,
                "valor_real": 23.5,
                "error": 1.5,
                "es_correcto": false,
                "timestamp": "2026-01-30T10:30:00"
            }
        ],
        "total": 20
    }
    ```
    """
    feedback = feedback_mgr.obtener_feedback_reciente(limite)
    return {"feedback": feedback, "total": len(feedback)}

# ============================================================
# ENDPOINTS DE AUDITORÍA Y MOVIMIENTOS
# ============================================================

@router.post("/auditoria/movimiento")
def registrar_movimiento(request: MovimientoRequest) -> Dict[str, Any]:
    """
    Registra el movimiento de un valor entre cajones.
    
    **Request:**
    ```json
    {
        "valor": "temperatura_exterior",
        "origen": "cajon_temperatura",
        "destino": "cajon_meteorologico",
        "usuario": "usuario"
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "mensaje": "Movimiento registrado correctamente"
    }
    ```
    """
    auditoria_mgr.registrar_movimiento(
        valor=request.valor,
        origen=request.origen,
        destino=request.destino,
        usuario=request.usuario
    )
    return {"success": True, "mensaje": "Movimiento registrado correctamente"}

@router.post("/auditoria/edicion")
def registrar_edicion(request: EdicionRequest) -> Dict[str, Any]:
    """
    Registra la edición de un nombre o valor.
    
    **Request:**
    ```json
    {
        "entidad": "cajon_temperatura",
        "campo": "nombre",
        "valor_anterior": "Temperatura",
        "valor_nuevo": "Temperatura & Clima",
        "usuario": "usuario"
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "mensaje": "Edición registrada correctamente"
    }
    ```
    """
    auditoria_mgr.registrar_edicion(
        entidad=request.entidad,
        campo=request.campo,
        valor_anterior=request.valor_anterior,
        valor_nuevo=request.valor_nuevo,
        usuario=request.usuario
    )
    return {"success": True, "mensaje": "Edición registrada correctamente"}

@router.post("/auditoria/restaurar")
def restaurar_movimientos(request: RestaurarRequest) -> Dict[str, Any]:
    """
    Restaura los últimos N movimientos realizados.
    
    **Request:**
    ```json
    {
        "numero_movimientos": 5
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "acciones": [
            {
                "valor": "temperatura_exterior",
                "origen": "cajon_meteorologico",
                "destino": "cajon_temperatura",
                "timestamp_original": "2026-01-30T10:25:00"
            }
        ],
        "total_restaurados": 5
    }
    ```
    """
    acciones = auditoria_mgr.restaurar_movimientos(request.numero_movimientos)
    return {
        "success": True,
        "acciones": acciones,
        "total_restaurados": len(acciones)
    }

@router.get("/auditoria/historial")
def obtener_historial(tipo: Optional[str] = None, entidad: Optional[str] = None, limite: int = 100) -> Dict[str, Any]:
    """
    Obtiene el historial de cambios filtrado.
    
    **Query params:**
    - tipo: Filtrar por tipo de cambio (movimiento, edicion, configuracion, feedback, alerta)
    - entidad: Filtrar por entidad específica
    - limite: Número de registros a devolver
    
    **Response:**
    ```json
    {
        "historial": [
            {
                "tipo": "movimiento",
                "entidad": "temperatura_exterior",
                "cambio": {"origen": "cajon_temperatura", "destino": "cajon_meteorologico"},
                "usuario": "usuario",
                "timestamp": "2026-01-30T10:25:00"
            }
        ],
        "total": 100
    }
    ```
    """
    historial = auditoria_mgr.obtener_historial(tipo, entidad, limite)
    return {"historial": historial, "total": len(historial)}

@router.get("/auditoria/estadisticas")
def obtener_estadisticas_auditoria() -> Dict[str, Any]:
    """
    Obtiene estadísticas de auditoría.
    
    **Response:**
    ```json
    {
        "total_cambios": 250,
        "por_tipo": {
            "movimiento": 120,
            "edicion": 80,
            "feedback": 40,
            "alerta": 10
        },
        "ultimo_cambio": {
            "tipo": "movimiento",
            "timestamp": "2026-01-30T10:30:00"
        }
    }
    ```
    """
    return auditoria_mgr.obtener_estadisticas()
