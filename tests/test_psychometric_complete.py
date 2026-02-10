#!/usr/bin/env python3
"""
test_psychometric_complete.py - TESTS DE INTEGRACIÓN COMPLETA

Sistema Psicotécnico 7 Fases + Duelo + Auto-Corrección Global

COBERTURA:
1. Test intelligently_capa_flow (orquestador)
2. Test orchestrador_duelo (batalla justa)
3. Test auto_system_optimizer (auto-corrección)
4. Test formula_calculation_specificity (cálculos específicos)
5. Test integración end-to-end (fórmula externa → decisión final)
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List
from datetime import datetime

# Imports de sistema
try:
    from core.engines.intelligent_capa_flow import (
        CapaFlowOrchestrator, FormulaJourney, TestResult, CapaPriority, RepairabilityLevel
    )
    from core.engines.orchestrador_duelo import OrchestradorDuelo, DuelResult, DuelMetrics
    from core.engines.auto_system_optimizer import AutoSystemOptimizer, DetectedProblem
    from core.engines.formula_calculation_specificity import (
        FormulaCalculationAnalyzer, CalculationType, FormulaCalculationProfile
    )
except ModuleNotFoundError as exc:
    pytest.skip(f"Modulos de core.engines no disponibles: {exc}", allow_module_level=True)

logger = logging.getLogger(__name__)


class TestIntelligentCapaFlow:
    """Tests para orquestación de 7 fases"""
    
    @pytest.fixture
    def orchestrator(self):
        """Crear instancia de orquestador"""
        return CapaFlowOrchestrator()
    
    @pytest.mark.asyncio
    async def test_formula_journey_creation(self, orchestrator):
        """Test: Una fórmula inicia un viaje completo"""
        formula_id = "test_formula_v1"
        test_metrics = {"precision": 0.95, "stability": 0.80, "fluidity": 0.75}
        
        # Crear mock de test function
        async def mock_test(capa_id, formula_id):
            return TestResult(
                capa_id=capa_id,
                formula_id=formula_id,
                passed=True,
                latency_ms=50.0,
                confidence=0.95
            )
        
        # Ejecutar
        journey = await orchestrator.intelligent_test_formula(
            formula_id=formula_id,
            test_func=mock_test,
            formula_metrics=test_metrics
        )
        
        # Validaciones
        assert journey.formula_id == formula_id
        assert journey.justice_score >= 0.0
        assert journey.start_time is not None
        logger.info(f"✅ Journey creado para {formula_id}, justice_score={journey.justice_score:.2f}")
    
    @pytest.mark.asyncio
    async def test_critical_capas_early_exit(self, orchestrator):
        """Test: CAPA 1 (crítica) hace exit temprano si falla"""
        formula_id = "test_critical_failure"
        
        # CAPA 1 falla
        async def mock_test_with_failure(capa_id, formula_id):
            if capa_id == 1:  # CAPA 1 crítica
                return TestResult(
                    capa_id=1,
                    formula_id=formula_id,
                    passed=False,
                    latency_ms=100.0,
                    error_type="precision_fail",
                    repairability=RepairabilityLevel.NOT_REPAIRABLE,
                    confidence=0.0
                )
            # No debería llegar aquí
            raise AssertionError("No debería probar CAPA 2 si CAPA 1 falló")
        
        journey = await orchestrator.intelligent_test_formula(
            formula_id=formula_id,
            test_func=mock_test_with_failure,
            formula_metrics={"precision": 0.95, "stability": 0.80, "fluidity": 0.75}
        )
        
        # Validaciones
        assert journey.justice_score == 0.0  # Rechaza inmediatamente
        assert 1 in journey.failed_capas
        logger.info(f"✅ Early exit en CAPA crítica detectado")
    
    @pytest.mark.asyncio
    async def test_retry_logic_flexible_capas(self, orchestrator):
        """Test: CAPA flexible falla pero se reintenta si similar pasó"""
        formula_id = "test_flexible_retry"
        retry_count = {"count": 0}
        
        async def mock_test_with_retry(capa_id, formula_id):
            # CAPA 14 falla primera vez, pasa segunda (similar CAPA 16 pasó)
            if capa_id == 14:
                retry_count["count"] += 1
                return TestResult(
                    capa_id=14,
                    formula_id=formula_id,
                    passed=(retry_count["count"] > 1),  # Pasa en retry
                    latency_ms=100.0,
                    confidence=0.95,
                    retry_count=retry_count["count"]
                )
            return TestResult(capa_id=capa_id, formula_id=formula_id, passed=True, latency_ms=50.0)
        
        journey = await orchestrator.intelligent_test_formula(
            formula_id=formula_id,
            test_func=mock_test_with_retry,
            formula_metrics={"precision": 0.95, "stability": 0.80, "fluidity": 0.75}
        )
        
        # Validaciones
        assert journey.retested_count > 0
        logger.info(f"✅ Retry logic funcionó, reintento={journey.retested_count}")
    
    @pytest.mark.asyncio
    async def test_justice_score_calculation(self, orchestrator):
        """Test: Justice_score = 0.5*precision + 0.3*stability + 0.2*repair"""
        journey = FormulaJourney(formula_id="test_formula")
        
        # Métricas simuladas
        precision = 0.95
        stability = 0.80
        repair_factor = 0.75
        
        # Calcular (internamente)
        expected_justice = (0.5 * precision) + (0.3 * stability) + (0.2 * repair_factor)
        expected_justice = expected_justice  # ponderada, no promediada
        
        # Ejecutar cálculo
        orchestrator._calculate_justice_score(journey, precision, stability, repair_factor)
        
        # Validar
        assert abs(journey.justice_score - expected_justice) < 0.01
        assert journey.justice_score >= 0.55  # Mínimo aceptable
        logger.info(f"✅ Justice score calculado: {journey.justice_score:.3f}")


class TestOrchestradorDuelo:
    """Tests para lógica de duelo"""
    
    @pytest.fixture
    def duel_engine(self):
        """Crear orquestador de duelo"""
        return OrchestradorDuelo()
    
    @pytest.mark.asyncio
    async def test_duel_execution_basic(self, duel_engine):
        """Test: Duelo básico ejecuta correctamente"""
        
        # Simular duelo donde candidata gana claro
        async def mock_duel_test(formula_id, iteration):
            # Candidata siempre mejor
            if "candidata" in formula_id:
                return {
                    "precision": 0.95,
                    "stability": 0.90,
                    "fluidity": 0.85,
                    "latency_ms": 100.0,
                    "errors": 0
                }
            else:  # actual
                return {
                    "precision": 0.80,
                    "stability": 0.75,
                    "fluidity": 0.70,
                    "latency_ms": 150.0,
                    "errors": 0
                }
        
        result = await duel_engine.ejecutar_duelo(
            candidata_id="candidata_v1",
            justice_score=0.80,  # Pasó psicotécnico
            actual_id="actual_v1",
            test_func=mock_duel_test,
            iterations=50
        )
        
        # Validaciones
        assert result.decision == "ACCEPTED"  # Margen claro
        assert result.margin >= 0.10  # Margen >= 10%
        logger.info(f"✅ Duelo completado: decision={result.decision}, margin={result.margin:.2f}")
    
    @pytest.mark.asyncio
    async def test_duel_narrow_margin(self, duel_engine):
        """Test: Margen 5-10% → NEEDS_REVIEW"""
        
        async def mock_duel_narrow(formula_id, iteration):
            if "candidata" in formula_id:
                return {"precision": 0.80, "stability": 0.80, "fluidity": 0.80, "latency_ms": 100, "errors": 0}
            else:
                return {"precision": 0.76, "stability": 0.76, "fluidity": 0.76, "latency_ms": 105, "errors": 0}
        
        result = await duel_engine.ejecutar_duelo(
            candidata_id="candidata_narrow",
            justice_score=0.75,
            actual_id="actual",
            test_func=mock_duel_narrow,
            iterations=50
        )
        
        # Validaciones
        assert result.decision == "NEEDS_REVIEW"  # Margen 5-10%
        assert 0.05 <= result.margin < 0.10
        logger.info(f"✅ Narrow margin detectado: decision={result.decision}")
    
    @pytest.mark.asyncio
    async def test_justice_score_check(self, duel_engine):
        """Test: Si justice_score < 0.75 → REJECTED"""
        
        result = await duel_engine.ejecutar_duelo(
            candidata_id="candidata_low_justice",
            justice_score=0.70,  # Muy bajo
            actual_id="actual",
            test_func=AsyncMock(),
            iterations=1
        )
        
        assert result.decision == "REJECTED"
        logger.info(f"✅ Low justice score detectado y rechazado")


class TestAutoSystemOptimizer:
    """Tests para auto-optimización"""
    
    @pytest.fixture
    def optimizer(self):
        """Crear optimizador"""
        return AutoSystemOptimizer()
    
    @pytest.mark.asyncio
    async def test_problem_detection_incomplete(self, optimizer):
        """Test: Detectar fórmula incompleta"""
        
        # Simular fórmula con parámetros faltantes
        metrics = {
            "formula_utci": {
                "parameters": ["T", "RH"],  # Faltan "wind_speed", "radiacion"
                "precision": 0.85,
                "stability": 0.70,
            }
        }
        
        problems = await optimizer._analizar_formulas(metrics)
        
        # Validaciones
        assert len(problems) > 0
        assert any(p.problem_type.name == "FORMULA_INCOMPLETE" for p in problems)
        logger.info(f"✅ Fórmula incompleta detectada: {len(problems)} problemas")
    
    @pytest.mark.asyncio
    async def test_candidate_generation(self, optimizer):
        """Test: Generar candidata corregida"""
        
        problem = DetectedProblem(
            component_id="utci_v1",
            problem_type="FORMULA_INCOMPLETE",
            severity=0.7,
            root_cause="Falta parámetro: wind_speed",
            fix_proposal="Agregar wind_speed con default 2.0 m/s",
            can_be_fixed=True,
            is_transient=False
        )
        
        metrics = {"precision": 0.85, "stability": 0.70}
        
        candidata = await optimizer._generar_candidata_corregida(problem, metrics)
        
        # Validaciones
        assert candidata.candidata_id is not None
        assert len(candidata.cambios) > 0
        assert candidata.codigo_nuevo is not None
        logger.info(f"✅ Candidata generada: {candidata.candidata_id}")
    
    @pytest.mark.asyncio
    async def test_auto_deploy_decision(self, optimizer):
        """Test: Decidir si auto-deployar según margen"""
        
        # Margen >= 5%
        action1 = optimizer._decidir_accion(margin_mejora=0.07, formula_id="test1")
        assert action1.value == "AUTO_DEPLOY"
        
        # Margen 2-5%
        action2 = optimizer._decidir_accion(margin_mejora=0.03, formula_id="test2")
        assert action2.value == "NOTIFY_HUMAN"
        
        # Margen < 2%
        action3 = optimizer._decidir_accion(margin_mejora=0.01, formula_id="test3")
        assert action3.value == "IGNORE"
        
        logger.info(f"✅ Auto-deploy decision logic validado")


class TestFormulaCalculationSpecificity:
    """Tests para análisis de cálculos específicos"""
    
    @pytest.fixture
    def analyzer(self):
        """Crear analizador"""
        return FormulaCalculationAnalyzer()
    
    def test_determine_affected_calculations(self, analyzer):
        """Test: ¿Qué cálculos afecta la fórmula?"""
        
        code = """
        def calculate_utci(temperature, humidity, wind_speed, radiation):
            # UTCI calculation
            return utci_value
        """
        
        affected = analyzer._determine_affected_calculations(code)
        
        assert CalculationType.TEMP_UTCI in affected
        assert CalculationType.TEMP_SENSACION_TERMICA in affected
        logger.info(f"✅ Cálculos afectados identificados: {len(affected)}")
    
    def test_analyze_better_in_specific_calculation(self, analyzer):
        """Test: Fórmula mejor en UN cálculo específico"""
        
        test_results = {
            CalculationType.TEMP_UTCI: {
                "precision": 0.95,      # Nueva
                "stability": 0.85,
                "fluidity": 0.80,
                "latency_ms": 100,
                "dataset_size": 1000,
                "validation_count": 100,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        current_scores = {
            CalculationType.TEMP_UTCI: {
                "precision": 0.80,      # Actual
                "stability": 0.75,
                "fluidity": 0.70,
            }
        }
        
        profile = analyzer.analyze_formula(
            formula_id="formula_utci_mejorada",
            formula_code="def calc(): pass",
            test_results=test_results,
            current_reference_scores=current_scores
        )
        
        # Validaciones
        assert profile.overall_decision == "ACCEPT_FOR_SPECIFIC"
        assert CalculationType.TEMP_UTCI in profile.better_in
        assert CalculationType.TEMP_UTCI in profile.accepted_for
        logger.info(f"✅ Fórmula aceptada para cálculo específico: {profile.decision_reason}")
    
    def test_reject_if_better_nowhere(self, analyzer):
        """Test: Rechazar si NO es mejor en ningún lado"""
        
        test_results = {
            CalculationType.TEMP_UTCI: {
                "precision": 0.75,      # Peor que actual
                "stability": 0.70,
                "fluidity": 0.65,
                "latency_ms": 200,
                "dataset_size": 1000,
                "validation_count": 100,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        current_scores = {
            CalculationType.TEMP_UTCI: {
                "precision": 0.85,
                "stability": 0.80,
                "fluidity": 0.75,
            }
        }
        
        profile = analyzer.analyze_formula(
            formula_id="formula_peor",
            formula_code="def calc(): pass",
            test_results=test_results,
            current_reference_scores=current_scores
        )
        
        assert profile.overall_decision == "REJECT"
        logger.info(f"✅ Fórmula rechazada correctamente")


class TestEndToEndIntegration:
    """Tests de integración end-to-end"""
    
    @pytest.mark.asyncio
    async def test_formula_external_to_final_decision(self):
        """Test: Fórmula externa → Psicotécnico → Duelo → Decisión final"""
        
        logger.info("🚀 TEST END-TO-END: FÓRMULA EXTERNA → DECISIÓN FINAL")
        
        # 1. Crear componentes
        orchestrator = CapaFlowOrchestrator()
        duel_engine = OrchestradorDuelo()
        
        # 2. Simular fórmula externa
        external_formula_id = "external_formula_v2.1.0"
        formula_metrics = {
            "precision": 0.92,
            "stability": 0.85,
            "fluidity": 0.80
        }
        
        # 3. PSICOTÉCNICO: 7 fases
        async def mock_test(capa_id, formula_id):
            # Simular: todas pasan
            return TestResult(
                capa_id=capa_id,
                formula_id=formula_id,
                passed=True,
                latency_ms=50.0,
                confidence=0.95
            )
        
        journey = await orchestrator.intelligent_test_formula(
            formula_id=external_formula_id,
            test_func=mock_test,
            formula_metrics=formula_metrics
        )
        
        logger.info(f"📊 Psicotécnico completado: justice_score={journey.justice_score:.3f}")
        
        # 4. DUELO: Si pasó psicotécnico
        if journey.justice_score >= 0.75:
            async def mock_duel(formula_id, iteration):
                if "external" in formula_id:
                    return {"precision": 0.92, "stability": 0.85, "fluidity": 0.80, "latency_ms": 100, "errors": 0}
                return {"precision": 0.85, "stability": 0.78, "fluidity": 0.72, "latency_ms": 120, "errors": 0}
            
            duel_result = await duel_engine.ejecutar_duelo(
                candidata_id=external_formula_id,
                justice_score=journey.justice_score,
                actual_id="actual_formula_current",
                test_func=mock_duel,
                iterations=100
            )
            
            logger.info(f"⚔️  Duelo completado: decision={duel_result.decision}, margin={duel_result.margin:.2%}")
            
            # 5. DECISIÓN FINAL
            if duel_result.decision == "ACCEPTED":
                logger.info(f"✅ ACEPTADA: {external_formula_id} → Integrar en sistema")
            elif duel_result.decision == "NEEDS_REVIEW":
                logger.info(f"⚠️  REVISAR: {external_formula_id} → Requiere validación humana")
            else:
                logger.info(f"❌ RECHAZADA: {external_formula_id}")
        else:
            logger.info(f"❌ RECHAZADA EN PSICOTÉCNICO: justice_score={journey.justice_score:.3f}")
        
        # Validaciones finales
        assert journey is not None
        assert journey.justice_score >= 0.0
        assert journey.justice_score <= 1.0
        logger.info(f"✅ TEST END-TO-END COMPLETADO")


# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
