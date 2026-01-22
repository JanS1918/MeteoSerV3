# ============================================================
# MÓDULO 2 — SENSORES VIRTUALES INTELIGENTES
# Archivo: core/sensors/virtual_sensors.py
# ============================================================

import math
import time
from typing import Dict, Any, List, Optional
from core.sensors.pm_calibration import apply_pm_calibration
from core.sensors.sensor_aliases import canonical_sensor_name

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
            normalized_inputs: Dict[str, float] = {}
            for key, value in inputs.items():
                canonical_key = canonical_sensor_name(key)
                normalized_inputs[canonical_key or key] = value
            # contar inputs presentes
            required = vs.spec.get("inputs", [])
            present = sum(1 for r in required if r in normalized_inputs)
            value = vs.compute(normalized_inputs)
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

    @staticmethod
    def _normalize_pressure(value: float | None) -> float | None:
        if value is None:
            return None
        try:
            raw = float(value)
        except Exception:
            return None
        if raw > 1500:
            return raw / 1000.0
        if raw > 300:
            return raw / 10.0
        if 6.0 <= raw <= 40.0:
            return raw * 3.386389
        return raw

    @staticmethod
    def _calc_specific_humidity(temp: float, rh: float, pressure: float) -> float | None:
        if pressure is None or pressure <= 0:
            return None
        rh_val = max(0.0, min(100.0, rh))
        es = 0.6108 * math.exp((17.27 * temp) / (temp + 237.3))
        ea = es * (rh_val / 100.0)
        denom = pressure - 0.378 * ea
        if denom <= 0:
            return None
        return 0.62197 * ea / denom

    @staticmethod
    def fn_specific_humidity(inputs: Dict[str, float], **params):
        temp = inputs.get("temperatura")
        rh = inputs.get("humedad")
        pres = inputs.get("presion")
        if temp is None or rh is None or pres is None:
            return None
        pressure = VirtualSensorManager._normalize_pressure(pres)
        if pressure is None:
            return None
        try:
            return VirtualSensorManager._calc_specific_humidity(float(temp), float(rh), pressure)
        except Exception:
            return None

    @staticmethod
    def fn_vpd_q(inputs: Dict[str, float], **params):
        temp = inputs.get("temperatura")
        rh = inputs.get("humedad")
        pres = inputs.get("presion")
        if temp is None or rh is None or pres is None:
            return None
        pressure = VirtualSensorManager._normalize_pressure(pres)
        if pressure is None:
            return None
        try:
            t_val = float(temp)
            rh_val = float(rh)
            q_act = VirtualSensorManager._calc_specific_humidity(t_val, rh_val, pressure)
            q_sat = VirtualSensorManager._calc_specific_humidity(t_val, 100.0, pressure)
            if q_act is None or q_sat is None:
                return None
            return max(0.0, q_sat - q_act)
        except Exception:
            return None

    @staticmethod
    def fn_pm_corrected(inputs: Dict[str, float], pm_key: str, humidity_key: str = "humedad"):
        pm_val = inputs.get(pm_key)
        rh = inputs.get(humidity_key)
        if pm_val is None or rh is None:
            return None
        try:
            pm = float(pm_val)
            rh_val = float(rh)
        except Exception:
            return None
        model = inputs.get("pm_model")
        calibrated = apply_pm_calibration(pm, rh_val, model)
        if calibrated is not None:
            return calibrated
        rh_clamped = max(0.0, min(100.0, rh_val))
        factor = 1.0 + 0.025 * max(0.0, rh_clamped - 40.0)
        return pm / max(0.1, factor)

    @staticmethod
    def fn_penman_monteith(inputs: Dict[str, float], **params):
        temp = inputs.get("temperatura")
        rh = inputs.get("humedad")
        rad = inputs.get("radiacion")
        wind = inputs.get("viento")
        pres = inputs.get("presion")
        if None in (temp, rh, rad, wind, pres):
            return None
        pressure = VirtualSensorManager._normalize_pressure(pres)
        if pressure is None:
            pressure = 101.325
        try:
            t_val = float(temp)
            rh_val = float(rh)
            rad_val = float(rad)
            wind_val = max(0.1, float(wind))
        except Exception:
            return None
        es = 0.6108 * math.exp((17.27 * t_val) / (t_val + 237.3))
        ea = es * (rh_val / 100.0)
        delta = 4098 * es / ((t_val + 237.3) ** 2)
        gamma = 0.000665 * pressure
        rn = rad_val * 0.0864
        g = 0.0
        denominator = delta + gamma * (1 + 0.34 * wind_val)
        if denominator == 0:
            return None
        eto = (0.408 * delta * (rn - g) + gamma * (900 / (t_val + 273.0)) * wind_val * (es - ea)) / denominator
        return max(0.0, eto)


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
        "sonometro": {
            "inputs": ["microfono", "ruido", "audio_peak"],
            "fn": lambda inputs, **params: max(
                inputs.get("ruido", 0),
                inputs.get("microfono", 0),
                inputs.get("audio_peak", 0)
            ),
            "params": {},
            "capabilities": ["ruido", "sonometro"],
        },
        "sismografo": {
            "inputs": ["giroscopio", "acelerometro", "vibracion", "microfono", "audio_peak"],
            "fn": lambda inputs, **params: max(
                abs(inputs.get("giroscopio", 0)),
                abs(inputs.get("acelerometro", 0)),
                abs(inputs.get("vibracion", 0)),
                abs(inputs.get("microfono", 0)),
                abs(inputs.get("audio_peak", 0))
            ),
            "params": {},
            "capabilities": ["sismo", "sismografo"],
        },
    }
    specs.update({
        "humedad_especifica": {
            "inputs": ["temperatura", "humedad", "presion"],
            "fn": VirtualSensorManager.fn_specific_humidity,
            "params": {},
            "capabilities": ["humedad_especifica", "humedad"],
        },
        "vpd_q": {
            "inputs": ["temperatura", "humedad", "presion"],
            "fn": VirtualSensorManager.fn_vpd_q,
            "params": {},
            "capabilities": ["vpd", "vpd_q"],
        },
        "pm25_corregido": {
            "inputs": ["pm25", "humedad"],
            "fn": lambda inputs, **params: VirtualSensorManager.fn_pm_corrected(inputs, pm_key="pm25"),
            "params": {},
            "capabilities": ["pm25", "calidad_aire"],
        },
        "pm10_corregido": {
            "inputs": ["pm10", "humedad"],
            "fn": lambda inputs, **params: VirtualSensorManager.fn_pm_corrected(inputs, pm_key="pm10"),
            "params": {},
            "capabilities": ["pm10", "calidad_aire"],
        },
        "evapotranspiracion_penman_monteith": {
            "inputs": ["temperatura", "humedad", "radiacion", "viento", "presion"],
            "fn": VirtualSensorManager.fn_penman_monteith,
            "params": {},
            "capabilities": ["et", "evapotranspiracion"],
        },
    })
    return specs


# ============================================================
# FIN DEL MÓDULO
# ============================================================
