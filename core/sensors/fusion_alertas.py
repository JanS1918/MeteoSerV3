"""
═══════════════════════════════════════════════════════════════════════════════
MÓDULO: ALERTAS DEL SISTEMA DE FUSIÓN ADAPTATIVA
═══════════════════════════════════════════════════════════════════════════════

Genera y gestiona alertas para anomalías detectadas en fusión de sensores.
Integración con sistema de alertas MeteoSerV3.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from core.sensors.adaptive_sensor_fusion import (
    generar_alerta_anomalia,
    detectar_microclima,
    evaluar_sesgo_radiacion_wh65
)
from core.sensors.fusion_config import configuracion as config_fusion

logger = logging.getLogger(__name__)


class GestorAlertasFusion:
    """Gestor centralizado de alertas del sistema de fusión."""
    
    def __init__(self):
        """Inicializar gestor de alertas."""
        self.alertas_activas = []
        self.historial_alertas = []
        self.archivo_registro = config_fusion.obtener_ruta_log_alertas() if config_fusion else 'data/fusion_alerts.jsonl'
    
    def procesar_sensores(
        self,
        temp_wh65: float,
        hum_wh65: float,
        temp_wh31: float,
        hum_wh31: float,
        radiacion_w_m2: float = 0.0
    ) -> List[Dict]:
        """
        Procesar lecturas de sensores y generar todas las alertas relevantes.
        
        Args:
            temp_wh65, hum_wh65: Valores WH65
            temp_wh31, hum_wh31: Valores WH31
            radiacion_w_m2: Radiación solar
        
        Returns:
            Lista de alertas generadas
        """
        alertas = []
        timestamp = datetime.now().isoformat()
        
        # 1. DETECCIÓN DE ANOMALÍA
        alerta_anomalia = generar_alerta_anomalia(
            temp_wh65, hum_wh65, temp_wh31, hum_wh31, timestamp
        )
        if alerta_anomalia:
            alertas.append(alerta_anomalia)
            logger.warning(f"[ALERTA] Anomalía detectada: {alerta_anomalia['razon']}")
        
        # 2. DETECCIÓN DE MICROCLIMA
        microclima = detectar_microclima(temp_wh65, hum_wh65, temp_wh31, hum_wh31)
        if microclima:
            alerta_microclima = {
                **microclima,
                'timestamp': timestamp,
                'tipo': 'microclima'
            }
            alertas.append(alerta_microclima)
            logger.info(f"[ALERTA] Microclima detectado: {microclima['descripcion']}")
        
        # 3. EVALUACIÓN DE SESGO DE RADIACIÓN
        if radiacion_w_m2 > 0:
            sesgo = evaluar_sesgo_radiacion_wh65(temp_wh65, temp_wh31, radiacion_w_m2)
            if sesgo['sesgo_radiacion_probable']:
                alerta_sesgo = {
                    'timestamp': timestamp,
                    'tipo': 'sesgo_radiacion',
                    'severidad': 'BAJA',
                    'razon': f"WH65 puede estar sesgado por radiación (rad={radiacion_w_m2:.0f}W/m², ΔT={sesgo['diferencia_temp_wh65_mayor']:.1f}°C)",
                    'datos': sesgo,
                    'recomendacion': 'Considerar usar WH31 para índices de confort'
                }
                alertas.append(alerta_sesgo)
                logger.info(f"[ALERTA] Posible sesgo por radiación en WH65")
        
        # GUARDAR ALERTAS EN LOG
        if config_fusion and config_fusion.debe_guardar_alertas():
            for alerta in alertas:
                self._guardar_alerta(alerta)
        
        self.alertas_activas = alertas
        return alertas
    
    def _guardar_alerta(self, alerta: Dict) -> bool:
        """Guardar alerta individual en archivo JSONL."""
        try:
            ruta = Path(self.archivo_registro)
            ruta.parent.mkdir(parents=True, exist_ok=True)
            
            with open(ruta, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alerta, ensure_ascii=False) + '\n')
            
            logger.debug(f"[ALERTAS] Alerta guardada en {self.archivo_registro}")
            return True
        except Exception as e:
            logger.error(f"[ALERTAS] Error guardando alerta: {e}")
            return False
    
    def obtener_alertas_activas(self) -> List[Dict]:
        """Obtener lista de alertas activas actualmente."""
        return self.alertas_activas.copy()
    
    def limpiar_alertas_antiguas(self, horas_max: int = 24) -> int:
        """
        Limpiar alertas antiguas del archivo de log.
        
        Args:
            horas_max: Mantener solo alertas de últimas N horas
        
        Returns:
            Número de alertas eliminadas
        """
        from datetime import timedelta
        
        try:
            ruta = Path(self.archivo_registro)
            if not ruta.exists():
                return 0
            
            tiempo_limite = datetime.now() - timedelta(hours=horas_max)
            alertas_validas = []
            alertas_eliminadas = 0
            
            with open(ruta, 'r', encoding='utf-8') as f:
                for linea in f:
                    try:
                        alerta = json.loads(linea)
                        timestamp_str = alerta.get('timestamp')
                        if timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            if timestamp > tiempo_limite:
                                alertas_validas.append(alerta)
                            else:
                                alertas_eliminadas += 1
                        else:
                            alertas_validas.append(alerta)
                    except json.JSONDecodeError:
                        continue
            
            # Reescribir archivo solo con alertas válidas
            with open(ruta, 'w', encoding='utf-8') as f:
                for alerta in alertas_validas:
                    f.write(json.dumps(alerta, ensure_ascii=False) + '\n')
            
            logger.info(f"[ALERTAS] Limpieza: {alertas_eliminadas} alertas eliminadas")
            return alertas_eliminadas
        
        except Exception as e:
            logger.error(f"[ALERTAS] Error limpiando alertas antiguas: {e}")
            return 0
    
    def obtener_estadisticas(self) -> Dict:
        """Generar estadísticas de alertas."""
        try:
            ruta = Path(self.archivo_registro)
            if not ruta.exists():
                return {'total_alertas': 0, 'por_tipo': {}}
            
            contadores = {}
            total = 0
            
            with open(ruta, 'r', encoding='utf-8') as f:
                for linea in f:
                    try:
                        alerta = json.loads(linea)
                        tipo = alerta.get('tipo', 'desconocido')
                        contadores[tipo] = contadores.get(tipo, 0) + 1
                        total += 1
                    except json.JSONDecodeError:
                        continue
            
            return {
                'total_alertas': total,
                'por_tipo': contadores,
                'tipos_unicos': list(contadores.keys())
            }
        except Exception as e:
            logger.error(f"[ALERTAS] Error generando estadísticas: {e}")
            return {'error': str(e)}


# Instancia global del gestor de alertas
gestor_alertas = GestorAlertasFusion()
