"""
Integration Bridge: Conecta Universal Orchestrator con main_asgi.py
Expone endpoints de descubrimiento y asimilación en FastAPI
"""

import logging
import asyncio
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from core.discovery.universal_orchestrator import UniversalOrchestrator, DetectedHardware, DetectionSource
    _IMPORT_ERROR: Optional[Exception] = None
except ImportError as e:
    _IMPORT_ERROR = e
    UniversalOrchestrator = None
    DetectedHardware = None
    DetectionSource = None
    logging.getLogger(__name__).error(f"Error importando discovery: {e}")

logger = logging.getLogger(__name__)


class HardwareNotification(BaseModel):
    """Notificación de hardware detectado"""
    sensor_id: str
    sensor_type: str
    source: str
    message: str
    metadata: Dict


class AssimilationRequest(BaseModel):
    """Solicitud de asimilación de hardware"""
    sensor_id: str
    sensor_config: Optional[Dict] = None


class OmnipotenceIntegration:
    """Integración de descubrimiento universal con FastAPI"""
    
    def __init__(self):
        try:
            self.orchestrator = UniversalOrchestrator() if UniversalOrchestrator else None
        except Exception as e:
            logger.error(f"Error inicializando UniversalOrchestrator: {e}")
            self.orchestrator = None
        
        self.router = APIRouter(prefix="/admin/omnipotence", tags=["Omnipotence"])
        self.system_core = None
        self.sensor_assimilator = None
        self._setup_routes()
    
    def _setup_routes(self):
        """Configura rutas de descubrimiento universal"""
        
        @self.router.post("/start-radar")
        async def start_universal_radar():
            """Inicia el Radar Universal de Hardware"""
            try:
                if self.orchestrator is None:
                    raise HTTPException(status_code=503, detail=f"Discovery no disponible: {_IMPORT_ERROR}")
                asyncio.create_task(self.orchestrator.start_universal_scan())
                return {
                    "status": "success",
                    "message": "🛸 Radar Universal iniciado",
                    "description": "Escaneando USB, Bluetooth, WiFi simultáneamente"
                }
            except Exception as e:
                logger.error(f"Error iniciando radar: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/stop-radar")
        async def stop_universal_radar():
            """Detiene el Radar Universal"""
            try:
                if self.orchestrator is None:
                    raise HTTPException(status_code=503, detail=f"Discovery no disponible: {_IMPORT_ERROR}")
                await self.orchestrator.stop_universal_scan()
                return {
                    "status": "success",
                    "message": "Radar Universal detenido"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/detected-hardware")
        async def get_detected_hardware():
            """Obtiene todo hardware detectado"""
            try:
                if self.orchestrator is None:
                    raise HTTPException(status_code=503, detail=f"Discovery no disponible: {_IMPORT_ERROR}")
                devices = await self.orchestrator.get_all_detected()
                return {
                    "status": "success",
                    "count": len(devices),
                    "hardware": [d.to_dict() for d in devices]
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/pending-assimilation")
        async def get_pending_hardware():
            """Obtiene hardware esperando asimilación"""
            try:
                if self.orchestrator is None:
                    raise HTTPException(status_code=503, detail=f"Discovery no disponible: {_IMPORT_ERROR}")
                devices = await self.orchestrator.get_pending_hardware()
                return {
                    "status": "success",
                    "count": len(devices),
                    "pending": [d.to_dict() for d in devices]
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/assimilate")
        async def assimilate_hardware(request: AssimilationRequest):
            """Asimila un hardware detectado al sistema"""
            try:
                if self.orchestrator is None:
                    raise HTTPException(status_code=503, detail=f"Discovery no disponible: {_IMPORT_ERROR}")
                sensor_id = request.sensor_id
                
                # Obtener información del hardware
                devices = await self.orchestrator.get_all_detected()
                hardware = next((d for d in devices if d.sensor_id == sensor_id), None)
                
                if not hardware:
                    raise HTTPException(status_code=404, detail=f"Hardware no encontrado: {sensor_id}")
                
                # Asimilar al sistema
                success = await self.orchestrator.assimilate_hardware(sensor_id)
                
                if not success:
                    raise HTTPException(status_code=500, detail="Fallo al asimilar hardware")
                
                # Registrar en asimilador si disponible
                if self.sensor_assimilator:
                    config = request.sensor_config or {}
                    await self.sensor_assimilator.assimilate_sensor(
                        hardware.to_dict(),
                        config
                    )
                
                return {
                    "status": "success",
                    "message": f"✅ Hardware {sensor_id} asimilado al sistema",
                    "hardware": hardware.to_dict()
                }
            except Exception as e:
                logger.error(f"Error asimilando: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/driver-status")
        async def get_driver_status():
            """Obtiene estado de drivers instalados"""
            try:
                if self.orchestrator is None:
                    raise HTTPException(status_code=503, detail=f"Discovery no disponible: {_IMPORT_ERROR}")
                drivers = self.orchestrator.driver_installer.get_installed_drivers()
                return {
                    "status": "success",
                    "installed_drivers": drivers
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/radar-status")
        async def get_radar_status():
            """Obtiene estado del Radar Universal"""
            try:
                if self.orchestrator is None:
                    raise HTTPException(status_code=503, detail=f"Discovery no disponible: {_IMPORT_ERROR}")
                all_detected = await self.orchestrator.get_all_detected()
                pending = await self.orchestrator.get_pending_hardware()
                
                return {
                    "status": "success",
                    "radar_running": self.orchestrator.is_running,
                    "total_detected": len(all_detected),
                    "pending_assimilation": len(pending),
                    "detected_by_source": {
                        "USB": len([d for d in all_detected if d.source == DetectionSource.USB]),
                        "BLUETOOTH": len([d for d in all_detected if d.source == DetectionSource.BLE]),
                        "WIFI": len([d for d in all_detected if d.source == DetectionSource.MDNS]),
                        "ECOWITT": len([d for d in all_detected if d.source == DetectionSource.ECOWITT]),
                    }
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    def set_system_core(self, core):
        """Establece referencia al SystemCore"""
        self.system_core = core
        if self.orchestrator is not None:
            self.orchestrator.usb_scanner = self.orchestrator.usb_scanner  # Asegurar acceso
    
    def set_sensor_assimilator(self, assimilator):
        """Establece referencia al SensorAssimilator"""
        self.sensor_assimilator = assimilator
    
    def get_router(self):
        """Retorna el router de FastAPI"""
        return self.router
    
    async def on_new_hardware_callback(self, hardware: DetectedHardware):
        """Callback cuando se detecta nuevo hardware"""
        logger.info(f"📢 Nuevo hardware detectado: {hardware.sensor_id} ({hardware.sensor_type})")
    
    async def on_ready_for_assimilation_callback(self, hardware: DetectedHardware):
        """Callback cuando hardware está listo para asimilación"""
        logger.info(f"✨ Hardware listo para asimilación: {hardware.sensor_id}")
    
    async def register_callbacks(self):
        """Registra callbacks con el orquestador"""
        if self.orchestrator is None:
            raise RuntimeError(f"Discovery no disponible: {_IMPORT_ERROR}")
        await self.orchestrator.register_callback('new_hardware', self.on_new_hardware_callback)
        await self.orchestrator.register_callback('ready_for_assimilation', self.on_ready_for_assimilation_callback)


# Instancia global
omnipotence_integration = OmnipotenceIntegration()


def get_omnipotence_integration() -> OmnipotenceIntegration:
    """Retorna la instancia global de integración"""
    return omnipotence_integration
