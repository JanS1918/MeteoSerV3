"""
═══════════════════════════════════════════════════════════════════════════════
MÓDULO: FUSIÓN ADAPTATIVA DE SENSORES WH65 + WH31
═══════════════════════════════════════════════════════════════════════════════

Objetivo: Combinar inteligentemente ambos sensores (WH65 en zona soleada/despejada 
y WH31 en zona sombría/húmeda) usando una media ponderada adaptativa según el 
índice y contexto.

Ventajas:
- Ambos sensores participan siempre (nunca se excluye totalmente uno)
- Ponderación contextual: confort, predicción, alerta, etc.
- Detección de anomalías automática
- Trazabilidad completa de decisiones

Autores: MeteoSer V3.0 | Fecha: 2026-02-10
═══════════════════════════════════════════════════════════════════════════════
"""

import logging
from typing import Tuple, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PONDERACIONES POR CONTEXTO
# ═══════════════════════════════════════════════════════════════════════════════

PONDERACIONES = {
    # Confort humano: priorizar zona fresca/sombría (WH31)
    'confort': {
        'temperatura': {'wh65': 0.3, 'wh31': 0.7},
        'humedad': {'wh65': 0.4, 'wh31': 0.6},
        'razon': 'Confort humano prioriza zona sombría',
    },
    
    # Predicción de lluvia: priorizar zona expuesta (WH65)
    'lluvia': {
        'temperatura': {'wh65': 0.7, 'wh31': 0.3},
        'humedad': {'wh65': 0.65, 'wh31': 0.35},
        'razon': 'Predicción lluvia usa zona expuesta',
    },
    
    # Alerta: media equilibrada, detectar anomalías
    'alerta': {
        'temperatura': {'wh65': 0.5, 'wh31': 0.5},
        'humedad': {'wh65': 0.5, 'wh31': 0.5},
        'razon': 'Alerta requiere balance entre ambas zonas',
    },
    
    # Microclima: detectar diferencias locales
    'microclima': {
        'temperatura': {'wh65': 0.5, 'wh31': 0.5},
        'humedad': {'wh65': 0.5, 'wh31': 0.5},
        'razon': 'Microclima estudia diferencias reales',
    },
    
    # Rocío/niebla: priorizar zona húmeda (WH31)
    'rocio_niebla': {
        'temperatura': {'wh65': 0.4, 'wh31': 0.6},
        'humedad': {'wh65': 0.35, 'wh31': 0.65},
        'razon': 'Rocío/niebla propenso en zonas sombrías',
    },
    
    # Confort en exposición solar: priorizar WH65
    'confort_expuesto': {
        'temperatura': {'wh65': 0.7, 'wh31': 0.3},
        'humedad': {'wh65': 0.6, 'wh31': 0.4},
        'razon': 'Confort en zona soleada',
    },
    
    # Predicción general: media equilibrada
    'prediccion_general': {
        'temperatura': {'wh65': 0.6, 'wh31': 0.4},
        'humedad': {'wh65': 0.55, 'wh31': 0.45},
        'razon': 'Predicción general combina ambas perspectivas',
    },
    
    # Validación de sensores: detectar fallos
    'validacion': {
        'temperatura': {'wh65': 0.5, 'wh31': 0.5},
        'humedad': {'wh65': 0.5, 'wh31': 0.5},
        'razon': 'Validación requiere simetría',
    },
}

# Umbrales de anomalía
UMBRALES_ANOMALIA = {
    'temperatura_delta_max': 15.0,  # °C: diferencia máxima permitida
    'humedad_delta_max': 40.0,       # %: diferencia máxima permitida
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATACLASS PARA DECISIONES DE FUSIÓN
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DecisionFusion:
    """Resultado de la fusión adaptativa de sensores."""
    temperatura_media: float
    humedad_media: float
    peso_wh65_temp: float
    peso_wh31_temp: float
    peso_wh65_hum: float
    peso_wh31_hum: float
    contexto: str
    anomalia: bool
    razon_anomalia: Optional[str] = None
    razon_fusion: str = ""
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario para logging/persistencia."""
        return {
            'temperatura_media': round(self.temperatura_media, 2),
            'humedad_media': round(self.humedad_media, 2),
            'peso_wh65_temp': round(self.peso_wh65_temp, 2),
            'peso_wh31_temp': round(self.peso_wh31_temp, 2),
            'peso_wh65_hum': round(self.peso_wh65_hum, 2),
            'peso_wh31_hum': round(self.peso_wh31_hum, 2),
            'contexto': self.contexto,
            'anomalia': self.anomalia,
            'razon_anomalia': self.razon_anomalia,
            'razon_fusion': self.razon_fusion,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL: MEDIA ADAPTATIVA
# ═══════════════════════════════════════════════════════════════════════════════

def media_adaptativa(
    temp_wh65: float,
    hum_wh65: float,
    temp_wh31: float,
    hum_wh31: float,
    contexto: str = 'prediccion_general'
) -> DecisionFusion:
    """
    Calcula media ponderada adaptativa entre WH65 (soleado) y WH31 (sombrío).
    
    Args:
        temp_wh65: Temperatura WH65 (°C)
        hum_wh65: Humedad WH65 (%)
        temp_wh31: Temperatura WH31 (°C)
        hum_wh31: Humedad WH31 (%)
        contexto: Tipo de índice/cálculo ('confort', 'lluvia', 'alerta', etc.)
    
    Returns:
        DecisionFusion con temperatura/humedad media, pesos, y detalles
    
    Lógica:
    -------
    1. Verificar si hay anomalía (diferencia extrema)
    2. Si hay anomalía: lanzar alerta y usar media equilibrada (0.5/0.5)
    3. Si no: obtener ponderaciones del contexto y aplicar
    4. Retornar DecisionFusion con trazabilidad completa
    """
    
    # Validar entrada mínima
    try:
        temp_wh65 = float(temp_wh65) if temp_wh65 is not None else 0.0
        hum_wh65 = float(hum_wh65) if hum_wh65 is not None else 50.0
        temp_wh31 = float(temp_wh31) if temp_wh31 is not None else 0.0
        hum_wh31 = float(hum_wh31) if hum_wh31 is not None else 50.0
    except (TypeError, ValueError) as e:
        logger.error(f"[FUSION] Error validando entrada: {e}")
        # Fallback: retornar valores como están, sin media
        return DecisionFusion(
            temperatura_media=temp_wh65 or temp_wh31 or 0.0,
            humedad_media=hum_wh65 or hum_wh31 or 50.0,
            peso_wh65_temp=0.5,
            peso_wh31_temp=0.5,
            peso_wh65_hum=0.5,
            peso_wh31_hum=0.5,
            contexto=contexto,
            anomalia=True,
            razon_anomalia='Error en validación de entrada',
            razon_fusion='Fallback: sin fusión disponible',
        )
    
    # 1. DETECCIÓN DE ANOMALÍAS
    delta_temp = abs(temp_wh65 - temp_wh31)
    delta_hum = abs(hum_wh65 - hum_wh31)
    
    anomalia = False
    razon_anomalia = None
    
    if delta_temp > UMBRALES_ANOMALIA['temperatura_delta_max']:
        anomalia = True
        razon_anomalia = f"Diferencia temperatura extrema: {delta_temp:.1f}°C"
        logger.warning(f"[ALERTA ANOMALIA] {razon_anomalia} (WH65={temp_wh65:.1f}°C, WH31={temp_wh31:.1f}°C)")
    
    if delta_hum > UMBRALES_ANOMALIA['humedad_delta_max']:
        anomalia = True
        if razon_anomalia:
            razon_anomalia += f" + Diferencia humedad extrema: {delta_hum:.1f}%"
        else:
            razon_anomalia = f"Diferencia humedad extrema: {delta_hum:.1f}%"
        logger.warning(f"[ALERTA ANOMALIA] {razon_anomalia} (WH65={hum_wh65:.1f}%, WH31={hum_wh31:.1f}%)")
    
    # 2. OBTENER PONDERACIONES
    if contexto not in PONDERACIONES:
        logger.warning(f"[FUSION] Contexto '{contexto}' no reconocido, usando 'prediccion_general'")
        contexto = 'prediccion_general'
    
    config = PONDERACIONES[contexto]
    razon_fusion = config['razon']
    
    # Si hay anomalía, usar ponderación equilibrada en lugar de la del contexto
    if anomalia:
        peso_wh65_temp = 0.5
        peso_wh31_temp = 0.5
        peso_wh65_hum = 0.5
        peso_wh31_hum = 0.5
        razon_fusion += " [ANOMALIA: ponderación equilibrada]"
        logger.info(f"[FUSION] Por anomalía, usando ponderación 50/50")
    else:
        peso_wh65_temp = config['temperatura']['wh65']
        peso_wh31_temp = config['temperatura']['wh31']
        peso_wh65_hum = config['humedad']['wh65']
        peso_wh31_hum = config['humedad']['wh31']
    
    # 3. CALCULAR MEDIA PONDERADA
    temp_media = temp_wh65 * peso_wh65_temp + temp_wh31 * peso_wh31_temp
    hum_media = hum_wh65 * peso_wh65_hum + hum_wh31 * peso_wh31_hum
    
    # Clamp humedad a rango válido
    hum_media = max(0.0, min(100.0, hum_media))
    
    # 4. LOG Y RETORNO
    logger.info(
        f"[FUSION] Contexto={contexto} | T_media={temp_media:.2f}°C "
        f"(WH65={temp_wh65:.2f}*{peso_wh65_temp}, WH31={temp_wh31:.2f}*{peso_wh31_temp}) | "
        f"H_media={hum_media:.1f}% (WH65={hum_wh65:.1f}*{peso_wh65_hum}, WH31={hum_wh31:.1f}*{peso_wh31_hum})"
    )
    
    return DecisionFusion(
        temperatura_media=temp_media,
        humedad_media=hum_media,
        peso_wh65_temp=peso_wh65_temp,
        peso_wh31_temp=peso_wh31_temp,
        peso_wh65_hum=peso_wh65_hum,
        peso_wh31_hum=peso_wh31_hum,
        contexto=contexto,
        anomalia=anomalia,
        razon_anomalia=razon_anomalia,
        razon_fusion=razon_fusion,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CONVENIENCIA
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_temperatura_adaptativa(
    temp_wh65: float,
    temp_wh31: float,
    contexto: str = 'prediccion_general'
) -> float:
    """Obtener solo la temperatura media adaptativa."""
    fusion = media_adaptativa(temp_wh65, 50.0, temp_wh31, 50.0, contexto)
    return fusion.temperatura_media


def obtener_humedad_adaptativa(
    hum_wh65: float,
    hum_wh31: float,
    contexto: str = 'prediccion_general'
) -> float:
    """Obtener solo la humedad media adaptativa."""
    fusion = media_adaptativa(0.0, hum_wh65, 0.0, hum_wh31, contexto)
    return fusion.humedad_media


def detectar_anomalia(
    temp_wh65: float,
    hum_wh65: float,
    temp_wh31: float,
    hum_wh31: float
) -> Tuple[bool, Optional[str]]:
    """Detectar si hay anomalía entre sensores."""
    fusion = media_adaptativa(temp_wh65, hum_wh65, temp_wh31, hum_wh31, 'validacion')
    return fusion.anomalia, fusion.razon_anomalia


# ═══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE ALERTAS Y DECISIONES AVANZADAS
# ═══════════════════════════════════════════════════════════════════════════════

def generar_alerta_anomalia(
    temp_wh65: float,
    hum_wh65: float,
    temp_wh31: float,
    hum_wh31: float,
    timestamp: Optional[str] = None
) -> Optional[Dict]:
    """
    Generar alerta si se detecta anomalía entre sensores.
    
    Returns:
        Dict con detalles de alerta o None si no hay anomalía
    """
    from datetime import datetime
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    anomalia, razon = detectar_anomalia(temp_wh65, hum_wh65, temp_wh31, hum_wh31)
    
    if anomalia:
        return {
            'timestamp': timestamp,
            'tipo': 'anomalia_sensores',
            'severidad': 'MEDIA',
            'razon': razon,
            'datos': {
                'wh65': {'temp': round(temp_wh65, 2), 'humedad': round(hum_wh65, 1)},
                'wh31': {'temp': round(temp_wh31, 2), 'humedad': round(hum_wh31, 1)},
                'diferencias': {
                    'temperatura_delta': round(abs(temp_wh65 - temp_wh31), 2),
                    'humedad_delta': round(abs(hum_wh65 - hum_wh31), 1),
                }
            },
            'recomendacion': 'Revisar funcionamiento de sensores o compensar ponderación'
        }
    
    return None


def detectar_microclima(
    temp_wh65: float,
    hum_wh65: float,
    temp_wh31: float,
    hum_wh31: float
) -> Optional[Dict]:
    """
    Detectar si existe microclima significativo (diferencias >3°C o >15% humedad).
    
    Returns:
        Dict con detalles del microclima o None si no es significativo
    """
    delta_temp = abs(temp_wh65 - temp_wh31)
    delta_hum = abs(hum_wh65 - hum_wh31)
    
    DELTA_TEMP_MICRO = 3.0
    DELTA_HUM_MICRO = 15.0
    
    if delta_temp > DELTA_TEMP_MICRO or delta_hum > DELTA_HUM_MICRO:
        # Determinar tipo de microclima
        if temp_wh31 < temp_wh65 and hum_wh31 > hum_wh65:
            tipo = "ZONA_FRESCA_HUMEDA"  # WH31 más frío y húmedo (sombra protegida)
            descripcion = "Microclima fresquizado en zona sombría"
        elif temp_wh31 > temp_wh65 and hum_wh31 < hum_wh65:
            tipo = "ZONA_CALIDA_SECA"  # WH31 más caliente (paradoja)
            descripcion = "Microclima inesperado: WH31 más caliente"
        elif temp_wh31 < temp_wh65:
            tipo = "ZONA_FRESCA"  # WH31 más frío
            descripcion = "Zona sombría significativamente más fresca"
        elif hum_wh31 > hum_wh65:
            tipo = "ZONA_HUMEDA"  # WH31 más húmedo
            descripcion = "Zona sombría significativamente más húmeda"
        else:
            tipo = "MICROCLIMA_DETECTADO"
            descripcion = "Microclima local detectado"
        
        return {
            'tipo': tipo,
            'descripcion': descripcion,
            'severidad': 'INFORMATIVA',
            'delta_temperatura': round(delta_temp, 2),
            'delta_humedad': round(delta_hum, 1),
            'zona_mas_comoda': 'WH31 (sombría)' if temp_wh31 < temp_wh65 else 'WH65 (soleada)',
            'recomendacion': f"Para confort, preferir zona {'sombría' if temp_wh31 < temp_wh65 else 'soleada'}",
        }
    
    return None


def evaluar_sesgo_radiacion_wh65(
    temp_wh65: float,
    temp_wh31: float,
    radiacion_w_m2: float
) -> Dict:
    """
    Evaluar si WH65 podría estar sesgado por radiación solar.
    
    High radiation + WH65 much warmer than WH31 = probable radiative bias
    
    Returns:
        Dict con evaluación del sesgo
    """
    delta_temp = temp_wh65 - temp_wh31
    sesgo_probable = radiacion_w_m2 > 400 and delta_temp > 3.0
    
    return {
        'sesgo_radiacion_probable': sesgo_probable,
        'radiacion_w_m2': round(radiacion_w_m2, 1),
        'diferencia_temp_wh65_mayor': round(delta_temp, 2),
        'confiabilidad_wh31': 'ALTA' if sesgo_probable else 'NORMAL',
        'recomendacion': 'Considerar usar WH31 para índices de confort si radiación >400' if sesgo_probable else 'Ambos sensores confiables',
    }


def guardar_decision_fusion(
    temp_wh65: float,
    hum_wh65: float,
    temp_wh31: float,
    hum_wh31: float,
    contexto: str,
    decision_fusion: DecisionFusion,
    archivo_log: str = 'data/fusion_decisions.jsonl'
) -> bool:
    """
    Guardar decisión de fusión en archivo JSONL para análisis posterior.
    
    Returns:
        True si se guardó correctamente
    """
    import json
    from datetime import datetime
    from pathlib import Path
    
    try:
        logger_data = {
            'timestamp': datetime.now().isoformat(),
            'contexto': contexto,
            'entrada': {
                'wh65_temp': round(temp_wh65, 2),
                'wh65_hum': round(hum_wh65, 1),
                'wh31_temp': round(temp_wh31, 2),
                'wh31_hum': round(hum_wh31, 1),
            },
            'salida': decision_fusion.to_dict(),
        }
        
        # Crear directorio si no existe
        Path(archivo_log).parent.mkdir(parents=True, exist_ok=True)
        
        # Append al archivo JSONL
        with open(archivo_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(logger_data, ensure_ascii=False) + '\n')
        
        logger.debug(f"[FUSION] Decisión guardada en {archivo_log}")
        return True
    except Exception as e:
        logger.error(f"[FUSION] Error guardando decisión: {e}")
        return False


def analizar_patrones_fusion(
    archivo_log: str = 'data/fusion_decisions.jsonl',
    ultimas_n: int = 1000
) -> Optional[Dict]:
    """
    Analizar patrones en archivo de decisiones para ajuste dinámico de ponderaciones.
    
    Args:
        archivo_log: Path al archivo JSONL de decisiones
        ultimas_n: Últimas N líneas a analizar
    
    Returns:
        Dict con estadísticas de patrones
    """
    import json
    from pathlib import Path
    
    try:
        log_path = Path(archivo_log)
        if not log_path.exists():
            logger.warning(f"[ANALISIS] Archivo de log no existe: {archivo_log}")
            return None
        
        decisiones = []
        with open(archivo_log, 'r', encoding='utf-8') as f:
            # Leer últimas n líneas
            for i, linea in enumerate(f):
                if i >= (sum(1 for _ in open(archivo_log)) - ultimas_n):
                    try:
                        decisiones.append(json.loads(linea))
                    except json.JSONDecodeError:
                        continue
        
        if not decisiones:
            return None
        
        # Calcular estadísticas
        from statistics import mean, stdev
        
        stats = {
            'total_muestras': len(decisiones),
            'contextos_usados': list(set(d['contexto'] for d in decisiones)),
            'anomalias_detectadas': sum(1 for d in decisiones if d['salida']['anomalia']),
            'temperatura_media_global': round(mean(d['salida']['temperatura_media'] for d in decisiones), 2) if decisiones else None,
            'humedad_media_global': round(mean(d['salida']['humedad_media'] for d in decisiones), 2) if decisiones else None,
        }
        
        logger.info(f"[ANALISIS] Patrones: {stats['total_muestras']} muestras, "
                   f"{stats['anomalias_detectadas']} anomalías")
        
        return stats
    except Exception as e:
        logger.error(f"[ANALISIS] Error analizando patrones: {e}")
        return None
