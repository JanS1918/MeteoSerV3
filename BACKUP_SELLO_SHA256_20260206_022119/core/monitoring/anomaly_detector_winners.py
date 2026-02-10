#!/usr/bin/env python3
"""CAPA 16: Anomaly Detector Winners - Si mejora > 20% pero estabilidad < -10% → OVERFITTING"""

import logging
from dataclasses import dataclass

logger = logging.getLogger("anomaly_detector_winners")


@dataclass
class OverfittingAnalysis:
    formula_name: str
    improvement: float
    stability_delta: float
    detected_overfitting: bool
    reason: str


class AnomalyDetectorWinners:
    """Detecta overfitting en fórmulas ganadoras."""
    
    MIN_IMPROVEMENT = 0.20
    MAX_STABILITY_LOSS = -0.10
    
    def __init__(self):
        logger.info("[OK] AnomalyDetectorWinners inicializado")
    
    def analyze_improvement(self, formula_name: str, improvement_pct: float,
                          stability_delta: float, precision_delta: float) -> OverfittingAnalysis:
        """Mejora > 20% pero estabilidad cae > 10% = sospechoso (overfitting)"""
        
        is_overfitting = (improvement_pct > self.MIN_IMPROVEMENT and stability_delta < self.MAX_STABILITY_LOSS)
        
        if is_overfitting:
            reason = f"[ERROR] OVERFITTING: Mejora {improvement_pct:.1%} pero estabilidad cae {stability_delta:.1%}"
        else:
            if improvement_pct <= self.MIN_IMPROVEMENT:
                reason = f"[OK] Mejora baja ({improvement_pct:.1%}), no sospechosa"
            elif stability_delta >= self.MAX_STABILITY_LOSS:
                reason = f"[OK] Estabilidad estable ({stability_delta:.1%}), mejora legítima"
            else:
                reason = f"[OK] Mejora {improvement_pct:.1%} con estabilidad {stability_delta:.1%}, válida"
        
        return OverfittingAnalysis(formula_name, improvement_pct, stability_delta, is_overfitting, reason)
