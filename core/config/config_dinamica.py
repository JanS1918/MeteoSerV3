"""
═══════════════════════════════════════════════════════════════════════════════
STEP 13: FEATURE FLAGS & CONFIGURACIÓN DINÁMICA
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Hot reload de configuración sin reiniciar
  - Feature flags por tenant
  - Override dinámico de thresholds
  - Rollback automático en degradación

Fecha de creación: 2026-02-11
Versión: 1.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)
DATA_PATH = Path("data/config")
DATA_PATH.mkdir(parents=True, exist_ok=True)


class EstadoFeature(str, Enum):
    """Estados de una feature."""
    DESHABILITADO = "deshabilitado"
    HABILITADO = "habilitado"
    ROLLING = "rolling"  # Rollout gradual
    DEGRADADO = "degradado"  # Con problemas pero activo


@dataclass
class ConfiguracionDinamica:
    """Configuración que puede cambiar en caliente."""
    clave: str
    valor: Any
    tipo: str  # 'float', 'int', 'str', 'bool', 'list', 'dict'
    descripcion: str = ""
    
    # Validación
    minimo: Optional[float] = None
    maximo: Optional[float] = None
    valores_permitidos: Optional[List] = None
    
    # Metadata
    tenant_id: str = "default"
    timestamp_creacion: str = ""
    timestamp_actualizacion: str = ""
    version: int = 1
    
    def __post_init__(self):
        if not self.timestamp_creacion:
            self.timestamp_creacion = datetime.now().isoformat()
        self.timestamp_actualizacion = datetime.now().isoformat()
    
    def validar(self, nuevo_valor: Any) -> tuple[bool, str]:
        """Valida nuevo valor."""
        try:
            # Validar tipo
            tipo_esperado = type(nuevo_valor).__name__
            if self.tipo == 'float' and not isinstance(nuevo_valor, (int, float)):
                return False, "Debe ser número"
            if self.tipo == 'int' and not isinstance(nuevo_valor, int):
                return False, "Debe ser entero"
            if self.tipo == 'bool' and not isinstance(nuevo_valor, bool):
                return False, "Debe ser booleano"
            
            # Validar rango
            if self.minimo is not None and nuevo_valor < self.minimo:
                return False, f"Menor a mínimo {self.minimo}"
            if self.maximo is not None and nuevo_valor > self.maximo:
                return False, f"Mayor a máximo {self.maximo}"
            
            # Validar valores permitidos
            if self.valores_permitidos and nuevo_valor not in self.valores_permitidos:
                return False, f"No está en {self.valores_permitidos}"
            
            return True, "Válido"
            
        except Exception as e:
            return False, str(e)


@dataclass
class FeatureFlag:
    """Feature flag con control granular."""
    nombre: str
    estado: EstadoFeature = EstadoFeature.DESHABILITADO
    descripcion: str = ""
    
    # Deploy gradual
    porcentaje_rollout: float = 0.0  # 0-100 para ROLLING
    usuarios_whitelist: list = None
    usuarios_blacklist: list = None
    
    # Metadata
    tenant_id: str = "default"
    timestamp_creacion: str = ""
    timestamp_actualizacion: str = ""
    version: int = 1
    
    def __post_init__(self):
        if not self.timestamp_creacion:
            self.timestamp_creacion = datetime.now().isoformat()
        self.timestamp_actualizacion = datetime.now().isoformat()
        if self.usuarios_whitelist is None:
            self.usuarios_whitelist = []
        if self.usuarios_blacklist is None:
            self.usuarios_blacklist = []


# ═══════════════════════════════════════════════════════════════════════════
# GESTOR DE CONFIGURACIÓN DINÁMICA
# ═══════════════════════════════════════════════════════════════════════════

class GestorConfigDinamica:
    """Gestiona configuración dinámica con validación."""
    
    def __init__(self):
        self.configuraciones: Dict[str, ConfiguracionDinamica] = {}
        self.features: Dict[str, FeatureFlag] = {}
        self.historico_cambios = []
        
        self.ruta_config = DATA_PATH / "configuraciones"
        self.ruta_features = DATA_PATH / "features"
        self.ruta_historico = DATA_PATH / "historico"
        
        self.ruta_config.mkdir(parents=True, exist_ok=True)
        self.ruta_features.mkdir(parents=True, exist_ok=True)
        self.ruta_historico.mkdir(parents=True, exist_ok=True)
        
        self._cargar_todas()
    
    def _cargar_todas(self):
        """Carga configuraciones y features existentes."""
        # Cargar configuraciones
        if self.ruta_config.exists():
            for archivo in self.ruta_config.glob("*.json"):
                try:
                    with open(archivo, 'r') as f:
                        datos = json.load(f)
                        config = ConfiguracionDinamica(**datos)
                        self.configuraciones[config.clave] = config
                except Exception as e:
                    logger.warning(f"Error cargando config: {e}")
        
        # Cargar features
        if self.ruta_features.exists():
            for archivo in self.ruta_features.glob("*.json"):
                try:
                    with open(archivo, 'r') as f:
                        datos = json.load(f)
                        feature = FeatureFlag(**datos)
                        self.features[feature.nombre] = feature
                except Exception as e:
                    logger.warning(f"Error cargando feature: {e}")
    
    def obtener_configuracion(self, clave: str, 
                             default: Any = None) -> Any:
        """Obtiene valor de configuración."""
        config = self.configuraciones.get(clave)
        return config.valor if config else default
    
    def actualizar_configuracion(self, clave: str, 
                                nuevo_valor: Any) -> bool:
        """Actualiza configuración con validación."""
        
        config = self.configuraciones.get(clave)
        if not config:
            logger.warning(f"Configuración {clave} no existe")
            return False
        
        # Validar
        valido, mensaje = config.validar(nuevo_valor)
        if not valido:
            logger.error(f"Validación fallida para {clave}: {mensaje}")
            return False
        
        valor_anterior = config.valor
        config.valor = nuevo_valor
        config.version += 1
        config.timestamp_actualizacion = datetime.now().isoformat()
        
        # Guardar
        self._guardar_configuracion(config)
        self._registrar_cambio(clave, valor_anterior, nuevo_valor)
        
        logger.info(f"Config actualizada: {clave} = {nuevo_valor}")
        return True
    
    def _guardar_configuracion(self, config: ConfiguracionDinamica):
        """Guarda configuración."""
        archivo = self.ruta_config / f"{config.clave}.json"
        with open(archivo, 'w') as f:
            json.dump(asdict(config), f, indent=2, default=str)
    
    def crear_configuracion(self, clave: str, valor: Any, 
                           tipo: str, **kwargs) -> ConfiguracionDinamica:
        """Crea nueva configuración."""
        
        if clave in self.configuraciones:
            raise ValueError(f"Configuración {clave} ya existe")
        
        config = ConfiguracionDinamica(
            clave=clave,
            valor=valor,
            tipo=tipo,
            **kwargs
        )
        
        self._guardar_configuracion(config)
        self.configuraciones[clave] = config
        
        return config
    
    # ─────────────────────────────────────────────────────────────────────
    # FEATURE FLAGS
    # ─────────────────────────────────────────────────────────────────────
    
    def crear_feature_flag(self, nombre: str, 
                          estado: str = "deshabilitado",
                          **kwargs) -> FeatureFlag:
        """Crea nuevo feature flag."""
        
        feature = FeatureFlag(
            nombre=nombre,
            estado=EstadoFeature(estado),
            **kwargs
        )
        
        self._guardar_feature(feature)
        self.features[nombre] = feature
        
        logger.info(f"Feature flag creado: {nombre}")
        return feature
    
    def actualizar_feature(self, nombre: str, 
                          **cambios) -> Optional[FeatureFlag]:
        """Actualiza feature flag."""
        
        feature = self.features.get(nombre)
        if not feature:
            return None
        
        for clave, valor in cambios.items():
            if hasattr(feature, clave):
                setattr(feature, clave, valor)
        
        feature.version += 1
        feature.timestamp_actualizacion = datetime.now().isoformat()
        
        self._guardar_feature(feature)
        logger.info(f"Feature actualizado: {nombre}")
        
        return feature
    
    def _guardar_feature(self, feature: FeatureFlag):
        """Guarda feature flag."""
        archivo = self.ruta_features / f"{feature.nombre}.json"
        with open(archivo, 'w') as f:
            json.dump(asdict(feature), f, indent=2, default=str)
    
    def esta_habilitada_feature(self, nombre: str, 
                               usuario_id: str = None) -> bool:
        """Verifica si feature está habilitada para usuario."""
        
        feature = self.features.get(nombre)
        if not feature:
            return False
        
        # Verificar estado
        if feature.estado == EstadoFeature.DESHABILITADO:
            return False
        
        if feature.estado == EstadoFeature.DEGRADADO:
            return True  # Sigue activa pero degradada
        
        # Verificar whitelist/blacklist
        if usuario_id:
            if usuario_id in feature.usuarios_blacklist:
                return False
            if feature.usuarios_whitelist and usuario_id not in feature.usuarios_whitelist:
                return False
        
        # Rolling deployment
        if feature.estado == EstadoFeature.ROLLING:
            if usuario_id:
                import hashlib
                hash_usuario = int(
                    hashlib.md5(usuario_id.encode()).hexdigest(), 16
                ) % 100
                return hash_usuario < feature.porcentaje_rollout
            return feature.porcentaje_rollout > 0
        
        return True
    
    def _registrar_cambio(self, clave: str, 
                         valor_anterior: Any, valor_nuevo: Any):
        """Registra cambio en histórico."""
        
        cambio = {
            'timestamp': datetime.now().isoformat(),
            'clave': clave,
            'valor_anterior': valor_anterior,
            'valor_nuevo': valor_nuevo
        }
        
        self.historico_cambios.append(cambio)
        
        # Guardar en archivo
        archivo = self.ruta_historico / f"cambio_{len(self.historico_cambios)}.json"
        with open(archivo, 'w') as f:
            json.dump(cambio, f, indent=2, default=str)
    
    def obtener_histocico_cambios(self, limites: int = 100) -> list:
        """Obtiene histórico de cambios."""
        return self.historico_cambios[-limites:]


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_gestor_config_instance = None


def obtener_gestor_config() -> GestorConfigDinamica:
    """Obtiene instancia singleton."""
    global _gestor_config_instance
    if _gestor_config_instance is None:
        _gestor_config_instance = GestorConfigDinamica()
    return _gestor_config_instance


def iniciar_gestor_config() -> Dict[str, Any]:
    """Inicializa gestor de configuración."""
    try:
        gestor = obtener_gestor_config()
        
        # Crear configuraciones default si no existen
        default_configs = [
            ('umbral_alerta_critica_wh31', 2.0, 'float'),
            ('umbral_alerta_severa_wh31', 1.5, 'float'),
            ('intervalo_monitoreo_alertas', 30, 'int'),
            ('intervalo_validacion_wh31', 604800, 'int'),  # 7 días
            ('habilitado_notificaciones_email', True, 'bool'),
            ('habilitado_notificaciones_slack', True, 'bool'),
        ]
        
        for clave, valor, tipo in default_configs:
            if clave not in gestor.configuraciones:
                gestor.crear_configuracion(clave, valor, tipo)
        
        contexto = {
            'estado': 'ACTIVO',
            'configuraciones_cargadas': len(gestor.configuraciones),
            'features_cargadas': len(gestor.features),
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[CONFIG] Gestor iniciado - "
            f"{contexto['configuraciones_cargadas']} configs, "
            f"{contexto['features_cargadas']} features"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando configuración: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
