import logging
import queue
import threading
from typing import Any, Optional, Dict
"""
BUS ASYNC WRITER - Escritura Lock-Free sin Contención
======================================================
Sistema de escritura asincrónica en el Bus usando Queue.

Arquitectura:
- Cola (Queue): Thread-safe, sin locks manuales
- Worker thread: Un único escribidor, sin contención
- Non-blocking: publicar() retorna inmediatamente

Beneficio:
- 100 threads escribiendo = 0 contención
- latencia de publicar() = O(1) constant
"""

from queue import Queue, Full
from threading import Thread
import time
from typing import Any, Callable, Optional
from collections import deque


class BusAsyncWriter:
    """
    Escritor asincrónico del Bus sin locks de contención
    
    100 threads pueden publicar() sin esperar a otros.
    Un worker thread procesa internamente de forma ordenada.
    """
    
    def __init__(self, tamaño_cola: int = 10000, 
                 callback_lleno: Optional[Callable] = None):
        """
        Args:
            tamaño_cola: Máximo de escrituras pendientes
            callback_lleno: Se llama si cola se llena (overflow)
        """
        self.cola = Queue(maxsize=tamaño_cola)
        self.bus_almacenamiento: dict = {}
        self.worker_thread = None
        self.activo = False
        
        # Estadísticas
        self.escrituras_procesadas = 0
        self.escrituras_rechazadas = 0
        self.cola_max_tamaño_visto = 0
        self.callback_lleno = callback_lleno
    
    def iniciar(self):
        """Inicia el worker thread"""
        if self.activo:
            return
        
        self.activo = True
        self.worker_thread = Thread(
            target=self._procesar_cola,
            daemon=True,
            name="BusAsyncWriter"
        )
        self.worker_thread.start()
    
    def detener(self):
        """Detiene el worker y procesa escrituras pendientes"""
        self.activo = False
        
        # Procesar cola pendiente
        while not self.cola.empty():
            try:
                clave, valor = self.cola.get_nowait()
                self.bus_almacenamiento[clave] = valor
                self.escrituras_procesadas += 1
            except:
                break
        
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def publicar(self, clave: str, valor: Any, timeout: float = 0.0) -> bool:
        """
        Publica dato en el Bus (NON-BLOCKING)
        
        Args:
            clave: Identificador del dato
            valor: Valor a almacenar
            timeout: Tiempo máximo de espera (0 = no espera)
        
        Returns:
            True si publicó, False si cola llena (overflow)
        """
        if not self.activo:
            return False
        
        try:
            self.cola.put((clave, valor), timeout=timeout)
            return True
        
        except Full:
            self.escrituras_rechazadas += 1
            
            # Notificar si hay callback
            if self.callback_lleno:
                self.callback_lleno(clave, valor)
            
            return False
    
    def obtener(self, clave: str) -> Optional[Any]:
        """Obtiene valor actual (O(1))"""
        return self.bus_almacenamiento.get(clave)
    
    def _procesar_cola(self):
        """
        Worker thread que procesa cola (no hay contención)
        
        - Un solo thread accede a bus_almacenamiento
        - No hay locks, no hay wait/notify
        - Throughput limitado solo por CPU, no por sincronización
        """
        while self.activo:
            try:
                # Esperar próximo elemento (timeout para poder cerrar limpiamente)
                clave, valor = self.cola.get(timeout=0.1)
                
                # Escribir sin contención (soy el único writer)
                self.bus_almacenamiento[clave] = valor
                self.escrituras_procesadas += 1
                
                # Estadística
                tamaño_actual = self.cola.qsize()
                if tamaño_actual > self.cola_max_tamaño_visto:
                    self.cola_max_tamaño_visto = tamaño_actual
                
                self.cola.task_done()
            
            except queue.Empty:
                # Timeout esperado - continuar sin datos esta iteración
                pass
            except Exception as e:
                # ERROR CRÍTICO: La cola ha fallado o hay corrupción de datos
                logging.error(f"🚨 ERROR CRÍTICO en bus_async_writer.proceso(): {type(e).__name__}: {e}", exc_info=True)
                self.escrituras_rechazadas += 1
                # No romper el loop - reintentar en siguiente iteración
    
    def obtener_estadisticas(self) -> dict:
        """Estadísticas de desempeño del writer"""
        return {
            'activo': self.activo,
            'escrituras_procesadas': self.escrituras_procesadas,
            'escrituras_rechazadas': self.escrituras_rechazadas,
            'cola_actual': self.cola.qsize(),
            'cola_max_tamaño_visto': self.cola_max_tamaño_visto,
            'total_datos_en_bus': len(self.bus_almacenamiento),
            'eficiencia': (self.escrituras_procesadas / 
                          (self.escrituras_procesadas + self.escrituras_rechazadas)
                          if (self.escrituras_procesadas + self.escrituras_rechazadas) > 0
                          else 0)
        }
    
    def limpiar_bus(self):
        """Limpia almacenamiento (cuidado, pierde datos)"""
        self.bus_almacenamiento.clear()
    
    def obtener_todas_variables(self) -> dict:
        """Retorna snapshot completo del Bus"""
        return dict(self.bus_almacenamiento)


class WriterConIntento:
    """
    Versión mejorada: Reintentos con backoff exponencial
    """
    
    def __init__(self, writer: BusAsyncWriter, max_reintentos: int = 3):
        self.writer = writer
        self.max_reintentos = max_reintentos
    
    def publicar_con_reintentos(self, clave: str, valor: Any) -> bool:
        """
        Publica con reintentos exponenciales
        
        Si cola está llena, reintenta después de tiempo exponencial
        """
        for intento in range(self.max_reintentos):
            if self.writer.publicar(clave, valor, timeout=0.1):
                return True
            
            # Backoff exponencial: 10ms, 20ms, 40ms
            tiempo_espera = 0.01 * (2 ** intento)
            time.sleep(tiempo_espera)
        
        return False


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║        BUS ASYNC WRITER - Escritura Sin Contención         ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Ejemplo de uso:
    
        writer = BusAsyncWriter(tamaño_cola=10000)
        writer.iniciar()
        
        # 100 threads pueden publicar sin esperar
        for i in range(100):
            writer.publicar(f"variable_{i}", valor_i)
        
        # Acceso O(1)
        valor = writer.obtener("variable_0")
        
        # Estadísticas
        stats = writer.obtener_estadisticas()
        # {
        #   'escrituras_procesadas': 100,
        #   'cola_actual': 0,
        #   'eficiencia': 1.0
        # }
        
        # Al cerrar
        writer.detener()
    """)
