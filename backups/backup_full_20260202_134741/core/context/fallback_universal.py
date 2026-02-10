"""
Fallback Universal - Sistema de respaldo y degradación automática.
Arquitectura de Resiliencia: nunca un cálculo se detiene por falta de datos.
"""
import logging
import math
from typing import Any, Dict, Optional, Tuple, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class EstadoFisico(str, Enum):
    """Estados de pureza científica de un dato."""
    REAL = "REAL"              # Dato directo de sensor, sin procesar
    ESTIMADO = "ESTIMADO"      # Dato calculado usando fallback/constantes ISA
    SINTETICO = "SINTÉTICO"    # Dato calculado por degradación de fórmula


class EstadoFisicoBasal:
    """
    Estado Físico Basal - Constantes ISA y valores de referencia.
    Sistema de respaldo cuando los sensores fallan.
    """
    
    # Constantes ISA (International Standard Atmosphere)
    PRESION_ISA = 1013.25  # hPa al nivel del mar
    TEMPERATURA_ISA = 15.0  # °C al nivel del mar
    HUMEDAD_RELATIVA_ISA = 50.0  # %
    VELOCIDAD_VIENTO_ISA = 2.0  # m/s (brisa ligera)
    
    # Constantes de superficie terrestre
    ALBEDO_TIERRA = 0.23  # Albedo promedio global
    EMISIVIDAD_TIERRA = 0.95  # Emisividad superficial
    CONDUCTIVIDAD_SUELO = 0.8  # W/mK para suelo medio
    HUMEDAD_SUELO = 0.25  # Fracción volumétrica media
    
    # Constantes astronómicas
    ELEVACION_SOLAR_DIA = 45.0  # Grados (mediodía aproximado)
    AZIMUTH_SOLAR_SUR = 180.0  # Grados
    
    # Constantes atmosféricas
    COBERTURA_NUBES = 0.5  # Fracción (cielo medio cubierto)
    VISIBILIDAD_ISA = 10000.0  # Metros (10 km)
    
    @classmethod
    def obtener_diccionario_completo(cls) -> Dict[str, float]:
        """Retorna todos los valores basales en un diccionario."""
        return {
            'presion': cls.PRESION_ISA,
            'temperatura': cls.TEMPERATURA_ISA,
            'humedad_relativa': cls.HUMEDAD_RELATIVA_ISA,
            'velocidad_viento': cls.VELOCIDAD_VIENTO_ISA,
            'albedo': cls.ALBEDO_TIERRA,
            'emisividad': cls.EMISIVIDAD_TIERRA,
            'conductividad_suelo': cls.CONDUCTIVIDAD_SUELO,
            'humedad_suelo': cls.HUMEDAD_SUELO,
            'elevacion_solar': cls.ELEVACION_SOLAR_DIA,
            'azimuth_solar': cls.AZIMUTH_SOLAR_SUR,
            'cobertura_nubes': cls.COBERTURA_NUBES,
            'visibilidad': cls.VISIBILIDAD_ISA
        }


class CascadaDegradacion:
    """
    Cascada de Degradación Física.
    Si una fórmula de élite falla, el sistema degrada automáticamente
    a versiones anteriores más estables.
    """
    
    # Cascadas de cálculo psicromérico (saturación de vapor)
    CASCADA_SATURACION = [
        'virial_greenspan',      # Élite: ecuación virial + Greenspan
        'hyland_wexler',         # Intermedio: Hyland-Wexler ASHRAE
    ]
    
    # Cascadas de estabilidad atmosférica
    CASCADA_ESTABILIDAD = [
        'monin_obukhov_zilitinkevich',  # Élite: Monin-Obukhov con Zilitinkevich
        'richardson_bulk',               # Intermedio: Richardson bulk
        'lapse_rate_simple'              # Básico: tasa de lapso simple
    ]
    
    # Cascadas de evapotranspiración
    CASCADA_ET = [
        'shuttleworth_wallace',   # Élite: doble fuente Shuttleworth-Wallace
        'penman_monteith',        # Intermedio: Penman-Monteith FAO-56
        'thornthwaite'            # Básico: Thornthwaite simplificado
    ]
    
    # Cascadas de radiación
    CASCADA_RADIACION = [
        'rayleigh_miller',        # Élite: dispersión Rayleigh-Miller
        'bird_hulstrom',          # Intermedio: Bird-Hulstrom
        'hottel'                  # Básico: Hottel simplificado
    ]
    
    @classmethod
    def obtener_cascada(cls, tipo: str) -> list:
        """Obtiene la cascada de degradación para un tipo de cálculo."""
        cascadas = {
            'saturacion': cls.CASCADA_SATURACION,
            'estabilidad': cls.CASCADA_ESTABILIDAD,
            'et': cls.CASCADA_ET,
            'radiacion': cls.CASCADA_RADIACION
        }
        return cascadas.get(tipo, [])


class FallbackUniversal:
    """
    Fallback Universal - Arquitectura de Resiliencia.
    No acepta None/NaN/Error: siempre produce un valor físico válido.
    """
    
    def __init__(self):
        self.basal = EstadoFisicoBasal()
        self.cascada = CascadaDegradacion()
        self.historial_degradacion = []  # Registro de cada degradación aplicada
    
    def validar_valor(self, valor: Any, nombre: str = "valor") -> Tuple[bool, Optional[float]]:
        """
        Valida si un valor es utilizable o necesita fallback.
        
        Parámetros:
        -----------
        valor : Any
            Valor a validar
        nombre : str
            Nombre del parámetro (para logging)
            
        Retorna:
        --------
        Tuple[bool, Optional[float]]
            (es_valido, valor_limpio)
        """
        if valor is None:
            logger.debug(f"Valor {nombre} es None, requiere fallback")
            return False, None
        
        try:
            val_float = float(valor)
            if math.isnan(val_float) or math.isinf(val_float):
                logger.debug(f"Valor {nombre} es NaN/Inf, requiere fallback")
                return False, None
            return True, val_float
        except (TypeError, ValueError):
            logger.debug(f"Valor {nombre} no convertible a float, requiere fallback")
            return False, None
    
    def aplicar_fallback(self, valor: Any, clave_basal: str, nombre: str = "valor") -> Tuple[float, EstadoFisico]:
        """
        Aplica fallback a un valor inválido usando el Estado Físico Basal.
        
        Parámetros:
        -----------
        valor : Any
            Valor a validar/corregir
        clave_basal : str
            Clave en el diccionario basal para usar como fallback
        nombre : str
            Nombre del parámetro (para logging)
            
        Retorna:
        --------
        Tuple[float, EstadoFisico]
            (valor_final, estado)
        """
        es_valido, valor_limpio = self.validar_valor(valor, nombre)
        
        if es_valido:
            return valor_limpio, EstadoFisico.REAL
        
        # Aplicar fallback desde Estado Físico Basal
        basal_dict = self.basal.obtener_diccionario_completo()
        valor_fallback = basal_dict.get(clave_basal, 0.0)
        
        logger.warning(f"Fallback aplicado a {nombre}: {valor} → {valor_fallback} (ISA)")
        self.historial_degradacion.append({
            'parametro': nombre,
            'valor_original': valor,
            'valor_fallback': valor_fallback,
            'tipo': 'fallback_basal'
        })
        
        return valor_fallback, EstadoFisico.ESTIMADO
    
    def ejecutar_con_degradacion(
        self, 
        funciones_cascada: list, 
        parametros: dict,
        tipo_cascada: str
    ) -> Tuple[Optional[float], EstadoFisico, str]:
        """
        Ejecuta una cascada de funciones con degradación automática.
        
        Parámetros:
        -----------
        funciones_cascada : list
            Lista de (nombre_funcion, funcion_callable)
        parametros : dict
            Parámetros para pasar a las funciones
        tipo_cascada : str
            Tipo de cascada (para logging)
            
        Retorna:
        --------
        Tuple[Optional[float], EstadoFisico, str]
            (resultado, estado, nombre_funcion_usada)
        """
        for nombre_func, func in funciones_cascada:
            try:
                resultado = func(**parametros)
                
                # Validar resultado
                es_valido, valor_limpio = self.validar_valor(resultado, f"resultado_{nombre_func}")
                
                if es_valido:
                    # Determinar estado según posición en cascada
                    if nombre_func == funciones_cascada[0][0]:
                        estado = EstadoFisico.REAL
                    else:
                        estado = EstadoFisico.SINTETICO
                        logger.info(f"Degradación aplicada en {tipo_cascada}: usando {nombre_func}")
                        self.historial_degradacion.append({
                            'tipo_cascada': tipo_cascada,
                            'funcion_usada': nombre_func,
                            'tipo': 'degradacion_formula'
                        })
                    
                    return valor_limpio, estado, nombre_func
                    
            except Exception as e:
                logger.debug(f"Función {nombre_func} falló: {e}, intentando siguiente en cascada")
                continue
        
        # Si todas las funciones fallan, retornar None y flag
        logger.error(f"Todas las funciones de cascada {tipo_cascada} fallaron")
        return None, EstadoFisico.SINTETICO, "fallback_total"
    
    def obtener_historial(self) -> list:
        """Retorna el historial completo de degradaciones aplicadas."""
        return self.historial_degradacion.copy()
    
    def limpiar_historial(self):
        """Limpia el historial de degradaciones."""
        self.historial_degradacion.clear()


# Singleton global
_fallback_instance = None

def obtener_fallback_universal() -> FallbackUniversal:
    """Obtiene la instancia global del fallback universal."""
    global _fallback_instance
    if _fallback_instance is None:
        _fallback_instance = FallbackUniversal()
    return _fallback_instance
