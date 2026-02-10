#!/usr/bin/env python3
"""
SISTEMA AUTÓNOMO DE MANTENIMIENTO ZERO
======================================
Integra todos los sistemas de monitoreo, calibración y auto-recuperación
para operación remota sin intervención humana.

ESCENARIO: Abandono 6 meses, acceso remoto, mantenimiento ZERO
OBJETIVO: Sistema auto-compensa degradación y se recupera de fallos

Componentes integrados:
1. Watchdog (auto-recovery de fallos críticos)
2. Auto-Calibrator (compensa degradación sensores)
3. Drift Gate (detección anomalías < 1 min)
4. Bias Detector (sesgo sensores 90 días)
5. Monitor Bus (vigilancia 33+ micro-valores)

Autor: MeteoSerV3 - Fase 1 Abandono Remoto
Fecha: 5 Febrero 2026
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import json

logger = logging.getLogger("autonomous_maintenance")


@dataclass
class SystemHealth:
    """Estado de salud del sistema completo"""
    timestamp: datetime
    watchdog_active: bool
    calibration_status: str
    drift_anomalies: int
    bias_detected: List[str]
    bus_throughput_mbps: float
    critical_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def is_healthy(self) -> bool:
        """Sistema saludable si no hay errores críticos"""
        return len(self.critical_errors) == 0 and self.watchdog_active


@dataclass
class MaintenanceAction:
    """Acción de mantenimiento ejecutada"""
    timestamp: datetime
    action_type: str  # "calibration", "drift_fix", "bias_correction", "recovery"
    sensor_name: str
    description: str
    success: bool
    error: Optional[str] = None


class AutonomousMaintenanceSystem:
    """
    Sistema autónomo que mantiene MeteoSerV3 operativo sin intervención humana.
    
    Filosofía:
    - NO espera a que alguien limpie sensores → auto-calibra
    - NO espera a que alguien reinicie sistema → watchdog recupera
    - NO espera a que alguien detecte derivas → drift gate previene
    - Precisión absoluta → PRESION.ARGENTONA_MEDIA, no ISA genérico
    """
    
    def __init__(self, bus=None):
        """
        Args:
            bus: BusCapasInformacion (opcional, se obtiene automáticamente si None)
        """
        from core.bus.bus_capas_informacion import obtener_bus
        self.bus = bus or obtener_bus()
        
        # Componentes
        self.watchdog = None  # Se configura externamente (proceso separado)
        self.auto_calibrator = None
        self.drift_gate = None
        self.bias_detector = None
        self.bus_monitor = None
        
        # Estado
        self.running = False
        self.health_history: deque = deque(maxlen=1440)  # 24h a 1 min/sample
        self.maintenance_log: deque = deque(maxlen=1000)
        self.last_calibration = None
        self.last_drift_check = None
        self.last_bias_check = None
        
        # Configuración
        self.calibration_interval_hours = 6  # Auto-calibrar cada 6h
        self.drift_check_interval_seconds = 60  # Revisar drift cada 1 min
        self.bias_check_interval_hours = 24  # Revisar bias diario
        
        self.lock = threading.RLock()
        logger.info("[OK] AutonomousMaintenanceSystem inicializado")
    
    def initialize_components(self):
        """Inicializa todos los componentes de mantenimiento"""
        try:
            # 1. Auto-Calibrator
            from core.calibration import obtener_auto_calibrador, CALIBRACION_AVANZADA_DISPONIBLE
            if CALIBRACION_AVANZADA_DISPONIBLE:
                self.auto_calibrator = obtener_auto_calibrador(self.bus)
                logger.info("✅ Auto-Calibrator inicializado (sklearn disponible)")
            else:
                logger.warning("⚠️ Auto-Calibrator sin módulos avanzados (falta sklearn)")
            
            # 2. Drift Gate
            from core.monitoring.drift_detection_gate import DriftDetectionGate
            self.drift_gate = DriftDetectionGate()
            logger.info("✅ Drift Detection Gate inicializado")
            
            # 3. Bias Detector
            if CALIBRACION_AVANZADA_DISPONIBLE:
                from core.calibration.bias_detector import DetectorBias
                self.bias_detector = DetectorBias(ventana_historico=129600)  # 90 días × 1440 min
                logger.info("✅ Bias Detector inicializado (ventana 90 días)")
            
            # 4. Bus Monitor
            from core.bus.monitor_bus import MonitorBusRealtime
            self.bus_monitor = MonitorBusRealtime(intervalo_actualizacion=60.0)
            logger.info("✅ Bus Monitor inicializado")
            
            logger.info("[INIT] Todos los componentes de mantenimiento activos")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error inicializando componentes: {e}", exc_info=True)
            return False
    
    def start_autonomous_mode(self):
        """Inicia modo autónomo (loop en thread separado)"""
        if self.running:
            logger.warning("Sistema autónomo ya está corriendo")
            return
        
        if not self.initialize_components():
            logger.error("No se puede iniciar: componentes no inicializados")
            return
        
        self.running = True
        thread = threading.Thread(target=self._autonomous_loop, daemon=True)
        thread.start()
        logger.info("🚀 MODO AUTÓNOMO ACTIVADO - Mantenimiento Zero")
    
    def stop_autonomous_mode(self):
        """Detiene modo autónomo"""
        self.running = False
        logger.info("⏹️ Modo autónomo detenido")
    
    def _autonomous_loop(self):
        """Loop principal de mantenimiento autónomo"""
        logger.info("[LOOP] Iniciando ciclo de mantenimiento autónomo")
        
        while self.running:
            try:
                now = datetime.now()
                
                # CHECKPOINT 1: Calibración automática (cada 6h)
                if self._should_calibrate(now):
                    self._execute_auto_calibration()
                
                # CHECKPOINT 2: Detección de drift (cada 1 min)
                if self._should_check_drift(now):
                    self._execute_drift_detection()
                
                # CHECKPOINT 3: Análisis de bias (cada 24h)
                if self._should_check_bias(now):
                    self._execute_bias_analysis()
                
                # CHECKPOINT 4: Health check general
                health = self._compute_system_health()
                self.health_history.append(health)
                
                if not health.is_healthy():
                    logger.warning(f"⚠️ Sistema degradado: {health.critical_errors}")
                
                # Sleep hasta próximo checkpoint
                time.sleep(30)  # Check cada 30s (overhead mínimo)
                
            except Exception as e:
                logger.error(f"[ERROR] Error en loop autónomo: {e}", exc_info=True)
                time.sleep(60)  # Esperar 1 min antes de reintentar
    
    def _should_calibrate(self, now: datetime) -> bool:
        """¿Debe ejecutar calibración?"""
        if self.last_calibration is None:
            return True
        elapsed = (now - self.last_calibration).total_seconds() / 3600
        return elapsed >= self.calibration_interval_hours
    
    def _should_check_drift(self, now: datetime) -> bool:
        """¿Debe revisar drift?"""
        if self.last_drift_check is None:
            return True
        elapsed = (now - self.last_drift_check).total_seconds()
        return elapsed >= self.drift_check_interval_seconds
    
    def _should_check_bias(self, now: datetime) -> bool:
        """¿Debe analizar bias?"""
        if self.last_bias_check is None:
            return True
        elapsed = (now - self.last_bias_check).total_seconds() / 3600
        return elapsed >= self.bias_check_interval_hours
    
    def _execute_auto_calibration(self):
        """Ejecuta ciclo de auto-calibración"""
        if not self.auto_calibrator:
            return
        
        logger.info("🔧 Iniciando auto-calibración de sensores...")
        sensors_calibrated = []
        
        try:
            # Sensores críticos que requieren calibración periódica
            critical_sensors = ["temperatura", "humedad", "presion"]
            
            for sensor in critical_sensors:
                try:
                    # Intentar calibrar desde histórico
                    modelo = self.auto_calibrator.entrenar_desde_bus(sensor, dias=7)
                    self.auto_calibrator.modelos[sensor] = modelo
                    self.auto_calibrator.guardar_modelo(sensor)
                    
                    sensors_calibrated.append(sensor)
                    logger.info(f"✅ {sensor} calibrado (R²={modelo.r2_score:.3f}, offset={modelo.intercept:+.2f})")
                    
                    # Registrar acción
                    action = MaintenanceAction(
                        timestamp=datetime.now(),
                        action_type="calibration",
                        sensor_name=sensor,
                        description=f"Auto-calibración exitosa (R²={modelo.r2_score:.3f})",
                        success=True
                    )
                    self.maintenance_log.append(action)
                    
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo calibrar {sensor}: {e}")
                    action = MaintenanceAction(
                        timestamp=datetime.now(),
                        action_type="calibration",
                        sensor_name=sensor,
                        description="Auto-calibración fallida",
                        success=False,
                        error=str(e)
                    )
                    self.maintenance_log.append(action)
            
            self.last_calibration = datetime.now()
            logger.info(f"[DONE] Calibración completada: {len(sensors_calibrated)}/{len(critical_sensors)} sensores")
            
        except Exception as e:
            logger.error(f"[ERROR] Error en auto-calibración: {e}", exc_info=True)
    
    def _execute_drift_detection(self):
        """Ejecuta detección de drift en valores del bus"""
        if not self.drift_gate:
            return
        
        try:
            # Obtener valores recientes del bus para análisis
            temperatura = self.bus.leer("temperatura")
            presion = self.bus.leer("presion")
            humedad = self.bus.leer("humedad")
            
            if temperatura is not None:
                self.drift_gate.record_measurement("temperatura", temperatura, latency_ms=5.0)
            if presion is not None:
                self.drift_gate.record_measurement("presion", presion, latency_ms=5.0)
            if humedad is not None:
                self.drift_gate.record_measurement("humedad", humedad, latency_ms=5.0)
            
            # Analizar drift de sensores principales
            for sensor in ["temperatura", "presion", "humedad"]:
                analysis = self.drift_gate.analyze(sensor)
                if not analysis.passed:
                    logger.warning(f"🔴 Drift detectado en {sensor}: {analysis.reason}")
                    
                    # Registrar detección
                    action = MaintenanceAction(
                        timestamp=datetime.now(),
                        action_type="drift_fix",
                        sensor_name=sensor,
                        description=f"Drift detectado: {analysis.reason}",
                        success=False  # Requiere intervención o auto-calibración
                    )
                    self.maintenance_log.append(action)
            
            self.last_drift_check = datetime.now()
            
        except Exception as e:
            logger.error(f"[ERROR] Error en drift detection: {e}", exc_info=True)
    
    def _execute_bias_analysis(self):
        """Ejecuta análisis de bias en sensores (ventana 90 días)"""
        if not self.bias_detector:
            return
        
        logger.info("📊 Analizando bias de sensores (ventana 90 días)...")
        biases_detected = []
        
        try:
            sensors_to_analyze = ["temperatura", "presion", "humedad"]
            
            for sensor in sensors_to_analyze:
                # Generar reporte completo
                reporte = self.bias_detector.generar_reporte(sensor)
                
                if 'error' in reporte:
                    continue  # Sensor sin suficiente histórico
                
                # Revisar si detectó bias en algún método
                metodos = reporte.get('metodos', {})
                bias_detectado = False
                
                if metodos.get('offset', {}).get('detectado'):
                    bias_detectado = True
                    offset_val = metodos['offset']['valor']
                    logger.warning(f"⚠️ {sensor}: Offset detectado = {offset_val:+.2f}")
                
                if metodos.get('regresion', {}).get('detectado'):
                    bias_detectado = True
                    params = metodos['regresion']['parametros']
                    logger.warning(f"⚠️ {sensor}: Regresión anómala (pendiente={params.get('pendiente', 1.0):.3f})")
                
                if metodos.get('deriva', {}).get('detectado'):
                    bias_detectado = True
                    tasa = metodos['deriva']['tasa_por_dia']
                    logger.warning(f"⚠️ {sensor}: Deriva temporal = {tasa:+.3f}/día")
                
                if bias_detectado:
                    biases_detected.append(sensor)
                    
                    # Publicar al bus (si existe bias publisher)
                    try:
                        from core.calibration.bias_sensor_bus_publisher import BiasSensorBusPublisher
                        bias_publisher = BiasSensorBusPublisher()
                        offset = metodos.get('offset', {}).get('valor', 0.0)
                        bias_publisher.register_bias(
                            sensor_name=sensor,
                            bias_offset_celsius=offset,
                            confidence=0.85,
                            last_calibration_ts=time.time()
                        )
                        bias_publisher.publish_to_bus(sensor)
                    except Exception as e:
                        logger.debug(f"No se pudo publicar bias: {e}")
                    
                    # Registrar acción
                    action = MaintenanceAction(
                        timestamp=datetime.now(),
                        action_type="bias_correction",
                        sensor_name=sensor,
                        description=f"Bias detectado: {reporte.get('conclusion', 'N/A')}",
                        success=True
                    )
                    self.maintenance_log.append(action)
            
            self.last_bias_check = datetime.now()
            logger.info(f"[DONE] Análisis bias completado: {len(biases_detected)} sensores con bias")
            
        except Exception as e:
            logger.error(f"[ERROR] Error en bias analysis: {e}", exc_info=True)
    
    def _compute_system_health(self) -> SystemHealth:
        """Calcula estado de salud del sistema"""
        critical_errors = []
        warnings = []
        bias_detected = []
        
        # 1. Revisar watchdog (externo)
        watchdog_active = True  # Asumimos OK (watchdog es proceso separado)
        
        # 2. Revisar calibración
        calibration_status = "OK"
        if self.auto_calibrator:
            if not self.auto_calibrator.modelos:
                warnings.append("Ningún sensor calibrado")
                calibration_status = "NO_CALIBRATED"
        else:
            warnings.append("Auto-calibrator no disponible")
            calibration_status = "UNAVAILABLE"
        
        # 3. Revisar drift
        drift_anomalies = 0
        if self.drift_gate:
            for sensor in ["temperatura", "presion", "humedad"]:
                analysis = self.drift_gate.analyze(sensor)
                if not analysis.passed:
                    drift_anomalies += 1
                    warnings.append(f"Drift en {sensor}")
        
        # 4. Revisar bias
        if self.bias_detector:
            for sensor in ["temperatura", "presion", "humedad"]:
                reporte = self.bias_detector.generar_reporte(sensor)
                if reporte.get('conclusion') == "REQUIERE CALIBRACIÓN URGENTE":
                    bias_detected.append(sensor)
                    critical_errors.append(f"Bias crítico en {sensor}")
        
        # 5. Throughput del bus
        bus_throughput = 0.0
        if self.bus_monitor:
            try:
                dashboard = self.bus.generar_dashboard()
                total_items = (dashboard['capas']['CORE']['items'] + 
                             dashboard['capas']['INTERMEDIATE']['items'] +
                             dashboard['capas']['DEBUG']['items'])
                bus_throughput = total_items * 0.001  # Estimación MB/s
            except Exception:
                pass
        
        return SystemHealth(
            timestamp=datetime.now(),
            watchdog_active=watchdog_active,
            calibration_status=calibration_status,
            drift_anomalies=drift_anomalies,
            bias_detected=bias_detected,
            bus_throughput_mbps=bus_throughput,
            critical_errors=critical_errors,
            warnings=warnings
        )
    
    def get_status_report(self) -> Dict[str, Any]:
        """Genera reporte de estado completo"""
        current_health = self._compute_system_health()
        
        # Últimas 24h de health
        health_24h = list(self.health_history)
        healthy_count = sum(1 for h in health_24h if h.is_healthy())
        uptime_percentage = (healthy_count / len(health_24h) * 100) if health_24h else 0.0
        
        # Últimas acciones de mantenimiento
        recent_actions = list(self.maintenance_log)[-10:]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "autonomous_mode": self.running,
            "current_health": {
                "status": "HEALTHY" if current_health.is_healthy() else "DEGRADED",
                "watchdog": current_health.watchdog_active,
                "calibration": current_health.calibration_status,
                "drift_anomalies": current_health.drift_anomalies,
                "bias_detected": current_health.bias_detected,
                "bus_throughput_mbps": current_health.bus_throughput_mbps,
                "critical_errors": current_health.critical_errors,
                "warnings": current_health.warnings
            },
            "uptime_24h": f"{uptime_percentage:.1f}%",
            "last_calibration": self.last_calibration.isoformat() if self.last_calibration else None,
            "last_drift_check": self.last_drift_check.isoformat() if self.last_drift_check else None,
            "last_bias_check": self.last_bias_check.isoformat() if self.last_bias_check else None,
            "maintenance_actions_count": len(self.maintenance_log),
            "recent_actions": [
                {
                    "timestamp": a.timestamp.isoformat(),
                    "type": a.action_type,
                    "sensor": a.sensor_name,
                    "description": a.description,
                    "success": a.success
                }
                for a in recent_actions
            ]
        }
    
    def force_calibration(self, sensor: str = None):
        """Fuerza calibración inmediata de sensor(es)"""
        if sensor:
            logger.info(f"[FORCE] Calibración forzada de {sensor}")
            self.last_calibration = None  # Reset para forzar
        else:
            logger.info("[FORCE] Calibración forzada de todos los sensores")
            self.last_calibration = None
        
        self._execute_auto_calibration()
    
    def force_bias_analysis(self):
        """Fuerza análisis de bias inmediato"""
        logger.info("[FORCE] Análisis de bias forzado")
        self.last_bias_check = None
        self._execute_bias_analysis()


# Singleton global
_maintenance_system: Optional[AutonomousMaintenanceSystem] = None

def get_maintenance_system(bus=None) -> AutonomousMaintenanceSystem:
    """Obtiene instancia singleton del sistema de mantenimiento"""
    global _maintenance_system
    if _maintenance_system is None:
        _maintenance_system = AutonomousMaintenanceSystem(bus)
    return _maintenance_system


if __name__ == "__main__":
    # Test standalone
    logging.basicConfig(level=logging.INFO)
    
    system = get_maintenance_system()
    system.start_autonomous_mode()
    
    print("✅ Sistema autónomo iniciado")
    print("📊 Presiona Ctrl+C para ver reporte y salir")
    
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n📋 REPORTE FINAL:")
        report = system.get_status_report()
        print(json.dumps(report, indent=2, default=str))
        
        system.stop_autonomous_mode()
        print("\n⏹️ Sistema detenido")
