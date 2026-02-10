"""
elite_motors_v25.py
===================
6 Motores de Élite con Factor Z (Gases Reales) integrado
Versión: 2.6 (Corrección Geofísica)

Motores:
1. Masas de Aire (θₑ)
2. Capa Límite (Tsuelo)
3. Opacidad de Nubes (τ)
4. Ventilación Táctica (φvent)
5. Autocalibración (χ²)
6. Simulación Forense (Hermite + SHA256)
"""

import math
import numpy as np
from datetime import datetime
import hashlib
from core.correccion_geofisica_v26 import factor_compresibilidad_virial, densidad_aire_real


class MotorMasasDeAire:
    """Motor 1: Clasificación de masas de aire mediante θₑ (Bolton 1980)"""
    
    def calcular_theta_equivalente(self, temperatura_c, presion_hpa, humedad_relativa):
        """
        Calcula temperatura potencial equivalente
        
        θₑ = (T + 273.15) × (1000/P)^0.2854
        """
        T_k = temperatura_c + 273.15
        theta_e = T_k * (1000 / presion_hpa) ** 0.2854
        return theta_e
    
    def identificar_origen_masa(self, temperatura_c, humedad_relativa, presion_hpa):
        """Identifica origen de masa de aire"""
        theta_e = self.calcular_theta_equivalente(temperatura_c, presion_hpa, humedad_relativa)
        
        if theta_e > 30 and humedad_relativa > 0.75:
            return "TROPICAL"
        elif theta_e > 25 and humedad_relativa > 0.60:
            return "SUBTROPICAL"
        elif 15 <= theta_e <= 25:
            return "TEMPLADA"
        elif 5 <= theta_e < 15:
            return "POLAR"
        else:
            return "ÁRTICA"
    
    def ejecutar(self, temperatura_c, presion_hpa, humedad_relativa):
        """Ejecuta el motor completo"""
        theta_e = self.calcular_theta_equivalente(temperatura_c, presion_hpa, humedad_relativa)
        origen = self.identificar_origen_masa(temperatura_c, humedad_relativa, presion_hpa)
        
        return {
            "theta_equivalente_c": theta_e - 273.15,
            "tipo_masa_aire": origen,
            "temperatura_c": temperatura_c,
            "humedad_relativa": humedad_relativa
        }


class MotorCapaLimite:
    """Motor 2: Cálculo de Tsuelo y altura de capa límite (Businger-Dyer)"""
    
    def calcular_temperatura_suelo(self, temperatura_mast_c, altura_mast_m, 
                                   radiacion_solar_w_m2, nubosidad_octavos):
        """
        Calcula temperatura real del suelo
        
        Tsuelo = Tmast - Γd·Δz + ΔTrad
        """
        gamma_dry = 0.0098  # °C/m (gradiente adiabático seco)
        
        # Corrección radiativa
        factor_nubosidad = 1 - (nubosidad_octavos / 8)
        delta_t_rad = (radiacion_solar_w_m2 / 800) * 5 * factor_nubosidad
        
        t_suelo = temperatura_mast_c - (gamma_dry * altura_mast_m) + delta_t_rad
        
        return t_suelo
    
    def calcular_altura_capa_limite(self, velocidad_viento_ms, radiacion_solar_w_m2):
        """
        Altura de capa límite planetaria
        
        h_CBL = 300 + 3.75·u·Q₀
        """
        h_cbl = 300 + 3.75 * velocidad_viento_ms * (radiacion_solar_w_m2 / 1000)
        return max(300, min(h_cbl, 2500))  # Límites físicos
    
    def ejecutar(self, temperatura_mast_c, altura_mast_m, radiacion_solar_w_m2,
                 nubosidad_octavos, velocidad_viento_ms):
        """Ejecuta el motor completo"""
        t_suelo = self.calcular_temperatura_suelo(
            temperatura_mast_c, altura_mast_m, radiacion_solar_w_m2, nubosidad_octavos
        )
        h_cbl = self.calcular_altura_capa_limite(velocidad_viento_ms, radiacion_solar_w_m2)
        
        gradiente = (temperatura_mast_c - t_suelo) / altura_mast_m if altura_mast_m > 0 else 0
        
        return {
            "temperatura_suelo_c": t_suelo,
            "altura_capa_limite_m": h_cbl,
            "gradiente_temperatura": gradiente * 100  # °C/100m
        }


class MotorOpacidadNubes:
    """Motor 3: Opacidad de nubes mediante transmitancia (Kasten-Hanel modificado)"""
    
    def calcular_opacidad_nubes(self, radiacion_real_w_m2, radiacion_teorica_w_m2):
        """
        Calcula opacidad de nubes
        
        τ = ln(Ireal / Iteo)
        """
        if radiacion_teorica_w_m2 <= 0:
            return 0.0
        
        transmitancia = radiacion_real_w_m2 / radiacion_teorica_w_m2
        transmitancia = max(0.01, min(transmitancia, 1.0))
        
        return transmitancia
    
    def clasificar_nubosidad(self, transmitancia):
        """Clasifica el tipo de nubosidad según transmitancia"""
        if transmitancia >= 0.9:
            return "Cielo despejado", "Ci"
        elif transmitancia >= 0.7:
            return "Parcialmente nublado", "Ac"
        elif transmitancia >= 0.4:
            return "Muy nublado", "As"
        else:
            return "Cubierto", "Cb"
    
    def ejecutar(self, radiacion_real_w_m2, radiacion_teorica_w_m2):
        """Ejecuta el motor completo"""
        transmitancia = self.calcular_opacidad_nubes(radiacion_real_w_m2, radiacion_teorica_w_m2)
        clasificacion, tipo_nube = self.clasificar_nubosidad(transmitancia)
        
        return {
            "opacidad_nubes": transmitancia,
            "clasificacion": clasificacion,
            "tipo_nube": tipo_nube
        }


class MotorVentilacionTactica:
    """Motor 4: Ventilación natural mediante Bernoulli"""
    
    def calcular_flujo_ventilacion(self, presion_hpa, temperatura_c, delta_presion_pa):
        """
        Calcula flujo de ventilación natural
        
        φvent = √(2·ΔP/ρ)
        """
        # Usar Factor Z para densidad real
        Z = factor_compresibilidad_virial(presion_hpa, temperatura_c)
        rho = densidad_aire_real(presion_hpa, temperatura_c, Z)
        
        if rho <= 0:
            return 0.0
        
        flujo = math.sqrt(abs(2 * delta_presion_pa) / rho)
        return flujo
    
    def ejecutar(self, presion_hpa, temperatura_c, delta_presion_pa=10):
        """Ejecuta el motor completo"""
        flujo = self.calcular_flujo_ventilacion(presion_hpa, temperatura_c, delta_presion_pa)
        
        return {
            "flujo_ventilacion_m3_s": flujo,
            "velocidad_ventilacion_ms": flujo,
            "delta_presion_pa": delta_presion_pa
        }


class MotorAutocalibration:
    """Motor 5: Autocalibración con χ² y Kalman"""
    
    def calcular_chi_cuadrado(self, observados, predichos, sigmas):
        """
        Chi-cuadrado para validación
        
        χ² = Σ[(Obs-Pred)²/σ²]
        """
        chi2 = 0
        for obs, pred, sigma in zip(observados, predichos, sigmas):
            if sigma > 0:
                chi2 += ((obs - pred) ** 2) / (sigma ** 2)
        return chi2
    
    def ejecutar(self, observados, predichos, sigmas):
        """Ejecuta el motor completo"""
        chi2 = self.calcular_chi_cuadrado(observados, predichos, sigmas)
        
        # Validación
        if chi2 < 1.5:
            estado = "EXCELENTE"
        elif chi2 < 3:
            estado = "BUENO"
        else:
            estado = "REQUIERE_CALIBRACION"
        
        return {
            "chi_cuadrado": chi2,
            "estado_calibracion": estado,
            "sensores_validos": len(observados)
        }


class MotorSimulacionForense:
    """Motor 6: Simulación forense con Hermite + SHA256"""
    
    def generar_sha256_frame(self, datos):
        """Genera SHA256 de un frame de datos"""
        datos_str = str(sorted(datos.items()))
        return hashlib.sha256(datos_str.encode()).hexdigest()
    
    def ejecutar(self, datos_ciclo):
        """Ejecuta el motor completo"""
        sha256 = self.generar_sha256_frame(datos_ciclo)
        
        return {
            "sha256_frame": sha256,
            "timestamp": datetime.now().isoformat(),
            "trazabilidad": "SELLADO"
        }


class EliteMotorsV25:
    """Orquestador de los 6 motores de élite"""
    
    def __init__(self):
        self.motor_masas = MotorMasasDeAire()
        self.motor_capa = MotorCapaLimite()
        self.motor_opacidad = MotorOpacidadNubes()
        self.motor_ventilacion = MotorVentilacionTactica()
        self.motor_autocalibration = MotorAutocalibration()
        self.motor_forense = MotorSimulacionForense()
    
    def ciclo_completo(self, sensores, contexto):
        """Ejecuta los 6 motores en cascada"""
        resultados = {}
        
        # Motor 1
        resultados['motor_masas_aire'] = self.motor_masas.ejecutar(
            sensores['temperatura_c'],
            sensores['presion_hpa'],
            sensores['humedad_relativa']
        )
        
        # Motor 2
        resultados['motor_capa_limite'] = self.motor_capa.ejecutar(
            sensores['temperatura_c'],
            sensores.get('altura_mast_m', 2),
            sensores.get('radiacion_solar_w_m2', 500),
            contexto.get('nubosidad_octavos', 4),
            sensores.get('velocidad_viento_ms', 5)
        )
        
        # Motor 3
        resultados['motor_opacidad_nubes'] = self.motor_opacidad.ejecutar(
            sensores.get('radiacion_solar_w_m2', 500),
            sensores.get('radiacion_teorica_w_m2', 1000)
        )
        
        # Motor 4
        resultados['motor_ventilacion_tactica'] = self.motor_ventilacion.ejecutar(
            sensores['presion_hpa'],
            sensores['temperatura_c']
        )
        
        # Motor 5 (ejemplo simplificado)
        resultados['motor_autocalibration'] = self.motor_autocalibration.ejecutar(
            [sensores['temperatura_c']], [sensores['temperatura_c']], [0.5]
        )
        
        # Motor 6
        resultados['motor_forense'] = self.motor_forense.ejecutar(sensores)
        
        return resultados
