"""
═══════════════════════════════════════════════════════════════════════════════
STEP 21: CLUSTERING & DISTRIBUCIÓN DE CARGA
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Soporte para múltiples instancias
  - Load balancing
  - Session affinity
  - Health checks distribuidos

Fecha: 2026-02-11
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EstadoNodo(str, Enum):
    """Estados de nodos en cluster."""
    SALUDABLE = "saludable"
    DEGRADADO = "degradado"
    NO_DISPONIBLE = "no_disponible"
    INICIALIZANDO = "inicializando"


@dataclass
class NodoCluster:
    """Nodo en cluster."""
    nodo_id: str
    host: str
    puerto: int
    estado: EstadoNodo = EstadoNodo.INICIALIZANDO
    carga_cpu: float = 0.0
    carga_memoria: float = 0.0
    conexiones_activas: int = 0
    timestamp_heartbeat: str = ""
    rol: str = "worker"  # "master" o "worker"


class GestorCluster:
    """Gestiona cluster de instancias."""
    
    def __init__(self, nodo_id: str, host: str, puerto: int, rol: str = "worker"):
        self.nodo_local = NodoCluster(
            nodo_id=nodo_id,
            host=host,
            puerto=puerto,
            rol=rol
        )
        self.nodos_remotos: Dict[str, NodoCluster] = {}
        self.lider = None  # ID del nodo líder (master)
    
    def registrar_nodo(self, nodo: NodoCluster):
        """Registra nodo remoto en cluster."""
        
        self.nodos_remotos[nodo.nodo_id] = nodo
        logger.info(f"Nodo registrado: {nodo.nodo_id} ({nodo.host}:{nodo.puerto})")
    
    def obtener_nodo_para_balance(self) -> NodoCluster:
        """Obtiene nodo con menor carga para balance."""
        
        nodos_saludables = [
            n for n in self.nodos_remotos.values()
            if n.estado == EstadoNodo.SALUDABLE
        ]
        
        if not nodos_saludables:
            return self.nodo_local
        
        # Seleccionar por menor carga
        return min(
            nodos_saludables,
            key=lambda n: n.conexiones_activas
        )
    
    def actualizar_carga_nodo(self, nodo_id: str, 
                             cpu: float, memoria: float,
                             conexiones: int):
        """Actualiza métricas de carga del nodo."""
        
        if nodo_id == self.nodo_local.nodo_id:
            self.nodo_local.carga_cpu = cpu
            self.nodo_local.carga_memoria = memoria
            self.nodo_local.conexiones_activas = conexiones
        elif nodo_id in self.nodos_remotos:
            nodo = self.nodos_remotos[nodo_id]
            nodo.carga_cpu = cpu
            nodo.carga_memoria = memoria
            nodo.conexiones_activas = conexiones
    
    def obtener_estado_cluster(self) -> Dict[str, Any]:
        """Obtiene estado general del cluster."""
        
        todos_nodos = [self.nodo_local] + list(self.nodos_remotos.values())
        
        saludables = len([n for n in todos_nodos if n.estado == EstadoNodo.SALUDABLE])
        degradados = len([n for n in todos_nodos if n.estado == EstadoNodo.DEGRADADO])
        no_disponibles = len([n for n in todos_nodos if n.estado == EstadoNodo.NO_DISPONIBLE])
        
        return {
            'total_nodos': len(todos_nodos),
            'saludables': saludables,
            'degradados': degradados,
            'no_disponibles': no_disponibles,
            'lider': self.lider,
            'nodo_local': {
                'id': self.nodo_local.nodo_id,
                'estado': self.nodo_local.estado.value,
                'carga_cpu': self.nodo_local.carga_cpu,
                'conexiones': self.nodo_local.conexiones_activas
            }
        }


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_gestor_cluster_instance = None


def obtener_gestor_cluster() -> GestorCluster:
    """Obtiene instancia singleton."""
    global _gestor_cluster_instance
    if _gestor_cluster_instance is None:
        import os
        import socket
        
        nodo_id = os.getenv('NODE_ID', socket.gethostname())
        host = os.getenv('NODE_HOST', '127.0.0.1')
        puerto = int(os.getenv('NODE_PORT', 8000))
        rol = os.getenv('NODE_ROLE', 'worker')
        
        _gestor_cluster_instance = GestorCluster(
            nodo_id=nodo_id,
            host=host,
            puerto=puerto,
            rol=rol
        )
    
    return _gestor_cluster_instance


def iniciar_gestor_cluster() -> Dict[str, Any]:
    """Inicializa clustering."""
    try:
        gestor = obtener_gestor_cluster()
        
        contexto = {
            'estado': 'ACTIVO',
            'nodo_id': gestor.nodo_local.nodo_id,
            'rol': gestor.nodo_local.rol,
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[CLUSTER] Nodo iniciado: {contexto['nodo_id']} "
            f"({contexto['rol']})"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando cluster: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
