"""
AUTO-CALIBRACIÓN DE SENSORES - Sistema Integrado
================================================
Sistema que aprende offset/bias sistemático de sensores y aplica correcciones automáticas.

Objetivo: ±0.5°C → ±0.1°C (5x más preciso)

Integra:
- DetectorBias: Detección avanzada (offset, regresión, deriva temporal)
- CalibradorRegresion: Correcciones por ML
- AutoCalibrador: Orquestación automática

Uso:
    calibrador = obtener_auto_calibrador()
    calibrador.configurar_deteccion_automatica(intervalo_horas=6)
    calibrador.entrenar_desde_referencia("temperatura", sensor_vals, ref_vals)
    temp_corregida = calibrador.corregir_en_tiempo_real("temperatura", temp_raw)
"""

import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from collections import deque
from dataclasses import dataclass, asdict
import threading
import time

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn no disponible. Instalar con: pip install scikit-learn")

# Importar módulos de calibración avanzados
try:
    from .bias_detector import DetectorBias
    from .regression_calibrator import CalibradorRegresion, ManagerCalibracion
    MODULOS_AVANZADOS = True
except ImportError:
    MODULOS_AVANZADOS = False
    print("⚠️ Módulos avanzados (bias_detector, regression_calibrator) no disponibles")


@dataclass
class ModeloCalibr acion:
    """Modelo de calibración para un sensor"""
    sensor: str
    tipo: str  # "lineal", "offset"
    slope: float  # Pendiente (típicamente ~1.0)
    intercept: float  # Offset
    r2_score: float  # Bondad de ajuste
    mse: float  # Error cuadrático medio
    n_muestras: int
    fecha_entrenamiento: str
    activo: bool = True
    
    def aplicar(self, valor: float) -> float:
        """Aplica corrección al valor raw"""
        if self.tipo == "lineal":
            return self.slope * valor + self.intercept
        elif self.tipo == "offset":
            return valor + self.intercept
        return valor
    
    def a_dict(self) -> Dict:
        return asdict(self)


class DetectorBias:
    """Detecta bias sistemático en lecturas de sensores"""
    
    def __init__(self):
        self.historicos: Dict[str, deque] = {}
        self.ventana_maxima = 10080  # 7 días × 1440 min
    
    def agregar_muestra(self, sensor: str, valor: float, timestamp: datetime = None):
        """Registra una muestra del sensor"""
        if sensor not in self.historicos:
            self.historicos[sensor] = deque(maxlen=self.ventana_maxima)
        
        if timestamp is None:
            timestamp = datetime.now()
        
        self.historicos[sensor].append((valor, timestamp))
    
    def detectar_deriva_temporal(self, sensor: str) -> Tuple[bool, float]:
        """
        Detecta si el sensor está derivando con el tiempo
        
        Returns:
            (hay_deriva, tasa_deriva_por_dia)
        """
        if sensor not in self.historicos:
            return False, 0.0
        
        muestras = list(self.historicos[sensor])
        if len(muestras) < 100:
            return False, 0.0
        
        # Convertir a arrays
        valores = np.array([m[0] for m in muestras])
        timestamps = np.array([(m[1] - muestras[0][1]).total_seconds() for m in muestras])
        
        # Regresión lineal vs tiempo
        if SKLEARN_AVAILABLE:
            X = timestamps.reshape(-1, 1)
            modelo = LinearRegression()
            modelo.fit(X, valores)
            
            # Deriva en unidades/día
            deriva_por_segundo = modelo.coef_[0]
            deriva_por_dia = deriva_por_segundo * 86400
            
            # Considerar significativa si > 0.1 unidades/día
            hay_deriva = abs(deriva_por_dia) > 0.1
            
            return hay_deriva, deriva_por_dia
        
        return False, 0.0
    
    def detectar_offset_constante(self, sensor: str, referencia: List[float]) -> Tuple[bool, float]:
        """
        Detecta offset constante comparando con referencia
        
        Args:
            sensor: Nombre del sensor
            referencia: Valores de referencia (ej: sensor calibrado)
        
        Returns:
            (hay_offset, magnitud_offset)
        """
        if sensor not in self.historicos:
            return False, 0.0
        
        muestras = list(self.historicos[sensor])
        valores = [m[0] for m in muestras[-len(referencia):]]
        
        if len(valores) != len(referencia):
            return False, 0.0
        
        # Offset medio
        diferencias = np.array(valores) - np.array(referencia)
        offset_medio = np.mean(diferencias)
        desvio = np.std(diferencias)
        
        # Offset significativo si > 0.5 unidades y consistente (desvío bajo)
        hay_offset = abs(offset_medio) > 0.5 and desvio < 1.0
        
        return hay_offset, offset_medio


class AutoCalibrador:
    """Sistema de auto-calibración de sensores"""
    
    def __init__(self, bus=None):
        """
        Args:
            bus: BusCapasInformacion (opcional)
        """
        self.bus = bus
        self.modelos: Dict[str, ModeloCalibracion] = {}
        self.detector_bias = DetectorBias()
        self.ruta_modelos = Path("data/calibration")
        self.ruta_modelos.mkdir(parents=True, exist_ok=True)
    
    def entrenar_desde_bus(self, sensor: str, dias: int = 7) -> ModeloCalibracion:
        """
        Entrena modelo de calibración desde históricos del Bus
        
        Args:
            sensor: Nombre del sensor en TIMESERIES
            dias: Días de histórico a usar
        
        Returns:
            Modelo entrenado
        """
        if self.bus is None:
            raise ValueError("Bus no configurado")
        
        if sensor not in self.bus.capa_timeseries:
            raise ValueError(f"Sensor '{sensor}' sin histórico en Bus")
        
        ts = self.bus.capa_timeseries[sensor]
        cutoff = datetime.now() - timedelta(days=dias)
        
        # Obtener datos
        datos = [(v, t) for v, t in ts.valores if t >= cutoff]
        
        if len(datos) < 100:
            raise ValueError(f"Insuficientes datos: {len(datos)} < 100")
        
        valores = np.array([d[0] for d in datos])
        timestamps = np.array([(d[1] - datos[0][1]).total_seconds() / 3600 for d in datos])  # horas
        
        print(f"\n📊 Entrenando calibración para '{sensor}'")
        print(f"   Datos: {len(datos)} muestras de {dias} días")
        print(f"   Rango: [{valores.min():.2f}, {valores.max():.2f}]")
        
        # Detectar tipo de corrección necesaria
        desvio = np.std(valores)
        
        if desvio < 0.1:
            print(f"   ⚠️  Sensor muy estable (σ={desvio:.3f}), posible sensor pegado")
            return None
        
        # Regresión lineal vs tiempo (detectar deriva)
        if SKLEARN_AVAILABLE:
            X = timestamps.reshape(-1, 1)
            modelo_regresion = LinearRegression()
            modelo_regresion.fit(X, valores)
            
            # Predicciones
            valores_pred = modelo_regresion.predict(X)
            
            # Métricas
            r2 = r2_score(valores, valores_pred)
            mse = mean_squared_error(valores, valores_pred)
            
            # Deriva por día
            deriva_por_hora = modelo_regresion.coef_[0]
            deriva_por_dia = deriva_por_hora * 24
            
            print(f"   Deriva: {deriva_por_dia:.4f} unidades/día")
            print(f"   R²: {r2:.4f}, MSE: {mse:.4f}")
            
            # Decidir tipo de corrección
            if abs(deriva_por_dia) > 0.05:
                # Deriva significativa → modelo lineal
                tipo = "lineal"
                slope = 1.0 - deriva_por_hora * len(datos) / 2 / valores.mean()
                intercept = modelo_regresion.intercept_
                print(f"   ✅ Corrección LINEAL (deriva detectada)")
            else:
                # Solo offset constante
                tipo = "offset"
                slope = 1.0
                offset_medio = valores.mean() - np.median(valores)
                intercept = -offset_medio if abs(offset_medio) > 0.1 else 0.0
                print(f"   ✅ Corrección OFFSET ({intercept:+.3f})")
            
            # Crear modelo
            modelo_calibracion = ModeloCalibracion(
                sensor=sensor,
                tipo=tipo,
                slope=slope,
                intercept=intercept,
                r2_score=r2,
                mse=mse,
                n_muestras=len(datos),
                fecha_entrenamiento=datetime.now().isoformat(),
                activo=True
            )
            
            self.modelos[sensor] = modelo_calibracion
            self.guardar_modelo(sensor)
            
            return modelo_calibracion
        
        else:
            print("   ❌ scikit-learn no disponible, no se puede entrenar")
            return None
    
    def aplicar_correccion(self, sensor: str, valor: float) -> Tuple[float, bool]:
        """
        Aplica corrección a un valor raw
        
        Args:
            sensor: Nombre del sensor
            valor: Valor raw
        
        Returns:
            (valor_corregido, fue_corregido)
        """
        if sensor not in self.modelos:
            return valor, False
        
        modelo = self.modelos[sensor]
        if not modelo.activo:
            return valor, False
        
        valor_corregido = modelo.aplicar(valor)
        return valor_corregido, True
    
    def publicar_correccion_al_bus(self, sensor: str, valor_raw: float):
        """Aplica corrección y publica ambos valores al Bus"""
        if self.bus is None:
            return
        
        valor_corregido, fue_corregido = self.aplicar_correccion(sensor, valor_raw)
        
        # Publicar raw (INTERMEDIATE)
        self.bus.publicar(
            variable=f"sensores.{sensor}_raw",
            valor=valor_raw,
            nivel="INTERMEDIATE",
            origen="core.calibration.AutoCalibrador",
            confianza=0.8,
            notas="Valor sin calibrar"
        )
        
        # Publicar corregido (CORE)
        if fue_corregido:
            modelo = self.modelos[sensor]
            self.bus.publicar(
                variable=f"sensores.{sensor}_calibrado",
                valor=valor_corregido,
                nivel="CORE",
                origen="core.calibration.AutoCalibrador",
                confianza=0.95,
                notas=f"Auto-calibrado ({modelo.tipo})"
            )
        else:
            self.bus.publicar(
                variable=f"sensores.{sensor}_calibrado",
                valor=valor_raw,
                nivel="CORE",
                origen="core.calibration.AutoCalibrador",
                confianza=0.85,
                notas="Sin calibración aplicada"
            )
    
    def guardar_modelo(self, sensor: str):
        """Guarda modelo de calibración a disco"""
        if sensor not in self.modelos:
            return
        
        ruta = self.ruta_modelos / f"{sensor}_calibration.json"
        with open(ruta, 'w') as f:
            json.dump(self.modelos[sensor].a_dict(), f, indent=2)
        
        print(f"   💾 Modelo guardado: {ruta}")
    
    def cargar_modelo(self, sensor: str) -> bool:
        """Carga modelo previamente guardado"""
        ruta = self.ruta_modelos / f"{sensor}_calibration.json"
        
        if not ruta.exists():
            return False
        
        with open(ruta, 'r') as f:
            datos = json.load(f)
        
        self.modelos[sensor] = ModeloCalibracion(**datos)
        print(f"   ✅ Modelo cargado: {sensor} ({self.modelos[sensor].tipo})")
        return True
    
    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas de calibración"""
        return {
            'sensores_calibrados': len(self.modelos),
            'modelos': [
                {
                    'sensor': m.sensor,
                    'tipo': m.tipo,
                    'intercept': m.intercept,
                    'r2': m.r2_score,
                    'activo': m.activo
                }
                for m in self.modelos.values()
            ]
        }


# Singleton global
_auto_calibrador_global = None


def obtener_auto_calibrador(bus=None):
    """Obtiene o crea auto-calibrador global"""
    global _auto_calibrador_global
    
    if _auto_calibrador_global is None:
        if bus is None:
            from core.bus import obtener_bus
            bus = obtener_bus()
        
        _auto_calibrador_global = AutoCalibrador(bus)
    
    return _auto_calibrador_global


class OrquestadorCalibracion:
    """
    Orquestador que integra DetectorBias + CalibradorRegresion + AutoCalibrador
    Automatiza completamente el proceso de calibración
    """
    
    def __init__(self, bus=None):
        self.bus = bus
        
        # Componentes
        if MODULOS_AVANZADOS:
            self.detector = DetectorBias(ventana_historico=1008)  # 7 días @ 10min
            self.manager_calibracion = ManagerCalibracion(bus)
        else:
            self.detector = None
            self.manager_calibracion = None
        
        self.auto_calibrador = obtener_auto_calibrador(bus)
        
        # Control de hilos
        self.hilo_deteccion = None
        self.deteccion_activa = False
        self.intervalo_deteccion_segundos = 3600 * 6  # 6 horas
    
    def entrenar_desde_referencias(self, sensor: str, 
                                    valores_sensor: np.ndarray, 
                                    valores_referencia: np.ndarray,
                                    tipo_modelo: str = "lineal") -> Dict:
        """
        Entrena calibración completa desde datos históricos
        
        Args:
            sensor: Nombre del sensor
            valores_sensor: Array de valores crudos del sensor
            valores_referencia: Array de valores verdaderos (ground truth)
            tipo_modelo: "lineal", "ridge", o "polinomial"
        
        Returns:
            Reporte completo con métricas
        """
        if not MODULOS_AVANZADOS:
            print("⚠️ Módulos avanzados no disponibles - usando calibración básica")
            return {}
        
        # 1. Agregar muestras al detector de bias
        for val_sensor, val_ref in zip(valores_sensor, valores_referencia):
            self.detector.agregar_muestra(sensor, val_sensor, val_ref, datetime.now())
        
        # 2. Generar reporte de detección
        reporte_bias = self.detector.generar_reporte(sensor)
        print(f"\n📊 REPORTE DE DETECCIÓN - {sensor}:")
        print(f"   Offset: {reporte_bias['offset_detectado']}")
        print(f"   Regresión: {reporte_bias['bias_regresion']}")
        print(f"   Deriva temporal: {reporte_bias['deriva_temporal']}")
        print(f"   CONCLUSIÓN: {reporte_bias['conclusion']}")
        
        # 3. Entrenar calibrador por regresión
        metricas = self.manager_calibracion.entrenar_calibrador(
            sensor, valores_sensor, valores_referencia, tipo=tipo_modelo
        )
        
        # 4. Auto-activar si la mejora es significativa
        if metricas['mae'] < 0.3:  # MAE < 0.3 es excelente
            self.manager_calibracion.activar_calibrador(sensor)
            print(f"✅ Calibrador '{sensor}' ACTIVADO (MAE={metricas['mae']:.3f} < 0.3)")
        else:
            print(f"⚠️  Calibrador '{sensor}' entrenado pero NO activado (MAE={metricas['mae']:.3f} > 0.3)")
        
        return {
            'reporte_bias': reporte_bias,
            'metricas_calibracion': metricas,
            'auto_activado': metricas['mae'] < 0.3
        }
    
    def iniciar_deteccion_automatica(self, intervalo_horas: int = 6):
        """
        Inicia hilo de detección automática de bias
        
        Args:
            intervalo_horas: Cada cuántas horas revisar
        """
        if not MODULOS_AVANZADOS:
            print("⚠️ Módulos avanzados no disponibles")
            return
        
        self.intervalo_deteccion_segundos = intervalo_horas * 3600
        self.deteccion_activa = True
        
        self.hilo_deteccion = threading.Thread(
            target=self._bucle_deteccion_automatica,
            daemon=True,
            name="AutoDeteccionBias"
        )
        self.hilo_deteccion.start()
        
        print(f"🤖 Detección automática INICIADA (cada {intervalo_horas}h)")
    
    def _bucle_deteccion_automatica(self):
        """Bucle que ejecuta detección periódica"""
        while self.deteccion_activa:
            try:
                # Esperar intervalo
                time.sleep(self.intervalo_deteccion_segundos)
                
                # Revisar cada sensor
                for sensor in self.detector.historicos.keys():
                    reporte = self.detector.generar_reporte(sensor)
                    
                    # Si requiere calibración urgente
                    if "URGENTE" in reporte['conclusion']:
                        print(f"\n🚨 ALERTA: Sensor '{sensor}' requiere calibración")
                        print(f"   {reporte['conclusion']}")
                        
                        # Publicar alerta al Bus si está disponible
                        if self.bus:
                            self.bus.publicar(
                                variable=f"alertas.calibracion.{sensor}",
                                valor=reporte,
                                nivel="CORE",
                                origen="OrquestadorCalibracion",
                                confianza=0.95,
                                notas="Alerta de calibración automática"
                            )
            
            except Exception as e:
                print(f"❌ Error en bucle de detección: {e}")
                time.sleep(60)  # Esperar 1 min antes de reintentar
    
    def detener_deteccion_automatica(self):
        """Detiene el hilo de detección"""
        self.deteccion_activa = False
        if self.hilo_deteccion:
            self.hilo_deteccion.join(timeout=5)
        print("⏹️  Detección automática DETENIDA")
    
    def corregir_en_tiempo_real(self, sensor: str, valor_crudo: float) -> float:
        """
        Aplica corrección en tiempo real (con fallback)
        
        Prioridad:
        1. ManagerCalibracion (regresión avanzada)
        2. AutoCalibrador (básico)
        
        Args:
            sensor: Nombre del sensor
            valor_crudo: Valor sin corregir
        
        Returns:
            Valor corregido
        """
        # Intentar con ManagerCalibracion (avanzado)
        if self.manager_calibracion and sensor in self.manager_calibracion.calibradores:
            return self.manager_calibracion.corregir_valor(sensor, valor_crudo)
        
        # Fallback a AutoCalibrador (básico)
        return self.auto_calibrador.aplicar_correccion(sensor, valor_crudo)
    
    def guardar_todo(self, directorio: str = "data/calibration"):
        """Guarda todos los calibradores y configuración"""
        if self.manager_calibracion:
            self.manager_calibracion.guardar_todos(directorio)
        
        self.auto_calibrador.guardar_modelos(directorio)
        
        print(f"💾 Todos los calibradores guardados en {directorio}")
    
    def cargar_todo(self, directorio: str = "data/calibration"):
        """Carga todos los calibradores guardados"""
        if self.manager_calibracion:
            self.manager_calibracion.cargar_todos(directorio)
        
        self.auto_calibrador.cargar_modelos(directorio)
        
        print(f"📂 Calibradores cargados desde {directorio}")
    
    def generar_reporte_completo(self) -> Dict:
        """Genera reporte de todos los sensores"""
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'calibradores_avanzados': None,
            'calibradores_basicos': None
        }
        
        if self.manager_calibracion:
            reporte['calibradores_avanzados'] = self.manager_calibracion.generar_reporte()
        
        reporte['calibradores_basicos'] = self.auto_calibrador.generar_reporte()
        
        return reporte


# Singleton global del orquestador
_orquestador_global = None

def obtener_orquestador_calibracion(bus=None) -> OrquestadorCalibracion:
    """
    Obtiene instancia global del orquestador de calibración
    
    Args:
        bus: BusCapasInformacion (opcional)
    
    Returns:
        OrquestadorCalibracion singleton
    """
    global _orquestador_global
    
    if _orquestador_global is None:
        _orquestador_global = OrquestadorCalibracion(bus)
    
    return _orquestador_global


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║         AUTO-CALIBRACIÓN - Sistema Integrado                 ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    Ejemplo COMPLETO:
    
        from core.bus import obtener_bus
        from core.calibration import obtener_orquestador_calibracion
        import numpy as np
        
        # 1. Obtener orquestador
        bus = obtener_bus()
        orquestador = obtener_orquestador_calibracion(bus)
        
        # 2. Datos históricos (sensor vs verdad)
        sensor_vals = np.array([20.5, 21.1, 21.7, 22.3, 22.9])
        ref_vals = np.array([20.0, 20.5, 21.0, 21.5, 22.0])
        
        # 3. Entrenar calibración
        reporte = orquestador.entrenar_desde_referencias(
            "temperatura", sensor_vals, ref_vals, tipo_modelo="lineal"
        )
        print(f"MAE: {reporte['metricas_calibracion']['mae']:.3f}")
        
        # 4. Iniciar detección automática (cada 6h)
        orquestador.iniciar_deteccion_automatica(intervalo_horas=6)
        
        # 5. Usar en tiempo real
        temp_cruda = 25.5
        temp_corregida = orquestador.corregir_en_tiempo_real("temperatura", temp_cruda)
        print(f"Crudo: {temp_cruda}, Corregido: {temp_corregida}")
        
        # 6. Guardar para próximas ejecuciones
        orquestador.guardar_todo()
        
    Próximo arranque:
        orquestador.cargar_todo()  # Carga automáticamente
        orquestador.iniciar_deteccion_automatica(6)  # Reactivar monitoreo
```
        
        # Entrenar (necesita 7+ días de datos)
        modelo = calibrador.entrenar_desde_bus("temperatura_c", dias=7)
        
        # Aplicar corrección
        temp_raw = 25.5
        temp_corregida, _ = calibrador.aplicar_correccion("temperatura_c", temp_raw)
        
        # Publicar al Bus automáticamente
        calibrador.publicar_correccion_al_bus("temperatura_c", temp_raw)
    """)
