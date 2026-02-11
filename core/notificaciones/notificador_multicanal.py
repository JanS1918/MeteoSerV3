"""
═══════════════════════════════════════════════════════════════════════════════
STEP 20: NOTIFICACIONES AVANZADAS - TELEGRAM, DISCORD, SLACK
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  -Múltiples canales de notificación
  - Telegram, Discord, Slack integrados
  - Rich formatting y medios embebidos
  - Rate limiting por canal

Fecha: 2026-02-11
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TipoCanal(str, Enum):
    """Canales de notificación disponibles."""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK_CUSTOM = "webhook_custom"


class NotificadorMulticanal:
    """Envía notificaciones a múltiples canales."""
    
    def __init__(self):
        self.configuraciones = {
            TipoCanal.TELEGRAM: self._obtener_config_telegram(),
            TipoCanal.DISCORD: self._obtener_config_discord(),
            TipoCanal.SLACK: self._obtener_config_slack(),
        }
        self.historico_envios = []
    
    def _obtener_config_telegram(self) -> Optional[Dict]:
        """Obtiene configuración de Telegram."""
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        return {
            'token': token,
            'chat_id': chat_id,
            'disponible': bool(token and chat_id)
        }
    
    def _obtener_config_discord(self) -> Optional[Dict]:
        """Obtiene configuración de Discord."""
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        
        return {
            'webhook_url': webhook_url,
            'disponible': bool(webhook_url)
        }
    
    def _obtener_config_slack(self) -> Optional[Dict]:
        """Obtiene configuración de Slack."""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        
        return {
            'webhook_url': webhook_url,
            'disponible': bool(webhook_url)
        }
    
    async def enviar_alerta_critica(self, alerta: Dict[str, Any]):
        """Envía alerta crítica a todos los canales configurados."""
        
        titulo = f"🔴 ALERTA CRÍTICA: {alerta.get('titulo', 'Sistema')}"
        mensaje = self._formatear_alerta(alerta)
        
        await self._enviar_a_todos_canales(titulo, mensaje, alerta)
    
    async def enviar_notificacion_auditoria(self, evento: Dict[str, Any]):
        """Envía evento de auditoría."""
        
        titulo = f"📋 Auditoría: {evento.get('accion', 'Evento')}"
        mensaje = self._formatear_auditoria(evento)
        
        await self._enviar_a_todos_canales(titulo, mensaje, evento)
    
    async def enviar_estado_salud(self, salud: Dict[str, Any]):
        """Envía diariamente estado de salud."""
        
        puntuacion = salud.get('puntuacion_total', 0)
        emoji = "🟢" if puntuacion >= 75 else "🟡" if puntuacion >= 60 else "🔴"
        
        titulo = f"{emoji} Estado Salud: {puntuacion}/100"
        mensaje = self._formatear_salud(salud)
        
        await self._enviar_a_todos_canales(titulo, mensaje, salud)
    
    def _formatear_alerta(self, alerta: Dict) -> str:
        """Formatea alerta para notificación."""
        
        return f"""
**Nivel**: {alerta.get('nivel', 'N/A')}
**Dominio**: {alerta.get('dominio', 'N/A')}
**Timestamp**: {alerta.get('timestamp', 'N/A')}
**ID**: `{alerta.get('id', 'N/A')}`
        """.strip()
    
    def _formatear_auditoria(self, evento: Dict) -> str:
        """Formatea evento de auditoría."""
        
        return f"""
**Usuario**: {evento.get('usuario_id', 'Sistema')}
**Acción**: {evento.get('accion', 'N/A')}
**Entidad**: {evento.get('entidad_tipo', 'N/A')} / {evento.get('entidad_id', 'N/A')}
**Resultado**: {evento.get('resultado', 'N/A')}
        """.strip()
    
    def _formatear_salud(self, salud: Dict) -> str:
        """Formatea estado de salud."""
        
        puntuacion = salud.get('puntuacion_total', {}).get('puntuacion_total', 0)
        
        return f"""
**Puntuación**: {puntuacion}/100
**Estado**: {salud.get('puntuacion_total', {}).get('estado_general', 'Desconocido')}
**Tendencia**: {salud.get('tendencia_7dias', {}).get('tendencia', 'N/A')}
        """.strip()
    
    async def _enviar_a_todos_canales(self, titulo: str, 
                                     mensaje: str,
                                     contexto: Dict):
        """Envía a todos los canales disponibles."""
        
        tareas = []
        
        if self.configuraciones[TipoCanal.TELEGRAM]['disponible']:
            tareas.append(
                self._enviar_telegram(titulo, mensaje)
            )
        
        if self.configuraciones[TipoCanal.DISCORD]['disponible']:
            tareas.append(
                self._enviar_discord(titulo, mensaje)
            )
        
        if self.configuraciones[TipoCanal.SLACK]['disponible']:
            tareas.append(
                self._enviar_slack(titulo, mensaje)
            )
        
        if tareas:
            await asyncio.gather(*tareas, return_exceptions=True)
    
    async def _enviar_telegram(self, titulo: str, mensaje: str):
        """Envía message por Telegram."""
        
        try:
            import requests
            
            config = self.configuraciones[TipoCanal.TELEGRAM]
            if not config['disponible']:
                return
            
            url = f"https://api.telegram.org/bot{config['token']}/sendMessage"
            
            payload = {
                'chat_id': config['chat_id'],
                'text': f"{titulo}\n\n{mensaje}",
                'parse_mode': 'Markdown'
            }
            
            requests.post(url, json=payload, timeout=10)
            logger.info("Notificación Telegram enviada")
            
        except Exception as e:
            logger.warning(f"Error enviando Telegram: {e}")
    
    async def _enviar_discord(self, titulo: str, mensaje: str):
        """Envía mensaje por Discord."""
        
        try:
            import requests
            
            config = self.configuraciones[TipoCanal.DISCORD]
            if not config['disponible']:
                return
            
            payload = {
                'embeds': [{
                    'title': titulo,
                    'description': mensaje,
                    'color': 15158332,  # Rojo
                    'timestamp': datetime.now().isoformat()
                }]
            }
            
            requests.post(
                config['webhook_url'],
                json=payload,
                timeout=10
            )
            logger.info("Notificación Discord enviada")
            
        except Exception as e:
            logger.warning(f"Error enviando Discord: {e}")
    
    async def _enviar_slack(self, titulo: str, mensaje: str):
        """Envía mensaje por Slack."""
        
        try:
            import requests
            
            config = self.configuraciones[TipoCanal.SLACK]
            if not config['disponible']:
                return
            
            payload = {
                'blocks': [
                    {
                        'type': 'header',
                        'text': {'type': 'plain_text', 'text': titulo}
                    },
                    {
                        'type': 'section',
                        'text': {'type': 'mrkdwn', 'text': mensaje}
                    }
                ]
            }
            
            requests.post(
                config['webhook_url'],
                json=payload,
                timeout=10
            )
            logger.info("Notificación Slack enviada")
            
        except Exception as e:
            logger.warning(f"Error enviando Slack: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_notificador_multicanal_instance = None


def obtener_notificador_multicanal() -> NotificadorMulticanal:
    """Obtiene instancia singleton."""
    global _notificador_multicanal_instance
    if _notificador_multicanal_instance is None:
        _notificador_multicanal_instance = NotificadorMulticanal()
    return _notificador_multicanal_instance


def iniciar_notificador_multicanal() -> Dict[str, Any]:
    """Inicializa notificador multicanal."""
    try:
        notificador = obtener_notificador_multicanal()
        
        canales_disponibles = [
            canal.value for canal, config in notificador.configuraciones.items()
            if config.get('disponible')
        ]
        
        contexto = {
            'estado': 'ACTIVO',
            'canales_disponibles': canales_disponibles,
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[NOTIFICACIONES] Notificador multicanal iniciado - "
            f"Canales: {', '.join(canales_disponibles)}"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando notificador: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
