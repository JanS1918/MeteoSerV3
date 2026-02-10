#!/usr/bin/env python3
"""
FormulaOptimizationOrchestrator: Orquestación automática de búsqueda + duelo + integración

Ejecuta en ciclos:
1. Descubre candidatas externas
2. Las valida
3. Duelo con interna
4. Integra ganadora si es externa
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

from core.monitoring.external_formula_discoverer import ExternalFormulaDiscoverer
from core.monitoring.automated_duel_engine import AutomatedDuelEngine
from core.monitoring.external_formula_integrator import ExternalFormulaIntegrator

logger = logging.getLogger("meteoser.formula_optimization_orchestrator")


@dataclass
class OptimizationCycle:
    """Un ciclo de optimización"""
    timestamp: float
    ciclo_num: int
    parametros_procesados: int
    candidatas_descubiertas: int
    duelos_ejecutados: int
    ganadoras_externas: int
    integraciones_exitosas: int
    duracion_segundos: float
    detalles: List[Dict[str, Any]]


class FormulaOptimizationOrchestrator:
    """
    Orquestador principal del sistema de mejora automática de fórmulas.
    
    Flujo:
    1. Descubrir candidatas externas para parámetros clave
    2. Validar cada candidata
    3. Para cada candidata válida, ejecutar duelo
    4. Si externa gana, integrarla
    5. Registrar todo
    
    Se ejecuta periódicamente (configurable).
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar motores
        self.discoverer = ExternalFormulaDiscoverer(base_dir)
        self.duel_engine = AutomatedDuelEngine(base_dir)
        self.integrator = ExternalFormulaIntegrator(base_dir)

        # Config
        self.cycles_file = self.data_dir / "optimization_cycles.json"
        self.config_file = self.data_dir / "optimization_config.json"

        self._cycles: List[Dict[str, Any]] = []
        self._ciclo_counter = 0
        self._load_cycles()
        self._load_config()

    def _load_cycles(self) -> None:
        """Carga histórico de ciclos."""
        if not self.cycles_file.exists():
            self._cycles = []
            return
        try:
            raw = json.loads(self.cycles_file.read_text(encoding="utf-8"))
            self._cycles = raw.get("ciclos", [])
            self._ciclo_counter = len(self._cycles)
        except Exception as e:
            logger.exception(f"Error cargando ciclos: {e}")
            self._cycles = []

    def _load_config(self) -> None:
        """Carga configuración de optimización."""
        if not self.config_file.exists():
            self.config = {
                "enabled": True,
                "intervalo_minutos": 60,
                "parametros_prioridad": [
                    "sensacion_termica",
                    "humedad_relativa",
                    "punto_rocio",
                    "indice_calor",
                    "radiacion_solar"
                ],
                "minimo_score_ganadora_externa": 75.0,
                "minimo_margen_victoria": 5.0,
                "max_candidatas_por_parametro": 5
            }
            self._save_config()
        else:
            try:
                self.config = json.loads(self.config_file.read_text(encoding="utf-8"))
            except Exception:
                self.config = {}

    def _save_config(self) -> None:
        """Guarda configuración."""
        try:
            self.config_file.write_text(
                json.dumps(self.config, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            logger.exception(f"Error guardando config: {e}")

    def _save_cycles(self) -> None:
        """Guarda histórico de ciclos."""
        try:
            payload = {"ciclos": self._cycles[-100:]}  # Últimos 100
            self.cycles_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            logger.exception(f"Error guardando ciclos: {e}")

    def ejecutar_ciclo(
        self,
        parametros: Optional[List[str]] = None,
        datos_prueba: Optional[Dict[str, List[Dict[str, float]]]] = None
    ) -> OptimizationCycle:
        """
        Ejecuta un ciclo completo de optimización.

        Args:
            parametros: lista de parámetros a optimizar
                       (si None, usa prioridades de config)
            datos_prueba: dict {parametro: [datos]} para duelos
                         (si None, genera dummy data)

        Returns:
            OptimizationCycle con resultado
        """
        self._ciclo_counter += 1
        inicio = time.time()

        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 CICLO DE OPTIMIZACIÓN #{self._ciclo_counter}")
        logger.info(f"{'='*60}\n")

        if parametros is None:
            parametros = self.config.get("parametros_prioridad", [])

        ciclo = OptimizationCycle(
            timestamp=datetime.now(timezone.utc).timestamp(),
            ciclo_num=self._ciclo_counter,
            parametros_procesados=0,
            candidatas_descubiertas=0,
            duelos_ejecutados=0,
            ganadoras_externas=0,
            integraciones_exitosas=0,
            duracion_segundos=0,
            detalles=[]
        )

        # === Procesar cada parámetro ===
        for parametro in parametros:
            logger.info(f"\n📋 Procesando: {parametro}")

            # 1. Descubrir candidatas
            candidatas_validas, resultado_discovery = self.discoverer.discover_for_parameter(
                parametro,
                inputs_disponibles=[],  # TODO: obtener del bus
                data_sample=None
            )

            ciclo.candidatas_descubiertas += resultado_discovery.candidatas_descubiertas
            ciclo.parametros_procesados += 1

            if not candidatas_validas:
                logger.info(f"   ⚠️  No hay candidatas válidas para {parametro}")
                ciclo.detalles.append({
                    "parametro": parametro,
                    "status": "sin_candidatas"
                })
                continue

            # 2. Para cada candidata válida, ejecutar duelo
            max_candidatas = self.config.get("max_candidatas_por_parametro", 5)
            candidatas_a_duelar = candidatas_validas[:max_candidatas]

            for cand in candidatas_a_duelar:
                # Generar datos de prueba si no se proporcionan
                if datos_prueba is None or parametro not in datos_prueba:
                    datos = self._generar_datos_dummy(parametro)
                else:
                    datos = datos_prueba[parametro]

                # Obtener fórmula interna (DUMMY por ahora)
                # TODO: obtener del bus actual
                fn_interna = self._obtener_formula_interna(parametro)
                fn_externa = self._obtener_formula_externa(cand.formula_ref)

                if not fn_interna or not fn_externa:
                    logger.warning(f"   ⚠️  No se pudo obtener fórmulas para duelo")
                    continue

                # Ejecutar duelo
                resultado_duelo = self.duel_engine.duelo(
                    parametro=parametro,
                    interna=fn_interna,
                    interna_id=f"interna_{parametro}",
                    externa=fn_externa,
                    externa_id=cand.id,
                    externa_nombre=cand.nombre,
                    datos_prueba=datos,
                    valores_esperados=None  # TODO: obtener datos reales
                )

                ciclo.duelos_ejecutados += 1

                # 3. Si externa gana, integrar
                if resultado_duelo.ganadora == "external":
                    score = resultado_duelo.score_ganadora
                    margen = resultado_duelo.margen_victoria

                    min_score = self.config.get("minimo_score_ganadora_externa", 75.0)
                    min_margen = self.config.get("minimo_margen_victoria", 5.0)

                    if score >= min_score and margen >= min_margen:
                        logger.info(f"   🏆 ¡GANADORA EXTERNA! Score: {score:.1f}, Margen: {margen:.1f}")

                        # Integrar
                        success = self.integrator.integrar_ganadora(
                            parametro=parametro,
                            externa_id=cand.id,
                            externa_nombre=cand.nombre,
                            externa_ref=cand.formula_ref,
                            inputs_requeridos=cand.inputs_requeridos,
                            score_duelo=score,
                            metadata={
                                "margen_victoria": margen,
                                "ciclo": self._ciclo_counter,
                                "fuente": cand.fuente
                            }
                        )

                        if success:
                            ciclo.ganadoras_externas += 1
                            ciclo.integraciones_exitosas += 1
                            ciclo.detalles.append({
                                "parametro": parametro,
                                "candidata": cand.nombre,
                                "status": "integrada",
                                "score": score
                            })
                        else:
                            ciclo.detalles.append({
                                "parametro": parametro,
                                "candidata": cand.nombre,
                                "status": "ganadora_pero_fallo_integracion",
                                "score": score
                            })
                    else:
                        ciclo.ganadoras_externas += 1
                        ciclo.detalles.append({
                            "parametro": parametro,
                            "candidata": cand.nombre,
                            "status": "ganadora_rechazada_por_umbral",
                            "score": score,
                            "razon": f"Score {score:.1f} < {min_score} o Margen {margen:.1f} < {min_margen}"
                        })
                else:
                    ciclo.detalles.append({
                        "parametro": parametro,
                        "candidata": cand.nombre,
                        "status": "perdio_duelo",
                        "score": resultado_duelo.score_perdedora
                    })

        # === Finalizar ciclo ===
        ciclo.duracion_segundos = time.time() - inicio

        self._cycles.append(asdict(ciclo))
        self._save_cycles()

        # === Resumen ===
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ CICLO #{self._ciclo_counter} COMPLETADO")
        logger.info(f"   Parámetros procesados: {ciclo.parametros_procesados}")
        logger.info(f"   Candidatas descubiertas: {ciclo.candidatas_descubiertas}")
        logger.info(f"   Duelos ejecutados: {ciclo.duelos_ejecutados}")
        logger.info(f"   Ganadoras externas: {ciclo.ganadoras_externas}")
        logger.info(f"   Integraciones exitosas: {ciclo.integraciones_exitosas}")
        logger.info(f"   Duración: {ciclo.duracion_segundos:.1f}s")
        logger.info(f"{'='*60}\n")

        return ciclo

    def _generar_datos_dummy(self, parametro: str) -> List[Dict[str, float]]:
        """Genera datos dummy para pruebas (TEMPORAL)."""
        # TODO: Obtener datos reales del sistema/logs
        dummy_data = {
            "sensacion_termica": [
                {"temperatura": 25, "velocidad_viento": 10, "humedad_relativa": 60},
                {"temperatura": 30, "velocidad_viento": 5, "humedad_relativa": 80},
                {"temperatura": 15, "velocidad_viento": 20, "humedad_relativa": 40},
            ],
            "humedad_relativa": [
                {"temperatura": 25, "punto_rocio": 15},
                {"temperatura": 30, "punto_rocio": 20},
            ],
            "punto_rocio": [
                {"temperatura": 25, "humedad_relativa": 60},
                {"temperatura": 30, "humedad_relativa": 75},
            ]
        }
        return dummy_data.get(parametro, [
            {"valor1": 1.0, "valor2": 2.0},
            {"valor1": 1.5, "valor2": 2.5},
        ])

    def _obtener_formula_interna(self, parametro: str) -> Optional[Callable]:
        """Obtiene fórmula interna actual (DUMMY)."""
        # TODO: Obtener del bus actual
        def dummy_internal(**kwargs):
            return sum(kwargs.values()) / len(kwargs) if kwargs else 0

        return dummy_internal

    def _obtener_formula_externa(self, ref: str) -> Optional[Callable]:
        """Obtiene fórmula externa por referencia."""
        try:
            partes = ref.rsplit(".", 1)
            if len(partes) != 2:
                return None
            modulo_name, func_name = partes
            modulo = __import__(modulo_name, fromlist=[func_name])
            func = getattr(modulo, func_name, None)
            return func if callable(func) else None
        except Exception as e:
            logger.debug(f"Error importando {ref}: {e}")
            return None

    def listar_ciclos(self) -> List[Dict[str, Any]]:
        """Lista ciclos ejecutados."""
        return self._cycles

    def obtener_ultimo_ciclo(self) -> Optional[Dict[str, Any]]:
        """Obtiene último ciclo ejecutado."""
        return self._cycles[-1] if self._cycles else None

    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de optimización."""
        if not self._cycles:
            return {
                "ciclos_totales": 0,
                "candidatas_descubiertas": 0,
                "duelos_ejecutados": 0,
                "ganadoras_integradas": 0
            }

        return {
            "ciclos_totales": len(self._cycles),
            "candidatas_descubiertas": sum(c.get("candidatas_descubiertas", 0) for c in self._cycles),
            "duelos_ejecutados": sum(c.get("duelos_ejecutados", 0) for c in self._cycles),
            "ganadoras_integradas": sum(c.get("integraciones_exitosas", 0) for c in self._cycles),
            "ultimo_ciclo": self._cycles[-1] if self._cycles else None
        }
