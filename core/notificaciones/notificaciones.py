"""
SISTEMA NOTIFICACIONES - EMAIL + SLACK v1.0
═════════════════════════════════════════════════════════════════════════════

Envía notificaciones de alertas y auditorías críticas por:
- Email (SMTP)
- Slack (Webhook)
-Console (local)

Configuración:
  EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, EMAIL_FROM, EMAIL_TO (env vars)
  SLACK_WEBHOOK_URL (env var)

Fecha: 11 de febrero de 2026
"""

import logging
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import asyncio
import threading

logger = logging.getLogger(__name__)


class NotificadorAlertas:
    """Envía notificaciones de alertas y auditorías."""
    
    def __init__(self):
        """Inicializa notificadores disponibles."""
        self.email_config = self._cargar_config_email()
        self.slack_config = self._cargar_config_slack()
        self.console_enabled = True
        self.historial_notificaciones = []
        self.max_historial = 100
        
        logger.info("[NOTIF] Sistema de notificaciones inicializado")
        if self.email_config:
            logger.info(f"[NOTIF] Email habilitado: {self.email_config['from']}")
        if self.slack_config:
            logger.info(f"[NOTIF] Slack habilitado")
    
    def _cargar_config_email(self) -> Optional[Dict]:
        """Carga configuración de email de env vars."""
        host = os.getenv("EMAIL_SMTP_HOST")
        port = os.getenv("EMAIL_SMTP_PORT")
        from_addr = os.getenv("EMAIL_FROM")
        to_addrs = os.getenv("EMAIL_TO")
        
        if not all([host, port, from_addr, to_addr s]):
            return None
        
        return {
            "host": host,
            "port": int(port),
            "from": from_addr,
            "to": [a.strip() for a in to_addrs.split(",")],
            "usar_tls": os.getenv("EMAIL_USE_TLS", "1") in ("1", "true")
        }
    
    def _cargar_config_slack(self) -> Optional[Dict]:
        """Carga configuración de Slack de env vars."""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
        if not webhook_url:
            return None
        
        return {
            "webhook_url": webhook_url,
            "canal": os.getenv("SLACK_CHANNEL", "#alertas-meteoser")
        }
    
    async def notificar_alerta_critica(self, alerta: Dict):
        """Envía notificación cuando una alerta CRÍTICA se activa."""
        try:
            mensaje = f"""
🔴 ALERTA CRÍTICA METEOSER
═════════════════════════════════════════════════════════════════════════════

Dominio:      {alerta.get('dominio', 'DESCONOCIDO')}
Nivel:        {alerta.get('nivel', 'CRÍTICO')}
Magnitud:     {alerta.get('impacto_magnitud', 'N/A')}
Causa:        {alerta.get('evento_causa', 'Evento desconocido')}

Acción Recomendada:
{alerta.get('recomendacion', 'Monitorear situación')}

Timestamp:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═════════════════════════════════════════════════════════════════════════════
"""
            
            await self._enviar_notificaciones(
                asunto=f"⚠️  ALERTA CRÍTICA: {alerta.get('dominio', 'Sistema')}",
                mensaje=mensaje,
                tipo="ALERTA_CRITICA",
                datos=alerta
            )
        except Exception as e:
            logger.error(f"Error notificando alerta: {e}")
    
    async def notificar_auditoria_fallo(self, auditoria: Dict):
        """Envía notificación cuando hay fallo en auditoría post-ciclo."""
        try:
            dominios_fail = auditoria.get('dominios_fallidos', [])
            cobertura = auditoria.get('cobertura_porcentaje', 0)
            
            mensaje = f"""
❌ FALLO EN AUDITORÍA POST-CICLO
═════════════════════════════════════════════════════════════════════════════

Estado:       {auditoria.get('estado_auditoria', 'UNKNOWN')}
Cobertura:    {cobertura:.0f}%
Dominios con Fallo:  {', '.join(dominios_fail) if dominios_fail else 'Ninguno'}

Constantes Faltantes: {auditoria.get('constantes_presentes', 0)}/{auditoria.get('total_constantes_esperadas', 0)}

Recomendaciones:
{chr(10).join(['  - ' + r for r in auditoria.get('recomendaciones', [])])}

Timestamp:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═════════════════════════════════════════════════════════════════════════════
"""
            
            await self._enviar_notificaciones(
                asunto=f"❌ Auditoría FAIL - Cobertura {cobertura:.0f}%",
                mensaje=mensaje,
                tipo="AUDITORIA_FAIL",
                datos=auditoria
            )
        except Exception as e:
            logger.error(f"Error notificando auditoría: {e}")
    
    async def notificar_validacion_wh31_anomalia(self, validacion: Dict):
        """Envía notificación si hay anomalía en validación WH31."""
        try:
            stats = validacion.get('estadisticas', {})
            diff = stats.get('diferencial_wh31_vs_wh65', {}).get('promedio', 0)
            
            if abs(diff) > 2.0:  # Umbral de anomalía
                mensaje = f"""
⚠️  ANOMALÍA DETECTADA EN VALIDACIÓN WH31
═════════════════════════════════════════════════════════════════════════════

Diferencial WH31-WH65:  {diff:+.2f}°C (ANÓMALO - umbral: ±2.0°C)
Error Sistemático:      {stats.get('error_sistematico_wh31', {}).get('promedio', 0):.3f}°C
Período Análisis:       {stats.get('periodo_dias', 0):.1f} días

Acción Recomendada:
1. Revisar instalación física del sensor WH31
2. Verificar componentes ópticos (posible neblina/suciedad)
3. Comparar con histórico de calibración
4. Considerar reemplazo si el sesgo persiste

Timestamp:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═════════════════════════════════════════════════════════════════════════════
"""
                
                await self._enviar_notificaciones(
                    asunto=f"⚠️  Anomalía WH31: Diferencial {diff:+.2f}°C",
                    mensaje=mensaje,
                    tipo="VALIDACION_ANOMALIA",
                    datos=validacion
                )
        except Exception as e:
            logger.error(f"Error notificando anomalía WH31: {e}")
    
    async def notificar_estado_sistema(self, estado: Dict):
        """Envía notificación de estado general del sistema (resumen diario)."""
        try:
            mensaje = f"""
📊 REPORTE DIARIO METEOSER
═════════════════════════════════════════════════════════════════════════════

Alertas Críticas:       {estado.get('criticas_activas', 0)}
Alertas Totales:        {estado.get('total_activas', 0)}
Auditoría:              {estado.get('auditoria_estado', 'UNKNOWN')}
Validaciones WH31:      {estado.get('wh31_ejecuciones', 0)} (últimos 7 días)

Dominios Afectados:
{chr(10).join(['  - ' + d for d in estado.get('dominios_criticos', [])])}

Timestamp:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
═════════════════════════════════════════════════════════════════════════════
"""
            
            await self._enviar_notificaciones(
                asunto="📊 Reporte Diario MeteoSerV3",
                mensaje=mensaje,
                tipo="REPORTE_DIARIO",
                datos=estado
            )
        except Exception as e:
            logger.error(f"Error notificando estado: {e}")
    
    async def _enviar_notificaciones(self, asunto: str, mensaje: str, tipo: str, datos: Dict):
        """Distribuye notificación a todos los canales configurados."""
        
        # Registrar en historial
        self.historial_notificaciones.append({
            'timestamp': datetime.now().isoformat(),
            'tipo': tipo,
            'asunto': asunto,
            'canales_enviados': []
        })
        if len(self.historial_notificaciones) > self.max_historial:
            self.historial_notificaciones = self.historial_notificaciones[-self.max_historial:]
        
        # Console siempre
        if self.console_enabled:
            logger.warning(f"[NOTIF] {tipo}: {asunto}")
        
        # Email
        if self.email_config:
            try:
                await self._enviar_email(asunto, mensaje)
                self.historial_notificaciones[-1]['canales_enviados'].append('EMAIL')
            except Exception as e:
                logger.warning(f"[NOTIF] Error enviando email: {e}")
        
        # Slack
        if self.slack_config:
            try:
                await self._enviar_slack(asunto, mensaje, tipo, datos)
                self.historial_notificaciones[-1]['canales_enviados'].append('SLACK')
            except Exception as e:
                logger.warning(f"[NOTIF] Error enviando Slack: {e}")
    
    async def _enviar_email(self, asunto: str, body: str):
        """Envía notificación por email."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            config = self.email_config
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = config['from']
            msg['To'] = ', '.join(config['to'])
            msg['Subject'] = asunto
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar (en thread separado para no bloquear)
            def _send():
                server = smtplib.SMTP(config['host'], config['port'])
                if config['usar_tls']:
                    server.starttls()
                server.send_message(msg)
                server.quit()
            
            thread = threading.Thread(target=_send, daemon=True)
            thread.start()
            thread.join(timeout=10)
            
            logger.debug(f"[NOTIF] Email enviado: {asunto}")
            
        except Exception as e:
            logger.error(f"[NOTIF] Error en email: {e}")
    
    async def _enviar_slack(self, asunto: str, body: str, tipo: str, datos: Dict):
        """Envía notificación por Slack."""
        try:
            import requests
            
            # Emoji por tipo
            emoji_map = {
                'ALERTA_CRITICA': '🔴',
                'AUDITORIA_FAIL': '❌',
                'VALIDACION_ANOMALIA': '⚠️',
                'REPORTE_DIARIO': '📊'
            }
            
            emoji = emoji_map.get(tipo, '📣')
            
            # Formato Slack
            payload = {
                "channel": self.slack_config.get('canal', '#alertas'),
                "username": "MeteoSer Notificador",
                "icon_emoji": emoji,
                "text": f"{emoji} *{asunto}*",
                "attachments": [
                    {
                        "color": "danger" if "CRÍTICA" in asunto or "FAIL" in asunto else "warning",
                        "text": body,
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            # Enviar en thread
            async def _send():
                response = requests.post(
                    self.slack_config['webhook_url'],
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
            
            # Ejecutar sin bloquear
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_send())
            
            logger.debug(f"[NOTIF] Slack enviado: {asunto}")
            
        except Exception as e:
            logger.error(f"[NOTIF] Error en Slack: {e}")
    
    def obtener_historial(self, limites: int = 20) -> List[Dict]:
        """Retorna historial de notificaciones."""
        return self.historial_notificaciones[-limites:]


# Instancia global
_notificador_instance = None


def obtener_notificador() -> NotificadorAlertas:
    """Obtiene o crea la instancia global."""
    global _notificador_instance
    
    if _notificador_instance is None:
        _notificador_instance = NotificadorAlertas()
    
    return _notificador_instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    notif = obtener_notificador()
    print("Sistema de notificaciones cargado")
    print(f"Email disponible: {notif.email_config is not None}")
    print(f"Slack disponible: {notif.slack_config is not None}")
