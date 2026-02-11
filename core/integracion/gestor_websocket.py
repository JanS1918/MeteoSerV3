"""
═══════════════════════════════════════════════════════════════════════════════
STEP 12: WEBSOCKET LIVE UPDATES
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Reemplazo de polling 30s → push en vivo
  - Reducir latencia y carga de servidor
  - Auto-reconnect con exponential backoff
  - Multiplexado por canal de suscripción

Fecha de creación: 2026-02-11
Versión: 1.0
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Set, Callable, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════
# MODELOS
# ═══════════════════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)


class CanalSuscripcion:
    """Canales disponibles para WebSocket."""
    ALERTAS_EN_VIVO = "alertas.vivo"
    SALUD_SISTEMA = "salud.sistema"
    AUDITORIA_POST_CICLO = "auditoria.post_ciclo"
    VALIDACION_WH31 = "validacion.wh31"
    ESTADO_SERVICIOS = "estado.servicios"
    TODAS = "todas"  # Suscribirse a todos


@dataclass
class MensajeWebSocket:
    """Mensaje WebSocket standarizado."""
    tipo: str  # 'update', 'subscribe', 'unsubscribe', 'ping', 'pong'
    canal: str
    payload: Dict[str, Any]
    timestamp: str = ""
    cliente_id: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), default=str)


# ═══════════════════════════════════════════════════════════════════════════
# GESTOR DE SUBSCRIPCIONES WEBSOCKET
# ═══════════════════════════════════════════════════════════════════════════

class GestorWebSocket:
    """Gestiona subscripciones y broadcasting de WebSocket."""
    
    def __init__(self):
        # Por cada canal, conjunto de websockets suscritos
        self.suscriptores: Dict[str, Set[Any]] = defaultdict(set)
        self.clientes_canales: Dict[str, Set[str]] = defaultdict(set)
        self.buffer_ultimos_mensajes = defaultdict(list)
    
    def registrar_cliente(self, websocket: Any, cliente_id: str, 
                         canales: list):
        """Registra cliente nuevo con sus canales."""
        for canal in canales:
            self.suscriptores[canal].add(websocket)
            self.clientes_canales[cliente_id].add(canal)
        
        logger.info(
            f"Cliente {cliente_id} registrado en "
            f"{len(canales)} canales"
        )
    
    def desregistrar_cliente(self, cliente_id: str):
        """Desregistra cliente de todos sus canales."""
        canales = self.clientes_canales.get(cliente_id, set())
        
        for canal in canales:
            websockets = [
                ws for ws in self.suscriptores[canal]
                if hasattr(ws, '_cliente_id') and 
                   ws._cliente_id == cliente_id
            ]
            for ws in websockets:
                self.suscriptores[canal].discard(ws)
        
        del self.clientes_canales[cliente_id]
        logger.info(f"Cliente {cliente_id} desregistrado")
    
    async def publicar_en_canal(self, canal: str, 
                               mensaje: MensajeWebSocket):
        """Publica mensaje a todos los clientes del canal."""
        
        if not self.suscriptores.get(canal):
            return False
        
        # Guardar en buffer para nuevos clientes
        self.buffer_ultimos_mensajes[canal].append({
            'mensaje': asdict(mensaje),
            'timestamp': datetime.now().isoformat()
        })
        
        # Mantener solo últimos 100 mensajes por canal
        if len(self.buffer_ultimos_mensajes[canal]) > 100:
            self.buffer_ultimos_mensajes[canal].pop(0)
        
        # Enviar a todos los suscriptores
        json_msg = mensaje.to_json()
        desconectados = set()
        
        for websocket in self.suscriptores[canal]:
            try:
                await websocket.send_text(json_msg)
            except Exception as e:
                logger.warning(f"Error enviando mensaje WebSocket: {e}")
                desconectados.add(websocket)
        
        # Limpiar desconectados
        for ws in desconectados:
            self.suscriptores[canal].discard(ws)
        
        return len(self.suscriptores[canal]) > 0
    
    def obtener_buffer_canal(self, canal: str, 
                            limites: int = 50) -> list:
        """Obtiene últimos mensajes de un canal."""
        return self.buffer_ultimos_mensajes[canal][-limites:]
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de conexiones."""
        return {
            'canales_activos': len(self.suscriptores),
            'total_suscriptores': sum(
                len(ws) for ws in self.suscriptores.values()
            ),
            'clientes_activos': len(self.clientes_canales),
            'por_canal': {
                canal: len(suscriptores)
                for canal, suscriptores in self.suscriptores.items()
            }
        }


# ═══════════════════════════════════════════════════════════════════════════
# HELPER PARA BROADCASTS
# ═══════════════════════════════════════════════════════════════════════════

_gestor_websocket_instance = None


def obtener_gestor_websocket() -> GestorWebSocket:
    """Obtiene instancia singleton."""
    global _gestor_websocket_instance
    if _gestor_websocket_instance is None:
        _gestor_websocket_instance = GestorWebSocket()
    return _gestor_websocket_instance


async def publicar_alerta_viva(alerta: Dict):
    """Publica alerta renderizada en real time."""
    gestor = obtener_gestor_websocket()
    mensaje = MensajeWebSocket(
        tipo='update',
        canal=CanalSuscripcion.ALERTAS_EN_VIVO,
        payload=alerta
    )
    await gestor.publicar_en_canal(
        CanalSuscripcion.ALERTAS_EN_VIVO,
        mensaje
    )


async def publicar_actualizacion_salud(salud: Dict):
    """Publica actualización de puntuación de salud."""
    gestor = obtener_gestor_websocket()
    mensaje = MensajeWebSocket(
        tipo='update',
        canal=CanalSuscripcion.SALUD_SISTEMA,
        payload=salud
    )
    await gestor.publicar_en_canal(
        CanalSuscripcion.SALUD_SISTEMA,
        mensaje
    )


async def publicar_estado_servicios(estado: Dict):
    """Publica cambio en disponibilidad de servicios."""
    gestor = obtener_gestor_websocket()
    mensaje = MensajeWebSocket(
        tipo='update',
        canal=CanalSuscripcion.ESTADO_SERVICIOS,
        payload=estado
    )
    await gestor.publicar_en_canal(
        CanalSuscripcion.ESTADO_SERVICIOS,
        mensaje
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    gestor = obtener_gestor_websocket()
    print("\n=== GESTOR WEBSOCKET DISPONIBLE ===")
    print(f"Canales: {[attr for attr in dir(CanalSuscripcion) if not attr.startswith('_')]}")
    
    stats = gestor.obtener_estadisticas()
    print(f"Estadísticas: {stats}")
