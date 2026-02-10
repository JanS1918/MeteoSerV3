"""
integracion_elite_motors_v25.py
================================
Integración de los 6 motores de élite + Bucholtz V2.5 + Vector #26
Versión: 2.6 (con correcciones geofísicas)

Conecta todo al Bus de Estado Global
"""

from datetime import datetime
from elite_motors_v25 import EliteMotorsV25
from bucholtz_rayleigh_v25 import BucholtzRayleighV25
from vector_aproximacion_v26 import VectorAproximacion


class IntegracionMotoresV25:
    """Orquestador maestro de todos los motores"""
    
    def __init__(self):
        self.elite_motors = EliteMotorsV25()
        self.bucholtz = BucholtzRayleighV25()
        self.vector = VectorAproximacion(rugosidad_terreno=0.15, declinacion_magnetica=2.0)
    
    def execute_ciclo_completo(self, sensores, contexto_ambiental):
        """
        Ejecuta la cascada completa de motores
        
        Args:
            sensores: dict con temperatura, presión, humedad, viento, radiación
            contexto_ambiental: dict con tipo_aire, nubosidad, etc.
        
        Returns:
            dict con todos los resultados
        """
        resultado = {}
        
        # 1. Ejecutar 6 motores de élite
        elite_results = self.elite_motors.ciclo_completo(sensores, contexto_ambiental)
        resultado.update(elite_results)
        
        # 2. Ejecutar Bucholtz-Rayleigh V2.5
        tipo_aire = elite_results.get('motor_masas_aire', {}).get('tipo_masa_aire', 'TEMPLADA')
        
        visibilidad_m, visibilidad_km, clasificacion = self.bucholtz.visibilidad_bucholtz_completa(
            temperatura_c=sensores['temperatura_c'],
            presion_hpa=sensores['presion_hpa'],
            humedad_relativa=sensores['humedad_relativa'],
            tipo_aire=tipo_aire,
            elevacion_solar=45
        )
        
        resultado['bucholtz_rayleigh_v25'] = {
            "visibilidad_m": visibilidad_m,
            "visibilidad_km": visibilidad_km,
            "clasificacion": clasificacion
        }
        
        # 3. Ejecutar Vector de Aproximación (#26)
        vector_result = self.vector.vector_final_aproximacion(
            presion_hpa=sensores['presion_hpa'],
            velocidad_viento_ms=sensores.get('velocidad_viento_ms', 5),
            direccion_viento_grados=sensores.get('direccion_viento_grados', 0),
            tendencia_presion_hpa_h=sensores.get('tendencia_presion_hpa_h', 0),
            radiacion_real_w_m2=sensores.get('radiacion_solar_w_m2', 500),
            radiacion_teorica_w_m2=sensores.get('radiacion_teorica_w_m2', 1000),
            temperatura_cambio_c=sensores.get('temperatura_cambio_c', 0),
            rssi_dbm=sensores.get('rssi_dbm', -70),
            rayos_detectados=sensores.get('rayos_detectados', 0)
        )
        
        resultado['vector_aproximacion'] = vector_result
        
        # 4. Nivel de alerta
        distancia = vector_result['distancia_km']
        if distancia < 30:
            nivel_alerta = "🚨 ALERTA ROJA - Inclemencia inmediata"
        elif distancia < 100:
            nivel_alerta = "⚠️ ALERTA NARANJA - Tormenta próxima"
        else:
            nivel_alerta = "✓ VERDE - Sin peligro inmediato"
        
        resultado['nivel_alerta'] = nivel_alerta
        
        # 5. Confianza de predicción
        if vector_result['componentes']['buys_ballot']['severidad_buys_ballot'] == "ALTA":
            confianza = "ALTA"
        else:
            confianza = "MEDIA"
        
        resultado['confianza_prediccion'] = confianza
        
        # 6. Timestamp
        resultado['timestamp'] = datetime.now().isoformat()
        
        return resultado
    
    def comparar_visibilidad_factor_z(self, temperatura_c, presion_hpa, humedad_relativa, tipo_aire):
        """
        Compara visibilidad con y sin Factor Z para dashboard
        """
        return self.bucholtz.comparar_con_sin_factor_z(
            temperatura_c, presion_hpa, humedad_relativa, tipo_aire
        )
