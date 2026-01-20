# ============================================================
# MÓDULO 3 — APRENDIZAJE Y PATRONES
# Archivo: core/learning/learning_engine.py
# ============================================================

import json
import math
import os
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

# Intentamos importar componentes auxiliares si existen
try:
    from ..integration.integration_manager import (
        SensorIntegrationManager,
        SensorRegistry,
    )
except Exception:
    SensorIntegrationManager = None
    SensorRegistry = None

try:
    from ..sensors.virtual_sensors import VirtualSensorManager
except Exception:
    VirtualSensorManager = None


# ------------------------------------------------------------
# UTILIDADES ESTADÍSTICAS SIMPLES (sin dependencias externas)
# ------------------------------------------------------------
def mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def variance(xs: List[float]) -> float:
    if not xs:
        return 0.0
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def pearson_corr(xs: List[float], ys: List[float]) -> float:
    if not xs or not ys or len(xs) != len(ys):
        return 0.0
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    if denx == 0 or deny == 0:
        return 0.0
    return num / (denx * deny)


# ------------------------------------------------------------
# MODELO SIMPLE ONLINE: REGRESIÓN LINEAL INCREMENTAL (SGD)
# ------------------------------------------------------------
class OnlineLinearModel:
    """
    Modelo lineal simple entrenado con SGD online.
    - weights: dict feature->weight
    - bias: float
    - lr: learning rate
    """

    def __init__(self, lr: float = 0.001):
        self.weights: Dict[str, float] = {}
        self.bias: float = 0.0
        self.lr = lr

    def predict(self, features: Dict[str, float]) -> float:
        s = self.bias
        for k, v in features.items():
            s += self.weights.get(k, 0.0) * v
        return s

    def update(self, features: Dict[str, float], target: float):
        pred = self.predict(features)
        err = pred - target
        # update bias
        self.bias -= self.lr * err
        # update weights
        for k, v in features.items():
            w = self.weights.get(k, 0.0)
            w -= self.lr * err * v
            self.weights[k] = w

    def to_dict(self):
        return {"weights": self.weights, "bias": self.bias, "lr": self.lr}

    @classmethod
    def from_dict(cls, d):
        m = cls(lr=d.get("lr", 0.001))
        m.weights = d.get("weights", {})
        m.bias = d.get("bias", 0.0)
        return m


# ------------------------------------------------------------
# LEARNING ENGINE
# ------------------------------------------------------------
class LearningEngine:
    """
    Motor de aprendizaje y detección de patrones.
    - almacena series temporales por sensor
    - calcula correlaciones entre pares
    - entrena modelos online para predicción de variables clave
    - detecta anomalías simples
    - exporta/importa modelos y metadatos
    """

    def __init__(
        self,
        base_path: str,
        registry: Optional[SensorRegistry] = None,
        virtual_manager: Optional[VirtualSensorManager] = None,
        history_len: int = 1440,
    ):
        """
        base_path: carpeta donde guardar modelos y metadatos
        history_len: número máximo de muestras por sensor (por defecto 1440)
        """
        self.base_path = base_path
        self.registry = registry
        self.virtual_manager = virtual_manager
        self.history_len = history_len

        # series: sensor_id -> deque(values)
        self.series: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.history_len)
        )
        # timestamps: sensor_id -> deque(timestamps)
        self.timestamps: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.history_len)
        )

        # modelos: target_sensor -> OnlineLinearModel
        self.models: Dict[str, OnlineLinearModel] = {}

        # correlaciones cacheadas: (a,b) -> corr
        self.correlations: Dict[Tuple[str, str], float] = {}

        # anomalías detectadas (simple)
        self.anomalies: List[Dict] = []

        # persistencia
        os.makedirs(self.base_path, exist_ok=True)
        self._models_file = os.path.join(self.base_path, "learning_models.json")
        self._meta_file = os.path.join(self.base_path, "learning_meta.json")
        self._load_models()

    # ------------------------------------------------------------
    # INGESTA DE DATOS
    # ------------------------------------------------------------
    def ingest(
        self, sensor_values: Dict[str, float], timestamp: Optional[float] = None
    ):
        """
        Ingesta un diccionario sensor->valor en el motor.
        Actualiza series, calcula correlaciones básicas y detecta anomalías.
        """
        ts = timestamp or time.time()
        for s, v in sensor_values.items():
            try:
                fv = float(v)
            except Exception:
                continue
            self.series[s].append(fv)
            self.timestamps[s].append(ts)

        # actualizar correlaciones para pares con suficientes datos
        self._update_correlations(list(sensor_values.keys()))

        # detectar anomalías simples
        self._detect_anomalies(sensor_values)

    # ------------------------------------------------------------
    # CORRELACIONES Y PATRONES
    # ------------------------------------------------------------
    def _update_correlations(self, sensors: List[str]):
        """
        Recalcula correlaciones entre los sensores listados y otros con datos.
        """
        for a in sensors:
            for b, seq_b in self.series.items():
                if a == b:
                    continue
                seq_a = list(self.series.get(a, []))
                seq_b = list(seq_b)
                # usar la longitud mínima para alinear
                n = min(len(seq_a), len(seq_b))
                if n < 10:
                    continue
                xs = seq_a[-n:]
                ys = seq_b[-n:]
                corr = pearson_corr(xs, ys)
                key = tuple(sorted((a, b)))
                self.correlations[key] = corr

    def top_correlations(self, sensor: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Devuelve los sensores más correlacionados con 'sensor'.
        """
        items = []
        for (a, b), c in self.correlations.items():
            other = None
            if a == sensor:
                other = b
            elif b == sensor:
                other = a
            if other:
                items.append((other, c))
        items.sort(key=lambda x: abs(x[1]), reverse=True)
        return items[:top_n]

    # ------------------------------------------------------------
    # ENTRENAMIENTO ONLINE
    # ------------------------------------------------------------
    def ensure_model(self, target_sensor: str, lr: float = 0.001):
        if target_sensor not in self.models:
            self.models[target_sensor] = OnlineLinearModel(lr=lr)

    def train_online(
        self, target_sensor: str, feature_sensors: List[str], lr: float = 0.001
    ):
        """
        Entrena online el modelo para predecir target_sensor usando feature_sensors.
        Usa la última muestra disponible si hay datos alineados.
        """
        self.ensure_model(target_sensor, lr=lr)
        model = self.models[target_sensor]

        # construir features y target a partir de las últimas muestras alineadas
        lengths = [len(self.series[s]) for s in feature_sensors + [target_sensor]]
        if min(lengths) < 1:
            return False

        # tomar la última muestra index por sensor (alineación simple por índice final)
        features = {}
        for s in feature_sensors:
            seq = self.series.get(s)
            if not seq:
                features[s] = 0.0
            else:
                features[s] = float(seq[-1])

        target_seq = self.series.get(target_sensor)
        target_value = float(target_seq[-1]) if target_seq else 0.0

        model.update(features, target_value)
        return True

    def predict(
        self, target_sensor: str, feature_values: Dict[str, float]
    ) -> Optional[float]:
        if target_sensor not in self.models:
            return None
        return self.models[target_sensor].predict(feature_values)

    # ------------------------------------------------------------
    # DETECCIÓN DE ANOMALÍAS (REGLAS SIMPLES)
    # ------------------------------------------------------------
    def _detect_anomalies(self, sensor_values: Dict[str, float]):
        """
        Detecta anomalías por desviación respecto a media móvil y por saltos bruscos.
        Registra eventos en self.anomalies.
        """
        for s, v in sensor_values.items():
            seq = list(self.series.get(s, []))
            if len(seq) < 10:
                continue
            window = seq[-50:] if len(seq) >= 50 else seq
            m = mean(window)
            var = variance(window)
            std = math.sqrt(var)
            # desviación z
            z = (v - m) / (std + 1e-6)
            if abs(z) > 4.0:
                self.anomalies.append(
                    {
                        "sensor": s,
                        "value": v,
                        "type": "outlier_z",
                        "z": z,
                        "ts": time.time(),
                    }
                )
            # salto brusco respecto a anterior
            if len(seq) >= 2:
                prev = seq[-2]
                if prev != 0 and abs((v - prev) / (abs(prev) + 1e-6)) > 0.5:
                    self.anomalies.append(
                        {
                            "sensor": s,
                            "value": v,
                            "type": "sudden_jump",
                            "prev": prev,
                            "ts": time.time(),
                        }
                    )

    # ------------------------------------------------------------
    # EXPORT / IMPORT MODELOS Y METADATOS
    # ------------------------------------------------------------
    def _load_models(self):
        if os.path.exists(self._models_file):
            try:
                with open(self._models_file, "r") as f:
                    data = json.load(f)
                    for target, md in data.get("models", {}).items():
                        self.models[target] = OnlineLinearModel.from_dict(md)
            except Exception:
                pass

    def save_models(self):
        data = {"models": {t: m.to_dict() for t, m in self.models.items()}}
        with open(self._models_file, "w") as f:
            json.dump(data, f, indent=2)

    def export_meta(self):
        meta = {
            "sensors": {s: len(self.series[s]) for s in self.series},
            "correlations_count": len(self.correlations),
            "anomalies_count": len(self.anomalies),
            "models": list(self.models.keys()),
        }
        with open(self._meta_file, "w") as f:
            json.dump(meta, f, indent=2)

    # ------------------------------------------------------------
    # UTILIDADES Y CONSULTAS
    # ------------------------------------------------------------
    def get_series(self, sensor: str, n: int = 100) -> List[float]:
        seq = list(self.series.get(sensor, []))
        return seq[-n:]

    def get_anomalies(self, since_ts: Optional[float] = None) -> List[Dict]:
        if since_ts is None:
            return list(self.anomalies)
        return [a for a in self.anomalies if a.get("ts", 0) >= since_ts]

    def get_model_info(self, target_sensor: str) -> Optional[Dict]:
        m = self.models.get(target_sensor)
        if not m:
            return None
        return m.to_dict()

    # ------------------------------------------------------------
    # INTEGRACIÓN CON SENSORES VIRTUALES (OPCIONAL)
    # ------------------------------------------------------------
    def integrate_with_virtuals(self):
        """
        Si existe VirtualSensorManager, usar sensores virtuales activos como features.
        """
        if not self.virtual_manager:
            return
        # ejemplo: crear/actualizar modelos para sensores virtuales activos
        for vid in self.virtual_manager.list_virtuals():
            info = self.virtual_manager.get_virtual_info(vid)
            if not info:
                continue
            if info.get("active"):
                # elegir features: top correlaciones con el virtual si existen
                top = self.top_correlations(vid, top_n=3)
                features = [t[0] for t in top]
                # crear modelo si no existe
                self.ensure_model(vid)
                # intentar entrenar online si hay datos
                self.train_online(vid, features)


# ============================================================
# FIN DEL MÓDULO
# ============================================================
