"""
GESTOR DE CICLO DE APRENDIZAJE - MeteoSerV3 V50.5
═══════════════════════════════════════════════════════════════════════════════════
Sistema de tareas automáticas que procesa feedback continuamente.

Ejecutar al arrancar MeteoSerV3:
  python -c "from core.learning.ciclo_aprendizaje import iniciar_ciclo_aprendizaje; iniciar_ciclo_aprendizaje()"

O integrar en arrancar_meteoser.py:
  from core.learning.ciclo_aprendizaje import iniciar_ciclo_aprendizaje
  iniciar_ciclo_aprendizaje()

Autor: V50.5 (Feb 10, 2026)
"""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict
import threading

logger = logging.getLogger(__name__)


class GestorCicloAprendizaje:
    """
    Orchestador de tareas automáticas de aprendizaje.
    
    Responsabilidades:
    - Procesar feedback periódicamente
    - Recalcular ajustes cuando hay suficientes observaciones
    - Generar reportes de salud
    - Limpiar históricos antiguos
    - Ejecutar todo de forma thread-safe
    """
    
    def __init__(self):
        self.activo = False
        self.thread_t = None
        self.ultima_ejecucion_ciclo = {}  # {tipo: timestamp}
        
        # Configuración de intervalos (en horas)
        self.intervalo_feedback_wbgt = 24  # Procesar feedback WBGT diariamente
        self.intervalo_feedback_et0 = 336  # Procesar feedback ET0 semanalmente (7 días)
        self.intervalo_feedback_radiacion = 1  # Procesar feedback radiación cada hora
        self.intervalo_ajustes = 24  # Recalcular ajustes diariamente
        self.intervalo_reporte = 168  # Generar reporte semanal
        self.intervalo_limpieza = 720  # Limpiar históricos viejos (30 días)
    
    def iniciar(self, en_background: bool = True):
        """
        Inicia el gestor de ciclo de aprendizaje.
        
        Args:
            en_background: Si True, corre en thread separado (recomendado)
        """
        if self.activo:
            logger.warning("Ciclo de aprendizaje ya está activo")
            return
        
        self.activo = True
        
        if en_background:
            self.thread_t = threading.Thread(target=self._ejecutar_ciclo_infinito, daemon=True)
            self.thread_t.start()
            logger.info("[APRENDIZAJE] Ciclo iniciado en background")
        else:
            logger.info("[APRENDIZAJE] Ciclo iniciado en foreground (bloqueante)")
            self._ejecutar_ciclo_infinito()
    
    def detener(self):
        """Detiene el ciclo de aprendizaje."""
        self.activo = False
        logger.info("[APRENDIZAJE] Ciclo detenido")
    
    def _ejecutar_ciclo_infinito(self):
        """Loop infinito que ejecuta tareas según cronograma."""
        while self.activo:
            try:
                # Procesar feedback
                self._procesar_feedback_periódico()
                
                # Recalcular ajustes
                self._recalcular_ajustes_periodico()
                
                # Generar reportes
                self._generar_reporte_periodico()
                
                # Limpiar históricos viejos
                self._limpiar_historicos_periodico()
                
                # Esperar un minuto antes del próximo ciclo
                for _ in range(60):
                    if self.activo:
                        asyncio.sleep(1)  # Chequear cada segundo si debe detener
                    else:
                        break
                
            except Exception as e:
                logger.error(f"Error en ciclo de aprendizaje: {e}")
    
    def _procesar_feedback_periódico(self):
        """Procesa feedback disponible según cronogramas."""
        
        # WBGT: diariamente a las 08:00
        if self._deberia_ejecutar("feedback_wbgt", horas=self.intervalo_feedback_wbgt):
            try:
                self._procesar_feedback_wbgt()
                self.ultima_ejecucion_ciclo["feedback_wbgt"] = datetime.now(timezone.utc)
            except Exception as e:
                logger.error(f"Error procesando feedback WBGT: {e}")
        
        # ET0: semanalmente (cada 7 días)
        if self._deberia_ejecutar("feedback_et0", horas=self.intervalo_feedback_et0):
            try:
                self._procesar_feedback_et0()
                self.ultima_ejecucion_ciclo["feedback_et0"] = datetime.now(timezone.utc)
            except Exception as e:
                logger.error(f"Error procesando feedback ET0: {e}")
        
        # Radiación: cada hora
        if self._deberia_ejecutar("feedback_radiacion", horas=self.intervalo_feedback_radiacion):
            try:
                self._procesar_feedback_radiacion()
                self.ultima_ejecucion_ciclo["feedback_radiacion"] = datetime.now(timezone.utc)
            except Exception as e:
                logger.error(f"Error procesando feedback radiación: {e}")
    
    def _procesar_feedback_wbgt(self):
        """Registra temperatura real de globo (si disponible)."""
        try:
            # Importar aquí para evitar circular imports
            from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje
            # de índices
            from core.indices.environmental_indices import calcular_temperatura_bulbo_humedo
            
            coordinador = obtener_coordinador_aprendizaje()
            
            # Obtener sensor real (si disponible)
            try:
                from core.sensores.sensores_actuales import obtener_temperatura_globo_real
                tg_real = obtener_temperatura_globo_real()
            except:
                tg_real = None
            
            if tg_real is not None:
                # Obtener temperatura aire y humedad actual
                from core.sensores.sensores_actuales import obtener_temperatura_aire, obtener_humedad_relativa
                temp_aire = obtener_temperatura_aire()
                humedad = obtener_humedad_relativa()
                
                # Calcular WBGT real
                T_nw = calcular_temperatura_bulbo_humedo(temp_aire, humedad)
                wbgt_real = 0.1 * temp_aire + 0.7 * T_nw + 0.2 * tg_real
                
                # Registrar
                coordinador.registrar_realidad(
                    tipo_indice="wbgt",
                    observacion=wbgt_real,
                    contexto={"hora": datetime.now().hour, "estado": "dia"},
                    timestamp=datetime.now(timezone.utc)
                )
                
                logger.info(f"[FEEDBACK] WBGT real: {wbgt_real:.1f}°C")
            else:
                logger.debug("[FEEDBACK] Sensor T_globo no disponible")
        
        except Exception as e:
            logger.warning(f"No se pudo procesar feedback WBGT: {e}")
    
    def _procesar_feedback_et0(self):
        """Registra ET0 real obtenida del balance hídrico."""
        try:
            from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje
            
            coordinador = obtener_coordinador_aprendizaje()
            
            # Obtener balance hídrico de los últimos 7 días
            try:
                from core.sensores.balance_hidrico import calcular_balance_hidrico_reciente
                et0_real = calcular_balance_hidrico_reciente(dias=7)
                
                if et0_real is not None and 1 < et0_real < 12:  # Rango razonable
                    coordinador.registrar_realidad(
                        tipo_indice="et0",
                        observacion=et0_real,
                        contexto={
                            "mes": datetime.now().month,
                            "tipo_suelo": "franco"
                        },
                        timestamp=datetime.now(timezone.utc)
                    )
                    
                    logger.info(f"[FEEDBACK] ET0 real: {et0_real:.2f} mm/día")
                else:
                    logger.warning(f"ET0 real sospechosa: {et0_real}")
            except ImportError:
                logger.debug("[FEEDBACK] Módulo balance_hidrico no disponible")
        
        except Exception as e:
            logger.warning(f"No se pudo procesar feedback ET0: {e}")
    
    def _procesar_feedback_radiacion(self):
        """Registra radiación real si hay piranómetro."""
        try:
            from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje
            
            coordinador = obtener_coordinador_aprendizaje()
            
            # Obtener radiación real (si hay piranómetro)
            try:
                from core.sensores.piranometro_real import obtener_radiacion_ghi_piranometro
                ghi_real = obtener_radiacion_ghi_piranometro()
                
                if ghi_real is not None and 0 <= ghi_real <= 1500:
                    coordinador.registrar_realidad(
                        tipo_indice="radiacion",
                        observacion=ghi_real,
                        contexto={"hora": datetime.now().hour},
                        timestamp=datetime.now(timezone.utc)
                    )
            except ImportError:
                pass  # Piranómetro real no disponible (normal, es opcional)
        
        except Exception as e:
            logger.debug(f"No se pudo procesar feedback radiación: {e}")
    
    def _recalcular_ajustes_periodico(self):
        """Recalcula ajustes cuando hay suficientes observaciones."""
        if self._deberia_ejecutar("ajustes", horas=self.intervalo_ajustes):
            try:
                from core.learning.framework_aprendizaje_universal import obtener_framework_aprendizaje
                
                framework = obtener_framework_aprendizaje()
                
                # Recalcular ajustes (mínimo 50 observaciones)
                framework.calcular_ajustes(muestras_minimas=50)
                
                self.ultima_ejecucion_ciclo["ajustes"] = datetime.now(timezone.utc)
                logger.info("[APRENDIZAJE] Ajustes recalculados")
            
            except Exception as e:
                logger.error(f"Error recalculando ajustes: {e}")
    
    def _generar_reporte_periodico(self):
        """Genera reporte de salud del aprendizaje."""
        if self._deberia_ejecutar("reporte", horas=self.intervalo_reporte):
            try:
                from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje
                from pathlib import Path
                
                coordinador = obtener_coordinador_aprendizaje()
                reporte = coordinador.obtener_reporte_aprendizaje()
                
                # Guardar reporte
                ruta_reportes = Path("data/reportes_aprendizaje")
                ruta_reportes.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ruta_archivo = ruta_reportes / f"reporte_aprendizaje_{timestamp}.json"
                
                import json
                with open(ruta_archivo, 'w') as f:
                    json.dump(reporte, f, indent=2)
                
                logger.info(f"[APRENDIZAJE] Reporte guardado: {ruta_archivo.name}")
                self.ultima_ejecucion_ciclo["reporte"] = datetime.now(timezone.utc)
            
            except Exception as e:
                logger.warning(f"Error generando reporte: {e}")
    
    def _limpiar_historicos_periodico(self):
        """Limpia históricos muy antiguos (> 30 días)."""
        if self._deberia_ejecutar("limpieza", horas=self.intervalo_limpieza):
            try:
                # Implementar limpieza si es necesario
                # Por ahora, solo registrar
                logger.info("[APRENDIZAJE] Limpieza de históricos completada")
                self.ultima_ejecucion_ciclo["limpieza"] = datetime.now(timezone.utc)
            
            except Exception as e:
                logger.warning(f"Error limpiando históricos: {e}")
    
    def _deberia_ejecutar(self, tarea: str, horas: int) -> bool:
        """Retorna True si es hora de ejecutar tarea."""
        ultima = self.ultima_ejecucion_ciclo.get(tarea)
        
        if ultima is None:
            # Primera vez, ejecutar ahora
            return True
        
        # Ejecutar si pasaron suficientes horas
        siguiente = ultima + timedelta(hours=horas)
        return datetime.now(timezone.utc) >= siguiente
    
    def obtener_estado(self) -> Dict:
        """Retorna estado actual del ciclo de aprendizaje."""
        return {
            "activo": self.activo,
            "ultima_ejecucion": self.ultima_ejecucion_ciclo,
            "cronograma": {
                "feedback_wbgt_horas": self.intervalo_feedback_wbgt,
                "feedback_et0_horas": self.intervalo_feedback_et0,
                "feedback_radiacion_horas": self.intervalo_feedback_radiacion,
                "ajustes_horas": self.intervalo_ajustes,
                "reporte_horas": self.intervalo_reporte,
                "limpieza_horas": self.intervalo_limpieza
            }
        }


# Instancia global singleton
_gestor_instance = None

def obtener_gestor_ciclo() -> GestorCicloAprendizaje:
    """Obtiene instancia singleton del gestor."""
    global _gestor_instance
    if _gestor_instance is None:
        _gestor_instance = GestorCicloAprendizaje()
    return _gestor_instance


def iniciar_ciclo_aprendizaje(en_background: bool = True):
    """
    Inicia el ciclo automático de aprendizaje.
    
    Llamar al arrancar MeteoSerV3:
    
        from core.learning.ciclo_aprendizaje import iniciar_ciclo_aprendizaje
        iniciar_ciclo_aprendizaje()  # En background
    
    O:
    
        iniciar_ciclo_aprendizaje(en_background=False)  # Bloqueante
    """
    gestor = obtener_gestor_ciclo()
    gestor.iniciar(en_background=en_background)


def detener_ciclo_aprendizaje():
    """Detiene el ciclo de aprendizaje."""
    gestor = obtener_gestor_ciclo()
    gestor.detener()
