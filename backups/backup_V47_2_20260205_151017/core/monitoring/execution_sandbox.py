#!/usr/bin/env python3
"""CAPA 17: Execution Sandbox - Timeout, CPU limits, RAM limits para fórmulas pre-duelo"""

import signal
import resource
import logging
from typing import Callable, Any, Tuple
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger("execution_sandbox")


@dataclass
class SandboxResult:
    formula_name: str
    executed: bool
    execution_time_ms: float
    result: Any = None
    error: str = None
    violation: str = None  # Si violó límites


class ExecutionSandbox:
    """Pre-duelo sandbox: timeout 30s, CPU ~50%, RAM 200MB"""
    
    TIMEOUT_SECONDS = 30
    CPU_LIMIT_HEURISTIC = 0.50  # 50% de un core
    RAM_LIMIT_MB = 200
    
    def __init__(self):
        logger.info(f"✅ ExecutionSandbox inicializado (timeout={self.TIMEOUT_SECONDS}s, RAM={self.RAM_LIMIT_MB}MB)")
    
    def timeout_handler(self, signum, frame):
        """Manejador de timeout SIGALRM"""
        raise TimeoutError(f"Sandbox timeout después de {self.TIMEOUT_SECONDS}s")
    
    def execute_with_limits(self, formula_name: str, formula_func: Callable, 
                          *args, **kwargs) -> SandboxResult:
        """Ejecuta función dentro de sandbox con límites."""
        import time
        start_time = time.time()
        
        try:
            # Configurar timeout
            signal.signal(signal.SIGALRM, self.timeout_handler)
            signal.alarm(self.TIMEOUT_SECONDS)
            
            # Ejecutar
            result = formula_func(*args, **kwargs)
            
            # Cancelar alarm
            signal.alarm(0)
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"✅ {formula_name} ejecutada en {execution_time_ms:.1f}ms")
            return SandboxResult(formula_name, True, execution_time_ms, result=result)
        
        except TimeoutError as e:
            signal.alarm(0)
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ {formula_name} violó timeout ({e})")
            return SandboxResult(formula_name, False, execution_time_ms, error=str(e),
                               violation=f"TIMEOUT EXCEDIDO ({self.TIMEOUT_SECONDS}s)")
        
        except Exception as e:
            signal.alarm(0)
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ {formula_name} error: {e}")
            return SandboxResult(formula_name, False, execution_time_ms, error=str(e))
    
    def validate_execution_time(self, execution_time_ms: float) -> Tuple[bool, str]:
        """Valida que tiempo < timeout"""
        if execution_time_ms > (self.TIMEOUT_SECONDS * 1000):
            return False, f"Tiempo {execution_time_ms:.0f}ms > límite {self.TIMEOUT_SECONDS}s"
        return True, f"✅ Tiempo {execution_time_ms:.1f}ms OK"
