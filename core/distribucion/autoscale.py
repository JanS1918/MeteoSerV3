"""
═══════════════════════════════════════════════════════════════════════════════
STEP 26: AUTO-ESCALADO INTELIGENTE
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Escalar automáticamente según carga
  - Monitorear CPU, memoria, conexiones
  - Desescalar cuando la demanda baja
  - Métricas para tomar decisiones

Fecha: 2026-02-11
"""

import logging
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class EstadoEscalado(str, Enum):
    """Estados de escalado."""
    NORMAL = "NORMAL"
    ESCALANDO_UP = "ESCALANDO_UP"
    ESCALANDO_DOWN = "ESCALANDO_DOWN"
    PICO = "PICO"
    BAJO_CARGA = "BAJO_CARGA"


@dataclass
class MetricasNodo:
    """Métricas del nodo actual."""
    cpu_porcentaje: float
    memoria_porcentaje: float
    conexiones_activas: int
    latencia_promedio_ms: float
    requests_por_segundo: float
    tasa_error_porcentaje: float
    timestamp: str


class MonitorMeTriticasSistema:
    """Monitor de métricas del sistema."""
    
    def __init__(self, ventana_promedio_segundos: int = 60):
        self.ventana_promedio_segundos = ventana_promedio_segundos
        self.historial_cpu: List[float] = []
        self.historial_memoria: List[float] = []
        self.historial_rps: List[float] = []
        self.historial_latencia: List[float] = []
        self.historial_errores: List[float] = []
    
    def obtener_metricas_sistema(self) -> MetricasNodo:
        """Obtiene métricas del sistema."""
        
        # CPU y Memoria
        cpu = psutil.cpu_percent(interval=0.1)
        memoria = psutil.virtual_memory().percent
        
        # Conexiones (intento de obtener)
        try:
            # En Linux
            conexiones = len(psutil.net_connections())
        except:
            conexiones = 0
        
        # Actualizar histórico
        self.historial_cpu.append(cpu)
        self.historial_memoria.append(memoria)
        
        # Mantener solo los últimos N segundos
        self._limpiar_historicos()
        
        metricas = MetricasNodo(
            cpu_porcentaje=cpu,
            memoria_porcentaje=memoria,
            conexiones_activas=conexiones,
            latencia_promedio_ms=self._calcular_promedio(
                self.historial_latencia
            ),
            requests_por_segundo=self._calcular_promedio(
                self.historial_rps
            ),
            tasa_error_porcentaje=self._calcular_promedio(
                self.historial_errores
            ),
            timestamp=datetime.now().isoformat()
        )
        
        return metricas
    
    def registrar_latencia(self, latencia_ms: float):
        """Registra latencia de request."""
        self.historial_latencia.append(latencia_ms)
    
    def registrar_rps(self, rps: float):
        """Registra requests por segundo."""
        self.historial_rps.append(rps)
    
    def registrar_error(self, tasa_error: float):
        """Registra tasa de error."""
        self.historial_errores.append(tasa_error)
    
    def _calcular_promedio(self, lista: List[float]) -> float:
        """Calcula promedio."""
        if not lista:
            return 0.0
        return sum(lista) / len(lista)
    
    def _limpiar_historicos(self):
        """Limpia registros antiguos."""
        # Mantener solo los últimos ventana_promedio_segundos registros
        max_registros = self.ventana_promedio_segundos
        
        if len(self.historial_cpu) > max_registros:
            self.historial_cpu = self.historial_cpu[-max_registros:]
        if len(self.historial_memoria) > max_registros:
            self.historial_memoria = self.historial_memoria[-max_registros:]
        if len(self.historial_rps) > max_registros:
            self.historial_rps = self.historial_rps[-max_registros:]
        if len(self.historial_latencia) > max_registros:
            self.historial_latencia = self.historial_latencia[-max_registros:]
        if len(self.historial_errores) > max_registros:
            self.historial_errores = self.historial_errores[-max_registros:]


class GestorAutoEscalado:
    """Gestor de auto-escalado."""
    
    def __init__(self):
        self.monitor = MonitorMeTriticasSistema()
        self.estado_escalado = EstadoEscalado.NORMAL
        
        # Umbrales
        self.umbral_cpu_escalar_up = 80.0      # %
        self.umbral_cpu_escalar_down = 30.0    # %
        self.umbral_memoria_escalar_up = 85.0  # %
        self.umbral_latencia_escalar_up = 200.0 # ms
        self.umbral_tasa_error_escalar_up = 5.0 # %
        
        # Estados previos
        self.ultimo_cambio_estado = datetime.now()
        self.cooldown_escalado_segundos = 60
        
        # Acción pendiente
        self.accion_pendiente: Optional[str] = None
    
    def analizar_y_decidir_escalado(self) -> Dict[str, Any]:
        """Analiza métricas y decide si escalar."""
        
        metricas = self.monitor.obtener_metricas_sistema()
        ahora = datetime.now()
        
        # Verificar cooldown
        tiempo_desde_cambio = (ahora - self.ultimo_cambio_estado).total_seconds()
        en_cooldown = tiempo_desde_cambio < self.cooldown_escalado_segundos
        
        resultado = {
            'metricas': {
                'cpu': f"{metricas.cpu_porcentaje:.1f}%",
                'memoria': f"{metricas.memoria_porcentaje:.1f}%",
                'latencia': f"{metricas.latencia_promedio_ms:.1f}ms",
                'tasa_error': f"{metricas.tasa_error_porcentaje:.1f}%"
            },
            'estado_anterior': self.estado_escalado.value,
            'en_cooldown': en_cooldown,
            'timestamp': metricas.timestamp
        }
        
        if en_cooldown:
            resultado['accion'] = 'NINGUNA (en cooldown)'
            return resultado
        
        # Analizar condiciones para escalar UP
        necesita_escalar_up = (
            metricas.cpu_porcentaje > self.umbral_cpu_escalar_up or
            metricas.memoria_porcentaje > self.umbral_memoria_escalar_up or
            metricas.latencia_promedio_ms > self.umbral_latencia_escalar_up or
            metricas.tasa_error_porcentaje > self.umbral_tasa_error_escalar_up
        )
        
        # Analizar condiciones para escalar DOWN
        necesita_escalar_down = (
            metricas.cpu_porcentaje < self.umbral_cpu_escalar_down and
            metricas.memoria_porcentaje < 50.0 and
            metricas.latencia_promedio_ms < 100.0
        )
        
        # Cambiar estado y registrar acción
        if necesita_escalar_up:
            self.estado_escalado = EstadoEscalado.ESCALANDO_UP
            self.accion_pendiente = 'ESCALAR_UP'
            self.ultimo_cambio_estado = ahora
            resultado['accion'] = 'ESCALAR UP'
            resultado['estado_nuevo'] = self.estado_escalado.value
            resultado['razon'] = self._obtener_razon_escalado(metricas)
            
            logger.warning(
                f"[AUTOSCALE] Escalando UP: {resultado['razon']}"
            )
        
        elif necesita_escalar_down and self.estado_escalado == EstadoEscalado.ESCALANDO_UP:
            self.estado_escalado = EstadoEscalado.ESCALANDO_DOWN
            self.accion_pendiente = 'ESCALAR_DOWN'
            self.ultimo_cambio_estado = ahora
            resultado['accion'] = 'ESCALAR DOWN'
            resultado['estado_nuevo'] = self.estado_escalado.value
            
            logger.info("[AUTOSCALE] Escalando DOWN por carga baja")
        
        else:
            resultado['accion'] = 'NINGUNA'
        
        return resultado
    
    def _obtener_razon_escalado(self, metricas: MetricasNodo) -> str:
        """Obtiene razón del escalado."""
        
        razones = []
        
        if metricas.cpu_porcentaje > self.umbral_cpu_escalar_up:
            razones.append(f"CPU alta ({metricas.cpu_porcentaje:.1f}%)")
        
        if metricas.memoria_porcentaje > self.umbral_memoria_escalar_up:
            razones.append(f"Memoria alta ({metricas.memoria_porcentaje:.1f}%)")
        
        if metricas.latencia_promedio_ms > self.umbral_latencia_escalar_up:
            razones.append(f"Latencia alta ({metricas.latencia_promedio_ms:.1f}ms)")
        
        if metricas.tasa_error_porcentaje > self.umbral_tasa_error_escalar_up:
            razones.append(f"Tasa error alta ({metricas.tasa_error_porcentaje:.1f}%)")
        
        return "; ".join(razones) if razones else "Razón desconocida"
    
    async def ejecutar_accion_escalado(self) -> Dict[str, Any]:
        """Ejecuta acción de escalado pendiente."""
        
        if not self.accion_pendiente:
            return {'estado': 'NINGUNA_ACCION'}
        
        accion = self.accion_pendiente
        self.accion_pendiente = None
        
        try:
            if accion == 'ESCALAR_UP':
                return await self._escalar_up()
            elif accion == 'ESCALAR_DOWN':
                return await self._escalar_down()
            else:
                return {'estado': 'ACCION_DESCONOCIDA'}
        
        except Exception as e:
            logger.error(f"Error ejecutando escalado: {e}")
            return {'estado': 'ERROR', 'detalles': str(e)}
    
    async def _escalar_up(self) -> Dict[str, Any]:
        """Escala hacia arriba."""
        
        logger.warning("[AUTOSCALE] Iniciando escalado UP")
        
        # En una aplicación real, aquí iría:
        # - Agregar workers
        # - Aumentar recursos
        # - Crear nuevos nodos
        
        await asyncio.sleep(1)  # Simular operación
        
        return {
            'accion': 'ESCALAR_UP',
            'estado': 'COMPLETAD0',
            'timestamp': datetime.now().isoformat()
        }
    
    async def _escalar_down(self) -> Dict[str, Any]:
        """Escala hacia abajo."""
        
        logger.info("[AUTOSCALE] Iniciando escalado DOWN")
        
        # En una aplicación real, aquí iría:
        # - Remover workers
        # - Liberar recursos
        # - Consolidar nodos
        
        await asyncio.sleep(1)  # Simular operación
        
        return {
            'accion': 'ESCALAR_DOWN',
            'estado': 'COMPLETADO',
            'timestamp': datetime.now().isoformat()
        }
    
    def obtener_estado_escalado(self) -> Dict[str, Any]:
        """Obtiene estado actual del auto-escalado."""
        
        metricas = self.monitor.obtener_metricas_sistema()
        
        return {
            'estado_actual': self.estado_escalado.value,
            'accion_pendiente': self.accion_pendiente,
            'metricas': {
                'cpu': f"{metricas.cpu_porcentaje:.1f}%",
                'memoria': f"{metricas.memoria_porcentaje:.1f}%",
                'latencia': f"{metricas.latencia_promedio_ms:.1f}ms",
                'rps': f"{metricas.requests_por_segundo:.2f}",
                'tasa_error': f"{metricas.tasa_error_porcentaje:.1f}%"
            },
            'umbrales': {
                'cpu_up': f"{self.umbral_cpu_escalar_up}%",
                'cpu_down': f"{self.umbral_cpu_escalar_down}%",
                'memoria_up': f"{self.umbral_memoria_escalar_up}%",
                'latencia_up': f"{self.umbral_latencia_escalar_up}ms",
                'error_up': f"{self.umbral_tasa_error_escalar_up}%"
            },
            'timestamp': datetime.now().isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_gestor_autoscale_instance = None


def obtener_gestor_autoscale() -> GestorAutoEscalado:
    """Obtiene instancia singleton."""
    global _gestor_autoscale_instance
    if _gestor_autoscale_instance is None:
        _gestor_autoscale_instance = GestorAutoEscalado()
    
    return _gestor_autoscale_instance


def iniciar_autoscale() -> Dict[str, Any]:
    """Inicializa auto-escalado."""
    try:
        gestor = obtener_gestor_autoscale()
        
        contexto = {
            'estado': 'ACTIVO',
            'umbrales': {
                'cpu_up': f"{gestor.umbral_cpu_escalar_up}%",
                'memoria_up': f"{gestor.umbral_memoria_escalar_up}%",
                'latencia_up': f"{gestor.umbral_latencia_escalar_up}ms"
            },
            'cooldown_segundos': gestor.cooldown_escalado_segundos,
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info("[AUTOSCALE] Auto-escalado iniciado")
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando auto-escalado: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
