#!/usr/bin/env python3
"""CAPA 15: Resource Budget Gate - CPU < 10%, RAM < 500MB, latency p95 < 1s"""

import logging
from typing import Dict
from dataclasses import dataclass
import statistics

logger = logging.getLogger("resource_budget_gate")


@dataclass
class ResourceAnalysis:
    formula_name: str
    cpu_pct: float
    ram_mb: float
    latency_p95: float
    passed: bool
    reason: str


class ResourceBudgetGate:
    """Valida presupuesto de recursos antes de deploy."""
    
    CPU_THRESHOLD = 10.0
    RAM_THRESHOLD = 500.0
    LATENCY_THRESHOLD = 1.0
    
    def __init__(self):
        self.resource_metrics: Dict[str, Dict] = {}
        logger.info("✅ ResourceBudgetGate inicializado")
    
    def record_execution(self, formula_name: str, cpu_pct: float, ram_mb: float, latency_ms: float):
        if formula_name not in self.resource_metrics:
            self.resource_metrics[formula_name] = {'cpu': [], 'ram': [], 'latency': []}
        self.resource_metrics[formula_name]['cpu'].append(cpu_pct)
        self.resource_metrics[formula_name]['ram'].append(ram_mb)
        self.resource_metrics[formula_name]['latency'].append(latency_ms / 1000.0)
        for key in self.resource_metrics[formula_name]:
            if len(self.resource_metrics[formula_name][key]) > 100:
                self.resource_metrics[formula_name][key] = self.resource_metrics[formula_name][key][-100:]
    
    def analyze(self, formula_name: str) -> ResourceAnalysis:
        if formula_name not in self.resource_metrics:
            return ResourceAnalysis(formula_name, 0.0, 0.0, 0.0, True, "Sin mediciones")
        
        metrics = self.resource_metrics[formula_name]
        cpu_p95 = sorted(metrics['cpu'])[int(0.95*len(metrics['cpu']))] if metrics['cpu'] else 0
        ram_p95 = sorted(metrics['ram'])[int(0.95*len(metrics['ram']))] if metrics['ram'] else 0
        lat_p95 = sorted(metrics['latency'])[int(0.95*len(metrics['latency']))] if metrics['latency'] else 0
        
        passed = (cpu_p95 <= self.CPU_THRESHOLD and ram_p95 <= self.RAM_THRESHOLD and lat_p95 <= self.LATENCY_THRESHOLD)
        
        if passed:
            reason = f"✅ Recursos OK: CPU={cpu_p95:.1f}%, RAM={ram_p95:.0f}MB, lat={lat_p95:.3f}s"
        else:
            failures = []
            if cpu_p95 > self.CPU_THRESHOLD:
                failures.append(f"CPU {cpu_p95:.1f}% > {self.CPU_THRESHOLD}%")
            if ram_p95 > self.RAM_THRESHOLD:
                failures.append(f"RAM {ram_p95:.0f}MB > {self.RAM_THRESHOLD}MB")
            if lat_p95 > self.LATENCY_THRESHOLD:
                failures.append(f"Latency {lat_p95:.3f}s > {self.LATENCY_THRESHOLD}s")
            reason = f"❌ Budget excedido: {', '.join(failures)}"
        
        return ResourceAnalysis(formula_name, cpu_p95, ram_p95, lat_p95, passed, reason)
