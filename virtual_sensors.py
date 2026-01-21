# ============================================================
# MÓDULO 2 — SENSORES VIRTUALES INTELIGENTES
# Archivo: core/sensors/virtual_sensors.py
# ============================================================

import math
import time
from typing import Dict, Any, List, Optional

# Intentamos importar el registro de sensores si existe.
try:
    from core.integration.integration_manager import SensorRegistry
except Exception:
    SensorRegistry = None  # Si no existe, el módulo sigue funcionando en modo local


# ------------------------------------------------------------
# CONSTANTES Y TIPOS
# ------------------------------------------------------------
RELIABILITY_STRONG = "fuerte"
RELIABILITY_MODERATE = "moderado"
RELIABILITY_WEAK = "débil"

VirtualSpec = Dict[str, Any]  # definición simple para especificación de sensor virtual


# ------------------------------------------------------------
# CLASE SensorVirtual
# ------------------------------------------------------------
class SensorVirtual:
    """
    Representa un sensor virtual.
    - id: identificador único interno
    - spec: especificación que describe cómo se calcula
    - last_value: último valor calculado
    - reliability: clasificación de fiabilidad
    - active: si se usa en índices principales
    """

    def __init__(self, vid: str, spec: VirtualSpec):
        self.id = vid
        self.spec = spec
        self.last_value: Optional[float] = None
        self.reliability: str = RELIABILITY_WEAK
        self.active: bool = False
        self.history: List[float] = []
        self.last_updated: Optional[float] = None

    def compute(self, inputs: Dict[str, float]) -> Optional[float]:
        """
        Ejecuta la función de cálculo definida en spec.
        spec debe contener: {"fn": callable, "inputs": ["sensorA","sensorB"], "params": {...}}
        """
        fn = self.spec.get("fn")
        if not callable(fn):
            return None

        try:
            required = self.spec.get("inputs", [])
            args = {k: inputs[k] for k in required if k in inputs}
            value = fn(args, **self.spec.get("params", {}))
            if value is None or (
                isinstance(value, float) and (math.isnan(value) or math.isinf(value))
            ):
                return None
            self.last_value = float(value)
            self.history.append(self.last_value)
            self.last_updated = time.time()
            # Mantener historia razonable
            if len(self.history) > 500:
                self.history = self.history[-500:]
            return self.last_value
        except Exception:
            return None


# ------------------------------------------------------------
# CLASE EvaluadorDeEstimaciones
# ------------------------------------------------------------
class EvaluadorDeEstimaciones:
    """
    Evalúa la calidad de un sensor virtual usando:
    - consistencia histórica
    - correlación con sensores base si se dispone
    - disponibilidad de inputs
    """

    def __init__(self):
        pass

    def score_consistency(self, history: List[float]) -> float:
        """
        Puntuación basada en varianza relativa y número de muestras.
        Devuelve 0..1 (1 = muy consistente).
        """
        if not history or len(history) < 5:
            return 0.0
        mean = sum(history) / len(history)
        var = sum((x - mean) ** 2 for x in history) / len(history)
        rel_var = var / (abs(mean) + 1e-6)
        # Mapear rel_var a 0..1 inversamente
        score = max(0.0, 1.0 - min(rel_var / 0.5, 1.0))
        # penalizar si pocas muestras
        score *= min(1.0, len(history) / 50.0)
        return score

    def score_availability(self, inputs_present: int, inputs_required: int) -> float:
        """
        Puntuación por disponibilidad de inputs.
        """
        if inputs_required == 0:
            return 1.0
        return max(0.0, inputs_present / inputs_required)

    def classify(
        self, history: List[float], inputs_present: int, inputs_required: int
    ) -> str:
        """
        Clasifica en fuerte/moderado/débil según puntuaciones combinadas.
        """
        c_score = self.score_consistency(history)
        a_score = self.score_availability(inputs_present, inputs_required)
        combined = 0.7 * c_score + 0.3 * a_score
        if combined >= 0.75:
            return RELIABILITY_STRONG
        if combined >= 0.4:
            return RELIABILITY_MODERATE
        return RELIABILITY_WEAK


# ------------------------------------------------------------
# CLASE VirtualSensorManager
# ------------------------------------------------------------
class VirtualSensorManager:
    """
    Gestor de sensores virtuales.
    - registrar especificaciones
    - calcular valores periódicamente
    - validar y clasificar fiabilidad
    - exponer API para integración con índices
    """

    def __init__(self, registry: Optional[SensorRegistry] = None):
        self.registry = registry
        self.virtuals: Dict[str, SensorVirtual] = {}
        self.evaluator = EvaluadorDeEstimaciones()

    # -------------------------
    # REGISTRO Y ESPECIFICACIONES
    # -------------------------
    def register_virtual(self, vid: str, spec: VirtualSpec):
        """
        Registra una especificación de sensor virtual.
        Si ya existe, la actualiza.
        """
        self.virtuals[vid] = SensorVirtual(vid, spec)

    def unregister_virtual(self, vid: str):
        if vid in self.virtuals:
            del self.virtuals[vid]

    def list_virtuals(self) -> List[str]:
        return list(self.virtuals.keys())

    # -------------------------
    # CÁLCULO Y VALIDACIÓN
    # -------------------------
    def compute_all(self, inputs: Dict[str, float]) -> Dict[str, Optional[float]]:
        """
        Calcula todos los sensores virtuales con los inputs disponibles.
        Devuelve un dict vid -> value (o None si no pudo calcularse).
        """
        results = {}
        for vid, vs in self.virtuals.items():
            # contar inputs presentes
            required = vs.spec.get("inputs", [])
            present = sum(1 for r in required if r in inputs)
            value = vs.compute(inputs)
            # evaluar y clasificar
            vs.reliability = self.evaluator.classify(vs.history, present, len(required))
            # activar si es fuerte o moderado y tiene valor
            vs.active = (
                vs.reliability in (RELIABILITY_STRONG, RELIABILITY_MODERATE)
            ) and (value is not None)
            results[vid] = value
        return results

    def get_virtual_info(self, vid: str) -> Optional[Dict[str, Any]]:
        if vid not in self.virtuals:
            return None
        v = self.virtuals[vid]
        return {
            "id": v.id,
            "last_value": v.last_value,
            "reliability": v.reliability,
            "active": v.active,
            "last_updated": v.last_updated,
            "spec": v.spec,
        }

    # -------------------------
    # INTEGRACIÓN CON REGISTRO DE SENSORES
    # -------------------------
    def publish_capabilities(self):
        """
        Si existe un SensorRegistry, publica capacidades derivadas de sensores virtuales.
        Ejemplo: si hay un sensor virtual que mide 'confort', se añade 'confort' a capacidades.
        """
        if not self.registry:
            return
        for vid, vs in self.virtuals.items():
            caps = vs.spec.get("capabilities", [])
            for c in caps:
                # registrar capacidad en el registro central
                try:
                    self.registry.capabilities.add(c)
                except Exception:
                    pass

    # -------------------------
    # UTILIDADES PARA ESPECIFICAR SENSORES VIRTUALES COMUNES
    # -------------------------
    @staticmethod
    def fn_ratio(
        inputs: Dict[str, float],
        numerator: str = None,
        denominator: str = None,
        scale: float = 1.0,
    ):
        """
        Ejemplo de función: ratio entre dos sensores.
        numerator y denominator son claves dentro de inputs.
        """
        if numerator not in inputs or denominator not in inputs:
            return None
        den = inputs[denominator]
        if den == 0:
            return None
        return (inputs[numerator] / den) * scale

    @staticmethod
    def fn_weighted_avg(inputs: Dict[str, float], weights: Dict[str, float]):
        """
        Media ponderada de varios inputs.
        weights: dict sensor->peso
        """
        total_w = 0.0
        s = 0.0
        for k, w in weights.items():
            if k in inputs:
                s += inputs[k] * w
                total_w += w
        if total_w == 0:
            return None
        return s / total_w


# ------------------------------------------------------------
# EJEMPLO DE ESPECIFICACIONES PREDEFINIDAS (PUEDES BORRARLAS)
# ------------------------------------------------------------
def default_specs():
    """
    Especificaciones de ejemplo para sensores virtuales útiles.
    No se ejecutan automáticamente; sirven como plantilla.
    """
    specs = {
        "confort_termico": {
            "inputs": ["temp_int", "hum_int", "wbgt_real"],
            "fn": lambda inputs, **params: VirtualSensorManager.fn_weighted_avg(
                inputs, weights={"temp_int": 0.6, "hum_int": 0.2, "wbgt_real": 0.2}
            ),
            "params": {},
            "capabilities": ["confort"],
        },
        "co2_normalizado": {
            "inputs": ["co2_int", "temp_int"],
            "fn": lambda inputs, **params: VirtualSensorManager.fn_ratio(
                inputs, numerator="co2_int", denominator="temp_int", scale=1.0
            ),
            "params": {},
            "capabilities": ["co2_index"],
        },
    }
    return specs


# ============================================================
# FIN DEL MÓDULO
# ============================================================
