#!/usr/bin/env python3
"""
CAPA 14: Drift Detection Gate
=============================
Bloquea si p95 latency > 1s O variancia > 5%
"""

import logging
from typing import Dict, Tuple, List
import statistics
from dataclasses import dataclass

logger = logging.getLogger("drift_detection_gate")


@dataclass
class DriftAnalysis:
    """Análisis de drift en formula."""
    formula_name: str
    latency_p95: float
    variance: float
    passed: bool
    reason: str


class DriftDetectionGate:
    """Detecta deriva temporal en salidas de fórmula."""
    
    LATENCY_P95_THRESHOLD = 1.0  # segundos
    VARIANCE_THRESHOLD = 0.05    # 5%
    
    def __init__(self):
        self.measurements: Dict[str, List[float]] = {}
        self.latencies: Dict[str, List[float]] = {}
        logger.info("[OK] DriftDetectionGate inicializado")
    
    def record_measurement(self, formula_name: str, value: float, latency_ms: float):
        """Registra una ejecución de fórmula."""
        if formula_name not in self.measurements:
            self.measurements[formula_name] = []
            self.latencies[formula_name] = []
        
        self.measurements[formula_name].append(value)
        self.latencies[formula_name].append(latency_ms / 1000.0)  # Convert to seconds
        
        # Mantener ventana de últimas 1000 mediciones
        if len(self.measurements[formula_name]) > 1000:
            self.measurements[formula_name] = self.measurements[formula_name][-1000:]
            self.latencies[formula_name] = self.latencies[formula_name][-1000:]
    
    def analyze(self, formula_name: str) -> DriftAnalysis:
        """Analiza drift de una fórmula."""
        
        if formula_name not in self.measurements or len(self.measurements[formula_name]) < 10:
            return DriftAnalysis(
                formula_name=formula_name,
                latency_p95=0.0,
                variance=0.0,
                passed=True,
                reason="Insuficientes mediciones"
            )
        
        values = self.measurements[formula_name]
        latencies = self.latencies[formula_name]
        
        # Calcular p95 latency
        sorted_latencies = sorted(latencies)
        idx_p95 = int(0.95 * len(sorted_latencies))
        latency_p95 = sorted_latencies[idx_p95]
        
        # Calcular variancia
        mean = statistics.mean(values)
        variance = statistics.variance(values) / (mean ** 2) if mean > 0 else 0.0
        
        # Validar
        passed = (latency_p95 <= self.LATENCY_P95_THRESHOLD and 
                 variance <= self.VARIANCE_THRESHOLD)
        
        if passed:
            reason = f"[OK] Drift OK: p95={latency_p95:.3f}s, var={variance:.3f}"
        else:
            reasons = []
            if latency_p95 > self.LATENCY_P95_THRESHOLD:
                reasons.append(f"latency p95 {latency_p95:.3f}s > {self.LATENCY_P95_THRESHOLD}s")
            if variance > self.VARIANCE_THRESHOLD:
                reasons.append(f"variance {variance:.3f} > {self.VARIANCE_THRESHOLD}")
            reason = f"[ERROR] Drift excedido: {', '.join(reasons)}"
        
        return DriftAnalysis(
            formula_name=formula_name,
            latency_p95=latency_p95,
            variance=variance,
            passed=passed,
            reason=reason
        )

    """
    CARA 15: Resource Budget Gate
    CPU < 10%, RAM < 500MB, latency p95 < 1s
    """

@dataclass
class ResourceAnalysis:
    """Análisis de recursos."""
    formula_name: str
    cpu_pct: float
    ram_mb: float
    latency_p95: float
    passed: bool
    reason: str


class ResourceBudgetGate:
    """Valida presupuesto de recursos."""
    
    CPU_THRESHOLD = 10.0      # %
    RAM_THRESHOLD = 500.0     # MB
    LATENCY_THRESHOLD = 1.0   # segundos
    
    def __init__(self):
        self.resource_metrics: Dict[str, Dict] = {}
        logger.info("[OK] ResourceBudgetGate inicializado")
    
    def record_execution(self, formula_name: str, cpu_pct: float, 
                        ram_mb: float, latency_ms: float):
        """Registra ejecución con métricas de recursos."""
        if formula_name not in self.resource_metrics:
            self.resource_metrics[formula_name] = {
                'cpu': [], 'ram': [], 'latency': []
            }
        
        self.resource_metrics[formula_name]['cpu'].append(cpu_pct)
        self.resource_metrics[formula_name]['ram'].append(ram_mb)
        self.resource_metrics[formula_name]['latency'].append(latency_ms / 1000.0)
        
        # Mantener últimas 100
        for key in self.resource_metrics[formula_name]:
            if len(self.resource_metrics[formula_name][key]) > 100:
                self.resource_metrics[formula_name][key] = \
                    self.resource_metrics[formula_name][key][-100:]
    
    def analyze(self, formula_name: str) -> ResourceAnalysis:
        """Analiza presupuesto de recursos."""
        
        if formula_name not in self.resource_metrics:
            return ResourceAnalysis(
                formula_name=formula_name,
                cpu_pct=0.0, ram_mb=0.0, latency_p95=0.0,
                passed=True,
                reason="Sin mediciones"
            )
        
        metrics = self.resource_metrics[formula_name]
        
        cpu_p95 = sorted(metrics['cpu'])[int(0.95*len(metrics['cpu']))] if metrics['cpu'] else 0
        ram_p95 = sorted(metrics['ram'])[int(0.95*len(metrics['ram']))] if metrics['ram'] else 0
        lat_p95 = sorted(metrics['latency'])[int(0.95*len(metrics['latency']))] if metrics['latency'] else 0
        
        passed = (cpu_p95 <= self.CPU_THRESHOLD and 
                 ram_p95 <= self.RAM_THRESHOLD and 
                 lat_p95 <= self.LATENCY_THRESHOLD)
        
        if passed:
            reason = f"[OK] Recursos OK: CPU={cpu_p95:.1f}%, RAM={ram_p95:.0f}MB, lat={lat_p95:.3f}s"
        else:
            failures = []
            if cpu_p95 > self.CPU_THRESHOLD:
                failures.append(f"CPU {cpu_p95:.1f}% > {self.CPU_THRESHOLD}%")
            if ram_p95 > self.RAM_THRESHOLD:
                failures.append(f"RAM {ram_p95:.0f}MB > {self.RAM_THRESHOLD}MB")
            if lat_p95 > self.LATENCY_THRESHOLD:
                failures.append(f"Latency {lat_p95:.3f}s > {self.LATENCY_THRESHOLD}s")
            reason = f"[ERROR] Budget excedido: {', '.join(failures)}"
        
        return ResourceAnalysis(
            formula_name=formula_name,
            cpu_pct=cpu_p95,
            ram_mb=ram_p95,
            latency_p95=lat_p95,
            passed=passed,
            reason=reason
        )

"""
CARA 16: Anomaly Detector Winners (Overfitting Detection)
Si mejora > 20% pero estabilidad < -10% → RECHAZO (overfitting)
"""

@dataclass
class OverfittingAnalysis:
    """Análisis de overfitting."""
    formula_name: str
    improvement: float
    stability_delta: float
    detected_overfitting: bool
    reason: str


class AnomalyDetectorWinners:
    """Detecta overfitting en fórmulas ganadoras."""
    
    MIN_IMPROVEMENT = 0.20      # 20%
    MAX_STABILITY_LOSS = -0.10  # -10%
    
    def __init__(self):
        logger.info("[OK] AnomalyDetectorWinners inicializado")
    
    def analyze_improvement(self, formula_name: str, 
                          improvement_pct: float,
                          stability_delta: float,
                          precision_delta: float) -> OverfittingAnalysis:
        """Detecta si mejora parece sospechosa (overfitting)."""
        
        # Lógica: mejora > 20% pero estabilidad cae > 10% = sospechoso
        is_overfitting = (improvement_pct > self.MIN_IMPROVEMENT and 
                         stability_delta < self.MAX_STABILITY_LOSS)
        
        if is_overfitting:
            reason = (f"[ERROR] OVERFITTING DETECTADO: Mejora {improvement_pct:.1%} "
                     f"pero estabilidad cae {stability_delta:.1%}")
        else:
            if improvement_pct <= self.MIN_IMPROVEMENT:
                reason = f"[OK] Mejora baja ({improvement_pct:.1%}), no es sospechosa"
            elif stability_delta >= self.MAX_STABILITY_LOSS:
                reason = f"[OK] Estabilidad estable ({stability_delta:.1%}), mejora legítima"
            else:
                reason = (f"[OK] Mejora {improvement_pct:.1%} con "
                         f"estabilidad {stability_delta:.1%}, válida")
        
        return OverfittingAnalysis(
            formula_name=formula_name,
            improvement=improvement_pct,
            stability_delta=stability_delta,
            detected_overfitting=is_overfitting,
            reason=reason
        )

"""
CARA 17: Execution Sandbox
Timeout 30s, CPU 50%, RAM 200MB, pre-duelo
"""

import signal
from contextlib import contextmanager
try:
    import resource
except Exception:
    # `resource` and `SIGALRM` are POSIX-only; on Windows provide None fallback
    resource = None

class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException("Ejecución excedió timeout")


@dataclass
class SandboxResult:
    """Resultado de ejecución en sandbox."""
    success: bool
    output: any
    timeout: bool
    resource_exceeded: bool
    reason: str


class ExecutionSandbox:
    """Sandbox para pre-validar fórmulas antes del duelo."""
    
    TIMEOUT_SECONDS = 30
    CPU_LIMIT_PCT = 50  # Heurístico (rlimit es en CPU time, no %)
    RAM_LIMIT_MB = 200
    
    @staticmethod
    @contextmanager
    def sandbox_execution(timeout_s: int = TIMEOUT_SECONDS,
                          ram_limit_mb: int = RAM_LIMIT_MB):
        """Context manager para ejecución en sandbox."""
        
        # Guardar límites anteriores (si están disponibles)
        old_alarm = None
        old_rlimit = None
        if hasattr(signal, 'alarm'):
            try:
                old_alarm = signal.alarm(0)
            except Exception:
                old_alarm = None
        if resource is not None:
            try:
                old_rlimit = resource.getrlimit(resource.RLIMIT_AS)
            except Exception:
                old_rlimit = None

        try:
            # Configurar timeout solo en plataformas POSIX con SIGALRM
            if hasattr(signal, 'SIGALRM') and hasattr(signal, 'alarm'):
                try:
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(timeout_s)
                except Exception:
                    pass

            # Configurar límite de memoria si el módulo resource está disponible
            if resource is not None:
                try:
                    ram_bytes = ram_limit_mb * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (ram_bytes, ram_bytes))
                except Exception:
                    pass

            yield

        finally:
            # Restaurar alarm (si aplica)
            if hasattr(signal, 'alarm'):
                try:
                    signal.alarm(0)
                except Exception:
                    pass

            # Restaurar límites de memoria si se guardaron
            if resource is not None and old_rlimit is not None:
                try:
                    resource.setrlimit(resource.RLIMIT_AS, old_rlimit)
                except Exception:
                    pass

            if old_alarm:
                try:
                    signal.alarm(old_alarm)
                except Exception:
                    pass
    
    @staticmethod
    def execute_with_limits(formula_func, inputs: Dict,
                            timeout_s: int = TIMEOUT_SECONDS,
                            ram_limit_mb: int = RAM_LIMIT_MB) -> SandboxResult:
        """Ejecuta fórmula con límites de recursos."""
        
        try:
            with ExecutionSandbox.sandbox_execution(timeout_s, ram_limit_mb):
                result = formula_func(**inputs)
            
            return SandboxResult(
                success=True,
                output=result,
                timeout=False,
                resource_exceeded=False,
                reason="[OK] Ejecución exitosa dentro de límites"
            )
        
        except TimeoutException:
            return SandboxResult(
                success=False,
                output=None,
                timeout=True,
                resource_exceeded=False,
                reason=f"[ERROR] Timeout: Ejecución excedió {timeout_s}s"
            )
        
        except MemoryError:
            return SandboxResult(
                success=False,
                output=None,
                timeout=False,
                resource_exceeded=True,
                reason=f"[ERROR] RAM excedida: Límite {ram_limit_mb}MB"
            )
        
        except Exception as e:
            return SandboxResult(
                success=False,
                output=None,
                timeout=False,
                resource_exceeded=False,
                reason=f"[ERROR] Error en ejecución: {str(e)}"
            )

"""
CARA 13: Bus Integration Auditor
Trazabilidad 100%: si publica 3 subfactores → 3 deben estar en Bus
"""

@dataclass
class BusAuditResult:
    """Resultado de auditoría Bus."""
    formula_name: str
    declared_subfactors: int
    published_subfactors: int
    missing_subfactors: List[str]
    complete: bool
    reason: str


class BusIntegrationAuditor:
    """Audita integridad de Bus."""
    
    def __init__(self, bus=None):
        self.bus = bus
        logger.info("[OK] BusIntegrationAuditor inicializado")
    
    def audit_subfactor_completeness(self, formula_name: str,
                                     declared_subfactors: List[str],
                                     published_subfactors: List[str]) -> BusAuditResult:
        """Audita si todos los subfactores llegaron al Bus."""
        
        declared_set = set(declared_subfactors)
        published_set = set(published_subfactors)
        
        missing = declared_set - published_set
        complete = len(missing) == 0
        
        if complete:
            reason = f"[OK] Integridad OK: {len(declared_set)} subfactores publicados"
        else:
            reason = (f"[ERROR] FALTA INTEGRIDAD: {len(missing)} subfactores NO en Bus: "
                      f"{', '.join(list(missing)[:3])}")

        return BusAuditResult(
            formula_name=formula_name,
            declared_subfactors=len(declared_set),
            published_subfactors=len(published_set),
            missing_subfactors=list(missing),
            complete=complete,
            reason=reason
        )
