"""
═══════════════════════════════════════════════════════════════════════════════
STEP 11: WEBHOOKS & EVENTOS REACTIVOS
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Sistema pub/sub con webhooks HTTP
  - Integración en tiempo real con sistemas externos
  - Retry logic con exponential backoff
  - Histórico de deliveries

Fecha de creación: 2026-02-11
Versión: 1.0
"""

import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from collections import deque
import hashlib
import hmac

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)
DATA_PATH = Path("data/webhooks")
DATA_PATH.mkdir(parents=True, exist_ok=True)


class EventoTipo(str, Enum):
    """Tipos de eventos disponibles."""
    ALERTA_CRITICA = "alerta.critica"
    ALERTA_SEVERA = "alerta.severa"
    AUDITORIA_FAIL = "auditoria.fallo"
    VALIDACION_WH31_ANOMALIA = "validacion.wh31.anomalia"
    SALUD_DEGRADACION = "salud.degradacion"
    TENANT_ESTADO_CAMBIO = "tenant.estado.cambio"


class EstadoEntrega(str, Enum):
    """Estados de entrega de webhook."""
    PENDIENTE = "pendiente"
    EXITOSA = "exitosa"
    EN_REINTENTOS = "en_reintentos"
    FALLIDA = "fallida"
    CANCELADA = "cancelada"


@dataclass
class ConfiguracionWebhook:
    """Configuración de un webhook."""
    webhook_id: str
    url: str
    eventos: List[str]
    activo: bool = True
    secret: Optional[str] = None  # Para HMAC signing
    headers_personalizados: Dict[str, str] = None
    timeout: int = 30
    reintentos_max: int = 5
    backoff_delay: int = 5  # segundos
    timestamp_creacion: str = ""
    
    def __post_init__(self):
        if not self.timestamp_creacion:
            self.timestamp_creacion = datetime.now().isoformat()
        if not self.headers_personalizados:
            self.headers_personalizados = {}


@dataclass
class EventoPublicado:
    """Evento que se publica a webhooks."""
    tipo: str
    timestamp: str
    datos: Dict[str, Any]
    id_evento: str = ""
    origen: str = "meteoser"
    
    def __post_init__(self):
        if not self.id_evento:
            import uuid
            self.id_evento = str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════
# GESTOR DE WEBHOOKS
# ═══════════════════════════════════════════════════════════════════════════

class GestorWebhooks:
    """Gestiona webhooks y entrega de eventos."""
    
    def __init__(self):
        self.webhooks: Dict[str, ConfiguracionWebhook] = {}
        self.historico_entregas = deque(maxlen=1000)
        self.ruta_config = DATA_PATH / "configuraciones"
        self.ruta_historico = DATA_PATH / "historico"
        
        self.ruta_config.mkdir(parents=True, exist_ok=True)
        self.ruta_historico.mkdir(parents=True, exist_ok=True)
        
        self._cargar_webhooks()
        self._sesion_http = None
    
    def _cargar_webhooks(self):
        """Carga configuraciones de webhooks existentes."""
        if not self.ruta_config.exists():
            return
        
        for archivo in self.ruta_config.glob("webhook_*.json"):
            try:
                with open(archivo, 'r') as f:
                    datos = json.load(f)
                    config = ConfiguracionWebhook(**datos)
                    self.webhooks[config.webhook_id] = config
            except Exception as e:
                logger.warning(f"Error cargando webhook: {e}")
    
    async def _obtener_sesion(self) -> aiohttp.ClientSession:
        """Obtiene o crea sesión HTTP."""
        if self._sesion_http is None:
            self._sesion_http = aiohttp.ClientSession()
        return self._sesion_http
    
    def registrar_webhook(self, webhook_id: str, url: str, 
                         eventos: List[str], **kwargs) -> ConfiguracionWebhook:
        """Registra nuevo webhook."""
        
        if webhook_id in self.webhooks:
            raise ValueError(f"Webhook {webhook_id} ya existe")
        
        config = ConfiguracionWebhook(
            webhook_id=webhook_id,
            url=url,
            eventos=eventos,
            **kwargs
        )
        
        self._guardar_configuracion(config)
        self.webhooks[webhook_id] = config
        
        logger.info(f"Webhook registrado: {webhook_id} -> {url}")
        return config
    
    def _guardar_configuracion(self, config: ConfiguracionWebhook):
        """Guarda configuración de webhook."""
        archivo = self.ruta_config / f"webhook_{config.webhook_id}.json"
        datos = asdict(config)
        
        with open(archivo, 'w') as f:
            json.dump(datos, f, indent=2, default=str)
    
    def _generar_firma(self, evento: EventoPublicado, 
                       secret: str) -> str:
        """Genera firma HMAC para validación."""
        payload = json.dumps(asdict(evento), sort_keys=True, default=str)
        firma = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return firma
    
    async def publicar_evento(self, evento: EventoPublicado) -> Dict[str, Any]:
        """Publica evento a todos los webhooks suscritos."""
        
        resultado = {
            'id_evento': evento.id_evento,
            'tipo': evento.tipo,
            'timestamp': datetime.now().isoformat(),
            'entregas': {}
        }
        
        webhooks_suscritos = [
            w for w in self.webhooks.values()
            if evento.tipo in w.eventos and w.activo
        ]
        
        if not webhooks_suscritos:
            logger.debug(f"Evento {evento.tipo} sin webhooks suscritos")
            return resultado
        
        sesion = await self._obtener_sesion()
        tareas = []
        
        for webhook in webhooks_suscritos:
            tarea = self._entregar_evento(
                sesion, webhook, evento, reintentos=0
            )
            tareas.append(tarea)
        
        entregas = await asyncio.gather(*tareas, return_exceptions=True)
        
        for webhook, entrega in zip(webhooks_suscritos, entregas):
            resultado['entregas'][webhook.webhook_id] = entrega
        
        return resultado
    
    async def _entregar_evento(self, sesion: aiohttp.ClientSession,
                               webhook: ConfiguracionWebhook,
                               evento: EventoPublicado,
                               reintentos: int = 0) -> Dict[str, Any]:
        """Entrega evento a webhook individual con reintentos."""
        
        entrega = {
            'webhook_id': webhook.webhook_id,
            'url': webhook.url,
            'estado': EstadoEntrega.PENDIENTE.value,
            'intentos': reintentos + 1,
            'timestamp': datetime.now().isoformat(),
            'error': None,
            'codigo_respuesta': None
        }
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'MeteoSerV3/Webhook-Delivery/1.0',
                'X-Event-ID': evento.id_evento,
                'X-Event-Type': evento.tipo,
                **webhook.headers_personalizados
            }
            
            # Agregar firma si hay secret
            if webhook.secret:
                firma = self._generar_firma(evento, webhook.secret)
                headers['X-Signature'] = f"sha256={firma}"
            
            payload = asdict(evento)
            
            async with sesion.post(
                webhook.url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=webhook.timeout),
                allow_redirects=False
            ) as respuesta:
                
                entrega['codigo_respuesta'] = respuesta.status
                
                if 200 <= respuesta.status < 300:
                    entrega['estado'] = EstadoEntrega.EXITOSA.value
                    logger.info(
                        f"Webhook exitoso: {webhook.webhook_id} "
                        f"(evento {evento.tipo})"
                    )
                elif reintentos < webhook.reintentos_max:
                    # Reintentar con exponential backoff
                    delay = webhook.backoff_delay * (2 ** reintentos)
                    await asyncio.sleep(delay)
                    
                    entrega['estado'] = EstadoEntrega.EN_REINTENTOS.value
                    return await self._entregar_evento(
                        sesion, webhook, evento, reintentos + 1
                    )
                else:
                    entrega['estado'] = EstadoEntrega.FALLIDA.value
                    entrega['error'] = f"HTTP {respuesta.status} tras {reintentos + 1} intentos"
                    logger.error(
                        f"Webhook fallido: {webhook.webhook_id} "
                        f"(evento {evento.tipo}): {respuesta.status}"
                    )
        
        except asyncio.TimeoutError:
            if reintentos < webhook.reintentos_max:
                delay = webhook.backoff_delay * (2 ** reintentos)
                await asyncio.sleep(delay)
                entrega['estado'] = EstadoEntrega.EN_REINTENTOS.value
                return await self._entregar_evento(
                    sesion, webhook, evento, reintentos + 1
                )
            else:
                entrega['estado'] = EstadoEntrega.FALLIDA.value
                entrega['error'] = "Timeout en conexión"
        
        except Exception as e:
            if reintentos < webhook.reintentos_max:
                delay = webhook.backoff_delay * (2 ** reintentos)
                await asyncio.sleep(delay)
                entrega['estado'] = EstadoEntrega.EN_REINTENTOS.value
                return await self._entregar_evento(
                    sesion, webhook, evento, reintentos + 1
                )
            else:
                entrega['estado'] = EstadoEntrega.FALLIDA.value
                entrega['error'] = str(e)
                logger.error(f"Error entregando webhook: {e}")
        
        # Guardar en histórico
        self.historico_entregas.append(entrega)
        self._guardar_entrega(entrega)
        
        return entrega
    
    def _guardar_entrega(self, entrega: Dict):
        """Guarda histórico de entrega en archivo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        archivo = self.ruta_historico / f"entrega_{timestamp}.json"
        
        with open(archivo, 'w') as f:
            json.dump(entrega, f, indent=2, default=str)
    
    def obtener_historico(self, webhook_id: Optional[str] = None,
                         limites: int = 100) -> List[Dict]:
        """Obtiene histórico de entregas."""
        historico = list(self.historico_entregas)
        
        if webhook_id:
            historico = [
                h for h in historico
                if h.get('webhook_id') == webhook_id
            ]
        
        return historico[-limites:]
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de webhooks."""
        return {
            'total_webhooks': len(self.webhooks),
            'total_events_registrados': len([
                t.value for t in EventoTipo
            ]),
            'entregas_totales': len(self.historico_entregas),
            'entregas_exitosas': len([
                h for h in self.historico_entregas
                if h.get('estado') == EstadoEntrega.EXITOSA.value
            ]),
            'entregas_fallidas': len([
                h for h in self.historico_entregas
                if h.get('estado') == EstadoEntrega.FALLIDA.value
            ])
        }
    
    async def cerrar(self):
        """Cierra sesión HTTP."""
        if self._sesion_http:
            await self._sesion_http.close()


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_gestor_webhooks_instance = None


def obtener_gestor_webhooks() -> GestorWebhooks:
    """Obtiene instancia singleton."""
    global _gestor_webhooks_instance
    if _gestor_webhooks_instance is None:
        _gestor_webhooks_instance = GestorWebhooks()
    return _gestor_webhooks_instance


def iniciar_gestor_webhooks() -> Dict[str, Any]:
    """Inicializa gestor de webhooks."""
    try:
        gestor = obtener_gestor_webhooks()
        
        contexto = {
            'estado': 'ACTIVO',
            'webhooks_registrados': len(gestor.webhooks),
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[WEBHOOKS] Gestor iniciado - "
            f"{contexto['webhooks_registrados']} webhooks activos"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando gestor de webhooks: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    gestor = obtener_gestor_webhooks()
    
    # Test registro
    gestor.registrar_webhook(
        'test_webhook',
        'https://example.com/webhook',
        [EventoTipo.ALERTA_CRITICA.value],
        secret='secret_key'
    )
    
    print("\n=== WEBHOOK REGISTRADO ===")
    for webhook_id, config in gestor.webhooks.items():
        print(f"  • {webhook_id}: {config.url}")
