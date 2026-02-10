#!/usr/bin/env python3
"""
LSTM TRAINING SETUP - Experimentos de Predicción
================================================
Setup completo para entrenar modelos LSTM de predicción meteorológica.

IMPORTANTE: Esto es EXPERIMENTAL, NO producción.
- Requiere TensorFlow/Keras
- Requiere 90+ días de datos históricos
- Consumo RAM: ~1-2GB durante entrenamiento
- Tiempo: 30-60 min por modelo

Predicciones objetivo:
1. Temperatura próximas 3h (horizonte corto)
2. Presión próximas 6h (tendencias)
3. Humedad próximas 3h
4. Índice WBGT futuro (alerta temprana)

Autor: MeteoSerV3 - Fase 2 Experimentación
"""

import logging
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import json

logger = logging.getLogger("lstm_training")


@dataclass
class TrainingConfig:
    """Configuración de entrenamiento LSTM"""
    variable: str  # "temperatura", "presion", "humedad"
    sequence_length: int = 60  # Ventana de entrada (60 = 1h si samples=1min)
    prediction_horizon: int = 180  # Horizonte predicción (180min = 3h)
    batch_size: int = 32
    epochs: int = 50
    validation_split: float = 0.2
    lstm_units: int = 64
    dropout_rate: float = 0.2
    learning_rate: float = 0.001


@dataclass
class TrainingResult:
    """Resultado de entrenamiento"""
    variable: str
    model_path: str
    training_loss: float
    validation_loss: float
    mae: float  # Mean Absolute Error
    rmse: float  # Root Mean Squared Error
    r2_score: float
    training_time_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)


class LSTMTrainingSetup:
    """
    Setup de entrenamiento LSTM para predicción meteorológica.
    
    Workflow:
    1. Obtener datos históricos del Bus (90+ días)
    2. Preparar secuencias (X: ventana pasada, y: valor futuro)
    3. Entrenar modelo LSTM
    4. Validar predicciones
    5. Guardar modelo y métricas
    """
    
    def __init__(self, bus=None):
        """
        Args:
            bus: BusCapasInformacion (opcional)
        """
        from core.bus.bus_capas_informacion import obtener_bus
        self.bus = bus or obtener_bus()
        
        self.models_dir = Path("data/lstm_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.training_history: List[TrainingResult] = []
        
        # Verificar disponibilidad de TensorFlow
        self.tf_available = False
        try:
            import tensorflow as tf
            from tensorflow import keras
            self.tf = tf
            self.keras = keras
            self.tf_available = True
            logger.info(f"✅ TensorFlow {tf.__version__} disponible")
        except ImportError:
            logger.warning("⚠️ TensorFlow no disponible. Instalar: pip install tensorflow")
    
    def check_data_availability(self, variable: str, min_days: int = 90) -> Tuple[bool, int, str]:
        """
        Verifica si hay suficientes datos históricos.
        
        Args:
            variable: Nombre de la variable
            min_days: Días mínimos requeridos
        
        Returns:
            (disponible, dias_data, mensaje)
        """
        if variable not in self.bus.capa_timeseries:
            return False, 0, f"Variable '{variable}' sin histórico en Bus"
        
        ts = self.bus.capa_timeseries[variable]
        if len(ts.valores) == 0:
            return False, 0, "Histórico vacío"
        
        # Calcular rango temporal
        timestamps = [t for v, t in ts.valores]
        oldest = min(timestamps)
        newest = max(timestamps)
        days_available = (newest - oldest).total_seconds() / 86400
        
        if days_available < min_days:
            return False, int(days_available), f"Insuficiente: {int(days_available)} < {min_days} días"
        
        return True, int(days_available), f"✅ {int(days_available)} días disponibles"
    
    def prepare_sequences(self, 
                         variable: str, 
                         sequence_length: int = 60,
                         prediction_horizon: int = 180) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara secuencias para LSTM: (X, y)
        X = ventana pasada [t-n, ..., t-1, t]
        y = valor futuro [t+h]
        
        Args:
            variable: Variable a predecir
            sequence_length: Longitud de ventana (samples)
            prediction_horizon: Horizonte de predicción (samples)
        
        Returns:
            (X, y) arrays de NumPy
        """
        if variable not in self.bus.capa_timeseries:
            raise ValueError(f"Variable '{variable}' sin histórico")
        
        ts = self.bus.capa_timeseries[variable]
        valores = np.array([v for v, t in ts.valores])
        
        # Normalizar (0-1)
        min_val, max_val = valores.min(), valores.max()
        valores_norm = (valores - min_val) / (max_val - min_val + 1e-8)
        
        # Crear secuencias
        X, y = [], []
        
        for i in range(len(valores_norm) - sequence_length - prediction_horizon):
            # Ventana de entrada
            x_seq = valores_norm[i:i+sequence_length]
            # Valor objetivo (futuro)
            y_val = valores_norm[i + sequence_length + prediction_horizon]
            
            X.append(x_seq)
            y.append(y_val)
        
        X = np.array(X)
        y = np.array(y)
        
        # Reshape para LSTM: (samples, timesteps, features)
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        logger.info(f"[DATA] Secuencias preparadas: X={X.shape}, y={y.shape}")
        logger.info(f"       Normalización: [{min_val:.2f}, {max_val:.2f}]")
        
        # Guardar stats de normalización para desnormalizar predicciones
        norm_stats = {
            'min': float(min_val),
            'max': float(max_val)
        }
        self._save_normalization_stats(variable, norm_stats)
        
        return X, y
    
    def build_lstm_model(self, config: TrainingConfig):
        """
        Construye arquitectura LSTM.
        
        Arquitectura:
        - LSTM(64 units) + Dropout(0.2)
        - LSTM(32 units) + Dropout(0.2)
        - Dense(1) output
        """
        if not self.tf_available:
            raise RuntimeError("TensorFlow no disponible")
        
        model = self.keras.Sequential([
            self.keras.layers.LSTM(config.lstm_units, 
                                  return_sequences=True, 
                                  input_shape=(config.sequence_length, 1)),
            self.keras.layers.Dropout(config.dropout_rate),
            
            self.keras.layers.LSTM(config.lstm_units // 2, 
                                  return_sequences=False),
            self.keras.layers.Dropout(config.dropout_rate),
            
            self.keras.layers.Dense(1)
        ])
        
        model.compile(
            optimizer=self.keras.optimizers.Adam(learning_rate=config.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info(f"[MODEL] LSTM construido: {model.count_params()} parámetros")
        return model
    
    def train_model(self, config: TrainingConfig) -> Optional[TrainingResult]:
        """
        Entrena modelo LSTM completo.
        
        Args:
            config: Configuración de entrenamiento
        
        Returns:
            TrainingResult con métricas
        """
        if not self.tf_available:
            logger.error("TensorFlow no disponible")
            return None
        
        # 1. Verificar datos
        available, days, msg = self.check_data_availability(config.variable, min_days=30)
        if not available:
            logger.error(f"[ERROR] {msg}")
            return None
        
        logger.info(f"[TRAIN] Iniciando entrenamiento de {config.variable}")
        logger.info(f"        Datos: {msg}")
        
        # 2. Preparar secuencias
        X, y = self.prepare_sequences(
            config.variable,
            config.sequence_length,
            config.prediction_horizon
        )
        
        # 3. Split train/validation
        split_idx = int(len(X) * (1 - config.validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        logger.info(f"[SPLIT] Train: {len(X_train)} | Val: {len(X_val)}")
        
        # 4. Construir modelo
        model = self.build_lstm_model(config)
        
        # 5. Entrenar
        import time
        start_time = time.time()
        
        history = model.fit(
            X_train, y_train,
            batch_size=config.batch_size,
            epochs=config.epochs,
            validation_data=(X_val, y_val),
            verbose=1,
            callbacks=[
                self.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                )
            ]
        )
        
        training_time = time.time() - start_time
        
        # 6. Métricas finales
        try:
            from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
            y_pred = model.predict(X_val)
            mae = mean_absolute_error(y_val, y_pred)
            rmse = np.sqrt(mean_squared_error(y_val, y_pred))
            r2 = r2_score(y_val, y_pred)
        except ImportError:
            logger.warning("⚠️ scikit-learn no disponible. Instalar: pip install scikit-learn")
            y_pred = model.predict(X_val)
            mae = np.mean(np.abs(y_val - y_pred.flatten()))
            rmse = np.sqrt(np.mean((y_val - y_pred.flatten())**2))
            r2 = 1.0 - (np.sum((y_val - y_pred.flatten())**2) / np.sum((y_val - np.mean(y_val))**2))
        
        logger.info(f"[METRICS] MAE={mae:.4f}, RMSE={rmse:.4f}, R²={r2:.4f}")
        
        # 7. Guardar modelo
        model_path = self.models_dir / f"lstm_{config.variable}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.h5"
        model.save(str(model_path))
        logger.info(f"[SAVE] Modelo guardado: {model_path}")
        
        # 8. Resultado
        result = TrainingResult(
            variable=config.variable,
            model_path=str(model_path),
            training_loss=history.history['loss'][-1],
            validation_loss=history.history['val_loss'][-1],
            mae=float(mae),
            rmse=float(rmse),
            r2_score=float(r2),
            training_time_seconds=training_time
        )
        
        self.training_history.append(result)
        return result
    
    def train_all_sensors(self) -> List[TrainingResult]:
        """Entrena modelos para todos los sensores principales"""
        sensors = ["temperatura", "presion", "humedad"]
        results = []
        
        for sensor in sensors:
            logger.info(f"\n{'='*60}")
            logger.info(f"Entrenando modelo para: {sensor}")
            logger.info(f"{'='*60}")
            
            config = TrainingConfig(
                variable=sensor,
                sequence_length=60,  # 1h de histórico
                prediction_horizon=180,  # Predecir 3h futuro
                batch_size=32,
                epochs=50,
                lstm_units=64
            )
            
            result = self.train_model(config)
            if result:
                results.append(result)
                logger.info(f"✅ {sensor} completado (R²={result.r2_score:.3f})")
            else:
                logger.warning(f"⚠️ {sensor} falló")
        
        return results
    
    def _save_normalization_stats(self, variable: str, stats: Dict):
        """Guarda estadísticas de normalización"""
        stats_file = self.models_dir / f"norm_stats_{variable}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def load_model(self, model_path: str):
        """Carga modelo entrenado"""
        if not self.tf_available:
            raise RuntimeError("TensorFlow no disponible")
        
        return self.keras.models.load_model(model_path)
    
    def predict_future(self, 
                       variable: str, 
                       model_path: str, 
                       sequence_length: int = 60) -> Optional[float]:
        """
        Hace predicción con modelo entrenado.
        
        Args:
            variable: Variable a predecir
            model_path: Path del modelo .h5
            sequence_length: Longitud de ventana
        
        Returns:
            Predicción desnormalizada (valor real)
        """
        # Cargar modelo
        model = self.load_model(model_path)
        
        # Obtener últimas N muestras
        if variable not in self.bus.capa_timeseries:
            return None
        
        ts = self.bus.capa_timeseries[variable]
        valores = np.array([v for v, t in ts.valores])
        
        if len(valores) < sequence_length:
            logger.warning(f"Insuficientes datos: {len(valores)} < {sequence_length}")
            return None
        
        # Cargar stats de normalización
        stats_file = self.models_dir / f"norm_stats_{variable}.json"
        with open(stats_file, 'r') as f:
            norm_stats = json.load(f)
        
        min_val = norm_stats['min']
        max_val = norm_stats['max']
        
        # Normalizar últimos valores
        last_values = valores[-sequence_length:]
        last_values_norm = (last_values - min_val) / (max_val - min_val + 1e-8)
        
        # Reshape para LSTM
        X = last_values_norm.reshape((1, sequence_length, 1))
        
        # Predecir
        y_pred_norm = model.predict(X, verbose=0)[0][0]
        
        # Desnormalizar
        y_pred = y_pred_norm * (max_val - min_val) + min_val
        
        logger.info(f"[PRED] {variable}: {y_pred:.2f}")
        return float(y_pred)
    
    def get_training_summary(self) -> Dict[str, Any]:
        """Resumen de todos los entrenamientos"""
        if not self.training_history:
            return {"message": "Sin entrenamientos registrados"}
        
        summary = {
            "total_trainings": len(self.training_history),
            "models": []
        }
        
        for result in self.training_history:
            summary["models"].append({
                "variable": result.variable,
                "model_path": result.model_path,
                "mae": result.mae,
                "rmse": result.rmse,
                "r2_score": result.r2_score,
                "training_time": f"{result.training_time_seconds:.1f}s",
                "timestamp": result.timestamp.isoformat()
            })
        
        return summary


# Singleton global
_lstm_setup: Optional[LSTMTrainingSetup] = None

def get_lstm_setup(bus=None) -> LSTMTrainingSetup:
    """Obtiene instancia singleton del LSTM training setup"""
    global _lstm_setup
    if _lstm_setup is None:
        _lstm_setup = LSTMTrainingSetup(bus)
    return _lstm_setup


if __name__ == "__main__":
    # Test de configuración
    logging.basicConfig(level=logging.INFO)
    
    lstm = get_lstm_setup()
    
    if lstm.tf_available:
        print("✅ TensorFlow disponible - Listo para entrenar")
        print("\nEjemplo de uso:")
        print("  config = TrainingConfig(variable='temperatura', epochs=50)")
        print("  result = lstm.train_model(config)")
        print("\nPara entrenar todos:")
        print("  results = lstm.train_all_sensors()")
    else:
        print("⚠️ TensorFlow no disponible")
        print("Instalar: pip install tensorflow")
    
    print("\n📋 Modelos existentes:")
    for model_file in lstm.models_dir.glob("*.h5"):
        print(f"  {model_file.name}")
