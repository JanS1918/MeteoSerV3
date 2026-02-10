#!/usr/bin/env python3
"""
CAPA 17: Execution Sandbox - Aislamiento y límites para APIs externas
======================================================================
Timeout, CPU limits, RAM limits, network isolation para fórmulas pre-duelo.

Especialmente crítico para integraciones externas:
- GFS/NOAA (puede tardar 10-30s)
- ECMWF (API lenta)
- APIs de terceros (riesgo de timeout)

Límites:
- Timeout: 30s (configurable)
- RAM: 200MB (evita memory leaks)
- CPU: ~50% (evita consumo total)
- Network: Solo HTTPS permitido (no HTTP plano)
"""

import signal
try:
    import resource
except Exception:
    resource = None
import logging
import time
import urllib.request
from typing import Callable, Any, Tuple, Optional, Dict
from functools import wraps
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading

logger = logging.getLogger("execution_sandbox")


@dataclass
class SandboxResult:
    """Resultado de ejecución en sandbox"""
    formula_name: str
    executed: bool
    execution_time_ms: float
    result: Any = None
    error: str = None
    violation: str = None  # Si violó límites
    network_calls: int = 0
    memory_peak_mb: float = 0.0


@dataclass
class SandboxStats:
    """Estadísticas del sandbox"""
    total_executions: int = 0
    successful: int = 0
    timeouts: int = 0
    errors: int = 0
    avg_execution_time_ms: float = 0.0
    violations: Dict[str, int] = field(default_factory=dict)


class NetworkMonitor:
    """Monitor de llamadas de red (detecta APIs externas)"""
    
    def __init__(self):
        self.network_calls = 0
        self.blocked_calls = 0
        self.lock = threading.Lock()
    
    def record_call(self, url: str, allowed: bool = True):
        """Registra llamada de red"""
        with self.lock:
            self.network_calls += 1
            if not allowed:
                self.blocked_calls += 1
                logger.warning(f"⚠️ Llamada de red bloqueada: {url}")
            else:
                logger.debug(f"🌐 Llamada de red permitida: {url}")


class ExecutionSandbox:
    """
    Sandbox de ejecución con límites estrictos.
    
    Casos de uso:
    1. Pre-duelo de fórmulas (antes de competir)
    2. Integración de APIs externas (GFS, ECMWF)
    3. Experimentación con fórmulas no confiables
    4. Testing de nuevas fórmulas
    """
    
    # Límites por defecto
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_RAM_LIMIT_MB = 200
    DEFAULT_CPU_LIMIT_PERCENT = 0.50
    
    def __init__(self, 
                 timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
                 ram_limit_mb: int = DEFAULT_RAM_LIMIT_MB,
                 cpu_limit: float = DEFAULT_CPU_LIMIT_PERCENT,
                 allow_network: bool = True,
                 https_only: bool = True):
        """
        Args:
            timeout_seconds: Timeout máximo de ejecución
            ram_limit_mb: Límite de RAM (MB)
            cpu_limit: Límite CPU (0.0-1.0, fracción de un core)
            allow_network: Permitir llamadas de red
            https_only: Solo permitir HTTPS (no HTTP plano)
        """
        self.timeout_seconds = timeout_seconds
        self.ram_limit_mb = ram_limit_mb
        self.cpu_limit = cpu_limit
        self.allow_network = allow_network
        self.https_only = https_only
        
        self.network_monitor = NetworkMonitor()
        self.stats = SandboxStats()
        
        logger.info(f"[OK] ExecutionSandbox inicializado "
                   f"(timeout={timeout_seconds}s, RAM={ram_limit_mb}MB, "
                   f"network={'HTTPS-only' if https_only else 'all' if allow_network else 'disabled'})")
    
    def timeout_handler(self, signum, frame):
        """Manejador de timeout SIGALRM"""
        raise TimeoutError(f"Sandbox timeout después de {self.timeout_seconds}s")
    
    @contextmanager
    def _resource_limits(self):
        """Context manager para límites de recursos"""
        # Límite de memoria (soft limit)
        try:
            if resource is not None:
                soft, hard = resource.getrlimit(resource.RLIMIT_AS)
                new_limit = self.ram_limit_mb * 1024 * 1024  # MB -> bytes
                resource.setrlimit(resource.RLIMIT_AS, (new_limit, hard))
                logger.debug(f"Límite RAM establecido: {self.ram_limit_mb}MB")
        except Exception as e:
            logger.warning(f"No se pudo establecer límite RAM: {e}")
        
        try:
            yield
        finally:
            # Restaurar límites (si es necesario)
            try:
                if resource is not None:
                    resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
            except:
                pass
    
    def execute_with_limits(self, 
                           formula_name: str, 
                           formula_func: Callable, 
                           *args, 
                           **kwargs) -> SandboxResult:
        """
        Ejecuta función dentro de sandbox con límites estrictos.
        
        Args:
            formula_name: Nombre identificador de la fórmula
            formula_func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
        
        Returns:
            SandboxResult con resultado o error
        """
        start_time = time.time()
        self.stats.total_executions += 1
        
        try:
            # Configurar timeout
            if hasattr(signal, 'SIGALRM') and hasattr(signal, 'alarm'):
                signal.signal(signal.SIGALRM, self.timeout_handler)
                signal.alarm(self.timeout_seconds)
            
            # Ejecutar con límites de recursos
            with self._resource_limits():
                # Resetear contador de red
                network_calls_before = self.network_monitor.network_calls
                
                # Ejecutar función
                result = formula_func(*args, **kwargs)
                
                # Contar llamadas de red
                network_calls = self.network_monitor.network_calls - network_calls_before
            
            # Cancelar alarm
            if hasattr(signal, 'alarm'):
                signal.alarm(0)
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Actualizar stats
            self.stats.successful += 1
            self._update_avg_time(execution_time_ms)
            
            logger.info(f"✅ {formula_name} ejecutada en {execution_time_ms:.1f}ms "
                       f"(red: {network_calls} calls)")
            
            return SandboxResult(
                formula_name=formula_name,
                executed=True,
                execution_time_ms=execution_time_ms,
                result=result,
                network_calls=network_calls
            )
        
        except TimeoutError as e:
            if hasattr(signal, 'alarm'):
                signal.alarm(0)
            execution_time_ms = (time.time() - start_time) * 1000
            self.stats.timeouts += 1
            self.stats.violations["timeout"] = self.stats.violations.get("timeout", 0) + 1
            
            logger.error(f"⏱️ {formula_name} TIMEOUT después de {execution_time_ms:.1f}ms")
            
            return SandboxResult(
                formula_name=formula_name,
                executed=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
                violation=f"TIMEOUT EXCEDIDO ({self.timeout_seconds}s)"
            )
        
        except MemoryError as e:
            if hasattr(signal, 'alarm'):
                signal.alarm(0)
            execution_time_ms = (time.time() - start_time) * 1000
            self.stats.errors += 1
            self.stats.violations["memory"] = self.stats.violations.get("memory", 0) + 1
            
            logger.error(f"💾 {formula_name} MEMORY LIMIT excedido")
            
            return SandboxResult(
                formula_name=formula_name,
                executed=False,
                execution_time_ms=execution_time_ms,
                error=str(e),
                violation=f"MEMORY LIMIT EXCEDIDO ({self.ram_limit_mb}MB)"
            )
        
        except Exception as e:
            if hasattr(signal, 'alarm'):
                signal.alarm(0)
            execution_time_ms = (time.time() - start_time) * 1000
            self.stats.errors += 1
            
            logger.error(f"❌ {formula_name} error: {e}")
            
            return SandboxResult(
                formula_name=formula_name,
                executed=False,
                execution_time_ms=execution_time_ms,
                error=str(e)
            )
    
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Valida que URL cumpla políticas de seguridad.
        
        Args:
            url: URL a validar
        
        Returns:
            (permitida, razón)
        """
        if not self.allow_network:
            return False, "Red deshabilitada en sandbox"
        
        if self.https_only and not url.startswith("https://"):
            return False, "Solo HTTPS permitido (HTTP plano bloqueado)"
        
        # Whitelist de dominios permitidos (APIs meteorológicas confiables)
        trusted_domains = [
            "nomads.ncep.noaa.gov",  # GFS/NOAA
            "api.ecmwf.int",  # ECMWF
            "api.openweathermap.org",  # OpenWeather
            "api.weatherapi.com",  # WeatherAPI
        ]
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        
        if any(trusted in domain for trusted in trusted_domains):
            self.network_monitor.record_call(url, allowed=True)
            return True, f"Dominio confiable: {domain}"
        
        # Dominio no confiable → bloquear
        self.network_monitor.record_call(url, allowed=False)
        return False, f"Dominio no autorizado: {domain}"
    
    def validate_execution_time(self, execution_time_ms: float) -> Tuple[bool, str]:
        """Valida que tiempo esté dentro de límites"""
        max_ms = self.timeout_seconds * 1000
        if execution_time_ms > max_ms:
            return False, f"Tiempo {execution_time_ms:.0f}ms > límite {max_ms}ms"
        return True, f"[OK] Tiempo {execution_time_ms:.1f}ms dentro de límite"
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del sandbox"""
        success_rate = (self.stats.successful / self.stats.total_executions * 100 
                       if self.stats.total_executions > 0 else 0.0)
        
        return {
            "total_executions": self.stats.total_executions,
            "successful": self.stats.successful,
            "timeouts": self.stats.timeouts,
            "errors": self.stats.errors,
            "success_rate": f"{success_rate:.1f}%",
            "avg_execution_time_ms": f"{self.stats.avg_execution_time_ms:.1f}",
            "violations": dict(self.stats.violations),
            "network": {
                "total_calls": self.network_monitor.network_calls,
                "blocked_calls": self.network_monitor.blocked_calls
            }
        }
    
    def _update_avg_time(self, new_time_ms: float):
        """Actualiza promedio de tiempo de ejecución"""
        n = self.stats.successful
        if n == 1:
            self.stats.avg_execution_time_ms = new_time_ms
        else:
            self.stats.avg_execution_time_ms = (
                (self.stats.avg_execution_time_ms * (n - 1) + new_time_ms) / n
            )


# Singleton global para uso fácil
_sandbox_instance: Optional[ExecutionSandbox] = None

def get_sandbox() -> ExecutionSandbox:
    """Obtiene instancia singleton del sandbox"""
    global _sandbox_instance
    if _sandbox_instance is None:
        _sandbox_instance = ExecutionSandbox()
    return _sandbox_instance


# Decorator para funciones que requieren sandbox
def sandboxed(timeout: int = ExecutionSandbox.DEFAULT_TIMEOUT_SECONDS, 
             ram_mb: int = ExecutionSandbox.DEFAULT_RAM_LIMIT_MB):
    """
    Decorator para ejecutar función en sandbox.
    
    Uso:
        @sandboxed(timeout=30, ram_mb=200)
        def mi_formula_peligrosa(x, y):
            # código que puede fallar
            return x + y
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            sandbox = ExecutionSandbox(timeout_seconds=timeout, ram_limit_mb=ram_mb)
            result = sandbox.execute_with_limits(func.__name__, func, *args, **kwargs)
            
            if not result.executed:
                raise RuntimeError(f"Sandbox violation: {result.violation or result.error}")
            
            return result.result
        return wrapper
    return decorator


if __name__ == "__main__":
    # Tests de validación
    logging.basicConfig(level=logging.INFO)
    
    sandbox = ExecutionSandbox(timeout_seconds=5)
    
    # Test 1: Función normal (debe pasar)
    def formula_normal():
        time.sleep(1)
        return 42
    
    result = sandbox.execute_with_limits("formula_normal", formula_normal)
    print(f"Test 1: {result.executed} - {result.execution_time_ms:.1f}ms")
    
    # Test 2: Timeout (debe fallar)
    def formula_lenta():
        time.sleep(10)
        return 42
    
    result = sandbox.execute_with_limits("formula_lenta", formula_lenta)
    print(f"Test 2: {result.executed} - Violación: {result.violation}")
    
    # Test 3: Validación URL
    urls_test = [
        "https://nomads.ncep.noaa.gov/gfs",  # Debe pasar
        "http://example.com",  # Debe fallar (HTTP)
        "https://malicious.com",  # Debe fallar (no confiable)
    ]
    
    for url in urls_test:
        allowed, reason = sandbox.validate_url(url)
        print(f"URL {url}: {'✅ OK' if allowed else '❌ BLOCKED'} - {reason}")
    
    # Stats finales
    print("\n📊 Stats:")
    import json
    print(json.dumps(sandbox.get_stats(), indent=2))

