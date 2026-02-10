"""
CONFIGURACIÓN CENTRALIZADA DE DOMINIOS - v8 MeteoSerV3

Propósito: Centralizar TODOS los parámetros configurables (pesos, rangos, límites)
en un único lugar para facilitar mantenimiento, A/B testing y auditoría.

Fecha: 10 de febrero de 2026
Versión: 1.0
"""

# ============================================================================
# PESOS DE ÍNDICES SINTÉTICOS (configurables por dominio)
# ============================================================================

PESOS_INDICES = {
    "riego": {
        "balance_hidrico": 0.25,
        "et0_fao56": 0.25,
        "estres_cultivo": 0.20,
        "disponibilidad_agua": 0.20,
        "eficiencia_infiltracion": 0.10,
        "descripcion": "Pesos FAO-56 estándar para índice riego sintético"
    },
    
    "astronomia": {
        "observacion_nocturna": 0.30,
        "clearness_index": 0.25,
        "visibilidad_noche": 0.20,
        "fase_lunar": -0.25,  # Negativo porque penaliza (luna llena = mal)
        "descripcion": "Pesos NREL SPA para índice astronomía sintético"
    },
    
    "salud": {
        "uvi_personal": 0.20,  # Bajo peso, es importante pero no dominante
        "calor_extremo": 0.20,
        "frio_extremo": 0.20,
        "helada_riesgo": 0.15,
        "aire_interior": 0.15,
        "aire_exterior": 0.10,
        "descripcion": "Pesos OMS/ASHRAE para índice salud sintético"
    },
    
    "hidrologia": {
        "infiltracion": 0.25,
        "escorrentia": 0.25,
        "spi_indice": 0.25,
        "humedad_suelo_tendencia": 0.25,
        "descripcion": "Pesos WMO SPI para índice hidrología sintético"
    }
}

# ============================================================================
# RANGOS ÓPTIMOS POR DOMINIO
# ============================================================================

RANGOS_OPTIMOS = {
    "riego": {
        "lluvia_ideal_24h_mm": (5, 25),      # 5-25mm es bueno
        "humedad_suelo_optima": (40, 80),    # % capacidad de campo
        "et0_maxima_mm_dia": 8.0,            # Máxima evapotranspiración
    },
    
    "astronomia": {
        "elevacion_solar_minima": -18,       # Noche astronómica (<-18°)
        "claridad_minima": 0.7,              # Kt > 0.7 es despejado
        "visibilidad_minima_km": 10,         # >10km es buena visibilidad
        "fase_lunar_maxima": 0.2,            # Luna nueva o casi nueva
    },
    
    "salud": {
        "temperatura_ideal": (20, 26),       # Rango confortable °C
        "humedad_ideal": (40, 60),           # Rango confortable %
        "uv_limite_seguro": 8,               # UVI > 8 es riesgo
        "calor_critico_temp": 35,            # T > 35°C es crítico
        "frio_critico_temp": -5,             # T < -5°C es crítico
        "visibilidad_minima_km": 5,          # <5km indica contaminación
    },
    
    "hidrologia": {
        "infiltracion_optima_mm_h": (5, 20), # 5-20 mm/h es normal
        "escorrentia_critica": 60,           # >60 = riesgo inundación
        "spi_sequia": -1.5,                  # SPI < -1.5 = sequía extrema
        "spi_lluvia_extrema": 1.5,           # SPI > 1.5 = lluvia extrema
    }
}

# ============================================================================
# UMBRALES DE ALERTAS Y RECOMENDACIONES
# ============================================================================

UMBRALES_RECOMENDACIONES = {
    "cetreria": {
        "threshold_si": 55,
        "alerta_critica": 20,  # <20 = no volar bajo ninguna circunstancia
    },
    
    "lluvia": {
        "threshold_si": 50,
        "alerta_inminente": 75,  # >75 = lluvia muy probable
        "alerta_tormenta": 85,   # >85 = tormenta eléctrica probable
    },
    
    "deporte": {
        "threshold_si": 60,
        "alerta_critica": 30,
    },
    
    "confort": {
        "threshold_si": 65,
        "alerta_discomfort": 40,
    },
    
    "riego": {
        "threshold_si": 60,
        "alerta_sequia": 30,      # <30 = riego urgente
        "alerta_saturacion": 90,  # >90 = no regar
    },
    
    "astronomia": {
        "threshold_si": 70,
        "alerta_mala": 30,
    },
    
    "salud": {
        "threshold_si": 70,
        "alerta_critica_calor": 25,
        "alerta_critica_frio": 25,
    },
    
    "hidrologia": {
        "threshold_si": 60,
        "alerta_inundacion": 70,  # >70 = riesgo inundación
        "alerta_sequia": 30,      # <30 = riesgo sequía
    }
}

# ============================================================================
# CONFIGURACIÓN DE LOGGING Y PERFORMANCE
# ============================================================================

LOGGING_CONFIG = {
    "enabled": True,
    "log_level": "DEBUG",  # DEBUG, INFO, WARNING, ERROR
    "log_timing_functions": True,  # Log timing por función
    "timing_threshold_ms": 10,     # Log solo si > 10ms
    "log_format": "[{dominio:>12}] {funcion:30} {ms:6.1f}ms",
}

# ============================================================================
# METADATA DE VERSIONES (para auditoría)
# ============================================================================

METADATA_VERSIONES = {
    "riego": {
        "version": "2.0",
        "fecha_implementacion": "2026-02-10",
        "referencias": [
            "FAO-56: Crop evapotranspiration (Allen et al., 1998)",
            "Green-Ampt: Soil infiltration model (Green & Ampt, 1911)",
            "USDA: Soil water availability"
        ],
        "cambios_ultimos": "Implementación inicial v8"
    },
    
    "astronomia": {
        "version": "2.0",
        "fecha_implementacion": "2026-02-10",
        "referencias": [
            "NREL SPA: Solar Position Algorithm (Blonquist & Yin, 2006)",
            "Algol: Moon phase calculation (standard algorithm)",
            "ISO 21348: Solar irradiance spectral categories"
        ],
        "cambios_ultimos": "Implementación inicial v8 + NREL SPA"
    },
    
    "salud": {
        "version": "2.0",
        "fecha_implementacion": "2026-02-10",
        "referencias": [
            "OMS/WMO: UV Index and risk categories",
            "ASHRAE 62.1-2019: Ventilation and acceptable indoor air quality",
            "Osczevski & Bluestein: Wind chill temperature (2005)"
        ],
        "cambios_ultimos": "Implementación inicial v8 + OMS UV guidelines"
    },
    
    "hidrologia": {
        "version": "2.0",
        "fecha_implementacion": "2026-02-10",
        "referencias": [
            "WMO: Standardized Precipitation Index (McKee et al., 1993)",
            "Green-Ampt: Soil infiltration model (Green & Ampt, 1911)",
            "FAO: Water balance and drought indicators"
        ],
        "cambios_ultimos": "Implementación inicial v8 + WMO SPI"
    }
}

# ============================================================================
# UTILIDADES
# ============================================================================

def obtener_peso(dominio: str, indice: str) -> float:
    """Obtiene el peso de un índice dentro de un dominio."""
    return PESOS_INDICES.get(dominio, {}).get(indice, 0.0)

def obtener_rango_optimo(dominio: str, parametro: str) -> tuple:
    """Obtiene el rango óptimo para un parámetro en un dominio."""
    return RANGOS_OPTIMOS.get(dominio, {}).get(parametro, (0, 100))

def obtener_threshold_recomendacion(dominio: str) -> int:
    """Obtiene el threshold SÍ/NO para un dominio."""
    return UMBRALES_RECOMENDACIONES.get(dominio, {}).get("threshold_si", 50)

def obtener_version_dominio(dominio: str) -> str:
    """Obtiene la versión de un dominio."""
    return METADATA_VERSIONES.get(dominio, {}).get("version", "1.0")

def obtener_referencias_dominio(dominio: str) -> list:
    """Obtiene las referencias bibliográficas de un dominio."""
    return METADATA_VERSIONES.get(dominio, {}).get("referencias", [])
