"""
Scheduler Rápido de Derivadas V51
Propósito: Calcular derivadas de radiación, humedad y presión cada 1-2 minutos
Casos de uso:
  - Detección rápida de cambios radiáticos (nubes)
  - Detección rápida de cambios de humedad (lluvia inminente)
  - Detección rápida de cambios de presión (sistemas frontales)

Flujo: Lee datos del bus → Calcula dX/dt → Publica derivadas al bus
Ejecución: Background daemon actualizado cada 1-2 minutos
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional, List
from collections import deque

try:
    from core.indices.bus_estado_global import BusEstadoGlobal
except ImportError:
    try:
        from bus_estado_global import BusEstadoGlobal
    except ImportError:
        BusEstadoGlobal = None

logger = logging.getLogger(__name__)

class CalculadorDerivadosRapidosV51:
    """
    Scheduler rápido que:
    1. Lee radiación (GHI), humedad, presión del bus cada N segundos
    2. Calcula derivadas (tasas de cambio)
    3. Publica en el bus: dGHI/dt, dHR/dt, dP/dt
    
    Derivadas calculadas:
    - dGHI/dt [W/m²/s]: Velocidad de cambio de radiación global
    - dHR/dt [%/min]: Velocidad de cambio de humedad relativa
    - dP/dt [hPa/min]: Velocidad de cambio de presión
    
    Interpretación:
    - |dGHI/dt| > 50 W/m²/s: Cambio radiativo rápido (nubes)
    - dHR/dt > 2 %/min: Aumento rápido de humedad
    - dP/dt < -1 hPa/min: Caída rápida de presión (sistema frontal)
    """
    
    def __init__(self, intervalo_segundos: int = 60, ventana_historial: int = 20):
        """
        Args:
            intervalo_segundos: Cada cuántos segundos calcular (default 60s = 1 min)
            ventana_historial: Cuántas muestras mantener en historial (default 20)
        """
        self.intervalo = intervalo_segundos
        self.ventana_historial = ventana_historial
        self.activo = False
        self.thread = None
        self.bus = None
        
        # Histórico de lecturas (mantiene último N valores)
        self.historial_ghi = deque(maxlen=ventana_historial)  # (timestamp, valor)
        self.historial_hr = deque(maxlen=ventana_historial)
        self.historial_p = deque(maxlen=ventana_historial)
        
        # Última derivada calculada
        self.derivada_ghi_actual = 0.0
        self.derivada_hr_actual = 0.0
        self.derivada_p_actual = 0.0
        
        logger.info(f"[DERIVADAS_RAPIDAS] Inicializado (intervalo={intervalo_segundos}s, ventana={ventana_historial})")
    
    def iniciar(self):
        """Inicia el scheduler en background"""
        if self.activo:
            logger.warning("[DERIVADAS_RAPIDAS] Ya está activo")
            return
        
        try:
            self.bus = BusEstadoGlobal.obtener_instancia() if BusEstadoGlobal else None
        except:
            self.bus = None
            logger.warning("[DERIVADAS_RAPIDAS] No hay bus disponible")
        
        self.activo = True
        self.thread = threading.Thread(target=self._loop_calculo, daemon=True)
        self.thread.start()
        logger.info("[DERIVADAS_RAPIDAS] ✓ Iniciado en background")
    
    def detener(self):
        """Detiene el scheduler"""
        self.activo = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("[DERIVADAS_RAPIDAS] ✓ Detenido")
    
    def _loop_calculo(self):
        """Loop principal que calcula derivadas cada N segundos"""
        while self.activo:
            try:
                self._ciclo_derivadas()
            except Exception as e:
                logger.error(f"[DERIVADAS_RAPIDAS] Error en ciclo: {e}")
            
            time.sleep(self.intervalo)
    
    def _ciclo_derivadas(self):
        """Calcula e publica todas las derivadas"""
        
        if not self.bus:
            return
        
        ahora = datetime.now()
        
        # ═══════════════════════════════════════════════════════════════════════
        # LEER DEL BUS
        # ═══════════════════════════════════════════════════════════════════════
        
        def leer_bus(clave: str, default: float = 0.0) -> float:
            """Lee un valor del bus de forma segura"""
            try:
                if hasattr(self.bus, 'obtener'):
                    val = self.bus.obtener(clave)
                    if val is not None:
                        return float(val)
                
                if hasattr(self.bus, 'consumir'):
                    val = self.bus.consumir(clave, "derivadas_rapidas_v51")
                    if val is not None:
                        return float(val)
                
                if hasattr(self.bus, '_estado') and clave in self.bus._estado:
                    return float(self.bus._estado[clave])
            except Exception as e:
                logger.debug(f"[DERIVADAS_RAPIDAS] Error leyendo '{clave}': {e}")
            
            return default
        
        # Leer valores actuales del bus
        ghi = leer_bus("radiacion_ghi_w_m2", 0.0)
        hr = leer_bus("humedad", 60.0)
        p = leer_bus("presion", 1013.25)
        
        # ═══════════════════════════════════════════════════════════════════════
        # ACTUALIZAR HISTÓRICO
        # ═══════════════════════════════════════════════════════════════════════
        
        self.historial_ghi.append((ahora, ghi))
        self.historial_hr.append((ahora, hr))
        self.historial_p.append((ahora, p))
        
        # ═══════════════════════════════════════════════════════════════════════
        # CALCULAR DERIVADAS
        # ═══════════════════════════════════════════════════════════════════════
        
        # dGHI/dt: pendiente de radiación [W/m²/s]
        self.derivada_ghi_actual = self._calcular_derivada(self.historial_ghi)
        
        # dHR/dt: pendiente de humedad [%/min]
        self.derivada_hr_actual = self._calcular_derivada(self.historial_hr, factor_tiempo=60.0)
        
        # dP/dt: pendiente de presión [hPa/min]
        self.derivada_p_actual = self._calcular_derivada(self.historial_p, factor_tiempo=60.0)
        
        # ═══════════════════════════════════════════════════════════════════════
        # PUBLICAR EN EL BUS
        # ═══════════════════════════════════════════════════════════════════════
        
        # Radiación
        self.bus.publicar(
            clave="derivada_ghi_w_m2_s",
            valor=self.derivada_ghi_actual,
            fuente="derivadas_rapidas_v51",
            metadatos={
                "unidad": "W/m²/s",
                "interpretacion": "neg=nubes, pos=clearing",
                "umbral_nube": "abs(valor) > 50",
                "actualizado": ahora.isoformat()
            }
        )
        
        # Humedad
        self.bus.publicar(
            clave="derivada_hr_porciento_min",
            valor=self.derivada_hr_actual,
            fuente="derivadas_rapidas_v51",
            metadatos={
                "unidad": "%/min",
                "interpretacion": "pos=aumento humedad",
                "umbral_lluvia": "valor > 2",
                "actualizado": ahora.isoformat()
            }
        )
        
        # Presión
        self.bus.publicar(
            clave="derivada_presion_hpa_min",
            valor=self.derivada_p_actual,
            fuente="derivadas_rapidas_v51",
            metadatos={
                "unidad": "hPa/min",
                "interpretacion": "neg=baja presión frontal",
                "umbral_sistema": "valor < -1",
                "actualizado": ahora.isoformat()
            }
        )
        
        # Resumen de derivadas
        resumen = {
            "dGHI_dt_w_m2_s": self.derivada_ghi_actual,
            "dHR_dt_pct_min": self.derivada_hr_actual,
            "dP_dt_hpa_min": self.derivada_p_actual,
            "ghi_actual_w_m2": ghi,
            "hr_actual_pct": hr,
            "p_actual_hpa": p,
            "historial_puntos": len(self.historial_ghi),
            "timestamp": ahora.isoformat()
        }
        
        self.bus.publicar(
            clave="derivadas_resumen_rapido",
            valor=resumen,
            fuente="derivadas_rapidas_v51",
            metadatos={"arquitectura": "V51_DERIVADAS_RAPIDAS"}
        )
        
        logger.debug(
            f"[DERIVADAS_RAPIDAS] dGHI={self.derivada_ghi_actual:.1f} W/m²/s, "
            f"dHR={self.derivada_hr_actual:.2f} %/min, "
            f"dP={self.derivada_p_actual:.3f} hPa/min"
        )
    
    def _calcular_derivada(
        self,
        historial: deque,
        factor_tiempo: float = 1.0
    ) -> float:
        """
        Calcula la derivada (tasa de cambio) usando regresión lineal
        
        Args:
            historial: deque con tuplas (timestamp, valor)
            factor_tiempo: Factor de conversión de tiempo
              - 1.0 para segundos (resultado en /s)
              - 60.0 para minutos (resultado en /min)
        
        Returns:
            Tasa de cambio [valor/unidad_tiempo]
        """
        
        if len(historial) < 2:
            return 0.0
        
        try:
            # Convertir temporal a lista
            datos = list(historial)
            
            # Calcular tiempo en segundos desde la primera medida
            t_inicio = datos[0][0]
            tiempos = [(d[0] - t_inicio).total_seconds() for d in datos]
            valores = [d[1] for d in datos]
            
            # Regresión lineal simple: y = a + b*x
            n = len(datos)
            if n < 2:
                return 0.0
            
            t_mean = sum(tiempos) / n
            v_mean = sum(valores) / n
            
            numerador = sum((tiempos[i] - t_mean) * (valores[i] - v_mean) for i in range(n))
            denominador = sum((tiempos[i] - t_mean) ** 2 for i in range(n))
            
            if denominador < 0.001:  # Evitar división por cero
                return 0.0
            
            # Pendiente en unidades/segundo
            pendiente_seg = numerador / denominador
            
            # Convertir según factor_tiempo
            return pendiente_seg * factor_tiempo
        
        except Exception as e:
            logger.debug(f"[DERIVADAS_RAPIDAS] Error calculando derivada: {e}")
            return 0.0


# ═════════════════════════════════════════════════════════════════════════════
# FUNCIONES GLOBALES
# ═════════════════════════════════════════════════════════════════════════════

_derivadas_global = None

def iniciar_calculador_derivadas_rapidas(intervalo_seg: int = 60) -> Optional[CalculadorDerivadosRapidosV51]:
    """Inicia el scheduler de derivadas rápido global"""
    global _derivadas_global
    
    if _derivadas_global is None:
        _derivadas_global = CalculadorDerivadosRapidosV51(intervalo_segundos=intervalo_seg)
    
    _derivadas_global.iniciar()
    logger.info("[APP] Calculador de Derivadas Rápidas iniciado")
    return _derivadas_global

def detener_calculador_derivadas_rapidas():
    """Detiene el scheduler de derivadas"""
    global _derivadas_global
    if _derivadas_global:
        _derivadas_global.detener()

def obtener_calculador_derivadas_rapidas() -> Optional[CalculadorDerivadosRapidosV51]:
    """Obtiene la instancia global del calculador de derivadas"""
    return _derivadas_global
