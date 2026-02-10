#!/usr/bin/env python3
"""CAPA 14: Drift Detection Gate"""

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
    """Detecta deriva temporal en salidas de fórmula - p95 latency > 1s O variancia > 5%"""
    
    LATENCY_P95_THRESHOLD = 1.0
    VARIANCE_THRESHOLD = 0.05
    
    def __init__(self):
        self.measurements: Dict[str, List[float]] = {}
        self.latencies: Dict[str, List[float]] = {}
        logger.info("[OK] DriftDetectionGate inicializado")
    
    def record_measurement(self, formula_name: str, value: float, latency_ms: float):
        if formula_name not in self.measurements:
            self.measurements[formula_name] = []
            self.latencies[formula_name] = []
        self.measurements[formula_name].append(value)
        self.latencies[formula_name].append(latency_ms / 1000.0)
        if len(self.measurements[formula_name]) > 1000:
            self.measurements[formula_name] = self.measurements[formula_name][-1000:]
            self.latencies[formula_name] = self.latencies[formula_name][-1000:]
    
    def analyze(self, formula_name: str) -> DriftAnalysis:
        if formula_name not in self.measurements or len(self.measurements[formula_name]) < 10:
            return DriftAnalysis(formula_name, 0.0, 0.0, True, "Insuficientes mediciones")
        
        values = self.measurements[formula_name]
        latencies = self.latencies[formula_name]
        sorted_latencies = sorted(latencies)
        idx_p95 = int(0.95 * len(sorted_latencies))
        latency_p95 = sorted_latencies[idx_p95]
        mean = statistics.mean(values)
        variance = statistics.variance(values) / (mean ** 2) if mean > 0 else 0.0
        passed = (latency_p95 <= self.LATENCY_P95_THRESHOLD and variance <= self.VARIANCE_THRESHOLD)
        
        reason = (f"[OK] Drift OK: p95={latency_p95:.3f}s, var={variance:.3f}" if passed
                 else f"[ERROR] Drift excedido: p95={latency_p95:.3f}s > {self.LATENCY_P95_THRESHOLD}s, var={variance:.3f} > {self.VARIANCE_THRESHOLD}")
        
        return DriftAnalysis(formula_name, latency_p95, variance, passed, reason)
