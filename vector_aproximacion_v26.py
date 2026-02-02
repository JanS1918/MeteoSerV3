"""
vector_aproximacion_v26.py
===========================
Vector de Aproximación (#26) con Ángulo de Ekman integrado
Versión: 2.6 (Corrección Geofísica)

Fusión de 3 fuentes:
- 50% Ley de Buys-Ballot
- 40% Análisis Óptico
- 10% Tracking RSSI

Correcciones V2.6:
- Ángulo de Inflow de Ekman según rugosidad
- Declinación magnética (+2° Argentona)
- Suavizado EMA
"""

import math
from core.correccion_geofisica_v26 import angulo_inflow_ekman, corregir_vector_aproximacion


class VectorAproximacion:
    """Vector de aproximación con corrección de Ekman"""
    
    def __init__(self, rugosidad_terreno=0.15, declinacion_magnetica=2.0):
        self.rugosidad = rugosidad_terreno
        self.declinacion = declinacion_magnetica
        self.historial_direcciones = []
    
    def ley_buys_ballot(self, presion_hpa, velocidad_viento_ms, direccion_viento_grados,
                        tendencia_presion_hpa_h):
        """
        Localiza baja presión usando Ley de Buys-Ballot
        
        En Hemisferio Norte: baja presión está a 90° a la izquierda del viento
        """
        # Dirección hacia la baja presión (90° a la izquierda)
        direccion_baja = (direccion_viento_grados - 90) % 360
        
        # Distancia estimada (heurística: 100 km por cada hPa de diferencia)
        distancia_km = abs(1013 - presion_hpa) * 100
        
        # ETA según tendencia
        if tendencia_presion_hpa_h < 0:
            eta_horas = abs(presion_hpa - 985) / abs(tendencia_presion_hpa_h)
        else:
            eta_horas = 999  # Sistema alejándose
        
        return {
            "direccion_grados": direccion_baja,
            "distancia_km_estimada": distancia_km,
            "eta_horas": min(eta_horas, 48),
            "severidad_buys_ballot": "ALTA" if tendencia_presion_hpa_h < -2 else "MODERADA"
        }
    
    def analisis_cuadrante_optico(self, radiacion_real_w_m2, radiacion_teorica_w_m2,
                                  temperatura_cambio_c):
        """
        Detecta frente por cambio óptico
        """
        transmitancia = radiacion_real_w_m2 / radiacion_teorica_w_m2 if radiacion_teorica_w_m2 > 0 else 1.0
        
        # Cuadrante según cambio de temperatura
        if temperatura_cambio_c < -2:
            cuadrante = "N"
            direccion_grados = 0
        elif temperatura_cambio_c > 2:
            cuadrante = "S"
            direccion_grados = 180
        else:
            cuadrante = "O"
            direccion_grados = 270
        
        if transmitancia < 0.3:
            tipo_evento = "Cúmulos densos (Cb)"
            precision = "ALTA"
        elif transmitancia < 0.6:
            tipo_evento = "Cúmulos/estratos"
            precision = "MEDIA"
        else:
            tipo_evento = "Nubes altas"
            precision = "BAJA"
        
        return {
            "direccion_grados": direccion_grados,
            "cuadrante": cuadrante,
            "transmitancia": transmitancia,
            "tipo_evento": tipo_evento,
            "precision": precision
        }
    
    def tracking_rayos_rssi(self, rssi_dbm, rayos_detectados):
        """
        Estima distancia y severidad por RSSI
        """
        # Distancia: 10-200 km según RSSI
        distancia_km = 10 * (rssi_dbm + 90) / 30
        distancia_km = max(10, min(distancia_km, 200))
        
        # Severidad por número de rayos
        if rayos_detectados > 20:
            severidad = "MUY ALTA"
        elif rayos_detectados > 10:
            severidad = "ALTA"
        elif rayos_detectados > 3:
            severidad = "MODERADA"
        else:
            severidad = "BAJA"
        
        # Velocidad de aproximación (heurística)
        velocidad_aproximacion = 30 if rayos_detectados > 10 else 20
        
        return {
            "distancia_estimada_km": distancia_km,
            "rayos_detectados": rayos_detectados,
            "severidad_tormentosa": severidad,
            "velocidad_aproximacion_kmh": velocidad_aproximacion
        }
    
    def filtro_ema_suavizado(self, valores, alpha=0.2):
        """Suavizado EMA para prevenir jitter"""
        if not valores:
            return []
        
        ema = [valores[0]]
        for valor in valores[1:]:
            ema_nuevo = alpha * valor + (1 - alpha) * ema[-1]
            ema.append(ema_nuevo)
        
        return ema
    
    def vector_final_aproximacion(self, presion_hpa, velocidad_viento_ms, direccion_viento_grados,
                                  tendencia_presion_hpa_h, radiacion_real_w_m2, radiacion_teorica_w_m2,
                                  temperatura_cambio_c, rssi_dbm, rayos_detectados):
        """
        Fusión final con ponderación y corrección de Ekman
        
        Dirección = 50% Buys-Ballot + 40% Óptico + 10% RSSI
        """
        # Componentes
        bb = self.ley_buys_ballot(presion_hpa, velocidad_viento_ms, direccion_viento_grados,
                                   tendencia_presion_hpa_h)
        optico = self.analisis_cuadrante_optico(radiacion_real_w_m2, radiacion_teorica_w_m2,
                                                temperatura_cambio_c)
        rssi = self.tracking_rayos_rssi(rssi_dbm, rayos_detectados)
        
        # Fusión ponderada
        direccion_fusion = (
            0.5 * bb["direccion_grados"] +
            0.4 * optico["direccion_grados"] +
            0.1 * 225  # RSSI típicamente desde SO
        ) % 360
        
        # Corrección de Ekman por rugosidad
        inflow_ekman = angulo_inflow_ekman(velocidad_viento_ms, self.rugosidad)
        direccion_corregida = corregir_vector_aproximacion(direccion_fusion, inflow_ekman)
        
        # Declinación magnética
        direccion_final = (direccion_corregida + self.declinacion) % 360
        
        # Historial para EMA
        self.historial_direcciones.append(direccion_final)
        if len(self.historial_direcciones) > 10:
            self.historial_direcciones = self.historial_direcciones[-10:]
        
        # Suavizado EMA
        direcciones_suavizadas = self.filtro_ema_suavizado(self.historial_direcciones)
        direccion_suavizada = direcciones_suavizadas[-1] if direcciones_suavizadas else direccion_final
        
        # Distancia y ETA
        distancia_km = (bb["distancia_km_estimada"] + rssi["distancia_estimada_km"]) / 2
        velocidad_aproximacion = rssi["velocidad_aproximacion_kmh"]
        eta_horas = distancia_km / velocidad_aproximacion if velocidad_aproximacion > 0 else 999
        
        # Predicción textual
        direccion_cardinal = self._grados_a_cuadrante(direccion_suavizada)
        prediccion = f"LLUVIA desde {direccion_cardinal} a {velocidad_aproximacion:.0f} km/h, ETA: {eta_horas:.1f}h"
        
        return {
            "direccion_grados": direccion_suavizada,
            "direccion_cardinal": direccion_cardinal,
            "distancia_km": distancia_km,
            "eta_horas": eta_horas,
            "velocidad_aproximacion_kmh": velocidad_aproximacion,
            "prediccion": prediccion,
            "componentes": {
                "buys_ballot": bb,
                "analisis_optico": optico,
                "tracking_rayos": rssi
            },
            "correcciones": {
                "inflow_ekman_grados": inflow_ekman,
                "declinacion_magnetica_grados": self.declinacion,
                "rugosidad_terreno": self.rugosidad
            }
        }
    
    def _grados_a_cuadrante(self, grados):
        """Convierte grados a 16 puntos cardinales"""
        cuadrantes = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"
        ]
        indice = round(grados / 22.5) % 16
        return cuadrantes[indice]
