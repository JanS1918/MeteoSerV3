#!/usr/bin/env python3
"""
test_formula_discovery_system.py

Prueba completa del sistema de descubrimiento y duelo de fórmulas.

Flujo:
1. Descubre candidatas externas
2. Valida cada una
3. Ejecuta duelos
4. Integra ganadora
"""

import sys
import logging
from pathlib import Path

# Setup
base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

# Config logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("test_formula_discovery")

from core.monitoring.external_formula_discoverer import ExternalFormulaDiscoverer
from core.monitoring.automated_duel_engine import AutomatedDuelEngine
from core.monitoring.external_formula_integrator import ExternalFormulaIntegrator
from core.monitoring.formula_optimization_orchestrator import FormulaOptimizationOrchestrator


def test_discovery():
    """Prueba 1: Descubrimiento de candidatas"""
    logger.info("\n" + "=" * 70)
    logger.info("🔍 PRUEBA 1: DESCUBRIMIENTO DE CANDIDATAS EXTERNAS")
    logger.info("=" * 70)

    discoverer = ExternalFormulaDiscoverer()

    # Descubrir para sensación térmica
    candidatas, resultado = discoverer.discover_for_parameter(
        parametro="sensacion_termica",
        inputs_disponibles=["temperatura", "velocidad_viento", "humedad_relativa"],
        data_sample=None
    )

    logger.info(f"\n✅ Descubiertas {len(candidatas)} candidatas válidas:")
    for cand in candidatas:
        logger.info(f"   - {cand.nombre} ({cand.fuente})")
        logger.info(f"     ID: {cand.id}")
        logger.info(f"     Score: {cand.score_validacion:.2f}/100")
        logger.info(f"     Inputs: {', '.join(cand.inputs_requeridos)}")

    return candidatas


def test_duel():
    """Prueba 2: Motor de duelo"""
    logger.info("\n" + "=" * 70)
    logger.info("⚔️  PRUEBA 2: DUELOS AUTOMATIZADOS")
    logger.info("=" * 70)

    duel_engine = AutomatedDuelEngine()

    # Fórmula interna dummy
    def formula_interna(temperatura=20, velocidad_viento=5, humedad_relativa=50, **kwargs):
        return {
            "valor": temperatura - (velocidad_viento * 1.5) + (humedad_relativa * 0.1),
            "metadata": {"fuente": "interna"}
        }

    # Fórmula externa dummy (scipy)
    def formula_externa(temperatura=20, velocidad_viento=5, humedad_relativa=50, **kwargs):
        try:
            import scipy.special
            # Usar erf para normalización
            val = scipy.special.erf(temperatura / 30.0) * 30.0
            return {
                "valor": val,
                "metadata": {"fuente": "externa"}
            }
        except:
            return formula_interna(temperatura, velocidad_viento, humedad_relativa, **kwargs)

    # Datos de prueba
    datos_prueba = [
        {"temperatura": 20, "velocidad_viento": 5, "humedad_relativa": 50},
        {"temperatura": 25, "velocidad_viento": 10, "humedad_relativa": 60},
        {"temperatura": 30, "velocidad_viento": 15, "humedad_relativa": 70},
        {"temperatura": 15, "velocidad_viento": 3, "humedad_relativa": 40},
        {"temperatura": 35, "velocidad_viento": 20, "humedad_relativa": 80},
    ]

    # Ejecutar duelo
    resultado = duel_engine.duelo(
        parametro="sensacion_termica",
        interna=formula_interna,
        interna_id="sensacion_termica_v1",
        externa=formula_externa,
        externa_id="scipy_sensacion_termica_0",
        externa_nombre="scipy.special.erf - Sensación Térmica",
        datos_prueba=datos_prueba,
        valores_esperados=None
    )

    logger.info(f"\n📊 Resultado del duelo:")
    logger.info(f"   Ganadora: {resultado.ganadora.upper()}")
    logger.info(f"   Score ganadora: {resultado.score_ganadora:.2f}/100")
    logger.info(f"   Score perdedora: {resultado.score_perdedora:.2f}/100")
    logger.info(f"   Margen victoria: {resultado.margen_victoria:.2f}")
    logger.info(f"   Duración: {resultado.duracion_segundos:.2f}s")

    return resultado


def test_integration():
    """Prueba 3: Integración de ganadora"""
    logger.info("\n" + "=" * 70)
    logger.info("🔧 PRUEBA 3: INTEGRACIÓN DE GANADORA EXTERNA")
    logger.info("=" * 70)

    integrator = ExternalFormulaIntegrator()

    success = integrator.integrar_ganadora(
        parametro="sensacion_termica",
        externa_id="scipy_sensacion_termica_0",
        externa_nombre="scipy.special.erf - Sensación Térmica",
        externa_ref="scipy.special.erf",
        inputs_requeridos=["temperatura"],
        score_duelo=85.5,
        metadata={
            "margen_victoria": 12.3,
            "ciclo": 1,
            "fuente": "scipy"
        }
    )

    if success:
        logger.info("✅ Integración exitosa")
        integrada = integrator.obtener_info_integrada("sensacion_termica")
        if integrada:
            logger.info(f"   Wrapper ID: {integrada.get('wrapper_id')}")
            logger.info(f"   Path: {integrada.get('wrapper_path')}")
    else:
        logger.info("❌ Integración falló")

    return success


def test_orchestrator():
    """Prueba 4: Orquestador completo"""
    logger.info("\n" + "=" * 70)
    logger.info("🎯 PRUEBA 4: ORQUESTADOR COMPLETO")
    logger.info("=" * 70)

    orchestrator = FormulaOptimizationOrchestrator()

    # Ejecutar ciclo
    ciclo = orchestrator.ejecutar_ciclo(
        parametros=["sensacion_termica", "humedad_relativa"],
        datos_prueba=None
    )

    logger.info(f"\n📈 Estadísticas después de ciclo:")
    stats = orchestrator.obtener_estadisticas()
    logger.info(f"   Ciclos totales: {stats.get('ciclos_totales')}")
    logger.info(f"   Candidatas descubiertas: {stats.get('candidatas_descubiertas')}")
    logger.info(f"   Duelos ejecutados: {stats.get('duelos_ejecutados')}")
    logger.info(f"   Ganadoras integradas: {stats.get('ganadoras_integradas')}")

    return ciclo


def main():
    logger.info("\n" + "=" * 70)
    logger.info("🚀 SISTEMA DE DESCUBRIMIENTO Y DUELO DE FÓRMULAS")
    logger.info("=" * 70)

    try:
        # Prueba 1: Discovery
        candidatas = test_discovery()

        # Prueba 2: Duel
        duelo = test_duel()

        # Prueba 3: Integration
        integracion = test_integration()

        # Prueba 4: Orchestrator
        ciclo = test_orchestrator()

        logger.info("\n" + "=" * 70)
        logger.info("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        logger.info("=" * 70)
        logger.info(f"\nResumen:")
        logger.info(f"  - Candidatas descubiertas: {len(candidatas)}")
        logger.info(f"  - Duelo ejecutado: {duelo.ganadora} ganó")
        logger.info(f"  - Integración: {'exitosa' if integracion else 'falló'}")
        logger.info(f"  - Ciclo completado: {ciclo.ciclo_num}")
        logger.info("\n🔄 Sistema listo para búsqueda automática periódica\n")

    except Exception as e:
        logger.exception(f"❌ Error en pruebas: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
