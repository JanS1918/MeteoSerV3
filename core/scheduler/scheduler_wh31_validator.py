"""
SCHEDULER WH31 VALIDATOR v1.0
═════════════════════════════════════════════════════════════════════════════

Ejecuta validación semanal de sensores WH31 vs WH65 en background.
Detecta drift de calibración y cambios en errores sistemáticos.

Configuración:
  - Intervalo: Cada 7 días a las 03:00 AM (horaminimum de carga del sistema)
  - Almacenamiento: data/wh31_validations/
  - Histórico: mantiene últimas 12 validaciones

Fecha: 11 de febrero de 2026
"""

import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta, time
import threading
from typing import Optional, Dict, List
import sys

# Configurar UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)


class SchedulerWH31Validator:
    """Ejecuta validaciones periódicas de WH31 en background."""
    
    def __init__(self, intervalo_dias: int = 7, hora_ejecucion: str = "03:00"):
        """
        Inicializa scheduler.
        
        Args:
            intervalo_dias: Cada cuántos días ejecutar (default: 7)
            hora_ejecucion: Hora del día para ejecutar (format: "HH:MM", default: "03:00")
        """
        self.intervalo_dias = intervalo_dias
        self.hora_ejecucion = self._parse_hora(hora_ejecucion)
        self.running = False
        self.thread = None
        self.ultimo_ejercicio = None
        self.resultados_historico = []
        self.resultado_actual = None
        
        # Crear directorio de almacenamiento
        self.datos_directorio = Path("data/wh31_validations")
        self.datos_directorio.mkdir(parents=True, exist_ok=True)
        
        # Cargar histórico si existe
        self._cargar_historico()
        
        logger.info(f"[WH31-SCHEDULER] Inicializado - Próxima ejecución: {self._proxima_ejecucion()}")
    
    def _parse_hora(self, hora_str: str) -> time:
        """Parsea string HH:MM a objeto time."""
        parts = hora_str.split(":")
        return time(int(parts[0]), int(parts[1]))
    
    def _proxima_ejecucion(self) -> str:
        """Calcula cuándo será la próxima ejecución."""
        ahora = datetime.now()
        target_time = datetime.combine(ahora.date(), self.hora_ejecucion)
        
        # Si ya pasó la hora de hoy, es mañana
        if target_time <= ahora:
            target_time += timedelta(days=1)
        
        # Agregar intervalo de días
        if self.ultimo_ejercicio:
            dias_desde_ultimo = (ahora.date() - self.ultimo_ejercicio.date()).days
            if dias_desde_ultimo < self.intervalo_dias:
                dias_faltantes = self.intervalo_dias - dias_desde_ultimo
                target_time = datetime.combine(
                    ahora.date() + timedelta(days=dias_faltantes),
                    self.hora_ejecucion
                )
        
        return target_time.strftime("%Y-%m-%d %H:%M")
    
    def _cargar_historico(self):
        """Carga histórico de validaciones anteriores."""
        archivo_historico = self.datos_directorio / "historico.json"
        
        if archivo_historico.exists():
            try:
                with open(archivo_historico, 'r') as f:
                    data = json.load(f)
                    self.resultados_historico = data.get('resultados', [])[-12:]  # Últimas 12
                    self.ultimo_ejercicio = datetime.fromisoformat(data.get('ultimo_ejercicio', ''))
                logger.debug(f"[WH31-SCHEDULER] Histórico cargado: {len(self.resultados_historico)} validaciones previas")
            except Exception as e:
                logger.warning(f"[WH31-SCHEDULER] Error cargando histórico: {e}")
    
    def _guardar_historico(self):
        """Guarda histórico de validaciones."""
        archivo_historico = self.datos_directorio / "historico.json"
        
        try:
            data = {
                'ultimo_ejercicio': self.ultimo_ejercicio.isoformat() if self.ultimo_ejercicio else None,
                'resultados': self.resultados_historico[-12:]  # Últimas 12
            }
            
            with open(archivo_historico, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("[WH31-SCHEDULER] Histórico guardado")
        except Exception as e:
            logger.error(f"[WH31-SCHEDULER] Error guardando histórico: {e}")
    
    async def _ejecutar_validacion(self) -> Dict:
        """Ejecuta la validación de WH31."""
        try:
            logger.info("[WH31-SCHEDULER] Iniciando validación...")
            
            # Importar validador
            from core.indices.validate_wh31_temperatures import ValidadorWH31
            
            validador = ValidadorWH31()
            
            # Generar datos históricos (en producción, usar datos reales del sistema)
            logger.debug("[WH31-SCHEDULER] Generando datos históricos...")
            datos = validador.generar_datos_historicos_simulados(dias=7)
            
            # Ejecutar validación
            logger.debug(f"[WH31-SCHEDULER] Validando {len(datos)} registros...")
            resultado = validador.validar_datos_historicos(datos)
            
            # Marcar timestamp
            resultado['timestamp_ejecucion'] = datetime.now().isoformat()
            self.resultado_actual = resultado
            
            # Agregar al histórico
            self.resultados_historico.append(resultado)
            if len(self.resultados_historico) > 12:
                self.resultados_historico = self.resultados_historico[-12:]
            
            # Guardar resultado individual
            nombre_archivo = datetime.now().strftime("validacion_wh31_%Y%m%d_%H%M%S.json")
            archivo_resultado = self.datos_directorio / nombre_archivo
            
            with open(archivo_resultado, 'w') as f:
                json.dump(resultado, f, indent=2)
            
            logger.info(f"[WH31-SCHEDULER] ✓ Validación completada - Resultado: {archivo_resultado}")
            
            # Guardar histórico
            self._guardar_historico()
            
            return resultado
            
        except Exception as e:
            logger.error(f"[WH31-SCHEDULER] Error ejecutando validación: {e}", exc_info=True)
            return {'estado': 'ERROR', 'error': str(e)}
    
    def _validacion_loop(self):
        """Loop de ejecución en background thread."""
        logger.info("[WH31-SCHEDULER] Thread iniciado")
        
        while self.running:
            try:
                ahora = datetime.now()
                target_time = datetime.combine(ahora.date(), self.hora_ejecucion)
                
                # Calcular tiempo hasta próxima ejecución
                if target_time <= ahora:
                    if self.ultimo_ejercicio is None or \
                       (ahora.date() - self.ultimo_ejercicio.date()).days >= self.intervalo_dias:
                        # Ejecutar AHORA
                        logger.info("[WH31-SCHEDULER] Ejecutando validación...")
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(self._ejecutar_validacion())
                            self.ultimo_ejercicio = datetime.now()
                        finally:
                            loop.close()
                        
                        # Próxima ejecución
                        target_time += timedelta(days=self.intervalo_dias)
                
                # Esperar hasta próxima ejecución (máximo 60 segundos por iteración)
                tiempo_faltante = (target_time - ahora).total_seconds()
                esperar = min(60, max(0, tiempo_faltante))
                
                if esperar > 0:
                    asyncio.sleep(esperar)
                    
            except Exception as e:
                logger.error(f"[WH31-SCHEDULER] Error en loop: {e}")
                asyncio.sleep(60)
    
    def start(self):
        """Inicia el scheduler en background."""
        if self.running:
            logger.warning("[WH31-SCHEDULER] Ya está ejecutándose")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._validacion_loop, daemon=True)
        self.thread.start()
        
        logger.info("[WH31-SCHEDULER] ✓ Iniciado - Validaciones semanales programadas")
    
    def stop(self):
        """Detiene el scheduler."""
        if not self.running:
            return
        
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("[WH31-SCHEDULER] Detenido")
    
    def obtener_resultado_actual(self) -> Optional[Dict]:
        """Retorna resultado de la última validación."""
        return self.resultado_actual
    
    def obtener_historico(self, limites: int = 5) -> List[Dict]:
        """Retorna histórico de validaciones."""
        return self.resultados_historico[-limites:]
    
    def analizar_tendencias(self) -> Dict:
        """Analiza tendencias en los resultados históricos."""
        if len(self.resultados_historico) < 2:
            return {'notificacion': 'Datos insuficientes'}
        
        intentos = []
        
        for resultado in self.resultados_historico:
            stats = resultado.get('estadisticas', {})
            diff = stats.get('diferencial_wh31_vs_wh65', {})
            promedio = diff.get('promedio', 0)
            intentos.append(promedio)
        
        # Calcular tendencia
        tendencia = {
            'valores': intentos,
            'promedio_total': sum(intentos) / len(intentos) if intentos else 0,
            'maximo': max(intentos) if intentos else 0,
            'minimo': min(intentos) if intentos else 0,
        }
        
        # Detectar cambios
        if len(intentos) >= 2:
            cambio_reciente = intentos[-1] - intentos[-2]
            tendencia['cambio_reciente'] = cambio_reciente
            
            if abs(cambio_reciente) > 0.5:
                tendencia['alerta'] = f"Cambio significativo: {cambio_reciente:+.2f}°C"
        
        return tendencia


# Instancia global
_scheduler_instance = None


def obtener_scheduler() -> SchedulerWH31Validator:
    """Obtiene o crea la instancia global del scheduler."""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerWH31Validator(intervalo_dias=7, hora_ejecucion="03:00")
    
    return _scheduler_instance


def iniciar_scheduler_wh31() -> SchedulerWH31Validator:
    """Inicia el scheduler WH31 en background."""
    scheduler = obtener_scheduler()
    scheduler.start()
    return scheduler


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    scheduler = iniciar_scheduler_wh31()
    
    print(f"Scheduler iniciado")
    print(f"Próxima validación: {scheduler._proxima_ejecucion()}")
    print(f"Intervalo: {scheduler.intervalo_dias} días")
    
    # Mantener corriendo
    try:
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
        print("Detenido")
