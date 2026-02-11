"""
═══════════════════════════════════════════════════════════════════════════════
STEP 14: RATE LIMITING & THROTTLING
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Proteger API contra abuso
  - Throttling por endpoint y por cliente
  - Límites por tenant
  - Estadísticas de uso

Fecha de creación: 2026-02-11
Versión: 1.0
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LimiteCuota:
    """Límite de cuota para endpoint."""
    nombre: str
    requests_max: int  # Máximo de requests
    ventana_segundos: int  # Ventana deslizante
    descripcion: str = ""


# ═══════════════════════════════════════════════════════════════════════════
# LIMITADOR DE TASA
# ═══════════════════════════════════════════════════════════════════════════

class LimitadorTasa:
    """Token bucket algorithm para rate limiting."""
    
    def __init__(self):
        # Por cliente: {cliente_id: deque de timestamps}
        self.ventanas_deslizantes: Dict[str, deque] = defaultdict(deque)
        
        # Cuotas limitadas por endpoint
        self.cuotas_endpoint: Dict[str, LimiteCuota] = {}
        
        # Estadísticas
        self.estadisticas: Dict[str, Dict] = defaultdict(lambda: {
            'requests_total': 0,
            'requests_rechazados': 0,
            'timestamp_primer_request': None,
            'timestamp_ultimo_request': None
        })
        
        self._inicializar_cuotas_default()
    
    def _inicializar_cuotas_default(self):
        """Inicializa cuotas por defecto."""
        cuotas_default = [
            LimiteCuota("GET /api/v1/alertas/activas", 100, 60),
            LimiteCuota("GET /api/v1/salud/puntuacion", 50, 60),
            LimiteCuota("POST /api/v1/webhooks/registrar", 10, 3600),
            LimiteCuota("GET /api/v1/tenants", 100, 60),
            LimiteCuota("GET /dashboard/alertas", 30, 60),
            LimiteCuota("WS /ws/alertas", 5, 300),  # WebSocket
        ]
        
        for cuota in cuotas_default:
            self.cuotas_endpoint[cuota.nombre] = cuota
    
    def verificar_limite(self, cliente_id: str, endpoint: str) -> Tuple[bool, str]:
        """Verifica si cliente puede hacer request a endpoint."""
        
        # Obtener cuota
        cuota = self.cuotas_endpoint.get(endpoint)
        if not cuota:
            return True, "Sin límite configurado"
        
        clave_cliente = f"{cliente_id}:{endpoint}"
        ahora = time.time()
        
        # Limpiar requests fuera de ventana
        ventana = self.ventanas_deslizantes[clave_cliente]
        while ventana and ahora - ventana[0] > cuota.ventana_segundos:
            ventana.popleft()
        
        # Verificar si puede hacer request
        if len(ventana) < cuota.requests_max:
            ventana.append(ahora)
            self.estadisticas[clave_cliente]['requests_total'] += 1
            
            if not self.estadisticas[clave_cliente]['timestamp_primer_request']:
                self.estadisticas[clave_cliente]['timestamp_primer_request'] = datetime.now().isoformat()
            
            self.estadisticas[clave_cliente]['timestamp_ultimo_request'] = datetime.now().isoformat()
            
            return True, "Permitido"
        
        self.estadisticas[clave_cliente]['requests_rechazados'] += 1
        
        retry_after = int(ventana[0] + cuota.ventana_segundos - ahora)
        return False, f"Límite excedido. Reinten tar en {retry_after}s"
    
    def obtener_estado_cliente(self, cliente_id: str, 
                              endpoint: str = None) -> Dict:
        """Obtiene estado de límites del cliente."""
        
        if endpoint:
            clave = f"{cliente_id}:{endpoint}"
            ventana = self.ventanas_deslizantes[clave]
            cuota = self.cuotas_endpoint.get(endpoint)
            
            return {
                'cliente_id': cliente_id,
                'endpoint': endpoint,
                'requests_actuales': len(ventana),
                'requests_max': cuota.requests_max if cuota else None,
                'ventana_segundos': cuota.ventana_segundos if cuota else None,
                'estadisticas': self.estadisticas[clave]
            }
        else:
            # Todos los endpoints del cliente
            endpoints_cliente = {
                ep: self.obtener_estado_cliente(cliente_id, ep)
                for ep in self.cuotas_endpoint.keys()
            }
            
            return {
                'cliente_id': cliente_id,
                'endpoints': endpoints_cliente
            }
    
    def registrar_cuota(self, nombre: str, requests_max: int, 
                       ventana_segundos: int):
        """Registra nueva cuota."""
        
        self.cuotas_endpoint[nombre] = LimiteCuota(
            nombre=nombre,
            requests_max=requests_max,
            ventana_segundos=ventana_segundos
        )
    
    def obtener_estadisticas_globales(self) -> Dict:
        """Obtiene estadísticas globales."""
        
        total_requests = sum(
            s['requests_total'] for s in self.estadisticas.values()
        )
        total_rechazados = sum(
            s['requests_rechazados'] for s in self.estadisticas.values()
        )
        
        return {
            'total_requests': total_requests,
            'total_rechazados': total_rechazados,
            'tasa_rechazo': (
                total_rechazados / total_requests * 100 
                if total_requests > 0 else 0
            ),
            'clientes_activos': len(self.estadisticas),
            'endpoints_protegidos': len(self.cuotas_endpoint)
        }


# ═══════════════════════════════════════════════════════════════════════════
# THROTTLER ADAPTATIVO
# ═══════════════════════════════════════════════════════════════════════════

class ThrottlerAdaptativo:
    """Throttler que ajusta límites dinámicamente."""
    
    def __init__(self):
        self.limitador = LimitadorTasa()
        self.umbral_degradacion = 0.3  # Si >30% rechazos, degradar
        self.factor_ajuste = 0.8  # Reducir límites al 80%
    
    def verificar_y_ajustar(self, cliente_id: str, endpoint: str) -> Tuple[bool, str]:
        """Verifica límite y ajusta si necesario."""
        
        permitido, mensaje = self.limitador.verificar_limite(cliente_id, endpoint)
        
        # Comprobar si necesitamos degradar
        stats = self.limitador.obtener_estadisticas_globales()
        
        if stats['tasa_rechazo'] > self.umbral_degradacion * 100:
            logger.warning(
                f"Tasa de rechazo alta ({stats['tasa_rechazo']:.1f}%). "
                f"Considerando degradación."
            )
            
            # Opcionalmente reducir límites
            for cuota in self.limitador.cuotas_endpoint.values():
                cuota.requests_max = int(cuota.requests_max * self.factor_ajuste)
        
        return permitido, mensaje


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_limitador_instance = None


def obtener_limitador_tasa() -> LimitadorTasa:
    """Obtiene instancia singleton."""
    global _limitador_instance
    if _limitador_instance is None:
        _limitador_instance = LimitadorTasa()
    return _limitador_instance


def iniciar_limitador_tasa() -> Dict:
    """Inicializa limitador de tasa."""
    try:
        limitador = obtener_limitador_tasa()
        
        contexto = {
            'estado': 'ACTIVO',
            'endpoints_protegidos': len(limitador.cuotas_endpoint),
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[RATE-LIMIT] Limitador iniciado - "
            f"{contexto['endpoints_protegidos']} endpoints protegidos"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando limitador: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
