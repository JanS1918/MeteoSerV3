import logging
"""
MeteoSer AI Orchestrator - Núcleo Central
==========================================

Orquestador principal que coordina todos los subsistemas de IA.
- Loop asíncrono para operaciones no bloqueantes
- Gestión de eventos del Bus
- Coordinación entre módulos
- Políticas de seguridad y validación
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
import threading

logger = logging.getLogger(__name__)


@dataclass
class AITask:
    """Tarea para el orquestador"""
    id: str
    name: str
    priority: int  # 1-10, mayor = más prioritario
    callback: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    scheduled_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)  # Metadatos adicionales de la tarea


class AIOrchestrator:
    """
    Orquestador principal de la IA de MeteoSer.
    
    Coordina todos los subsistemas:
    - Knowledge Manager
    - Code Generator
    - Auto Heal Engine
    - Updater Engine
    - Dialog Manager
    - Contract Parser
    - Explainer
    """
    
    def __init__(self, bus=None):
        self.bus = bus
        self.running = False
        self.tasks: List[AITask] = []
        self.task_queue = self.tasks  # Alias para compatibilidad
        self.subsystems = {}
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "uptime_start": time.time(),
            "last_health_check": time.time(),
        }
        self._lock = threading.Lock()
        self._loop = None
        self._thread = None
        self._async_task: Optional[asyncio.Task] = None
        
        logger.info("🧠 AIOrchestrator inicializado")
    
    def register_subsystem(self, name: str, instance: Any) -> None:
        """Registra un subsistema en el orquestador"""
        with self._lock:
            self.subsystems[name] = instance
            logger.info(f"✅ Subsistema registrado: {name}")
    
    def set_bus(self, bus) -> None:
        """Registra la instancia del Bus"""
        self.bus = bus
        if bus:
            # Publicar metadatos de IA al Bus
            self.bus.publicar("ai_orchestrator_status", "active", "estado")
            self.bus.publicar("ai_orchestrator_version", "1.0.0", "version")
            self.bus.publicar("ai_orchestrator_start_time", datetime.now().isoformat(), "timestamp")
            logger.info("✅ Bus registrado en AIOrchestrator")
    
    def schedule_task(self, name: str, callback: Callable, priority: int = 5, 
                     *args, metadata: Optional[Dict] = None, **kwargs) -> str:
        """Programa una tarea para ejecución
        
        Args:
            name: Nombre de la tarea
            callback: Función callback a ejecutar
            priority: Prioridad (1-10, mayor = más prioritario)
            *args: Argumentos posicionales
            metadata: Dict opcional con metadatos de la tarea
            **kwargs: Argumentos nombrados
        """
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = AITask(
            id=task_id,
            name=name,
            priority=priority,
            callback=callback,
            args=args,
            kwargs=kwargs,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.tasks.append(task)
            # Ordenar por prioridad (mayor primero)
            self.tasks.sort(key=lambda t: t.priority, reverse=True)
        
        logger.info(f"📋 Tarea programada: {name} (id={task_id}, priority={priority})")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Obtiene el estado de una tarea"""
        with self._lock:
            for task in self.tasks:
                if task.id == task_id:
                    return {
                        "id": task.id,
                        "name": task.name,
                        "status": task.status,
                        "result": task.result,
                        "error": task.error,
                    }
        return None
    
    async def _process_tasks(self) -> None:
        """Procesa tareas en cola (loop asíncrono)"""
        while self.running:
            task = None
            with self._lock:
                # Buscar tarea de mayor prioridad en cola
                pending = [t for t in self.tasks if t.status == "pending"]
                if pending:
                    task = pending[0]
                    task.status = "running"
            
            if task:
                try:
                    logger.info(f"▶️ Ejecutando tarea: {task.name}")
                    # Ejecutar callback
                    if asyncio.iscoroutinefunction(task.callback):
                        result = await task.callback(*task.args, **task.kwargs)
                    else:
                        result = task.callback(*task.args, **task.kwargs)
                    
                    task.result = result
                    task.status = "completed"
                    self.metrics["tasks_completed"] += 1
                    logger.info(f"✅ Tarea completada: {task.name}")
                    
                except Exception as e:
                    task.status = "failed"
                    task.error = str(e)
                    self.metrics["tasks_failed"] += 1
                    logger.error(f"❌ Error en tarea {task.name}: {e}")
            else:
                # Sin tareas, esperar un poco
                await asyncio.sleep(0.1)
    
    async def _health_check(self) -> None:
        """Chequeo periódico de salud del sistema"""
        while self.running:
            await asyncio.sleep(30)  # Cada 30 segundos
            
            self.metrics["last_health_check"] = time.time()
            
            # Publicar métricas al Bus
            if self.bus:
                self.bus.publicar("ai_tasks_completed", self.metrics["tasks_completed"], "count")
                self.bus.publicar("ai_tasks_failed", self.metrics["tasks_failed"], "count")
                uptime = time.time() - self.metrics["uptime_start"]
                self.bus.publicar("ai_uptime_seconds", uptime, "s")
            
            logger.debug(f"💓 Health check: {len(self.tasks)} tareas, "
                        f"{self.metrics['tasks_completed']} completadas")
    
    async def _main_loop(self) -> None:
        """Loop principal asíncrono"""
        logger.info("🚀 AIOrchestrator loop iniciado")
        
        # Lanzar tareas en paralelo
        await asyncio.gather(
            self._process_tasks(),
            self._health_check(),
        )
    
    async def start(self) -> None:
        """Inicia el orquestador (versión async)"""
        if self.running:
            logger.warning("⚠️ AIOrchestrator ya está ejecutándose")
            return
        
        self.running = True
        self._async_task = asyncio.create_task(self._main_loop())
        logger.info("🧠 AIOrchestrator iniciado exitosamente")
    
    def start_sync(self) -> None:
        """Inicia el orquestador en un thread separado (versión sync)"""
        if self.running:
            logger.warning("⚠️ AIOrchestrator ya está ejecutándose")
            return
        
        self.running = True
        
        def _run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self._main_loop())
            finally:
                self._loop.close()
        
        self._thread = threading.Thread(target=_run_loop, daemon=True, name="AIOrchestrator")
        self._thread.start()
        
        logger.info("🧠 AIOrchestrator iniciado exitosamente")
    
    async def stop(self) -> None:
        """Detiene el orquestador (versión async)"""
        if not self.running:
            return
        
        logger.info("🛑 Deteniendo AIOrchestrator...")
        self.running = False
        
        if self._async_task and not self._async_task.done():
            self._async_task.cancel()
            try:
                await self._async_task
            except asyncio.CancelledError:
                logging.exception("Silent except at 238 - revisar contexto")
        
        self._async_task = None
        
        if self.bus:
            self.bus.publicar("ai_orchestrator_status", "stopped", "estado")
        
        logger.info("✅ AIOrchestrator detenido")
    
    def stop_sync(self) -> None:
        """Detiene el orquestador (versión sync)"""
        if not self.running:
            return
        
        logger.info("🛑 Deteniendo AIOrchestrator...")
        self.running = False
        
        if self._thread:
            self._thread.join(timeout=5)
        
        if self.bus:
            self.bus.publicar("ai_orchestrator_status", "stopped", "estado")
        
        logger.info("✅ AIOrchestrator detenido")
    
    def get_metrics(self) -> Dict:
        """Retorna métricas del orquestador"""
        uptime = time.time() - self.metrics["uptime_start"]
        return {
            "status": "running" if self.running else "stopped",
            "uptime_seconds": uptime,
            "uptime": uptime,  # Alias para uptime_seconds
            "tasks_total": len(self.tasks),
            "tasks_pending": len([t for t in self.tasks if t.status == "pending"]),
            "tasks_running": len([t for t in self.tasks if t.status == "running"]),
            "tasks_completed": self.metrics["tasks_completed"],
            "tasks_failed": self.metrics["tasks_failed"],
            "subsystems_count": len(self.subsystems),
            "subsystems": list(self.subsystems.keys()),
        }
    
    def get_status(self) -> Dict:
        """Retorna estado completo del orquestador"""
        metrics = self.get_metrics()
        return {
            "running": self.running,  # Top-level key
            "tasks_pending": metrics["tasks_pending"],  # Top-level key
            "subsystems": list(self.subsystems.keys()),  # Top-level key como lista
            # Datos previos
            "orchestrator": metrics,
            "subsystems_detail": {
                name: getattr(sys, "get_status", lambda: {"status": "unknown"})()
                for name, sys in self.subsystems.items()
            }
        }


# Instancia global (singleton)
_orchestrator_instance: Optional[AIOrchestrator] = None


def get_orchestrator(bus=None) -> AIOrchestrator:
    """Obtiene la instancia singleton del orquestador"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AIOrchestrator(bus=bus)
    elif bus and not _orchestrator_instance.bus:
        _orchestrator_instance.set_bus(bus)
    return _orchestrator_instance
