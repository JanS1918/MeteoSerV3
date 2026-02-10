"""
Calculador automático de índices ambientales V51
Flujo: Lee radiación + temperatura del bus → Calcula índices → Publica TODO en el bus
Ejecución: Scheduler cada 5 minutos en background
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional

try:
    from core.indices.bus_estado_global import BusEstadoGlobal
except ImportError:
    try:
        from bus_estado_global import BusEstadoGlobal
    except ImportError:
        BusEstadoGlobal = None

try:
    from core.scheduler.integrador_prediction_engine_v51 import obtener_integrador_prediction_engine
except ImportError:
    def obtener_integrador_prediction_engine():
        return None

logger = logging.getLogger(__name__)

class CalculadorIndicesAutomatico:
    """
    Scheduler que:
    1. Lee radiación (GHI, DNI, DHI) del bus
    2. Lee temperatura, humedad, presión, viento del bus
    3. Calcula WBGT, ET0, T_min, UTCI
    4. Publica TODO en el bus
    """
    
    def __init__(self, intervalo_segundos: int = 300):
        """
        Args:
            intervalo_segundos: Cada cuántos segundos calcular (default 5 min)
        """
        self.intervalo = intervalo_segundos
        self.activo = False
        self.thread = None
        self.bus = None
        self.alerta_lluvia = None  # Se inicializa después que el bus
        self.integrador_prediccion = None  # Se inicializa si available
        logger.info(f"[SCHEDULER] Calculador de Índices inicializado (intervalo={intervalo_segundos}s)")
    
    def iniciar(self):
        """Inicia el scheduler en background"""
        if self.activo:
            logger.warning("[SCHEDULER] Ya está activo")
            return
        
        try:
            self.bus = BusEstadoGlobal.obtener_instancia() if BusEstadoGlobal else None
        except:
            self.bus = None
            logger.warning("[SCHEDULER] No hay bus disponible")
        
        # Inicializar la alerta de lluvia
        try:
            from core.prediction.alerta_lluvia_inminente_v51 import AlertaLluviaInminenteV51
            self.alerta_lluvia = AlertaLluviaInminenteV51()
        except Exception as e:
            logger.warning(f"[SCHEDULER] No se pudo inicializar AlertaLluviaInminente: {e}")
            self.alerta_lluvia = None
        
        # Inicializar integrador de prediction_engine (Opción 3)
        try:
            integrador = obtener_integrador_prediction_engine()
            if integrador and integrador.disponible:
                self.integrador_prediccion = integrador
                logger.info("[SCHEDULER] Integrador prediction_engine disponible")
            else:
                self.integrador_prediccion = None
        except Exception as e:
            logger.debug(f"[SCHEDULER] Prediction_engine no disponible: {e}")
            self.integrador_prediccion = None
        
        self.activo = True
        self.thread = threading.Thread(target=self._loop_calculo, daemon=True)
        self.thread.start()
        logger.info("[SCHEDULER] ✓ Iniciado en background")
    
    def detener(self):
        """Detiene el scheduler"""
        self.activo = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("[SCHEDULER] ✓ Detenido")
    
    def _loop_calculo(self):
        """Loop principal que se ejecuta cada N segundos"""
        while self.activo:
            try:
                self._ciclo_calculo()
            except Exception as e:
                logger.error(f"[SCHEDULER] Error en ciclo: {e}")
            
            # Esperar hasta el siguiente ciclo
            time.sleep(self.intervalo)
    
    def _ciclo_calculo(self):
        """Calcula e publica todos los índices"""
        
        # ═══════════════════════════════════════════════════════════════════════
        # LEER DEL BUS
        # ═══════════════════════════════════════════════════════════════════════
        
        if not self.bus:
            return
        
        # Función auxiliar para leer del bus de forma segura
        def leer_bus(clave: str, default: float = 0.0) -> float:
            """Lee un valor del bus de forma segura"""
            try:
                # Intentar método obtener (BusEstadoGlobal)
                if hasattr(self.bus, 'obtener'):
                    val = self.bus.obtener(clave)
                    if val is not None:
                        return float(val)
                
                # Intentar método consumir
                if hasattr(self.bus, 'consumir'):
                    val = self.bus.consumir(clave, "scheduler_v51")
                    if val is not None:
                        return float(val)
                
                # Intentar acceso directo
                if hasattr(self.bus, '_estado') and clave in self.bus._estado:
                    return float(self.bus._estado[clave])
                
            except Exception as e:
                logger.debug(f"[SCHEDULER] Error leyendo '{clave}': {e}")
            
            return default
        
        # Radiación
        ghi = leer_bus("radiacion_ghi_w_m2", 0.0)
        dni = leer_bus("radiacion_dni_w_m2", 0.0)
        dhi = leer_bus("radiacion_dhi_w_m2", 0.0)
        
        # Temperatura y humedad
        temp_c = leer_bus("temperatura", 20.0)
        humedad = leer_bus("humedad", 60.0)
        presion = leer_bus("presion", 1013.25)
        
        # Viento
        viento_ms = leer_bus("velocidad_viento", 1.0)
        viento_kmh = viento_ms * 3.6
        
        # Contexto solar
        elevacion_solar = leer_bus("elevacion_solar", 0.0)
        
        # Si es noche (elevación < -6°), no calcular índices
        if elevacion_solar < -6:
            return
        
        # ═══════════════════════════════════════════════════════════════════════
        # CALCULAR INDICES
        # ═══════════════════════════════════════════════════════════════════════
        
        try:
            from core.indices.environmental_indices import (
                wbgt_liljegren_completo,
                calcular_et0_con_aprendizaje,
                utci_v4_02_fiala_completo
            )
            from core.prediction.alerta_lluvia_inminente_v51 import AlertaLluviaInminenteV51
            
            # WBGT (Wet Bulb Globe Temperature)
            try:
                wbgt_result = wbgt_liljegren_completo(
                    t_a=temp_c,
                    rh=humedad,
                    v=viento_ms,
                    rad=ghi,
                    pa=presion / 10.0  # Convert hPa to kPa
                )
                self._publicar_wbgt(wbgt_result)
            except Exception as e:
                logger.warning(f"[SCHEDULER] Error en WBGT: {e}")
            
            # ET0 (Evapotranspiración de referencia) - Usa radiación consigue mejorada
            try:
                et0_result = calcular_et0_con_aprendizaje(
                    temp_c=temp_c,
                    humedad=humedad,
                    radiacion=ghi,
                    viento=viento_ms,
                    hora_solar=None,
                    elevacion_solar=elevacion_solar,
                    presion_kpa=presion / 10.0
                )
                if et0_result and isinstance(et0_result, (int, float)):
                    self.bus.publicar(
                        clave="et0_mm_dia",
                        valor=float(et0_result),
                        fuente="scheduler_v51",
                        metadatos={"modelo": "FAO-56_Penman-Monteith", "radiacion": "V51"}
                    )
            except Exception as e:
                logger.debug(f"[SCHEDULER] ET0 error: {e}")
            
            # T_min (Temperatura mínima) - Usa radiación nocturna predicha
            # [PENDIENTE] Necesita función calcular_temperatura_minima del módulo Deardorff
            # Por ahora comentado hasta integración completa
            #try:
            #    t_min_result = temperatura_minima_deardorff_v46_5(...)
            #    # Publicar T_min
            #except Exception as e:
            #    logger.debug(f"[SCHEDULER] T_min: {e}")
            
            # UTCI (Universal Thermal Climate Index)
            try:
                # Estimar MRT desde radiación
                tmrt_estimated = temp_c + (ghi / 100.0) if ghi > 0 else temp_c + 2.0
                presion_kpa = presion / 10.0
                
                utci_result = utci_v4_02_fiala_completo(
                    temp_c,           # t_a
                    humedad,          # RH  
                    viento_ms,        # v_a
                    tmrt_estimated,   # tmrt_estimado
                    presion_kpa       # presion kPa
                )
                
                if utci_result and isinstance(utci_result, dict):
                    wbgt_utci = utci_result.get("utci", None)
                    if wbgt_utci:
                        self.bus.publicar(
                            clave="utci_indice_termico",
                            valor=float(wbgt_utci),
                            fuente="scheduler_v51",
                            metadatos={"modelo": "UTCI v4.02_Fiala", "radiacion": "V51"}
                        )
            except Exception as e:
                logger.debug(f"[SCHEDULER] UTCI: {e}")
        
        except ImportError as e:
            logger.warning(f"[SCHEDULER] No se pueden importar funciones: {e}")
            return
        
        # ═══════════════════════════════════════════════════════════════════════
        # ÍNDICES SIMPLES (sin radiación)
        # ═══════════════════════════════════════════════════════════════════════
        
        try:
            from core.indices.environmental_indices import (
                punto_rocio_magnus
            )
            
            # Punto de rocío
            try:
                pr = punto_rocio_magnus(temp_c, humedad)
                self.bus.publicar(
                    clave="punto_rocio_termometrico",
                    valor=float(pr),
                    fuente="scheduler_v51",
                    metadatos={"unidad": "°C"}
                )
            except:
                pass
            
        except Exception as e:
            logger.debug(f"[SCHEDULER] Índices simples: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # ALERTA DE LLUVIA INMINENTE (OPCIÓN 1: Integración en scheduler)
        # ═══════════════════════════════════════════════════════════════════════
        
        if self.alerta_lluvia and self.bus:
            try:
                # Preparar datos del bus para la alerta
                datos_alerta = {
                    "ghi_w_m2": ghi,
                    "humedad": humedad,
                    "presion": presion,
                    "temperatura": temp_c,
                    "dt_solar": leer_bus("dt_solar_grados", 0.0),  # ΔT sol/sombra
                    "timestamp": datetime.now()
                }
                
                # Evaluar alerta
                resultado_alerta = self.alerta_lluvia.evaluar(datos_alerta)
                
                # Publicar resultado en el bus
                self.bus.publicar(
                    clave="alerta_lluvia_inminente_score",
                    valor=resultado_alerta.get("score", 0),
                    fuente="scheduler_v51",
                    metadatos={
                        "eta_minutos": resultado_alerta.get("eta_minutos", 0),
                        "confianza": resultado_alerta.get("confianza", 0),
                        "modelo": "AlertaLluviaInmediata_V51"
                    }
                )
                
                # Publicar componentes de la alerta
                componentes = resultado_alerta.get("componentes", {})
                self.bus.publicar(
                    clave="alerta_lluvia_componentes",
                    valor=componentes,
                    fuente="scheduler_v51",
                    metadatos={"detalles": "dGHI/dt, dHR/dt, dP/dt, dΔT, Sundqvist"}
                )
                
                logger.debug(f"[SCHEDULER] Alerta lluvia: score={resultado_alerta.get('score', 0):.0f}, ETA={resultado_alerta.get('eta_minutos', 0):.0f}min")
                
            except Exception as e:
                logger.debug(f"[SCHEDULER] Error en alerta lluvia: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # PREDICTION ENGINE (OPCIÓN 3: Predicciones LSTM si disponibles)
        # ═══════════════════════════════════════════════════════════════════════
        
        if self.integrador_prediccion and self.integrador_prediccion.disponible:
            try:
                # Ejecutar predicciones disponibles
                predicciones = self.integrador_prediccion.ejecutar_predicciones()
                
                if predicciones:
                    # Publicar resumen de predicciones
                    self.bus.publicar(
                        clave="predicciones_lstm_automaticas",
                        valor=predicciones,
                        fuente="scheduler_v51_prediction_engine",
                        metadatos={
                            "modelos": len(predicciones),
                            "arquitectura": "V51_PREDICTION_ENGINE_V3"
                        }
                    )
                    
                    logger.debug(f"[SCHEDULER] Predicciones LSTM: {len(predicciones)} modelos ejecutados")
                
            except Exception as e:
                logger.debug(f"[SCHEDULER] Error en prediction_engine: {e}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # PUBLICAR RESUMEN COMPLETO
        # ═══════════════════════════════════════════════════════════════════════
        
        resumen = {
            "timestamp": datetime.now().isoformat(),
            "radiacion": {
                "ghi_w_m2": ghi,
                "dni_w_m2": dni,
                "dhi_w_m2": dhi
            },
            "temperatura": {
                "t_c": temp_c,
                "humedad_pct": humedad,
                "presion_hpa": presion,
                "viento_ms": viento_ms
            },
            "contexto_solar": {
                "elevacion_deg": elevacion_solar
            },
            "scheduler": "activo_v51"
        }
        
        self.bus.publicar(
            clave="ciclo_indices_completo",
            valor=resumen,
            fuente="scheduler_indices_v51",
            metadatos={"arquitectura": "V51_AUTOMATICA"}
        )
        
        logger.debug(f"[SCHEDULER] Ciclo completado - GHI={ghi:.0f} W/m², T={temp_c:.1f}°C, Índices publicados")
    
    def _publicar_wbgt(self, wbgt_result: Dict):
        """Publica todos los componentes WBGT en el bus"""
        
        try:
            # Componentes principales
            self.bus.publicar("wbgt_outdoor", float(wbgt_result.get("wbgt_outdoor", 0)), "scheduler_v51", 
                            {"unidad": "°C", "modelo": "Liljegren2008"})
            self.bus.publicar("wbgt_indoor", float(wbgt_result.get("wbgt_indoor", 0)), "scheduler_v51",
                            {"unidad": "°C"})
            self.bus.publicar("wbgt_heat_index", float(wbgt_result.get("heat_index", 0)), "scheduler_v51",
                            {"unidad": "°C"})
            
            # Componentes termométricos
            self.bus.publicar("wbgt_twb", float(wbgt_result.get("twb", 0)), "scheduler_v51",
                            {"unidad": "°C", "componente": "wet_bulb"})
            self.bus.publicar("wbgt_tg", float(wbgt_result.get("tg", 0)), "scheduler_v51",
                            {"unidad": "°C", "componente": "globe"})
            
            # Variantes
            if "twb_stull" in wbgt_result:
                self.bus.publicar("wbgt_twb_stull", float(wbgt_result["twb_stull"]), "scheduler_v51",
                                {"unidad": "°C", "metodo": "Stull"})
            
            if "tg_solar" in wbgt_result:
                self.bus.publicar("wbgt_tg_solar", float(wbgt_result["tg_solar"]), "scheduler_v51",
                                {"unidad": "°C", "componente": "radiativo"})
        except Exception as e:
            logger.debug(f"[SCHEDULER] Error publicando WBGT: {e}")


# Instancia global
_calculador_global = None

def iniciar_calculador_indices():
    """Inicia el scheduler automático global"""
    global _calculador_global
    
    if _calculador_global is None:
        _calculador_global = CalculadorIndicesAutomatico(intervalo_segundos=300)  # 5 min
    
    _calculador_global.iniciar()
    logger.info("[APP] Calculador de Índices automático iniciado")
    return _calculador_global

def detener_calculador_indices():
    """Detiene el scheduler"""
    global _calculador_global
    if _calculador_global:
        _calculador_global.detener()

def obtener_calculador_indices() -> Optional[CalculadorIndicesAutomatico]:
    """Obtiene la instancia global del calculador"""
    return _calculador_global
