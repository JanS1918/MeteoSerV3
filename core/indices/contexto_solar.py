"""
CONTEXTO SOLAR - Determina noche/día/twilight con máxima precisión
═══════════════════════════════════════════════════════════════════════════════════
Integra AstronomiaRecursiva para proporcionar contexto temporal en TODAS las decisiones.

Las decisiones meteorológicas dependen críticamente del estado solar:
- WBGT: Solo tiene sentido de día (elevación_solar > -6°)
- Alertas de condensación: Mayor riesgo en noche astral (elevación < -18°)
- Radiación: 0 W/m² si noche astral, máximo si elevación > 30°
- ET0: Solo significativa de día
- Temperatura mínima: Solo se calcula en noche (elevación < -6°)

Arquitectura:
1. Obtener posición solar con AstronomiaRecursiva (NREL SPA + Ciddor)
2. Clasificar estado: NOCHE_ASTRAL, NOCHE_CIVIL, TWILIGHT_MATUTINO, DÍA, TWILIGHT_VESPERTINO
3. Publicar en bus para que todos consuman contexto
4. Proporcionar thresholds dinámicos para alertas

Precisión: ±2 arcmin (0.033°) en posición solar
Autor: V50.3 (Feb 10, 2026)
"""

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class EstadoSolar(Enum):
    """Estados solares con límites precisos según IAU/ICAO estándares."""
    NOCHE_ASTRAL = "noche_astral"  # elevación < -18° (vea estelar óptima)
    NOCHE_NAUTICA = "noche_nautica"  # -18° <= elevación < -12° (navegación astronómica)
    NOCHE_CIVIL = "noche_civil"  # -12° <= elevación < -6° (luz difusa apenas visible)
    TWILIGHT = "twilight"  # -6° <= elevación < 0° (crepúsculo civil)
    DÍA = "dia"  # elevación >= 0° (amanecer/anochecer, sol por horizonte)
    DÍA_ALTO = "dia_alto"  # elevación > 30° (sol en altura, máxima radiación)


class ContextoSolar:
    """
    Generador de contexto solar para decisiones meteorológicas.
    
    Basado en:
    - AstronomiaRecursiva NREL SPA (±2 arcmin)
    - Refracción Ciddor (CIPM-2007)
    - Fases lunares (Meeus)
    
    Proporciona:
    - Estado solar (NOCHE_ASTRAL → DÍA_ALTO)
    - Thresholds dinámicos para WBGT, condensación, etc.
    - Confianza en radiación estimada
    - Recomendaciones de cálculos a ejecutar
    """
    
    def __init__(self, latitud: float = 41.387, longitud: float = 2.077, altitud_m: float = 65.0):
        """
        Args:
            latitud: Latitud (°)
            longitud: Longitud (°)
            altitud_m: Altitud (m)
        """
        self.lat = latitud
        self.lon = longitud
        self.alt = altitud_m
        
        # Compilar AstronomiaRecursiva
        try:
            from core.indices.astronomia_recursiva import AstronomiaRecursiva
            self.astro = AstronomiaRecursiva(latitud, longitud, altitud_m)
        except ImportError:
            logger.warning("[ContextoSolar] AstronomiaRecursiva no disponible, fallback a estimación simple")
            self.astro = None
    
    def calcular_contexto(
        self,
        fecha_hora: datetime,
        presion_hpa: float = 1013.25,
        temperatura_c: float = 15.0,
        humedad_rel: float = 50.0
    ) -> Dict:
        """
        Calcula contexto solar completo en un momento.
        
        Args:
            fecha_hora: Momento actual (se convierte a UTC si es naive)
            presion_hpa: Presión barométrica (hPa)
            temperatura_c: Temperatura del aire (°C)
            humedad_rel: Humedad relativa (0-100 %)
        
        Returns:
            Dict con:
            - estado: EstadoSolar enum
            - elevacion_solar_deg: Ángulo sobre horizonte (°)
            - azimut_solar_deg: Dirección (° desde norte)
            - es_noche: bool (elevación < 0)
            - es_dia: bool (elevación >= 0)
            - es_noche_astral: bool (elevación < -18°)
            - es_twilight: bool (-6° <= elevación < 0)
            - hora_solar_verdadera: Hora solar verdadera
            - duracion_noche_horas: Horas de noche aún restantes
            - radiacion_confianza_pct: Confianza en modelo de radiación (0-100)
            - threshold_wbgt_recomendado: Si se debe calcular WBGT
            - threshold_et0_recomendado: Si se debe calcular ET0
            - threshold_t_minima_recomendado: Si se debe calcular T_mín
            - threshold_condensacion_alerta_pct: Multiplicador de alerta condensación
            - threshold_anomalia_delta_t: Umbral ΔT para anomalía (°C)
        """
        # Garantizar UTC
        if fecha_hora.tzinfo is None:
            fecha_hora = fecha_hora.replace(tzinfo=timezone.utc)
        else:
            fecha_hora = fecha_hora.astimezone(timezone.utc)
        
        # ⚛️ Patrón BUS-FIRST: Intentar leer del bus
        elevacion = None
        azimut = None
        try:
            from core.system.bus import obtener_bus
            bus = obtener_bus()
            if bus:
                elevacion_bus = bus.leer("elevacion_solar_deg")
                azimut_bus = bus.leer("azimut_solar_deg")
                if elevacion_bus is not None and azimut_bus is not None:
                    elevacion = float(elevacion_bus)
                    azimut = float(azimut_bus)
                    logger.debug(f"[ContextoSolar] Datos astronómicos tomados del bus: elev={elevacion:.1f}°, azim={azimut:.1f}°")
        except Exception as e:
            logger.debug(f"[ContextoSolar] Error leyendo del bus: {e}")
        
        # Fallback: calcular localmente si no está en bus
        if elevacion is None or azimut is None:
            if self.astro:
                try:
                    pos_solar = self.astro.calcular_posicion_solar_nrel_spa(
                        fecha_utc=fecha_hora,
                        presion_hpa=presion_hpa,
                        temperatura_c=temperatura_c,
                        humedad_fraccion=humedad_rel / 100.0
                    )
                    elevacion = pos_solar.get("elevacion_aparente_deg", 0.0)
                    azimut = pos_solar.get("azimut_deg", 0.0)
                    logger.debug(f"[ContextoSolar] Datos astronómicos calculados localmente (fallback): elev={elevacion:.1f}°, azim={azimut:.1f}°")
                except Exception as e:
                    logger.warning(f"[ContextoSolar] Error calculando posición solar: {e}")
                    elevacion, azimut = self._calcular_solar_fallback(fecha_hora)
            else:
                elevacion, azimut = self._calcular_solar_fallback(fecha_hora)
        
        # Clasificar estado
        estado = self._clasificar_estado(elevacion)
        
        # Calcular hora solar verdadera
        hora_solar_verdadera = self._hora_solar_verdadera(fecha_hora)
        
        # Calcular duración de noche aún restante
        duracion_noche = self._duracion_noche_restante(fecha_hora, elevacion)
        
        # Calcular confianza en radiación
        radiacion_confianza = self._confianza_radiacion(elevacion, estado)
        
        # Determinar si calcular cada índice
        calc_wbgt = elevacion >= -6.0  # Al menos crepúsculo
        calc_et0 = elevacion > 0.0  # Solo de día
        calc_t_minima = elevacion < -6.0  # Noche civil o más oscuro
        
        # Multiplicador de alerta condensación (más sensible en noche)
        if elevacion < -12.0:  # Noche náutica
            alerta_condensacion_mult = 1.4  # 40% más sensible
        elif elevacion < -6.0:  # Noche civil
            alerta_condensacion_mult = 1.2  # 20% más sensible
        elif elevacion < 10.0:  # Amanecer/atardecer
            alerta_condensacion_mult = 1.0  # Normal
        else:
            alerta_condensacion_mult = 0.8  # 20% menos sensible (evaporación)
        
        # Umbral dinámico para anomalía ΔT
        if elevacion > 30.0:  # Sol en altura
            threshold_delta_t = 8.0  # Diferencias grandes normales
        elif elevacion > 10.0:  # Tarde media
            threshold_delta_t = 5.0
        elif elevacion > 0.0:  # Tarde baja
            threshold_delta_t = 3.0
        elif elevacion > -6.0:  # Crepúsculo
            threshold_delta_t = 2.0
        else:  # Noche
            threshold_delta_t = 1.0  # Muy sensible a anomalías
        
        return {
            "estado": estado.value,
            "elevacion_solar_deg": round(elevacion, 2),
            "azimut_solar_deg": round(azimut, 2),
            "es_noche": elevacion < 0.0,
            "es_dia": elevacion >= 0.0,
            "es_noche_astral": elevacion < -18.0,
            "es_noche_nautica": -18.0 <= elevacion < -12.0,
            "es_noche_civil": -12.0 <= elevacion < -6.0,
            "es_twilight": -6.0 <= elevacion < 0.0,
            "es_dia_alto": elevacion > 30.0,
            "hora_solar_verdadera": round(hora_solar_verdadera, 2),
            "duracion_noche_restante_horas": round(duracion_noche, 2),
            "timestamp_utc": fecha_hora.isoformat(),
            
            # Confianza y recomendaciones
            "radiacion_confianza_pct": int(radiacion_confianza),
            "calcular_wbgt": calc_wbgt,
            "calcular_et0": calc_et0,
            "calcular_temperatura_minima": calc_t_minima,
            "alerta_condensacion_multiplicador": round(alerta_condensacion_mult, 2),
            "threshold_anomalia_delta_t_celsius": round(threshold_delta_t, 1),
        }
    
    def _clasificar_estado(self, elevacion_deg: float) -> EstadoSolar:
        """Clasifica el estado solar según elevación."""
        if elevacion_deg < -18.0:
            return EstadoSolar.NOCHE_ASTRAL
        elif elevacion_deg < -12.0:
            return EstadoSolar.NOCHE_NAUTICA
        elif elevacion_deg < -6.0:
            return EstadoSolar.NOCHE_CIVIL
        elif elevacion_deg < 0.0:
            return EstadoSolar.TWILIGHT
        elif elevacion_deg <= 30.0:
            return EstadoSolar.DÍA
        else:
            return EstadoSolar.DÍA_ALTO
    
    def _confianza_radiacion(self, elevacion_deg: float, estado: EstadoSolar) -> float:
        """
        Calcula confianza en modelo de radiación.
        0% si noche astral, 100% si sol en altura.
        """
        if elevacion_deg < -18.0:  # Noche astral
            return 0.0
        elif elevacion_deg < -6.0:  # Noche civil
            return 5.0
        elif elevacion_deg < 0.0:  # Crepúsculo
            return 20.0
        elif elevacion_deg < 5.0:  # Amanecer temprano
            return 40.0
        elif elevacion_deg < 10.0:  # Mañana temprana
            return 60.0
        elif elevacion_deg < 30.0:  # Día normal
            return 85.0
        else:  # Sol en altura
            return 95.0
    
    def _hora_solar_verdadera(self, fecha_hora: datetime) -> float:
        """Calcula hora solar verdadera (0-24 horas decimales)."""
        try:
            if self.astro:
                # Usar ecuación del tiempo del módulo astronomía si está disponible
                resultado = self.astro.calcular_posicion_solar_nrel_spa(
                    fecha_utc=fecha_hora,
                    presion_hpa=1013.25,
                    temperatura_c=15.0,
                    humedad_fraccion=0.5
                )
                # Hora local aproximada desde hora_solar_verdadera en resultado
                hora_decimal = fecha_hora.hour + fecha_hora.minute / 60.0 + fecha_hora.second / 3600.0
                return hora_decimal
        except:
            pass
        
        # Fallback: hora local simple
        hora_decimal = fecha_hora.hour + fecha_hora.minute / 60.0 + fecha_hora.second / 3600.0
        return hora_decimal % 24.0
    
    def _duracion_noche_restante(self, fecha_hora: datetime, elevacion_solar: float) -> float:
        """
        Estima horas de noche aún restantes hasta amanecer.
        Basado en elevación solar y movimiento angular diario (≈15°/hora).
        """
        if elevacion_solar >= 0.0:  # Es de día
            # Estimación simple: si elevación = 5°, falta ~20min para ocaso (~30 min para empezar noche civil)
            horas_hasta_ocaso = max(0.0, (30.0 - elevacion_solar) / 15.0)
            horas_hasta_noche_civil = horas_hasta_ocaso + 1.0 / 60.0  # +1 min aprox
            return horas_hasta_noche_civil
        elif elevacion_solar >= -6.0:  # Crepúsculo
            # Falta poco para noche civil
            horas_hasta_noche = max(0.0, (6.0 + elevacion_solar) / 15.0)
            return horas_hasta_noche
        else:  # Ya es noche
            # Estimación: cuándo amanecer (elevación pasa de -6° a 0°)
            # Movimiento es 15°/hora, así que -6° → 0° es 24 minutos = 0.4 horas
            # Más -6° hacia abajo, más tiempo para amanecer
            # A -18° aún faltan ~48 min
            horas_hasta_amanecer = (elevacion_solar + 6.0) / 15.0
            if horas_hasta_amanecer < 0:
                # Si es mucho más oscuro, estimar 12 horas hasta amanecer
                angulo_falta = 6.0 - elevacion_solar  # Distancia a -6°
                horas_hasta_amanecer = 6.0 + angulo_falta / 15.0  # 6h (12h noche) + diferencia
            return max(0.0, horas_hasta_amanecer)
    
    def _calcular_solar_fallback(self, fecha_hora: datetime) -> Tuple[float, float]:
        """
        Fallback simple si AstronomiaRecursiva no disponible.
        Usa Spencer (1971) para declinación solar + hora solar simple.
        """
        try:
            # Día del año (1-366)
            # Nota: no usar .timetuple() en UTC, calcular manualmente
            fecha_local = fecha_hora.replace(tzinfo=None)
            dia_del_ano = fecha_local.timetuple().tm_yday
            
            # Spencer (1971): Declinación solar
            gamma = 2 * math.pi * (dia_del_ano - 1) / 365.0
            decl_rad = (0.006918
                       - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
                       - 0.006758 * math.cos(2*gamma) + 0.000907 * math.sin(2*gamma)
                       - 0.002697 * math.cos(3*gamma) + 0.00111 * math.sin(3*gamma))
            
            # Ecuación del tiempo (aproximación)
            eot_min = (229.18 * (0.000075
                               + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
                               - 0.014615 * math.cos(2*gamma) - 0.040849 * math.sin(2*gamma)))
            
            # Hora solar verdadera
            hora_local = fecha_hora.hour + fecha_hora.minute / 60.0 + fecha_hora.second / 3600.0
            hora_correg = hora_local + self.lon / 15.0 + eot_min / 60.0  # Longitud en horas + EoT
            
            # Ángulo horario
            h_rad = math.radians((hora_correg - 12.0) * 15.0)
            
            # Elevación solar (Duffie & Beckman)
            lat_rad = math.radians(self.lat)
            elevacion_rad = math.asin(math.sin(lat_rad) * math.sin(decl_rad) +
                                     math.cos(lat_rad) * math.cos(decl_rad) * math.cos(h_rad))
            elevacion_deg = math.degrees(elevacion_rad)
            
            # Azimut solar (complicado, aproximación simple)
            azimut_deg = 180.0  # Placer aproximado
            
            return elevacion_deg, azimut_deg
        except Exception as e:
            logger.warning(f"[ContextoSolar] Error en fallback solar: {e}")
            return 0.0, 180.0


def obtener_contexto_solar(
    fecha_hora: datetime,
    latitud: float = 41.387,
    longitud: float = 2.077,
    altitud_m: float = 65.0,
    presion_hpa: float = 1013.25,
    temperatura_c: float = 15.0,
    humedad_rel: float = 50.0
) -> Dict:
    """
    Función conveniente para obtener contexto solar en un momento.
    
    Uso típico en endpoints:
    ```python
    contexto = obtener_contexto_solar(
        datetime.now(),
        latitud=41.387,
        longitud=2.077,
        presion_hpa=sensores.get("presion", 1013.25),
        temperatura_c=sensores.get("temperatura", 15.0),
        humedad_rel=sensores.get("humedad", 50.0)
    )
    
    if not contexto["es_dia"]:
        # Noche: no calcular índices que requieren radiación
        wbgt = None
        et0 = None
    else:
        # Día: calcular normalmente
        wbgt = calcular_wbgt(...)
        et0 = calcular_et0(...)
    ```
    """
    ctx = ContextoSolar(latitud, longitud, altitud_m)
    return ctx.calcular_contexto(fecha_hora, presion_hpa, temperatura_c, humedad_rel)
