"""
CALIBRADOR POR REGRESIÓN - Corrección Automática de Sensores
=============================================================
Aplica correcciones automáticas basadas en modelos de regresión.

Flujo:
1. Detecta bias con DetectorBias
2. Entrena modelo de corrección (LinearRegression)
3. Guarda modelo para aplicación en tiempo real
4. Publica valores corregidos al Bus
"""

import numpy as np
import pickle
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Callable
import json

try:
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import PolynomialFeatures
except Exception:
    LinearRegression = None
    Ridge = None
    PolynomialFeatures = None

    class _LinearRegressionFallback:
        def __init__(self, *args, **kwargs):
            self.coef_ = np.array([0.0])
            self.intercept_ = 0.0

        def fit(self, X, y):
            x = np.asarray(X).reshape(-1)
            y = np.asarray(y).reshape(-1)
            if x.size == 0:
                self.coef_ = np.array([0.0])
                self.intercept_ = 0.0
                return self
            m, b = np.polyfit(x, y, 1)
            self.coef_ = np.array([m])
            self.intercept_ = b
            return self

        def predict(self, X):
            x = np.asarray(X).reshape(-1)
            return self.coef_[0] * x + self.intercept_

    class _RidgeFallback(_LinearRegressionFallback):
        pass

    class _PolynomialFeaturesFallback:
        def __init__(self, degree=1):
            self.degree = max(1, int(degree))

        def fit_transform(self, X):
            return self.transform(X)

        def transform(self, X):
            x = np.asarray(X).reshape(-1)
            cols = [x ** i for i in range(self.degree + 1)]
            return np.vstack(cols).T

    LinearRegression = _LinearRegressionFallback
    Ridge = _RidgeFallback
    PolynomialFeatures = _PolynomialFeaturesFallback


class CalibradorRegresion:
    """Calibra sensores usando regresión lineal/polinomial"""
    
    def __init__(self, tipo: str = "lineal", grado: int = 1):
        """
        Args:
            tipo: "lineal", "ridge", o "polinomial"
            grado: Grado del polinomio (si tipo=polinomial)
        """
        self.tipo = tipo
        self.grado = grado
        self.modelo = None
        self.poly_features = None
        self.entrenado = False
        self.metadatos = {}
    
    def entrenar(self, X_sensor: np.ndarray, y_verdad: np.ndarray) -> Dict:
        """
        Entrena modelo de corrección
        
        Args:
            X_sensor: Valores del sensor (crudo)
            y_verdad: Valores verdaderos (referencia)
        
        Returns:
            Métricas del entrenamiento
        """
        X = X_sensor.reshape(-1, 1) if X_sensor.ndim == 1 else X_sensor
        y = y_verdad
        
        if self.tipo == "lineal":
            self.modelo = LinearRegression()
            X_train = X
        
        elif self.tipo == "ridge":
            self.modelo = Ridge(alpha=1.0)
            X_train = X
        
        elif self.tipo == "polinomial":
            self.poly_features = PolynomialFeatures(degree=self.grado)
            X_train = self.poly_features.fit_transform(X)
            self.modelo = LinearRegression()
        
        else:
            raise ValueError(f"Tipo desconocido: {self.tipo}")
        
        # Entrenar
        self.modelo.fit(X_train, y)
        self.entrenado = True
        
        # Calcular métricas
        y_pred = self.predecir(X_sensor)
        mae = np.mean(np.abs(y - y_pred))
        rmse = np.sqrt(np.mean((y - y_pred)**2))
        max_error = np.max(np.abs(y - y_pred))
        
        self.metadatos = {
            'tipo': self.tipo,
            'grado': self.grado,
            'n_muestras': len(X),
            'mae': float(mae),
            'rmse': float(rmse),
            'max_error': float(max_error),
            'fecha_entrenamiento': datetime.now().isoformat()
        }
        
        if hasattr(self.modelo, 'coef_'):
            self.metadatos['coeficientes'] = self.modelo.coef_.tolist()
        if hasattr(self.modelo, 'intercept_'):
            self.metadatos['intercepto'] = float(self.modelo.intercept_)
        
        return self.metadatos
    
    def predecir(self, X_sensor: np.ndarray) -> np.ndarray:
        """
        Aplica corrección a valores del sensor
        
        Args:
            X_sensor: Valores crudos del sensor
        
        Returns:
            Valores corregidos
        """
        if not self.entrenado:
            raise RuntimeError("Modelo no entrenado")
        
        X = X_sensor.reshape(-1, 1) if X_sensor.ndim == 1 else X_sensor
        
        if self.tipo == "polinomial":
            X = self.poly_features.transform(X)
        
        return self.modelo.predict(X)
    
    def corregir_valor(self, valor_sensor: float) -> float:
        """Corrige un valor individual"""
        if not self.entrenado:
            return valor_sensor
        
        return float(self.predecir(np.array([valor_sensor]))[0])
    
    def guardar(self, ruta: str):
        """Guarda modelo y metadatos"""
        if not self.entrenado:
            raise RuntimeError("Modelo no entrenado")
        
        ruta_path = Path(ruta)
        ruta_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar modelo
        with open(ruta_path.with_suffix('.pkl'), 'wb') as f:
            pickle.dump({
                'modelo': self.modelo,
                'poly_features': self.poly_features,
                'tipo': self.tipo,
                'grado': self.grado
            }, f)
        
        # Guardar metadatos
        with open(ruta_path.with_suffix('.json'), 'w') as f:
            json.dump(self.metadatos, f, indent=2)
    
    def cargar(self, ruta: str):
        """Carga modelo previamente guardado"""
        ruta_path = Path(ruta)
        
        # Cargar modelo
        with open(ruta_path.with_suffix('.pkl'), 'rb') as f:
            data = pickle.load(f)
        
        self.modelo = data['modelo']
        self.poly_features = data.get('poly_features')
        self.tipo = data['tipo']
        self.grado = data['grado']
        self.entrenado = True
        
        # Cargar metadatos
        with open(ruta_path.with_suffix('.json'), 'r') as f:
            self.metadatos = json.load(f)
    
    def obtener_formula(self) -> str:
        """Retorna fórmula de corrección en texto"""
        if not self.entrenado:
            return "Modelo no entrenado"
        
        if self.tipo in ["lineal", "ridge"]:
            m = self.modelo.coef_[0] if hasattr(self.modelo, 'coef_') else 1.0
            b = self.modelo.intercept_ if hasattr(self.modelo, 'intercept_') else 0.0
            return f"y_corregido = {m:.4f} * x_sensor + {b:+.4f}"
        
        elif self.tipo == "polinomial":
            coefs = self.modelo.coef_
            partes = []
            for i, c in enumerate(coefs):
                if abs(c) < 1e-6:
                    continue
                if i == 0:
                    partes.append(f"{c:.4f}")
                elif i == 1:
                    partes.append(f"{c:+.4f}*x")
                else:
                    partes.append(f"{c:+.4f}*x^{i}")
            return "y_corregido = " + " ".join(partes)
        
        return "Fórmula no disponible"


class ManagerCalibracion:
    """Gestiona calibraciones de múltiples sensores"""
    
    def __init__(self, bus=None):
        """
        Args:
            bus: BusCapasInformacion (opcional)
        """
        self.bus = bus
        self.calibradores: Dict[str, CalibradorRegresion] = {}
        self.activo: Dict[str, bool] = {}
    
    def entrenar_calibrador(self, sensor: str, X_sensor: np.ndarray, 
                           y_verdad: np.ndarray, tipo: str = "lineal") -> Dict:
        """
        Entrena calibrador para un sensor
        
        Args:
            sensor: Nombre del sensor
            X_sensor: Valores crudos históricos
            y_verdad: Valores verdaderos históricos
            tipo: "lineal", "ridge", o "polinomial"
        
        Returns:
            Métricas del entrenamiento
        """
        calibrador = CalibradorRegresion(tipo=tipo)
        metricas = calibrador.entrenar(X_sensor, y_verdad)
        
        self.calibradores[sensor] = calibrador
        self.activo[sensor] = False  # No activar automáticamente
        
        print(f"[OK] Calibrador '{sensor}' entrenado: MAE={metricas['mae']:.3f}, RMSE={metricas['rmse']:.3f}")
        print(f"   Fórmula: {calibrador.obtener_formula()}")
        
        return metricas
    
    def activar_calibrador(self, sensor: str):
        """Activa corrección automática para un sensor"""
        if sensor not in self.calibradores:
            raise ValueError(f"Sensor '{sensor}' sin calibrador")
        
        self.activo[sensor] = True
        print(f"[OK] Calibrador '{sensor}' ACTIVADO - aplicará correcciones automáticamente")
    
    def desactivar_calibrador(self, sensor: str):
        """Desactiva corrección para un sensor"""
        if sensor in self.activo:
            self.activo[sensor] = False
            print(f"⏸️  Calibrador '{sensor}' DESACTIVADO")
    
    def corregir_valor(self, sensor: str, valor_crudo: float) -> float:
        """
        Aplica corrección si está activa
        
        Args:
            sensor: Nombre del sensor
            valor_crudo: Valor sin corregir
        
        Returns:
            Valor corregido (o crudo si calibrador inactivo)
        """
        if sensor not in self.calibradores or not self.activo.get(sensor, False):
            return valor_crudo
        
        return self.calibradores[sensor].corregir_valor(valor_crudo)
    
    def publicar_al_bus(self, sensor: str, valor_crudo: float):
        """
        Publica valor corregido al Bus si está configurado
        
        Args:
            sensor: Nombre del sensor
            valor_crudo: Valor sin corregir
        """
        if self.bus is None:
            return
        
        valor_corregido = self.corregir_valor(sensor, valor_crudo)
        
        # Publicar crudo (INTERMEDIATE)
        self.bus.publicar(
            variable=f"sensores.{sensor}_raw",
            valor=valor_crudo,
            nivel="INTERMEDIATE",
            origen="core.calibration.ManagerCalibracion",
            notas="Valor crudo sin calibrar"
        )
        
        # Publicar corregido (CORE)
        if self.activo.get(sensor, False):
            self.bus.publicar(
                variable=f"sensores.{sensor}_calibrado",
                valor=valor_corregido,
                nivel="CORE",
                origen="core.calibration.ManagerCalibracion",
                confianza=0.98,
                notas=f"Valor calibrado automáticamente (Δ={valor_corregido-valor_crudo:+.2f})"
            )
    
    def guardar_todos(self, directorio: str = "data/calibration"):
        """Guarda todos los calibradores"""
        dir_path = Path(directorio)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        for sensor, calibrador in self.calibradores.items():
            ruta = dir_path / f"calibrador_{sensor}"
            calibrador.guardar(str(ruta))
            print(f"[GUARDAR] Calibrador '{sensor}' guardado en {ruta}")
    
    def cargar_todos(self, directorio: str = "data/calibration"):
        """Carga todos los calibradores encontrados"""
        dir_path = Path(directorio)
        
        if not dir_path.exists():
            print(f"[WARNING]  Directorio {directorio} no existe")
            return
        
        for archivo in dir_path.glob("calibrador_*.pkl"):
            sensor = archivo.stem.replace("calibrador_", "")
            calibrador = CalibradorRegresion()
            calibrador.cargar(str(archivo.with_suffix("")))
            
            self.calibradores[sensor] = calibrador
            self.activo[sensor] = False
            
            print(f"📂 Calibrador '{sensor}' cargado (MAE={calibrador.metadatos.get('mae', 'N/A')})")
    
    def generar_reporte(self) -> Dict:
        """Genera reporte de todos los calibradores"""
        return {
            'timestamp': datetime.now().isoformat(),
            'calibradores': {
                sensor: {
                    'activo': self.activo.get(sensor, False),
                    'tipo': cal.tipo,
                    'formula': cal.obtener_formula(),
                    'metadatos': cal.metadatos
                }
                for sensor, cal in self.calibradores.items()
            }
        }


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        CALIBRADOR POR REGRESIÓN - Corrección Automática      ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Ejemplo de uso:
    
        from core.calibration import CalibradorRegresion, ManagerCalibracion
        from core.bus import obtener_bus
        import numpy as np
        
        # Datos históricos (sensor vs verdad)
        X_sensor = np.array([20.5, 21.0, 21.5, 22.0, 22.5])  # Sensor con bias
        y_verdad = np.array([20.0, 20.5, 21.0, 21.5, 22.0])  # Valores reales
        
        # Entrenar
        bus = obtener_bus()
        manager = ManagerCalibracion(bus)
        
        metricas = manager.entrenar_calibrador("temperatura", X_sensor, y_verdad)
        print(f"MAE: {metricas['mae']:.3f}")
        
        # Activar corrección automática
        manager.activar_calibrador("temperatura")
        
        # Usar
        valor_crudo = 25.5
        valor_corregido = manager.corregir_valor("temperatura", valor_crudo)
        print(f"Crudo: {valor_crudo}, Corregido: {valor_corregido}")
        
        # Publicar al Bus
        manager.publicar_al_bus("temperatura", 25.5)
        
        # Guardar para uso futuro
        manager.guardar_todos()
    """)
