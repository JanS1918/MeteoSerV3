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
from typing import Optional, Dict, List, Any
from collections import deque

from core.prediction.lstm_predictor import LSTMPredictor, PreparadorDatos

# PRECISIÓN TOTAL: desactivar redondeo en cálculos internos
def _no_round(value, *args, **kwargs):
    return value

round = _no_round


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
            
            print(f"[OK] Modelo '{nombre}' cargado (+{horizonte} min)")
    
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
                print(f"[ERROR] Modelo '{nombre_modelo}' no cargado")
                return None
            
            modelo = self.modelos[nombre_modelo]
            variables = self.variables_entrada[nombre_modelo]
            ventana = modelo.ventana
            
            # Verificar que todas las variables tengan suficiente histórico
            for var in variables:
                if var not in self.bus.capa_timeseries:
                    print(f"[WARNING] Variable '{var}' sin histórico en Bus")
                    return None
                
                if len(self.bus.capa_timeseries[var].valores) < ventana:
                    print(f"[WARNING] Insuficiente data para '{var}': {len(self.bus.capa_timeseries[var].valores)} < {ventana}")
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
            print("[WARNING] Motor de predicción ya activo")
            return
        
        self.intervalo_prediccion = intervalo
        self.activo = True
        self.hilo = threading.Thread(target=self._loop_prediccion, daemon=True)
        self.hilo.start()
        
        print(f"[LAUNCH] Motor de predicción iniciado (cada {intervalo}s)")
    
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
                print(f"[ERROR] Error en loop predicción: {e}")
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
                print(f"[CRITICAL] ALERTA CRÍTICA: {nombre_modelo} = {valor_predicho:.1f}")
            
            elif 'advertencia' in umbral_config and valor_predicho >= umbral_config['advertencia']:
                self.bus.publicar(
                    variable=f"alerta.{nombre_modelo}_advertencia",
                    valor=True,
                    nivel="INTERMEDIATE",
                    origen="core.prediction.MotorPrediccion",
                    confianza=meta.confianza,
                    notas=f"Advertencia: {nombre_modelo} predicho en {valor_predicho:.1f}"
                )
                print(f"[WARNING]  ADVERTENCIA: {nombre_modelo} = {valor_predicho:.1f}")


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


class PredictionEngine:
    """Predicción física/heurística en tiempo real usando sensores locales."""

    def __init__(self, system):
        self.system = system

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

    def _combine_estimators(self, values: List[float], weights: Optional[List[float]] = None) -> tuple[float, float]:
        if not values:
            return 0.0, 0.0
        if weights and len(weights) == len(values):
            total_w = sum(weights)
            if total_w > 0:
                avg = sum(v * w for v, w in zip(values, weights)) / total_w
            else:
                avg = sum(values) / len(values)
        else:
            avg = sum(values) / len(values)
        var = sum((v - avg) ** 2 for v in values) / max(1, len(values))
        std = var ** 0.5
        return max(0.0, min(100.0, avg)), max(0.0, std)

    def predecir(self) -> Dict[str, Any]:
        pred: Dict[str, Any] = {}
        indices: Dict[str, Any] | None = None
        time_feats = self._time_features()
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
        if tendencia_pres is None:
            tendencia_pres = self._trend("presion_barometrica")
            if tendencia_pres is not None:
                tendencia_pres = tendencia_pres / 100.0
        tendencia_hum = self._trend("humedad")
        tendencia_rad = self._trend("radiacion") or self._trend("radiacion_global")
        tendencia_viento = self._trend("velocidad_viento") or self._trend("viento")

        if tendencia_temp is not None:
            pred["tendencia_temperatura"] = {"valor": round(tendencia_temp, 3), "unidad": "C/h", "fuente": "historico"}
        if tendencia_pres is not None:
            pred["tendencia_presion"] = {"valor": round(tendencia_pres, 3), "unidad": "hPa/h", "fuente": "historico"}
        if tendencia_hum is not None:
            pred["tendencia_humedad"] = {"valor": round(tendencia_hum, 3), "unidad": "%/h", "fuente": "historico"}
        if tendencia_rad is not None:
            pred["tendencia_radiacion"] = {"valor": round(tendencia_rad, 3), "unidad": "W/m²/h", "fuente": "historico"}
        if tendencia_viento is not None:
            pred["tendencia_viento"] = {"valor": round(tendencia_viento, 3), "unidad": "m/s/h", "fuente": "historico"}

        # Predicción de lluvia local (pura física: microfísica Thompson + Sundqvist)
        humedad = self._last("humedad")
        presion = self._last("presion") or self._last("presion_barometrica") or self._last("presion_hpa")
        if presion is not None and presion > 2000:
            presion = presion / 100.0
        radiacion = self._last("radiacion") or self._last("radiacion_global")
        lluvia_rate = (
            self._last("lluvia_rate")
            or self._last("lluvia_rate_actual")
            or self._last("rainrate")
            or self._last("rainratein")
            or self._last("precipitacion_rate")
            or self._last("precipitacion_rate_mm_h")
        )
        if lluvia_rate is None:
            lluvia_rate = self._last("lluvia")

        prob_lluvia = None
        if humedad is not None and presion is not None:
            from core.indices.environmental_indices import _calcular_qnet_brunt_monteith
            from core.indices.microphysics_thompson_vectorized import calcular_hidrometeoros_vectorizado
            from core.indices.sundqvist_precipitation import calcular_probabilidad_lluvia_sundqvist

            temp = self._last("temperatura")
            nub = None
            if isinstance(indices, dict) and isinstance(indices.get("nubosidad_estimada"), dict):
                nub = indices.get("nubosidad_estimada", {}).get("valor")

            qnet_val = None
            if isinstance(indices, dict) and isinstance(indices.get("radiacion_neta"), dict):
                qnet_val = indices.get("radiacion_neta", {}).get("valor")
            if qnet_val is None and temp is not None and nub is not None:
                qnet_val = _calcular_qnet_brunt_monteith(float(temp), float(humedad), float(nub) / 100.0)

            try:
                lluvia_rate_val = float(lluvia_rate) if lluvia_rate is not None else 0.0
            except Exception:
                lluvia_rate_val = 0.0

            micro = calcular_hidrometeoros_vectorizado(
                temperatura_c=float(temp) if temp is not None else 0.0,
                humedad_relativa=float(humedad),
                presion_hpa=float(presion),
                lluvia_rate_mm_h=lluvia_rate_val,
            )
            tendencia_presion = self._trend("presion") or self._trend("presion_barometrica")
            if tendencia_presion is not None and tendencia_presion > 2:
                tendencia_presion = tendencia_presion / 100.0

            sundq = calcular_probabilidad_lluvia_sundqvist(
                temperatura_c=float(temp) if temp is not None else 0.0,
                humedad_relativa=float(humedad),
                presion_hpa=float(presion),
                qc=micro.get("qc_gkg", 0.0),
                qr=micro.get("qr_gkg", 0.0),
                tendencia_presion_hpa_h=tendencia_presion,
                radiacion_neta_wm2=qnet_val,
            )
            prob_lluvia = max(0.0, min(100.0, float(sundq.get("prob_lluvia_pct", 0.0))))

            pred["lluvia_microfisica_qc_gkg"] = {
                "valor": micro.get("qc_gkg", 0.0),
                "unidad": "g/kg",
                "fuente": "thompson"
            }
            pred["lluvia_microfisica_qr_gkg"] = {
                "valor": micro.get("qr_gkg", 0.0),
                "unidad": "g/kg",
                "fuente": "thompson"
            }
            pred["lluvia_tasa_condensacion_gkg_h"] = {
                "valor": sundq.get("tasa_condensacion_gkg_h", 0.0),
                "unidad": "g/kg/h",
                "fuente": "sundqvist"
            }
            pred["lluvia_eficiencia_precipitacion"] = {
                "valor": sundq.get("eficiencia_precipitacion", 0.0),
                "unidad": "0-1",
                "fuente": "sundqvist"
            }

        if prob_lluvia is not None:
            pred["prob_lluvia"] = {
                "valor": round(prob_lluvia, 2),
                "unidad": "%",
                "fuente": "sundqvist_thompson",
                "explicacion": "Microfísica Thompson + Sundqvist (sin heurísticas)"
            }

        # Predicción de incomodidad térmica (UTCI completo)
        utci_val = None
        if isinstance(indices, dict) and isinstance(indices.get("utci"), dict):
            utci_val = indices.get("utci", {}).get("valor")
        if utci_val is not None:
            try:
                utci_val = float(utci_val)
            except Exception:
                utci_val = None
        if utci_val is not None:
            if utci_val >= 32:
                score = min(100.0, (utci_val - 26.0) * 6.0)
            elif utci_val <= 0:
                score = min(100.0, (0.0 - utci_val) * 6.0)
            else:
                score = max(0.0, (abs(utci_val - 18.0) - 6.0) * 4.0)

            score = max(0.0, min(100.0, score))
            pred["riesgo_incomodidad_termica"] = {
                "valor": round(max(0.0, min(100.0, score)), 2),
                "unidad": "%",
                "fuente": "utci_completo",
                "explicacion": "UTCI completo"
            }

        return pred


# Alias para compatibilidad con código legacy
PredictionEngineLegacy = MotorPrediccion
