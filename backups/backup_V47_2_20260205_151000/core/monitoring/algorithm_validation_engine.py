"""
Validador de Algoritmos (Auto‑mejora protegida)

Objetivo:
- Evaluar propuestas de algoritmos sin aceptar a ciegas.
- Multi‑rondas + quorum.
- No‑regresión estricta por defecto.
- Permite degradación secundaria solo si la ganancia primaria es sustancial.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from core.monitoring.thermodynamic_judge import ThermodynamicJudge


@dataclass
class AlgorithmValidationResult:
    candidato_id: str
    is_valid: bool
    reasons: List[str]
    warnings: List[str]
    rounds_required: int
    rounds_passed: int
    score: float


class AlgorithmValidationEngine:
    def __init__(self):
        # Umbrales conservadores (alineados con máxima de precisión/estabilidad)
        self.rounds_required = 3
        self.rounds_min_pass = 2

        self.min_speedup_pct = 10.0
        self.max_memory_increase_pct = 5.0
        self.max_cpu_increase_pct = 5.0

        # No‑regresión estricta por defecto
        self.allow_secondary_degrade = True
        self.secondary_max_degrade_pct = 1.0
        self.primary_min_gain_pct = 15.0

        self.primary_metrics = {"precision_delta_pct", "stability_delta_pct"}
        self.secondary_metrics = {"memory_delta_pct", "cpu_delta_pct"}
        self._judge = ThermodynamicJudge()

    def validate(self, candidato_id: str, rounds: List[Dict[str, float]]) -> AlgorithmValidationResult:
        """Valida en múltiples rondas. Cada ronda es un dict de métricas."""
        reasons: List[str] = []
        warnings: List[str] = []

        if not rounds:
            return AlgorithmValidationResult(
                candidato_id=candidato_id,
                is_valid=False,
                reasons=["Sin rondas de evaluación"],
                warnings=[],
                rounds_required=self.rounds_required,
                rounds_passed=0,
                score=0.0,
            )

        rounds_passed = 0
        scores: List[float] = []
        total_violations = 0

        for metrics in rounds:
            passed, score, round_reasons, round_warnings = self._validate_round(metrics)
            scores.append(score)
            if passed:
                rounds_passed += 1
            reasons.extend(round_reasons)
            warnings.extend(round_warnings)

            # Juez termodinámico (si hay salidas físicas en metrics)
            outputs = metrics.get("outputs") or {}
            if isinstance(outputs, dict):
                res = self._judge.check_limits(outputs)
                if not res.ok:
                    warnings.extend(res.violations)
                    total_violations += len(res.violations)

        is_valid = rounds_passed >= min(self.rounds_required, self.rounds_min_pass)
        avg_score = sum(scores) / len(scores) if scores else 0.0
        if total_violations:
            avg_score *= self._judge.penalty_factor(["x"] * total_violations)

        return AlgorithmValidationResult(
            candidato_id=candidato_id,
            is_valid=is_valid,
            reasons=reasons,
            warnings=warnings,
            rounds_required=self.rounds_required,
            rounds_passed=rounds_passed,
            score=avg_score,
        )

    def _validate_round(self, metrics: Dict[str, float]) -> tuple[bool, float, List[str], List[str]]:
        reasons: List[str] = []
        warnings: List[str] = []

        speedup = metrics.get("speedup_pct", 0.0)
        precision_delta = metrics.get("precision_delta_pct", 0.0)
        stability_delta = metrics.get("stability_delta_pct", 0.0)
        mem_delta = metrics.get("memory_delta_pct", 0.0)
        cpu_delta = metrics.get("cpu_delta_pct", 0.0)

        if speedup < self.min_speedup_pct:
            reasons.append(f"Speedup insuficiente: {speedup:.2f}% < {self.min_speedup_pct:.2f}%")

        if precision_delta < 0:
            reasons.append(f"Regresión de precisión: {precision_delta:.4f}%")
        if stability_delta < 0:
            reasons.append(f"Regresión de estabilidad: {stability_delta:.4f}%")

        if mem_delta > self.max_memory_increase_pct:
            reasons.append(f"Memoria excesiva: {mem_delta:.2f}% > {self.max_memory_increase_pct:.2f}%")
        if cpu_delta > self.max_cpu_increase_pct:
            reasons.append(f"CPU excesiva: {cpu_delta:.2f}% > {self.max_cpu_increase_pct:.2f}%")

        # Permitir degradación secundaria si la ganancia primaria es sustancial
        if self.allow_secondary_degrade:
            if speedup >= self.primary_min_gain_pct:
                if mem_delta > self.secondary_max_degrade_pct:
                    warnings.append(
                        f"Degradación secundaria aceptada por ganancia primaria: memoria +{mem_delta:.2f}%"
                    )
                if cpu_delta > self.secondary_max_degrade_pct:
                    warnings.append(
                        f"Degradación secundaria aceptada por ganancia primaria: cpu +{cpu_delta:.2f}%"
                    )
            else:
                if mem_delta > self.secondary_max_degrade_pct:
                    reasons.append(
                        f"Degradación secundaria sin ganancia suficiente: memoria +{mem_delta:.2f}%"
                    )
                if cpu_delta > self.secondary_max_degrade_pct:
                    reasons.append(
                        f"Degradación secundaria sin ganancia suficiente: cpu +{cpu_delta:.2f}%"
                    )

        passed = len(reasons) == 0
        score = self._score_round(metrics)
        return passed, score, reasons, warnings

    @staticmethod
    def _score_round(metrics: Dict[str, float]) -> float:
        """Score compuesto simple, prioriza precisión/estabilidad sobre velocidad."""
        precision = metrics.get("precision_delta_pct", 0.0)
        stability = metrics.get("stability_delta_pct", 0.0)
        speedup = metrics.get("speedup_pct", 0.0)
        mem_delta = metrics.get("memory_delta_pct", 0.0)
        cpu_delta = metrics.get("cpu_delta_pct", 0.0)

        return (
            (precision * 0.5)
            + (stability * 0.3)
            + (speedup * 0.2)
            - (mem_delta * 0.1)
            - (cpu_delta * 0.1)
        )
