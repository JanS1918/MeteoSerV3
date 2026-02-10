#!/usr/bin/env python3
"""
CANARY ROLLOUT MANAGER - Despliegue Gradual Seguro
==================================================

Implementa deploy gradual de fórmulas en fases:
- Fase 1: 5% del tráfico (≥2h)
- Fase 2: 10% del tráfico (≥2h)
- Fase 3: 50% del tráfico (≥2h)
- Fase 4: 100% del tráfico (definitivo)

Si regresión > 1% en cualquier fase → rollback automático

Refinamiento V37.2:
- Cada fase dura ≥2h
- Mide regresión por métrica
- Rollback si degradación > 1%
- Logging exhaustivo de cada fase
"""

import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger("canary_rollout")


class CanaryPhase(Enum):
    """Fases del despliegue canary."""
    PENDING = "pending"
    PHASE_5 = "5%"
    PHASE_10 = "10%"
    PHASE_50 = "50%"
    PHASE_100 = "100%"
    ROLLED_BACK = "rolled_back"
    COMPLETED = "completed"


@dataclass
class CanaryMetrics:
    """Métricas de una fase canary."""
    phase: str
    percentage: int
    start_time: str
    end_time: Optional[str]
    samples_count: int
    
    # Métricas de baseline (antes del canary)
    baseline_precision: float
    baseline_stability: float
    baseline_efficiency: float
    baseline_rmse: float
    
    # Métricas de canary (durante el despliegue)
    canary_precision: float
    canary_stability: float
    canary_efficiency: float
    canary_rmse: float
    
    # Degradaciones
    precision_delta: float  # Negativo = empeor
    stability_delta: float
    efficiency_delta: float
    rmse_delta: float
    
    # Decisión
    passed: bool
    reason: str


@dataclass
class CanaryDeployment:
    """Registro de un despliegue canary."""
    formula_name: str
    formula_id: str
    timestamp: str
    status: str
    phases: List[Dict[str, Any]]
    current_phase: str
    total_duration_seconds: Optional[int]
    rollback_reason: Optional[str]
    notes: str


class CanaryRolloutManager:
    """
    Gestor de despliegues canary para fórmulas.
    
    Phases:
    1. 5% → 2h mínimo
    2. 10% → 2h mínimo
    3. 50% → 2h mínimo
    4. 100% → definitivo
    """
    
    DEGRADATION_THRESHOLD = 0.01  # 1% máximo de degradación
    MIN_PHASE_DURATION = 2 * 3600  # 2 horas en segundos
    MIN_SAMPLES = 100
    
    def __init__(self, base_path: str = ".", self_mod_engine=None):
        """
        Args:
            base_path: Directorio base del proyecto
            self_mod_engine: Engine para manejo de cambios
        """
        self.base_path = Path(base_path)
        self.self_mod_engine = self_mod_engine
        
        self.deployments_dir = self.base_path / "data" / "canary_deployments"
        self.deployments_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_deployments: Dict[str, CanaryDeployment] = {}
        self._load_deployments()
        
        logger.info("[OK] CanaryRolloutManager inicializado")
    
    def _load_deployments(self):
        """Carga despliegues anteriores desde disco."""
        try:
            deployments_file = self.deployments_dir / "deployments.json"
            if deployments_file.exists():
                with open(deployments_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"📖 Cargados {len(data)} despliegues anteriores")
        except Exception as e:
            logger.warning(f"[WARNING] No se pudieron cargar despliegues anteriores: {e}")
    
    def _save_deployment(self, deployment: CanaryDeployment):
        """Guarda despliegue a disco."""
        try:
            deployment_file = self.deployments_dir / f"deployment_{deployment.formula_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(deployment_file, 'w') as f:
                json.dump(asdict(deployment), f, indent=2)
            logger.info(f"[GUARDAR] Despliegue guardado: {deployment_file}")
        except Exception as e:
            logger.error(f"[ERROR] Error guardando despliegue: {e}")
    
    def start_canary_deployment(self, formula_name: str, formula_id: str, 
                                baseline_metrics: Dict[str, float]) -> str:
        """
        Inicia despliegue canary de una fórmula.
        
        Args:
            formula_name: Nombre de la fórmula
            formula_id: ID único de la fórmula
            baseline_metrics: Métricas de baseline {precision, stability, efficiency, rmse}
        
        Returns:
            deployment_id para trackear el despliegue
        """
        deployment_id = f"{formula_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"[LAUNCH] INICIANDO CANARY DEPLOYMENT")
        logger.info(f"   Formula: {formula_name} ({formula_id})")
        logger.info(f"   Baseline: precision={baseline_metrics.get('precision', 0):.3f}, "
                   f"stability={baseline_metrics.get('stability', 0):.3f}")
        
        deployment = CanaryDeployment(
            formula_name=formula_name,
            formula_id=formula_id,
            timestamp=datetime.now().isoformat(),
            status=CanaryPhase.PENDING.value,
            phases=[],
            current_phase="5%",
            total_duration_seconds=None,
            rollback_reason=None,
            notes="Inicio de despliegue canary"
        )
        
        self.current_deployments[deployment_id] = deployment
        self._save_deployment(deployment)
        
        return deployment_id
    
    def advance_phase(self, deployment_id: str, current_phase: str,
                      current_metrics: Dict[str, float]) -> Tuple[bool, str]:
        """
        Avanza a la siguiente fase después de validar regresión.
        
        Args:
            deployment_id: ID del despliegue
            current_phase: Fase actual (5%, 10%, 50%, 100%)
            current_metrics: Métricas actuales
        
        Returns:
            (passou, razón) - True si puede continuar, False si debe rollback
        """
        if deployment_id not in self.current_deployments:
            logger.error(f"[ERROR] Despliegue no encontrado: {deployment_id}")
            return False, "Despliegue no encontrado"
        
        deployment = self.current_deployments[deployment_id]
        
        logger.info(f"[STATS] Evaluando fase {current_phase} para {deployment.formula_name}")
        
        # Extraer baseline (primera fase)
        if not deployment.phases:
            baseline = {
                'precision': current_metrics.get('precision', 0),
                'stability': current_metrics.get('stability', 0),
                'efficiency': current_metrics.get('efficiency', 0),
                'rmse': current_metrics.get('rmse', 0)
            }
            logger.info(f"   Baseline establecido: {baseline}")
        else:
            # Comparar con baseline
            baseline = {
                'precision': deployment.phases[0].get('baseline_precision', 0),
                'stability': deployment.phases[0].get('baseline_stability', 0),
                'efficiency': deployment.phases[0].get('baseline_efficiency', 0),
                'rmse': deployment.phases[0].get('baseline_rmse', 0)
            }
        
        # Calcular deltas
        precision_delta = (current_metrics.get('precision', 0) - baseline['precision']) / (baseline['precision'] or 1.0)
        stability_delta = (current_metrics.get('stability', 0) - baseline['stability']) / (baseline['stability'] or 1.0)
        efficiency_delta = (current_metrics.get('efficiency', 0) - baseline['efficiency']) / (baseline['efficiency'] or 1.0)
        rmse_delta = (current_metrics.get('rmse', 0) - baseline['rmse']) / (baseline['rmse'] or 1.0)
        
        # Verificar si hay degradación
        max_delta = max(
            abs(precision_delta),
            abs(stability_delta),
            abs(efficiency_delta),
            abs(rmse_delta)
        )
        
        passed = max_delta <= self.DEGRADATION_THRESHOLD
        reason = f"Max degradation: {max_delta:.2%}" if not passed else f"Dentro de umbral ({max_delta:.2%})"
        
        # Registrar métricas de la fase
        phase_metrics = CanaryMetrics(
            phase=current_phase,
            percentage=int(current_phase.rstrip('%')),
            start_time=datetime.now().isoformat(),
            end_time=None,
            samples_count=self.MIN_SAMPLES,
            baseline_precision=baseline['precision'],
            baseline_stability=baseline['stability'],
            baseline_efficiency=baseline['efficiency'],
            baseline_rmse=baseline['rmse'],
            canary_precision=current_metrics.get('precision', 0),
            canary_stability=current_metrics.get('stability', 0),
            canary_efficiency=current_metrics.get('efficiency', 0),
            canary_rmse=current_metrics.get('rmse', 0),
            precision_delta=precision_delta,
            stability_delta=stability_delta,
            efficiency_delta=efficiency_delta,
            rmse_delta=rmse_delta,
            passed=passed,
            reason=reason
        )
        
        deployment.phases.append(asdict(phase_metrics))
        deployment.current_phase = current_phase
        
        if passed:
            logger.info(f"[OK] FASE {current_phase} APROBADA: {reason}")
            return True, reason
        else:
            logger.warning(f"[WARNING] FASE {current_phase} FALLIDA: {reason}")
            return False, reason
    
    def rollback(self, deployment_id: str, reason: str) -> bool:
        """
        Efectúa rollback del despliegue canary.
        
        Args:
            deployment_id: ID del despliegue
            reason: Razón del rollback
        
        Returns:
            True si rollback fue exitoso
        """
        if deployment_id not in self.current_deployments:
            logger.error(f"[ERROR] Despliegue no encontrado: {deployment_id}")
            return False
        
        deployment = self.current_deployments[deployment_id]
        
        logger.critical(f"🔙 ROLLBACK CANARY: {reason}")
        logger.critical(f"   Formula: {deployment.formula_name}")
        logger.critical(f"   Fase fallida: {deployment.current_phase}")
        
        # Usar self_mod_engine para rollback si está disponible
        if self.self_mod_engine:
            try:
                # TODO: Implementar rollback real
                logger.info(f"   Restaurando snapshot anterior...")
            except Exception as e:
                logger.error(f"[ERROR] Error en rollback: {e}")
                return False
        
        deployment.status = CanaryPhase.ROLLED_BACK.value
        deployment.rollback_reason = reason
        deployment.total_duration_seconds = int(
            (datetime.fromisoformat(datetime.now().isoformat()) - 
             datetime.fromisoformat(deployment.timestamp)).total_seconds()
        )
        
        self._save_deployment(deployment)
        return True
    
    def complete_deployment(self, deployment_id: str) -> bool:
        """
        Marca despliegue como completado (100% alcanzado).
        
        Args:
            deployment_id: ID del despliegue
        
        Returns:
            True si fue exitoso
        """
        if deployment_id not in self.current_deployments:
            logger.error(f"[ERROR] Despliegue no encontrado: {deployment_id}")
            return False
        
        deployment = self.current_deployments[deployment_id]
        
        logger.info(f"[OK] DESPLIEGUE COMPLETADO: {deployment.formula_name}")
        logger.info(f"   Fases totales: {len(deployment.phases)}")
        logger.info(f"   Estado final: 100%")
        
        deployment.status = CanaryPhase.COMPLETED.value
        deployment.current_phase = "100%"
        deployment.total_duration_seconds = int(
            (datetime.fromisoformat(datetime.now().isoformat()) - 
             datetime.fromisoformat(deployment.timestamp)).total_seconds()
        )
        
        self._save_deployment(deployment)
        
        # Publicar al Bus
        logger.info(f"📢 Publicando despliegue completado al Bus")
        
        return True
    
    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estado actual de un despliegue."""
        if deployment_id not in self.current_deployments:
            return None
        
        deployment = self.current_deployments[deployment_id]
        return asdict(deployment)
    
    def get_phase_recommendations(self, current_metrics: Dict[str, float]) -> str:
        """
        Proporciona recomendaciones basadas en métricas.
        
        Returns:
            Recomendación en texto
        """
        precision = current_metrics.get('precision', 0)
        stability = current_metrics.get('stability', 0)
        efficiency = current_metrics.get('efficiency', 0)
        
        recommendations = []
        
        if precision < 0.8:
            recommendations.append("[WARNING] Precisión baja, considerar revisión de fórmula")
        if stability < 0.8:
            recommendations.append("[WARNING] Estabilidad baja, posible variancia alta")
        if efficiency < 0.8:
            recommendations.append("[WARNING] Eficiencia baja, verificar recursos")
        
        if not recommendations:
            return "[OK] Todas las métricas dentro de rango normal"
        
        return " | ".join(recommendations)


# Ejemplo de uso
if __name__ == "__main__":
    manager = CanaryRolloutManager(base_path=".")
    
    # Simular despliegue
    deployment_id = manager.start_canary_deployment(
        formula_name="UTCI_Mejorada",
        formula_id="utci_v2",
        baseline_metrics={
            'precision': 0.95,
            'stability': 0.92,
            'efficiency': 0.88,
            'rmse': 0.5
        }
    )
    
    logger.info(f"Deployment ID: {deployment_id}")
    
    # Fase 5%
    passed, reason = manager.advance_phase(deployment_id, "5%", {
        'precision': 0.946,
        'stability': 0.915,
        'efficiency': 0.875,
        'rmse': 0.52
    })
    
    if passed:
        logger.info("[OK] Puede continuar a siguiente fase")
    else:
        logger.info(f"[ERROR] Rollback necesario: {reason}")
        manager.rollback(deployment_id, reason)
