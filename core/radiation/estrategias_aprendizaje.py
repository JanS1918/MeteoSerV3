"""
═══════════════════════════════════════════════════════════════════════════════
ESTRATEGIAS DE APRENDIZAJE SEPARADAS - Correctivo vs Diagnóstico
═══════════════════════════════════════════════════════════════════════════════

Implementa la separación dura entre dos capas de aprendizaje:

1. APRENDIZAJE CORRECTIVO (lento, estructural, ajusta pesos)
   - Corrige sesgos sistemáticos de REST2 en tu contexto local
   - Identidad local del cielo (Kt_local dinámico)
   - Memoria: semanas
   - Actúa SOLO en contexto limpio
   - Nunca toca radiación directamente, solo ajusta pesos

2. APRENDIZAJE DIAGNÓSTICO (rápido, detección, ajusta flags)
   - Detecta calima, ensuciamiento, nubosidad fina
   - NO corrige radiación ni índices
   - Solo modifica flags de confianza y pesos de fusión
   - Reduce autoengaños enormemente

Principio clave: Ambos necesitan bloqueo de contexto, pero sus estrategias son diferentes.

Autor: Sistema Robusto MeteoSerV3
Fecha: Feb 10, 2026
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ResultadoAprendizajeCorrectivo:
    """Resultado de aprendizaje correctivo."""
    
    kt_local: float = 0.85  # Índice de claridad ajustado localmente
    factor_aod_local: float = 0.084  # Profundidad óptica aerosoles local
    factor_agua: float = 1.0  # Corrección vapor de agua local
    pesos_ajuste: Dict[str, float] = field(default_factory=dict)
    
    # Auditoría
    numero_observaciones: int = 0
    confianza_ajuste: float = 0.0  # [0.0, 1.0]
    motivos_bloqueo: List[str] = field(default_factory=list)


@dataclass
class ResultadoAprendizajeDiagnostico:
    """Resultado de diagnóstico."""
    
    calima_detectada: bool = False
    calima_confianza: float = 0.0  # [0.0, 1.0]
    
    ensuciamiento_detectado: bool = False
    ensuciamiento_factor: float = 1.0  # [0.85, 1.0]
    
    nubosidad_fina_detectada: bool = False
    nubosidad_fina_confianza: float = 0.0
    
    # Flags de confianza por tipo de estado
    confianza_ghi: float = 1.0
    confianza_dni: float = 1.0
    confianza_dhi: float = 1.0
    confianza_radiacion_general: float = 1.0


class EstiloAprendizajeCorrectivo:
    """
    Aprendizaje CORRECTIVO: ajusta sesgos estructurales de REST2.
    
    Lento, profundo, solo en contexto limpio.
    """
    
    # Parámetros de aprendizaje
    MINIMO_OBSERVACIONES = 20  # Al menos 20 observaciones
    MEMORIA_DIAS = 14  # Olvidar datos de hace > 14 días
    
    # Umbrales de aprendizaje
    UMBRAL_CONFIDENCE_MINIMA = 0.7  # Confianza >= 70%
    
    def __init__(self):
        """Inicializa el aprendizaje correctivo."""
        self._historial_observaciones: List[Dict] = []
        self._ultimo_kt_local: float = 0.85  # Default inicial
        self._ultimo_aod_local: float = 0.084
        self._ultimo_factor_agua: float = 1.0
    
    def procesar(self,
                 ghi_modelo: float,
                 ghi_observado_estimado: float,
                 elevacion_solar_deg: float,
                 contexto_limpio: bool,
                 confianza_contexto: float,
                 timestamp: datetime) -> ResultadoAprendizajeCorrectivo:
        """
        Procesa una observación para ajuste correctivo.
        
        Args:
            ghi_modelo: GHI predicho por REST2
            ghi_observado_estimado: GHI observado/validado (confiable)
            elevacion_solar_deg: Ángulo solar
            contexto_limpio: ¿El contexto es físicamente limpio?
            confianza_contexto: Confianza general [0, 1]
            timestamp: Momento de la observación
        
        Returns:
            ResultadoAprendizajeCorrectivo
        """
        resultado = ResultadoAprendizajeCorrectivo()
        
        # PASO 1: Validar que podemos aprender
        if not contexto_limpio:
            resultado.motivos_bloqueo.append("contexto_no_limpio")
            resultado.kt_local = self._ultimo_kt_local
            resultado.factor_aod_local = self._ultimo_aod_local
            resultado.factor_agua = self._ultimo_factor_agua
            return resultado
        
        if confianza_contexto < self.UMBRAL_CONFIDENCE_MINIMA:
            resultado.motivos_bloqueo.append(
                f"confianza_baja={confianza_contexto:.2f} "
                f"< {self.UMBRAL_CONFIDENCE_MINIMA}"
            )
            resultado.kt_local = self._ultimo_kt_local
            resultado.factor_aod_local = self._ultimo_aod_local
            resultado.factor_agua = self._ultimo_factor_agua
            return resultado
        
        if elevacion_solar_deg < 15:
            resultado.motivos_bloqueo.append(
                f"elevacion_baja={elevacion_solar_deg:.1f}° < 15°"
            )
            resultado.kt_local = self._ultimo_kt_local
            resultado.factor_aod_local = self._ultimo_aod_local
            resultado.factor_agua = self._ultimo_factor_agua
            return resultado
        
        # PASO 2: Agregar observación al historial
        if ghi_modelo > 10:  # Solo si hay radiación significativa
            diferencia_ghi = ghi_observado_estimado - ghi_modelo
            
            self._historial_observaciones.append({
                "timestamp": timestamp,
                "elevacion_solar_deg": elevacion_solar_deg,
                "ghi_modelo": ghi_modelo,
                "ghi_observado": ghi_observado_estimado,
                "diferencia": diferencia_ghi,
                "confianza": confianza_contexto,
            })
        
        # PASO 3: Limpiar observaciones antiguas
        self._limpiar_historial_antiguo(timestamp)
        
        # PASO 4: Calcular ajuste si hay suficientes observaciones
        if len(self._historial_observaciones) >= self.MINIMO_OBSERVACIONES:
            resultado = self._calcular_ajuste(resultado)
        else:
            # Sin suficientes datos, mantener último conocimiento
            resultado.kt_local = self._ultimo_kt_local
            resultado.factor_aod_local = self._ultimo_aod_local
            resultado.factor_agua = self._ultimo_factor_agua
            resultado.numero_observaciones = len(self._historial_observaciones)
        
        return resultado
    
    def _limpiar_historial_antiguo(self, ahora: datetime) -> None:
        """Elimina observaciones más antiguas que MEMORIA_DIAS."""
        cutoff = ahora - timedelta(days=self.MEMORIA_DIAS)
        self._historial_observaciones = [
            obs for obs in self._historial_observaciones
            if obs["timestamp"] >= cutoff
        ]
    
    def _calcular_ajuste(self, resultado: ResultadoAprendizajeCorrectivo) -> ResultadoAprendizajeCorrectivo:
        """Calcula ajuste correctivo basado en historial."""
        
        resultado.numero_observaciones = len(self._historial_observaciones)
        
        # Calcular diferencia media ponderada por confianza
        peso_total = sum(obs["confianza"] for obs in self._historial_observaciones)
        diferencia_media = sum(
            obs["diferencia"] * obs["confianza"]
            for obs in self._historial_observaciones
        ) / peso_total if peso_total > 0 else 0
        
        # Error relativo medio
        error_relativo = sum(
            abs(obs["diferencia"] / max(obs["ghi_modelo"], 1)) * obs["confianza"]
            for obs in self._historial_observaciones
        ) / peso_total if peso_total > 0 else 0
        
        # Ajustar Kt_local (máximo +/- 10%)
        factor_kt = 1.0 + (diferencia_media / max(300, sum(
            obs["ghi_modelo"] for obs in self._historial_observaciones
        ) / len(self._historial_observaciones)))
        
        factor_kt = max(0.9, min(1.1, factor_kt))  # Acotar a ±10%
        resultado.kt_local = self._ultimo_kt_local * factor_kt
        resultado.kt_local = max(0.75, min(1.0, resultado.kt_local))
        
        # Confianza en el ajuste (mayor si error relativo es bajo)
        resultado.confianza_ajuste = max(0.0, 1.0 - error_relativo * 2)
        
        # Actualizar estado último
        self._ultimo_kt_local = resultado.kt_local
        
        logger.info(
            f"[APRENDIZAJE_CORRECTIVO] qt_local={resultado.kt_local:.3f}, "
            f"observaciones={resultado.numero_observaciones}, "
            f"confianza={resultado.confianza_ajuste:.2f}"
        )
        
        return resultado


class EstiloAprendizajeDiagnostico:
    """
    Aprendizaje DIAGNÓSTICO: detecta anomalías sin corregir.
    
    Rápido, superficial, nunca toca radiación directamente.
    """
    
    def __init__(self):
        """Inicializa el aprendizaje diagnóstico."""
        self._historial_corto: List[Dict] = []
    
    def procesar(self,
                 ghi_modelo: float,
                 ghi_observado_estimado: float,
                 elevacion_solar_deg: float,
                 temperatura_c: float,
                 humedad_rel: float) -> ResultadoAprendizajeDiagnostico:
        """
        Diagnóstico rápido de anomalías sin corrección.
        
        Args:
            ghi_modelo: GHI modelado
            ghi_observado_estimado: GHI estimado
            elevacion_solar_deg: Ángulo solar
            temperatura_c: Temperatura
            humedad_rel: Humedad relativa
        
        Returns:
            ResultadoAprendizajeDiagnostico
        """
        resultado = ResultadoAprendizajeDiagnostico()
        
        if elevacion_solar_deg < 10:
            # Noche, sin diagnóstico
            return resultado
        
        # DIAGNÓSTICO 1: Calima (aerosoles altos)
        # Síntoma: GHI observado < modelo * 0.85 + HR baja
        if ghi_observado_estimado < ghi_modelo * 0.85 and humedad_rel < 60 and elevacion_solar_deg > 20:
            resultado.calima_detectada = True
            resultado.calima_confianza = min(
                0.9,
                (1 - ghi_observado_estimado / ghi_modelo) * 2  # Máximo 90%
            )
        
        # DIAGNÓSTICO 2: Ensuciamiento gradual
        # Síntoma: DNI sistemáticamente bajo, pero algo de GHI
        # (Este es un placeholder; necesitaría más datos)
        resultado.ensuciamiento_detectado = False
        resultado.ensuciamiento_factor = 1.0
        
        # DIAGNÓSTICO 3: Nubosidad fina (Kt 0.6-0.8)
        # Síntoma: GHI significativa pero menor que clear-sky
        if 0.6 <= ghi_observado_estimado / max(ghi_modelo, 1) <= 0.8:
            resultado.nubosidad_fina_detectada = True
            resultado.nubosidad_fina_confianza = 0.6
        
        # ESTABLECER FLAGS DE CONFIANZA BASADOS EN DIAGNÓSTICOS
        resultado.confianza_radiacion_general = 1.0
        
        if resultado.calima_detectada:
            resultado.confianza_radiacion_general *= (1 - resultado.calima_confianza * 0.3)
        
        if resultado.nubosidad_fina_detectada:
            resultado.confianza_radiacion_general *= (1 - resultado.nubosidad_fina_confianza * 0.2)
        
        # DNI tiene confianza menor si hay calima
        resultado.confianza_dni = resultado.confianza_radiacion_general
        resultado.confianza_ghi = resultado.confianza_radiacion_general
        resultado.confianza_dhi = resultado.confianza_radiacion_general
        
        if resultado.calima_detectada:
            resultado.confianza_dni *= 0.8  # DNI más afectado por calima
        
        logger.debug(
            f"[DIAGNÓSTICO] calima={resultado.calima_detectada} (conf={resultado.calima_confianza:.2f}), "
            f"nubosidad_fina={resultado.nubosidad_fina_detectada}, "
            f"confianza_radiacion={resultado.confianza_radiacion_general:.2f}"
        )
        
        return resultado
