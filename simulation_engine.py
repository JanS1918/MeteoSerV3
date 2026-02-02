# ============================================================
# MÓDULO 4 — SIMULACIÓN INTERNA (MODELOS PREDICTIVOS)
# Archivo: core/simulation/simulation_engine.py
# ============================================================

import math
import time
import json
import os
from typing import Dict, List, Optional, Tuple

# Intentamos importar componentes auxiliares si existen
try:
    from ..learning.learning_engine import LearningEngine
except Exception:
    LearningEngine = None

try:
    from ..sensors.virtual_sensors import VirtualSensorManager
except Exception:
    VirtualSensorManager = None


# ------------------------------------------------------------
# UTILIDADES NUMÉRICAS SIMPLES
# ------------------------------------------------------------
def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ------------------------------------------------------------
# MODELO DE SIMULACIÓN SIMPLE MULTIVARIABLE
# ------------------------------------------------------------
class SimplePredictiveModel:
    """
    Modelo predictivo simple basado en:
    - combinación lineal de inputs
    - ajuste por tendencia exponencial
    - ruido controlado
    Diseñado para simulaciones internas que alimentan decisiones.
    """

    def __init__(self, name: str, weights: Dict[str, float], bias: float = 0.0, trend_alpha: float = 0.1, noise_std: float = 0.0):
        self.name = name
        self.weights = dict(weights)
        self.bias = bias
        self.trend_alpha = trend_alpha  # suavizado exponencial para tendencia
        self.noise_std = noise_std
        self.last_trend = 0.0

    def predict(self, inputs: Dict[str, float], dt_seconds: float = 60.0) -> float:
        s = self.bias
        for k, w in self.weights.items():
            s += w * inputs.get(k, 0.0)
        # aplicar tendencia suavizada
        trend = self.last_trend * (1.0 - self.trend_alpha) + self.trend_alpha * (s - self.last_trend)
        self.last_trend = trend
        # añadir ruido gaussiano simple (si noise_std > 0)
        noise = 0.0
        if self.noise_std > 0.0:
            # uso de Box-Muller simple
            import random
            u1 = random.random() or 1e-6
            u2 = random.random()
            z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
            noise = z0 * self.noise_std * math.sqrt(dt_seconds / 60.0)
        return float(s + trend + noise)


# ------------------------------------------------------------
# MOTOR DE SIMULACIÓN
# ------------------------------------------------------------
class SimulationEngine:
    """
    Motor que gestiona modelos predictivos internos.
    - mantiene modelos simples
    - ejecuta pasos de simulación con inputs reales y virtuales
    - produce predicciones que pueden alimentar índices y auto-evolución
    """

    MODELS_FILE = "simulation_models.json"

    def __init__(self, base_path: str, learning_engine: Optional[LearningEngine] = None, virtual_manager: Optional[VirtualSensorManager] = None):
        self.base_path = base_path
        self.learning_engine = learning_engine
        self.virtual_manager = virtual_manager
        self.models: Dict[str, SimplePredictiveModel] = {}
        os.makedirs(self.base_path, exist_ok=True)
        self._models_path = os.path.join(self.base_path, self.MODELS_FILE)
        self._load_models()
        
        # ⚛️ CEREBRO ESTADÍSTICO UNIVERSAL V1.3
        self.statistical_brain = StatisticalBrain(history_length=1440) if StatisticalBrain else None

    # ------------------------------------------------------------
    # GESTIÓN DE MODELOS
    # ------------------------------------------------------------
    def add_model(self, name: str, weights: Dict[str, float], bias: float = 0.0, trend_alpha: float = 0.1, noise_std: float = 0.0):
        self.models[name] = SimplePredictiveModel(name, weights, bias, trend_alpha, noise_std)
        self._save_models()

    def remove_model(self, name: str):
        if name in self.models:
            del self.models[name]
            self._save_models()

    def list_models(self) -> List[str]:
        return list(self.models.keys())

    def get_model_info(self, name: str) -> Optional[Dict]:
        m = self.models.get(name)
        if not m:
            return None
        return {
            "name": m.name,
            "weights": m.weights,
            "bias": m.bias,
            "trend_alpha": m.trend_alpha,
            "noise_std": m.noise_std,
            "last_trend": m.last_trend
        }

    def _save_models(self):
        data = {n: {"weights": m.weights, "bias": m.bias, "trend_alpha": m.trend_alpha, "noise_std": m.noise_std, "last_trend": m.last_trend} for n, m in self.models.items()}
        with open(self._models_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_models(self):
        if not os.path.exists(self._models_path):
            return
        try:
            with open(self._models_path, "r") as f:
                data = json.load(f)
                for n, md in data.items():
                    m = SimplePredictiveModel(n, md.get("weights", {}), md.get("bias", 0.0), md.get("trend_alpha", 0.1), md.get("noise_std", 0.0))
                    m.last_trend = md.get("last_trend", 0.0)
                    self.models[n] = m
        except Exception:
            pass

    # ------------------------------------------------------------
    # EJECUCIÓN DE PASO DE SIMULACIÓN
    # ------------------------------------------------------------
    def step(self, real_inputs: Dict[str, float], dt_seconds: float = 60.0) -> Dict[str, float]:
        """
        Ejecuta un paso de simulación:
        - combina inputs reales y virtuales (si hay virtual_manager)
        - ejecuta cada modelo y devuelve predicciones
        - integra suavizado Savitzky-Golay y EKF con Cerebro Estadístico V1.3
        """
        # ⚛️ CEREBRO ESTADÍSTICO: Suavizado de inputs críticos antes de física
        smoothed_inputs = real_inputs.copy()
        if self.statistical_brain and self.learning_engine:
            # Suavizar inputs críticos (presión, temperatura) para astronomía y vuelo
            critical_sensors = ["presion", "temperatura", "viento", "presion_atmosferica"]
            for sensor in critical_sensors:
                if sensor in real_inputs:
                    # Ingerir en cerebro
                    self.statistical_brain.ingest({sensor: real_inputs[sensor]})
                    # Obtener serie suavizada
                    smoothed = self.statistical_brain.smooth_series(sensor, window=11, order=3)
                    if smoothed:
                        smoothed_inputs[sensor] = smoothed[-1]
        
        # construir inputs combinados
        inputs = dict(smoothed_inputs)
        if self.virtual_manager:
            # intentar obtener últimos valores de virtuals
            for vid in self.virtual_manager.list_virtuals():
                info = self.virtual_manager.get_virtual_info(vid)
                if info and info.get("last_value") is not None:
                    inputs[vid] = info["last_value"]

        predictions: Dict[str, float] = {}
        for name, model in self.models.items():
            try:
                pred = model.predict(inputs, dt_seconds=dt_seconds)
                # aplicar límites razonables si la especificación del modelo lo requiere
                # (si en weights hay claves especiales 'min'/'max' se usan)
                minv = model.weights.get("_min", None)
                maxv = model.weights.get("_max", None)
                if minv is not None or maxv is not None:
                    if minv is None:
                        minv = -1e9
                    if maxv is None:
                        maxv = 1e9
                    pred = clamp(pred, float(minv), float(maxv))
                
                # ⚛️ EKF: Predicción con modelo físico si disponible
                if self.statistical_brain and name in ["humedad_pared", "sorcion_gab"]:
                    # Modelo físico para GAB (simplificado)
                    def gab_model(state, dt):
                        # Estado: [humedad, tasa_absorcion]
                        return state  # TODO: Implementar modelo GAB completo
                    
                    pred_ekf = self.statistical_brain.predict_with_ekf(name, gab_model, dt_seconds)
                    if pred_ekf is not None:
                        pred = pred_ekf
                
                predictions[name] = float(pred)
            except Exception:
                predictions[name] = float("nan")
        
        # ⚛️ METADATA: Quantum_Universal_Metrology_v1.3
        predictions["_metadata"] = {
            "motor": "Quantum_Universal_Metrology_v1.3",
            "smoothing": "savitzky_golay" if self.statistical_brain else "none",
            "ekf_active": self.statistical_brain is not None
        }
        
        return predictions

    # ------------------------------------------------------------
    # UTILIDADES PARA CREAR MODELOS DESDE APRENDIZAJE
    # ------------------------------------------------------------
    def create_models_from_learning(self, top_n_features: int = 3):
        """
        Si existe LearningEngine, crear modelos predictivos simples para variables clave
        usando correlaciones detectadas por el motor de aprendizaje.
        """
        if not self.learning_engine:
            return
        # crear modelos para cada sensor con correlaciones fuertes
        for sensor in list(self.learning_engine.series.keys()):
            top = self.learning_engine.top_correlations(sensor, top_n=top_n_features)
            if not top:
                continue
            weights = {}
            # asignar pesos proporcionales a correlación
            total = sum(abs(c) for _, c in top) or 1.0
            for other, corr in top:
                weights[other] = corr / total
            # añadir modelo si no existe
            if sensor not in self.models:
                self.add_model(sensor, weights, bias=0.0, trend_alpha=0.05, noise_std=0.0)

    # ------------------------------------------------------------
    # EXPORTAR PREDICCIONES A OTROS MÓDULOS
    # ------------------------------------------------------------
    def export_predictions(self, predictions: Dict[str, float], target_callback: Optional[callable] = None):
        """
        Exporta predicciones a un callback (por ejemplo, índices o evolución).
        Si no se proporciona callback, guarda en disco como registro simple.
        """
        ts = time.time()
        payload = {"ts": ts, "predictions": predictions}
        if callable(target_callback):
            try:
                target_callback(payload)
                return
            except Exception:
                pass
        # fallback: guardar en archivo de log
        log_file = os.path.join(self.base_path, "simulation_predictions.log")
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(payload) + "\n")
        except Exception:
            pass

# ============================================================
# FIN DEL MÓDULO
# ============================================================