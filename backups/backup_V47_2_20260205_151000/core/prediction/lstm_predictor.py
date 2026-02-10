"""
LSTM PREDICTOR - Red Neuronal para Predicción de Series Temporales
===================================================================
Predice valores futuros de UTCI, ET0, temperatura, etc. basándose
en histórico reciente (últimos 60 minutos).

Arquitectura:
    - Input: Secuencia de 60 muestras × 5 features (T, HR, P, V, Rad)
    - LSTM: 64 unidades con dropout
    - Dense: 32 unidades con regularización
    - Output: Valor predicho +5 min (o +10, +15)

Entrenamiento:
    - Recolecta 7 días de datos históricos
    - Entrena offline
    - Guarda modelo en data/models/lstm_utci.keras

Uso en producción:
    - Obtiene últimos 60 puntos del Bus (TIMESERIES)
    - Predice valor +5 min
    - Publica "prediccion.utci_plus_5min" al Bus (CORE)
"""

import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from collections import deque
import json

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠️ TensorFlow no disponible. Instalarlo con: pip install tensorflow")


class PreparadorDatos:
    """Prepara datos del Bus para entrenamiento LSTM"""
    
    def __init__(self, ventana: int = 60, horizonte: int = 5):
        """
        Args:
            ventana: Cuántas muestras mirar hacia atrás (default 60 min)
            horizonte: Cuántos minutos predecir hacia adelante (default 5)
        """
        self.ventana = ventana
        self.horizonte = horizonte
    
    def preparar_desde_bus(self, bus, variable: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extrae secuencias de entrenamiento del Bus (TIMESERIES)
        
        Args:
            bus: Instancia de BusCapasInformacion
            variable: Variable a predecir (ej: "temperatura_c")
        
        Returns:
            X: array shape (N, ventana, features)
            y: array shape (N,) - valores futuros
        """
        if variable not in bus.capa_timeseries:
            raise ValueError(f"Variable {variable} no tiene histórico en Bus")
        
        ts = bus.capa_timeseries[variable]
        valores = [(v, ts) for v, ts in ts.valores]
        
        if len(valores) < self.ventana + self.horizonte:
            raise ValueError(f"Insuficiente data: {len(valores)} < {self.ventana + self.horizonte}")
        
        X = []
        y = []
        
        for i in range(len(valores) - self.ventana - self.horizonte):
            # Ventana de entrada
            ventana_actual = [valores[j][0] for j in range(i, i + self.ventana)]
            # Valor futuro
            valor_futuro = valores[i + self.ventana + self.horizonte][0]
            
            X.append(ventana_actual)
            y.append(valor_futuro)
        
        return np.array(X), np.array(y)
    
    def preparar_multivariable(self, bus, variables: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara datos con múltiples features (T, HR, P, V, etc.)
        
        Args:
            bus: BusCapasInformacion
            variables: Lista de variables (ej: ["temperatura_c", "humedad_rh"])
        
        Returns:
            X: array shape (N, ventana, len(variables))
            y: array shape (N,) - predice primera variable
        """
        # Verificar que todas existen
        for var in variables:
            if var not in bus.capa_timeseries:
                raise ValueError(f"Variable {var} sin histórico")
        
        # Obtener el mínimo común de muestras
        min_muestras = min(
            len(bus.capa_timeseries[var].valores)
            for var in variables
        )
        
        if min_muestras < self.ventana + self.horizonte:
            raise ValueError(f"Insuficiente data multivariable: {min_muestras}")
        
        X = []
        y = []
        
        for i in range(min_muestras - self.ventana - self.horizonte):
            ventana_multi = []
            
            for t in range(self.ventana):
                features = [
                    bus.capa_timeseries[var].valores[i + t][0]
                    for var in variables
                ]
                ventana_multi.append(features)
            
            # Predecimos la primera variable
            valor_futuro = bus.capa_timeseries[variables[0]].valores[
                i + self.ventana + self.horizonte
            ][0]
            
            X.append(ventana_multi)
            y.append(valor_futuro)
        
        return np.array(X), np.array(y)
    
    def normalizar(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """Normaliza datos (0-1) y guarda parámetros"""
        X_min = X.min(axis=(0, 1), keepdims=True)
        X_max = X.max(axis=(0, 1), keepdims=True)
        
        X_norm = (X - X_min) / (X_max - X_min + 1e-8)
        
        y_min = y.min()
        y_max = y.max()
        y_norm = (y - y_min) / (y_max - y_min + 1e-8)
        
        params = {
            'X_min': X_min.tolist(),
            'X_max': X_max.tolist(),
            'y_min': float(y_min),
            'y_max': float(y_max)
        }
        
        return X_norm, y_norm, params


class LSTMPredictor:
    """Modelo LSTM para predicción de series temporales"""
    
    def __init__(self, ventana: int = 60, features: int = 1):
        """
        Args:
            ventana: Tamaño ventana temporal
            features: Número de features (1=univariado, 5=multivariado)
        """
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow no disponible")
        
        self.ventana = ventana
        self.features = features
        self.modelo = None
        self.params_normalizacion = None
        self.compilado = False
    
    def construir(self, lstm_units: int = 64, dense_units: int = 32, dropout: float = 0.2):
        """Construye arquitectura del modelo"""
        self.modelo = keras.Sequential([
            layers.Input(shape=(self.ventana, self.features)),
            
            # LSTM con dropout
            layers.LSTM(lstm_units, return_sequences=False, dropout=dropout),
            
            # Capa densa con regularización
            layers.Dense(dense_units, activation='relu',
                        kernel_regularizer=keras.regularizers.l2(0.01)),
            layers.Dropout(dropout),
            
            # Output
            layers.Dense(1)
        ])
        
        self.modelo.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.compilado = True
    
    def entrenar(self, X: np.ndarray, y: np.ndarray, 
                 epochs: int = 50, batch_size: int = 32,
                 validation_split: float = 0.2) -> Dict:
        """
        Entrena el modelo
        
        Returns:
            historia: Métricas de entrenamiento
        """
        if not self.compilado:
            self.construir()
        
        historia = self.modelo.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=5,
                    restore_best_weights=True
                )
            ]
        )
        
        return {
            'loss': historia.history['loss'],
            'val_loss': historia.history['val_loss'],
            'mae': historia.history['mae'],
            'val_mae': historia.history['val_mae']
        }
    
    def predecir(self, X: np.ndarray) -> np.ndarray:
        """Predice valores futuros"""
        if not self.compilado:
            raise RuntimeError("Modelo no construido/entrenado")
        
        return self.modelo.predict(X, verbose=0)
    
    def guardar(self, ruta: str):
        """Guarda modelo y parámetros de normalización"""
        if not self.compilado:
            raise RuntimeError("Modelo no construido")
        
        ruta_path = Path(ruta)
        ruta_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar modelo
        self.modelo.save(ruta_path.with_suffix('.keras'))
        
        # Guardar metadatos
        metadata = {
            'ventana': self.ventana,
            'features': self.features,
            'params_normalizacion': self.params_normalizacion,
            'fecha_entrenamiento': datetime.now().isoformat()
        }
        
        with open(ruta_path.with_suffix('.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def cargar(self, ruta: str):
        """Carga modelo previamente guardado"""
        ruta_path = Path(ruta)
        
        # Cargar modelo
        self.modelo = keras.models.load_model(ruta_path.with_suffix('.keras'))
        self.compilado = True
        
        # Cargar metadatos
        with open(ruta_path.with_suffix('.json'), 'r') as f:
            metadata = json.load(f)
        
        self.ventana = metadata['ventana']
        self.features = metadata['features']
        self.params_normalizacion = metadata.get('params_normalizacion')
    
    def set_params_normalizacion(self, params: Dict):
        """Guarda parámetros para desnormalizar predicciones"""
        self.params_normalizacion = params
    
    def desnormalizar_prediccion(self, y_norm: np.ndarray) -> np.ndarray:
        """Desnormaliza predicción a escala original"""
        if self.params_normalizacion is None:
            return y_norm
        
        y_min = self.params_normalizacion['y_min']
        y_max = self.params_normalizacion['y_max']
        
        return y_norm * (y_max - y_min) + y_min


def entrenar_modelo_utci(bus, 
                         horizonte: int = 5,
                         epochs: int = 50,
                         guardar_en: str = "data/models/lstm_utci") -> LSTMPredictor:
    """
    Función helper: Entrena modelo UTCI desde cero
    
    Args:
        bus: BusCapasInformacion con datos históricos
        horizonte: Minutos a predecir (default 5)
        epochs: Épocas de entrenamiento
        guardar_en: Ruta donde guardar modelo
    
    Returns:
        Modelo entrenado
    """
    print(f"\n🚀 Entrenando modelo LSTM para predicción UTCI (+{horizonte} min)...")
    
    # 1. Preparar datos
    preparador = PreparadorDatos(ventana=60, horizonte=horizonte)
    
    # Variables multivariables
    variables = ["temperatura_c", "humedad_rh", "presion_hpa", "viento_ms"]
    
    print(f"   Extrayendo datos de {len(variables)} variables...")
    X, y = preparador.preparar_multivariable(bus, variables)
    print(f"   ✅ Preparados: {len(X)} secuencias de entrenamiento")
    
    # 2. Normalizar
    print("   Normalizando datos...")
    X_norm, y_norm, params = preparador.normalizar(X, y)
    
    # 3. Crear modelo
    print(f"   Construyendo LSTM (ventana={preparador.ventana}, features={len(variables)})...")
    modelo = LSTMPredictor(ventana=preparador.ventana, features=len(variables))
    modelo.construir(lstm_units=64, dense_units=32, dropout=0.2)
    modelo.set_params_normalizacion(params)
    
    # 4. Entrenar
    print(f"   Entrenando ({epochs} epochs)...")
    historia = modelo.entrenar(X_norm, y_norm, epochs=epochs, batch_size=32)
    
    final_loss = historia['val_loss'][-1]
    final_mae = historia['val_mae'][-1]
    print(f"   ✅ Entrenado: val_loss={final_loss:.4f}, val_mae={final_mae:.4f}")
    
    # 5. Guardar
    print(f"   Guardando modelo en {guardar_en}...")
    modelo.guardar(guardar_en)
    print(f"   ✅ Modelo guardado")
    
    return modelo


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║          LSTM PREDICTOR - Sistema de Predicción              ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Para entrenar un modelo:
    
        from core.bus import obtener_bus
        from core.prediction import entrenar_modelo_utci
        
        bus = obtener_bus()
        # (asegurarse de tener 7+ días de datos en TIMESERIES)
        
        modelo = entrenar_modelo_utci(bus, horizonte=5, epochs=50)
    
    Para usar un modelo entrenado:
    
        from core.prediction import LSTMPredictor
        
        modelo = LSTMPredictor()
        modelo.cargar("data/models/lstm_utci")
        
        # Obtener últimos 60 puntos
        X = preparar_ventana_desde_bus(bus)
        prediccion = modelo.predecir(X)
    """)
