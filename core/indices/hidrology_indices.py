"""
Módulo de Hidrología: Infiltración, Escorrentía, SPI (Índice Estandarizado de Precipitación)
═════════════════════════════════════════════════════════════════════════════════════════

Sin sensores adicionales: estima con T, Lluvia acumulada, ET0
"""

import math
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from statistics import mean, stdev
import json

logger = logging.getLogger("hidrology_indices")


class InfiltracionEscorrentia:
    """
    Modelo Green-Ampt simplificado para infiltración y escorrentía.
    Parámetros según tipo de suelo sin sensor WH51.
    """
    
    # Parámetros por tipo suelo (estimados de HR y T tendencia)
    SOIL_PARAMS = {
        "arenoso": {
            "Ks": 25.0,      # conductividad saturada (mm/h)
            "S": 110.0,      # absorción capilar (mm)
            "theta_s": 0.43,  # porosidad
            "theta_r": 0.04,  # humedad residual
        },
        "franco": {
            "Ks": 6.0,
            "S": 150.0,
            "theta_s": 0.45,
            "theta_r": 0.08,
        },
        "arcilloso": {
            "Ks": 0.3,
            "S": 210.0,
            "theta_s": 0.47,
            "theta_r": 0.12,
        },
    }
    
    def __init__(self, lluvia_24h: float, lluvia_rate: Optional[float], 
                 humedad_relativa: float, temperatura: float,
                 pendiente_terreno_pct: float = 5.0):
        """
        lluvia_24h: mm acumulado en 24h
        lluvia_rate: mm/h actual
        humedad_relativa: % (0-100)
        temperatura: °C
        pendiente_terreno_pct: pendiente del terreno (defecto 5%)
        """
        self.lluvia_24h = lluvia_24h or 0.0
        self.lluvia_rate = lluvia_rate or 0.0
        self.humedad_relativa = humedad_relativa
        self.temperatura = temperatura
        self.pendiente = pendiente_terreno_pct / 100.0
        
        self.soil_type = self._estimar_tipo_suelo()
        self.params = self.SOIL_PARAMS[self.soil_type]
    
    def _estimar_tipo_suelo(self) -> str:
        """
        Estima tipo de suelo por HR y T.
        - HR > 75% + T tendencia -ve → arcilloso (retiene agua)
        - HR 40-75% → franco (equilibrado)
        - HR < 40% → arenoso (drena rápido)
        """
        if self.humedad_relativa > 75:
            return "arcilloso"
        elif self.humedad_relativa < 40:
            return "arenoso"
        else:
            return "franco"
    
    def infiltracion_mm_h(self) -> float:
        """
        Infiltración máxima en mm/h usando Green-Ampt simplificado.
        f(t) = Ks * (1 + S*θ_s / cumulative_infiltration)
        """
        Ks = self.params["Ks"]
        S = self.params["S"]
        theta_s = self.params["theta_s"]
        
        if self.lluvia_24h <= 0:
            return Ks  # Sin lluvia, infiltración máxima
        
        # Infiltración acumulada aproximada (iteración simple)
        F = min(self.lluvia_24h, Ks * 24)  # máximo en 24h
        
        if F > 0:
            f_t = Ks * (1.0 + (S * theta_s / F))
        else:
            f_t = Ks
        
        return max(0.1, min(f_t, Ks * 1.5))  # sin exceder 1.5*Ks
    
    def escorrentia_mm_h(self) -> float:
        """
        Escorrentía = lluvia_rate - infiltración
        Si lluvia_rate > infiltración, hay escorrentía.
        """
        inf = self.infiltracion_mm_h()
        escorr = max(0.0, self.lluvia_rate - inf)
        return escorr
    
    def flujo_surficial_coef(self) -> float:
        """
        Coeficiente de escorrentía (0-1) según pendiente y tipo suelo.
        C = (pendiente_factor) * (impermeabilidad_factor)
        """
        # Factor pendiente (mayor pendiente = mayor escorrentía)
        pendiente_factor = min(1.0, self.pendiente * 10.0)
        
        # Factor impermeabilidad por tipo suelo
        impermeab = {
            "arenoso": 0.2,
            "franco": 0.4,
            "arcilloso": 0.7,
        }
        imp_factor = impermeab.get(self.soil_type, 0.4)
        
        # Ajuste por HR (si muy saturado, escorrentía aumenta)
        hr_factor = 1.0 + (max(0, self.humedad_relativa - 75) / 25.0)
        
        C = pendiente_factor * imp_factor * hr_factor
        return min(1.0, C)
    
    def obtener_resultado(self) -> Dict[str, float]:
        """Retorna dict con infiltración, escorrentía y coef de escorrentía."""
        return {
            "infiltracion_mm_h": round(self.infiltracion_mm_h(), 2),
            "escorrentia_mm_h": round(self.escorrentia_mm_h(), 2),
            "coef_escorrentia": round(self.flujo_superficial_coef(), 3),
            "tipo_suelo_estimado": self.soil_type,
        }


class SPICalculator:
    """
    Standardized Precipitation Index (SPI)
    Indica sequía/inundación estandarizada en 3, 6, 12 meses.
    
    SPI > +2.0: Extremadamente húmedo
    SPI > +1.5: Muy húmedo
    SPI > +1.0: Húmedo
    -1.0 < SPI < +1.0: Normal
    SPI < -1.0: Seco
    SPI < -1.5: Muy seco
    SPI < -2.0: Extremadamente seco
    """
    
    def __init__(self):
        self.historical_data = {}
    
    def agregar_dato(self, fecha: datetime, lluvia_mm: float):
        """Agrega dato histórico de lluvia."""
        fecha_str = fecha.strftime("%Y-%m-%d")
        self.historical_data[fecha_str] = lluvia_mm
    
    def cargar_desde_archivo(self, ruta_json: str):
        """Carga histórico de lluvia desde JSON."""
        try:
            with open(ruta_json, 'r') as f:
                self.historical_data = json.load(f)
        except Exception as e:
            logger.warning(f"No se pudo cargar histórico SPI: {e}")
    
    def _accumular_ventanas(self, window_meses: int) -> List[float]:
        """
        Acumula lluvia en ventanas de N meses.
        Retorna lista de precipitaciones acumuladas para cada ventana.
        """
        if not self.historical_data:
            return []
        
        fechas_sorted = sorted(self.historical_data.keys())
        acumulados = []
        
        for i in range(len(fechas_sorted) - window_meses + 1):
            ventana = fechas_sorted[i:i+window_meses]
            acum = sum(self.historical_data.get(f, 0) for f in ventana)
            acumulados.append(acum)
        
        return acumulados
    
    def calcular_spi(self, window_meses: int = 3) -> Optional[float]:
        """
        Calcula SPI para una ventana de meses.
        SPI = (P - media) / desv_std
        """
        acumulados = self._accumular_ventanas(window_meses)
        
        if len(acumulados) < 2:
            logger.warning(f"Datos insuficientes para SPI-{window_meses}")
            return None
        
        try:
            media = mean(acumulados)
            desv = stdev(acumulados)
        except Exception as e:
            logger.error(f"Error calculando SPI: {e}")
            return None
        
        if desv == 0:
            return 0.0
        
        # SPI actual = (últimas ventana - media) / desv
        p_actual = acumulados[-1]
        spi = (p_actual - media) / desv
        
        return round(spi, 2)
    
    def clasificar_spi(self, spi: float) -> str:
        """Clasifica el SPI según estándar."""
        if spi >= 2.0:
            return "Extremadamente húmedo"
        elif spi >= 1.5:
            return "Muy húmedo"
        elif spi >= 1.0:
            return "Húmedo"
        elif spi >= -1.0:
            return "Normal"
        elif spi >= -1.5:
            return "Seco"
        elif spi >= -2.0:
            return "Muy seco"
        else:
            return "Extremadamente seco"
    
    def obtener_resultados(self) -> Dict[str, Any]:
        """Retorna SPI para 3, 6, 12 meses."""
        resultados = {}
        
        for window in [3, 6, 12]:
            spi = self.calcular_spi(window)
            if spi is not None:
                resultados[f"spi_{window}m"] = spi
                resultados[f"categoria_spi_{window}m"] = self.clasificar_spi(spi)
        
        return resultados


def calcular_infiltracion_escorrentia(
    lluvia_24h: float,
    lluvia_rate: Optional[float],
    humedad_relativa: float,
    temperatura: float,
    pendiente_terreno_pct: float = 5.0
) -> Dict[str, Any]:
    """
    Función envolvente para calcular infiltración y escorrentía.
    
    Args:
        lluvia_24h: Lluvia acumulada en 24h (mm)
        lluvia_rate: Intensidad actual de lluvia (mm/h)
        humedad_relativa: Humedad relativa (%)
        temperatura: Temperatura (°C)
        pendiente_terreno_pct: Pendiente estimada del terreno (%)
    
    Returns:
        Dict con infiltración (mm/h), escorrentía (mm/h), coef_escorrentía, tipo_suelo
    """
    calc = InfiltracionEscorrentia(
        lluvia_24h=lluvia_24h,
        lluvia_rate=lluvia_rate,
        humedad_relativa=humedad_relativa,
        temperatura=temperatura,
        pendiente_terreno_pct=pendiente_terreno_pct
    )
    return calc.obtener_resultado()


def calcular_spi_batch(
    historico_lluvia: Dict[str, float],
    windows: List[int] = [3, 6, 12]
) -> Dict[str, Any]:
    """
    Calcula SPI para múltiples ventanas.
    
    Args:
        historico_lluvia: Dict {fecha_str: lluvia_mm}
        windows: Lista de ventanas a calcular (meses)
    
    Returns:
        Dict con SPI y clasificaciones para cada ventana
    """
    calc = SPICalculator()
    for fecha_str, lluvia in historico_lluvia.items():
        try:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            calc.agregar_dato(fecha, lluvia)
        except ValueError:
            logger.warning(f"Formato de fecha inválido: {fecha_str}")
    
    resultados = {}
    for window in windows:
        spi = calc.calcular_spi(window)
        if spi is not None:
            resultados[f"spi_{window}m"] = spi
            resultados[f"categoria_spi_{window}m"] = calc.clasificar_spi(spi)
    
    return resultados
