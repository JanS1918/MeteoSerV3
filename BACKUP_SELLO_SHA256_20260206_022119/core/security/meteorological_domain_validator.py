"""
🌍 VALIDADOR DE DOMINIO METEOROLÓGICO

Verifica que una fórmula descubierta sea realmente un índice meteorológico conocido,
bloqueando funciones matemáticas genéricas como scipy.special.erf, numpy.sum(), etc.

Esto previene la entrada de "fórmulas bonitas pero inválidas" como scipy.erf.
"""

import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger("meteoser.meteorological_domain_validator")


class MeteorologicalDomainValidator:
    """
    Verifica que una función sea índice meteorológico CONOCIDO.
    
    Bloquea:
    - scipy.special.erf (función error matemática)
    - numpy.sum (función genérica)
    - math.sqrt (función base)
    - scipy.stats.* (distribuciones estadísticas)
    
    Permite:
    - Índices meteorológicos conocidos
    - Funciones de librerías de MeteoSerV3
    - Funciones custom validadas
    """
    
    # Índices meteorológicos VÁLIDOS
    METEOROLOGICAL_INDICES = {
        # Temperatura
        "temperatura", "temp", "t", "temperature",
        "sensacion_termica", "heat_index", "apparent_temperature",
        "temperatura_virtua", "virtual_temperature",
        "temperatura_potencial", "potential_temperature",
        "temperatura_equivalente", "equivalent_temperature",
        
        # Humedad
        "humedad_relativa", "relative_humidity", "rh",
        "humedad_absoluta", "absolute_humidity",
        "humedad_especifica", "specific_humidity",
        "razon_mezcla", "mixing_ratio",
        "punto_rocio", "dewpoint", "dew_point",
        
        # Presión
        "presion", "pressure", "p", "presion_msl", "sea_level_pressure",
        "presion_vapor", "vapor_pressure", "partial_pressure",
        
        # Viento
        "velocidad_viento", "wind_speed", "u_wind", "v_wind",
        "direccion_viento", "wind_direction",
        "rafagas_viento", "wind_gust",
        "vorticidad", "vorticity",
        
        # Radiación
        "radiacion_solar", "solar_radiation", "shortwave",
        "radiacion_infrarroja", "longwave_radiation",
        "indice_uv", "uv_index", "uvi",
        "irradianza_directa", "direct_irradiance",
        "irradianza_difusa", "diffuse_irradiance",
        
        # Precipitación
        "lluvia", "precipitation", "rain", "prec",
        "nieve", "snow",
        "granizo", "hail",
        
        # Evapotranspiración
        "evapotranspiracion", "evapotranspiration", "et",
        "evaporacion", "evaporation",
        "transpiración", "transpiration",
        
        # Visibilidad
        "visibilidad", "visibility", "vis",
        "coeficiente_extincion", "extinction_coefficient",
        
        # Nubes
        "cobertura_nubosa", "cloud_cover", "cloudiness",
        "altura_nube_base", "cloud_base", "cloud_ceiling",
        "optical_depth", "optical_thickness",
        
        # Índices compuestos
        "indice_calor", "heat_index", "humidex",
        "wind_chill", "sensacion_frio",
        "indice_confort", "comfort_index",
        "indice_discomfort", "discomfort_index",
        
        # UTCI y similares
        "utci", "universal_thermal_climate_index",
        "wet_bulb_temperature", "temperatura_bulbo_humedo",
        "black_globe_temperature", "temperatura_bola_negra",
        
        # Estabilidad
        "numero_richardson", "richardson_number",
        "numero_froude", "froude_number",
        "numero_monin_obukhov", "monin_obukhov_length",
    }
    
    # Librerías BLOQUEADAS (no son índices meteorológicos)
    BLOCKED_LIBRARIES = {
        "scipy.special": {
            "reason": "Funciones matemáticas especiales (erf, gamma, etc)",
            "blocked_functions": ["erf", "gamma", "beta", "polygamma", "zeta"]
        },
        "scipy.stats": {
            "reason": "Distribuciones estadísticas",
            "blocked_functions": ["norm", "t", "f", "chi2"]
        },
        "numpy": {
            "reason": "Funciones genéricas de array",
            "blocked_functions": ["sum", "mean", "std", "var", "max", "min"]
        },
        "math": {
            "reason": "Funciones matemáticas base",
            "blocked_functions": ["sqrt", "sin", "cos", "exp", "log"]
        },
    }
    
    # Librerías PERMITIDAS
    ALLOWED_LIBRARIES = {
        "meteoser", "core", "custom", "local",
        "scipy.constants",  # Constantes físicas OK
        "numpy.constants",  # Constantes OK (no funciones)
    }
    
    def __init__(self):
        self.rejections_log: list = []
        self.acceptances_log: list = []
    
    def validate(self, 
                formula_name: str, 
                source_library: str, 
                source_function: str,
                description: Optional[str] = None) -> Tuple[bool, str]:
        """
        Valida que una fórmula sea índice meteorológico válido.
        
        Args:
            formula_name: Nombre del índice (ej: "sensacion_termica")
            source_library: Librería fuente (ej: "scipy.special")
            source_function: Función específica (ej: "erf")
            description: Descripción opcional
        
        Returns:
            (is_valid, message)
            - is_valid=True: Fórmula PERMITIDA
            - is_valid=False: Fórmula BLOQUEADA
        """
        
        # 1️⃣ VERIFICAR: ¿Es nombre de índice meteorológico?
        formula_normalized = formula_name.lower().replace("-", "_").replace(" ", "_")
        
        if formula_normalized in self.METEOROLOGICAL_INDICES:
            # [OK] Nombre es índice conocido
            
            # 2️⃣ VERIFICAR: ¿De dónde viene?
            if source_library in self.ALLOWED_LIBRARIES:
                # [OK] Viene de librería permitida (meteoser, custom, etc)
                self.acceptances_log.append({
                    "formula": formula_name,
                    "library": source_library,
                    "reason": "Nombre + Librería válidos"
                })
                return True, f"[OK] PERMITIDA: {formula_name} (from {source_library})"
            
            elif source_library in self.BLOCKED_LIBRARIES:
                # [ERROR] Viene de librería bloqueada
                blocked_info = self.BLOCKED_LIBRARIES[source_library]
                self.rejections_log.append({
                    "formula": formula_name,
                    "library": source_library,
                    "function": source_function,
                    "reason": blocked_info["reason"]
                })
                return False, f"[ERROR] BLOQUEADA: {source_library}.{source_function} ({blocked_info['reason']})"
            
            else:
                # [WARNING] Librería desconocida - evaluar por función
                if source_function in ["erf", "gamma", "special"]:
                    return False, f"[ERROR] BLOQUEADA: {source_library}.{source_function} (función matemática, no meteorológica)"
                
                # Por defecto permitir si nombre es válido
                self.acceptances_log.append({
                    "formula": formula_name,
                    "library": source_library,
                    "reason": "Nombre válido, librería sin bloqueo explícito"
                })
                return True, f"[OK] PERMITIDA: {formula_name}"
        
        else:
            # [ERROR] Nombre NO es índice conocido
            
            if source_library in self.BLOCKED_LIBRARIES:
                # Definitivamente bloqueado
                blocked_info = self.BLOCKED_LIBRARIES[source_library]
                self.rejections_log.append({
                    "formula": formula_name,
                    "library": source_library,
                    "function": source_function,
                    "reason": f"NO es índice meteorológico + {blocked_info['reason']}"
                })
                return False, f"[ERROR] BLOQUEADA: {source_library}.{source_function} no es índice meteorológico"
            
            else:
                # [WARNING] Nombre desconocido - evaluar riesgo
                if source_library in ["scipy", "numpy", "math"]:
                    self.rejections_log.append({
                        "formula": formula_name,
                        "library": source_library,
                        "reason": "Nombre desconocido + librería genérica sospechosa"
                    })
                    return False, f"[WARNING] BLOQUEADA: '{formula_name}' NO es índice meteorológico conocido (en {source_library})"
                
                else:
                    # Custom o desconocido - permitir pero marcar
                    self.acceptances_log.append({
                        "formula": formula_name,
                        "library": source_library,
                        "reason": "Nombre desconocido pero librería permitida"
                    })
                    return True, f"[WARNING] PERMITIDA CON ADVERTENCIA: '{formula_name}' no es índice conocido pero librería ({source_library}) es permitida"
    
    def validate_quick(self, formula_name: str) -> bool:
        """Validación rápida: ¿Es nombre de índice meteorológico?"""
        return formula_name.lower().replace("-", "_") in self.METEOROLOGICAL_INDICES
    
    def get_rejection_log(self) -> list:
        """Obtener log de rechazos"""
        return self.rejections_log
    
    def get_acceptance_log(self) -> list:
        """Obtener log de aceptaciones"""
        return self.acceptances_log
    
    def clear_logs(self):
        """Limpiar logs"""
        self.rejections_log = []
        self.acceptances_log = []


# Tests
if __name__ == "__main__":
    validator = MeteorologicalDomainValidator()
    
    # [OK] PERMITIDAS
    print("[OK] PRUEBAS VÁLIDAS:")
    print(validator.validate("sensacion_termica", "core.indices", "sensacion_termica_hardy"))
    print(validator.validate("temperatura", "meteoser", "get_temperature"))
    print(validator.validate("humedad_relativa", "custom", "rh_func"))
    
    # [ERROR] BLOQUEADAS
    print("\n[ERROR] PRUEBAS BLOQUEADAS:")
    print(validator.validate("sensacion_termica", "scipy.special", "erf"))
    print(validator.validate("temperature", "numpy", "sum"))
    print(validator.validate("unknown_func", "scipy.stats", "norm"))
    
    print("\n[STATS] LOG DE RECHAZOS:", len(validator.get_rejection_log()))
    print("[STATS] LOG DE ACEPTACIONES:", len(validator.get_acceptance_log()))
