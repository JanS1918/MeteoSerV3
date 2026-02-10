"""
ALERTA DE LLUVIA INMINENTE V51
==============================
Predicción de lluvia en 10-20 minutos usando:
- Caída de radiación (dGHI/dt)
- Cambio de humedad relativa (dHR/dt) 
- Cambio de presión (dP/dt)
- Diferencial ΔT sol/sombra
- Probabilidad Sundqvist

Publica a bus:
- alerta_lluvia_inminente_score (0-100)
- alerta_lluvia_inminente_componentes (dict con detalles)
- alerta_lluvia_inminente_eta_minutos (10-20)
"""

import logging
import math
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AlertaLluviaInminenteV51:
    """
    Predictor de lluvia inminente sin LSTM.
    Usa física + observaciones locales para alertas tempranas.
    """
    
    def __init__(self):
        """Inicializa con umbrales físicos."""
        # Umbrales de sensibilidad
        self.UMBRAL_CAIDA_GHI_WM2_S = -15.0  # W/m²/s (bajada rápida de radiación)
        self.UMBRAL_AUMENTO_HR_MINUTO = 3.0   # %/min (humedad subiendo rápido)
        self.UMBRAL_CAIDA_PRESION_HPA_H = -4.0  # hPa/h (presión bajando rápido)
        self.UMBRAL_CAIDA_DT_SOLAR = -1.5    # °C/min (diferencial térmico decayendo)
        self.UMBRAL_SUNDQVIST = 40.0          # % de probabilidad
        
        # Historial para calcular derivadas
        self.historial_ghi = []               # (timestamp, ghi)
        self.historial_hr = []                # (timestamp, hr)
        self.historial_presion = []           # (timestamp, presion)
        self.historial_dt_solar = []          # (timestamp, dt)
        
        self._max_historial = 20  # Últimos 20 puntos (10 minutos a 30s cada uno)
        logger.info("[ALERTA_LLUVIA_V51] Inicializado")
    
    def evaluar(self, datos: Dict) -> Dict:
        """
        Evalúa riesgo de lluvia inminente.
        
        Args:
            datos: Dict con claves:
                - ghi_w_m2: Radiación global horizontal
                - humedad_rel: Humedad relativa (%)
                - presion_hpa: Presión (hPa)
                - temperatura_c: Temperatura (°C)
                - dt_solar_c: ΔT sol-sombra (°C, si existe)
                - prob_lluvia_sundqvist: Probabilidad Sundqvist (0-100)
        
        Returns:
            Dict con:
                - score: 0-100 (riesgo)
                - componentes: dict detalles
                - eta_minutos: estimación
        """
        
        ahora = datetime.now()
        
        # 1. CAÍDA DE RADIACIÓN (W/m²/s)
        ghi = datos.get("ghi_w_m2", 0)
        derivada_ghi = self._calcular_derivada(
            self.historial_ghi, ghi, ahora
        )
        score_ghi, info_ghi = self._evaluar_ghi(derivada_ghi)
        
        # 2. AUMENTO DE HUMEDAD (%/min)
        hr = datos.get("humedad_rel", 50)
        derivada_hr = self._calcular_derivada(
            self.historial_hr, hr, ahora, factor=1/60.0  # por minuto
        )
        score_hr, info_hr = self._evaluar_hr(derivada_hr)
        
        # 3. CAÍDA DE PRESIÓN (hPa/h)
        presion = datos.get("presion_hpa", 1013)
        derivada_presion = self._calcular_derivada(
            self.historial_presion, presion, ahora, factor=3600.0  # por hora
        )
        score_presion, info_presion = self._evaluar_presion(derivada_presion)
        
        # 4. CAÍDA DE ΔT SOL/SOMBRA (°C/min)
        dt_solar = datos.get("dt_solar_c", None)
        derivada_dt = 0
        score_dt = 0
        info_dt = {}
        
        if dt_solar is not None:
            derivada_dt = self._calcular_derivada(
                self.historial_dt_solar, dt_solar, ahora, factor=1/60.0
            )
            score_dt, info_dt = self._evaluar_dt_solar(derivada_dt)
        
        # 5. PROBABILIDAD SUNDQVIST
        prob_sundqvist = datos.get("prob_lluvia_sundqvist", 0)
        score_sundqvist, info_sundqvist = self._evaluar_sundqvist(prob_sundqvist)
        
        # SCORE TOTAL: promedio ponderado
        # Radiación (40%) + Presión (30%) + Humedad (20%) + ΔT Solar (10%) + Sundqvist (50% de peso extra)
        pesos = {
            "ghi": 0.25,
            "hr": 0.15,
            "presion": 0.25,
            "dt_solar": 0.10,
            "sundqvist": 0.25,
        }
        
        score_total = (
            score_ghi * pesos["ghi"] +
            score_hr * pesos["hr"] +
            score_presion * pesos["presion"] +
            score_dt * pesos["dt_solar"] +
            score_sundqvist * pesos["sundqvist"]
        )
        score_total = max(0, min(100, score_total))
        
        # ESTIMACIÓN DE ETA
        eta_minutos = self._estimar_eta(
            score_ghi, score_presion, score_hr
        )
        
        # CONSTRUCCIÓN DE RESPUESTA
        resultado = {
            "score": score_total,
            "eta_minutos": eta_minutos,
            "confianza": self._calcular_confianza(
                score_ghi, score_presion, score_hr, dt_solar is not None
            ),
            "componentes": {
                "caida_ghi_wm2s": derivada_ghi,
                "score_ghi": score_ghi,
                "info_ghi": info_ghi,
                
                "aumento_hr_porciento_min": derivada_hr,
                "score_hr": score_hr,
                "info_hr": info_hr,
                
                "caida_presion_hpa_h": derivada_presion,
                "score_presion": score_presion,
                "info_presion": info_presion,
                
                "caida_dt_solar_c_min": derivada_dt,
                "score_dt_solar": score_dt,
                "info_dt_solar": info_dt,
                
                "prob_sundqvist": prob_sundqvist,
                "score_sundqvist": score_sundqvist,
                "info_sundqvist": info_sundqvist,
            }
        }
        
        return resultado
    
    def _calcular_derivada(self, historial: list, valor: float, 
                          ahora: datetime, factor: float = 1.0) -> float:
        """
        Calcula derivada temporal usando últimos 2 puntos confiables.
        
        Returns:
            Derivada en unidades/segundo * factor
        """
        # Agregar punto actual
        historial.append((ahora, valor))
        
        # Mantener solo últimos N puntos
        if len(historial) > self._max_historial:
            historial.pop(0)
        
        # Necesitar al menos 2 puntos
        if len(historial) < 2:
            return 0.0
        
        # Usar últimos 2 puntos
        (t1, v1) = historial[-2]
        (t2, v2) = historial[-1]
        
        dt_segundos = (t2 - t1).total_seconds()
        if dt_segundos <= 0:
            return 0.0
        
        derivada = (v2 - v1) / dt_segundos * factor
        return derivada
    
    def _evaluar_ghi(self, derivada_ghi: float) -> Tuple[float, Dict]:
        """Caída de radiación."""
        if derivada_ghi < self.UMBRAL_CAIDA_GHI_WM2_S:
            # Caída muy rápida
            magnitud = abs(derivada_ghi) / abs(self.UMBRAL_CAIDA_GHI_WM2_S)
            score = min(100, 60 + magnitud * 40)
            info = {"tipo": "caida_rapida", "severidad": "alta"}
        elif derivada_ghi < -5.0:
            # Caída leve pero significativa
            score = 40
            info = {"tipo": "caida_leve", "severidad": "moderada"}
        else:
            score = max(0, derivada_ghi * -5)  # Cada -1 W/m²/s = 5 puntos
            info = {"tipo": "estable", "severidad": "baja"}
        
        return min(100, score), info
    
    def _evaluar_hr(self, derivada_hr: float) -> Tuple[float, Dict]:
        """Aumento de humedad relativa."""
        if derivada_hr > self.UMBRAL_AUMENTO_HR_MINUTO:
            # Humedad subiendo rápido
            magnitud = derivada_hr / self.UMBRAL_AUMENTO_HR_MINUTO
            score = min(100, 50 + magnitud * 50)
            info = {"tipo": "aumento_rapido", "severidad": "alta"}
        elif derivada_hr > 1.0:
            # Aumento leve pero significativo
            score = 30
            info = {"tipo": "aumento_leve", "severidad": "moderada"}
        else:
            score = max(0, derivada_hr * 30)
            info = {"tipo": "estable", "severidad": "baja"}
        
        return min(100, score), info
    
    def _evaluar_presion(self, derivada_presion: float) -> Tuple[float, Dict]:
        """Caída de presión."""
        if derivada_presion < self.UMBRAL_CAIDA_PRESION_HPA_H:
            # Caída rápida = frente húmedo
            magnitud = abs(derivada_presion) / abs(self.UMBRAL_CAIDA_PRESION_HPA_H)
            score = min(100, 70 + magnitud * 30)
            info = {"tipo": "caida_rapida", "severidad": "alta", "fenomeno": "frente_humedo"}
        elif derivada_presion < -2.0:
            # Caída moderada
            score = 40
            info = {"tipo": "caida_moderada", "severidad": "moderada"}
        else:
            score = max(0, derivada_presion * -20)
            info = {"tipo": "estable", "severidad": "baja"}
        
        return min(100, score), info
    
    def _evaluar_dt_solar(self, derivada_dt: float) -> Tuple[float, Dict]:
        """Caída de ΔT sol/sombra."""
        if derivada_dt < self.UMBRAL_CAIDA_DT_SOLAR:
            # Diferencial decayendo rápido = nubosidad inminente
            magnitud = abs(derivada_dt) / abs(self.UMBRAL_CAIDA_DT_SOLAR)
            score = min(100, 55 + magnitud * 45)
            info = {"tipo": "caida_rapida", "severidad": "alta", "fenomeno": "nubosidad_inminente"}
        elif derivada_dt < -0.5:
            # Caída leve
            score = 25
            info = {"tipo": "caida_leve", "severidad": "moderada"}
        else:
            score = max(0, derivada_dt * -40)
            info = {"tipo": "estable", "severidad": "baja"}
        
        return min(100, score), info
    
    def _evaluar_sundqvist(self, prob_sundqvist: float) -> Tuple[float, Dict]:
        """Probabilidad Sundqvist de lluvia."""
        if prob_sundqvist > self.UMBRAL_SUNDQVIST:
            # Probabilidad significativa
            score = min(100, 30 + (prob_sundqvist / 100.0) * 70)
            info = {"tipo": "probabilidad_alta", "severidad": "moderada"}
        elif prob_sundqvist > 20:
            # Probabilidad baja pero no nula
            score = 20
            info = {"tipo": "probabilidad_baja", "severidad": "baja"}
        else:
            score = 0
            info = {"tipo": "improbable", "severidad": "nula"}
        
        return score, info
    
    def _estimar_eta(self, score_ghi: float, score_presion: float, 
                     score_hr: float) -> float:
        """
        Estima tiempo (minutos) hasta lluvia.
        
        Returns:
            10-20 minutos (o 0 si no hay riesgo)
        """
        if score_ghi + score_presion + score_hr < 30:
            return 0
        
        # Usar score de presión como indicador principal
        # Caída rápida = lluvia en 10 min
        # Caída leve = lluvia en 20 min
        if score_presion > 70:
            return 10
        elif score_presion > 40:
            return 12
        elif score_ghi > 60:
            return 15
        else:
            return 20
    
    def _calcular_confianza(self, score_ghi: float, score_presion: float,
                           score_hr: float, tiene_dt_solar: bool) -> str:
        """Calcula confianza de la predicción."""
        # Más señales = más confianza
        senales = sum([
            score_ghi > 30,
            score_presion > 30,
            score_hr > 30,
            tiene_dt_solar,
        ])
        
        if senales >= 3:
            return "alta"
        elif senales >= 2:
            return "moderada"
        else:
            return "baja"


def evaluar_lluvia_inminente(bus_datos: Dict) -> Dict:
    """
    Función global para evaluar alerta de lluvia.
    
    Args:
        bus_datos: Dict con datos del bus
    
    Returns:
        Dict con score, ETA y componentes
    """
    evaluador = AlertaLluviaInminenteV51()
    return evaluador.evaluar(bus_datos)
