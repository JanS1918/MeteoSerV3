"""
SERVICIO ALERTAS IMPACTO EN VIVO v1.0
═════════════════════════════════════════════════════════════════════════════

Monitorea eventos meteorológicos en tiempo real y genera alertas predictivas
basadas en matriz de impacto cruzado. Publica alertas en el bus continuamente.

Configuración:
  - Intervalo: Cada 30 segundos
  - Almacenamiento: data/alertas/
  - Histórico: mantiene últimas 1000 alertas
  - Bus: publica alertas_activas, alertas_criticas, etc.

Fecha: 11 de febrero de 2026
"""

import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
import threading
from typing import Optional, Dict, List, Set
from collections import deque
import sys

# Configurar UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)


class ServicioAlertasEnVivo:
    """Genera y monitorea alertas predictivas en tiempo real."""
    
    def __init__(self, intervalo_segundos: int = 30, max_alertas_historico: int = 1000):
        """
        Inicializa servicio de alertas.
        
        Args:
            intervalo_segundos: Cada cuántos segundos chequear eventos (default: 30)
            max_alertas_historico: Máximo de alertas en histórico (default: 1000)
        """
        self.intervalo_segundos = intervalo_segundos
        self.max_alertas_historico = max_alertas_historico
        self.running = False
        self.thread = None
        self.alertas_activas = {}  # {dominio: alerta}
        self.alertas_criticas_ids = set()  # IDs de alertas críticas activas
        self.historico_alertas = deque(maxlen=max_alertas_historico)
        self.estadisticas = {
            'total_generadas': 0,
            'total_resueltas': 0,
            'criticas_activas': 0,
            'ultima_actualizacion': None
        }
        
        # Crear directorio de almacenamiento
        self.datos_directorio = Path("data/alertas")
        self.datos_directorio.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[ALERTAS-VIVO] Servicio inicializado - Intervalo: {intervalo_segundos}s")
    
    async def _obtener_eventos_actuales(self) -> List[Dict]:
        """Obtiene eventos meteorológicos actuales del sistema."""
        try:
            # En producción, leer del bus o sensores reales
            # Por ahora simular
            eventos = [
                # {
                #     'tipo': 'lluvia',
                #     'valor': system.data.get('lluvia_1h', 0),
                #     'timestamp': datetime.now().isoformat(),
                #     'descripcion': f"Lluvia actual: {sistema.data.get('lluvia_1h')}mm"
                # },
                # Similar para otros eventos
            ]
            return eventos
        except Exception as e:
            logger.debug(f"Error obteniendo eventos: {e}")
            return []
    
    async def _calcular_alertas(self) -> Dict:
        """Calcula alertas basadas en matriz de impacto."""
        try:
            from core.indices.predictive_alerts_impact import GeneradorAlertasImpacto
            
            generador = GeneradorAlertasImpacto()
            eventos = generador.obtener_eventos_actuales_simulados()
            impactos = generador.calcular_impactos(eventos)
            alertas = generador.generar_alertas(eventos, impactos)
            consolidado = generador.consolidar_alertas(alertas)
            
            return consolidado
            
        except Exception as e:
            logger.error(f"Error calculando alertas: {e}")
            return {'total_alertas': 0, 'criticas': 0, 'alertas': []}
    
    async def _procesar_alertas(self, consolidado: Dict):
        """Procesa alertas calculadas y actualiza estado."""
        ahora = datetime.now().isoformat()
        
        # Almacenar alertas nuevas en histórico
        for alerta_dict in consolidado.get('alertas', []):
            alerta_dict['id'] = f"{alerta_dict['dominio']}_{ahora}_{len(self.historico_alertas)}"
            alerta_dict['timestamp_recibida'] = ahora
            self.historico_alertas.append(alerta_dict)
            self.estadisticas['total_generadas'] += 1
        
        # Actualizar alertas activas
        alertas_dominios = {a['dominio']: a for a in consolidado.get('alertas', [])}
        
        # Detectar alertas que se resolvieron
        dominios_resueltos = set(self.alertas_activas.keys()) - set(alertas_dominios.keys())
        for dominio in dominios_resueltos:
            alert_id = self.alertas_activas[dominio].get('id')
            if alert_id in self.alertas_criticas_ids:
                self.alertas_criticas_ids.remove(alert_id)
            logger.info(f"[ALERTAS-VIVO] ✓ Alerta RESUELTA: {dominio}")
            self.estadisticas['total_resueltas'] += 1
            del self.alertas_activas[dominio]
        
        # Detectar nuevas alertas críticas y enviar notificaciones
        for alerta_dict in consolidado.get('alertas', []):
            if alerta_dict.get('nivel') == 'CRÍTICO':
                alerta_id = alerta_dict.get('id')
                if alerta_id not in self.alertas_criticas_ids:
                    self.alertas_criticas_ids.add(alerta_id)
                    # Enviar notificación
                    try:
                        from core.notificaciones.notificaciones import obtener_notificador
                        notificador = obtener_notificador()
                        # Ejecutar notificación en background
                        asyncio.create_task(notificador.notificar_alerta_critica(alerta_dict))
                    except Exception as e:
                        logger.debug(f"[ALERTAS-VIVO] No se pudo enviar notificación: {e}")
        
        # Actualizar alertas activas
        self.alertas_activas = alertas_dominios
        
        # Registrar también en storage
        self._guardar_snapshot_alertas(consolidado)
        
        # Actualizar estadísticas
        self.estadisticas['criticas_activas'] = consolidado.get('criticas', 0)
        self.estadisticas['ultima_actualizacion'] = ahora
    
    def _guardar_snapshot_alertas(self, consolidado: Dict):
        """Guarda snapshot actual de alertas."""
        try:
            archivo_actual = self.datos_directorio / "alertas_actuales.json"
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'total_alertas': consolidado.get('total_alertas', 0),
                'criticas': consolidado.get('criticas', 0),
                'severas': consolidado.get('severas', 0),
                'alertas': consolidado.get('alertas', [])
            }
            
            with open(archivo_actual, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.debug(f"Error guardando snapshot: {e}")
    
    async def _loop_monitoreo(self):
        """Loop principal de monitoreo en background."""
        logger.info("[ALERTAS-VIVO] Loop de monitoreo iniciado")
        
        while self.running:
            try:
                # Calcular alertas
                consolidado = await self._calcular_alertas()
                
                # Procesar resultados
                await self._procesar_alertas(consolidado)
                
                # Log de estado
                total = consolidado.get('total_alertas', 0)
                criticas = consolidado.get('criticas', 0)
                
                if criticas > 0:
                    logger.warning(f"[ALERTAS-VIVO] ⚠️  {total} alertas activas ({criticas} CRÍTICAS)")
                elif total > 0:
                    logger.info(f"[ALERTAS-VIVO] {total} alertas activas")
                
                # Esperar antes de siguiente iteración
                await asyncio.sleep(self.intervalo_segundos)
                
            except Exception as e:
                logger.error(f"[ALERTAS-VIVO] Error en loop: {e}")
                await asyncio.sleep(self.intervalo_segundos)
    
    def _thread_loop(self):
        """Ejecuta loop async en thread separado."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._loop_monitoreo())
        finally:
            loop.close()
    
    def start(self):
        """Inicia servicio en background thread."""
        if self.running:
            logger.warning("[ALERTAS-VIVO] Ya está ejecutándose")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._thread_loop, daemon=True)
        self.thread.start()
        
        logger.info(f"[ALERTAS-VIVO] ✓ Servicio iniciado - Monitoreo cada {self.intervalo_segundos}s")
    
    def stop(self):
        """Detiene el servicio."""
        if not self.running:
            return
        
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("[ALERTAS-VIVO] Detenido")
    
    def obtener_alertas_activas(self) -> Dict:
        """Retorna estado actual de alertas."""
        return {
            'total': len(self.alertas_activas),
            'criticas': len(self.alertas_criticas_ids),
            'alertas': self.alertas_activas,
            'estadisticas': self.estadisticas
        }
    
    def obtener_historico(self, limites: int = 100, filtro_nivel: Optional[str] = None) -> List[Dict]:
        """Retorna histórico de alertas."""
        historico = list(self.historico_alertas)[-limites:]
        
        if filtro_nivel:
            historico = [a for a in historico if a.get('nivel') == filtro_nivel]
        
        return historico
    
    def obtener_estadisticas(self) -> Dict:
        """Retorna estadísticas de alertas."""
        return {
            **self.estadisticas,
            'alertas_activas_por_dominio': {
                d: a.get('nivel') for d, a in self.alertas_activas.items()
            },
            'historico_total': len(self.historico_alertas),
            'criticas_no_resueltas': len(self.alertas_criticas_ids)
        }
    
    def publicar_en_bus(self, bus):
        """Publica estado actual de alertas en el bus."""
        try:
            estado = self.obtener_alertas_activas()
            stats = self.obtener_estadisticas()
            
            bus.publicar("alertas_total_activas", estado['total'], "count")
            bus.publicar("alertas_criticas_activas", estado['criticas'], "count")
            bus.publicar("alertas_timestamp_ultimo_update", stats['ultima_actualizacion'], "ISO8601")
            
            # Publicar por dominio
            for dominio, alerta in estado['alertas'].items():
                bus.publicar(f"alerta_{dominio}_nivel", alerta.get('nivel'), "texto")
                bus.publicar(f"alerta_{dominio}_magnitud", alerta.get('impacto_magnitud'), "valor")
            
            logger.debug("[ALERTAS-VIVO] Estado publicado en bus")
            
        except Exception as e:
            logger.warning(f"[ALERTAS-VIVO] Error publicando en bus: {e}")


# Instancia global
_servicio_instance = None


def obtener_servicio() -> ServicioAlertasEnVivo:
    """Obtiene o crea la instancia global del servicio."""
    global _servicio_instance
    
    if _servicio_instance is None:
        _servicio_instance = ServicioAlertasEnVivo(intervalo_segundos=30)
    
    return _servicio_instance


def iniciar_servicio_alertas() -> ServicioAlertasEnVivo:
    """Inicia el servicio de alertas en background."""
    servicio = obtener_servicio()
    servicio.start()
    return servicio


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    servicio = iniciar_servicio_alertas()
    
    print("Servicio de alertas iniciado")
    print(f"Intervalo de monitoreo: {servicio.intervalo_segundos} segundos")
    
    # Mantener corriendo
    try:
        while True:
            asyncio.sleep(5)
            estado = servicio.obtener_alertas_activas()
            print(f"  Alertas activas: {estado['total']}, Críticas: {estado['criticas']}")
    except KeyboardInterrupt:
        servicio.stop()
        print("Detenido")
