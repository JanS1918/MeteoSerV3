# ============================================================
# MÓDULO UNIFICADO — LEARNING + SIMULATION
# Archivo: core/learning/learning_simulation.py
# ============================================================

import os
import json
import time
import math
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

# ------------------------------------------------------------
# UTILIDADES
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


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ------------------------------------------------------------
# MODELO LINEAL ONLINE
# ------------------------------------------------------------


class OnlineLinearModel:
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
        self.bias -= self.lr * err
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
# MODELO PREDICTIVO SIMPLE
# ------------------------------------------------------------


class SimplePredictiveModel:
    def __init__(
        self,
        name: str,
        weights: Dict[str, float],
        bias: float = 0.0,
        trend_alpha: float = 0.1,
        noise_std: float = 0.0,
    ):
        self.name = name
        self.weights = dict(weights)
        self.bias = bias
        self.trend_alpha = trend_alpha
        self.noise_std = noise_std
        self.last_trend = 0.0

    def predict(self, inputs: Dict[str, float], dt_seconds: float = 60.0) -> float:
        s = self.bias
        for k, w in self.weights.items():
            s += w * inputs.get(k, 0.0)
        trend = self.last_trend * (1 - self.trend_alpha) + self.trend_alpha * (
            s - self.last_trend
        )
        self.last_trend = trend
        noise = 0.0
        if self.noise_std > 0.0:
            import random

            u1 = random.random() or 1e-6
            u2 = random.random()
            z0 = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
            noise = z0 * self.noise_std * math.sqrt(dt_seconds / 60.0)
        return float(s + trend + noise)


# ------------------------------------------------------------
# LEARNING ENGINE
# ------------------------------------------------------------


class LearningEngine:
    def __init__(self, base_path: str, history_len: int = 1440):
        self.base_path = base_path
        self.history_len = history_len
        self.series: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.history_len)
        )
        self.timestamps: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.history_len)
        )
        self.models: Dict[str, OnlineLinearModel] = {}
        self.correlations: Dict[Tuple[str, str], float] = {}
        self.anomalies: List[Dict] = []
        os.makedirs(self.base_path, exist_ok=True)
        self._models_file = os.path.join(self.base_path, "learning_models.json")
        self._meta_file = os.path.join(self.base_path, "learning_meta.json")
        self._load_models()

    def ingest(
        self, sensor_values: Dict[str, float], timestamp: Optional[float] = None
    ):
        ts = timestamp or time.time()
        for s, v in sensor_values.items():
            try:
                fv = float(v)
            except Exception:
                continue
            self.series[s].append(fv)
            self.timestamps[s].append(ts)
        self._update_correlations(list(sensor_values.keys()))
        self._detect_anomalies(sensor_values)

    def _update_correlations(self, sensors: List[str]):
        for a in sensors:
            for b, seq_b in self.series.items():
                if a == b:
                    continue
                seq_a = list(self.series.get(a, []))
                seq_b = list(seq_b)
                n = min(len(seq_a), len(seq_b))
                if n < 10:
                    continue
                xs = seq_a[-n:]
                ys = seq_b[-n:]
                corr = pearson_corr(xs, ys)
                key = tuple(sorted((a, b)))
                self.correlations[key] = corr

    def top_correlations(self, sensor: str, top_n: int = 5):
        items = []
        for (a, b), c in self.correlations.items():
            if a == sensor:
                items.append((b, c))
            elif b == sensor:
                items.append((a, c))
        items.sort(key=lambda x: abs(x[1]), reverse=True)
        return items[:top_n]

    def ensure_model(self, target_sensor: str, lr: float = 0.001):
        if target_sensor not in self.models:
            self.models[target_sensor] = OnlineLinearModel(lr=lr)

    def train_online(
        self, target_sensor: str, feature_sensors: List[str], lr: float = 0.001
    ):
        self.ensure_model(target_sensor, lr=lr)
        model = self.models[target_sensor]
        lengths = [len(self.series[s]) for s in feature_sensors + [target_sensor]]
        if min(lengths) < 1:
            return False
        features = {s: float(self.series[s][-1]) for s in feature_sensors}
        target_value = float(self.series[target_sensor][-1])
        model.update(features, target_value)
        return True

    def predict(self, target_sensor: str, feature_values: Dict[str, float]):
        if target_sensor not in self.models:
            return None
        return self.models[target_sensor].predict(feature_values)

    def _detect_anomalies(self, sensor_values: Dict[str, float]):
        for s, v in sensor_values.items():
            seq = list(self.series.get(s, []))
            if len(seq) < 10:
                continue
            window = seq[-50:] if len(seq) >= 50 else seq
            m = mean(window)
            std = math.sqrt(variance(window))
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


# ------------------------------------------------------------
# SIMULATION ENGINE
# ------------------------------------------------------------


class SimulationEngine:
    MODELS_FILE = "simulation_models.json"

    def __init__(
        self, base_path: str, learning_engine: Optional[LearningEngine] = None
    ):
        self.base_path = base_path
        self.learning_engine = learning_engine
        self.models: Dict[str, SimplePredictiveModel] = {}
        os.makedirs(self.base_path, exist_ok=True)
        self._models_path = os.path.join(self.base_path, self.MODELS_FILE)
        self._load_models()

    def add_model(
        self,
        name: str,
        weights: Dict[str, float],
        bias: float = 0.0,
        trend_alpha: float = 0.1,
        noise_std: float = 0.0,
    ):
        self.models[name] = SimplePredictiveModel(
            name, weights, bias, trend_alpha, noise_std
        )
        self._save_models()

    def list_models(self):
        return list(self.models.keys())

    def _save_models(self):
        data = {
            n: {
                "weights": m.weights,
                "bias": m.bias,
                "trend_alpha": m.trend_alpha,
                "noise_std": m.noise_std,
                "last_trend": m.last_trend,
            }
            for n, m in self.models.items()
        }
        with open(self._models_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_models(self):
        if not os.path.exists(self._models_path):
            return
        try:
            with open(self._models_path, "r") as f:
                data = json.load(f)
                for n, md in data.items():
                    m = SimplePredictiveModel(
                        n,
                        md.get("weights", {}),
                        md.get("bias", 0.0),
                        md.get("trend_alpha", 0.1),
                        md.get("noise_std", 0.0),
                    )
                    m.last_trend = md.get("last_trend", 0.0)
                    self.models[n] = m
        except Exception:
            pass

    def step(self, real_inputs: Dict[str, float], dt_seconds: float = 60.0):
        inputs = dict(real_inputs)
        predictions = {}
        for name, model in self.models.items():
            try:
                pred = model.predict(inputs, dt_seconds=dt_seconds)
                minv = model.weights.get("_min", None)
                maxv = model.weights.get("_max", None)
                if minv is not None or maxv is not None:
                    if minv is None:
                        minv = -1e9
                    if maxv is None:
                        maxv = 1e9
                    pred = clamp(pred, float(minv), float(maxv))
                predictions[name] = float(pred)
            except Exception:
                predictions[name] = float("nan")
        return predictions

    def create_models_from_learning(self, top_n_features: int = 3):
        if not self.learning_engine:
            return
        for sensor in list(self.learning_engine.series.keys()):
            top = self.learning_engine.top_correlations(sensor, top_n=top_n_features)
            if not top:
                continue
            weights = {}
            total = sum(abs(c) for _, c in top) or 1.0
            for other, corr in top:
                weights[other] = corr / total
            if sensor not in self.models:
                self.add_model(
                    sensor, weights, bias=0.0, trend_alpha=0.05, noise_std=0.0
                )


# ============================================================
# FIN DEL MÓDULO
# ============================================================
