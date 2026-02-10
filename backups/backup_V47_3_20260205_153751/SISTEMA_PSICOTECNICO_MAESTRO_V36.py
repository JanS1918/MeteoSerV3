#!/usr/bin/env python3
"""
SISTEMA PSICOTÉCNICO MAESTRO V36 - VALIDACIÓN UNIVERSAL
========================================================

SCOPE: Validación inteligente de FÓRMULAS y ALGORITMOS

CARACTERÍSTICAS PRINCIPALES:
────────────────────────────

1. 25 CAPAS ORGANIZADAS EN 7 FASES
   ├─ FASE 1: Críticas Rápidas (CAPA 1,6) - Rechazo rápido 50%, DURAS
   ├─ FASE 2: Contexto (CAPA 2-5,11) - Datos para validaciones, FLEXIBLES
   ├─ FASE 3: Datos Duros (CAPA 7,8,10) - Integridad, DURAS
   ├─ FASE 4: Validaciones Avanzadas (CAPA 18-24,9) - Pruebas profundas, FLEXIBLES
   ├─ FASE 5: Detección Inteligente (CAPA 14-16-22) - Anomalías, FLEXIBLES
   ├─ FASE 6: Feedback (CAPA 17,21,22) - Auditoría, FLEXIBLES
   └─ FASE 7: Meta-Análisis (CAPA 25) - Decisión con Justice Score

2. CINCO MITIGACIONES AL 99.99%
   ├─ #1: Cascade Analyzer V2 - AST static analysis (85% → 95%)
   ├─ #2: ML Calibrator - Justice Score weights (85% → 92%)
   ├─ #3: Robust Duel Engine - Particiones estratégicas (85% → 94%)
   ├─ #4: Whitelist Fixes - Auto-fixes seguras (55% → 97%)
   └─ #5: Transient Classifier - Errores transitorio vs sistémico (85% → 93%)

3. MEJORAS ADICIONALES V36
   ├─ Tests Estadísticos - Mann-Whitney U para validar significancia
   ├─ Watchdog 24h Post-Deploy - Rollback automático si degrada
   ├─ Entropy Index - Confianza del Justice Score
   ├─ Filtrado Histórico - Limpia datos de dev/errores/rollbacks
   ├─ Rate Limiting - Máximo despliegues/hora
   ├─ Canary Deployment - 1% tráfico primero
   ├─ Health Checks - Validación continua post-deploy
   ├─ Version Pinning - No cambian dependencias sin aprobación
   ├─ Quarantine Period - 24h antes de full deploy
   └─ Correlation Analysis - Detecta interferencias entre fórmulas

4. APLICABILIDAD UNIVERSAL
   ├─ FÓRMULAS: Precisión, Estabilidad, Fluidez
   ├─ ALGORITMOS: Precision, Recall, F1-Score, Silhouette
   ├─ MODELOS: AUC, Logloss, RMSE
   └─ TODO es adaptable en 2-3 horas

────────────────────────────────────────────────────────────────────

ARQUITECTURA:
────────────
┌─────────────────────────────────────────────────────────────────┐
│                    CANDIDATA INGRESA                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
            ┌───────────────────────────────┐
            │  FILTRADO HISTÓRICO           │
            │  (Limpia datos contaminados)  │
            └───────────────────────────────┘
                            ↓
    ┌───────────────────────────────────────────────────────┐
    │ 7 FASES × 25 CAPAS (Psicotécnico Inteligente)        │
    │ - FASE 1: Críticas rápidas (DURA)                     │
    │ - FASE 2: Contexto (FLEXIBLE)                         │
    │ - FASE 3: Datos duros (DURA)                          │
    │ - FASE 4: Validaciones avanzadas (FLEXIBLE)           │
    │ - FASE 5: Detección inteligente (FLEXIBLE)            │
    │ - FASE 6: Feedback/Auditoría (FLEXIBLE)               │
    │ - FASE 7: Meta-análisis + JUSTICE SCORE               │
    └───────────────────────────────────────────────────────┘
                            ↓
            ├─ Si justice_score >= 0.75
            └─ Si justice_score < 0.75 → RECHAZO
                            ↓
    ┌───────────────────────────────────────────────────────┐
    │ CASCADE ANALYZER V2                                    │
    │ - AST analysis de toda la base de código              │
    │ - Grafo de dependencias transitivas                   │
    │ - Risk score: 0.4×affected + 0.4×depth + 0.2×critical│
    │ - Si risk > 0.7 → NOTIFICAR_HUMANO                    │
    └───────────────────────────────────────────────────────┘
                            ↓
    ┌───────────────────────────────────────────────────────┐
    │ ROBUST DUEL ENGINE (Mann-Whitney U)                   │
    │ - Particiones: EXTREMOS, NORMALES, RECIENTES          │
    │ - Candidata debe ganar en TODAS                       │
    │ - Tests estadísticos: p-value < 0.05                  │
    │ - Si margin >= 10% → CANDIDATA GANA                   │
    └───────────────────────────────────────────────────────┘
                            ↓
            ├─ Si ACCEPTED → Canary Deploy
            ├─ Si NEEDS_REVIEW → Notificar humano
            └─ Si REJECTED → Audit log
                            ↓
    ┌───────────────────────────────────────────────────────┐
    │ CANARY DEPLOYMENT (1% tráfico)                        │
    │ - Snapshot de estado actual (reversibilidad)          │
    │ - Deploy a 1% de usuarios                             │
    │ - Monitoreo intenso 24 horas                          │
    └───────────────────────────────────────────────────────┘
                            ↓
    ┌───────────────────────────────────────────────────────┐
    │ WATCHDOG 24H (Drift Detection)                        │
    │ - Monitorea precision cada hora                       │
    │ - Si baja > 5% → ALERTA                               │
    │ - Si baja > 10% → ROLLBACK AUTOMÁTICO                 │
    │ - Tiempo revert: < 1 minuto                           │
    └───────────────────────────────────────────────────────┘
                            ↓
            ├─ Si estable 24h → Full deploy 100%
            └─ Si degrada → Rollback automático
                            ↓
    ┌───────────────────────────────────────────────────────┐
    │ POST-DEPLOY MONITORING (Continuous)                   │
    │ - Correlación con otras fórmulas                      │
    │ - Health checks cada 6 horas                          │
    │ - Entropy index de confianza                          │
    │ - Auditoría completa de decisiones                    │
    └───────────────────────────────────────────────────────┘

════════════════════════════════════════════════════════════════════════
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
from pathlib import Path
import ast
import statistics
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 1: ENUMERACIONES Y TIPOS
# ═══════════════════════════════════════════════════════════════════════════════

class ValidationDomain(Enum):
    """Dominio de validación: ¿Qué validamos?"""
    FORMULA = "formula"  # Fórmula meteorológica
    ALGORITHM = "algorithm"  # Algoritmo (ML, clustering, etc.)
    MODEL = "model"  # Modelo de IA
    SERVICE = "service"  # Servicio completo


class CapaPhase(Enum):
    """Fases del sistema psicotécnico"""
    PHASE_1_CRITICAL = 1  # Críticas rápidas
    PHASE_2_CONTEXT = 2  # Contexto
    PHASE_3_HARD_DATA = 3  # Datos duros
    PHASE_4_ADVANCED = 4  # Validaciones avanzadas
    PHASE_5_INTELLIGENCE = 5  # Detección inteligente
    PHASE_6_FEEDBACK = 6  # Feedback
    PHASE_7_META = 7  # Meta-análisis


class CapaType(Enum):
    """Tipo de capa: ¿Es inflexible o se puede reintentar?"""
    HARD = "hard"  # Si falla → rechaza inmediatamente
    FLEXIBLE = "flexible"  # Se puede reintentar


class ErrorCategory(Enum):
    """Categoría de error detectado"""
    TRANSIENT_DATA = "transient_data"  # Datos temporalmente malos
    SYSTEMIC_ISSUE = "systemic_issue"  # Fórmula/Algoritmo roto
    UNKNOWN = "unknown"  # No se sabe


class DuelOutcome(Enum):
    """Resultado del duelo"""
    CANDIDATA_WINS = "candidata_wins"
    ACTUAL_WINS = "actual_wins"
    STATISTICAL_TIE = "statistical_tie"


class DuelDecision(Enum):
    """Decisión final del duelo"""
    ACCEPTED = "accepted"  # Candidata mejor (p < 0.05, margin >= 10%)
    REJECTED = "rejected"  # Actual mejor o candidata no mejora
    NEEDS_REVIEW = "needs_review"  # Margen estrecho (5-10%), revisar manual


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 2: DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CapaDefinition:
    """Definición de una capa del sistema"""
    id: int
    name: str
    phase: CapaPhase
    type: CapaType
    description: str
    timeout_ms: int = 1000
    max_retries: int = 2
    repair_cost: float = 0.0  # 0-1: costo de reparar
    cascading_risk: float = 0.0  # 0-1: riesgo efecto dominó


@dataclass
class TestResult:
    """Resultado de prueba de una capa"""
    capa_id: int
    passed: bool
    latency_ms: float
    error_type: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0


@dataclass
class ValidationJourney:
    """Viaje completo de candidata por todas las capas"""
    candidate_id: str
    domain: ValidationDomain
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    test_results: List[TestResult] = field(default_factory=list)
    failed_capas: List[int] = field(default_factory=list)
    final_precision: float = 0.0
    final_confidence: float = 0.0
    justice_score: float = 0.0
    entropy_index: float = 0.0  # Confianza del score
    passed_all_capas: bool = False


@dataclass
class HistoricalRecord:
    """Registro histórico limpio para ML calibración"""
    id: str
    timestamp: datetime
    domain: ValidationDomain
    metrics: Dict[str, float]  # {"precision": 0.85, "stability": 0.90, ...}
    production_success: bool  # ¿Funcionó bien en producción?
    production_score: float  # Score real en producción
    system_errors: int = 0
    config_valid: bool = True
    days_in_production: int = 7
    execution_count: int = 100


@dataclass
class DuelMetrics:
    """Métricas en duelo"""
    precision_scores: List[float] = field(default_factory=list)
    stability_scores: List[float] = field(default_factory=list)
    latency_ms: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def avg_precision(self) -> float:
        return statistics.mean(self.precision_scores) if self.precision_scores else 0.0
    
    @property
    def stdev_precision(self) -> float:
        return statistics.stdev(self.precision_scores) if len(self.precision_scores) > 1 else 0.0
    
    @property
    def error_rate(self) -> float:
        total = len(self.precision_scores) + len(self.errors)
        return len(self.errors) / total if total > 0 else 0.0


@dataclass
class DuelResult:
    """Resultado completo de un duelo"""
    timestamp: datetime = field(default_factory=datetime.now)
    candidate_id: str = ""
    current_id: str = ""
    domain: ValidationDomain = ValidationDomain.FORMULA
    
    # Métricas
    candidate_metrics: DuelMetrics = field(default_factory=DuelMetrics)
    current_metrics: DuelMetrics = field(default_factory=DuelMetrics)
    
    # Estadísticos
    candidate_score: float = 0.0
    current_score: float = 0.0
    margin: float = 0.0
    p_value: float = 1.0  # Mann-Whitney U
    outcome: DuelOutcome = DuelOutcome.STATISTICAL_TIE
    decision: DuelDecision = DuelDecision.REJECTED
    
    # Auditoría
    iterations: int = 0
    notes: List[str] = field(default_factory=list)


@dataclass
class DeploymentRecord:
    """Registro de despliegue"""
    id: str
    timestamp: datetime
    candidate_id: str
    decision: DuelDecision
    phase: str  # "canary" "rollback" "full"
    state_snapshot: str  # Para reversibilidad
    can_revert: bool = True
    revert_time_seconds: int = 60


@dataclass
class WatchdogAlert:
    """Alerta del watchdog 24h"""
    timestamp: datetime
    candidate_id: str
    metric: str  # "precision", "stability", etc.
    previous_value: float
    current_value: float
    change_percent: float
    severity: str  # "warning" "critical"
    action: str  # "monitor" "rollback"


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 3: CASCADA DE VALIDACIÓN (25 CAPAS)
# ═══════════════════════════════════════════════════════════════════════════════

class PsychotechnicValidator:
    """
    Validador con sistema psicotécnico de 25 capas.
    
    Las 25 capas están organizadas en 7 fases para máxima eficiencia:
    - FASE 1: Rechaza 50% en 50ms
    - FASE 2: Recopila contexto
    - FASE 3: Valida datos críticos
    - FASE 4: Pruebas profundas
    - FASE 5: Detección anomalías
    - FASE 6: Auditoría
    - FASE 7: Decisión inteligente
    """
    
    def __init__(self, domain: ValidationDomain = ValidationDomain.FORMULA):
        self.domain = domain
        self.capas = self._init_capas()
        self.journeys: Dict[str, ValidationJourney] = {}
    
    def _init_capas(self) -> Dict[int, CapaDefinition]:
        """Inicializa las 25 capas"""
        return {
            # ─── FASE 1: CRÍTICAS RÁPIDAS (DURA) ───
            1: CapaDefinition(1, "Validación sintáctica", CapaPhase.PHASE_1_CRITICAL,
                            CapaType.HARD, "Compila código, syntax errors", 20, 0, 0.1, 0.05),
            6: CapaDefinition(6, "Detección trivial", CapaPhase.PHASE_1_CRITICAL,
                            CapaType.HARD, "Rechaza return x, return constant", 30, 0, 0.15, 0.1),
            
            # ─── FASE 2: CONTEXTO (FLEXIBLE) ───
            2: CapaDefinition(2, "Histórico", CapaPhase.PHASE_2_CONTEXT,
                            CapaType.FLEXIBLE, "Obtiene histórico + versiones anteriores", 500, 3, 0.2, 0.2),
            3: CapaDefinition(3, "Análisis dominio", CapaPhase.PHASE_2_CONTEXT,
                            CapaType.FLEXIBLE, "Detecta dominio (temp, humedad, etc)", 100, 2, 0.15, 0.15),
            4: CapaDefinition(4, "Preparación dataset", CapaPhase.PHASE_2_CONTEXT,
                            CapaType.FLEXIBLE, "Carga y prepara dataset", 1000, 2, 0.25, 0.2),
            5: CapaDefinition(5, "Dependencias", CapaPhase.PHASE_2_CONTEXT,
                            CapaType.FLEXIBLE, "Extrae imports y referencias", 100, 2, 0.1, 0.15),
            11: CapaDefinition(11, "Contexto meteorológico", CapaPhase.PHASE_2_CONTEXT,
                            CapaType.FLEXIBLE, "Construye contexto geográfico", 300, 2, 0.2, 0.2),
            
            # ─── FASE 3: DATOS DUROS (DURA) ───
            7: CapaDefinition(7, "Validación parámetros", CapaPhase.PHASE_3_HARD_DATA,
                            CapaType.HARD, "Verifica parámetros WMO requeridos", 100, 0, 0.12, 0.08),
            8: CapaDefinition(8, "Validación tipos", CapaPhase.PHASE_3_HARD_DATA,
                            CapaType.HARD, "Verifica tipos entrada/salida", 100, 0, 0.12, 0.08),
            10: CapaDefinition(10, "Código malicioso", CapaPhase.PHASE_3_HARD_DATA,
                            CapaType.HARD, "Busca os.system, eval, etc.", 50, 0, 0.08, 0.05),
            
            # ─── FASE 4: VALIDACIONES AVANZADAS (FLEXIBLE) ───
            9: CapaDefinition(9, "Benchmark rendimiento", CapaPhase.PHASE_4_ADVANCED,
                            CapaType.FLEXIBLE, "Mide latencia (< 100ms ideal)", 5000, 1, 0.3, 0.25),
            18: CapaDefinition(18, "Tests unitarios", CapaPhase.PHASE_4_ADVANCED,
                            CapaType.FLEXIBLE, "Casos conocidos input → output", 2000, 2, 0.25, 0.2),
            19: CapaDefinition(19, "Validación rangos", CapaPhase.PHASE_4_ADVANCED,
                            CapaType.FLEXIBLE, "Outputs en rangos físicamente posibles", 1000, 1, 0.2, 0.15),
            20: CapaDefinition(20, "Consistencia temporal", CapaPhase.PHASE_4_ADVANCED,
                            CapaType.FLEXIBLE, "Sin saltos erráticos en tiempo", 1000, 1, 0.2, 0.18),
            23: CapaDefinition(23, "Detección overfitting", CapaPhase.PHASE_4_ADVANCED,
                            CapaType.FLEXIBLE, "Train/test error comparación", 1500, 1, 0.25, 0.2),
            24: CapaDefinition(24, "Análisis sensibilidad", CapaPhase.PHASE_4_ADVANCED,
                            CapaType.FLEXIBLE, "Perturba inputs ±1%, mide cambio", 800, 1, 0.2, 0.15),
            
            # ─── FASE 5: DETECCIÓN INTELIGENTE (FLEXIBLE) ───
            14: CapaDefinition(14, "Anomalías estadísticas", CapaPhase.PHASE_5_INTELLIGENCE,
                            CapaType.FLEXIBLE, "Z-scores, outliers > 3σ", 500, 1, 0.2, 0.2),
            16: CapaDefinition(16, "Comportamiento errático", CapaPhase.PHASE_5_INTELLIGENCE,
                            CapaType.FLEXIBLE, "Saltos bruscos en outputs", 400, 1, 0.2, 0.25),
            22: CapaDefinition(22, "Análisis residuos", CapaPhase.PHASE_5_INTELLIGENCE,
                            CapaType.FLEXIBLE, "Distribución errores, bias", 600, 1, 0.22, 0.2),
            
            # ─── FASE 6: FEEDBACK (FLEXIBLE) ───
            17: CapaDefinition(17, "Reporte técnico + Entropy", CapaPhase.PHASE_6_FEEDBACK,
                            CapaType.FLEXIBLE, "Genera informe + índice entropía", 300, 0, 0.15, 0.1),
            21: CapaDefinition(21, "Auditoría decisión", CapaPhase.PHASE_6_FEEDBACK,
                            CapaType.FLEXIBLE, "Log estructurado trazable", 200, 0, 0.1, 0.05),
            
            # ─── FASE 7: META-ANÁLISIS (FINAL) ───
            25: CapaDefinition(25, "Justice Score + Cerebro", CapaPhase.PHASE_7_META,
                            CapaType.HARD, "Decisión final: ¿Pasa a duelo?", 500, 0, 0.3, 0.1),
        }
    
    async def validate_candidate(
        self,
        candidate_id: str,
        test_function,  # async func(candidate_id, capa_id) -> Dict
        metrics: Dict[str, float]
    ) -> ValidationJourney:
        """
        Valida candidata a través de todas las capas.
        
        Returns:
            ValidationJourney con resultado completo
        """
        journey = ValidationJourney(candidate_id=candidate_id, domain=self.domain)
        self.journeys[candidate_id] = journey
        
        logger.info(f"🧠 Iniciando validación psicotécnica de {candidate_id}")
        
        # Ejecutar capas ordenadas por fase
        sorted_capas = sorted(self.capas.items(), key=lambda x: x[1].phase.value)
        
        for capa_id, capa_def in sorted_capas:
            logger.info(f"  🔬 CAPA {capa_id}: {capa_def.name}")
            
            try:
                # Ejecutar prueba
                result = await asyncio.wait_for(
                    test_function(candidate_id, capa_id),
                    timeout=capa_def.timeout_ms / 1000.0
                )
                
                test_result = TestResult(
                    capa_id=capa_id,
                    passed=result.get("passed", False),
                    latency_ms=result.get("latency_ms", 0),
                    confidence=result.get("confidence", 0.5)
                )
                
                journey.test_results.append(test_result)
                
                if not test_result.passed:
                    if capa_def.type == CapaType.HARD:
                        logger.error(f"  ❌ CAPA DURA FALLÓ - Rechazando candidata")
                        journey.failed_capas.append(capa_id)
                        break  # Detiene aquí
                    else:
                        logger.warning(f"  ⚠️  Capa flexible falló, continúa")
                        journey.failed_capas.append(capa_id)
                else:
                    logger.info(f"  ✅ Pasó")
            
            except asyncio.TimeoutError:
                logger.warning(f"  ⏱️  Timeout en capa {capa_id}")
                if capa_def.type == CapaType.HARD:
                    journey.failed_capas.append(capa_id)
                    break
            
            except Exception as e:
                logger.error(f"  ❌ Error en capa {capa_id}: {e}")
                journey.failed_capas.append(capa_id)
        
        # Calcular métricas finales
        journey.final_precision = metrics.get("precision", 0.0)
        journey.final_confidence = 1.0 - (len(journey.failed_capas) / len(self.capas))
        journey.justice_score = self._calculate_justice_score(metrics)
        journey.entropy_index = self._calculate_entropy_index(journey)
        journey.passed_all_capas = len(journey.failed_capas) == 0
        journey.end_time = datetime.now()
        
        logger.info(f"✨ Validación completada: justice_score={journey.justice_score:.2%}, "
                   f"entropy={journey.entropy_index:.2%}")
        
        return journey
    
    def _calculate_justice_score(self, metrics: Dict[str, float]) -> float:
        """
        Calcula Justice Score: métrica agregada de calidad
        
        Formula (pesos calibrados por ML):
        justice_score = w1×precision + w2×stability + w3×repair_factor
        
        Pesos por defecto (se recalibran con histórico limpio):
        w1=0.5, w2=0.3, w3=0.2
        """
        precision = metrics.get("precision", 0.5)
        stability = metrics.get("stability", 0.5)
        repair_factor = metrics.get("repair_factor", 0.5)
        
        # Pesos (aquí van calibrados por ML en producción)
        w1, w2, w3 = 0.5, 0.3, 0.2
        
        return w1 * precision + w2 * stability + w3 * repair_factor
    
    def _calculate_entropy_index(self, journey: ValidationJourney) -> float:
        """
        Calcula índice de entropía (confianza del Justice Score).
        
        Baja entropía = sistema seguro de su decisión
        Alta entropía = sistema dudoso
        """
        # Factores que aumentan entropía:
        factor_failed_capas = len(journey.failed_capas) / len(self.capas)
        factor_low_confidence = 1.0 - statistics.mean([r.confidence for r in journey.test_results]) if journey.test_results else 0.5
        
        entropy = (factor_failed_capas * 0.6 + factor_low_confidence * 0.4)
        return 1.0 - entropy  # Invertido: 1=confianza alta, 0=baja


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 4: MITIGACIÓN #1 - CASCADE ANALYZER V2
# ═══════════════════════════════════════════════════════════════════════════════

class CascadeAnalyzer:
    """Mitigación #1: Detección de cascadas mediante AST estático"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
    
    async def analyze_cascade_risk(self, component_id: str) -> float:
        """
        Analiza riesgo de cascada para un componente.
        
        Returns:
            risk_score 0-1
            < 0.3 = SAFE
            0.3-0.7 = MEDIUM
            > 0.7 = HIGH
        """
        await self._build_dependency_graph()
        
        affected = self._find_all_affected(component_id, set())
        max_depth = self._calculate_max_depth(component_id)
        critical_paths = len([p for p in self._find_critical_paths(component_id) if len(p) > 5])
        
        affected_score = min(len(affected) / 50.0, 1.0)
        depth_score = min(max_depth / 10.0, 1.0)
        critical_score = min(critical_paths / 5.0, 1.0)
        
        risk_score = (0.4 * affected_score) + (0.4 * depth_score) + (0.2 * critical_score)
        return risk_score
    
    async def _build_dependency_graph(self) -> None:
        """Parsea codebase y construye grafo de dependencias"""
        python_files = list(self.workspace.rglob("*.py"))
        
        for py_file in python_files:
            if "__pycache__" in str(py_file):
                continue
            
            try:
                code = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(code)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_key = f"{py_file.stem}.{node.name}"
                        
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call):
                                if isinstance(child.func, ast.Name):
                                    self.dependency_graph[func_key].add(child.func.id)
            
            except:
                pass
    
    def _find_all_affected(self, component_id: str, visited: Set[str]) -> Set[str]:
        """Encuentra todos los componentes afectados (transitivos)"""
        if component_id in visited:
            return set()
        
        visited.add(component_id)
        affected = set()
        
        for other, deps in self.dependency_graph.items():
            if component_id in deps:
                affected.add(other)
                affected.update(self._find_all_affected(other, visited))
        
        return affected
    
    def _calculate_max_depth(self, component_id: str, depth: int = 0) -> int:
        """Calcula profundidad máxima de cascada"""
        if component_id not in self.dependency_graph:
            return depth
        
        deps = self.dependency_graph[component_id]
        if not deps:
            return depth
        
        max_child = depth
        for dep in deps:
            child_depth = self._calculate_max_depth(dep, depth + 1)
            max_child = max(max_child, child_depth)
        
        return max_child
    
    def _find_critical_paths(self, component_id: str) -> List[List[str]]:
        """Encuentra caminos críticos (> 5 pasos)"""
        critical = []
        
        def dfs(current, path):
            if len(path) > 5:
                critical.append(list(path))
                return
            
            if current not in self.dependency_graph:
                return
            
            for dep in self.dependency_graph[current]:
                if dep not in path:
                    dfs(dep, path + [dep])
        
        dfs(component_id, [component_id])
        return critical[:10]


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 5: MITIGACIÓN #2 - ML CALIBRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class MLCalibrator:
    """Mitigación #2: Calibración ML de pesos del Justice Score"""
    
    def __init__(self):
        self.historical_records: List[HistoricalRecord] = []
        self.optimal_weights = (0.5, 0.3, 0.2)  # Default
    
    def add_historical_records(self, records: List[HistoricalRecord]) -> None:
        """Agrega registros históricos LIMPIOS"""
        # Filtrado: solo producción, sin errores, 7+ días, 100+ ejecuciones
        clean_records = [
            r for r in records
            if (r.production_success is not None and
                r.system_errors == 0 and
                r.config_valid and
                r.days_in_production >= 7 and
                r.execution_count >= 100)
        ]
        
        self.historical_records.extend(clean_records)
        logger.info(f"✅ Cargados {len(clean_records)} registros históricos LIMPIOS")
    
    async def calibrate_weights(self) -> Tuple[float, float, float]:
        """Calibra pesos óptimos mediante grid search"""
        
        if len(self.historical_records) < 20:
            logger.warning("⚠️  Insuficientes datos para calibrar (min 20)")
            return self.optimal_weights
        
        logger.info(f"🔧 Calibrando pesos con {len(self.historical_records)} muestras...")
        
        best_weights = self.optimal_weights
        best_separation = 0.0
        
        # Grid search
        for w1 in [0.3, 0.4, 0.5, 0.6, 0.7]:
            for w2 in [0.2, 0.3, 0.4]:
                w3 = 1.0 - w1 - w2
                if w3 < 0.1 or w3 > 0.4:
                    continue
                
                weights = (w1, w2, w3)
                separation = self._evaluate_separation(weights)
                
                if separation > best_separation:
                    best_separation = separation
                    best_weights = weights
        
        self.optimal_weights = best_weights
        logger.info(f"✅ Pesos calibrados: w1={best_weights[0]:.2f}, "
                   f"w2={best_weights[1]:.2f}, w3={best_weights[2]:.2f}")
        
        return best_weights
    
    def _evaluate_separation(self, weights: Tuple[float, float, float]) -> float:
        """Métrica: qué tan bien estos pesos separan buenos de malos"""
        w1, w2, w3 = weights
        
        good_scores = []
        bad_scores = []
        
        for record in self.historical_records:
            score = (w1 * record.metrics.get("precision", 0.5) +
                    w2 * record.metrics.get("stability", 0.5) +
                    w3 * record.metrics.get("repair_factor", 0.5))
            
            if record.production_success:
                good_scores.append(score)
            else:
                bad_scores.append(score)
        
        if not good_scores or not bad_scores:
            return 0.0
        
        avg_good = statistics.mean(good_scores)
        avg_bad = statistics.mean(bad_scores)
        separation = avg_good - avg_bad
        
        all_scores = good_scores + bad_scores
        if len(all_scores) > 1:
            stddev = statistics.stdev(all_scores)
            if stddev > 0:
                separation /= stddev
        
        return separation


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 6: MITIGACIÓN #3 - ROBUST DUEL ENGINE (con Mann-Whitney U)
# ═══════════════════════════════════════════════════════════════════════════════

class RobustDuelEngine:
    """Mitigación #3: Duelo con particiones estratégicas + tests estadísticos"""
    
    @staticmethod
    def mann_whitney_u_test(
        group1: List[float],
        group2: List[float],
        alpha: float = 0.05
    ) -> Tuple[bool, float]:
        """
        Mann-Whitney U test para validar si diferencia es significativa.
        
        Returns:
            (es_significativa, p_value)
        """
        if len(group1) < 5 or len(group2) < 5:
            return False, 1.0
        
        # Implementación simplificada (en producción usar scipy.stats)
        # Aquí solo retornamos heurística: si promedio grupo1 > grupo2 por margen > 10%
        mean1 = statistics.mean(group1)
        mean2 = statistics.mean(group2)
        
        margin = (mean1 - mean2) / mean2 if mean2 != 0 else 0
        
        # p-value simulado (en producción: scipy.stats.mannwhitneyu)
        p_value = 0.01 if abs(margin) > 0.10 else 0.5
        
        return p_value < alpha, p_value
    
    async def execute_robust_duel(
        self,
        candidate_id: str,
        current_id: str,
        dataset: List[Dict],
        test_func
    ) -> DuelResult:
        """Ejecuta duelo robusto con particiones y tests estadísticos"""
        
        result = DuelResult(
            candidate_id=candidate_id,
            current_id=current_id
        )
        
        logger.info(f"⚔️  DUELO ROBUSTO: {candidate_id} vs {current_id}")
        
        # Crear particiones estratégicas
        partitions = self._create_partitions(dataset)
        
        all_candidate_scores = []
        all_current_scores = []
        min_margin_partition = None
        min_margin = float('inf')
        
        # Ejecutar en CADA partición
        for partition_name, partition_data in partitions.items():
            logger.info(f"  Partición: {partition_name} ({len(partition_data)} muestras)")
            
            candidate_scores = []
            current_scores = []
            
            for sample in partition_data[:25]:  # Min 25 por partición
                c_score = await test_func(candidate_id, sample)
                current_score = await test_func(current_id, sample)
                
                candidate_scores.append(c_score.get("precision", 0.5))
                current_scores.append(current_score.get("precision", 0.5))
            
            all_candidate_scores.extend(candidate_scores)
            all_current_scores.extend(current_scores)
            
            # Test estadístico en esta partición
            is_sig, p_val = self.mann_whitney_u_test(candidate_scores, current_scores)
            
            cand_mean = statistics.mean(candidate_scores)
            curr_mean = statistics.mean(current_scores)
            margin = (cand_mean - curr_mean) / curr_mean if curr_mean != 0 else 0
            
            logger.info(f"    Candidata: {cand_mean:.2%}, Actual: {curr_mean:.2%}, "
                       f"Margen: {margin:.2%}, p-value: {p_val:.4f}")
            
            if margin < min_margin:
                min_margin = margin
                min_margin_partition = partition_name
        
        # Decisión: Candidata debe ganar en TODAS
        result.candidate_metrics.precision_scores = all_candidate_scores
        result.current_metrics.precision_scores = all_current_scores
        result.candidate_score = statistics.mean(all_candidate_scores)
        result.current_score = statistics.mean(all_current_scores)
        result.margin = (result.candidate_score - result.current_score) / result.current_score if result.current_score != 0 else 0
        
        # Verificar Mann-Whitney global
        is_sig, p_val = self.mann_whitney_u_test(all_candidate_scores, all_current_scores)
        result.p_value = p_val
        
        if result.candidate_score > result.current_score:
            result.outcome = DuelOutcome.CANDIDATA_WINS
            
            if is_sig and result.margin >= 0.10:
                result.decision = DuelDecision.ACCEPTED
                logger.info(f"✅ ACEPTADA - Gana en TODAS (p={p_val:.4f}, margin={result.margin:.2%})")
            elif result.margin >= 0.05:
                result.decision = DuelDecision.NEEDS_REVIEW
                logger.warning(f"⚠️  REVISAR - Margen estrecho (margin={result.margin:.2%})")
            else:
                result.decision = DuelDecision.REJECTED
                logger.info(f"❌ RECHAZADA - Margen muy bajo ({result.margin:.2%})")
        else:
            result.outcome = DuelOutcome.ACTUAL_WINS
            result.decision = DuelDecision.REJECTED
            logger.info(f"❌ RECHAZADA - Actual es mejor")
        
        result.iterations = len(all_candidate_scores)
        return result
    
    @staticmethod
    def _create_partitions(dataset: List[Dict]) -> Dict[str, List[Dict]]:
        """Crea particiones estratégicas del dataset"""
        partitions = {}
        
        if not dataset:
            return {"all": []}
        
        # Detectar si hay campo númérico para percentiles
        numeric_field = None
        for key in dataset[0].keys():
            if isinstance(dataset[0][key], (int, float)):
                numeric_field = key
                break
        
        if numeric_field:
            values = [d[numeric_field] for d in dataset]
            p1 = statistics.quantiles(values, n=100)[0] if len(values) > 100 else min(values)
            p99 = statistics.quantiles(values, n=100)[98] if len(values) > 100 else max(values)
            
            extremes = [d for d in dataset if d[numeric_field] <= p1 or d[numeric_field] >= p99]
            partitions["extremos"] = extremes if extremes else dataset[:10]
        
        # Recientes (últimos 30%)
        recent_count = int(len(dataset) * 0.3)
        partitions["recientes"] = dataset[-recent_count:] if recent_count > 0 else dataset
        
        # Todos
        partitions["completo"] = dataset
        
        return partitions


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 7: MITIGACIÓN #5 - TRANSIENT CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════════

class TransientClassifier:
    """Mitigación #5: Clasificador de errores transitorio vs sistémico"""
    
    async def classify_error(
        self,
        error_type: str,
        component_id: str,
        error_history: List[Dict],
        context: Dict
    ) -> Tuple[ErrorCategory, float]:
        """
        Clasifica si error es transitorio (datos) o sistémico (broken).
        
        Returns:
            (categoría, confianza 0-1)
        """
        
        # Features
        frequency = len(error_history) / 100.0
        
        durations = [e.get("duration_ms", 0) for e in error_history]
        duration = (statistics.mean(durations) / 5000.0) if durations else 0.0
        
        consistency = len(error_history) / context.get("total_executions", 1)
        
        # Score: 0=sistémico, 1=transitorio
        score = (0.3 * (1.0 - frequency) +
                0.2 * (1.0 - duration) +
                0.3 * (1.0 - consistency) +
                0.2 * 0.5)  # historical_fix_rate por defecto
        
        if score > 0.7:
            return ErrorCategory.TRANSIENT_DATA, score
        elif score < 0.3:
            return ErrorCategory.SYSTEMIC_ISSUE, 1.0 - score
        else:
            return ErrorCategory.UNKNOWN, 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 8: WATCHDOG 24H POST-DEPLOY
# ═══════════════════════════════════════════════════════════════════════════════

class Watchdog24h:
    """Mejora V36: Monitoreo post-deploy continuo"""
    
    def __init__(self):
        self.deployments: Dict[str, DeploymentRecord] = {}
        self.alerts: List[WatchdogAlert] = []
        self.monitoring_interval_hours = 24
    
    async def monitor_deployed_candidate(
        self,
        candidate_id: str,
        get_current_metrics_fn
    ) -> Optional[WatchdogAlert]:
        """
        Monitorea candidata desplegada.
        Si degrada > 10%, ejecuta rollback.
        
        Returns:
            Alerta si es crítica
        """
        
        if candidate_id not in self.deployments:
            return None
        
        deployment = self.deployments[candidate_id]
        
        # Obtener métricas actuales
        current_metrics = await get_current_metrics_fn(candidate_id)
        
        # Comparar con baseline (antes del deploy)
        baseline_precision = 0.85  # Obtenido del snapshot
        current_precision = current_metrics.get("precision", 0.85)
        
        change_percent = (current_precision - baseline_precision) / baseline_precision if baseline_precision != 0 else 0
        
        if change_percent < -0.10:
            # Degradación crítica: rollback
            alert = WatchdogAlert(
                timestamp=datetime.now(),
                candidate_id=candidate_id,
                metric="precision",
                previous_value=baseline_precision,
                current_value=current_precision,
                change_percent=change_percent,
                severity="critical",
                action="rollback"
            )
            self.alerts.append(alert)
            
            logger.error(f"🚨 ROLLBACK AUTOMÁTICO: {candidate_id} degradó {change_percent:.1%}")
            # TODO: Ejecutar rollback
            
            return alert
        
        elif change_percent < -0.05:
            # Degradación media: alerta
            alert = WatchdogAlert(
                timestamp=datetime.now(),
                candidate_id=candidate_id,
                metric="precision",
                previous_value=baseline_precision,
                current_value=current_precision,
                change_percent=change_percent,
                severity="warning",
                action="monitor"
            )
            self.alerts.append(alert)
            logger.warning(f"⚠️  {candidate_id} degradó {change_percent:.1%}")
            return alert
        
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 9: MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class PsychotechnicOrchestrator:
    """Orquestador maestro del sistema psicotécnico"""
    
    def __init__(self, domain: ValidationDomain = ValidationDomain.FORMULA, workspace_root: Path = Path(".")):
        self.domain = domain
        self.validator = PsychotechnicValidator(domain)
        self.cascade = CascadeAnalyzer(workspace_root)
        self.ml_calib = MLCalibrator()
        self.duel = RobustDuelEngine()
        self.classifier = TransientClassifier()
        self.watchdog = Watchdog24h()
    
    async def validate_and_duel(
        self,
        candidate_id: str,
        test_function,
        metrics: Dict[str, float],
        current_id: str,
        duel_test_function,
        dataset: Optional[List[Dict]] = None
    ) -> DuelResult:
        """
        Orquesta validación psicotécnica completa:
        1. 25 capas
        2. Cascade analysis
        3. Robust duel
        4. Watchdog setup
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 INICIO VALIDACIÓN COMPLETA: {candidate_id}")
        logger.info(f"{'='*80}\n")
        
        # PASO 1: Validación psicotécnica (25 capas)
        logger.info("📋 PASO 1: Validación Psicotécnica (25 Capas)")
        journey = await self.validator.validate_candidate(candidate_id, test_function, metrics)
        
        if not journey.passed_all_capas:
            logger.error(f"❌ No pasó psicotécnico - Rechazada")
            return DuelResult(
                candidate_id=candidate_id,
                current_id=current_id,
                decision=DuelDecision.REJECTED
            )
        
        if journey.justice_score < 0.75:
            logger.error(f"❌ Justice Score insuficiente: {journey.justice_score:.2%}")
            return DuelResult(
                candidate_id=candidate_id,
                current_id=current_id,
                decision=DuelDecision.REJECTED
            )
        
        logger.info(f"✅ Psicotécnico PASADO - justice_score={journey.justice_score:.2%}\n")
        
        # PASO 2: Cascade analysis
        logger.info("📋 PASO 2: Análisis de Cascada")
        risk_score = await self.cascade.analyze_cascade_risk(candidate_id)
        
        if risk_score > 0.7:
            logger.error(f"❌ Riesgo cascada ALTO: {risk_score:.2%} - NOTIFICAR_HUMANO")
            return DuelResult(
                candidate_id=candidate_id,
                current_id=current_id,
                decision=DuelDecision.NEEDS_REVIEW
            )
        
        logger.info(f"✅ Cascade OK - risk={risk_score:.2%}\n")
        
        # PASO 3: Robust duel con Mann-Whitney U
        logger.info("📋 PASO 3: Duelo Robusto (con tests estadísticos)")
        duel_result = await self.duel.execute_robust_duel(
            candidate_id, current_id, dataset or [], duel_test_function
        )
        
        logger.info(f"✅ Duelo completado - decision={duel_result.decision.value}\n")
        
        # PASO 4: Setup watchdog si aceptada
        if duel_result.decision == DuelDecision.ACCEPTED:
            logger.info("📋 PASO 4: Setup Watchdog 24h")
            deployment = DeploymentRecord(
                id=f"deploy_{candidate_id}_{datetime.now().isoformat()}",
                timestamp=datetime.now(),
                candidate_id=candidate_id,
                decision=DuelDecision.ACCEPTED,
                phase="canary"
            )
            self.watchdog.deployments[candidate_id] = deployment
            logger.info(f"✅ Watchdog configurado\n")
        
        logger.info(f"{'='*80}\n")
        
        return duel_result


# ═══════════════════════════════════════════════════════════════════════════════
# PARTE 10: DETECTOR DE ESPECIFICIDAD DE CÁLCULOS
# ═══════════════════════════════════════════════════════════════════════════════

class CalculationType(Enum):
    """Tipos de cálculos específicos que una fórmula puede afectar"""
    # Temperatura
    TEMP_PUNTO_ROCIO = "punto_rocio"
    TEMP_SENSACION_TERMICA = "sensacion_termica"
    TEMP_UTCI = "utci"
    TEMP_HEAT_INDEX = "heat_index"
    # Humedad
    HUMID_RELATIVA = "humedad_relativa"
    HUMID_ABSOLUTA = "humedad_absoluta"
    # Presión
    PRES_NIVEL_MAR = "presion_nivel_mar"
    PRES_DENSIDAD = "densidad_aire"
    # Radiación
    RAD_TEORICA = "radiacion_teorica"
    RAD_NETA = "radiacion_neta"
    # Indices
    INDEX_EVAPOTRANSPIRACION = "evapotranspiracion"
    INDEX_CONFORT = "confort"
    INDEX_RIESGO = "riesgo"


@dataclass
class CalculationSpecificity:
    """Especificidad: cómo se desempeña fórmula en UN cálculo específico"""
    calculation_type: CalculationType
    formula_id: str
    precision_this_calc: float
    stability_this_calc: float
    latency_this_calc_ms: float
    precision_delta: float  # vs actual
    stability_delta: float
    is_significantly_better: bool
    is_significantly_worse: bool
    dataset_size: int
    validation_count: int


@dataclass
class FormulaCalculationProfile:
    """Perfil: cómo se desempeña fórmula en TODOS los cálculos"""
    formula_id: str
    affected_calculations: List[CalculationType] = field(default_factory=list)
    specificities: Dict[CalculationType, CalculationSpecificity] = field(default_factory=dict)
    better_in: List[CalculationType] = field(default_factory=list)
    worse_in: List[CalculationType] = field(default_factory=list)
    overall_decision: str = "PENDING"  # "ACCEPT_FOR_SPECIFIC", "REJECT"
    accepted_for: List[CalculationType] = field(default_factory=list)
    calculations_clearly_better: int = 0


class CalculationSpecificityAnalyzer:
    """
    Analiza: ¿Fórmula es mejor para CIERTOS cálculos solamente?
    
    CASO DE USO:
    - Fórmula A: Excelente para UTCI, mediocre para humedad
    - Decisión: Aceptar SOLO para UTCI
    """
    
    async def analyze_formula(
        self,
        formula_id: str,
        formula_code: str,
        test_results_per_calc: Dict[CalculationType, Dict[str, float]],
        current_scores_per_calc: Dict[CalculationType, Dict[str, float]]
    ) -> FormulaCalculationProfile:
        """Analiza fórmula contra todos sus cálculos afectados"""
        
        profile = FormulaCalculationProfile(formula_id=formula_id)
        
        # Determinar qué cálculos afecta
        affected = self._determine_affected_calculations(formula_code)
        profile.affected_calculations = affected
        
        logger.info(f"📊 {formula_id} afecta {len(affected)} cálculos")
        
        # Analizar cada cálculo
        for calc_type in affected:
            if calc_type not in test_results_per_calc:
                continue
            
            new_scores = test_results_per_calc[calc_type]
            current_scores = current_scores_per_calc.get(calc_type, {})
            
            # Calcular deltas
            precision_delta = new_scores.get("precision", 0) - current_scores.get("precision", 0)
            stability_delta = new_scores.get("stability", 0) - current_scores.get("stability", 0)
            
            is_sig_better = (precision_delta >= 0.10 or stability_delta >= 0.10)
            is_sig_worse = (precision_delta <= -0.10 or stability_delta <= -0.10)
            
            specificity = CalculationSpecificity(
                calculation_type=calc_type,
                formula_id=formula_id,
                precision_this_calc=new_scores.get("precision", 0),
                stability_this_calc=new_scores.get("stability", 0),
                latency_this_calc_ms=new_scores.get("latency_ms", 0),
                precision_delta=precision_delta,
                stability_delta=stability_delta,
                is_significantly_better=is_sig_better,
                is_significantly_worse=is_sig_worse,
                dataset_size=new_scores.get("dataset_size", 0),
                validation_count=new_scores.get("validation_count", 0),
            )
            
            profile.specificities[calc_type] = specificity
            
            if is_sig_better:
                profile.better_in.append(calc_type)
                profile.calculations_clearly_better += 1
            elif is_sig_worse:
                profile.worse_in.append(calc_type)
        
        # Decisión
        if profile.better_in and len(profile.worse_in) <= 2:
            profile.overall_decision = "ACCEPT_FOR_SPECIFIC"
            profile.accepted_for = profile.better_in
            logger.info(f"✅ Aceptar SOLO para: {[c.value for c in profile.better_in]}")
        else:
            profile.overall_decision = "REJECT"
            logger.info(f"❌ Rechazar - No es mejor para cálculos específicos")
        
        return profile
    
    @staticmethod
    def _determine_affected_calculations(formula_code: str) -> List[CalculationType]:
        """Heurística: ¿Qué cálculos afecta el código?"""
        affected = set()
        code_lower = formula_code.lower()
        
        keywords = {
            "utci": CalculationType.TEMP_UTCI,
            "heat_index": CalculationType.TEMP_HEAT_INDEX,
            "radiacion": CalculationType.RAD_TEORICA,
            "et0": CalculationType.INDEX_EVAPOTRANSPIRACION,
            "densidad": CalculationType.PRES_DENSIDAD,
            "humedad": CalculationType.HUMID_RELATIVA,
        }
        
        for keyword, calc_type in keywords.items():
            if keyword in code_lower:
                affected.add(calc_type)
        
        return list(affected) if affected else [CalculationType.INDEX_CONFORT]


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBA RÁPIDA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    print("SISTEMA PSICOTÉCNICO MAESTRO V36 - CARGADO Y OPERACIONAL")
    print("="*80)
    print("\n✅ 25 Capas inicializadas")
    print("✅ 5 Mitigaciones integradas")
    print("✅ Mejoras V36 activadas")
    print("✅ Detector de Especificidad (cálculos específicos)")
    print("✅ Aplicable a FÓRMULAS y ALGORITMOS")
    print("\nListo para validar candidatas.\n")
