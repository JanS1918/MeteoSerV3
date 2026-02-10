"""
MOTOR DE PREDICCIÓN - Integración con Bus de Capas
===================================================
Orquesta predicciones en tiempo real:
1. Obtiene últimos 60 minutos del Bus (TIMESERIES)
2. Ejecuta modelo LSTM
3. Publica predicción al Bus (CORE con nivel de confianza)
4. Genera alertas si predicción supera umbrales

Uso:
    motor = obtener_motor_prediccion()
    motor.cargar_modelo("data/models/lstm_utci")
    motor.predecir_y_publicar()  # Ejecutar cada minuto
"""

import numpy as np
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from collections import deque

from core.prediction.lstm_predictor import LSTMPredictor, PreparadorDatos


class MotorPrediccion:
    """Motor que ejecuta predicciones y publica al Bus"""
    
    def __init__(self, bus):
        """
        Args:
            bus: Instancia de BusCapasInformacion
        """
        self.bus = bus
        self.modelos: Dict[str, LSTMPredictor] = {}
        self.variables_entrada: Dict[str, List[str]] = {}
        self.horizontes: Dict[str, int] = {}
        self.activo = False
        self.hilo = None
        self.intervalo_prediccion = 60  # segundos
        self.lock = threading.RLock()
        
        # Estadísticas
        self.predicciones_realizadas = 0
        self.ultimas_predicciones: deque = deque(maxlen=100)
    
    def cargar_modelo(self, nombre: str, ruta: str, 
                     variables_entrada: List[str],
                     horizonte: int = 5):
        """
        Carga un modelo entrenado
        
        Args:
            nombre: Identificador del modelo (ej: "utci")
            ruta: Ruta al modelo guardado
            variables_entrada: Variables del Bus necesarias
            horizonte: Minutos que predice
        """
        with self.lock:
            modelo = LSTMPredictor()
            modelo.cargar(ruta)
            
            self.modelos[nombre] = modelo
            self.variables_entrada[nombre] = variables_entrada
            self.horizontes[nombre] = horizonte
            
            print(f"✅ Modelo '{nombre}' cargado (+{horizonte} min)")
    
    def predecir(self, nombre_modelo: str) -> Optional[float]:
        """
        Ejecuta predicción de un modelo específico
        
        Args:
            nombre_modelo: Identificador del modelo
        
        Returns:
            Valor predicho (o None si falló)
        """
        with self.lock:
            if nombre_modelo not in self.modelos:
                print(f"❌ Modelo '{nombre_modelo}' no cargado")
                return None
            
            modelo = self.modelos[nombre_modelo]
            variables = self.variables_entrada[nombre_modelo]
            ventana = modelo.ventana
            
            # Verificar que todas las variables tengan suficiente histórico
            for var in variables:
                if var not in self.bus.capa_timeseries:
                    print(f"⚠️ Variable '{var}' sin histórico en Bus")
                    return None
                
                if len(self.bus.capa_timeseries[var].valores) < ventana:
                    print(f"⚠️ Insuficiente data para '{var}': {len(self.bus.capa_timeseries[var].valores)} < {ventana}")
                    return None
            
            # Preparar ventana de entrada
            X = []
            for t in range(ventana):
                features = [
                    self.bus.capa_timeseries[var].valores[t][0]
                    for var in variables
                ]
                X.append(features)
            
            X = np.array(X).reshape(1, ventana, len(variables))
            
            # Normalizar si hay parámetros
            if modelo.params_normalizacion:
                params = modelo.params_normalizacion
                X_min = np.array(params['X_min'])
                X_max = np.array(params['X_max'])
                X = (X - X_min) / (X_max - X_min + 1e-8)
            
            # Predecir
            y_norm = modelo.predecir(X)
            
            # Desnormalizar
            y = modelo.desnormalizar_prediccion(y_norm)
            
            return float(y[0][0])
    
    def predecir_y_publicar(self, nombre_modelo: str):
        """
        Predice y publica al Bus automáticamente
        
        Args:
            nombre_modelo: Modelo a ejecutar
        """
        prediccion = self.predecir(nombre_modelo)
        
        if prediccion is None:
            return
        
        horizonte = self.horizontes[nombre_modelo]
        
        # Calcular confianza basada en histórico de aciertos
        confianza = self._calcular_confianza(nombre_modelo, prediccion)
        
        # Publicar al Bus
        self.bus.publicar(
            variable=f"prediccion.{nombre_modelo}_plus_{horizonte}min",
            valor=prediccion,
            nivel="CORE",
            origen="core.prediction.MotorPrediccion",
            confianza=confianza,
            unidad="°C" if "temp" in nombre_modelo or "utci" in nombre_modelo else "",
            notas=f"Predicción +{horizonte} min por LSTM"
        )
        
        # Registrar
        self.predicciones_realizadas += 1
        self.ultimas_predicciones.append({
            'modelo': nombre_modelo,
            'prediccion': prediccion,
            'timestamp': datetime.now(),
            'confianza': confianza
        })
        
        print(f"🔮 Predicción {nombre_modelo} (+{horizonte} min): {prediccion:.2f} (confianza: {confianza:.2f})")
    
    def _calcular_confianza(self, nombre_modelo: str, prediccion: float) -> float:
        """
        Calcula confianza de predicción basada en histórico
        
        Criterios:
        - Si predicción muy distinta del valor actual → baja confianza
        - Si modelo ha acertado mucho → alta confianza
        - Si valores recientes muy estables → alta confianza
        """
        # Por defecto, confianza media
        confianza = 0.8
        
        # Obtener valor actual (primera variable de entrada)
        variables = self.variables_entrada[nombre_modelo]
        if variables[0] in self.bus.capa_timeseries:
            ts = self.bus.capa_timeseries[variables[0]]
            if ts.valores:
                valor_actual = ts.valores[-1][0]
                
                # Si predicción es muy distinta, bajar confianza
                diferencia = abs(prediccion - valor_actual)
                if diferencia > 5.0:  # Más de 5 unidades
                    confianza -= 0.2
                elif diferencia > 2.0:
                    confianza -= 0.1
                
                # Si valores recientes estables, subir confianza
                if len(ts.valores) >= 10:
                    ultimos = [v[0] for v in list(ts.valores)[-10:]]
                    desvio = np.std(ultimos)
                    if desvio < 0.5:  # Muy estable
                        confianza += 0.1
        
        return max(0.5, min(1.0, confianza))
    
    def iniciar_prediccion_automatica(self, intervalo: int = 60):
        """
        Inicia thread que ejecuta predicciones periódicamente
        
        Args:
            intervalo: Segundos entre predicciones (default 60)
        """
        if self.activo:
            print("⚠️ Motor de predicción ya activo")
            return
        
        self.intervalo_prediccion = intervalo
        self.activo = True
        self.hilo = threading.Thread(target=self._loop_prediccion, daemon=True)
        self.hilo.start()
        
        print(f"🚀 Motor de predicción iniciado (cada {intervalo}s)")
    
    def detener_prediccion_automatica(self):
        """Detiene predicciones automáticas"""
        self.activo = False
        if self.hilo:
            self.hilo.join(timeout=5)
        print("⏹️  Motor de predicción detenido")
    
    def _loop_prediccion(self):
        """Loop principal de predicciones"""
        while self.activo:
            try:
                # Predecir con todos los modelos cargados
                for nombre_modelo in self.modelos.keys():
                    self.predecir_y_publicar(nombre_modelo)
                
                time.sleep(self.intervalo_prediccion)
            except Exception as e:
                print(f"❌ Error en loop predicción: {e}")
                time.sleep(self.intervalo_prediccion)
    
    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas del motor"""
        with self.lock:
            return {
                'modelos_cargados': len(self.modelos),
                'predicciones_realizadas': self.predicciones_realizadas,
                'activo': self.activo,
                'intervalo_seg': self.intervalo_prediccion,
                'ultimas_predicciones': [
                    {
                        'modelo': p['modelo'],
                        'valor': p['prediccion'],
                        'timestamp': p['timestamp'].isoformat(),
                        'confianza': p['confianza']
                    }
                    for p in list(self.ultimas_predicciones)[-10:]
                ]
            }
    
    def generar_alertas(self, umbrales: Dict[str, Dict[str, float]]):
        """
        Genera alertas si predicciones superan umbrales
        
        Args:
            umbrales: Dict con estructura:
                {
                    "utci": {"critico": 35.0, "advertencia": 30.0},
                    "et0": {"critico": 8.0}
                }
        """
        for nombre_modelo, umbral_config in umbrales.items():
            variable_prediccion = f"prediccion.{nombre_modelo}_plus_{self.horizontes.get(nombre_modelo, 5)}min"
            
            meta = self.bus.capa_core.obtener(variable_prediccion)
            if not meta:
                continue
            
            valor_predicho = meta.valor
            
            # Verificar umbrales
            if 'critico' in umbral_config and valor_predicho >= umbral_config['critico']:
                self.bus.publicar(
                    variable=f"alerta.{nombre_modelo}_critica",
                    valor=True,
                    nivel="CORE",
                    origen="core.prediction.MotorPrediccion",
                    confianza=meta.confianza,
                    notas=f"¡ALERTA! {nombre_modelo} predicho en {valor_predicho:.1f} >= {umbral_config['critico']}"
                )
                print(f"🚨 ALERTA CRÍTICA: {nombre_modelo} = {valor_predicho:.1f}")
            
            elif 'advertencia' in umbral_config and valor_predicho >= umbral_config['advertencia']:
                self.bus.publicar(
                    variable=f"alerta.{nombre_modelo}_advertencia",
                    valor=True,
                    nivel="INTERMEDIATE",
                    origen="core.prediction.MotorPrediccion",
                    confianza=meta.confianza,
                    notas=f"Advertencia: {nombre_modelo} predicho en {valor_predicho:.1f}"
                )
                print(f"⚠️  ADVERTENCIA: {nombre_modelo} = {valor_predicho:.1f}")


# Singleton global
_motor_prediccion_global = None


def obtener_motor_prediccion(bus=None):
    """
    Obtiene o crea motor de predicción global
    
    Args:
        bus: BusCapasInformacion (si None, lo obtiene automáticamente)
    """
    global _motor_prediccion_global
    
    if _motor_prediccion_global is None:
        if bus is None:
            from core.bus import obtener_bus
            bus = obtener_bus()
        
        _motor_prediccion_global = MotorPrediccion(bus)
    
    return _motor_prediccion_global

    def _trend(self, nombre: str, window_s: int = 3600) -> Optional[float]:
        historial = self.system.obtener_historial_sensor(nombre)
        if not historial or len(historial) < 2:
            return None
        now = time.time()
        recent = [(t, v) for t, v in historial if (now - t) <= window_s]
        if len(recent) < 2:
            recent = historial[-10:]
        if len(recent) < 2:
            return None
        t0, v0 = recent[0]
        t1, v1 = recent[-1]
        dt_h = (t1 - t0) / 3600.0
        if dt_h <= 0:
            return None
        return (v1 - v0) / dt_h

    def _last(self, nombre: str) -> Optional[float]:
        val = self.system.obtener_sensor(nombre)
        if val is None:
            return None
        try:
            return float(val)
        except Exception:
            return None

    def _sensor_reliability(self, nombre: str) -> Optional[float]:
        try:
            meta = getattr(self.system, "sensores_metadata", {}).get(nombre, {})
        except Exception:
            meta = {}
        if not meta:
            return None
        try:
            val = float(meta.get("fiabilidad"))
            if val > 1.5:
                val = val / 100.0
            return max(0.0, min(1.0, val))
        except Exception:
            return None

    def _support_factor(self, sensores: List[str]) -> float:
        if not sensores:
            return 1.0
        reliabs: List[float] = []
        for s in sensores:
            r = self._sensor_reliability(s)
            if r is not None:
                reliabs.append(r)
        if not reliabs:
            return 1.0
        avg = sum(reliabs) / max(1, len(reliabs))
        factor = 0.6 + avg * 0.5
        return max(0.6, min(1.1, factor))

    def _support_from_indices(self, indices: Dict[str, Any] | None, nombres: List[str]) -> float:
        if not indices or not nombres:
            return 1.0
        scores: List[float] = []
        for n in nombres:
            info = indices.get(n)
            if not isinstance(info, dict):
                continue
            conf_score = info.get("confianza_score")
            if conf_score is None:
                continue
            try:
                scores.append(float(conf_score))
            except Exception:
                continue
        if not scores:
            return 1.0
        avg = sum(scores) / max(1, len(scores))
        factor = 0.8 + (avg / 100.0) * 0.4
        return max(0.7, min(1.2, factor))

    def predecir(self) -> Dict[str, Any]:
        pred: Dict[str, Any] = {}
        indices: Dict[str, Any] | None = None
        try:
            from core.indices.environmental_indices import EnvironmentalIndices
            if not isinstance(self.system.indices, EnvironmentalIndices):
                self.system.indices = EnvironmentalIndices(self.system)
            indices = self.system.indices.obtener_todos()
        except Exception:
            indices = None
        # Tendencias
        tendencia_temp = self._trend("temperatura")
        tendencia_pres = self._trend("presion")
        tendencia_hum = self._trend("humedad")
        tendencia_rad = self._trend("radiacion")
        tendencia_viento = self._trend("viento")

        if tendencia_temp is not None:
            pred["tendencia_temperatura"] = {"valor": round(tendencia_temp, 3), "unidad": "C/h", "fuente": "historico"}
        if tendencia_pres is not None:
            pred["tendencia_presion"] = {"valor": round(tendencia_pres, 3), "unidad": "hPa/h", "fuente": "historico"}
        if tendencia_hum is not None:
            pred["tendencia_humedad"] = {"valor": round(tendencia_hum, 3), "unidad": "%/h", "fuente": "historico"}
        if tendencia_rad is not None:
            pred["tendencia_radiacion"] = {"valor": round(tendencia_rad, 3), "unidad": "W/m²/h", "fuente": "historico"}
        if tendencia_viento is not None:
            pred["tendencia_viento"] = {"valor": round(tendencia_viento, 3), "unidad": "km/h/h", "fuente": "historico"}

        # Predicción de lluvia local (solo con sensores propios)
        humedad = self._last("humedad")
        presion = self._last("presion")
        radiacion = self._last("radiacion")
        lluvia_rate = self._last("lluvia_rate")
        if lluvia_rate is None:
            lluvia_rate = self._last("lluvia")

        prob_lluvia = None
        lluvia_cumplida = False
        lluvia_continua = False
        if humedad is not None:
            base = min(100.0, max(0.0, (humedad - 60) * 2.0))
            if presion is not None and tendencia_pres is not None:
                if tendencia_pres < 0:
                    base += min(30.0, abs(tendencia_pres) * 10)
            if radiacion is not None and radiacion < 100:
                base += 10.0
            if lluvia_rate is not None and lluvia_rate > 0:
                # Si ya está lloviendo y la probabilidad era alta, la alerta se cumple
                lluvia_cumplida = True
                # Si la tendencia de lluvia_rate es positiva o estable, se espera lluvia continua
                tendencia_lluvia = self._trend("lluvia_rate")
                if tendencia_lluvia is not None and tendencia_lluvia >= 0:
                    lluvia_continua = True
                base = 100.0
            prob_lluvia = max(0.0, min(100.0, base))

        if prob_lluvia is not None:
            support = self._support_factor(["humedad", "presion", "radiacion", "lluvia_rate", "lluvia"])
            support *= self._support_from_indices(indices, ["riesgo_lluvia", "riesgo_micro_lluvias", "alerta_tormenta"])
            prob_lluvia = max(0.0, min(100.0, prob_lluvia * support))
            if lluvia_cumplida and lluvia_continua:
                pred["prob_lluvia_continua"] = {
                    "valor": round(prob_lluvia, 2),
                    "unidad": "%",
                    "fuente": "sensores_propios",
                    "explicacion": "Lluvia actual y tendencia positiva: alta probabilidad de lluvia continua"
                }
            elif lluvia_cumplida:
                pred["prob_lluvia_cumplida"] = {
                    "valor": round(prob_lluvia, 2),
                    "unidad": "%",
                    "fuente": "sensores_propios",
                    "explicacion": "La alerta de lluvia se ha cumplido: está lloviendo"
                }
            else:
                pred["prob_lluvia"] = {
                    "valor": round(prob_lluvia, 2),
                    "unidad": "%",
                    "fuente": "sensores_propios",
                    "explicacion": "HR + tendencia presión + radiación + lluvia actual"
                }

        # Predicción de incomodidad térmica (simple)
        temp = self._last("temperatura")
        viento = self._last("viento")
        if temp is not None:
            score = 0.0
            if temp > 28:
                score += (temp - 28) * 5
            if temp < 12:
                score += (12 - temp) * 4
            if viento is not None and viento > 30:
                score += (viento - 30) * 1.5
            support = self._support_factor(["temperatura", "viento"])
            support *= self._support_from_indices(indices, ["sensacion_termica_compuesta", "sensacion_calor", "sensacion_frio"])
            score = max(0.0, min(100.0, score * support))
            pred["riesgo_incomodidad_termica"] = {
                "valor": round(max(0.0, min(100.0, score)), 2),
                "unidad": "%",
                "fuente": "sensores_propios",
                "explicacion": "Temperatura + viento"
            }

        return pred
