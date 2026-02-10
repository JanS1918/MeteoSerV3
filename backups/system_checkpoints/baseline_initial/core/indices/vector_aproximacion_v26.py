"""
vector_aproximacion_v26.py

Vector de Aproximación (Predicción #26) - Radar Pasivo de Inclemencia

Implementa la fusión de:
- Ley de Buys-Ballot (gradiente de presión + viento)
- Análisis óptico de cuadrantes (radiación diferencial)
- Tracking de rayos (RSSI, intensidad de señal)
- Corrección de declinación magnética
- Filtro de histéresis (EMA) para suavizado

Resultado: "Lluvia/Tormenta aproximándose desde [Dirección] a [Velocidad] km/h, ETA: [Tiempo]"
"""

import math
from typing import Dict, Optional, Tuple
from collections import deque


class VectorAproximacion:
    """Radar Pasivo de Inclemencia - Predicción #26"""
    
    def __init__(self, lat: float = 41.5513, lon: float = 2.3998):
        self.lat = lat
        self.lon = lon
        # Declinación magnética para Argentona (aproximadamente +2°)
        self.declinacion_magnetica = 2.0  # grados
        
        # Historial para filtro EMA
        self.historial_direccion = deque(maxlen=10)
        self.historial_velocidad = deque(maxlen=10)
        self.historial_rayos = deque(maxlen=20)
        
        # Factor EMA (más pequeño = más suavizado)
        self.factor_ema = 0.3


    def ley_buys_ballot(self, presion_hpa: float, tendencia_presion_hpa_h: float,
                       viento_dir_magnetico: float, viento_vel_ms: float) -> Dict[str, Any]:
        """
        Ley de Buys-Ballot: En hemisferio norte, si te pones de espaldas al viento,
        las bajas presiones (lluvia) están a tu izquierda.
        
        Calcula la dirección del centro de baja presión.
        """
        # Convertir a norte geográfico
        viento_dir_geografico = (viento_dir_magnetico + self.declinacion_magnetica) % 360
        
        # Ángulo de desviación desde el viento (perpendicularidad Buys-Ballot)
        # En hemisferio norte, la baja está a 90° a la izquierda del viento
        angulo_baja_presion = (viento_dir_geografico + 90) % 360
        
        # Estimar distancia aproximada de la baja (función de tendencia)
        # Si la presión baja rápido (< -2 hPa/h), la tormenta está cerca
        if tendencia_presion_hpa_h < -3:
            distancia_categoria = "MUY CERCANA (< 50 km)"
            distancia_km = 20
        elif tendencia_presion_hpa_h < -1:
            distancia_categoria = "CERCANA (50-150 km)"
            distancia_km = 100
        elif tendencia_presion_hpa_h < 0:
            distancia_categoria = "MEDIA (150-300 km)"
            distancia_km = 200
        else:
            distancia_categoria = "LEJANA o SIN CAMBIO"
            distancia_km = 999
        
        # Calcular ETA basado en velocidad del viento (aproximación)
        if viento_vel_ms > 0.5:
            eta_horas = distancia_km / (viento_vel_ms * 3.6)  # m/s a km/h
        else:
            eta_horas = 999
        
        return {
            "direccion_baja_presion_grados": round(angulo_baja_presion, 1),
            "direccion_baja_presion_cuadrante": self._grados_a_cuadrante(angulo_baja_presion),
            "distancia_categoria": distancia_categoria,
            "distancia_km_estimada": round(distancia_km, 1),
            "tendencia_presion_hpa_h": round(tendencia_presion_hpa_h, 3),
            "eta_horas": round(eta_horas, 1) if eta_horas < 999 else "Indefinido",
            "severidad_buys_ballot": self._severidad_presion(tendencia_presion_hpa_h)
        }


    def analisis_cuadrante_optico(self, radiacion_real_w_m2: float, 
                                 radiacion_teorica_w_m2: float,
                                 posicion_sol_azimut: float,
                                 angulo_cenital_sol: float) -> Dict[str, Any]:
        """
        Análisis diferencial de radiación por cuadrantes para detectar
        el avance de la nubosidad.
        
        Si el UV cae más rápido en el Este pero el Oeste está limpio,
        la nubosidad se acerca desde el Oeste.
        """
        if radiacion_teorica_w_m2 < 1:
            transmitancia = 0.0
        else:
            transmitancia = radiacion_real_w_m2 / radiacion_teorica_w_m2
        
        # Si el sol está bajo (amanecer/atardecer), el análisis es menos preciso
        precision = "ALTA" if 20 < angulo_cenital_sol < 70 else "BAJA"
        
        # Cuadrante óptico de oscurecimiento (opuesto al sol)
        cuadrante_oscuro = (posicion_sol_azimut + 180) % 360
        
        # Interpretación
        if transmitancia > 0.8:
            tipo_evento = "Cielo despejado"
            aproximacion = "Sin nubosidad significativa"
            direccion_flujo = 360
        elif transmitancia > 0.6:
            tipo_evento = "Cirros/nubes altas"
            aproximacion = "Posible frente de baja presión distante (6-24h)"
            direccion_flujo = cuadrante_oscuro
        elif transmitancia > 0.4:
            tipo_evento = "Cúmulos/estratos"
            aproximacion = "Frontal próximo (2-6h)"
            direccion_flujo = cuadrante_oscuro
        elif transmitancia > 0.2:
            tipo_evento = "Tormenta desarrollándose"
            aproximacion = "Impacto inminente (0-2h)"
            direccion_flujo = cuadrante_oscuro
        else:
            tipo_evento = "Tormenta severa"
            aproximacion = "IMPACTO INMEDIATO"
            direccion_flujo = cuadrante_oscuro
        
        return {
            "transmitancia": round(transmitancia, 3),
            "tipo_evento": tipo_evento,
            "aproximacion": aproximacion,
            "cuadrante_oscuro_grados": round(cuadrante_oscuro, 1),
            "cuadrante_oscuro_cardinal": self._grados_a_cuadrante(cuadrante_oscuro),
            "precision": precision,
            "direccion_flujo_grados": round(direccion_flujo, 1)
        }


    def tracking_rayos_rssi(self, rayos_detectados: int, rssi_promedio: float,
                           tendencia_rssi: str = "aumentando") -> Dict[str, Any]:
        """
        Tracking de rayos mediante RSSI (Received Signal Strength Indicator)
        
        RSSI más alto = rayos más cercanos
        Tendencia RSSI = aproximación o alejamiento
        """
        self.historial_rayos.append(rssi_promedio)
        
        # Estimar distancia según RSSI (modelo empírico)
        # RSSI ~ -110 a -30 dBm
        if rssi_promedio > -50:
            distancia_km = 10
            categoria_distancia = "MUY CERCANA"
        elif rssi_promedio > -70:
            distancia_km = 30
            categoria_distancia = "CERCANA"
        elif rssi_promedio > -90:
            distancia_km = 100
            categoria_distancia = "MEDIA"
        else:
            distancia_km = 200
            categoria_distancia = "LEJANA"
        
        # Velocidad de aproximación (cambio de RSSI en el tiempo)
        if len(self.historial_rayos) > 1:
            delta_rssi = self.historial_rayos[-1] - self.historial_rayos[-2]
            if delta_rssi > 5:
                velocidad_aproximacion = "Rápido acercamiento"
                velocidad_ms = 15
            elif delta_rssi > 1:
                velocidad_aproximacion = "Acercamiento moderado"
                velocidad_ms = 8
            elif delta_rssi < -5:
                velocidad_aproximacion = "Alejándose rápidamente"
                velocidad_ms = -15
            else:
                velocidad_aproximacion = "Estable/Pasando"
                velocidad_ms = 0
        else:
            velocidad_aproximacion = "Insuficientes datos"
            velocidad_ms = 0
        
        # Tasa de rayos
        if rayos_detectados > 10:
            actividad_electrica = "MUY ACTIVA"
            severidad = "EXTREMA"
        elif rayos_detectados > 5:
            actividad_electrica = "ACTIVA"
            severidad = "ALTA"
        elif rayos_detectados > 1:
            actividad_electrica = "MODERADA"
            severidad = "MEDIA"
        else:
            actividad_electrica = "LIGERA"
            severidad = "BAJA"
        
        return {
            "rayos_detectados": rayos_detectados,
            "rssi_promedio_dbm": round(rssi_promedio, 1),
            "distancia_estimada_km": round(distancia_km, 1),
            "categoria_distancia": categoria_distancia,
            "velocidad_aproximacion": velocidad_aproximacion,
            "velocidad_ms": round(velocidad_ms, 1),
            "actividad_electrica": actividad_electrica,
            "severidad_tormentosa": severidad
        }


    def filtro_ema_suavizado(self, valor_nuevo: float, historial: deque) -> float:
        """
        Exponential Moving Average (EMA) para suavizar saltos bruscos
        evitando que la brújula "oscile" con cada racha de viento
        """
        if not historial or len(historial) == 0:
            return valor_nuevo
        
        ema_anterior = sum(historial) / len(historial)
        ema_nueva = (valor_nuevo * self.factor_ema) + (ema_anterior * (1 - self.factor_ema))
        
        return ema_nueva


    def vector_final_aproximacion(self, presion_hpa: float, 
                                 tendencia_presion_hpa_h: float,
                                 viento_dir_magnetico: float, viento_vel_ms: float,
                                 radiacion_real: float, radiacion_teorica: float,
                                 azimut_sol: float, angulo_cenital_sol: float,
                                 rayos_detectados: int = 0, rssi_promedio: float = -80) -> Dict[str, Any]:
        """
        FUSIÓN FINAL: Combina Buys-Ballot + Óptica + Rayos en un VECTOR DE APROXIMACIÓN
        """
        # Subfusión 1: Buys-Ballot (presión + viento)
        buys_ballot = self.ley_buys_ballot(presion_hpa, tendencia_presion_hpa_h, 
                                          viento_dir_magnetico, viento_vel_ms)
        
        # Subfusión 2: Análisis óptico
        optica = self.analisis_cuadrante_optico(radiacion_real, radiacion_teorica,
                                               azimut_sol, angulo_cenital_sol)
        
        # Subfusión 3: Tracking de rayos
        rayos = self.tracking_rayos_rssi(rayos_detectados, rssi_promedio)
        
        # FUSIÓN DE VECTORES
        # Dirección final: promedio ponderado de Buys-Ballot + Óptica + Rayos
        dir_buys = buys_ballot["direccion_baja_presion_grados"]
        dir_optica = optica["direccion_flujo_grados"]
        dir_rayos = rayos.get("direccion_estimada_grados", 360) if rayos_detectados > 0 else 360
        
        # Ponderación según confianza
        peso_buys = 0.5 if tendencia_presion_hpa_h < 0 else 0.3
        peso_optica = 0.4
        peso_rayos = 0.1 if rayos_detectados > 0 else 0.0
        
        # Normalizar pesos
        suma_pesos = peso_buys + peso_optica + peso_rayos
        peso_buys /= suma_pesos
        peso_optica /= suma_pesos
        peso_rayos /= suma_pesos
        
        # Calcular dirección circular promedio
        dir_x = (math.sin(math.radians(dir_buys)) * peso_buys + 
                math.sin(math.radians(dir_optica)) * peso_optica +
                math.sin(math.radians(dir_rayos)) * peso_rayos)
        dir_y = (math.cos(math.radians(dir_buys)) * peso_buys +
                math.cos(math.radians(dir_optica)) * peso_optica +
                math.cos(math.radians(dir_rayos)) * peso_rayos)
        
        dir_final_rad = math.atan2(dir_x, dir_y)
        dir_final_grados = math.degrees(dir_final_rad) % 360
        
        # Aplicar filtro EMA
        self.historial_direccion.append(dir_final_grados)
        dir_suavizada = self.filtro_ema_suavizado(dir_final_grados, self.historial_direccion)
        
        # Velocidad de aproximación (promedio de fuentes)
        vel_aproximacion = (buys_ballot.get("eta_horas", 999) if isinstance(buys_ballot.get("eta_horas", 999), (int, float)) else 999)
        
        # ETA final
        distancia_media = (buys_ballot["distancia_km_estimada"] + rayos.get("distancia_estimada_km", 999)) / 2
        if viento_vel_ms > 1:
            eta_final = distancia_media / (viento_vel_ms * 3.6)
        else:
            eta_final = 999
        
        # Nivel de alerta general
        severidad_presion = 1 if tendencia_presion_hpa_h < -3 else 0
        severidad_rayos = 1 if rayos_detectados > 5 else 0
        severidad_optica = 1 if optica["transmitancia"] < 0.4 else 0
        
        nivel_alerta = severidad_presion + severidad_rayos + severidad_optica
        if nivel_alerta >= 2:
            alerta_general = "🚨 ALERTA ROJA - Tormenta inminente"
        elif nivel_alerta == 1:
            alerta_general = "⚠️ ALERTA NARANJA - Tormenta próxima"
        else:
            alerta_general = "✓ VERDE - Sin peligro inmediato"
        
        return {
            "vector_aproximacion": {
                "direccion_grados": round(dir_suavizada, 1),
                "direccion_cardinal": self._grados_a_cuadrante(dir_suavizada),
                "distancia_km": round(distancia_media, 1),
                "eta_horas": round(eta_final, 1) if eta_final < 999 else "Indefinido",
                "velocidad_aproximacion_kmh": round(viento_vel_ms * 3.6, 1)
            },
            "componentes": {
                "buys_ballot": buys_ballot,
                "analisis_optico": optica,
                "tracking_rayos": rayos
            },
            "nivel_alerta": alerta_general,
            "confianza_prediccion": "ALTA" if tendencia_presion_hpa_h < -1 else "MEDIA"
        }


    def _grados_a_cuadrante(self, grados: float) -> str:
        """Convierte grados a cardinal (N, NE, E, SE, S, SO, O, NO)"""
        cuadrantes = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
        indice = int((grados + 11.25) / 22.5) % 16
        return cuadrantes[indice]
    
    def _severidad_presion(self, tendencia_hpa_h: float) -> str:
        """Evalúa severidad según tendencia barométrica"""
        if tendencia_hpa_h < -5:
            return "EXTREMA"
        elif tendencia_hpa_h < -2:
            return "SEVERA"
        elif tendencia_hpa_h < -0.5:
            return "MODERADA"
        else:
            return "LEVE o ESTABLE"
