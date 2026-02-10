"""
🌪️ VALIDACIÓN CRUZADA CO2/PM2.5 - DETECTOR DE COMBUSTIÓN
═══════════════════════════════════════════════════════════════
Lógica de correlación para detectar eventos de combustión vs aire cargado.

ESCENARIOS:
  A) CO2↑ + PM2.5 bajo  → Aire cargado (ventilación recomendada)
  B) CO2↑ + PM2.5↑      → Combustión/Tabaco (alerta máxima)
  C) CO2 normal + PM2.5↑ → Fuente externa de partículas

Metadata: motor: Quantum_Diamond_Persistent_v1.4
═══════════════════════════════════════════════════════════════
"""

import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("indoor_air_validator")


# ════════════════════════════════════════════════════════════════
# UMBRALES DE DETECCIÓN
# ════════════════════════════════════════════════════════════════

class IndoorAirQuality(Enum):
    """Estados de calidad del aire interior."""
    EXCELENTE = "EXCELENTE"
    BUENO = "BUENO"
    ACEPTABLE = "ACEPTABLE"
    AIRE_CARGADO = "AIRE_CARGADO"           # CO2 alto, PM bajo
    CONTAMINADO = "CONTAMINADO"             # PM alto, CO2 normal
    COMBUSTION_CONFIRMADA = "COMBUSTION_CONFIRMADA"  # Ambos altos


# Umbrales físicos basados en ASHRAE y OMS
THRESHOLDS = {
    "co2": {
        "optimo": 400,      # ppm - Aire exterior limpio
        "bueno": 600,       # ppm - Aire interior con ventilación
        "aceptable": 800,   # ppm - Límite confort
        "cargado": 1000,    # ppm - Necesita ventilación
        "malo": 1500,       # ppm - Somnolencia, dolor de cabeza
        "critico": 2000     # ppm - Riesgo para la salud
    },
    "pm25": {
        "optimo": 5,        # µg/m³ - Excelente (OMS 2021)
        "bueno": 15,        # µg/m³ - Bueno
        "aceptable": 25,    # µg/m³ - Moderado
        "malo": 35,         # µg/m³ - Insalubre para grupos sensibles
        "muy_malo": 55,     # µg/m³ - Insalubre
        "peligroso": 150    # µg/m³ - Muy insalubre
    }
}

# Umbrales específicos de COMBUSTIÓN (ajuste v1.4)
COMBUSTION_THRESHOLDS = {
    "co2": 1200,   # ppm
    "pm25": 250    # µg/m3
}


# ════════════════════════════════════════════════════════════════
# CLASIFICADOR DE ESTADO DEL AIRE
# ════════════════════════════════════════════════════════════════

def classify_co2_level(co2_ppm: float) -> Tuple[str, str]:
    """
    Clasifica el nivel de CO2.
    
    Args:
        co2_ppm: Concentración de CO2 en ppm
        
    Returns:
        (nivel, descripcion)
    """
    t = THRESHOLDS["co2"]
    
    if co2_ppm < t["bueno"]:
        return "OPTIMO", "Aire fresco, ventilación excelente"
    elif co2_ppm < t["aceptable"]:
        return "BUENO", "Aire interior con buena ventilación"
    elif co2_ppm < t["cargado"]:
        return "ACEPTABLE", "Ventilación adecuada, pero mejorable"
    elif co2_ppm < t["malo"]:
        return "CARGADO", "Ventilación insuficiente, abrir ventanas"
    elif co2_ppm < t["critico"]:
        return "MALO", "Alta concentración, somnolencia posible"
    else:
        return "CRITICO", "Concentración peligrosa, ventilar urgente"


def classify_pm25_level(pm25_ugm3: float) -> Tuple[str, str]:
    """
    Clasifica el nivel de PM2.5.
    
    Args:
        pm25_ugm3: Concentración de PM2.5 en µg/m³
        
    Returns:
        (nivel, descripcion)
    """
    t = THRESHOLDS["pm25"]
    
    if pm25_ugm3 < t["optimo"]:
        return "OPTIMO", "Calidad del aire excelente"
    elif pm25_ugm3 < t["bueno"]:
        return "BUENO", "Calidad del aire buena"
    elif pm25_ugm3 < t["aceptable"]:
        return "ACEPTABLE", "Calidad moderada"
    elif pm25_ugm3 < t["malo"]:
        return "MALO", "Insalubre para grupos sensibles"
    elif pm25_ugm3 < t["muy_malo"]:
        return "MUY_MALO", "Insalubre para todos"
    elif pm25_ugm3 < t["peligroso"]:
        return "PELIGROSO", "Muy insalubre, activar purificador"
    else:
        return "EXTREMO", "Peligroso, emergencia de calidad del aire"


# ════════════════════════════════════════════════════════════════
# VALIDACIÓN CRUZADA
# ════════════════════════════════════════════════════════════════

def validate_indoor_air_cross(
    co2_ppm: Optional[float],
    pm25_ugm3: Optional[float],
    temperatura_c: Optional[float] = None,
    humedad_pct: Optional[float] = None
) -> Dict[str, Any]:
    """
    Validación cruzada CO2/PM2.5 para detección de eventos.
    
    LÓGICA DE DETECCIÓN:
    
    1. Si ambos son None → Sin datos
    2. Si CO2↑ y PM2.5 bajo → Aire cargado (respiración humana)
    3. Si CO2↑ y PM2.5↑ → Combustión/Tabaco confirmado
    4. Si CO2 normal y PM2.5↑ → Contaminación externa
    5. Si ambos bajos → Excelente
    
    Args:
        co2_ppm: CO2 en ppm (WH45)
        pm25_ugm3: PM2.5 en µg/m³ (WH43/HP2550A)
        temperatura_c: Temperatura interior (opcional)
        humedad_pct: Humedad interior (opcional)
        
    Returns:
        Dict con:
        - estado: IndoorAirQuality
        - flag: String de alerta
        - co2_nivel: Clasificación CO2
        - pm25_nivel: Clasificación PM2.5
        - recomendacion: Acción sugerida
        - score: Puntuación de gravedad (0-100)
        - metadata: Información adicional
    """
    result = {
        "estado": IndoorAirQuality.EXCELENTE,
        "flag": "OK",
        "co2_nivel": None,
        "pm25_nivel": None,
        "co2_descripcion": None,
        "pm25_descripcion": None,
        "recomendacion": "Sin acción necesaria",
        "score": 0,
        "metadata": {
            "motor": "Quantum_Diamond_Persistent_v1.4",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    
    # Si no hay datos, retornar sin información
    if co2_ppm is None and pm25_ugm3 is None:
        result["flag"] = "SIN_DATOS"
        result["recomendacion"] = "Sensores no disponibles"
        return result
    
    # Clasificar niveles individuales
    co2_nivel = None
    pm25_nivel = None
    co2_desc = None
    pm25_desc = None
    
    if co2_ppm is not None:
        co2_nivel, co2_desc = classify_co2_level(co2_ppm)
        result["co2_nivel"] = co2_nivel
        result["co2_descripcion"] = co2_desc
    
    if pm25_ugm3 is not None:
        pm25_nivel, pm25_desc = classify_pm25_level(pm25_ugm3)
        result["pm25_nivel"] = pm25_nivel
        result["pm25_descripcion"] = pm25_desc
    
    # ═══════════════════════════════════════════════════════════
    # LÓGICA DE VALIDACIÓN CRUZADA
    # ═══════════════════════════════════════════════════════════
    
    # Caso 1: Ambos sensores disponibles (el más valioso)
    if co2_ppm is not None and pm25_ugm3 is not None:
        # Detección de combustión: usar umbrales estrictos definidos en v1.4
        co2_alto = co2_ppm >= COMBUSTION_THRESHOLDS["co2"]
        pm25_alto = pm25_ugm3 >= COMBUSTION_THRESHOLDS["pm25"]
        
        if co2_alto and pm25_alto:
            # COMBUSTIÓN CONFIRMADA (tabaco, incienso, cocina)
            result["estado"] = IndoorAirQuality.COMBUSTION_CONFIRMADA
            result["flag"] = "EVENTO_COMBUSTION_CONFIRMADO"
            result["recomendacion"] = "[WARNING] COMBUSTIÓN DETECTADA: Ventilar urgente, activar extractor"
            result["score"] = min(100, int(co2_ppm / 20 + pm25_ugm3))
            logger.warning(f"🔥 COMBUSTIÓN CONFIRMADA: CO2={co2_ppm}ppm, PM2.5={pm25_ugm3}µg/m³")
            
        elif co2_alto and not pm25_alto:
            # AIRE CARGADO (respiración humana sin combustión)
            result["estado"] = IndoorAirQuality.AIRE_CARGADO
            result["flag"] = "AIRE_CARGADO_RESPIRACION"
            result["recomendacion"] = "💨 Aire cargado por ocupación: Abrir ventanas 5-10 min"
            result["score"] = int(co2_ppm / 30)
            logger.info(f"💨 AIRE CARGADO: CO2={co2_ppm}ppm, PM2.5={pm25_ugm3}µg/m³")
            
        elif not co2_alto and pm25_alto:
            # PARTÍCULAS SIN COMBUSTIÓN (contaminación externa, polen)
            result["estado"] = IndoorAirQuality.CONTAMINADO
            result["flag"] = "PARTICULAS_EXTERNAS"
            result["recomendacion"] = "[PARTICULAS] Partículas externas: Cerrar ventanas, activar purificador"
            result["score"] = int(pm25_ugm3)
            logger.info(f"[PARTICULAS] PARTÍCULAS EXTERNAS: CO2={co2_ppm}ppm, PM2.5={pm25_ugm3}µg/m³")
            
        else:
            # AMBOS BAJOS = EXCELENTE
            if co2_ppm < THRESHOLDS["co2"]["bueno"] and pm25_ugm3 < THRESHOLDS["pm25"]["bueno"]:
                result["estado"] = IndoorAirQuality.EXCELENTE
                result["flag"] = "AIRE_EXCELENTE"
                result["recomendacion"] = "[OK] Calidad del aire óptima"
                result["score"] = 0
            else:
                result["estado"] = IndoorAirQuality.ACEPTABLE
                result["flag"] = "AIRE_ACEPTABLE"
                result["recomendacion"] = "Calidad del aire aceptable"
                result["score"] = int((co2_ppm / 40 + pm25_ugm3) / 2)
    
    # Caso 2: Solo CO2 disponible
    elif co2_ppm is not None:
        if co2_ppm >= THRESHOLDS["co2"]["malo"]:
            result["estado"] = IndoorAirQuality.AIRE_CARGADO
            result["flag"] = "CO2_ALTO_SIN_PM25"
            result["recomendacion"] = "CO2 elevado: Ventilar"
            result["score"] = int(co2_ppm / 30)
        elif co2_ppm < THRESHOLDS["co2"]["bueno"]:
            result["estado"] = IndoorAirQuality.EXCELENTE
            result["flag"] = "OK"
            result["score"] = 0
        else:
            result["estado"] = IndoorAirQuality.ACEPTABLE
            result["flag"] = "OK"
            result["score"] = int(co2_ppm / 40)
    
    # Caso 3: Solo PM2.5 disponible
    elif pm25_ugm3 is not None:
        if pm25_ugm3 >= THRESHOLDS["pm25"]["malo"]:
            result["estado"] = IndoorAirQuality.CONTAMINADO
            result["flag"] = "PM25_ALTO_SIN_CO2"
            result["recomendacion"] = "PM2.5 elevado: Activar purificador"
            result["score"] = int(pm25_ugm3)
        elif pm25_ugm3 < THRESHOLDS["pm25"]["bueno"]:
            result["estado"] = IndoorAirQuality.EXCELENTE
            result["flag"] = "OK"
            result["score"] = 0
        else:
            result["estado"] = IndoorAirQuality.ACEPTABLE
            result["flag"] = "OK"
            result["score"] = int(pm25_ugm3 / 2)
    
    # Añadir contexto de temperatura/humedad si disponible
    if temperatura_c is not None and humedad_pct is not None:
        result["metadata"]["temperatura_interior"] = temperatura_c
        result["metadata"]["humedad_interior"] = humedad_pct
        
        # Ajustar recomendación si hay condensación (humedad >70%)
        if humedad_pct > 70 and co2_ppm is not None and co2_ppm > THRESHOLDS["co2"]["cargado"]:
            result["recomendacion"] += " + Humedad alta: Ventilar para evitar moho"
    
    return result


# ════════════════════════════════════════════════════════════════
# INTEGRACIÓN CON STATISTICAL BRAIN
# ════════════════════════════════════════════════════════════════

def add_cross_validation_to_brain_results(
    brain_results: Dict[str, Any],
    sensor_values: Dict[str, float]
) -> Dict[str, Any]:
    """
    Añade validación cruzada CO2/PM2.5 a los resultados del cerebro.
    
    Args:
        brain_results: Resultados de StatisticalBrain.ingest()
        sensor_values: Valores actuales de sensores
        
    Returns:
        brain_results actualizado con campo "indoor_air_quality"
    """
    co2 = sensor_values.get("co2")
    pm25 = sensor_values.get("pm25") or sensor_values.get("pm25_interior")
    temperatura = sensor_values.get("temperatura_interior") or sensor_values.get("tempinf")
    humedad = sensor_values.get("humedad_interior") or sensor_values.get("humidityin")
    
    validation = validate_indoor_air_cross(co2, pm25, temperatura, humedad)
    
    brain_results["indoor_air_quality"] = validation
    
    # Si hay combustión confirmada, añadir flag de alta prioridad
    if validation["estado"] == IndoorAirQuality.COMBUSTION_CONFIRMADA:
        brain_results["flags"]["COMBUSTION_CONFIRMADA"] = validation["flag"]
        brain_results["scores"]["indoor_air_danger"] = validation["score"]
    
    return brain_results
