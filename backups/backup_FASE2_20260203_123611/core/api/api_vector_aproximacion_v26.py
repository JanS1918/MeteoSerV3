import logging
"""
api_vector_aproximacion_v26.py
=================================
Endpoint de API para servir datos del Vector de Aproximación (#26)
Conecta brujula_tactica_v25.html con integracion_elite_motors_v25.py

Características:
- GET /api/vector-aproximacion: Obtiene estado actual
- WebSocket para actualización en tiempo real
- Fusión de los 3 componentes (Buys-Ballot, óptico, RSSI)
- Alerta dinámica según severidad
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse
import asyncio
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Router de FastAPI
router = APIRouter(prefix="/api", tags=["Vector Aproximación"])

# Estado global del vector (simulado, conectar con bus real)
estado_vector_actual = {
    "vector_aproximacion": {
        "direccion_grados": 0,
        "direccion_cardinal": "N",
        "distancia_km": 0,
        "eta_horas": 0,
        "velocidad_aproximacion_kmh": 0
    },
    "nivel_alerta": "✓ VERDE - Sin peligro inmediato",
    "confianza_prediccion": "MEDIA",
    "componentes": {
        "buys_ballot": {
            "tendencia_presion_hpa_h": 0,
            "severidad_buys_ballot": "--",
            "distancia_km_estimada": 0
        },
        "analisis_optico": {
            "transmitancia": 1.0,
            "tipo_evento": "--",
            "precision": "--"
        },
        "tracking_rayos": {
            "rayos_detectados": 0,
            "distancia_estimada_km": 0,
            "severidad_tormentosa": "--"
        }
    },
    "timestamp": datetime.now().isoformat()
}

# Manager de conexiones WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                logging.exception("Silent except at 71 - revisar contexto")

manager = ConnectionManager()


@router.get("/vector-aproximacion")
async def obtener_vector_aproximacion():
    """
    Endpoint GET para obtener estado actual del Vector de Aproximación
    
    Returns:
        {
            "vector_aproximacion": {
                "direccion_grados": float,
                "direccion_cardinal": str,
                "distancia_km": float,
                "eta_horas": float,
                "velocidad_aproximacion_kmh": float
            },
            "nivel_alerta": str,
            "confianza_prediccion": str,
            "componentes": {...},
            "timestamp": str
        }
    """
    return JSONResponse(content=estado_vector_actual)


@router.get("/vector-aproximacion/alerta")
async def obtener_alerta_nivel():
    """Obtiene solo el nivel de alerta actual"""
    return {
        "nivel": estado_vector_actual.get("nivel_alerta", "VERDE"),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/vector-aproximacion/prediccion")
async def obtener_prediccion_eta():
    """Obtiene predicción de ETA para la inclemencia"""
    vector = estado_vector_actual["vector_aproximacion"]
    return {
        "prediccion": f"Lluvia desde {vector.get('direccion_cardinal', 'desconocida')} "
                     f"a {vector.get('velocidad_aproximacion_kmh', 0):.0f} km/h, "
                     f"ETA: {vector.get('eta_horas', 0):.1f}h",
        "distancia_km": vector.get("distancia_km", 0),
        "eta_horas": vector.get("eta_horas", 0),
        "confianza": estado_vector_actual.get("confianza_prediccion", "MEDIA")
    }


@router.get("/vector-aproximacion/componentes")
async def obtener_componentes():
    """Obtiene detalles de los 3 componentes de fusión"""
    componentes = estado_vector_actual.get("componentes", {})
    return {
        "buys_ballot": componentes.get("buys_ballot", {}),
        "analisis_optico": componentes.get("analisis_optico", {}),
        "tracking_rayos": componentes.get("tracking_rayos", {}),
        "fusion_weights": {
            "buys_ballot": 0.5,
            "analisis_optico": 0.4,
            "tracking_rayos": 0.1
        }
    }


@router.post("/vector-aproximacion/actualizar")
async def actualizar_vector_aproximacion(datos: Dict[str, Any]):
    """
    Endpoint POST para actualizar estado del vector (desde integracion_elite_motors_v25.py)
    
    Args:
        datos: Diccionario con estructura del estado_vector_actual
    """
    global estado_vector_actual
    
    # Validar estructura mínima
    if "vector_aproximacion" in datos:
        estado_vector_actual.update(datos)
        estado_vector_actual["timestamp"] = datetime.now().isoformat()
        
        # Broadcast a todos los clientes WebSocket conectados
        await manager.broadcast(estado_vector_actual)
        
        return {"status": "actualizado", "timestamp": estado_vector_actual["timestamp"]}
    
    return JSONResponse(
        status_code=400,
        content={"error": "Estructura de datos inválida"}
    )


@router.websocket("/ws/vector-aproximacion")
async def websocket_vector_aproximacion(websocket: WebSocket):
    """
    WebSocket para actualización en tiempo real del vector de aproximación
    Los clientes se conectan y reciben actualizaciones automáticas
    """
    await manager.connect(websocket)
    
    # Enviar estado actual inmediatamente
    await websocket.send_json(estado_vector_actual)
    
    try:
        while True:
            # Mantener conexión abierta
            data = await websocket.receive_text()
            
            # Procesar comandos si es necesario
            if data == "refresh":
                await websocket.send_json(estado_vector_actual)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/brujula-tactica")
async def mostrar_brujula_tactica():
    """Endpoint para servir la página HTML de la brújula táctica"""
    with open("templates/brujula_tactica_v25.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@router.get("/vector-aproximacion/diagnostico")
async def diagnostico_vector():
    """Diagnóstico completo del vector de aproximación"""
    vector = estado_vector_actual["vector_aproximacion"]
    componentes = estado_vector_actual["componentes"]
    
    # Calcular scores de confianza por componente
    bb_score = 0.95 if componentes["buys_ballot"]["severidad_buys_ballot"] != "--" else 0
    op_score = 1.0 if componentes["analisis_optico"]["tipo_evento"] != "--" else 0
    ray_score = 0.9 if componentes["tracking_rayos"]["rayos_detectados"] > 0 else 0
    
    # Score general
    general_score = (bb_score * 0.5 + op_score * 0.4 + ray_score * 0.1)
    
    return {
        "diagnóstico": {
            "general_score": f"{general_score:.2%}",
            "componentes_activos": sum([
                bb_score > 0,
                op_score > 0,
                ray_score > 0
            ]),
            "máx_componentes": 3,
            "confianza_general": estado_vector_actual.get("confianza_prediccion", "DESCONOCIDA"),
            "nivel_alerta": estado_vector_actual.get("nivel_alerta", "DESCONOCIDA").split(" ")[1] if " " in estado_vector_actual.get("nivel_alerta", "") else "DESCONOCIDA"
        },
        "vector_estimado": {
            "distancia": f"{vector.get('distancia_km', 0):.1f} km",
            "velocidad": f"{vector.get('velocidad_aproximacion_kmh', 0):.1f} km/h",
            "eta": f"{vector.get('eta_horas', 0):.1f} horas",
            "dirección": vector.get("direccion_cardinal", "desconocida")
        },
        "timestamp": estado_vector_actual["timestamp"]
    }


# Función para inicializar la API
def init_vector_api(app):
    """Registrar rutas en aplicación FastAPI"""
    app.include_router(router)
    print("✓ API Vector de Aproximación V2.6 inicializada")


# Funciones de utilidad para actualizar desde motores de élite
async def publicar_actualizacion_vector(datos_vector: Dict[str, Any]):
    """
    Publica actualización del vector desde integracion_elite_motors_v25.py
    
    Args:
        datos_vector: Datos completos del vector con sus 3 componentes
    """
    global estado_vector_actual
    estado_vector_actual = datos_vector
    await manager.broadcast(estado_vector_actual)


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="Vector Aproximación V2.6")
    init_vector_api(app)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
