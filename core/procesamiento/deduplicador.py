"""
═══════════════════════════════════════════════════════════════════════════════
STEP 24: DEDUPLICACIÓN DE DATOS
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Evitar procesamiento de alertas duplicadas
  - Fingerprinting de eventos
  - Ventanas deslizantes de deduplicación
  - Idempotencia en operaciones

Fecha: 2026-02-11
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class RegistroDeduplicacion:
    """Registro de evento deduplicado."""
    fingerprint: str
    timestamp: str
    contador: int
    primera_ocurrencia: str
    ultima_ocurrencia: str


class DeduplicadorEventos:
    """Deduplicador de eventos y alertas."""
    
    def __init__(self, ventana_minutos: int = 30, max_registros: int = 10000):
        self.ventana_minutos = ventana_minutos
        self.max_registros = max_registros
        self.registros: Dict[str, RegistroDeduplicacion] = {}
        self.historial = deque(maxlen=max_registros)
    
    def generar_fingerprint(self, evento: Dict[str, Any]) -> str:
        """Genera fingerprint único para evento."""
        
        # Campos clave para deduplicación
        campos_clave = {
            'tipo_alerta': evento.get('tipo_alerta'),
            'sensor_id': evento.get('sensor_id'),
            'parametro': evento.get('parametro'),
            'severidad': evento.get('severidad'),
            'valor': evento.get('valor')
        }
        
        # Crear JSON determinístico
        json_str = json.dumps(
            campos_clave,
            sort_keys=True,
            default=str
        )
        
        # Generar hash SHA-256
        fingerprint = hashlib.sha256(json_str.encode()).hexdigest()[:16]
        
        return fingerprint
    
    def es_duplicado(self, evento: Dict[str, Any]) -> bool:
        """Verifica si evento es duplicado."""
        
        fingerprint = self.generar_fingerprint(evento)
        ahora = datetime.now()
        
        if fingerprint in self.registros:
            registro = self.registros[fingerprint]
            
            # Parsear timestamp de última ocurrencia
            ultima_ocurrencia = datetime.fromisoformat(
                registro.ultima_ocurrencia
            )
            
            # Verificar si está dentro de la ventana
            tiempo_transcurrido = (ahora - ultima_ocurrencia).total_seconds() / 60
            
            if tiempo_transcurrido < self.ventana_minutos:
                # Es duplicado dentro de la ventana
                registro.contador += 1
                registro.ultima_ocurrencia = ahora.isoformat()
                return True
            else:
                # Ventana expiró, crear nuevo registro
                del self.registros[fingerprint]
                return False
        
        return False
    
    def registrar_evento(self, evento: Dict[str, Any]) -> Dict[str, Any]:
        """Registra evento (duplicado o nuevo)."""
        
        fingerprint = self.generar_fingerprint(evento)
        ahora = datetime.now()
        
        if fingerprint in self.registros:
            # Actualizar registro existente
            registro = self.registros[fingerprint]
            registro.contador += 1
            registro.ultima_ocurrencia = ahora.isoformat()
            
            resultado = {
                'tipo': 'DUPLICADO',
                'fingerprint': fingerprint,
                'contador': registro.contador,
                'primera_ocurrencia': registro.primera_ocurrencia,
                'suprimido': True
            }
        
        else:
            # Nuevo evento
            registro = RegistroDeduplicacion(
                fingerprint=fingerprint,
                timestamp=ahora.isoformat(),
                contador=1,
                primera_ocurrencia=ahora.isoformat(),
                ultima_ocurrencia=ahora.isoformat()
            )
            
            self.registros[fingerprint] = registro
            
            resultado = {
                'tipo': 'NUEVO',
                'fingerprint': fingerprint,
                'contador': 1,
                'primera_ocurrencia': ahora.isoformat(),
                'suprimido': False
            }
        
        # Agregar al historial
        self.historial.append({
            'fingerprint': fingerprint,
            'tipo': resultado['tipo'],
            'timestamp': ahora.isoformat()
        })
        
        # Limpiar registros expirados si es necesario
        if len(self.registros) > self.max_registros:
            self._limpiar_expirados()
        
        return resultado
    
    def _limpiar_expirados(self):
        """Limpia registros que expiron su ventana."""
        
        ahora = datetime.now()
        fingerprints_expirados = []
        
        for fingerprint, registro in self.registros.items():
            ultima_ocurrencia = datetime.fromisoformat(
                registro.ultima_ocurrencia
            )
            
            tiempo_transcurrido = (ahora - ultima_ocurrencia).total_seconds() / 60
            
            if tiempo_transcurrido >= self.ventana_minutos:
                fingerprints_expirados.append(fingerprint)
        
        for fingerprint in fingerprints_expirados:
            del self.registros[fingerprint]
        
        if fingerprints_expirados:
            logger.info(
                f"[DEDUP] {len(fingerprints_expirados)} registros "
                f"expirados eliminados"
            )
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de deduplicación."""
        
        total_eventos = len(self.historial)
        eventos_duplicados = sum(
            1 for e in self.historial if e['tipo'] == 'DUPLICADO'
        )
        
        eventos_nuevos = total_eventos - eventos_duplicados
        
        tasa_duplicacion = (
            (eventos_duplicados / total_eventos * 100)
            if total_eventos > 0 else 0
        )
        
        return {
            'total_eventos_procesados': total_eventos,
            'eventos_nuevos': eventos_nuevos,
            'eventos_duplicados': eventos_duplicados,
            'tasa_duplicacion': f"{tasa_duplicacion:.1f}%",
            'registros_activos': len(self.registros),
            'ventana_minutos': self.ventana_minutos,
            'timestamp': datetime.now().isoformat()
        }


class DeduplicadorIdempotencia:
    """Deduplicador basado en ID de idempotencia."""
    
    def __init__(self, ttl_minutos: int = 60):
        self.ttl_minutos = ttl_minutos
        self.ids_procesados: Dict[str, str] = {}  # id_idempotencia -> resultado
    
    def procesar_con_idempotencia(self, 
                                  id_idempotencia: str,
                                  func_procesamiento) -> Dict[str, Any]:
        """Procesa con garantía de idempotencia."""
        
        # Verificar si ya fue procesado
        if id_idempotencia in self.ids_procesados:
            return {
                'tipo': 'REINTENTO',
                'id_idempotencia': id_idempotencia,
                'procesado_previamente': True,
                'timestamp': datetime.now().isoformat()
            }
        
        # Procesar
        resultado = func_procesamiento()
        
        # Guardar resultado
        self.ids_procesados[id_idempotencia] = json.dumps(resultado, default=str)
        
        return {
            'tipo': 'NUEVO',
            'id_idempotencia': id_idempotencia,
            'procesado_previamente': False,
            'resultado': resultado,
            'timestamp': datetime.now().isoformat()
        }
    
    def obtener_resultado_previo(self, id_idempotencia: str) -> Optional[Any]:
        """Obtiene resultado de procesamiento previo."""
        
        if id_idempotencia in self.ids_procesados:
            return json.loads(self.ids_procesados[id_idempotencia])
        
        return None
    
    def limpiar_antiguos(self):
        """Limpia IDs antiguos."""
        # Implementación simplificada
        if len(self.ids_procesados) > 10000:
            # Mantener solo los últimos 5000
            items_a_mantener = dict(
                list(self.ids_procesados.items())[-5000:]
            )
            self.ids_procesados = items_a_mantener
            logger.info("[DEDUP] IDs idempotencia antiguos eliminados")


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_deduplicador_eventos_instance = None
_deduplicador_idempotencia_instance = None


def obtener_deduplicador_eventos() -> DeduplicadorEventos:
    """Obtiene instancia de deduplicador de eventos."""
    global _deduplicador_eventos_instance
    if _deduplicador_eventos_instance is None:
        _deduplicador_eventos_instance = DeduplicadorEventos(
            ventana_minutos=30,
            max_registros=10000
        )
    
    return _deduplicador_eventos_instance


def obtener_deduplicador_idempotencia() -> DeduplicadorIdempotencia:
    """Obtiene instancia de deduplicador de idempotencia."""
    global _deduplicador_idempotencia_instance
    if _deduplicador_idempotencia_instance is None:
        _deduplicador_idempotencia_instance = DeduplicadorIdempotencia(
            ttl_minutos=60
        )
    
    return _deduplicador_idempotencia_instance


def iniciar_deduplicadores() -> Dict[str, Any]:
    """Inicializa deduplicadores."""
    try:
        dedup_eventos = obtener_deduplicador_eventos()
        dedup_idempotencia = obtener_deduplicador_idempotencia()
        
        contexto = {
            'estado': 'ACTIVO',
            'deduplicador_eventos': {
                'ventana_minutos': dedup_eventos.ventana_minutos,
                'max_registros': dedup_eventos.max_registros
            },
            'deduplicador_idempotencia': {
                'ttl_minutos': dedup_idempotencia.ttl_minutos
            },
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info("[DEDUP] Deduplicadores iniciados")
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando deduplicadores: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
