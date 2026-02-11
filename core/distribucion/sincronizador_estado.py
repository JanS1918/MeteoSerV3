"""
═══════════════════════════════════════════════════════════════════════════════
STEP 22: SINCRONIZACIÓN DE ESTADO DISTRIBUIDO
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Mantener estado consistente entre nodos
  - Usar Redis como backend distribuido
  - Gossip protocol para propagación rápida
  - Eventual consistency

Fecha: 2026-02-11
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EventoEstado:
    """Evento de cambio de estado."""
    clave: str
    valor: Any
    version: int
    timestamp: str
    nodo_origen: str
    tipo_operacion: str  # "set", "delete", "merge"


class SincronizadorEstado:
    """Sincroniza estado entre nodos del cluster."""
    
    def __init__(self, nodo_id: str):
        self.nodo_id = nodo_id
        self.estado_local: Dict[str, Dict[str, Any]] = {}
        self.historial_eventos: list = []
        self.cliente_redis = None
        self._intentar_conectar_redis()
    
    def _intentar_conectar_redis(self):
        """Intenta conectar a Redis."""
        try:
            import redis
            import os
            
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            
            self.cliente_redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True
            )
            
            self.cliente_redis.ping()
            logger.info("[SYNC] Redis disponible para sincronización")
            
        except Exception as e:
            logger.warning(f"[SYNC] Redis no disponible, usando en-memoria: {e}")
            self.cliente_redis = None
    
    async def sincronizar_estado(self, clave: str, valor: Any) -> bool:
        """Sincroniza estado con otros nodos."""
        
        evento = EventoEstado(
            clave=clave,
            valor=valor,
            version=1,
            timestamp=datetime.now().isoformat(),
            nodo_origen=self.nodo_id,
            tipo_operacion="set"
        )
        
        # Guardar localmente
        self.estado_local[clave] = {
            'valor': valor,
            'version': evento.version,
            'timestamp': evento.timestamp
        }
        
        # Sincronizar con Redis si disponible
        if self.cliente_redis:
            try:
                clave_redis = f"estado:{clave}"
                self.cliente_redis.set(
                    clave_redis,
                    json.dumps({
                        'valor': valor,
                        'version': evento.version,
                        'timestamp': evento.timestamp,
                        'nodo_origen': self.nodo_id
                    }),
                    ex=86400  # 24 horas TTL
                )
            except Exception as e:
                logger.warning(f"Error sincronizando en Redis: {e}")
        
        # Registrar evento
        self.historial_eventos.append(evento)
        
        return True
    
    async def obtener_estado(self, clave: str) -> Optional[Any]:
        """Obtiene estado sincronizado."""
        
        # Intentar obtener de Redis primero
        if self.cliente_redis:
            try:
                clave_redis = f"estado:{clave}"
                valor_redis = self.cliente_redis.get(clave_redis)
                
                if valor_redis:
                    datos = json.loads(valor_redis)
                    return datos.get('valor')
            except Exception:
                pass
        
        # Fallback a estado local
        if clave in self.estado_local:
            return self.estado_local[clave].get('valor')
        
        return None
    
    async def sincronizar_con_nodo(self, nodo_id: str,
                                  nodo_host: str,
                                  nodo_puerto: int):
        """Sincroniza con nodo remoto (gossip protocol)."""
        
        try:
            import aiohttp
            
            url = f"http://{nodo_host}:{nodo_puerto}/api/v1/sync/estado"
            
            payload = {
                'nodo_id': self.nodo_id,
                'estado': self.estado_local,
                'timestamp': datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=5) as resp:
                    if resp.status == 200:
                        datos_remoto = await resp.json()
                        await self._fusionar_estado(
                            datos_remoto.get('estado', {})
                        )
                        logger.info(f"Estado sincronizado con {nodo_id}")
                        return True
        
        except Exception as e:
            logger.warning(f"Error sincronizando con {nodo_id}: {e}")
        
        return False
    
    async def _fusionar_estado(self, estado_remoto: Dict[str, Any]):
        """Fusiona estado remoto con local (merge strategy)."""
        
        for clave, datos_remoto in estado_remoto.items():
            datos_local = self.estado_local.get(clave)
            
            if not datos_local:
                # No existe localmente, tomar remoto
                self.estado_local[clave] = datos_remoto
            else:
                # Comparar versiones, tomar más reciente
                if datos_remoto.get('version', 0) > datos_local.get('version', 0):
                    self.estado_local[clave] = datos_remoto
    
    def obtener_consistencia(self) -> Dict[str, Any]:
        """Obtiene información de consistencia."""
        
        return {
            'nodo_id': self.nodo_id,
            'claves_locales': len(self.estado_local),
            'eventos_procesados': len(self.historial_eventos),
            'redis_disponible': self.cliente_redis is not None,
            'timestamp': datetime.now().isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_sincronizador_instance = None


def obtener_sincronizador_estado(nodo_id: str = None) -> SincronizadorEstado:
    """Obtiene instancia singleton."""
    global _sincronizador_instance
    if _sincronizador_instance is None:
        import os
        import socket
        
        nodo_id = nodo_id or os.getenv('NODE_ID', socket.gethostname())
        _sincronizador_instance = SincronizadorEstado(nodo_id)
    
    return _sincronizador_instance


def iniciar_sincronizador_estado() -> Dict[str, Any]:
    """Inicializa sincronización de estado."""
    try:
        sincronizador = obtener_sincronizador_estado()
        
        contexto = {
            'estado': 'ACTIVO',
            'nodo_id': sincronizador.nodo_id,
            'backend': 'Redis' if sincronizador.cliente_redis else 'En-Memoria',
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[SYNC] Sincronización iniciada - "
            f"Backend: {contexto['backend']}"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando sincronización: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
