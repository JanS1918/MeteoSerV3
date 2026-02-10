"""
DETECTOR DE BIAS - Análisis de Sesgo Sistemático en Sensores
=============================================================
Detecta offset, deriva temporal y patrones de error en sensores.

Métodos:
1. Diferencia persistente (sensor - referencia)
2. Regresión lineal (pendiente ≠ 1 o intercepto ≠ 0)
3. Análisis temporal (deriva en el tiempo)
4. Comparación con vecinos (si hay estaciones cercanas)
"""

import numpy as np
from enum import Enum
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta
from collections import deque

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score, mean_absolute_error
except Exception:
    LinearRegression = None

    def r2_score(y_true, y_pred):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    def mean_absolute_error(y_true, y_pred):
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        return float(np.mean(np.abs(y_true - y_pred)))

    class _LinearRegressionFallback:
        def __init__(self):
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

    LinearRegression = _LinearRegressionFallback


class MetodoBias(Enum):
    """Métodos de detección de bias"""
    DIFERENCIA_MEDIA = "diferencia_media"  # Offset constante
    REGRESION_LINEAL = "regresion_lineal"  # Pendiente/intercepto
    DERIVA_TEMPORAL = "deriva_temporal"    # Cambio en el tiempo
    COMPARACION_VECINOS = "comparacion_vecinos"  # vs otras estaciones


class DetectorBias:
    """Detecta bias sistemático en sensores"""
    
    def __init__(self, ventana_historico: int = 1008):  # 7 días * 24h * 6 (cada 10 min)
        """
        Args:
            ventana_historico: Muestras a considerar (default 7 días)
        """
        self.ventana = ventana_historico
        self.historicos: Dict[str, deque] = {}
    
    def agregar_muestra(self, sensor: str, valor_sensor: float, 
                       valor_referencia: Optional[float] = None,
                       timestamp: Optional[datetime] = None):
        """
        Agrega muestra para análisis futuro
        
        Args:
            sensor: Nombre del sensor
            valor_sensor: Valor medido
            valor_referencia: Valor "verdadero" (si disponible)
            timestamp: Momento de lectura
        """
        if sensor not in self.historicos:
            self.historicos[sensor] = deque(maxlen=self.ventana)
        
        if timestamp is None:
            timestamp = datetime.now()
        
        self.historicos[sensor].append({
            'sensor': valor_sensor,
            'referencia': valor_referencia,
            'timestamp': timestamp
        })
    
    def detectar_offset(self, sensor: str, umbral: float = 0.5) -> Tuple[bool, float, str]:
        """
        Detecta offset constante (Método 1: DIFERENCIA_MEDIA)
        
        Args:
            sensor: Nombre del sensor
            umbral: Diferencia mínima para considerar bias
        
        Returns:
            (hay_bias, offset, descripcion)
        """
        if sensor not in self.historicos or len(self.historicos[sensor]) < 50:
            return False, 0.0, "Insuficiente data"
        
        datos = list(self.historicos[sensor])
        
        # Solo considerar muestras con referencia
        pares = [(d['sensor'], d['referencia']) for d in datos 
                 if d['referencia'] is not None]
        
        if len(pares) < 50:
            return False, 0.0, "Insuficiente data con referencia"
        
        sensores = np.array([p[0] for p in pares])
        referencias = np.array([p[1] for p in pares])
        
        # Diferencia media
        diferencias = sensores - referencias
        offset_medio = np.mean(diferencias)
        desvio = np.std(diferencias)
        
        # ¿Es significativo?
        if abs(offset_medio) > umbral and desvio < abs(offset_medio) * 2:
            descripcion = f"Offset constante detectado: sensor lee {offset_medio:+.2f} respecto a referencia (σ={desvio:.2f})"
            return True, offset_medio, descripcion
        
        return False, 0.0, f"No hay offset significativo (diferencia={offset_medio:.2f}, σ={desvio:.2f})"
    
    def detectar_bias_regresion(self, sensor: str) -> Tuple[bool, Dict, str]:
        """
        Detecta bias mediante regresión lineal (Método 2: REGRESION_LINEAL)
        
        Si sensor perfecto: y = 1*x + 0
        Si hay bias: y = m*x + b (m≠1 o b≠0)
        
        Returns:
            (hay_bias, params, descripcion)
            params = {'pendiente': m, 'intercepto': b, 'r2': r2, 'mae': mae}
        """
        if sensor not in self.historicos or len(self.historicos[sensor]) < 100:
            return False, {}, "Insuficiente data"
        
        datos = list(self.historicos[sensor])
        pares = [(d['referencia'], d['sensor']) for d in datos 
                 if d['referencia'] is not None]
        
        if len(pares) < 100:
            return False, {}, "Insuficiente data con referencia"
        
        X = np.array([p[0] for p in pares]).reshape(-1, 1)  # Referencia
        y = np.array([p[1] for p in pares])  # Sensor
        
        # Regresión lineal
        modelo = LinearRegression()
        modelo.fit(X, y)
        
        pendiente = modelo.coef_[0]
        intercepto = modelo.intercept_
        
        y_pred = modelo.predict(X)
        r2 = r2_score(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        
        params = {
            'pendiente': pendiente,
            'intercepto': intercepto,
            'r2': r2,
            'mae': mae,
            'modelo': modelo
        }
        
        # Detectar bias
        hay_bias = False
        descripcion_partes = []
        
        # Pendiente significativamente distinta de 1
        if abs(pendiente - 1.0) > 0.05:
            hay_bias = True
            if pendiente > 1.0:
                descripcion_partes.append(f"sensor sobreestima {(pendiente-1)*100:.1f}%")
            else:
                descripcion_partes.append(f"sensor subestima {(1-pendiente)*100:.1f}%")
        
        # Intercepto significativo
        if abs(intercepto) > 0.3:
            hay_bias = True
            descripcion_partes.append(f"offset de {intercepto:+.2f}")
        
        if hay_bias:
            desc = f"Bias lineal detectado: {', '.join(descripcion_partes)} (R²={r2:.3f}, MAE={mae:.2f})"
        else:
            desc = f"Sensor bien calibrado: y = {pendiente:.3f}x + {intercepto:.3f} (R²={r2:.3f})"
        
        return hay_bias, params, desc
    
    def detectar_deriva_temporal(self, sensor: str, ventana_dias: int = 7) -> Tuple[bool, float, str]:
        """
        Detecta deriva temporal (Método 3: DERIVA_TEMPORAL)
        
        Compara primeros N días vs últimos N días.
        Si hay diferencia sistemática → deriva temporal.
        
        Returns:
            (hay_deriva, tasa_deriva_por_dia, descripcion)
        """
        if sensor not in self.historicos or len(self.historicos[sensor]) < 200:
            return False, 0.0, "Insuficiente data"
        
        datos = list(self.historicos[sensor])
        
        # Solo con referencia
        pares = [(d['timestamp'], d['sensor'], d['referencia']) 
                 for d in datos if d['referencia'] is not None]
        
        if len(pares) < 200:
            return False, 0.0, "Insuficiente data con referencia"
        
        # Ordenar por tiempo
        pares.sort(key=lambda x: x[0])
        
        # Dividir en dos mitades temporales
        mitad = len(pares) // 2
        primera_mitad = pares[:mitad]
        segunda_mitad = pares[mitad:]
        
        # Calcular offset promedio de cada mitad
        offset_inicial = np.mean([s - r for t, s, r in primera_mitad])
        offset_final = np.mean([s - r for t, s, r in segunda_mitad])
        
        # Tiempo transcurrido
        t_inicial = primera_mitad[0][0]
        t_final = segunda_mitad[-1][0]
        dias = (t_final - t_inicial).total_seconds() / 86400
        
        # Tasa de deriva
        deriva_total = offset_final - offset_inicial
        deriva_por_dia = deriva_total / dias if dias > 0 else 0.0
        
        # ¿Es significativa?
        if abs(deriva_total) > 0.5 and abs(deriva_por_dia) > 0.05:
            desc = f"Deriva temporal detectada: {deriva_por_dia:+.3f} por día (total {deriva_total:+.2f} en {dias:.1f} días)"
            return True, deriva_por_dia, desc
        
        return False, deriva_por_dia, f"No hay deriva significativa ({deriva_por_dia:+.3f}/día)"
    
    def generar_reporte(self, sensor: str) -> Dict:
        """
        Genera reporte completo de bias para un sensor
        
        Returns:
            Dict con todos los análisis
        """
        reporte = {
            'sensor': sensor,
            'timestamp': datetime.now().isoformat(),
            'muestras': len(self.historicos.get(sensor, [])),
            'metodos': {}
        }
        
        if sensor not in self.historicos:
            reporte['error'] = "Sensor sin histórico"
            return reporte
        
        # Método 1: Offset
        hay_offset, offset, desc_offset = self.detectar_offset(sensor)
        reporte['metodos']['offset'] = {
            'detectado': hay_offset,
            'valor': offset,
            'descripcion': desc_offset
        }
        
        # Método 2: Regresión
        hay_regresion, params, desc_regresion = self.detectar_bias_regresion(sensor)
        reporte['metodos']['regresion'] = {
            'detectado': hay_regresion,
            'parametros': {k: v for k, v in params.items() if k != 'modelo'},
            'descripcion': desc_regresion
        }
        
        # Método 3: Deriva
        hay_deriva, tasa, desc_deriva = self.detectar_deriva_temporal(sensor)
        reporte['metodos']['deriva'] = {
            'detectado': hay_deriva,
            'tasa_por_dia': tasa,
            'descripcion': desc_deriva
        }
        
        # Conclusión general
        detectados = sum([hay_offset, hay_regresion, hay_deriva])
        if detectados >= 2:
            reporte['conclusion'] = "REQUIERE CALIBRACIÓN URGENTE"
        elif detectados == 1:
            reporte['conclusion'] = "Calibración recomendada"
        else:
            reporte['conclusion'] = "Sensor bien calibrado"
        
        return reporte


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║             DETECTOR DE BIAS - Análisis de Sensores          ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Ejemplo de uso:
    
        from core.calibration import DetectorBias
        
        detector = DetectorBias(ventana_historico=1008)  # 7 días
        
        # Agregar muestras (sensor vs referencia confiable)
        for i in range(1000):
            detector.agregar_muestra(
                "temperatura",
                valor_sensor=25.5 + bias,  # Sensor con bias
                valor_referencia=25.0      # Valor verdadero
            )
        
        # Analizar
        hay_bias, offset, desc = detector.detectar_offset("temperatura")
        print(f"Offset: {desc}")
        
        hay_bias, params, desc = detector.detectar_bias_regresion("temperatura")
        print(f"Regresión: {desc}")
        
        # Reporte completo
        reporte = detector.generar_reporte("temperatura")
        print(reporte['conclusion'])
    """)
