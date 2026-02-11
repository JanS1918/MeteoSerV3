"""
═══════════════════════════════════════════════════════════════════════════════
STEP 27: PROCESAMIENTO EN LOTE (BATCH PROCESSING)
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Procesar múltiples eventos juntos
  - Reducir overhead de procesamiento individual
  - Optimizar inserciones en BD
  - Mejorar throughput

Fecha: 2026-02-11
"""

import logging
import asyncio
from typing import List, Callable, Optional, Any, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class ConfiguracionBatch:
    """Configuración de batch processing."""
    tamaño_maximo: int = 100          # Máximo de items por batch
    timeout_segundos: int = 30         # Máximo tiempo esperando batch
    max_reintentos: int = 3
    delay_entre_reintentos: float = 1.0


@dataclass
class ResultadoBatch:
    """Resultado del procesamiento de batch."""
    items_procesados: int = 0
    items_exitosos: int = 0
    items_fallidos: int = 0
    errores: List[str] = field(default_factory=list)
    tiempo_ejecucion_ms: float = 0.0
    timestamp: str = ""


class ProcesadorBatch:
    """Procesador genérico de batches."""
    
    def __init__(self,
                 nombre: str,
                 config: ConfiguracionBatch = None):
        
        self.nombre = nombre
        self.config = config or ConfiguracionBatch()
        self.cola_pendiente: deque = deque()
        self.estadisticas = {
            'batches_procesados': 0,
            'items_totales': 0,
            'items_exitosos': 0,
            'items_fallidos': 0,
            'tiempo_total_ms': 0.0
        }
        self._lock = asyncio.Lock()
        self._evento_flush = asyncio.Event()
    
    async def agregar_item(self, item: Any) -> bool:
        """Agrega item a la cola."""
        
        try:
            async with self._lock:
                self.cola_pendiente.append(item)
            
            # Verificar si hay que procesar
            if len(self.cola_pendiente) >= self.config.tamaño_maximo:
                self._evento_flush.set()
            
            return True
        
        except Exception as e:
            logger.error(f"Error agregando item a batch {self.nombre}: {e}")
            return False
    
    async def procesar_lote(self,
                           func_procesamiento: Callable,
                           items: List[Any]) -> ResultadoBatch:
        """Procesa lote de items."""
        
        inicio = datetime.now()
        resultado = ResultadoBatch(timestamp=inicio.isoformat())
        resultado.items_procesados = len(items)
        
        try:
            # Procesar con reintentos
            for intento in range(self.config.max_reintentos):
                try:
                    # Llamar función de procesamiento
                    resp = await func_procesamiento(items) if asyncio.iscoroutinefunction(func_procesamiento) else func_procesamiento(items)
                    
                    # Actualizar resultado
                    if isinstance(resp, dict):
                        resultado.items_exitosos = resp.get('exitosos', len(items))
                        resultado.items_fallidos = resp.get('fallidos', 0)
                        resultado.errores = resp.get('errores', [])
                    else:
                        resultado.items_exitosos = len(items)
                        resultado.items_fallidos = 0
                    
                    break  # Éxito, salir de reintentos
                
                except Exception as e:
                    resultado.errores.append(str(e))
                    
                    if intento < self.config.max_reintentos - 1:
                        logger.warning(
                            f"[BATCH] {self.nombre} intento {intento + 1} falló, "
                            f"reintentando..."
                        )
                        await asyncio.sleep(self.config.delay_entre_reintentos)
                    else:
                        logger.error(
                            f"[BATCH] {self.nombre} falló después de "
                            f"{self.config.max_reintentos} intentos"
                        )
                        resultado.items_fallidos = len(items)
        
        finally:
            # Calcular tiempo
            fin = datetime.now()
            resultado.tiempo_ejecucion_ms = (fin - inicio).total_seconds() * 1000
            
            # Actualizar estadísticas globales
            self.estadisticas['batches_procesados'] += 1
            self.estadisticas['items_totales'] += resultado.items_procesados
            self.estadisticas['items_exitosos'] += resultado.items_exitosos
            self.estadisticas['items_fallidos'] += resultado.items_fallidos
            self.estadisticas['tiempo_total_ms'] += resultado.tiempo_ejecucion_ms
        
        return resultado
    
    async def procesar_pendiente(self,
                                func_procesamiento: Callable) -> Optional[ResultadoBatch]:
        """Procesa items pendientes."""
        
        async with self._lock:
            if len(self.cola_pendiente) == 0:
                return None
            
            # Extraer items
            items = []
            while self.cola_pendiente and len(items) < self.config.tamaño_maximo:
                items.append(self.cola_pendiente.popleft())
        
        # Procesar sin lock
        resultado = await self.procesar_lote(func_procesamiento, items)
        
        logger.info(
            f"[BATCH] {self.nombre}: {resultado.items_exitosos}/"
            f"{resultado.items_procesados} exitosos "
            f"({resultado.tiempo_ejecucion_ms:.1f}ms)"
        )
        
        return resultado
    
    async def procesar_con_timeout(self,
                                  func_procesamiento: Callable,
                                  timeout_segundos: Optional[float] = None):
        """Procesa con timeout, retornando automáticamente."""
        
        timeout = timeout_segundos or self.config.timeout_segundos
        
        try:
            await asyncio.wait_for(
                self._evento_flush.wait(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # Timeout - procesar lo que hay
            pass
        
        # Procesar pendiente
        return await self.procesar_pendiente(func_procesamiento)
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas."""
        
        total = self.estadisticas['items_totales']
        exitosos = self.estadisticas['items_exitosos']
        
        tasa_exito = (exitosos / total * 100) if total > 0 else 0.0
        throughput = (total / self.estadisticas['tiempo_total_ms'] * 1000) if self.estadisticas['tiempo_total_ms'] > 0 else 0.0
        
        return {
            'nombre': self.nombre,
            'batches_procesados': self.estadisticas['batches_procesados'],
            'items_totales': total,
            'items_exitosos': exitosos,
            'items_fallidos': self.estadisticas['items_fallidos'],
            'tasa_exito': f"{tasa_exito:.1f}%",
            'throughput_items_por_segundo': f"{throughput:.2f}",
            'tiempo_total_ms': f"{self.estadisticas['tiempo_total_ms']:.1f}",
            'cola_pendiente': len(self.cola_pendiente),
            'timestamp': datetime.now().isoformat()
        }


class GestorProcesadoresBatch:
    """Gestor central de procesadores batch."""
    
    def __init__(self):
        self.procesadores: Dict[str, ProcesadorBatch] = {}
    
    def crear_procesador(self,
                        nombre: str,
                        config: ConfiguracionBatch = None) -> ProcesadorBatch:
        """Crea nuevo procesador batch."""
        
        if nombre not in self.procesadores:
            procesador = ProcesadorBatch(nombre, config)
            self.procesadores[nombre] = procesador
            logger.info(f"[BATCH] Procesador creado: {nombre}")
        
        return self.procesadores[nombre]
    
    def obtener_procesador(self, nombre: str) -> Optional[ProcesadorBatch]:
        """Obtiene procesador existente."""
        return self.procesadores.get(nombre)
    
    def obtener_estadisticas_global(self) -> Dict[str, Any]:
        """Obtiene estadísticas de todos los procesadores."""
        
        estadisticas = {}
        
        for nombre, procesador in self.procesadores.items():
            estadisticas[nombre] = procesador.obtener_estadisticas()
        
        return {
            'procesadores_activos': len(self.procesadores),
            'procesadores': estadisticas,
            'timestamp': datetime.now().isoformat()
        }


# Procesadores predefinidos para casos comunes

class ProcesadorAlertas(ProcesadorBatch):
    """Procesador especializado para alertas."""
    
    def __init__(self):
        super().__init__(
            nombre="alertas",
            config=ConfiguracionBatch(
                tamaño_maximo=100,
                timeout_segundos=10
            )
        )
    
    async def procesar_lote_alertas(self,
                                    alertas: List[Dict]) -> Dict[str, Any]:
        """Procesa lote de alertas."""
        
        # En una aplicación real, aquí iría inserción en BD, etc.
        exitosos = len(alertas)
        fallidos = 0
        
        logger.info(f"[BATCH] Procesadas {exitosos} alertas en lote")
        
        return {
            'exitosos': exitosos,
            'fallidos': fallidos,
            'errores': []
        }


class ProcesadorWebhooks(ProcesadorBatch):
    """Procesador especializado para entregas de webhooks."""
    
    def __init__(self):
        super().__init__(
            nombre="webhooks",
            config=ConfiguracionBatch(
                tamaño_maximo=50,
                timeout_segundos=20
            )
        )


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_gestor_batch_instance = None


def obtener_gestor_batch() -> GestorProcesadoresBatch:
    """Obtiene instancia singleton."""
    global _gestor_batch_instance
    if _gestor_batch_instance is None:
        _gestor_batch_instance = GestorProcesadoresBatch()
    
    return _gestor_batch_instance


def iniciar_procesadores_batch() -> Dict[str, Any]:
    """Inicializa procesadores batch predefinidos."""
    try:
        gestor = obtener_gestor_batch()
        
        # Crear procesadores predefinidos
        gestor.crear_procesador("alertas", ConfiguracionBatch(100, 10))
        gestor.crear_procesador("webhooks", ConfiguracionBatch(50, 20))
        gestor.crear_procesador("auditoria", ConfiguracionBatch(200, 30))
        
        contexto = {
            'estado': 'ACTIVO',
            'procesadores_iniciales': 3,
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info("[BATCH] Procesadores batch iniciados")
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando batch: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
