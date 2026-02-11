"""
═══════════════════════════════════════════════════════════════════════════════
STEP 29: RECUPERACIÓN DE FALLOS Y FAILOVER
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Recuperación automática de servicios
  - Failover a réplicas
  - Health checks periódicos
  - Reintentos inteligentes

Fecha: 2026-02-11
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EstadoServicio(str, Enum):
    """Estados de un servicio."""
    SALUDABLE = "SALUDABLE"
    DEGRADADO = "DEGRADADO"
    NO_DISPONIBLE = "NO_DISPONIBLE"
    RECUPERÁNDOSE = "RECUPERÁNDOSE"


@dataclass
class ConfiguracionHealthCheck:
    """Configuración de health check."""
    intervalo_segundos: int = 30
    timeout_segundos: int = 5
    max_fallos_consecutivos: int = 3
    reintentos_recuperacion: int = 5


@dataclass
class RegistroSalud:
    """Registro de salud de servicio."""
    nombre_servicio: str
    estado: EstadoServicio
    ultimo_check: str
    fallos_consecutivos: int = 0
    exitos_consecutivos: int = 0
    tiempo_recuperacion_estimado: str = ""


class VerificadorSalud:
    """Verifica salud de servicios."""
    
    def __init__(self, nombre_servicio: str,
                 func_health_check: Callable,
                 config: ConfiguracionHealthCheck = None):
        
        self.nombre_servicio = nombre_servicio
        self.func_health_check = func_health_check
        self.config = config or ConfiguracionHealthCheck()
        
        self.registro_salud = RegistroSalud(
            nombre_servicio=nombre_servicio,
            estado=EstadoServicio.RECUPERÁNDOSE
        )
        
        self._tarea_check = None
        self._activo = False
    
    async def realizar_check(self) -> bool:
        """Realiza verificación de salud."""
        
        try:
            # Ejecutar health check con timeout
            resultado = await asyncio.wait_for(
                self.func_health_check(),
                timeout=self.config.timeout_segundos
            )
            
            # Actualizar registro
            if resultado:
                self.registro_salud.exitos_consecutivos += 1
                self.registro_salud.fallos_consecutivos = 0
                
                # Cambiar estado si recuperado
                if self.registro_salud.estado in [
                    EstadoServicio.DEGRADADO,
                    EstadoServicio.NO_DISPONIBLE,
                    EstadoServicio.RECUPERÁNDOSE
                ]:
                    self.registro_salud.estado = EstadoServicio.SALUDABLE
                    logger.info(
                        f"[HEALTH] {self.nombre_servicio} "
                        f"recuperado a SALUDABLE"
                    )
            else:
                self.registro_salud.fallos_consecutivos += 1
                self.registro_salud.exitos_consecutivos = 0
                
                # Cambiar estado si hay demasiados fallos
                if self.registro_salud.fallos_consecutivos >= self.config.max_fallos_consecutivos:
                    estado_anterior = self.registro_salud.estado
                    self.registro_salud.estado = EstadoServicio.NO_DISPONIBLE
                    
                    if estado_anterior != EstadoServicio.NO_DISPONIBLE:
                        logger.error(
                            f"[HEALTH] {self.nombre_servicio} "
                            f"marcado como NO_DISPONIBLE"
                        )
            
            self.registro_salud.ultimo_check = datetime.now().isoformat()
            return resultado
        
        except asyncio.TimeoutError:
            self.registro_salud.fallos_consecutivos += 1
            self.registro_salud.estado = EstadoServicio.DEGRADADO
            self.registro_salud.ultimo_check = datetime.now().isoformat()
            
            logger.warning(
                f"[HEALTH] {self.nombre_servicio} "
                f"timeout en health check"
            )
            return False
        
        except Exception as e:
            self.registro_salud.fallos_consecutivos += 1
            self.registro_salud.estado = EstadoServicio.DEGRADADO
            self.registro_salud.ultimo_check = datetime.now().isoformat()
            
            logger.error(
                f"[HEALTH] {self.nombre_servicio} "
                f"error en check: {e}"
            )
            return False
    
    async def iniciar_monitoreo(self):
        """Inicia monitoreo continuo."""
        
        self._activo = True
        
        while self._activo:
            await self.realizar_check()
            await asyncio.sleep(self.config.intervalo_segundos)
    
    def detener_monitoreo(self):
        """Detiene monitoreo."""
        self._activo = False
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Obtiene estado actual."""
        
        return {
            'nombre_servicio': self.nombre_servicio,
            'estado': self.registro_salud.estado.value,
            'ultimo_check': self.registro_salud.ultimo_check,
            'fallos_consecutivos': self.registro_salud.fallos_consecutivos,
            'exitos_consecutivos': self.registro_salud.exitos_consecutivos,
            'es_saludable': self.registro_salud.estado == EstadoServicio.SALUDABLE
        }


class GestorRecuperacion:
    """Gestor de recuperación y failover."""
    
    def __init__(self):
        self.verificadores: Dict[str, VerificadorSalud] = {}
        self.replicas_por_servicio: Dict[str, List[str]] = {}
        self.historico_fallos: List[Dict[str, Any]] = []
    
    def registrar_servicio(self,
                          nombre_servicio: str,
                          func_health_check: Callable,
                          replicas: List[str] = None,
                          config: ConfiguracionHealthCheck = None):
        """Registra servicio para monitoreo."""
        
        verificador = VerificadorSalud(
            nombre_servicio,
            func_health_check,
            config
        )
        
        self.verificadores[nombre_servicio] = verificador
        
        if replicas:
            self.replicas_por_servicio[nombre_servicio] = replicas
        
        logger.info(
            f"[FAILOVER] Servicio registrado: {nombre_servicio} "
            f"(replicas: {len(replicas) if replicas else 0})"
        )
    
    async def iniciar_monitoreo_global(self):
        """Inicia monitoreo de todos los servicios."""
        
        tareas = [
            verificador.iniciar_monitoreo()
            for verificador in self.verificadores.values()
        ]
        
        await asyncio.gather(*tareas)
    
    async def ejecutar_failover(self, nombre_servicio: str) -> bool:
        """Ejecuta failover a réplica."""
        
        replicas = self.replicas_por_servicio.get(nombre_servicio, [])
        
        if not replicas:
            logger.error(
                f"[FAILOVER] No hay replicas para {nombre_servicio}"
            )
            return False
        
        logger.warning(
            f"[FAILOVER] Iniciando failover de {nombre_servicio} "
            f"a {len(replicas)} replicas"
        )
        
        # Registrar fallo
        self.historico_fallos.append({
            'servicio': nombre_servicio,
            'timestamp': datetime.now().isoformat(),
            'replicas_disponibles': len(replicas)
        })
        
        # En una aplicación real aquí iría:
        # - Redirigir tráfico a réplica
        # - Actualizar DNS/load balancer
        # - Notificar a usuarios
        
        await asyncio.sleep(1)  # Simular failover
        
        logger.info(
            f"[FAILOVER] Failover completado para {nombre_servicio}"
        )
        
        return True
    
    async def ejecutar_recuperacion_gradual(self,
                                           nombre_servicio: str) -> bool:
        """Ejecuta recuperación gradual de servicio."""
        
        verificador = self.verificadores.get(nombre_servicio)
        
        if not verificador:
            return False
        
        logger.info(
            f"[RECOVERY] Iniciando recuperación de {nombre_servicio}"
        )
        
        # Reintentar conectar con backoff exponencial
        for intento in range(
            verificador.config.reintentos_recuperacion
        ):
            resultado = await verificador.realizar_check()
            
            if resultado:
                logger.info(
                    f"[RECOVERY] {nombre_servicio} recuperado "
                    f"en intento {intento + 1}"
                )
                return True
            
            # Espera exponencial
            espera = min(2 ** intento, 60)  # Máximo 60 segundos
            
            logger.warning(
                f"[RECOVERY] {nombre_servicio} reintentando "
                f"en {espera}s (intento {intento + 1}/"
                f"{verificador.config.reintentos_recuperacion})"
            )
            
            await asyncio.sleep(espera)
        
        logger.error(
            f"[RECOVERY] {nombre_servicio} no pudo recuperarse"
        )
        
        return False
    
    def obtener_estado_global(self) -> Dict[str, Any]:
        """Obtiene estado de todos los servicios."""
        
        servicios = {}
        
        for nombre, verificador in self.verificadores.items():
            servicios[nombre] = verificador.obtener_estado()
        
        # Contar estados
        saludables = sum(
            1 for s in servicios.values()
            if s['es_saludable']
        )
        
        total = len(servicios)
        
        return {
            'servicios_total': total,
            'servicios_saludables': saludables,
            'servicios_degradados': total - saludables,
            'salud_general': f"{saludables/total*100:.1f}%" if total > 0 else "N/A",
            'servicios': servicios,
            'fallos_registrados': len(self.historico_fallos),
            'timestamp': datetime.now().isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_gestor_recuperacion_instance = None


def obtener_gestor_recuperacion() -> GestorRecuperacion:
    """Obtiene instancia singleton."""
    global _gestor_recuperacion_instance
    if _gestor_recuperacion_instance is None:
        _gestor_recuperacion_instance = GestorRecuperacion()
    
    return _gestor_recuperacion_instance


async def iniciar_failover_recovery() -> Dict[str, Any]:
    """Inicializa sistema de failover."""
    try:
        gestor = obtener_gestor_recuperacion()
        
        # Health check dummy para demostración
        async def health_check_dummy():
            return True
        
        # Registrar servicios críticos
        servicios_criticos = [
            'api_alertas',
            'base_datos',
            'redis_cache'
        ]
        
        for servicio in servicios_criticos:
            gestor.registrar_servicio(
                servicio,
                health_check_dummy,
                replicas=[f'{servicio}-replica-1', f'{servicio}-replica-2'],
                config=ConfiguracionHealthCheck(
                    intervalo_segundos=30,
                    max_fallos_consecutivos=3
                )
            )
        
        contexto = {
            'estado': 'ACTIVO',
            'servicios_monitoreados': len(servicios_criticos),
            'config': {
                'intervalo_check': '30s',
                'max_fallos_antes_failover': 3
            },
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info("[FAILOVER] Sistema de failover iniciado")
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando failover: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
