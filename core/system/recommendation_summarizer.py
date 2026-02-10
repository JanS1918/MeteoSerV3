"""
RECOMMENDATION SUMMARIZER v2.0 - Convertidor de Índices a Recomendaciones UI

Propósito: Convertir 8 índices sintéticos (0-100) en 8 recomendaciones legibles
("¿Hoy es buen día para X? SÍ/NO + % confianza + razón")

Entrada:
  - indice_cetreria_sintetico: float (0-100)
  - indice_lluvia_sintetico: float (0-100)
  - indice_deporte_sintetico: float (0-100)
  - indice_confort_sintetico: float (0-100)
  - indice_riego_sintetico: float (0-100)
  - indice_astronomia_sintetico: float (0-100)
  - indice_salud_sintetico: float (0-100)  [INVERTED: bajo=salud mala]
  - indice_hidrologia_sintetico: float (0-100)

Salida: Dict con 8 recomendaciones + confianza global

Configuración:
  - Threshold "SÍ" vs "NO": 50 puntos (ajustable por dominio)
  - Confianza: Basada en % sensores disponibles (0-100%)
  - Razón: Descripción de factores limitantes

Fecha: 10 de febrero de 2026
"""

from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN POR DOMINIO
# ============================================================================

DOMAIN_CONFIG = {
    "cetreria": {
        "nombre": "Cetrería",
        "pregunta": "¿Buen día para cetrería?",
        "threshold_si": 55,  # >55 = recomendable
        "sensores_necesarios": ["temperatura", "viento", "visibilidad", "presion", "radiacion"],
        "factores_negativos": ["viento fuerte >12 km/h", "lluvia activa", "visibilidad <5km"],
        "factores_positivos": ["termales activos", "cielo despejado", "viento moderado 5-15 km/h"]
    },
    
    "lluvia": {
        "nombre": "Precaución: Lluvia",
        "pregunta": "¿Habrá lluvia hoy?",
        "threshold_si": 50,  # >50 = probabilidad alta
        "sensores_necesarios": ["presion", "humedad", "viento"],
        "factores_negativos": ["presión baja", "humedad muy alta", "cambio presión rápido"],
        "factores_positivos": ["anticiclón", "humedad baja", "presión estable"]
    },
    
    "deporte": {
        "nombre": "Deporte / Senderismo",
        "pregunta": "¿Buen día para deporte?",
        "threshold_si": 60,  # >60 = excelente
        "sensores_necesarios": ["temperatura", "viento", "visibilidad", "radiacion"],
        "factores_negativos": ["lluvia inminente", "viento fuerte", "visibilidad nula"],
        "factores_positivos": ["temperatura ideal 15-25°C", "sin lluvia", "cielo claro"]
    },
    
    "confort": {
        "nombre": "Confort Climático",
        "pregunta": "¿Día confortable?",
        "threshold_si": 65,  # >65 = muy confortable
        "sensores_necesarios": ["temperatura", "humedad", "radiacion", "viento"],
        "factores_negativos": ["muy calor", "muy frio", "humedad extrema", "UV muy alto"],
        "factores_positivos": ["temperatura 20-26°C", "humedad 40-60%", "sin radiación extrema"]
    },
    
    "riego": {
        "nombre": "Necesidad de Riego",
        "pregunta": "¿Necesario riego hoy?",
        "threshold_si": 60,  # >60 = sí, riego recomendado
        "sensores_necesarios": ["humedad_suelo", "lluvia", "temperatura", "radiacion"],
        "factores_negativos": ["suelo saturado", "lluvia reciente", "estrés bajo"],
        "factores_positivos": ["suelo seco", "calor evaporativo alto", "estrés cultivo alto"]
    },
    
    "astronomia": {
        "nombre": "Observación Astronómica",
        "pregunta": "¿Buen cielo para observar?",
        "threshold_si": 70,  # >70 = excelente
        "sensores_necesarios": ["elevacion_solar", "radiacion", "visibilidad", "humedad"],
        "factores_negativos": ["luz solar residual", "nubes", "humedad alta", "bruma"],
        "factores_positivos": ["noche oscura", "cielo despejado", "visibilidad >15km"]
    },
    
    "salud": {
        "nombre": "Salud Ambiental",
        "pregunta": "¿Día saludable?",
        "threshold_si": 70,  # >70 = bueno (inverted scoring)
        "sensores_necesarios": ["temperatura", "humedad", "radiacion", "viento", "visibilidad"],
        "factores_negativos": ["UV extremo", "calor/frío extremo", "helada", "aire contaminado"],
        "factores_positivos": ["temperatura ideal", "UV bajo", "aire limpio", "humedad óptima"]
    },
    
    "hidrologia": {
        "nombre": "Hidrología / Drenaje",
        "pregunta": "¿Riesgo de inundación?",
        "threshold_si": 50,  # >50 = sí, riesgo presente
        "sensores_necesarios": ["lluvia", "humedad_suelo", "presion"],
        "factores_negativos": ["lluvia intensa", "suelo saturado", "infiltración baja"],
        "factores_positivos": ["infiltración alta", "suelo drenado", "escorrentia baja"]
    }
}

# ============================================================================
# FUNCIONES DE CÁLCULO
# ============================================================================

def _evaluar_dominio(
    indice_valor: float,
    config: Dict,
    sensores_disponibles: int,
    sensores_totales: int
) -> Dict[str, any]:
    """
    Evalúa un índice sintético y retorna recomendación + confianza.
    
    Args:
        indice_valor: Float 0-100
        config: Configuración del dominio
        sensores_disponibles: Número de sensores disponibles
        sensores_totales: Número de sensores necesarios
    
    Returns:
        Dict con recomendación, confianza, razón, etc.
    """
    
    # Calcular confianza basada en disponibilidad de sensores
    confianza_sensores = max(0, min(100, (sensores_disponibles / sensores_totales) * 100)) if sensores_totales > 0 else 100.0
    
    # Determinar SI/NO basado en threshold
    threshold = config.get("threshold_si", 50)
    es_recomendable = indice_valor > threshold
    
    # Mapear indicador verbal
    if indice_valor >= 80:
        indicador = "EXCELENTE"
    elif indice_valor >= 60:
        indicador = "BUENO"
    elif indice_valor >= 40:
        indicador = "REGULAR"
    else:
        indicador = "MALO"
    
    # Generar respuesta
    respuesta = "SÍ" if es_recomendable else "NO"
    
    # Razón basada en factores
    if es_recomendable:
        razon_lista = config.get("factores_positivos", [])
    else:
        razon_lista = config.get("factores_negativos", [])
    
    # Tomar el factor más relevante (primero)
    razon = razon_lista[0] if razon_lista else "Datos insuficientes"
    
    return {
        "dominio": config.get("nombre", ""),
        "respuesta": respuesta,
        "indice": round(indice_valor, 1),
        "indicador": indicador,
        "confianza": round(confianza_sensores, 1),
        "razon": razon,
        "sensores_disponibles": sensores_disponibles,
        "sensores_necesarios": sensores_totales
    }


def _contar_sensores_disponibles(datos: Dict) -> Dict[str, int]:
    """
    Cuenta sensores disponibles (no None) para cada dominio.
    
    Args:
        datos: Dict con todos los sensor values
    
    Returns:
        Dict[dominio] = cantidad sensores disponibles
    """
    
    sensores = {
        "temperatura": datos.get("temperatura") is not None,
        "humedad": datos.get("humedad") is not None,
        "lluvia": datos.get("lluvia") is not None,
        "presion": datos.get("presion") is not None,
        "viento": datos.get("viento_kmh") is not None or datos.get("viento") is not None,
        "radiacion": datos.get("radiacion") is not None,
        "uv": datos.get("uv") is not None,
        "visibilidad": datos.get("visibilidad_km") is not None or datos.get("visibilidad") is not None,
        "elevacion_solar": datos.get("elevacion_solar") is not None,
        "humedad_suelo": datos.get("humedad_suelo") is not None,
    }
    
    # Contar por dominio
    disponibles_por_dominio = {}
    
    for dominio, config in DOMAIN_CONFIG.items():
        sensores_necesarios = config.get("sensores_necesarios", [])
        disponibles = sum(1 for sensor in sensores_necesarios if sensores.get(sensor, False))
        disponibles_por_dominio[dominio] = disponibles
    
    return disponibles_por_dominio


def calcular_recomendaciones_completas(
    indice_cetreria: float,
    indice_lluvia: float,
    indice_deporte: float,
    indice_confort: float,
    indice_riego: float,
    indice_astronomia: float,
    indice_salud: float,
    indice_hidrologia: float,
    datos_sensores: Optional[Dict] = None
) -> Dict:
    """
    Calcula 8 recomendaciones a partir de índices sintéticos.
    
    Args:
        8x indice_*: floats 0-100
        datos_sensores: Dict con sensor data (para confianza)
    
    Returns:
        Dict con recomendaciones por dominio
    """
    
    try:
        # Validar entradas
        indices = {
            "cetreria": max(0, min(100, indice_cetreria or 50)),
            "lluvia": max(0, min(100, indice_lluvia or 50)),
            "deporte": max(0, min(100, indice_deporte or 50)),
            "confort": max(0, min(100, indice_confort or 50)),
            "riego": max(0, min(100, indice_riego or 50)),
            "astronomia": max(0, min(100, indice_astronomia or 50)),
            "salud": max(0, min(100, indice_salud or 50)),
            "hidrologia": max(0, min(100, indice_hidrologia or 50))
        }
        
        # Contar sensores disponibles si se proporciona datos
        if datos_sensores is None:
            datos_sensores = {}
        
        sensores_disponibles = _contar_sensores_disponibles(datos_sensores)
        
        # Evaluar cada dominio
        recomendaciones = {}
        confianzas = []
        
        for dominio, indice_valor in indices.items():
            config = DOMAIN_CONFIG.get(dominio, {})
            sensores_disp = sensores_disponibles.get(dominio, 0)
            sensores_tot = len(config.get("sensores_necesarios", []))
            
            rec = _evaluar_dominio(
                indice_valor=indice_valor,
                config=config,
                sensores_disponibles=sensores_disp,
                sensores_totales=sensores_tot
            )
            
            recomendaciones[dominio] = rec
            confianzas.append(rec["confianza"])
        
        # Confianza global (promedio)
        confianza_global = sum(confianzas) / len(confianzas) if confianzas else 100.0
        
        # Retornar estructura completa
        return {
            "timestamp": None,  # Will be set by bus_expander
            "recomendaciones": recomendaciones,
            "confianza_global": round(confianza_global, 1),
            "resumen": {
                "recomendables": sum(1 for r in recomendaciones.values() if r["respuesta"] == "SÍ"),
                "total_dominios": len(recomendaciones),
                "sensores_promedio": round(sum(r["sensores_disponibles"] for r in recomendaciones.values()) / len(recomendaciones), 1)
            }
        }
    
    except Exception as e:
        logger.error(f"[ERROR] calcular_recomendaciones_completas: {e}")
        # Retorna estructura mínima en caso de error
        return {
            "timestamp": None,
            "recomendaciones": {},
            "confianza_global": 0.0,
            "resumen": {"recomendables": 0, "total_dominios": 0, "sensores_promedio": 0}
        }


def formatear_recomendacion_para_ui(
    recomendacion: Dict,
    dominio: str
) -> str:
    """
    Formatea recomendación individual para mostrar en UI.
    
    Ej: "[Cetrería] ¿Hoy? SÍ (87% confianza) - Termales activos"
    
    Args:
        recomendacion: Dict individual de recomendación
        dominio: Clave del dominio
    
    Returns:
        String formateado para UI
    """
    
    try:
        config = DOMAIN_CONFIG.get(dominio, {})
        pregunta = config.get("pregunta", "¿Hoy?")
        
        # Construcción del string
        nombre = recomendacion.get("dominio", "")
        respuesta = recomendacion.get("respuesta", "?")
        confianza = recomendacion.get("confianza", 0)
        razon = recomendacion.get("razon", "")
        indice = recomendacion.get("indice", 0)
        
        # Formato legible
        formateado = (
            f"[{nombre}] {pregunta} {respuesta} "
            f"({confianza:.0f}% conf, índice {indice:.0f}/100) - {razon}"
        )
        
        return formateado
    
    except Exception as e:
        logger.error(f"[ERROR] formatear_recomendacion_para_ui: {e}")
        return "[ERROR] No se pudo formatear recomendación"


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def generar_alerta_si_necesario(recomendaciones: Dict) -> Optional[str]:
    """
    Genera alerta crítica si hay riesgo de lluvia o salud.
    
    Returns:
        String de alerta o None
    """
    
    try:
        if not recomendaciones:
            return None
        
        lluvia_rec = recomendaciones.get("lluvia", {})
        salud_rec = recomendaciones.get("salud", {})
        hidrologia_rec = recomendaciones.get("hidrologia", {})
        
        alertas = []
        
        # Alerta de lluvia
        if lluvia_rec.get("respuesta") == "SÍ" and lluvia_rec.get("indice", 0) > 75:
            alertas.append("ALERTA: Lluvia probable en próximas horas")
        
        # Alerta de salud
        if salud_rec.get("respuesta") == "NO" and salud_rec.get("indice", 0) < 30:
            alertas.append("ALERTA SALUD: Condiciones peligrosas (UV/Calor/Frío extremo)")
        
        # Alerta de hidrología
        if hidrologia_rec.get("respuesta") == "SÍ" and hidrologia_rec.get("indice", 0) > 70:
            alertas.append("ALERTA: Riesgo de inundación/escorrentía")
        
        if alertas:
            return " | ".join(alertas)
        
        return None
    
    except Exception as e:
        logger.error(f"[ERROR] generar_alerta_si_necesario: {e}")
        return None


# ============================================================================
# TEST / DEBUG
# ============================================================================

if __name__ == "__main__":
    # Test básico
    print("=" * 70)
    print("RECOMMENDATION SUMMARIZER v2.0 - Test")
    print("=" * 70)
    
    # Datos de prueba
    datos_test = {
        "temperatura": 22.0,
        "humedad": 55.0,
        "lluvia": 0.0,
        "presion": 1013.0,
        "viento": 5.0,
        "radiacion": 600.0,
        "uv": 4.0,
        "visibilidad": 15.0,
        "elevacion_solar": 45.0,
        "humedad_suelo": 40.0
    }
    
    # Simulación de índices sintéticos
    recomendaciones = calcular_recomendaciones_completas(
        indice_cetreria=75,
        indice_lluvia=20,
        indice_deporte=80,
        indice_confort=85,
        indice_riego=60,
        indice_astronomia=30,
        indice_salud=75,
        indice_hidrologia=40,
        datos_sensores=datos_test
    )
    
    # Mostrar resultados
    print(f"\nConfianza Global: {recomendaciones['confianza_global']:.1f}%")
    print(f"Resumen: {recomendaciones['resumen']['recomendables']}/{recomendaciones['resumen']['total_dominios']} dominios recomendables\n")
    
    for dominio, rec in recomendaciones.get("recomendaciones", {}).items():
        formateado = formatear_recomendacion_para_ui(rec, dominio)
        print(formateado)
    
    # Alerta
    alerta = generar_alerta_si_necesario(recomendaciones.get("recomendaciones", {}))
    if alerta:
        print(f"\n{alerta}")
    else:
        print("\n(Sin alertas)")
    
    print("\n" + "=" * 70)
