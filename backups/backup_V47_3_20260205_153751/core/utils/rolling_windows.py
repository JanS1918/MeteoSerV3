# -*- coding: utf-8 -*-
"""
rolling_windows.py

Sistema de Ventanas Deslizantes Vectorizadas V45.0
=================================================
Ventanas rolling de 60 registros con álgebra lineal para tendencias.

OBJETIVO:
- Eliminar ruido de sensores con promedios móviles
- Calcular derivadas/tendencias con regresión lineal vectorizada
- Detectar patrones físicos (bajada de presión → tormenta)

GANANCIA:
- Precisión: tendencias robustas vs. restas simples ruidosas
- Performance: numpy vectorizado 100x más rápido que bucles

Referencias:
- Savitzky-Golay filter para suavizado de señales
- Least-squares regression para tendencias
"""

from __future__ import annotations

import math
from collections import deque
from typing import Dict, Optional

import numpy as np


class RollingWindow:
    """Ventana deslizante vectorizada con cálculo de tendencias."""
    
    def __init__(self, window_size: int = 60, min_samples: int = 10):
        """
        Inicializa ventana rolling.
        
        Args:
            window_size: Tamaño de la ventana (default: 60 registros)
            min_samples: Mínimo de muestras para cálculos válidos
        """
        self.window_size = window_size
        self.min_samples = min_samples
        self._data = deque(maxlen=window_size)
        self._timestamps = deque(maxlen=window_size)
    
    def add(self, value: float, timestamp: float = None) -> None:
        """Añade un nuevo valor a la ventana."""
        self._data.append(value)
        if timestamp is not None:
            self._timestamps.append(timestamp)
    
    def get_array(self) -> Optional[np.ndarray]:
        """Retorna array numpy de los datos actuales."""
        if len(self._data) < self.min_samples:
            return None
        return np.array(self._data, dtype=np.float64)
    
    def mean(self) -> Optional[float]:
        """Media de la ventana."""
        arr = self.get_array()
        if arr is None:
            return None
        return float(np.mean(arr))
    
    def std(self) -> Optional[float]:
        """Desviación estándar de la ventana."""
        arr = self.get_array()
        if arr is None:
            return None
        return float(np.std(arr))
    
    def trend_linear(self) -> Optional[float]:
        """
        Tendencia lineal (pendiente) usando regresión de mínimos cuadrados.
        
        Returns:
            Pendiente (unidades por step). None si no hay suficientes datos.
        """
        arr = self.get_array()
        if arr is None:
            return None
        
        n = len(arr)
        x = np.arange(n, dtype=np.float64)
        
        # Regresión lineal vectorizada: y = mx + b
        # m = (n·Σxy - Σx·Σy) / (n·Σx² - (Σx)²)
        sum_x = np.sum(x)
        sum_y = np.sum(arr)
        sum_xy = np.sum(x * arr)
        sum_x2 = np.sum(x * x)
        
        denom = n * sum_x2 - sum_x * sum_x
        if abs(denom) < 1e-12:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denom
        return float(slope)
    
    def trend_per_hour(self, dt_seconds: float = 60.0) -> Optional[float]:
        """
        Tendencia por hora.
        
        Args:
            dt_seconds: Intervalo entre registros (default: 60s)
        
        Returns:
            Cambio por hora (unidades/h)
        """
        slope = self.trend_linear()
        if slope is None:
            return None
        
        # Convertir pendiente (unidades/step) a unidades/hora
        steps_per_hour = 3600.0 / dt_seconds
        return slope * steps_per_hour
    
    def savitzky_golay(self, window_length: int = 11, polyorder: int = 2) -> Optional[float]:
        """
        Filtro Savitzky-Golay para suavizado preservando extremos.
        
        Args:
            window_length: Tamaño de ventana del filtro (impar)
            polyorder: Orden del polinomio
        
        Returns:
            Valor suavizado más reciente
        """
        arr = self.get_array()
        if arr is None or len(arr) < window_length:
            return None
        
        # Asegurar ventana impar
        if window_length % 2 == 0:
            window_length += 1
        
        # Simplificación: promedio ponderado con pesos gaussianos
        # (Savitzky-Golay completo requiere scipy; esto es operacional)
        half_window = window_length // 2
        weights = np.exp(-0.5 * (np.arange(-half_window, half_window + 1) ** 2) / (half_window / 3) ** 2)
        weights /= np.sum(weights)
        
        smoothed = np.convolve(arr, weights, mode='same')
        return float(smoothed[-1])
    
    def percentile(self, p: float) -> Optional[float]:
        """Percentil p de la ventana."""
        arr = self.get_array()
        if arr is None:
            return None
        return float(np.percentile(arr, p))
    
    def is_outlier_current(self, n_sigma: float = 3.0) -> bool:
        """
        Detecta si el valor más reciente es outlier.
        
        Args:
            n_sigma: Número de desviaciones estándar
        
        Returns:
            True si el último valor es outlier
        """
        arr = self.get_array()
        if arr is None or len(arr) < 2:
            return False
        
        current = arr[-1]
        mean = np.mean(arr[:-1])
        std = np.std(arr[:-1])
        
        if std < 1e-6:
            return False
        
        z_score = abs(current - mean) / std
        return z_score > n_sigma


class RollingWindowManager:
    """
    Gestor de múltiples ventanas rolling para variables meteorológicas.
    
    Mantiene ventanas para:
    - Presión barométrica
    - Humedad relativa
    - Velocidad del viento
    - Temperatura
    - Radiación
    """
    
    def __init__(self, window_size: int = 60, dt_seconds: float = 60.0):
        """
        Inicializa gestor de ventanas.
        
        Args:
            window_size: Tamaño de ventanas
            dt_seconds: Intervalo temporal entre registros (segundos)
        """
        self.window_size = window_size
        self.dt_seconds = dt_seconds
        
        self.presion = RollingWindow(window_size)
        self.humedad = RollingWindow(window_size)
        self.viento = RollingWindow(window_size)
        self.temperatura = RollingWindow(window_size)
        self.radiacion = RollingWindow(window_size)
    
    def update(self, data: Dict[str, float], timestamp: float = None) -> None:
        """
        Actualiza todas las ventanas con nuevos datos.
        
        Args:
            data: Diccionario con variables meteorológicas
            timestamp: Timestamp del registro
        """
        if "presion_barometrica" in data:
            # Convertir Pa a hPa para trabajar con valores razonables
            presion_hpa = data["presion_barometrica"] / 100.0
            self.presion.add(presion_hpa, timestamp)
        
        if "humedad" in data:
            self.humedad.add(data["humedad"], timestamp)
        
        if "velocidad_viento" in data:
            self.viento.add(data["velocidad_viento"], timestamp)
        
        if "temperatura" in data:
            self.temperatura.add(data["temperatura"], timestamp)
        
        if "radiacion" in data:
            self.radiacion.add(data["radiacion"], timestamp)
    
    def get_trends_report(self) -> Dict[str, Optional[float]]:
        """
        Genera reporte completo de tendencias horarias.
        
        Returns:
            Dict con tendencias por hora de cada variable
        """
        return {
            "presion_trend_hpa_h": self.presion.trend_per_hour(self.dt_seconds),
            "humedad_trend_pct_h": self.humedad.trend_per_hour(self.dt_seconds),
            "viento_trend_ms_h": self.viento.trend_per_hour(self.dt_seconds),
            "temperatura_trend_c_h": self.temperatura.trend_per_hour(self.dt_seconds),
            "radiacion_trend_wm2_h": self.radiacion.trend_per_hour(self.dt_seconds),
        }
    
    def detect_storm_pattern(self) -> Dict[str, bool]:
        """
        Detecta patrones de tormenta usando tendencias vectorizadas.
        
        Returns:
            Dict con flags de detección:
            - pressure_drop: Caída rápida de presión (> 3 hPa/h)
            - humidity_rise: Subida de humedad (> 10%/h)
            - wind_gust: Incremento de viento (> 5 m/s/h)
        """
        trends = self.get_trends_report()
        
        pressure_drop = False
        if trends["presion_trend_hpa_h"] is not None:
            pressure_drop = trends["presion_trend_hpa_h"] < -3.0
        
        humidity_rise = False
        if trends["humedad_trend_pct_h"] is not None:
            humidity_rise = trends["humedad_trend_pct_h"] > 10.0
        
        wind_gust = False
        if trends["viento_trend_ms_h"] is not None:
            wind_gust = trends["viento_trend_ms_h"] > 5.0
        
        return {
            "pressure_drop": pressure_drop,
            "humidity_rise": humidity_rise,
            "wind_gust": wind_gust,
            "storm_likely": pressure_drop and (humidity_rise or wind_gust),
        }
