"""
═══════════════════════════════════════════════════════════════════════════════
STEP 16: AUDIT TRAIL - LOGGING COMPLETO
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Registro completo de acciones críticas
  - Trazabilidad de cambios en configuración
  - Cumpimiento normativo y seguridad
  - Búsqueda y análisis de logs

Fecha de creación: 2026-02-11
Versión: 1.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)
DATA_PATH = Path("data/audit")
DATA_PATH.mkdir(parents=True, exist_ok=True)


class TipoAccion(str, Enum):
    """Tipos de acciones auditables."""
    CONFIG_CAMBIO = "config.cambio"
    CONFIG_CREACION = "config.creacion"
    WEBHOOK_REGISTRO = "webhook.registro"
    WEBHOOK_ACTIVACION = "webhook.activacion"
    TENANT_CREACION = "tenant.creacion"
    TENANT_CAMBIO_ESTADO = "tenant.cambio_estado"
    FEATURE_CAMBIO = "feature.cambio"
    API_ENDPOINT_LLAMADA = "api.endpoint.llamada"
    AUTENTICACION = "autenticacion"
    AUTORIZACION_FALLO = "autorizacion.fallo"
    SEGURIDAD_EVENTO = "seguridad.evento"


class SeveridadAudit(str, Enum):
    """Nivel de severidad."""
    INFORMATIVO = "informativo"
    ADVERTENCIA = "advertencia"
    CRÍTICO = "crítico"
    SEGURIDAD = "seguridad"


@dataclass
class EventoAudit:
    """Evento de auditoría."""
    tipo: str
    severidad: str
    usuario_id: str
    entidad_tipo: str
    entidad_id: str
    accion: str
    detalles: Dict[str, Any]
    ip_origen: Optional[str] = None
    user_agent: Optional[str] = None
    resultado: str = "exitoso"  # "exitoso", "fallo", "parcial"
    codigo_error: Optional[str] = None
    timestamp: str = ""
    id_evento: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.id_evento:
            import uuid
            self.id_evento = str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════
# REGISTRADOR DE AUDITORÍA
# ═══════════════════════════════════════════════════════════════════════════

class RegistradorAudit:
    """Registra eventos de auditoría."""
    
    def __init__(self, retencion_dias: int = 90):
        self.retencion_dias = retencion_dias
        self.eventos_memoria = deque(maxlen=10000)
        self.ruta_eventos = DATA_PATH / "eventos"
        self.ruta_eventos.mkdir(parents=True, exist_ok=True)
    
    def registrar(self, evento: EventoAudit) -> str:
        """Registra evento de auditoría."""
        
        # Guardar en memoria
        self.eventos_memoria.append(evento)
        
        # Guardar en archivo
        archivo = self.ruta_eventos / f"audit_{evento.id_evento}.json"
        
        try:
            with open(archivo, 'w') as f:
                json.dump(asdict(evento), f, indent=2, default=str)
            
            log_msg = (
                f"AUDIT[{evento.tipo}] usuario={evento.usuario_id} "
                f"entidad={evento.entidad_tipo}/{evento.entidad_id} "
                f"accion={evento.accion} resultado={evento.resultado}"
            )
            
            if evento.severidad == SeveridadAudit.CRÍTICO.value:
                logger.critical(log_msg)
            elif evento.severidad == SeveridadAudit.SEGURIDAD.value:
                logger.warning(f"SECURITY: {log_msg}")
            else:
                logger.info(log_msg)
            
            return evento.id_evento
            
        except Exception as e:
            logger.error(f"Error registrando evento de auditoría: {e}")
            return ""
    
    def buscar_eventos(self, 
                      usuario_id: Optional[str] = None,
                      tipo_accion: Optional[str] = None,
                      entidad_tipo: Optional[str] = None,
                      desde: Optional[datetime] = None,
                      hasta: Optional[datetime] = None,
                      limites: int = 100) -> List[Dict]:
        """Busca eventos en histórico."""
        
        eventos = list(self.eventos_memoria)
        
        # Filtrar
        if usuario_id:
            eventos = [e for e in eventos if e.usuario_id == usuario_id]
        
        if tipo_accion:
            eventos = [e for e in eventos if e.tipo == tipo_accion]
        
        if entidad_tipo:
            eventos = [e for e in eventos if e.entidad_tipo == entidad_tipo]
        
        # Filtrar por fecha
        if desde:
            eventos = [
                e for e in eventos
                if datetime.fromisoformat(e.timestamp) >= desde
            ]
        
        if hasta:
            eventos = [
                e for e in eventos
                if datetime.fromisoformat(e.timestamp) <= hasta
            ]
        
        # Ordenar por fecha (más recientes primero)
        eventos = sorted(
            eventos,
            key=lambda e: e.timestamp,
            reverse=True
        )
        
        return [asdict(e) for e in eventos[:limites]]
    
    def obtener_evento(self, id_evento: str) -> Optional[Dict]:
        """Obtiene evento específico."""
        
        for evento in self.eventos_memoria:
            if evento.id_evento == id_evento:
                return asdict(evento)
        
        # Intentar leer de archivo
        archivo = self.ruta_eventos / f"audit_{id_evento}.json"
        if archivo.exists():
            try:
                with open(archivo, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return None
    
    # ─────────────────────────────────────────────────────────────────────
    # MÉTODOS DE CONVENIENCIA
    # ─────────────────────────────────────────────────────────────────────
    
    def registrar_cambio_config(self, usuario_id: str, 
                               clave_config: str,
                               valor_anterior: Any,
                               valor_nuevo: Any,
                               ip_origen: str = None):
        """Registra cambio de configuración."""
        
        evento = EventoAudit(
            tipo=TipoAccion.CONFIG_CAMBIO.value,
            severidad=SeveridadAudit.INFORMATIVO.value,
            usuario_id=usuario_id,
            entidad_tipo="configuracion",
            entidad_id=clave_config,
            accion="actualizar",
            detalles={
                'valor_anterior': valor_anterior,
                'valor_nuevo': valor_nuevo
            },
            ip_origen=ip_origen
        )
        
        return self.registrar(evento)
    
    def registrar_intento_no_autorizado(self, usuario_id: str,
                                       endpoint: str,
                                       ip_origen: str = None):
        """Registra intento de acceso no autorizado."""
        
        evento = EventoAudit(
            tipo=TipoAccion.AUTORIZACION_FALLO.value,
            severidad=SeveridadAudit.SEGURIDAD.value,
            usuario_id=usuario_id,
            entidad_tipo="api",
            entidad_id=endpoint,
            accion="acceso_denegado",
            detalles={'endpoint': endpoint},
            ip_origen=ip_origen,
            resultado="fallo"
        )
        
        return self.registrar(evento)
    
    def registrar_webhook_publicacion(self, webhook_id: str,
                                     evento_tipo: str,
                                     resultado: str,
                                     usuario_id: str = "sistem"):
        """Registra publicación de webhook."""
        
        evento = EventoAudit(
            tipo=TipoAccion.WEBHOOK_ACTIVACION.value,
            severidad=SeveridadAudit.INFORMATIVO.value,
            usuario_id=usuario_id,
            entidad_tipo="webhook",
            entidad_id=webhook_id,
            accion="publicacion",
            detalles={'evento_tipo': evento_tipo},
            resultado=resultado
        )
        
        return self.registrar(evento)
    
    def registrar_llamada_api(self, usuario_id: str,
                             metodo: str,
                             endpoint: str,
                             codigo_respuesta: int,
                             ip_origen: str = None):
        """Registra llamada a API."""
        
        evento = EventoAudit(
            tipo=TipoAccion.API_ENDPOINT_LLAMADA.value,
            severidad=SeveridadAudit.INFORMATIVO.value,
            usuario_id=usuario_id,
            entidad_tipo="api",
            entidad_id=endpoint,
            accion=metodo,
            detalles={'codigo_respuesta': codigo_respuesta},
            ip_origen=ip_origen
        )
        
        return self.registrar(evento)
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de auditoría."""
        
        eventos = list(self.eventos_memoria)
        
        return {
            'total_eventos': len(eventos),
            'por_tipo': self._contar_por_campo(eventos, 'tipo'),
            'por_usuario': self._contar_por_campo(eventos, 'usuario_id'),
            'por_severidad': self._contar_por_campo(eventos, 'severidad'),
            'por_resultado': self._contar_por_campo(eventos, 'resultado')
        }
    
    def _contar_por_campo(self, eventos: List, campo: str) -> Dict[str, int]:
        """Cuenta ocurrencias por campo."""
        
        conteos = {}
        for evento in eventos:
            valor = getattr(evento, campo)
            conteos[valor] = conteos.get(valor, 0) + 1
        
        return conteos


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_registrador_audit_instance = None


def obtener_registrador_audit() -> RegistradorAudit:
    """Obtiene instancia singleton."""
    global _registrador_audit_instance
    if _registrador_audit_instance is None:
        _registrador_audit_instance = RegistradorAudit()
    return _registrador_audit_instance


def iniciar_registrador_audit() -> Dict[str, Any]:
    """Inicializa registrador de auditoría."""
    try:
        registrador = obtener_registrador_audit()
        
        contexto = {
            'estado': 'ACTIVO',
            'retencion_dias': registrador.retencion_dias,
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[AUDIT] Registrador iniciado - "
            f"Retención: {contexto['retencion_dias']} días"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando registrador de auditoría: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
