"""
CONTEXTO SENSORES V1.0
═════════════════════════════════════════════════════════════════════════════

Gestión de contexto sensor:
- Diferenciación WH31 (protegido) vs WH65 (expuesto)
- Factores de protección del viento
- Correcciones por exposición radiativa
- Confianza de medida por sensor

Fecha: 11 de febrero de 2026
"""

from typing import Optional, Dict
import logging
import math

logger = logging.getLogger(__name__)


def factor_proteccion_sensores(
    tipo_sensor: str = "wh65",
    distancia_a_pared_metros: Optional[float] = None,
    altura_suelo_cms: Optional[float] = None
) -> Dict[str, float]:
    """
    Calcula factor de protección para sensor de temperatura.
    
    Tipos:
    - "wh65": Completamente expuesto (sin protección)
    - "wh31": Protegido (esquina, pared cercana)
    - "stevenson": Screen Stevenson (estándar meteorológico)
    
    Args:
        tipo_sensor: Modelo del sensor
        distancia_a_pared_metros: Distancia a pared más cercana (affects WH31)
        altura_suelo_cms: Altura del sensor (affects radiación)
    
    Returns:
        {
            'factor_viento': float 0.0-1.0,  # Cuánto afecta el viento (1.0=total, 0.3=poco)
            'factor_calentamiento_radiativo': float 0.0-1.0,  # Cuánto se calienta por sol directo
            'factor_evaporacion': float 0.0-1.0,  # Cuánto se enfría por evaporación
            'confianza_temperatura': float 0-100,  # Confianza en medida (%)
            'descripcion': str
        }
    """
    
    if tipo_sensor.lower() == "wh65":
        # WH65: Totalmente expuesto al viento y radiación
        logger.debug("WH65: Sensor COMPLETAMENTE EXPUESTO")
        return {
            "factor_viento": 1.0,                    # 100% efecto viento
            "factor_calentamiento_radiativo": 0.95,  # 95% calentamiento por radiación
            "factor_evaporacion": 0.85,              # 85% evaporación (enfría)
            "confianza_temperatura": 85.0,           # Buena confianza (hay evaporación)
            "descripcion": "WH65 expuesto: máxima precisión pero sensor caliente"
        }
    
    elif tipo_sensor.lower() == "wh31":
        # WH31: Protegido (esquina, pared cercana)
        # Si distancia_a_pared < 1m: protección adicional
        factor_pared = 1.0
        if distancia_a_pared_metros is not None:
            if distancia_a_pared_metros < 0.5:
                factor_pared = 0.80  # -20% viento (fuerte protección)
            elif distancia_a_pared_metros < 1.0:
                factor_pared = 0.85  # -15% viento (protección moderada)
            elif distancia_a_pared_metros < 2.0:
                factor_pared = 0.92  # -8% viento (protección leve)
        
        logger.debug(f"WH31: Sensor PROTEGIDO (factor_pared={factor_pared:.2f})")
        return {
            "factor_viento": 0.70 * factor_pared,        # 70% efecto viento (protegido)
            "factor_calentamiento_radiativo": 1.10,      # 110% (pared refleja calor)
            "factor_evaporacion": 0.40,                  # 40% evaporación (aire quieto)
            "confianza_temperatura": 70.0,               # Menor confianza (sesgo radiativo)
            "descripcion": f"WH31 protegido: lee +1-3°C por radiación (factor_pared={factor_pared:.0%})"
        }
    
    elif tipo_sensor.lower() == "stevenson":
        # Stevenson Screen (estándar meteorológico)
        logger.debug("Stevenson Screen: Sensor ESTÁNDAR METEOROLÓGICO")
        return {
            "factor_viento": 0.60,                   # 60% efecto viento (bien ventilado)
            "factor_calentamiento_radiativo": 0.85,  # 85% (protección de radiación)
            "factor_evaporacion": 0.70,              # 70% evaporación controlada
            "confianza_temperatura": 95.0,           # Máxima confianza (estándar)
            "descripcion": "Stevenson: referencia meteorológica, máxima confianza"
        }
    
    else:
        # Fallback: genérico
        logger.warning(f"Tipo sensor desconocido: {tipo_sensor}, usando fallback genérico")
        return {
            "factor_viento": 0.80,
            "factor_calentamiento_radiativo": 0.90,
            "factor_evaporacion": 0.70,
            "confianza_temperatura": 75.0,
            "descripcion": "Sensor genérico (confianza media)"
        }


def sensacion_termica_corregida(
    temperatura_c: float,
    humedad_relativa: float,
    velocidad_viento_kmh: float,
    tipo_sensor_primario: str = "wh65",
    tipo_sensor_viento: str = "wh65",
    distancia_pared_metros: Optional[float] = None
) -> Dict[str, float]:
    """
    Calcula sensación térmica CORREGIDA por contexto de sensores.
    
    Si WH31 está protegido, el viento que LEE es menor al viento REAL.
    Esto afecta sensación térmica (wind chill / heat index).
    
    Returns:
        {
            'sensacion_termica_raw': float,      # Sin corrección
            'sensacion_termica_corregida': float, # Con corrección
            'factor_correccion': float,           # Qué se aplicó
            'nota': str
        }
    """
    
    contexto_temp = factor_proteccion_sensores(tipo_sensor_primario, distancia_pared_metros)
    contexto_viento = factor_proteccion_sensores(tipo_sensor_viento, distancia_pared_metros)
    
    # Viento AJUSTADO para el cálculo de sensación térmica
    # Si sensor protegido, el viento REAL es mayor (dividir por factor < 1.0)
    viento_ajustado = velocidad_viento_kmh / contexto_viento["factor_viento"] if contexto_viento["factor_viento"] > 0 else velocidad_viento_kmh
    
    # Wind chill / Heat Index (fórmula simplificada)
    # Sensación térmica cruda (usando temperatura sin corregir)
    if temperatura_c < 10:
        # Wind chill (frío)
        sens_raw = 13.12 + 0.6215 * temperatura_c - 11.37 * (velocidad_viento_kmh ** 0.16) + 0.3965 * temperatura_c * (velocidad_viento_kmh ** 0.16)
        sens_corr = 13.12 + 0.6215 * temperatura_c - 11.37 * (viento_ajustado ** 0.16) + 0.3965 * temperatura_c * (viento_ajustado ** 0.16)
    else:
        # Heat index (calor)
        if humedad_relativa < 50 and temperatura_c < 27:
            sens_raw = temperatura_c
            sens_corr = temperatura_c
        else:
            # Rothfusz (para calor)
            c1, c2, c3, c4, c5, c6, c7, c8, c9 = (42.379, 2.04901523, 10.14333127, -0.22475541, -0.00683783, -0.05481717, 0.00122874, 0.00085282, -0.00000199)
            t2 = temperatura_c ** 2
            rh2 = humedad_relativa ** 2
            sens_raw = c1 + c2*temperatura_c + c3*humedad_relativa - c4*temperatura_c*humedad_relativa - c5*t2 - c6*rh2 + c7*t2*humedad_relativa + c8*temperatura_c*rh2 - c9*t2*rh2
            sens_corr = sens_raw  # Heat index no depende mucho del viento medido
    
    factor_corr = contexto_viento["factor_viento"]
    
    return {
        "sensacion_termica_raw": round(sens_raw, 1),
        "sensacion_termica_corregida": round(sens_corr, 1),
        "factor_correccion_viento": round(factor_corr, 2),
        "viento_real_estimado_kmh": round(velocidad_viento_kmh / factor_corr, 1),
        "nota": f"{contexto_temp['descripcion']} + {contexto_viento['descripcion']}"
    }


def temperatura_ajustada_por_sensor(
    temperatura_medida_c: float,
    tipo_sensor: str = "wh65",
    radiacion_w_m2: Optional[float] = None,
    distancia_pared_metros: Optional[float] = None
) -> Dict[str, float]:
    """
    Estima temperatura REAL ajustando por error sistemático del sensor.
    
    WH31 lee +1-3°C más por radiación. WH65 es más realista pero más frío.
    
    Returns:
        {
            'temperatura_medida': float,
            'temperatura_estimada_real': float,
            'error_sistematico_grados': float,
            'confianza_medida': float  # 0-100
        }
    """
    
    contexto = factor_proteccion_sensores(tipo_sensor, distancia_pared_metros)
    
    if tipo_sensor.lower() == "wh31" and radiacion_w_m2 is not None and radiacion_w_m2 > 0:
        # WH31 se calienta por radiación: ~1-3°C dependiendo de radiación
        # Fórmula: 3°C por 1000 W/m² (máximo 3°C)
        calentamiento = min((radiacion_w_m2 / 1000.0) * 3.0, 3.0)
        
        temp_real = temperatura_medida_c - calentamiento
        error = calentamiento
        
        logger.debug(f"WH31: temp_med={temperatura_medida_c:.1f}°C, rad={radiacion_w_m2:.0f}W/m², calentamiento={calentamiento:.1f}°C → temp_real={temp_real:.1f}°C")
        
        return {
            "temperatura_medida": round(temperatura_medida_c, 1),
            "temperatura_estimada_real": round(temp_real, 1),
            "error_sistematico_grados": round(error, 1),
            "confianza_medida": contexto["confianza_temperatura"],
            "tipo_sensor": tipo_sensor,
            "razon": f"WH31 protegido: -calor radiativo ({calentamiento:.1f}°C)"
        }
    
    elif tipo_sensor.lower() == "wh65":
        # WH65 es prácticamente sin error (evaporación lo compensa)
        return {
            "temperatura_medida": round(temperatura_medida_c, 1),
            "temperatura_estimada_real": round(temperatura_medida_c, 1),
            "error_sistematico_grados": 0.0,
            "confianza_medida": contexto["confianza_temperatura"],
            "tipo_sensor": tipo_sensor,
            "razon": "WH65 expuesto: medida realista (evaporación compensa radiación)"
        }
    
    else:
        return {
            "temperatura_medida": round(temperatura_medida_c, 1),
            "temperatura_estimada_real": round(temperatura_medida_c, 1),
            "error_sistematico_grados": 0.0,
            "confianza_medida": contexto["confianza_temperatura"],
            "tipo_sensor": tipo_sensor,
            "razon": "Sensor genérico: sin corrección aplicada"
        }
