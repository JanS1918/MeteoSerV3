# Sistema de auditoría y logs de cambios
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

class AuditoriaManager:
    """Gestiona logs y auditoría de cambios en el sistema."""
    
    def __init__(self, log_path: str = "data/auditoria.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.cambios_sesion: List[Dict[str, Any]] = []
    
    def registrar_cambio(self, tipo: str, entidad: str, cambio: Dict[str, Any], 
                        usuario: str = 'sistema', metadata: Optional[Dict[str, Any]] = None):
        """Registra un cambio en el sistema."""
        registro = {
            'tipo': tipo,  # 'movimiento', 'edicion', 'configuracion', 'feedback', 'alerta'
            'entidad': entidad,  # nombre del valor, sensor, cajón, etc.
            'cambio': cambio,
            'usuario': usuario,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self._guardar_log(registro)
        self.cambios_sesion.append(registro)
        if len(self.cambios_sesion) > 500:
            self.cambios_sesion = self.cambios_sesion[-500:]
    
    def _guardar_log(self, registro: Dict[str, Any]):
        """Guarda un registro en el archivo de auditoría."""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(registro, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Error guardando auditoría: {e}")
    
    def registrar_movimiento(self, valor: str, origen: str, destino: str, usuario: str = 'sistema'):
        """Registra el movimiento de un valor entre cajones."""
        self.registrar_cambio(
            tipo='movimiento',
            entidad=valor,
            cambio={'origen': origen, 'destino': destino},
            usuario=usuario
        )
    
    def registrar_edicion(self, entidad: str, campo: str, valor_anterior: Any, valor_nuevo: Any, usuario: str = 'sistema'):
        """Registra la edición de un nombre o valor."""
        self.registrar_cambio(
            tipo='edicion',
            entidad=entidad,
            cambio={'campo': campo, 'anterior': valor_anterior, 'nuevo': valor_nuevo},
            usuario=usuario
        )
    
    def registrar_configuracion(self, parametro: str, valor_anterior: Any, valor_nuevo: Any, usuario: str = 'sistema'):
        """Registra cambios en la configuración."""
        self.registrar_cambio(
            tipo='configuracion',
            entidad=parametro,
            cambio={'anterior': valor_anterior, 'nuevo': valor_nuevo},
            usuario=usuario
        )
    
    def registrar_feedback_log(self, indice: str, detalles: Dict[str, Any], usuario: str = 'sistema'):
        """Registra feedback del usuario."""
        self.registrar_cambio(
            tipo='feedback',
            entidad=indice,
            cambio=detalles,
            usuario=usuario
        )
    
    def registrar_alerta_log(self, sensor: str, alerta: Dict[str, Any], usuario: str = 'sistema'):
        """Registra alertas del sistema."""
        self.registrar_cambio(
            tipo='alerta',
            entidad=sensor,
            cambio=alerta,
            usuario=usuario
        )
    
    def obtener_historial(self, tipo: Optional[str] = None, entidad: Optional[str] = None, 
                         limite: int = 100) -> List[Dict[str, Any]]:
        """Obtiene el historial de cambios filtrado."""
        resultado = self.cambios_sesion
        
        if tipo:
            resultado = [r for r in resultado if r['tipo'] == tipo]
        
        if entidad:
            resultado = [r for r in resultado if r['entidad'] == entidad]
        
        return resultado[-limite:]
    
    def restaurar_movimientos(self, numero_movimientos: int) -> List[Dict[str, Any]]:
        """Restaura los últimos N movimientos realizados."""
        movimientos = [r for r in self.cambios_sesion if r['tipo'] == 'movimiento']
        movimientos_a_restaurar = movimientos[-numero_movimientos:]
        
        # Invertir el orden para deshacer de último a primero
        movimientos_a_restaurar.reverse()
        
        acciones_restauracion = []
        for mov in movimientos_a_restaurar:
            accion = {
                'valor': mov['entidad'],
                'origen': mov['cambio']['destino'],  # Invertido
                'destino': mov['cambio']['origen'],  # Invertido
                'timestamp_original': mov['timestamp']
            }
            acciones_restauracion.append(accion)
            
            # Registrar la restauración
            self.registrar_movimiento(
                valor=mov['entidad'],
                origen=mov['cambio']['destino'],
                destino=mov['cambio']['origen'],
                usuario='sistema_restauracion'
            )
        
        return acciones_restauracion
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de auditoría."""
        tipos = {}
        for registro in self.cambios_sesion:
            tipo = registro['tipo']
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        return {
            'total_cambios': len(self.cambios_sesion),
            'por_tipo': tipos,
            'ultimo_cambio': self.cambios_sesion[-1] if self.cambios_sesion else None
        }
