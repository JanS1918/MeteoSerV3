"""
Tests para AIOrchestrator
"""

import pytest
import asyncio
import time
from core.ai.orchestrator import AIOrchestrator, AITask


def test_orchestrator_singleton():
    """El orchestrator debe ser singleton"""
    from core.ai.orchestrator import get_orchestrator
    
    orch1 = get_orchestrator()
    orch2 = get_orchestrator()
    
    assert orch1 is orch2


def test_orchestrator_initialization():
    """Inicialización básica del orchestrator"""
    orch = AIOrchestrator()
    
    assert orch.running is False
    assert len(orch.task_queue) == 0
    assert len(orch.subsystems) == 0


def test_schedule_task():
    """Programar una tarea"""
    orch = AIOrchestrator()
    
    def dummy_task():
        return "done"
    
    task_id = orch.schedule_task(
        name="Test Task",
        callback=dummy_task,
        priority=5,
        metadata={"test": True}
    )
    
    assert task_id is not None
    assert len(orch.task_queue) == 1


def test_task_priority():
    """Las tareas deben ejecutarse por prioridad"""
    orch = AIOrchestrator()
    
    results = []
    
    def task_low():
        results.append("low")
    
    def task_high():
        results.append("high")
    
    orch.schedule_task("Low Priority", task_low, priority=1)
    orch.schedule_task("High Priority", task_high, priority=10)
    
    # La tarea de mayor prioridad debería estar primero
    assert orch.task_queue[0].priority == 10


@pytest.mark.asyncio
async def test_orchestrator_run_stop():
    """Iniciar y detener el orchestrator"""
    orch = AIOrchestrator()
    
    # Iniciar en background
    asyncio.create_task(orch.start())
    
    # Esperar un poco
    await asyncio.sleep(0.5)
    
    assert orch.running is True
    
    # Detener
    await orch.stop()
    
    assert orch.running is False


def test_get_status():
    """Obtener estado del orchestrator"""
    orch = AIOrchestrator()
    
    status = orch.get_status()
    
    assert "running" in status
    assert "tasks_pending" in status
    assert "subsystems" in status


def test_get_metrics():
    """Obtener métricas del orchestrator"""
    orch = AIOrchestrator()
    
    metrics = orch.get_metrics()
    
    assert "tasks_completed" in metrics
    assert "tasks_failed" in metrics
    assert "uptime" in metrics
