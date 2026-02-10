#!/usr/bin/env python3
"""
CAPA 25: CEREBRO AUTÓNOMO DE AUTO-OPTIMIZACIÓN
===============================================

La capa que gobierna TODAS las demás 24 capas.

Meta-orquestador inteligente que:
- Monitorea estado global de las 24 capas
- Ajusta thresholds dinámicamente basado en histórico
- Detecta patrones emergentes de fallo
- Coordina respuestas entre capas
- Aprende de cada incidente (ML simple)
- Optimiza el sistema completo de forma autónoma

Esta es la capa "System of Systems" - el director de orquesta.

Filosofía: Las 24 capas son instrumentos, CAPA 25 es el director.

Uso:
    brain = AutonomousOptimizationBrain()
    brain.register_all_capas(...)
    brain.start_monitoring()
    
    # Auto-optimización continua
    brain.optimize_thresholds()
    brain.coordinate_response(incident)
"""

import logging
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from collections import defaultdict, deque

logger = logging.getLogger("autonomous_brain")


class CapaHealth(Enum):
    """Estado de salud de una capa"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"


class IncidentSeverity(Enum):
    """Severidad de incidente multi-capa"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CapaMetrics:
    """Métricas de una capa individual"""
    capa_id: int
    capa_name: str
    health: CapaHealth
    activations: int = 0
    rejections: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    last_update: float = 0.0
    current_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class SystemIncident:
    """Incidente que afecta múltiples capas"""
    incident_id: str
    timestamp: float
    severity: IncidentSeverity
    affected_capas: List[int]
    root_cause: str
    coordinated_response: Dict[str, Any]
    resolved: bool = False
    resolution_time_s: float = 0.0


@dataclass
class OptimizationDecision:
    """Decisión de optimización tomada por el cerebro"""
    timestamp: float
    capa_id: int
    threshold_name: str
    old_value: float
    new_value: float
    reason: str
    confidence: float


class AutonomousOptimizationBrain:
    """
    CAPA 25: El cerebro que gobierna todas las capas.
    
    Meta-orquestador inteligente con auto-optimización continua.
    """
    
    # Thresholds del cerebro mismo
    DEGRADATION_THRESHOLD = 0.15  # 15% error rate = degraded
    CRITICAL_THRESHOLD = 0.30     # 30% error rate = critical
    MIN_SAMPLES_OPTIMIZATION = 100  # Mínimo para ajustar thresholds
    OPTIMIZATION_INTERVAL = 3600    # Optimizar cada 1 hora
    
    # Learning rates para ajuste de thresholds
    THRESHOLD_ADJUSTMENT_RATE = 0.05  # 5% ajuste máximo por iteración
    
    def __init__(self, data_dir: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parents[2]
        self.data_dir = data_dir or (base_dir / "data" / "brain")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Registro de todas las capas
        self.capas: Dict[int, CapaMetrics] = {}
        
        # Histórico de métricas (ventana deslizante)
        self.metrics_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Incidentes multi-capa
        self.incidents: List[SystemIncident] = []
        
        # Decisiones de optimización
        self.optimization_history: List[OptimizationDecision] = []
        
        # Patrones aprendidos
        self.learned_patterns: Dict[str, Dict] = {}
        
        # Última optimización
        self.last_optimization = 0.0
        
        # Carga estado persistente
        self._load_brain_state()
        
        logger.info("🧠 CAPA 25: Cerebro Autónomo de Auto-Optimización inicializado")
    
    def register_capa(self, capa_id: int, capa_name: str, 
                     initial_thresholds: Optional[Dict[str, float]] = None):
        """Registra una capa en el cerebro para monitoreo."""
        self.capas[capa_id] = CapaMetrics(
            capa_id=capa_id,
            capa_name=capa_name,
            health=CapaHealth.HEALTHY,
            current_thresholds=initial_thresholds or {}
        )
        logger.info(f"📝 Capa {capa_id} ({capa_name}) registrada en cerebro")
    
    def register_all_capas(self, capas_config: Dict[int, Dict]):
        """Registra todas las 24 capas de una vez."""
        for capa_id, config in capas_config.items():
            self.register_capa(
                capa_id,
                config.get("name", f"Capa_{capa_id}"),
                config.get("thresholds", {})
            )
        logger.info(f"✅ {len(self.capas)} capas registradas en cerebro")
    
    def report_capa_execution(self, capa_id: int, success: bool, 
                             latency_ms: float, error: Optional[str] = None):
        """Reporta ejecución de una capa al cerebro."""
        if capa_id not in self.capas:
            logger.warning(f"⚠️ Capa {capa_id} no registrada")
            return
        
        capa = self.capas[capa_id]
        capa.activations += 1
        if not success:
            capa.rejections += 1
        
        # Actualizar métricas
        capa.avg_latency_ms = (capa.avg_latency_ms * 0.9 + latency_ms * 0.1)
        capa.error_rate = capa.rejections / max(capa.activations, 1)
        capa.last_update = time.time()
        
        # Guardar en histórico
        self.metrics_history[capa_id].append({
            "timestamp": time.time(),
            "success": success,
            "latency_ms": latency_ms,
            "error": error
        })
        
        # Evaluar salud
        self._update_capa_health(capa_id)
    
    def _update_capa_health(self, capa_id: int):
        """Actualiza el estado de salud de una capa."""
        capa = self.capas[capa_id]
        
        if capa.error_rate >= self.CRITICAL_THRESHOLD:
            capa.health = CapaHealth.CRITICAL
            logger.critical(f"🔴 CAPA {capa_id} ({capa.capa_name}) CRÍTICA: error_rate={capa.error_rate:.1%}")
            self._trigger_incident_detection(capa_id)
        elif capa.error_rate >= self.DEGRADATION_THRESHOLD:
            capa.health = CapaHealth.DEGRADED
            logger.warning(f"🟡 CAPA {capa_id} ({capa.capa_name}) DEGRADADA: error_rate={capa.error_rate:.1%}")
        else:
            capa.health = CapaHealth.HEALTHY
    
    def _trigger_incident_detection(self, primary_capa_id: int):
        """Detecta si el fallo es parte de un incidente multi-capa."""
        affected_capas = [primary_capa_id]
        
        # Buscar otras capas afectadas en la última hora
        now = time.time()
        for capa_id, capa in self.capas.items():
            if capa_id == primary_capa_id:
                continue
            if now - capa.last_update < 3600:  # Última hora
                if capa.health in [CapaHealth.CRITICAL, CapaHealth.DEGRADED]:
                    affected_capas.append(capa_id)
        
        # Si afecta múltiples capas, crear incidente
        if len(affected_capas) > 1:
            incident = SystemIncident(
                incident_id=f"INC_{int(now)}",
                timestamp=now,
                severity=IncidentSeverity.CRITICAL if len(affected_capas) > 3 else IncidentSeverity.HIGH,
                affected_capas=affected_capas,
                root_cause=self._analyze_root_cause(affected_capas),
                coordinated_response=self._coordinate_response(affected_capas)
            )
            self.incidents.append(incident)
            logger.critical(f"🚨 INCIDENTE MULTI-CAPA: {incident.incident_id} afecta {len(affected_capas)} capas")
    
    def _analyze_root_cause(self, affected_capas: List[int]) -> str:
        """Analiza causa raíz de incidente multi-capa usando patrones."""
        # Análisis simple: buscar patrones comunes
        capa_names = [self.capas[cid].capa_name for cid in affected_capas if cid in self.capas]
        
        # Patrones conocidos
        if any("watchdog" in name.lower() for name in capa_names):
            return "Posible deadlock o congelación del sistema principal"
        
        if any("canary" in name.lower() for name in capa_names):
            return "Degradación durante despliegue gradual"
        
        if all("gate" in name.lower() for name in capa_names):
            return "Sobrecarga en pipeline de validación pre-duelo"
        
        if any("bus" in name.lower() for name in capa_names):
            return "Problema de integración MQTT Bus"
        
        return f"Incidente afectando {len(affected_capas)} capas simultáneamente"
    
    def _coordinate_response(self, affected_capas: List[int]) -> Dict[str, Any]:
        """Coordina respuesta entre capas afectadas."""
        response = {
            "actions": [],
            "threshold_adjustments": {},
            "alerting": []
        }
        
        for capa_id in affected_capas:
            if capa_id not in self.capas:
                continue
            
            capa = self.capas[capa_id]
            
            # Estrategias según capa
            if capa_id == 21:  # Watchdog
                response["actions"].append({
                    "capa": 21,
                    "action": "increase_heartbeat_frequency",
                    "params": {"interval_s": 15}  # Más frecuente
                })
            
            if capa_id == 18:  # Canary
                response["actions"].append({
                    "capa": 18,
                    "action": "pause_canary_deployment",
                    "params": {"rollback": True}
                })
            
            if 12 <= capa_id <= 17:  # Pre-duelo gates
                response["threshold_adjustments"][capa_id] = {
                    "action": "relax_thresholds_temporarily",
                    "factor": 1.2  # 20% más permisivo temporalmente
                }
            
            response["alerting"].append({
                "capa": capa_id,
                "severity": "CRITICAL",
                "message": f"Capa {capa.capa_name} parte de incidente multi-capa"
            })
        
        return response
    
    def optimize_thresholds(self) -> List[OptimizationDecision]:
        """
        Auto-optimización de thresholds basado en histórico.
        
        Machine learning simple: ajusta thresholds para minimizar
        falsos positivos mientras mantiene detección de verdaderos fallos.
        """
        now = time.time()
        
        # Solo optimizar cada OPTIMIZATION_INTERVAL
        if now - self.last_optimization < self.OPTIMIZATION_INTERVAL:
            return []
        
        decisions = []
        
        for capa_id, capa in self.capas.items():
            # Necesitamos suficientes muestras
            if len(self.metrics_history[capa_id]) < self.MIN_SAMPLES_OPTIMIZATION:
                continue
            
            # Analizar histórico
            history = list(self.metrics_history[capa_id])
            
            # Calcular métricas
            total = len(history)
            failures = sum(1 for h in history if not h["success"])
            failure_rate = failures / total if total > 0 else 0
            
            avg_latency = sum(h["latency_ms"] for h in history) / total if total > 0 else 0
            p95_latency = sorted([h["latency_ms"] for h in history])[int(total * 0.95)] if total > 0 else 0
            
            # Optimizar thresholds según capa
            for threshold_name, current_value in capa.current_thresholds.items():
                new_value = self._calculate_optimal_threshold(
                    threshold_name, current_value, failure_rate, avg_latency, p95_latency
                )
                
                if new_value != current_value:
                    decision = OptimizationDecision(
                        timestamp=now,
                        capa_id=capa_id,
                        threshold_name=threshold_name,
                        old_value=current_value,
                        new_value=new_value,
                        reason=f"Optimización basada en {total} muestras, failure_rate={failure_rate:.1%}",
                        confidence=min(total / self.MIN_SAMPLES_OPTIMIZATION, 1.0)
                    )
                    decisions.append(decision)
                    self.optimization_history.append(decision)
                    
                    # Aplicar nuevo threshold
                    capa.current_thresholds[threshold_name] = new_value
                    logger.info(f"🔧 CAPA {capa_id} ({capa.capa_name}): {threshold_name} "
                               f"{current_value:.2f} → {new_value:.2f}")
        
        self.last_optimization = now
        self._save_brain_state()
        
        return decisions
    
    def _calculate_optimal_threshold(self, threshold_name: str, current_value: float,
                                    failure_rate: float, avg_latency: float, 
                                    p95_latency: float) -> float:
        """
        Calcula threshold óptimo usando heurísticas simples.
        
        Estrategia:
        - Si failure_rate < 5%: Threshold muy estricto, relajar un poco
        - Si failure_rate > 20%: Threshold muy permisivo, endurecer
        - Si 5% <= failure_rate <= 20%: Threshold óptimo, mantener
        """
        if "latency" in threshold_name.lower():
            # Optimizar latency thresholds
            if failure_rate < 0.05:
                # Muy pocos fallos, podemos ser más estrictos
                new_value = current_value * (1 - self.THRESHOLD_ADJUSTMENT_RATE)
                return max(new_value, p95_latency * 0.9)  # No menos que p95
            elif failure_rate > 0.20:
                # Demasiados fallos, relajar threshold
                new_value = current_value * (1 + self.THRESHOLD_ADJUSTMENT_RATE)
                return new_value
            else:
                # Threshold óptimo
                return current_value
        
        elif "cpu" in threshold_name.lower() or "ram" in threshold_name.lower():
            # Optimizar resource thresholds
            if failure_rate < 0.05:
                new_value = current_value * (1 - self.THRESHOLD_ADJUSTMENT_RATE)
                return max(new_value, 5.0)  # Mínimo razonable
            elif failure_rate > 0.20:
                new_value = current_value * (1 + self.THRESHOLD_ADJUSTMENT_RATE)
                return new_value
            else:
                return current_value
        
        elif "depth" in threshold_name.lower():
            # Depth es discreto, no ajustar dinámicamente
            return current_value
        
        else:
            # Threshold genérico
            if failure_rate < 0.05:
                return current_value * (1 - self.THRESHOLD_ADJUSTMENT_RATE)
            elif failure_rate > 0.20:
                return current_value * (1 + self.THRESHOLD_ADJUSTMENT_RATE)
            else:
                return current_value
    
    def get_system_health_summary(self) -> Dict:
        """Resumen de salud del sistema completo."""
        health_counts = defaultdict(int)
        for capa in self.capas.values():
            health_counts[capa.health.value] += 1
        
        total_activations = sum(c.activations for c in self.capas.values())
        total_rejections = sum(c.rejections for c in self.capas.values())
        overall_error_rate = total_rejections / max(total_activations, 1)
        
        return {
            "total_capas": len(self.capas),
            "health_distribution": dict(health_counts),
            "overall_error_rate": overall_error_rate,
            "total_activations": total_activations,
            "total_rejections": total_rejections,
            "active_incidents": len([i for i in self.incidents if not i.resolved]),
            "optimizations_applied": len(self.optimization_history),
            "last_optimization": self.last_optimization,
            "capas_critical": [c.capa_id for c in self.capas.values() if c.health == CapaHealth.CRITICAL],
            "capas_degraded": [c.capa_id for c in self.capas.values() if c.health == CapaHealth.DEGRADED]
        }
    
    def get_recommendations(self) -> List[Dict]:
        """Genera recomendaciones basadas en análisis del cerebro."""
        recommendations = []
        
        # Analizar capas críticas
        critical_capas = [c for c in self.capas.values() if c.health == CapaHealth.CRITICAL]
        if critical_capas:
            recommendations.append({
                "priority": "CRITICAL",
                "type": "immediate_action",
                "message": f"{len(critical_capas)} capas en estado CRÍTICO requieren atención inmediata",
                "affected_capas": [c.capa_id for c in critical_capas],
                "action": "Revisar logs y aplicar respuesta coordinada"
            })
        
        # Analizar incidentes no resueltos
        unresolved = [i for i in self.incidents if not i.resolved]
        if unresolved:
            recommendations.append({
                "priority": "HIGH",
                "type": "incident_resolution",
                "message": f"{len(unresolved)} incidentes multi-capa sin resolver",
                "incidents": [i.incident_id for i in unresolved],
                "action": "Aplicar respuestas coordinadas pendientes"
            })
        
        # Analizar thresholds que necesitan optimización
        if time.time() - self.last_optimization > self.OPTIMIZATION_INTERVAL:
            recommendations.append({
                "priority": "MEDIUM",
                "type": "optimization",
                "message": "Ejecutar ciclo de auto-optimización de thresholds",
                "action": "Llamar optimize_thresholds()"
            })
        
        return recommendations
    
    def _save_brain_state(self):
        """Persiste estado del cerebro."""
        state = {
            "capas": {
                cid: {
                    "capa_id": c.capa_id,
                    "capa_name": c.capa_name,
                    "health": c.health.value,
                    "activations": c.activations,
                    "rejections": c.rejections,
                    "avg_latency_ms": c.avg_latency_ms,
                    "error_rate": c.error_rate,
                    "current_thresholds": c.current_thresholds
                }
                for cid, c in self.capas.items()
            },
            "optimization_history": [
                {
                    "timestamp": d.timestamp,
                    "capa_id": d.capa_id,
                    "threshold_name": d.threshold_name,
                    "old_value": d.old_value,
                    "new_value": d.new_value,
                    "reason": d.reason,
                    "confidence": d.confidence
                }
                for d in self.optimization_history[-100:]  # Solo últimas 100
            ],
            "last_optimization": self.last_optimization
        }
        
        state_file = self.data_dir / "brain_state.json"
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    
    def _load_brain_state(self):
        """Carga estado persistente del cerebro."""
        state_file = self.data_dir / "brain_state.json"
        if not state_file.exists():
            return
        
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            
            # Restaurar capas
            for cid_str, capa_data in state.get("capas", {}).items():
                cid = int(cid_str)
                self.capas[cid] = CapaMetrics(
                    capa_id=capa_data["capa_id"],
                    capa_name=capa_data["capa_name"],
                    health=CapaHealth(capa_data["health"]),
                    activations=capa_data["activations"],
                    rejections=capa_data["rejections"],
                    avg_latency_ms=capa_data["avg_latency_ms"],
                    error_rate=capa_data["error_rate"],
                    current_thresholds=capa_data["current_thresholds"]
                )
            
            # Restaurar optimización
            for opt_data in state.get("optimization_history", []):
                self.optimization_history.append(OptimizationDecision(
                    timestamp=opt_data["timestamp"],
                    capa_id=opt_data["capa_id"],
                    threshold_name=opt_data["threshold_name"],
                    old_value=opt_data["old_value"],
                    new_value=opt_data["new_value"],
                    reason=opt_data["reason"],
                    confidence=opt_data["confidence"]
                ))
            
            self.last_optimization = state.get("last_optimization", 0.0)
            
            logger.info(f"✅ Estado del cerebro restaurado: {len(self.capas)} capas")
        
        except Exception as e:
            logger.error(f"❌ Error cargando estado del cerebro: {e}")
    
    def emergency_shutdown_coordination(self, reason: str) -> Dict:
        """
        Coordina shutdown de emergencia de todas las capas de forma ordenada.
        
        Estrategia:
        1. Pausar canary deployments (CAPA 18)
        2. Detener duelos (CAPAS 12-17)
        3. Salvar estado (CAPAS 1-5)
        4. Notificar watchdog (CAPA 21)
        5. Flush alertas (CAPA 24)
        """
        logger.critical(f"🚨 SHUTDOWN DE EMERGENCIA COORDINADO: {reason}")
        
        shutdown_plan = {
            "reason": reason,
            "timestamp": time.time(),
            "phases": []
        }
        
        # Fase 1: Pausar deployments
        shutdown_plan["phases"].append({
            "phase": 1,
            "name": "Pausar deployments",
            "capas": [18, 19, 20],
            "actions": ["pause_canary", "freeze_ab_tests", "prevent_rollouts"]
        })
        
        # Fase 2: Detener validaciones
        shutdown_plan["phases"].append({
            "phase": 2,
            "name": "Detener pipeline validación",
            "capas": list(range(12, 18)),
            "actions": ["stop_accepting_duelos", "finish_current_executions"]
        })
        
        # Fase 3: Salvar estado
        shutdown_plan["phases"].append({
            "phase": 3,
            "name": "Persistir estado crítico",
            "capas": [1, 2, 3, 22],
            "actions": ["flush_metrics", "save_learning_state", "backup_calibration"]
        })
        
        # Fase 4: Notificar watchdog
        shutdown_plan["phases"].append({
            "phase": 4,
            "name": "Notificar watchdog",
            "capas": [21],
            "actions": ["send_shutdown_heartbeat", "create_final_snapshot"]
        })
        
        # Fase 5: Alertas finales
        shutdown_plan["phases"].append({
            "phase": 5,
            "name": "Flush alertas críticas",
            "capas": [24],
            "actions": ["send_critical_alerts", "notify_operators"]
        })
        
        self._save_brain_state()
        
        return shutdown_plan


# Singleton global (opcional)
_brain_instance: Optional[AutonomousOptimizationBrain] = None

def get_brain() -> AutonomousOptimizationBrain:
    """Obtiene instancia singleton del cerebro."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AutonomousOptimizationBrain()
    return _brain_instance
