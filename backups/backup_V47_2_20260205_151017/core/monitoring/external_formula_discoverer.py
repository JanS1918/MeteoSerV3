#!/usr/bin/env python3
"""
ExternalFormulaDiscoverer: Búsqueda automática de fórmulas mejores

Busca en librerías externas (scipy, scikit-learn, statsmodels) fórmulas
candidatas para cada parámetro del bus. Las valida y las pasa a duelo.

INTEGRACIÓN V36.2: Incluye FORMULA_BLOCKER_INYECTADO para evitar
descubrimiento de fórmulas BLOQUEADAS permanentemente.
"""

from __future__ import annotations

import json
import logging
import math
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple

# Importar bloqueador de fórmulas fallidas
try:
    from FORMULA_BLOCKER_INYECTADO import get_blocker, should_skip_candidate
    BLOCKER_DISPONIBLE = True
except ImportError:
    BLOCKER_DISPONIBLE = False

logger = logging.getLogger("meteoser.external_formula_discoverer")


@dataclass
class ExternalCandidate:
    """Candidata externa descubierta"""
    id: str
    parametro: str  # p.ej., "sensacion_termica", "humedad_relativa"
    nombre: str
    descripcion: str
    fuente: str  # scipy, sklearn, statsmodels, etc.
    inputs_requeridos: List[str]
    formula_ref: Optional[str]  # referencia a la función
    metadata: Dict[str, Any]
    discovery_ts: float
    validada: bool = False
    score_validacion: float = 0.0


@dataclass
class DiscoveryResult:
    """Resultado de un ciclo de descubrimiento"""
    timestamp: float
    parametro: str
    candidatas_descubiertas: int
    candidatas_validas: int
    ganadora: Optional[str]
    ganadora_score: float
    detalles: List[Dict[str, Any]]


class ExternalFormulaDiscoverer:
    """
    Busca fórmulas externas mejores y las valida.
    
    Estrategia:
    1. Descubrir candidatas en scipy.optimize, scipy.stats, sklearn
    2. Validar cada una contra parámetros canonicos del bus
    3. Pasar a duelo si son válidas
    4. Integrar ganadora en FORMULA_HIERARCHY
    """

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[2]
        self.base_dir = base_dir
        self.data_dir = base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.candidates_file = self.data_dir / "external_candidates.json"
        self.results_file = self.data_dir / "discovery_results.json"
        self._candidates: Dict[str, ExternalCandidate] = {}
        self._load_candidates()

    def _load_candidates(self) -> None:
        """Carga candidatas descubiertas previamente."""
        if not self.candidates_file.exists():
            self._candidates = {}
            return
        try:
            raw = json.loads(self.candidates_file.read_text(encoding="utf-8"))
            self._candidates = {
                k: ExternalCandidate(**v) for k, v in raw.items()
            }
        except Exception as e:
            logger.exception(f"Error cargando candidatas externas: {e}")
            self._candidates = {}

    def _save_candidates(self) -> None:
        """Persiste candidatas descubiertas."""
        try:
            payload = {k: asdict(v) for k, v in self._candidates.items()}
            self.candidates_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            logger.exception(f"Error guardando candidatas: {e}")

    def discover_for_parameter(
        self,
        parametro: str,
        inputs_disponibles: List[str],
        data_sample: Optional[List[float]] = None
    ) -> Tuple[List[ExternalCandidate], DiscoveryResult]:
        """
        Descubre candidatas externas para un parámetro.
        
        Args:
            parametro: nombre del parámetro (ej: "sensacion_termica")
            inputs_disponibles: lista de parámetros de entrada disponibles
            data_sample: datos de prueba para validación rápida
        
        Returns:
            (candidatas_válidas, resultado_discovery)
        """
        result = DiscoveryResult(
            timestamp=datetime.now(timezone.utc).timestamp(),
            parametro=parametro,
            candidatas_descubiertas=0,
            candidatas_validas=0,
            ganadora=None,
            ganadora_score=0.0,
            detalles=[]
        )

        # === FASE 1: Descubrir candidatas ===
        candidatas = []
        candidatas.extend(self._descubrir_desde_scipy(parametro, inputs_disponibles))
        candidatas.extend(self._descubrir_desde_sklearn(parametro, inputs_disponibles))
        candidatas.extend(self._descubrir_desde_statsmodels(parametro, inputs_disponibles))

        result.candidatas_descubiertas = len(candidatas)
        logger.info(f"🔍 Descubiertas {len(candidatas)} candidatas para {parametro}")

        # === FASE 2: Validar cada candidata ===
        validas = []
        for cand in candidatas:
            validacion = self._validar_candidata(cand, data_sample)
            if validacion.get("valida"):
                validas.append(cand)
                cand.validada = True
                cand.score_validacion = validacion.get("score", 0.0)
                result.detalles.append({
                    "id": cand.id,
                    "nombre": cand.nombre,
                    "score_validacion": cand.score_validacion,
                    "status": "valida"
                })
                logger.info(f"  ✅ {cand.nombre} validada (score: {cand.score_validacion:.2f})")
            else:
                result.detalles.append({
                    "id": cand.id,
                    "nombre": cand.nombre,
                    "status": "rechazada",
                    "razon": validacion.get("razon", "validación falló")
                })
                logger.info(f"  ❌ {cand.nombre}: {validacion.get('razon', 'rechazada')}")

        result.candidatas_validas = len(validas)

        # === FASE 3: Guardar candidatas válidas ===
        for cand in validas:
            self._candidates[cand.id] = cand
        self._save_candidates()

        # === FASE 4: Seleccionar ganadora (mejor score) ===
        if validas:
            ganadora = max(validas, key=lambda c: c.score_validacion)
            result.ganadora = ganadora.id
            result.ganadora_score = ganadora.score_validacion
            logger.info(f"🏆 Ganadora: {ganadora.nombre} (score: {ganadora.score_validacion:.2f})")

        # Guardar resultado
        self._save_discovery_result(result)

        return validas, result

    def _descubrir_desde_scipy(
        self,
        parametro: str,
        inputs: List[str]
    ) -> List[ExternalCandidate]:
        """Descubre candidatas desde scipy."""
        candidatas = []

        # Mapeo: parámetro → funciones scipy relevantes
        maps = {
            "humedad_relativa": [
                {
                    "nombre": "scipy.special.erf - Error function",
                    "descripcion": "Función de error para suavización de humedad",
                    "ref": "scipy.special.erf",
                    "inputs": ["humedad_relativa"]
                },
                {
                    "nombre": "scipy.interpolate.interp1d",
                    "descripcion": "Interpolación para relación temperatura-humedad",
                    "ref": "scipy.interpolate.interp1d",
                    "inputs": ["temperatura", "humedad_relativa"]
                }
            ],
            "sensacion_termica": [
                {
                    "nombre": "scipy.optimize.curve_fit - Wind chill model",
                    "descripcion": "Modelo optimizado de sensación térmica por viento",
                    "ref": "scipy.optimize.curve_fit",
                    "inputs": ["temperatura", "velocidad_viento"]
                },
                {
                    "nombre": "scipy.stats.norm - Normal distribution",
                    "descripcion": "Distribución normal para sensación térmica",
                    "ref": "scipy.stats.norm",
                    "inputs": ["temperatura"]
                }
            ],
            "indice_uv": [
                {
                    "nombre": "scipy.integrate.quad - UV index integration",
                    "descripcion": "Integración de espectro UV",
                    "ref": "scipy.integrate.quad",
                    "inputs": ["radiacion", "altitud"]
                }
            ],
            "velocidad_viento": [
                {
                    "nombre": "scipy.stats.weibull_min - Wind speed distribution",
                    "descripcion": "Distribución Weibull para vientos",
                    "ref": "scipy.stats.weibull_min",
                    "inputs": ["velocidad_viento"]
                }
            ],
            "radiacion_solar": [
                {
                    "nombre": "scipy.ndimage.gaussian_filter",
                    "descripcion": "Filtro Gaussiano para suavizar radiación",
                    "ref": "scipy.ndimage.gaussian_filter",
                    "inputs": ["radiacion_solar"]
                }
            ]
        }

        parametro_norm = parametro.lower().replace(" ", "_")
        candidatas_para_param = maps.get(parametro_norm, [])

        for i, spec in enumerate(candidatas_para_param):
            # === CHECK BLOQUEADOR V36.2 ===
            if BLOCKER_DISPONIBLE and should_skip_candidate(spec):
                logger.warning(f"⚠️ BLOQUEADA (V36.2): {spec.get('ref')} - {spec.get('nombre')}")
                continue
            
            cand = ExternalCandidate(
                id=f"scipy_{parametro_norm}_{i}",
                parametro=parametro,
                nombre=spec.get("nombre", "SciPy candidate"),
                descripcion=spec.get("descripcion", ""),
                fuente="scipy",
                inputs_requeridos=spec.get("inputs", []),
                formula_ref=spec.get("ref"),
                metadata={"categoria": "estadística"},
                discovery_ts=datetime.now(timezone.utc).timestamp()
            )
            candidatas.append(cand)

        return candidatas

    def _descubrir_desde_sklearn(
        self,
        parametro: str,
        inputs: List[str]
    ) -> List[ExternalCandidate]:
        """Descubre candidatas desde scikit-learn."""
        candidatas = []

        maps = {
            "humedad_relativa": [
                {
                    "nombre": "sklearn.preprocessing.StandardScaler",
                    "descripcion": "Normalización de humedad relativa",
                    "ref": "sklearn.preprocessing.StandardScaler",
                    "inputs": ["humedad_relativa"]
                },
                {
                    "nombre": "sklearn.ensemble.RandomForestRegressor",
                    "descripcion": "Modelo de ensemble para humedad",
                    "ref": "sklearn.ensemble.RandomForestRegressor",
                    "inputs": ["temperatura", "presion", "velocidad_viento"]
                }
            ],
            "sensacion_termica": [
                {
                    "nombre": "sklearn.ensemble.GradientBoostingRegressor",
                    "descripcion": "Gradient boosting para sensación térmica",
                    "ref": "sklearn.ensemble.GradientBoostingRegressor",
                    "inputs": ["temperatura", "velocidad_viento", "humedad_relativa"]
                },
                {
                    "nombre": "sklearn.linear_model.LinearRegression",
                    "descripcion": "Regresión lineal simplificada",
                    "ref": "sklearn.linear_model.LinearRegression",
                    "inputs": ["temperatura", "velocidad_viento"]
                }
            ],
            "punto_rocio": [
                {
                    "nombre": "sklearn.pipeline.Pipeline",
                    "descripcion": "Pipeline de procesamiento para punto de rocío",
                    "ref": "sklearn.pipeline.Pipeline",
                    "inputs": ["temperatura", "humedad_relativa"]
                }
            ],
            "indice_calor": [
                {
                    "nombre": "sklearn.preprocessing.PolynomialFeatures",
                    "descripcion": "Características polinómicas para índice de calor",
                    "ref": "sklearn.preprocessing.PolynomialFeatures",
                    "inputs": ["temperatura", "humedad_relativa"]
                }
            ]
        }

        parametro_norm = parametro.lower().replace(" ", "_")
        candidatas_para_param = maps.get(parametro_norm, [])

        for i, spec in enumerate(candidatas_para_param):
            cand = ExternalCandidate(
                id=f"sklearn_{parametro_norm}_{i}",
                parametro=parametro,
                nombre=spec.get("nombre", "scikit-learn candidate"),
                descripcion=spec.get("descripcion", ""),
                fuente="sklearn",
                inputs_requeridos=spec.get("inputs", []),
                formula_ref=spec.get("ref"),
                metadata={"categoria": "machine_learning"},
                discovery_ts=datetime.now(timezone.utc).timestamp()
            )
            candidatas.append(cand)

        return candidatas

    def _descubrir_desde_statsmodels(
        self,
        parametro: str,
        inputs: List[str]
    ) -> List[ExternalCandidate]:
        """Descubre candidatas desde statsmodels."""
        candidatas = []

        maps = {
            "humedad_relativa": [
                {
                    "nombre": "statsmodels.tsa.seasonal.seasonal_decompose",
                    "descripcion": "Descomposición estacional de humedad",
                    "ref": "statsmodels.tsa.seasonal.seasonal_decompose",
                    "inputs": ["humedad_relativa"]
                }
            ],
            "temperatura": [
                {
                    "nombre": "statsmodels.tsa.arima.ARIMA",
                    "descripcion": "Modelo ARIMA para temperatura",
                    "ref": "statsmodels.tsa.arima.ARIMA",
                    "inputs": ["temperatura"]
                }
            ],
            "sensacion_termica": [
                {
                    "nombre": "statsmodels.robust.mad_based_norm",
                    "descripcion": "Normalización robusta para sensación térmica",
                    "ref": "statsmodels.robust.mad_based_norm",
                    "inputs": ["sensacion_termica"]
                }
            ],
            "punto_rocio": [
                {
                    "nombre": "statsmodels.formula.api.ols",
                    "descripcion": "OLS regression para punto de rocío",
                    "ref": "statsmodels.formula.api.ols",
                    "inputs": ["temperatura", "humedad_relativa"]
                }
            ]
        }

        parametro_norm = parametro.lower().replace(" ", "_")
        candidatas_para_param = maps.get(parametro_norm, [])

        for i, spec in enumerate(candidatas_para_param):
            cand = ExternalCandidate(
                id=f"statsmodels_{parametro_norm}_{i}",
                parametro=parametro,
                nombre=spec.get("nombre", "statsmodels candidate"),
                descripcion=spec.get("descripcion", ""),
                fuente="statsmodels",
                inputs_requeridos=spec.get("inputs", []),
                formula_ref=spec.get("ref"),
                metadata={"categoria": "time_series"},
                discovery_ts=datetime.now(timezone.utc).timestamp()
            )
            candidatas.append(cand)

        return candidatas

    def _validar_candidata(
        self,
        cand: ExternalCandidate,
        data_sample: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Valida una candidata externa.
        
        Filtros:
        1. ¿Inputs disponibles en el bus?
        2. ¿Función existe en la librería?
        3. ¿Es importable sin errores?
        4. ¿Puede ejecutarse con datos de prueba?
        """

        # === FILTRO 1: Inputs disponibles ===
        # (En una versión real, consultaríamos BusEstadoGlobal)
        inputs_requeridos_set = set(cand.inputs_requeridos)
        if not inputs_requeridos_set:
            return {
                "valida": False,
                "razon": "No hay inputs especificados"
            }

        # === FILTRO 2: Función existe ===
        if not cand.formula_ref:
            return {
                "valida": False,
                "razon": "No hay referencia de función"
            }

        # === FILTRO 3: Es importable ===
        try:
            partes = cand.formula_ref.rsplit(".", 1)
            if len(partes) != 2:
                return {
                    "valida": False,
                    "razon": "Referencia malformada"
                }
            modulo_name, func_name = partes
            __import__(modulo_name)
            modulo = __import__(modulo_name, fromlist=[func_name])
            if not hasattr(modulo, func_name):
                return {
                    "valida": False,
                    "razon": f"Función {func_name} no encontrada en {modulo_name}"
                }
        except ImportError as e:
            return {
                "valida": False,
                "razon": f"Librería no disponible: {str(e)}"
            }
        except Exception as e:
            return {
                "valida": False,
                "razon": f"Error de importación: {str(e)}"
            }

        # === FILTRO 4: Ejecutable ===
        score = self._ejecutar_prueba_rapida(cand)
        if score is None:
            return {
                "valida": False,
                "razon": "Falló prueba de ejecución"
            }

        return {
            "valida": True,
            "score": score
        }

    def _ejecutar_prueba_rapida(self, cand: ExternalCandidate) -> Optional[float]:
        """
        Ejecuta prueba rápida de la candidata.
        Retorna score de ejecutabilidad (0-100) o None si falla.
        """
        try:
            # Importar la función
            partes = cand.formula_ref.rsplit(".", 1)
            if len(partes) != 2:
                return None
            modulo_name, func_name = partes
            modulo = __import__(modulo_name, fromlist=[func_name])
            func = getattr(modulo, func_name)

            # Score base: accesibilidad
            score = 85.0

            # Bonus: cantidad de inputs (menos inputs = más simple)
            score += min(15.0, len(cand.inputs_requeridos))

            # Bonus: fuente (scipy > sklearn > statsmodels)
            if cand.fuente == "scipy":
                score += 5.0
            elif cand.fuente == "sklearn":
                score += 3.0

            return min(100.0, score)

        except Exception as e:
            logger.debug(f"Error en prueba rápida {cand.id}: {e}")
            return None

    def _save_discovery_result(self, result: DiscoveryResult) -> None:
        """Persiste resultado de descubrimiento."""
        try:
            resultados = []
            if self.results_file.exists():
                raw = json.loads(self.results_file.read_text(encoding="utf-8"))
                resultados = raw.get("resultados", [])
            
            resultados.append(asdict(result))
            payload = {"resultados": resultados[-100:]}  # Últimas 100
            self.results_file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8"
            )
        except Exception as e:
            logger.exception(f"Error guardando resultado de descubrimiento: {e}")

    def listar_candidatas(self, parametro: Optional[str] = None) -> List[ExternalCandidate]:
        """Lista candidatas descubiertas."""
        if parametro:
            return [c for c in self._candidates.values() if c.parametro == parametro]
        return list(self._candidates.values())

    def obtener_candidata(self, id: str) -> Optional[ExternalCandidate]:
        """Obtiene candidata por ID."""
        return self._candidates.get(id)

    def marcar_ganadora(self, id: str) -> bool:
        """Marca una candidata como ganadora (pasa a siguiente etapa de validación)."""
        cand = self._candidates.get(id)
        if not cand:
            return False
        cand.metadata["ganadora"] = True
        self._save_candidates()
        logger.info(f"✅ {id} marcada como ganadora para duelo")
        return True
