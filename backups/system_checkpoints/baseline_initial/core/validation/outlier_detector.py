"""
Detección de Outliers - Identifica lecturas anómalas de sensores.

Usa métodos estadísticos (IQR, Z-score, persistencia) para detectar
sensores pegados, ruidosos o fallando.
"""
import logging
from typing import Dict, List, Tuple, Optional
from collections import deque
import statistics
import numpy as np

logger = logging.getLogger(__name__)


class DetectorOutliers:
    """Detector de outliers con historial por sensor."""
    
    def __init__(self, historial_max: int = 100, iqr_multiplicador: float = 1.5):
        """
        Args:
            historial_max: Máximo de muestras a guardar por sensor
            iqr_multiplicador: Multiplicador para límites IQR (típico: 1.5)
        """
        self.historial = {}  # sensor -> deque de valores
        self.historial_max = historial_max
        self.iqr_mult = iqr_multiplicador
        self.alertas = {}  # Alertas acumuladas por sensor
    
    def agregar_muestra(self, sensor: str, valor: float) -> None:
        """Agrega valor al historial de un sensor."""
        if sensor not in self.historial:
            self.historial[sensor] = deque(maxlen=self.historial_max)
        
        self.historial[sensor].append(valor)
    
    def obtener_historial(self, sensor: str) -> List[float]:
        """Retorna historial del sensor."""
        if sensor not in self.historial:
            return []
        return list(self.historial[sensor])
    
    def detectar_iqr(self, sensor: str, valor: float) -> Tuple[bool, str]:
        """
        Detecta outliers usando método IQR (Interquartile Range).
        
        IQR es robusto a valores extremos.
        Límites: [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
        """
        historial = self.obtener_historial(sensor)
        
        if len(historial) < 4:  # Necesita al menos 4 valores
            return False, "Insuficiente historial"
        
        try:
            q1 = np.percentile(historial, 25)
            q3 = np.percentile(historial, 75)
            iqr = q3 - q1
            
            limite_bajo = q1 - self.iqr_mult * iqr
            limite_alto = q3 + self.iqr_mult * iqr
            
            if valor < limite_bajo or valor > limite_alto:
                fuera = "bajo" if valor < limite_bajo else "alto"
                return True, f"Outlier IQR ({fuera}): {valor:.2f} ∉ [{limite_bajo:.2f}, {limite_alto:.2f}]"
            
            return False, "OK"
        
        except Exception as e:
            logger.warning(f"Error en IQR para {sensor}: {e}")
            return False, "Error IQR"
    
    def detectar_zscore(self, sensor: str, valor: float) -> Tuple[bool, str]:
        """
        Detecta outliers usando Z-score.
        
        Z-score = (x - media) / desv.std
        Típicamente: |Z| > 3 es outlier
        """
        historial = self.obtener_historial(sensor)
        
        if len(historial) < 2:
            return False, "Insuficiente historial"
        
        try:
            media = statistics.mean(historial)
            desv = statistics.stdev(historial)
            
            if desv == 0:
                # Sin variación, cualquier cambio es outlier
                if valor != historial[-1]:
                    return True, f"Z-score: Salto discreto {historial[-1]:.2f} -> {valor:.2f}"
                return False, "Sin variación"
            
            z = abs((valor - media) / desv)
            
            if z > 3:
                return True, f"Outlier Z-score: |Z|={z:.2f} > 3"
            
            return False, "OK"
        
        except Exception as e:
            logger.warning(f"Error en Z-score para {sensor}: {e}")
            return False, "Error Z-score"
    
    def detectar_pegado(self, sensor: str, valor: float) -> Tuple[bool, str]:
        """
        Detecta si sensor está pegado (mismo valor repetido).
        
        Señal de falla: sensor no cambia en 5+ lecturas consecutivas.
        """
        historial = self.obtener_historial(sensor)
        
        if len(historial) < 5:
            return False, "Insuficiente historial"
        
        # Últimas 5 lecturas
        ultimas = historial[-5:]
        
        if all(v == valor for v in ultimas):
            return True, f"Sensor pegado: 5+ lecturas iguales a {valor:.2f}"
        
        return False, "OK"
    
    def detectar_ruido(self, sensor: str, valor: float) -> Tuple[bool, str]:
        """
        Detecta si sensor es muy ruidoso (varianza alta).
        
        Ruido excesivo: desv.std > media (coeficiente variación > 100%)
        """
        historial = self.obtener_historial(sensor)
        
        if len(historial) < 10:
            return False, "Insuficiente historial"
        
        try:
            media = statistics.mean(historial)
            desv = statistics.stdev(historial)
            
            if media == 0:
                return False, "Media cero"
            
            cv = (desv / abs(media)) * 100  # Coeficiente variación %
            
            if cv > 100:
                return True, f"Ruido excesivo: CV={cv:.1f}% (desv={desv:.2f}, media={media:.2f})"
            
            return False, f"Ruido normal (CV={cv:.1f}%)"
        
        except Exception as e:
            logger.warning(f"Error en ruido para {sensor}: {e}")
            return False, "Error ruido"
    
    def detectar(self, sensor: str, valor: float) -> Tuple[bool, str]:
        """
        Ejecuta todos los detectores y retorna si hay outlier.
        
        Prioridad:
        1. Sensor pegado (falla mecánica)
        2. IQR (robusto, preferido)
        3. Z-score (sensible a distribución)
        4. Ruido (advertencia, no bloquea)
        
        Returns:
            (es_outlier, razon)
        """
        # Agregar muestra al historial
        self.agregar_muestra(sensor, valor)
        
        # 1. Pegado (más importante)
        es_pegado, msg_pegado = self.detectar_pegado(sensor, valor)
        if es_pegado:
            self._registrar_alerta(sensor, msg_pegado)
            return True, msg_pegado
        
        # 2. IQR (robusto)
        es_outlier_iqr, msg_iqr = self.detectar_iqr(sensor, valor)
        if es_outlier_iqr:
            self._registrar_alerta(sensor, msg_iqr)
            return True, msg_iqr
        
        # 3. Z-score (sensible)
        es_outlier_z, msg_z = self.detectar_zscore(sensor, valor)
        if es_outlier_z and "Salto discreto" in msg_z:
            self._registrar_alerta(sensor, msg_z)
            return True, msg_z
        
        # 4. Ruido (solo advertencia)
        es_ruidoso, msg_ruido = self.detectar_ruido(sensor, valor)
        if es_ruidoso and "excesivo" in msg_ruido:
            logger.warning(f"⚠️ {sensor}: {msg_ruido}")
        
        return False, "OK"
    
    def _registrar_alerta(self, sensor: str, razon: str) -> None:
        """Registra alerta para un sensor."""
        if sensor not in self.alertas:
            self.alertas[sensor] = []
        
        self.alertas[sensor].append({
            "razon": razon,
            "timestamp": __import__('time').time(),
        })
        
        # Limitar a últimas 100 alertas por sensor
        if len(self.alertas[sensor]) > 100:
            self.alertas[sensor] = self.alertas[sensor][-100:]
        
        logger.warning(f"🚨 OUTLIER DETECTADO: {sensor} - {razon}")
    
    def obtener_estadisticas(self, sensor: str) -> Dict:
        """Retorna estadísticas de un sensor."""
        historial = self.obtener_historial(sensor)
        
        if not historial:
            return {"sin_datos": True}
        
        return {
            "muestras": len(historial),
            "media": statistics.mean(historial),
            "mediana": statistics.median(historial),
            "desv_std": statistics.stdev(historial) if len(historial) > 1 else 0,
            "minimo": min(historial),
            "maximo": max(historial),
            "rango": max(historial) - min(historial),
            "alertas": len(self.alertas.get(sensor, [])),
        }
    
    def limpiar_historial(self, sensor: str) -> None:
        """Limpia historial de un sensor."""
        if sensor in self.historial:
            self.historial[sensor].clear()
        if sensor in self.alertas:
            self.alertas[sensor].clear()


if __name__ == "__main__":
    # Test
    print("╔════════════════════════════════════════════╗")
    print("║   Test DetectorOutliers                    ║")
    print("╚════════════════════════════════════════════╝\n")
    
    detector = DetectorOutliers(historial_max=50, iqr_multiplicador=1.5)
    
    # Agregar datos normales
    print("1️⃣  Agregando datos normales (20 ± 2°C)")
    for i in range(20):
        valor = 20 + np.random.normal(0, 1)
        es_outlier, msg = detector.detectar("temperatura", valor)
        if es_outlier:
            print(f"  ⚠️ {valor:.2f}: {msg}")
    
    # Outlier obvio
    print("\n2️⃣  Agregando outlier (valor extremo: 50°C)")
    es_outlier, msg = detector.detectar("temperatura", 50.0)
    print(f"  Detectado: {es_outlier} - {msg}")
    
    # Sensor pegado
    print("\n3️⃣  Simulando sensor pegado (5 x 25.0°C)")
    for _ in range(5):
        es_outlier, msg = detector.detectar("temperatura", 25.0)
        if es_outlier:
            print(f"  Detectado: {msg}")
            break
    
    # Estadísticas
    print("\n📊 Estadísticas temperatura:")
    stats = detector.obtener_estadisticas("temperatura")
    for k, v in stats.items():
        print(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")
