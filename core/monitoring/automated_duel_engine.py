#!/usr/bin/env python3
"""
AutomatedDuelEngine: Duelos auténticos entre fórmulas

Compara candidata externa vs. interna actual con datos reales.
Ganador es quien sea superior en precisión, velocidad y robustez.
"""

from __future__ import annotations

import json
import logging
import time
import statistics
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple

logger = logging.getLogger("meteoser.automated_duel_engine")


@dataclass
class DuelMetrics:
    """Métricas de un competidor en un duelo"""
    nombre: str
    fuente: str  # "internal" o "external"
    tiempo_ejecucion: float  # segundos
    precision_mae: float  # Mean Absolute Error
    precision_rmse: float  # Root Mean Squared Error
    precision_r2: float  # Coeficiente de determinación
    robustez_score: float  # % de ejecuciones sin error
    estabilidad_score: float  # Consistencia de outputs
    score_total: float  # Puntuación final (0-100)


@dataclass
class DuelResult:
    """Resultado de un duelo"""
    timestamp: float
    parametro: str
    interna_id: str
    externa_id: Optional[str]
    externa_nombre: Optional[str]
    duracion_segundos: float
    ganadora: str  # "internal" o "external"
    score_ganadora: float
    score_perdedora: float
    margen_victoria: float  # diferencia de scores
    detalles: Dict[str, Any]


class AutomatedDuelEngine:
    """
    Motor de duelos auténticos:
    - Ejecuta ambas fórmulas con datos de prueba reales
    - Compara precisión, velocidad, robustez
    - Declara ganadora
    - Registra resultado para integración posterior
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.data_dir / "duel_results.json"
        self._results: List[DuelResult] = []
        self._load_results()

    def _load_results(self) -> None:
        """Carga histórico de duelos."""
        if not self.results_file.exists():
            self._results = []
            return
        try:
            raw = json.loads(self.results_file.read_text(encoding="utf-8"))
            self._results = raw.get("duelos", [])
        except Exception as e:
            logger.exception(f"Error cargando resultados de duelos: {e}")
            self._results = []

    def _save_results(self) -> None:
        """Persiste resultados de duelos."""
        try:
            payload = {"duelos": self._results[-500:]}  # Últimos 500
            self.results_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            logger.exception(f"Error guardando resultados de duelos: {e}")

    def duelo(
        self,
        parametro: str,
        interna: Callable,
        interna_id: str,
        externa: Callable,
        externa_id: str,
        externa_nombre: str,
        datos_prueba: List[Dict[str, float]],
        valores_esperados: Optional[List[float]] = None
    ) -> DuelResult:
        """
        Ejecuta duelo entre fórmula interna y externa.

        Args:
            parametro: nombre del parámetro
            interna: función interna (fórmula actual)
            interna_id: ID/nombre de fórmula interna
            externa: función externa (candidata)
            externa_id: ID de candidata externa
            externa_nombre: nombre de candidata externa
            datos_prueba: lista de dicts con inputs para ejecutar
            valores_esperados: valores ground-truth para medir error

        Returns:
            DuelResult con ganadora
        """
        inicio = time.time()

        logger.info(f"⚔️  DUELO: {parametro}")
        logger.info(f"   Interna: {interna_id}")
        logger.info(f"   Externa: {externa_nombre} ({externa_id})")

        # [TARGET] VALIDACIONES DE SEGURIDAD (antes de ejecutar/medir)
        try:
            from core.security import (
                MeteorologicalDomainValidator,
                SpecificationCompletenessValidator,
                PrecisionValidator
            )
            
            domain_validator = MeteorologicalDomainValidator()
            spec_validator = SpecificationCompletenessValidator()
            precision_validator = PrecisionValidator()
            
            # [TARGET] VALIDACIÓN 1: ¿Es índice meteorológico válido?
            source_lib = getattr(externa, 'source_library', 'unknown')
            source_func = getattr(externa, 'source_function', 'unknown')
            is_valid_domain, msg_domain = domain_validator.validate(
                parametro,
                source_lib,
                source_func
            )
            if not is_valid_domain:
                logger.warning(f"🚫 Externa RECHAZADA (dominio): {msg_domain}")
                return DuelResult(
                    timestamp=datetime.now(timezone.utc).timestamp(),
                    parametro=parametro,
                    interna_id=interna_id,
                    externa_id=externa_id,
                    externa_nombre=externa_nombre,
                    duracion_segundos=time.time() - inicio,
                    ganadora="internal",
                    score_ganadora=100.0,
                    score_perdedora=0.0,
                    margen_victoria=100.0,
                    detalles={"razon": "external_domain_invalid", "mensaje": msg_domain}
                )
            
            # [TARGET] VALIDACIÓN 2: ¿Especificación completa?
            spec_dict = getattr(externa, 'specification', {})
            is_valid_spec, errors_spec = spec_validator.validate(
                parametro,
                spec_dict,
                externa
            )
            if not is_valid_spec:
                logger.warning(f"🚫 Externa RECHAZADA (especificación incompleta): {errors_spec}")
                return DuelResult(
                    timestamp=datetime.now(timezone.utc).timestamp(),
                    parametro=parametro,
                    interna_id=interna_id,
                    externa_id=externa_id,
                    externa_nombre=externa_nombre,
                    duracion_segundos=time.time() - inicio,
                    ganadora="internal",
                    score_ganadora=100.0,
                    score_perdedora=0.0,
                    margen_victoria=100.0,
                    detalles={"razon": "external_spec_incomplete", "errores": errors_spec}
                )
            
            # [TARGET] VALIDACIÓN 3: ¿Precisión cumplida?
            required_precision = precision_validator.get_precision_for_parameter(parametro)
            if required_precision is not None:
                logger.info(f"[OK] {parametro} requiere precisión ±{required_precision}")
        
        except Exception as e:
            logger.warning(f"[WARNING] Validadores de seguridad no disponibles: {e}")
            # Continuar sin validadores (fallback)

        # === FASE 1: Ejecutar interna ===
        metricas_interna = self._ejecutar_y_medir(
            interna,
            datos_prueba,
            valores_esperados,
            nombre="interna",
            id_formula=interna_id
        )

        # === FASE 2: Ejecutar externa ===
        metricas_externa = self._ejecutar_y_medir(
            externa,
            datos_prueba,
            valores_esperados,
            nombre="externa",
            id_formula=externa_id
        )

        # === FASE 3: Comparar ===
        ganadora, score_ganadora, score_perdedora = self._comparar_metricas(
            metricas_interna,
            metricas_externa
        )

        resultado = DuelResult(
            timestamp=datetime.now(timezone.utc).timestamp(),
            parametro=parametro,
            interna_id=interna_id,
            externa_id=externa_id,
            externa_nombre=externa_nombre,
            duracion_segundos=time.time() - inicio,
            ganadora=ganadora,
            score_ganadora=score_ganadora,
            score_perdedora=score_perdedora,
            margen_victoria=abs(score_ganadora - score_perdedora),
            detalles={
                "interna": asdict(metricas_interna),
                "externa": asdict(metricas_externa)
            }
        )

        # === FASE 4: Registrar ===
        self._results.append(asdict(resultado))
        self._save_results()

        # === LOGGING ===
        simbolo = "[OK]" if ganadora == "internal" else "🆕"
        logger.info(f"{simbolo} GANADORA: {ganadora.upper()}")
        logger.info(f"   Score ganadora: {score_ganadora:.2f}/100")
        logger.info(f"   Score perdedora: {score_perdedora:.2f}/100")
        logger.info(f"   Margen: {abs(score_ganadora - score_perdedora):.2f}")

        return resultado

    def _ejecutar_y_medir(
        self,
        formula: Callable,
        datos_prueba: List[Dict[str, float]],
        valores_esperados: Optional[List[float]],
        nombre: str,
        id_formula: str
    ) -> DuelMetrics:
        """
        Ejecuta fórmula sobre datos de prueba y mide performance.
        """
        outputs = []
        errores = 0
        tiempo_total = 0.0

        for data in datos_prueba:
            try:
                inicio = time.perf_counter()
                resultado = formula(**data)
                tiempo_total += time.perf_counter() - inicio

                if isinstance(resultado, dict):
                    # Fórmula retorna dict con múltiples keys
                    valor = resultado.get("valor") or list(resultado.values())[0]
                else:
                    valor = resultado

                if isinstance(valor, (int, float)):
                    outputs.append(float(valor))
                else:
                    errores += 1
            except Exception as e:
                errores += 1
                logger.debug(f"Error ejecutando {nombre}: {e}")

        # === Calcular métricas ===
        n_ejecuciones = len(datos_prueba)
        robustez = (n_ejecuciones - errores) / n_ejecuciones if n_ejecuciones > 0 else 0.0

        # Precisión
        mae = self._calcular_mae(outputs, valores_esperados)
        rmse = self._calcular_rmse(outputs, valores_esperados)
        r2 = self._calcular_r2(outputs, valores_esperados)

        # Estabilidad (inverso del coeficiente de variación)
        estabilidad = self._calcular_estabilidad(outputs)

        # Score total (ponderado)
        tiempo_medio = tiempo_total / n_ejecuciones if n_ejecuciones > 0 else 0.0
        velocidad_score = max(0, 100 - (tiempo_medio * 1000))  # ms → score

        score_total = (
            r2 * 40.0 +  # 40% precisión (R²)
            (1 - mae) * 25.0 +  # 25% MAE
            robustez * 20.0 +  # 20% robustez
            estabilidad * 15.0  # 15% estabilidad
        )
        score_total = max(0, min(100, score_total))

        metricas = DuelMetrics(
            nombre=nombre,
            fuente="internal" if "interna" in nombre else "external",
            tiempo_ejecucion=tiempo_medio,
            precision_mae=mae,
            precision_rmse=rmse,
            precision_r2=r2,
            robustez_score=robustez,
            estabilidad_score=estabilidad,
            score_total=score_total
        )

        logger.debug(f"  {nombre}: MAE={mae:.4f}, R²={r2:.4f}, Robustez={robustez:.1%}, Score={score_total:.1f}")

        return metricas

    def _comparar_metricas(
        self,
        interna: DuelMetrics,
        externa: DuelMetrics
    ) -> Tuple[str, float, float]:
        """
        Compara métricas y declara ganadora.
        
        Ganador es quien tenga score_total más alto.
        Si scores muy cercanos (diff < 5), conservamos interna (cautela).
        """
        diff = externa.score_total - interna.score_total

        if diff > 5.0:
            # Externa gana por margen claro
            return "external", externa.score_total, interna.score_total

        elif diff < -5.0:
            # Interna gana por margen claro
            return "internal", interna.score_total, externa.score_total

        else:
            # Scores muy cercanos: mantener interna (principio de cautela)
            ganadora = "internal" if interna.score_total >= externa.score_total else "external"
            score_ganadora = max(interna.score_total, externa.score_total)
            score_perdedora = min(interna.score_total, externa.score_total)
            return ganadora, score_ganadora, score_perdedora

    def _calcular_mae(
        self,
        predichos: List[float],
        reales: Optional[List[float]]
    ) -> float:
        """Calcula Mean Absolute Error."""
        if not reales or not predichos or len(predichos) != len(reales):
            return 1.0  # Worst case

        mae = sum(abs(p - r) for p, r in zip(predichos, reales)) / len(predichos)
        # Normalizar a [0, 1]
        return min(1.0, mae / (max(abs(r) for r in reales) or 1.0))

    def _calcular_rmse(
        self,
        predichos: List[float],
        reales: Optional[List[float]]
    ) -> float:
        """Calcula Root Mean Squared Error."""
        if not reales or not predichos or len(predichos) != len(reales):
            return 1.0

        mse = sum((p - r) ** 2 for p, r in zip(predichos, reales)) / len(predichos)
        rmse = mse ** 0.5
        return min(1.0, rmse / (max(abs(r) for r in reales) or 1.0))

    def _calcular_r2(
        self,
        predichos: List[float],
        reales: Optional[List[float]]
    ) -> float:
        """Calcula Coeficiente de Determinación (R²)."""
        if not reales or not predichos or len(predichos) != len(reales):
            return 0.0

        media_reales = statistics.mean(reales)
        ss_tot = sum((r - media_reales) ** 2 for r in reales)
        ss_res = sum((p - r) ** 2 for p, r in zip(predichos, reales))

        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0

        r2 = 1 - (ss_res / ss_tot)
        return max(0.0, min(1.0, r2))

    def _calcular_estabilidad(self, outputs: List[float]) -> float:
        """
        Estabilidad = inverso del coeficiente de variación.
        Outputs consistentes → score alto.
        """
        if len(outputs) < 2:
            return 1.0

        media = statistics.mean(outputs)
        if media == 0:
            return 0.0

        desv = statistics.stdev(outputs)
        cv = desv / abs(media)

        # cv pequeño → estable → score alto
        estabilidad = 1.0 / (1.0 + cv)
        return max(0.0, min(1.0, estabilidad))

    def listar_duelos(self, parametro: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista resultados de duelos."""
        if parametro:
            return [d for d in self._results if d.get("parametro") == parametro]
        return self._results

    def obtener_ultimo_duelo(self, parametro: str) -> Optional[Dict[str, Any]]:
        """Obtiene último duelo de un parámetro."""
        duelos = [d for d in self._results if d.get("parametro") == parametro]
        return duelos[-1] if duelos else None

    def obtener_ganadora_actual(self, parametro: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de la ganadora actual para un parámetro.
        (Basado en últimos duelos)
        """
        duelos = [d for d in self._results if d.get("parametro") == parametro]
        if not duelos:
            return None

        ultimo = duelos[-1]
        return {
            "ganadora": ultimo.get("ganadora"),
            "id": ultimo.get("externa_id") if ultimo.get("ganadora") == "external" else ultimo.get("interna_id"),
            "nombre": ultimo.get("externa_nombre") if ultimo.get("ganadora") == "external" else None,
            "score": ultimo.get("score_ganadora"),
            "margen_victoria": ultimo.get("margen_victoria"),
            "timestamp": ultimo.get("timestamp")
        }
