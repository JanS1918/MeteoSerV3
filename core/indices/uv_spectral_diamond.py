"""
MOTOR DE INTEGRACIÓN ESPECTRAL UV DINÁMICA - MODELO ARGENTONA 2026
====================================================================
Motor de transferencia radiativa avanzado para cálculo de índice UV basado en:
- Beer-Lambert + modelo Fioletov
- Masa óptica angular dinámica
- Índice de claridad Kt
- Ozono estacional (Dobson)
- Correctores atmosféricos (presión, temperatura, VPD, AOD)
- Corrección de altitud
- Resolución de Diamante: 2 decimales si tiene, INT si es 0 o redondo
- UV = 0 absoluto si sol < 2° o radiación < 5 W/m²

Fuente: diamond_spectral_v3
"""

import math
from typing import Optional, Tuple
from datetime import datetime


class UVSpectralDiamond:
    """Motor de cálculo UV con transferencia radiativa completa."""
    
    def __init__(self, lat: float, lon: float, altitud: float = 100.0):
        """
        Args:
            lat: Latitud en grados
            lon: Longitud en grados
            altitud: Altitud en metros sobre el nivel del mar
        """
        self.lat = lat
        self.lon = lon
        self.altitud = altitud
        
    def calcular_uv(self,
                    radiacion_solar: float,
                    elevacion_solar: float,
                    presion_hpa: float,
                    temperatura_c: float,
                    humedad_relativa: float,
                    fecha: Optional[datetime] = None) -> Tuple[float, dict]:
        """
        Calcula el índice UV con modelo de transferencia radiativa completa.
        
        Args:
            radiacion_solar: Radiación solar global en W/m²
            elevacion_solar: Elevación solar en grados
            presion_hpa: Presión barométrica en hPa
            temperatura_c: Temperatura en °C
            humedad_relativa: Humedad relativa en %
            fecha: Fecha actual (para ozono estacional)
            
        Returns:
            Tuple[float, dict]: (índice UV, metadatos con motor y fuente)
        """
        # SUELO DE CALMA: UV = 0 absoluto si sol < 2° o radiación < 5 W/m²
        if elevacion_solar < 2.0 or radiacion_solar < 5.0:
            return 0, {"motor": "Spectral_Diamond_v3", "fuente": "diamond_spectral_v3", "modo": "suelo_calma"}
        
        if fecha is None:
            fecha = datetime.now()
        
        # 1. MASA ÓPTICA ANGULAR (Beer-Lambert)
        masa_optica = self._calcular_masa_optica(elevacion_solar)
        
        # 2. ÍNDICE DE CLARIDAD Kt
        kt = self._calcular_indice_claridad(radiacion_solar, elevacion_solar, fecha)
        
        # 3. OZONO ESTACIONAL (Unidades Dobson)
        ozono_du = self._calcular_ozono_estacional(self.lat, fecha)
        
        # 4. CORRECTORES ATMOSFÉRICOS
        factor_presion = self._corrector_presion(presion_hpa)
        factor_temperatura = self._corrector_temperatura(temperatura_c)
        factor_vapor = self._corrector_vapor(temperatura_c, humedad_relativa)
        factor_aerosoles = self._corrector_aerosoles(temperatura_c, humedad_relativa, kt)
        
        # 5. CORRECCIÓN DE ALTITUD
        factor_altitud = self._corrector_altitud(self.altitud)
        
        # 6. CÁLCULO UV CON TRANSFERENCIA RADIATIVA
        # UV base desde radiación y masa óptica
        uv_base = self._transferencia_radiativa_uv(
            radiacion_solar,
            masa_optica,
            kt,
            ozono_du
        )
        
        # Aplicar correctores atmosféricos y altitud
        uv_final = uv_base * factor_presion * factor_temperatura * factor_vapor * factor_aerosoles * factor_altitud
        
        # LEY DEL ENTERO: 2 decimales si tiene decimales, INT si es 0 o redondo
        if uv_final == 0 or (uv_final == int(uv_final)):
            uv_final = int(uv_final)
        else:
            uv_final = round(uv_final, 2)
        
        metadatos = {
            "motor": "Spectral_Diamond_v3",
            "fuente": "diamond_spectral_v3",
            "modo": "transferencia_radiativa",
            "masa_optica": round(masa_optica, 3),
            "kt": round(kt, 3),
            "ozono_du": round(ozono_du, 1)
        }
        
        return uv_final, metadatos
    
    def _calcular_masa_optica(self, elevacion_solar: float) -> float:
        """
        Calcula la masa óptica atmosférica según el ángulo cenital.
        Modelo de Kasten-Young (1989) mejorado.
        
        m = 1 / [cos(θ_z) + 0.50572 * (96.07995 - θ_z)^(-1.6364)]
        """
        if elevacion_solar >= 90:
            return 1.0
        
        zenith_deg = 90.0 - elevacion_solar
        zenith_rad = math.radians(zenith_deg)
        
        if elevacion_solar > 10:
            # Kasten-Young
            masa = 1.0 / (math.cos(zenith_rad) + 0.50572 * math.pow(96.07995 - zenith_deg, -1.6364))
        else:
            # Para ángulos bajos, aproximación exponencial
            masa = 1.0 / max(0.001, math.cos(zenith_rad))
        
        return masa
    
    def _calcular_indice_claridad(self, radiacion_solar: float, elevacion_solar: float, fecha: datetime) -> float:
        """
        Calcula el índice de claridad Kt = G / G0
        G = Radiación global medida
        G0 = Radiación extraterrestre teórica
        """
        # Constante solar (W/m²)
        solar_constant = 1367.0
        
        # Corrección por distancia Tierra-Sol (día del año)
        dia_anio = fecha.timetuple().tm_yday
        eccentricity_correction = 1.0 + 0.033 * math.cos(2 * math.pi * dia_anio / 365.0)
        
        # Radiación extraterrestre en superficie horizontal
        elevacion_rad = math.radians(elevacion_solar)
        g0 = solar_constant * eccentricity_correction * math.sin(elevacion_rad)
        
        if g0 <= 0:
            return 0.0
        
        kt = radiacion_solar / g0
        
        # Limitar Kt entre 0 y 1
        return max(0.0, min(1.0, kt))
    
    def _calcular_ozono_estacional(self, latitud: float, fecha: datetime) -> float:
        """
        Calcula el espesor de ozono atmosférico (Unidades Dobson) según latitud y fecha.
        Modelo de Van Heuklon (1979) modernizado.
        
        Fórmula empírica basada en observaciones satelitales:
        O3 = A + B*cos(2π*(d - d0)/365) + C*cos(4π*(d - d0)/365)
        
        donde A, B, C dependen de la latitud.
        """
        dia_anio = fecha.timetuple().tm_yday
        lat_rad = math.radians(latitud)
        
        # Coeficientes de Van Heuklon ajustados para cada banda latitudinal
        # Valores actualizados con climatología moderna
        lat_abs = abs(latitud)
        
        if lat_abs < 20:
            # Trópicos
            A = 260.0
            B = 15.0
            C = 5.0
            d0 = 0  # Sin fase estacional pronunciada
        elif lat_abs < 40:
            # Subtrópicos (Argentona está aquí, ~41°N)
            A = 310.0
            B = 35.0 * math.cos(lat_rad)
            C = 10.0
            d0 = 90 if latitud >= 0 else 270
        elif lat_abs < 60:
            # Latitudes medias-altas
            A = 340.0
            B = 50.0 * math.cos(lat_rad)
            C = 15.0
            d0 = 80 if latitud >= 0 else 280
        else:
            # Polares
            A = 320.0
            B = 80.0 * math.cos(lat_rad)
            C = 25.0
            d0 = 70 if latitud >= 0 else 290
        
        # Cálculo según Van Heuklon
        ozono_du = (A + 
                   B * math.cos(2 * math.pi * (dia_anio - d0) / 365.0) +
                   C * math.cos(4 * math.pi * (dia_anio - d0) / 365.0))
        
        # Limitar a valores físicamente posibles
        return max(200.0, min(500.0, ozono_du))
    
    def _corrector_presion(self, presion_hpa: float) -> float:
        """
        Corrector de presión atmosférica real para dispersión de Rayleigh.
        La dispersión de Rayleigh es proporcional a la densidad del aire.
        
        A menor presión → aire menos denso → menos dispersión → más UV
        Factor = (P_real / P_std)^0.5
        
        Modelo moderno: la raíz cuadrada captura mejor la relación no-lineal.
        """
        presion_std = 1013.25  # hPa a nivel del mar (estándar ICAO)
        
        # Relación no-lineal: la dispersión crece con la raíz de la densidad
        factor = math.pow(presion_hpa / presion_std, 0.5)
        
        # Limitar a valores físicos razonables (600-1100 hPa)
        return max(0.75, min(1.05, factor))
    
    def _corrector_temperatura(self, temperatura_c: float) -> float:
        """
        Corrector de temperatura para absorción UV.
        La temperatura afecta ligeramente la absorción del ozono.
        """
        temp_std = 15.0  # °C
        # Efecto muy leve: +1°C aumenta ~0.1% el UV
        return 1.0 + 0.001 * (temperatura_c - temp_std)
    
    def _corrector_vapor(self, temperatura_c: float, humedad_relativa: float) -> float:
        """
        Corrector de vapor de agua (Precipitable Water).
        El vapor de agua absorbe parte del UV.
        """
        # Calcular VPD (Vapor Pressure Deficit)
        es = 6.112 * math.exp(17.67 * temperatura_c / (temperatura_c + 243.5))  # hPa
        ea = es * humedad_relativa / 100.0
        vpd = es - ea
        
        # A mayor VPD (aire más seco), menor absorción de UV
        # Factor entre 0.95 y 1.05
        factor = 1.0 - 0.00005 * ea
        return max(0.95, min(1.05, factor))
    
    def _corrector_altitud(self, altitud_m: float) -> float:
        """
        Corrector de altitud: UV aumenta ~10% cada 1000m.
        """
        return 1.0 + (altitud_m / 1000.0) * 0.10
    
    def _corrector_aerosoles(self, temperatura_c: float, humedad_rel: float, kt: float) -> float:
        """
        Corrección avanzada de aerosoles por humedad: Modelo de Hinds (1999).
        
        Los aerosoles higroscópicos absorben agua y crecen con la humedad,
        aumentando la dispersión y absorción de UV. El crecimiento sigue
        una relación exponencial cerca del 100% RH.
        
        Factor de crecimiento f(RH) = (1 - RH/100)^(-γ)
        donde γ es el exponente de Hänel (típicamente 0.4-0.6 para aerosoles continentales)
        
        Referencias:
        - Hinds, W.C. (1999). Aerosol Technology
        - Kasten, F. (1969). Visibility forecast in the phase of pre-condensation
        """
        # Humedad relativa normalizada [0-1]
        rh = max(0.0, min(100.0, humedad_rel)) / 100.0
        
        # Exponente de Hänel para aerosoles continentales marinos
        gamma = 0.45
        
        # Factor de crecimiento higroscópico (diverge cerca del 100% RH)
        if rh < 0.95:
            crecimiento = math.pow(1.0 - rh, -gamma)
        else:
            # Limitar cerca de saturación para evitar divergencia
            crecimiento = math.pow(0.05, -gamma)
        
        # Normalizar a RH=50% como referencia (crecimiento=1.0 a 50% RH)
        crecimiento_ref = math.pow(0.5, -gamma)
        factor_crecimiento = crecimiento / crecimiento_ref
        
        # Profundidad óptica base de aerosoles (AOD) típica: 0.1-0.3
        # Ajustamos por temperatura (inversión térmica aumenta AOD)
        aod_base = 0.15
        if temperatura_c > 25:
            aod_base *= 1.2  # Más aerosoles en días calurosos
        elif temperatura_c < 5:
            aod_base *= 0.8  # Menos aerosoles en días fríos
        
        # Ajuste por claridad atmosférica (Kt bajo = más aerosoles)
        aod_base *= (1.0 + 0.5 * (1.0 - kt))
        
        # Transmitancia de aerosoles con crecimiento higroscópico
        # T_aerosol = exp(-AOD * factor_crecimiento)
        tau_aerosol = aod_base * factor_crecimiento
        transmitancia = math.exp(-tau_aerosol)
        
        # Limitar a valores físicos (mínimo 0.5 para días muy brumosos)
        return max(0.5, min(1.0, transmitancia))
    
    def _transferencia_radiativa_uv(self, radiacion_solar: float, masa_optica: float,
                                     kt: float, ozono_du: float) -> float:
        """
        Modelo de transferencia radiativa para UV basado en Beer-Lambert + Fioletov.
        
        UV ≈ (Radiación Solar * Kt * factor_espectral) * exp(-τ * m)
        
        donde:
        - τ (tau) es la profundidad óptica total (ozono + Rayleigh + aerosoles)
        - m es la masa óptica
        - factor_espectral es la proporción de UV en la radiación total
        """
        # Profundidad óptica del ozono (modelo simplificado)
        # τ_ozono ≈ (Ozono_DU / 300) * 0.3
        tau_ozono = (ozono_du / 300.0) * 0.3
        
        # Profundidad óptica de Rayleigh (dispersión molecular)
        tau_rayleigh = 0.15
        
        # Profundidad óptica de aerosoles (turbidez atmosférica)
        # Estimación basada en Kt: si Kt es bajo, hay más aerosoles
        tau_aerosol = (1.0 - kt) * 0.2
        
        # Profundidad óptica total
        tau_total = tau_ozono + tau_rayleigh + tau_aerosol
        
        # Transmitancia atmosférica (Beer-Lambert)
        transmitancia = math.exp(-tau_total * masa_optica)
        
        # Factor espectral: proporción de UV en la radiación solar global
        # Depende de Kt y masa óptica
        # Valores típicos: 3-5% de la radiación solar total es UV
        if kt > 0.7:
            # Cielo claro: mayor proporción de UV
            factor_espectral = 0.045
        elif kt > 0.4:
            # Parcialmente nublado
            factor_espectral = 0.038
        else:
            # Muy nublado
            factor_espectral = 0.030
        
        # Cálculo UV final
        uv = (radiacion_solar * factor_espectral * transmitancia) / 25.0
        
        return max(0.0, uv)


# Instancia global para uso en el sistema
_uv_engine = None


def get_uv_spectral_engine(lat: float = 41.55, lon: float = 2.40, altitud: float = 100.0) -> UVSpectralDiamond:
    """Obtiene o crea la instancia global del motor UV."""
    global _uv_engine
    if _uv_engine is None:
        _uv_engine = UVSpectralDiamond(lat, lon, altitud)
    return _uv_engine
