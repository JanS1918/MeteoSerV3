#!/usr/bin/env python3
"""
run_continuous_optimization.py

Ejecuta el sistema de optimización de fórmulas en modo continuo (background).

Uso:
    python run_continuous_optimization.py --interval 60  # Ejecutar cada 60 minutos
    python run_continuous_optimization.py --once         # Ejecutar una sola vez
"""

import sys
import logging
import argparse
import time
from pathlib import Path
from threading import Thread
from datetime import datetime, timezone, timedelta

# Setup
base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("optimizer_runner")

from core.monitoring.formula_optimization_orchestrator import FormulaOptimizationOrchestrator


class OptimizationScheduler:
    """Planificador de ciclos de optimización."""

    def __init__(self, intervalo_minutos: int = 60):
        self.intervalo_minutos = intervalo_minutos
        self.intervalo_segundos = intervalo_minutos * 60
        self.orchestrator = FormulaOptimizationOrchestrator()
        self.corriendo = False
        self.proximo_ciclo = None

    def ejecutar_una_vez(self) -> None:
        """Ejecuta un ciclo y termina."""
        logger.info("🚀 Ejecutando ciclo de optimización (una sola vez)")
        try:
            ciclo = self.orchestrator.ejecutar_ciclo()
            self._log_resumen(ciclo)
        except Exception as e:
            logger.exception(f"❌ Error en ciclo: {e}")

    def ejecutar_continuo(self) -> None:
        """Ejecuta ciclos periódicamente en background."""
        logger.info(f"🔄 Iniciando modo continuo (intervalo: {self.intervalo_minutos} min)")
        logger.info(f"   Próximo ciclo en {self.intervalo_segundos} segundos")

        self.corriendo = True

        try:
            while self.corriendo:
                self.proximo_ciclo = datetime.now(timezone.utc) + timedelta(seconds=self.intervalo_segundos)

                logger.info(f"\n📅 Próximo ciclo programado para: {self.proximo_ciclo.isoformat()}")

                # Dormir hasta próximo ciclo
                time.sleep(self.intervalo_segundos)

                if not self.corriendo:
                    break

                # Ejecutar ciclo
                try:
                    logger.info(f"\n⏰ Iniciando ciclo en: {datetime.now(timezone.utc).isoformat()}")
                    ciclo = self.orchestrator.ejecutar_ciclo()
                    self._log_resumen(ciclo)

                except Exception as e:
                    logger.exception(f"❌ Error en ciclo: {e}")

        except KeyboardInterrupt:
            logger.info("\n⏹️  Deteniendo scheduler...")
            self.corriendo = False

    def _log_resumen(self, ciclo) -> None:
        """Registra resumen del ciclo."""
        logger.info(f"\n📊 RESUMEN CICLO #{ciclo.ciclo_num}:")
        logger.info(f"   ✅ Parámetros procesados: {ciclo.parametros_procesados}")
        logger.info(f"   🔍 Candidatas descubiertas: {ciclo.candidatas_descubiertas}")
        logger.info(f"   ⚔️  Duelos ejecutados: {ciclo.duelos_ejecutados}")
        logger.info(f"   🏆 Ganadoras externas: {ciclo.ganadoras_externas}")
        logger.info(f"   🔧 Integraciones exitosas: {ciclo.integraciones_exitosas}")
        logger.info(f"   ⏱️  Duración: {ciclo.duracion_segundos:.1f}s")

        if ciclo.integraciones_exitosas > 0:
            logger.info(f"\n   🎉 {ciclo.integraciones_exitosas} fórmula(s) externa(s) integrada(s)")
            for detalle in ciclo.detalles:
                if detalle.get("status") == "integrada":
                    logger.info(f"       - {detalle.get('candidata')}")


def main():
    parser = argparse.ArgumentParser(
        description="Ejecutor de ciclos de optimización de fórmulas"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Intervalo entre ciclos en minutos (default: 60)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecutar solo una vez y terminar"
    )

    args = parser.parse_args()

    logger.info("\n" + "=" * 70)
    logger.info("🎯 OPTIMIZADOR AUTOMÁTICO DE FÓRMULAS - SISTEMA CONTINUO")
    logger.info("=" * 70)

    scheduler = OptimizationScheduler(intervalo_minutos=args.interval)

    if args.once:
        scheduler.ejecutar_una_vez()
    else:
        try:
            scheduler.ejecutar_continuo()
        except KeyboardInterrupt:
            logger.info("\n✅ Optimizer finalizado")
            sys.exit(0)


if __name__ == "__main__":
    main()
