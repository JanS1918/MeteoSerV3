# Sistema de fiabilidad y alertas para sensores e índices
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path
from core.data_model import Fiabilidad

class FiabilidadManager:
    """Gestiona el estado de fiabilidad, alertas y errores de sensores e índices."""
    
    def __init__(self):
        self.estado_sensores: Dict[str, Dict[str, Any]] = {}
        self.alertas_activas: Dict[str, Dict[str, Any]] = {}
        self.historial_alertas: List[Dict[str, Any]] = []
        
    def registrar_sensor(self, nombre: str, tipo: str, fiabilidad: Fiabilidad = Fiabilidad.ALTA):
        """Registra un nuevo sensor en el sistema de fiabilidad."""
        self.estado_sensores[nombre] = {
            'nombre': nombre,
            'tipo': tipo,
            'fiabilidad': fiabilidad.value,
            'ultima_lectura': None,
            'ultimo_error': None,
            'contador_errores': 0,
            'contador_lecturas_ok': 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def actualizar_lectura(self, nombre: str, exito: bool, valor: Optional[float] = None, error: Optional[str] = None):
        """Actualiza el estado de fiabilidad tras una lectura."""
        if nombre not in self.estado_sensores:
            self.registrar_sensor(nombre, 'desconocido')
        
        sensor = self.estado_sensores[nombre]
        sensor['timestamp'] = datetime.now().isoformat()
        
        if exito:
            sensor['contador_lecturas_ok'] += 1
            sensor['ultima_lectura'] = valor
            sensor['ultimo_error'] = None
            
            # Mejorar fiabilidad si hay lecturas consecutivas OK
            if sensor['contador_lecturas_ok'] > 10 and sensor['fiabilidad'] != Fiabilidad.ALTA.value:
                sensor['fiabilidad'] = Fiabilidad.MEDIA.value
            if sensor['contador_lecturas_ok'] > 50:
                sensor['fiabilidad'] = Fiabilidad.ALTA.value
            
            # Limpiar alerta si existe
            if nombre in self.alertas_activas:
                self._cerrar_alerta(nombre)
        else:
            sensor['contador_errores'] += 1
            sensor['ultimo_error'] = error
            sensor['contador_lecturas_ok'] = 0
            
            # Degradar fiabilidad
            if sensor['contador_errores'] > 3:
                sensor['fiabilidad'] = Fiabilidad.BAJA.value
            if sensor['contador_errores'] > 10:
                sensor['fiabilidad'] = Fiabilidad.FALLA.value
            
            # Crear alerta
            self._crear_alerta(nombre, error or 'Error de lectura')
    
    def _crear_alerta(self, nombre: str, mensaje: str):
        """Crea una nueva alerta para un sensor."""
        alerta = {
            'nombre': nombre,
            'mensaje': mensaje,
            'gravedad': 'alta' if self.estado_sensores[nombre]['contador_errores'] > 10 else 'media',
            'timestamp': datetime.now().isoformat(),
            'resuelta': False
        }
        self.alertas_activas[nombre] = alerta
        self.historial_alertas.append(alerta.copy())
    
    def _cerrar_alerta(self, nombre: str):
        """Cierra una alerta activa."""
        if nombre in self.alertas_activas:
            self.alertas_activas[nombre]['resuelta'] = True
            del self.alertas_activas[nombre]
    
    def obtener_fiabilidad(self, nombre: str) -> str:
        """Obtiene la fiabilidad actual de un sensor."""
        if nombre not in self.estado_sensores:
            return Fiabilidad.MEDIA.value
        return self.estado_sensores[nombre]['fiabilidad']
    
    def obtener_alertas_activas(self) -> List[Dict[str, Any]]:
        """Obtiene todas las alertas activas."""
        return list(self.alertas_activas.values())
    
    def obtener_estado_completo(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema de fiabilidad."""
        return {
            'sensores': self.estado_sensores,
            'alertas_activas': list(self.alertas_activas.values()),
            'total_sensores': len(self.estado_sensores),
            'total_alertas': len(self.alertas_activas)
        }
    
    def cerrar_alerta_manual(self, nombre: str) -> bool:
        """Cierra manualmente una alerta."""
        if nombre in self.alertas_activas:
            self._cerrar_alerta(nombre)
            return True
        return False
