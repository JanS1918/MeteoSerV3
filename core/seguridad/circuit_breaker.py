"""
═══════════════════════════════════════════════════════════════════════════════
STEP 23: CIRCUIT BREAKER Y RESILIENCIA
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Evitar cascadas de fallos
  - Estados: CERRADO, ABIERTO, SEMIABIERTO
  - Recuperación automática
  - Degradación elegante

Fecha: 2026-02-11
"""

import logging
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class EstadoCircuito(str, Enum):
    """Estados del circuit breaker."""
    CERRADO = "CERRADO"           # Normal
    ABIERTO = "ABIERTO"           # Fallo, bloqueando
    SEMIABIERTO = "SEMIABIERTO"   # Recuperándose


@dataclass
class EstadisticasCircuito:
    """Estadísticas del circuito."""
    total_llamadas: int = 0
    llamadas_exitosas: int = 0
    llamadas_fallidas: int = 0
    tasa_exito: float = 0.0
    ultimo_cambio_estado: str = ""
    tiempo_abierto_segundos: int = 0


class CircuitBreaker:
    """Implementa patrón circuit breaker."""
    
    def __init__(self,
                 nombre: str,
                 umbral_fallo: float = 0.5,    # 50% fallos
                 timeout_recuperacion: int = 60):  # 60 segundos
        
        self.nombre = nombre
        self.umbral_fallo = umbral_fallo
        self.timeout_recuperacion = timeout_recuperacion
        
        self.estado = EstadoCircuito.CERRADO
        self.estadisticas = EstadisticasCircuito()
        self.tiempo_ultimo_fallo: Optional[datetime] = None
    
    def puede_ejecutar(self) -> bool:
        """Verifica si la llamada puede ejecutarse."""
        
        if self.estado == EstadoCircuito.CERRADO:
            return True
        
        if self.estado == EstadoCircuito.ABIERTO:
            # Verificar si ya pasó el timeout de recuperación
            if self.tiempo_ultimo_fallo:
                tiempo_transcurrido = (datetime.now() - self.tiempo_ultimo_fallo).total_seconds()
                if tiempo_transcurrido > self.timeout_recuperacion:
                    logger.info(f"[CB] {self.nombre} transitando a SEMIABIERTO")
                    self.estado = EstadoCircuito.SEMIABIERTO
                    return True
            
            return False
        
        if self.estado == EstadoCircuito.SEMIABIERTO:
            return True
        
        return False
    
    async def ejecutar(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta función protegida por circuit breaker."""
        
        if not self.puede_ejecutar():
            raise Exception(
                f"[CB] {self.nombre} abierto. "
                f"Degradación elegante activada."
            )
        
        try:
            resultado = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._registrar_exito()
            return resultado
        
        except Exception as e:
            self._registrar_fallo()
            raise
    
    def _registrar_exito(self):
        """Registra llamada exitosa."""
        
        self.estadisticas.total_llamadas += 1
        self.estadisticas.llamadas_exitosas += 1
        
        # Actualizar tasa de éxito
        self.estadisticas.tasa_exito = (
            self.estadisticas.llamadas_exitosas /
            self.estadisticas.total_llamadas
        )
        
        # Si estábamos en SEMIABIERTO, cerrar circuito
        if self.estado == EstadoCircuito.SEMIABIERTO:
            logger.info(f"[CB] {self.nombre} cerrando (recuperado)")
            self.estado = EstadoCircuito.CERRADO
            self.estadisticas.ultimo_cambio_estado = datetime.now().isoformat()
    
    def _registrar_fallo(self):
        """Registra llamada fallida."""
        
        self.estadisticas.total_llamadas += 1
        self.estadisticas.llamadas_fallidas += 1
        self.tiempo_ultimo_fallo = datetime.now()
        
        # Actualizar tasa de éxito
        self.estadisticas.tasa_exito = (
            self.estadisticas.llamadas_exitosas /
            self.estadisticas.total_llamadas
        ) if self.estadisticas.total_llamadas > 0 else 0.0
        
        # Verificar si hay que abrir el circuito
        if self.estadisticas.tasa_exito < (1 - self.umbral_fallo):
            logger.warning(
                f"[CB] {self.nombre} abierto ("
                f"tasa exito: {self.estadisticas.tasa_exito:.1%})"
            )
            self.estado = EstadoCircuito.ABIERTO
            self.estadisticas.ultimo_cambio_estado = datetime.now().isoformat()
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Obtiene estado actual del circuito."""
        
        return {
            'nombre': self.nombre,
            'estado': self.estado.value,
            'estadisticas': {
                'total_llamadas': self.estadisticas.total_llamadas,
                'exitosas': self.estadisticas.llamadas_exitosas,
                'fallidas': self.estadisticas.llamadas_fallidas,
                'tasa_exito': f"{self.estadisticas.tasa_exito:.1%}"
            },
            'config': {
                'umbral_fallo': f"{self.umbral_fallo:.1%}",
                'timeout_recuperacion': f"{self.timeout_recuperacion}s"
            },
            'timestamp': datetime.now().isoformat()
        }


class GestorCircuitBreakers:
    """Gestor central de circuit breakers."""
    
    def __init__(self):
        self.circuitos: Dict[str, CircuitBreaker] = {}
    
    def crear_circuito(self, nombre: str,
                      umbral_fallo: float = 0.5,
                      timeout_recuperacion: int = 60) -> CircuitBreaker:
        """Crea nuevo circuit breaker."""
        
        if nombre in self.circuitos:
            return self.circuitos[nombre]
        
        circuito = CircuitBreaker(
            nombre=nombre,
            umbral_fallo=umbral_fallo,
            timeout_recuperacion=timeout_recuperacion
        )
        
        self.circuitos[nombre] = circuito
        logger.info(f"[CB] Circuito creado: {nombre}")
        
        return circuito
    
    async def ejecutar_con_CB(self, nombre_CB: str,
                             func: Callable,
                             fallback: Optional[Callable] = None,
                             *args, **kwargs) -> Any:
        """Ejecuta función con circuit breaker."""
        
        circuito = self.circuitos.get(nombre_CB)
        if not circuito:
            # Crear si no existe
            circuito = self.crear_circuito(nombre_CB)
        
        try:
            return await circuito.ejecutar(func, *args, **kwargs)
        
        except Exception as e:
            logger.warning(
                f"[CB] {nombre_CB} falló: {e}. "
                f"Intentando fallback..."
            )
            
            if fallback:
                try:
                    return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
                except Exception as fb_error:
                    logger.error(f"[CB] Fallback también falló: {fb_error}")
                    raise
            else:
                raise
    
    def obtener_estado_global(self) -> Dict[str, Any]:
        """Obtiene estado de todos los circuitos."""
        
        circuitos_info = {}
        para_abrir = 0
        para_cerrar = 0
        
        for nombre, circuito in self.circuitos.items():
            info = circuito.obtener_estado()
            circuitos_info[nombre] = info
            
            if circuito.estado == EstadoCircuito.ABIERTO:
                para_abrir += 1
            elif circuito.estado == EstadoCircuito.CERRADO:
                para_cerrar += 1
        
        return {
            'total_circuitos': len(self.circuitos),
            'abiertos': para_abrir,
            'cerrados': para_cerrar,
            'circuitos': circuitos_info,
            'timestamp': datetime.now().isoformat()
        }
    
    def resetear_circuito(self, nombre: str) -> bool:
        """Resetea estadísticas de un circuito."""
        
        if nombre in self.circuitos:
            self.circuitos[nombre].estado = EstadoCircuito.CERRADO
            self.circuitos[nombre].estadisticas = EstadisticasCircuito()
            logger.info(f"[CB] Circuito reseteado: {nombre}")
            return True
        
        return False


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

from typing import Dict, List

_gestor_cb_instance = None


def obtener_gestor_circuit_breakers() -> GestorCircuitBreakers:
    """Obtiene instancia singleton."""
    global _gestor_cb_instance
    if _gestor_cb_instance is None:
        _gestor_cb_instance = GestorCircuitBreakers()
    
    return _gestor_cb_instance


def iniciar_circuit_breakers() -> Dict[str, Any]:
    """Inicializa circuit breakers predefinidos."""
    try:
        gestor = obtener_gestor_circuit_breakers()
        
        # Crear circuitos para servicios críticos
        servicios = [
            ('api_alertas', 0.4, 30),
            ('api_webhooks', 0.5, 60),
            ('base_datos', 0.3, 90),
            ('redis_cache', 0.4, 45),
            ('notificaciones', 0.5, 60),
        ]
        
        for nombre, umbral, timeout in servicios:
            gestor.crear_circuito(nombre, umbral, timeout)
        
        logger.info(f"[CB] {len(servicios)} circuitos creados")
        
        return {
            'estado': 'ACTIVO',
            'circuitos_creados': len(servicios),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error iniciando circuit breakers: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
