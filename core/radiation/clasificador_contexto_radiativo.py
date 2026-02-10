"""
═══════════════════════════════════════════════════════════════════════════════
CLASIFICADOR DE CONTEXTO RADIATIVO - Motor de Decisión de Aprendizaje
═══════════════════════════════════════════════════════════════════════════════

Responsabilidad única: Determinar si el contexto es físicamente limpio para aprendizaje.

No aprende por defecto. Solo aprende cuando el contexto radiativo es limpio y sin ambigüedad.

Reglas de decisión:
- SOL < 10°: BLOQUEADO (amanecer/ocaso, geometría no confiable)
- LLUVIA: BLOQUEADO (radiación enmascarada)
- NIEBLA densa (visibilidad < 5km): BLOQUEADO
- NUBOSIDAD rápida (derivada GHI > threshold): BLOQUEADO
- VIENTO fuerte + sol bajo: BLOQUEADO
- HR extrema (< 20% o > 95%): DEGRADADO (menor confianza)
- Contexto estable, sol > 15°, sin precipitación: ABIERTO (aprendizaje permitido)

Autor: Sistema Robusto MeteoSerV3
Fecha: Feb 10, 2026
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EstadoContextoRadiativo:
    """Estado completo del contexto radiativo en un momento."""
    
    # Variables entrada
    timestamp: datetime
    elevacion_solar_deg: float
    ghi_w_m2: float
    presion_hpa: float
    humedad_rel: float
    temperatura_c: float
    velocidad_viento_ms: float
    precipitacion_mm: float
    visibilidad_km: Optional[float] = None
    
    # Derivadas (calculadas)
    derivada_ghi_w_m2_s: float = 0.0  # dGHI/dt
    
    # Clasificación (generada por clasificador)
    es_valido_para_aprendizaje: bool = False
    confianza_general: float = 1.0  # [0.0, 1.0]
    motivos_bloqueo: List[str] = None
    motivos_degradacion: List[str] = None
    
    def __post_init__(self):
        if self.motivos_bloqueo is None:
            self.motivos_bloqueo = []
        if self.motivos_degradacion is None:
            self.motivos_degradacion = []


class ClasificadorContextoRadiativo:
    """
    Motor de decisión que clasifica el contexto radiativo.
    
    Paradigma: EL SISTEMA NO APRENDE POR DEFECTO.
    Solo aprende cuando todas las condiciones físicas son claras.
    """
    
    # Umbrales duros (no negociables)
    ELEVACION_SOLAR_MINIMA_APRENDIZAJE = 15.0  # Grados
    ELEVACION_SOLAR_MINIMA_OPERATORIA = 10.0  # Grados (para leer sensores)
    
    # Umbrales de nubosidad rápida
    DERIVADA_GHI_MAX_W_M2_S = 50.0  # W/m²/s - cambio rápido = nubes transitivas
    
    # Umbrales de precipitación
    UMBRAL_LLUVIA_MINIMA_MM = 0.5  # mm en 1 minuto = lluvia
    
    # Umbrales de visibilidad (niebla)
    UMBRAL_VISIBILIDAD_MIN_KM = 5.0  # km < 5km = niebla densa
    
    # Umbrales de viento crítico
    VIENTO_FUERTE_MS = 8.0  # m/s (29 km/h)
    
    # HR extrema
    HR_BAJA_MINIMA = 20.0  # % - aire demasiado seco
    HR_ALTA_MAXIMA = 95.0  # % - aire demasiado húmedo
    
    def __init__(self):
        """Inicializa el clasificador."""
        self._historial_ghi: List[Tuple[datetime, float]] = []
        self._historial_max_size = 60  # Últimos 60 segundos
        self._ultimo_contexto: Optional[EstadoContextoRadiativo] = None
    
    def clasificar(self, estado: EstadoContextoRadiativo) -> EstadoContextoRadiativo:
        """
        Clasifica el contexto radiativo actual.
        
        Args:
            estado: EstadoContextoRadiativo con datos sensoriales
        
        Returns:
            EstadoContextoRadiativo clasificado (con flags y confianza)
        """
        estado.motivos_bloqueo = []
        estado.motivos_degradacion = []
        
        # PASO 1: Validación de entrada
        if not self._validar_entrada(estado):
            estado.es_valido_para_aprendizaje = False
            estado.confianza_general = 0.0
            return estado
        
        # PASO 2: Calcular derivada GHI (cambio rápido)
        estado.derivada_ghi_w_m2_s = self._calcular_derivada_ghi(estado)
        
        # PASO 3: Aplicar reglas de bloqueo (duro)
        self._aplicar_reglas_bloqueo(estado)
        
        # PASO 4: Aplicar reglas de degradación (confianza)
        self._aplicar_reglas_degradacion(estado)
        
        # PASO 5: Decidir validez global
        estado.es_valido_para_aprendizaje = (
            len(estado.motivos_bloqueo) == 0
        )
        
        # PASO 6: Calcular confianza según degradaciones
        estado.confianza_general = self._calcular_confianza(estado)
        
        # PASO 7: Registro y auditoría
        self._registrar_clasificacion(estado)
        self._ultimo_contexto = estado
        
        return estado
    
    def _validar_entrada(self, estado: EstadoContextoRadiativo) -> bool:
        """Valida que la entrada tenga datos mínimos."""
        if estado.elevacion_solar_deg < 0:
            logger.warning("[CONTEXTO] Elevación solar negativa (noche)")
            return False
        
        if estado.ghi_w_m2 < 0:
            logger.warning("[CONTEXTO] GHI negativa (sensor defectuoso)")
            return False
        
        if estado.humedad_rel < 0 or estado.humedad_rel > 100:
            logger.warning("[CONTEXTO] HR fuera de rango")
            return False
        
        if estado.presion_hpa < 850 or estado.presion_hpa > 1050:
            logger.warning("[CONTEXTO] Presión fuera de rango (sensor defectuoso)")
            return False
        
        return True
    
    def _calcular_derivada_ghi(self, estado: EstadoContextoRadiativo) -> float:
        """
        Calcula la derivada temporal de GHI.
        
        dGHI/dt alta = nubes transitivas rápidas
        """
        ahora = estado.timestamp
        
        # Mantener historial
        self._historial_ghi.append((ahora, estado.ghi_w_m2))
        
        # Limpiar histórico antiguo (> 60 segundos)
        cutoff = ahora - timedelta(seconds=60)
        self._historial_ghi = [(ts, val) for ts, val in self._historial_ghi 
                               if ts >= cutoff]
        
        # Si hay menos de 2 puntos, no calcular derivada
        if len(self._historial_ghi) < 2:
            return 0.0
        
        # Calcular derivada lineal simple
        # (último punto) - (primer punto antiguo)
        ts_primero, ghi_primero = self._historial_ghi[0]
        ts_ultimo, ghi_ultimo = self._historial_ghi[-1]
        
        dt_segundos = (ts_ultimo - ts_primero).total_seconds()
        if dt_segundos < 1:
            return 0.0
        
        derivada = (ghi_ultimo - ghi_primero) / dt_segundos
        
        return derivada
    
    def _aplicar_reglas_bloqueo(self, estado: EstadoContextoRadiativo) -> None:
        """Aplica reglas de BLOQUEO DURO (aprendizaje NO permitido)."""
        
        # REGLA 1: Sol muy bajo (amanecer/ocaso)
        if estado.elevacion_solar_deg < self.ELEVACION_SOLAR_MINIMA_APRENDIZAJE:
            estado.motivos_bloqueo.append(
                f"elevacion_solar={estado.elevacion_solar_deg:.1f}° "
                f"< {self.ELEVACION_SOLAR_MINIMA_APRENDIZAJE}°"
            )
        
        # REGLA 2: Lluvia detectada
        if estado.precipitacion_mm > self.UMBRAL_LLUVIA_MINIMA_MM:
            estado.motivos_bloqueo.append(
                f"lluvia={estado.precipitacion_mm:.2f}mm "
                f"> {self.UMBRAL_LLUVIA_MINIMA_MM}mm"
            )
        
        # REGLA 3: Niebla densa (baja visibilidad)
        if estado.visibilidad_km is not None and \
           estado.visibilidad_km < self.UMBRAL_VISIBILIDAD_MIN_KM:
            estado.motivos_bloqueo.append(
                f"niebla (visibilidad={estado.visibilidad_km:.1f}km "
                f"< {self.UMBRAL_VISIBILIDAD_MIN_KM}km)"
            )
        
        # REGLA 4: Nubosidad rápida (derivada GHI alta)
        if abs(estado.derivada_ghi_w_m2_s) > self.DERIVADA_GHI_MAX_W_M2_S:
            estado.motivos_bloqueo.append(
                f"nubosidad_rapida (dGHI/dt={estado.derivada_ghi_w_m2_s:.1f}W/m²/s "
                f"> {self.DERIVADA_GHI_MAX_W_M2_S}W/m²/s)"
            )
        
        # REGLA 5: Viento fuerte + sol bajo (confusión sensor)
        if estado.elevacion_solar_deg < 30 and estado.velocidad_viento_ms > self.VIENTO_FUERTE_MS:
            estado.motivos_bloqueo.append(
                f"viento_fuerte_sol_bajo "
                f"(viento={estado.velocidad_viento_ms:.1f}m/s, "
                f"elevacion={estado.elevacion_solar_deg:.1f}°)"
            )
    
    def _aplicar_reglas_degradacion(self, estado: EstadoContextoRadiativo) -> None:
        """Aplica reglas que DEGRADAN CONFIANZA (pero no bloquean)."""
        
        # REGLA 1: HR extrema (aire anómalo)
        if estado.humedad_rel < self.HR_BAJA_MINIMA:
            estado.motivos_degradacion.append(
                f"hr_baja={estado.humedad_rel:.1f}% "
                f"< {self.HR_BAJA_MINIMA}%"
            )
        
        if estado.humedad_rel > self.HR_ALTA_MAXIMA:
            estado.motivos_degradacion.append(
                f"hr_alta={estado.humedad_rel:.1f}% "
                f"> {self.HR_ALTA_MAXIMA}%"
            )
        
        # REGLA 2: Viento moderado (aunque no muy bajo)
        # No bloquea, pero reduce confianza
        if 5.0 <= estado.velocidad_viento_ms <= self.VIENTO_FUERTE_MS:
            # Solo nota en log, no es motivo formal
            pass
        
        # REGLA 3: Cambio moderado GHI (no es rápido, pero notable)
        if 20 < abs(estado.derivada_ghi_w_m2_s) <= self.DERIVADA_GHI_MAX_W_M2_S:
            estado.motivos_degradacion.append(
                f"nubosidad_moderada (dGHI/dt={estado.derivada_ghi_w_m2_s:.1f}W/m²/s)"
            )
    
    def _calcular_confianza(self, estado: EstadoContextoRadiativo) -> float:
        """
        Calcula confianza general [0.0, 1.0] basada en degradaciones.
        
        Confianza máxima: 1.0 (contexto limpio)
        Confianza mínima: 0.0 (bloqueado, aunque no se usa si está bloqueado)
        """
        confianza = 1.0
        
        # Cada degradación resta un porcentaje
        degradaciones_peso = {
            "hr_baja": -0.1,
            "hr_alta": -0.1,
            "nubosidad_moderada": -0.15,
        }
        
        for motivo in estado.motivos_degradacion:
            for clave, penalidad in degradaciones_peso.items():
                if clave in motivo:
                    confianza += penalidad
                    break
        
        confianza = max(0.0, min(1.0, confianza))
        
        return confianza
    
    def _registrar_clasificacion(self, estado: EstadoContextoRadiativo) -> None:
        """Registra la clasificación for auditoría."""
        if estado.es_valido_para_aprendizaje:
            logger.info(
                f"[CONTEXTO] ABIERTO para aprendizaje "
                f"(elev={estado.elevacion_solar_deg:.1f}°, "
                f"confianza={estado.confianza_general:.2f})"
            )
        else:
            motivos = ", ".join(estado.motivos_bloqueo)
            logger.warning(
                f"[CONTEXTO] BLOQUEADO para aprendizaje: {motivos}"
            )
    
    def obtener_ultimo_contexto(self) -> Optional[EstadoContextoRadiativo]:
        """Retorna el último contexto clasificado."""
        return self._ultimo_contexto
    
    def resetear_historial(self) -> None:
        """Resetea el historial (ej: al cambiar de día)."""
        self._historial_ghi.clear()
        logger.info("[CONTEXTO] Historial GHI reseteado")
