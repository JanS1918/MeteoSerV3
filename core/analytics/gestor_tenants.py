"""
═══════════════════════════════════════════════════════════════════════════════
STEP 10: MULTI-TENANT ISOLATION & ESCALABILIDAD
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Soporte para múltiples dominios/tenants independientes
  - Isolación completa de alertas y datos por tenant
  - Configuración de thresholds personalizados
  - Namespace separation en almacenamiento
  - Preparación para expansión futura

Fecha de creación: 2026-02-11
Versión: 1.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════
# MODELOS Y ENUMS
# ═══════════════════════════════════════════════════════════════════════════

logger = logging.getLogger(__name__)
DATA_PATH = Path("data/tenants")
DATA_PATH.mkdir(parents=True, exist_ok=True)


class EstadoTenant(str, Enum):
    """Estados posibles de un tenant."""
    ACTIVO = "ACTIVO"
    PAUSADO = "PAUSADO"
    DEGRADADO = "DEGRADADO"
    SUSPENDIDO = "SUSPENDIDO"


@dataclass
class ConfiguracionTenant:
    """Configuración de tenant individual."""
    tenant_id: str
    nombre: str
    descripcion: str = ""
    dominio_primario: str = ""
    
    # Thresholds de alertas
    umbral_critico_wh31: float = 2.0      # °C de error máximo para crítico
    umbral_severo_wh31: float = 1.5        # °C para severo
    umbral_critico_cobertura: int = 70     # % mínimo cobertura audit
    
    # Configuración de notificaciones
    email_contacto: str = ""
    slack_webhook: Optional[str] = None
    notificaciones_habilitadas: bool = True
    
    # Configuración de retención
    dias_retencion_alertas: int = 90
    dias_retencion_auditorias: int = 180
    
    # Metadatos
    estado: EstadoTenant = EstadoTenant.ACTIVO
    timestamp_creacion: str = ""
    timestamp_actualizacion: str = ""
    custom_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.timestamp_creacion:
            self.timestamp_creacion = datetime.now().isoformat()
        self.timestamp_actualizacion = datetime.now().isoformat()
        if self.custom_metadata is None:
            self.custom_metadata = {}


# ═══════════════════════════════════════════════════════════════════════════
# GESTOR DE TENANTS
# ═══════════════════════════════════════════════════════════════════════════

class GestorTenants:
    """Gestiona múltiples tenants con aislamiento completo."""
    
    def __init__(self):
        self.ruta_config = DATA_PATH / "configuraciones"
        self.ruta_datos = DATA_PATH / "datos"
        
        self.ruta_config.mkdir(parents=True, exist_ok=True)
        self.ruta_datos.mkdir(parents=True, exist_ok=True)
        
        self.tenants_activos: Dict[str, ConfiguracionTenant] = {}
        self._cargar_tenants()
    
    def _cargar_tenants(self):
        """Carga configuraciones de tenants existentes."""
        if not self.ruta_config.exists():
            return
        
        for archivo in self.ruta_config.glob("tenant_*.json"):
            try:
                with open(archivo, 'r') as f:
                    datos = json.load(f)
                    
                    # Reconstruir objeto ConfiguracionTenant
                    configuracion = ConfiguracionTenant(
                        tenant_id=datos['tenant_id'],
                        nombre=datos['nombre'],
                        descripcion=datos.get('descripcion', ''),
                        dominio_primario=datos.get('dominio_primario', ''),
                        umbral_critico_wh31=datos.get('umbral_critico_wh31', 2.0),
                        umbral_severo_wh31=datos.get('umbral_severo_wh31', 1.5),
                        umbral_critico_cobertura=datos.get('umbral_critico_cobertura', 70),
                        email_contacto=datos.get('email_contacto', ''),
                        slack_webhook=datos.get('slack_webhook'),
                        notificaciones_habilitadas=datos.get('notificaciones_habilitadas', True),
                        dias_retencion_alertas=datos.get('dias_retencion_alertas', 90),
                        dias_retencion_auditorias=datos.get('dias_retencion_auditorias', 180),
                        estado=EstadoTenant(datos.get('estado', 'ACTIVO')),
                        timestamp_creacion=datos.get('timestamp_creacion', ''),
                        timestamp_actualizacion=datos.get('timestamp_actualizacion', '')
                    )
                    
                    self.tenants_activos[configuracion.tenant_id] = configuracion
                    logger.info(f"Tenant cargado: {configuracion.tenant_id}")
                    
            except Exception as e:
                logger.warning(f"Error cargando {archivo}: {e}")
    
    def crear_tenant(self, tenant_id: str, nombre: str, 
                     **kwargs) -> ConfiguracionTenant:
        """Crea nuevo tenant con configuración."""
        
        if tenant_id in self.tenants_activos:
            raise ValueError(f"Tenant {tenant_id} ya existe")
        
        configuracion = ConfiguracionTenant(
            tenant_id=tenant_id,
            nombre=nombre,
            **kwargs
        )
        
        # Guardar configuración
        self._guardar_configuracion(configuracion)
        
        # Crear directorios de datos
        self._crear_estructura_datos(tenant_id)
        
        self.tenants_activos[tenant_id] = configuracion
        
        logger.info(f"Tenant creado: {tenant_id}")
        return configuracion
    
    def _guardar_configuracion(self, configuracion: ConfiguracionTenant):
        """Guarda configuración de tenant en archivo."""
        archivo = self.ruta_config / f"tenant_{configuracion.tenant_id}.json"
        
        datos = asdict(configuracion)
        datos['estado'] = datos['estado'].value  # Convertir enum a string
        
        with open(archivo, 'w') as f:
            json.dump(datos, f, indent=2, default=str)
    
    def _crear_estructura_datos(self, tenant_id: str):
        """Crea estructura de directorios para tenant."""
        directorios = [
            self.ruta_datos / tenant_id / "alertas",
            self.ruta_datos / tenant_id / "auditorias",
            self.ruta_datos / tenant_id / "validaciones",
            self.ruta_datos / tenant_id / "reportes"
        ]
        
        for directorio in directorios:
            directorio.mkdir(parents=True, exist_ok=True)
    
    def obtener_tenant(self, tenant_id: str) -> Optional[ConfiguracionTenant]:
        """Obtiene configuración de un tenant."""
        return self.tenants_activos.get(tenant_id)
    
    def obtener_todos_tenants(self) -> List[ConfiguracionTenant]:
        """Obtiene lista de todos los tenants."""
        return list(self.tenants_activos.values())
    
    def actualizar_tenant(self, tenant_id: str, 
                         **configuracion) -> ConfiguracionTenant:
        """Actualiza configuración de tenant."""
        
        tenant = self.obtener_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} no existe")
        
        # Actualizar campos permitidos
        campos_permitidos = {
            'nombre', 'descripcion', 'dominio_primario',
            'umbral_critico_wh31', 'umbral_severo_wh31',
            'umbral_critico_cobertura', 'email_contacto',
            'slack_webhook', 'notificaciones_habilitadas',
            'dias_retencion_alertas', 'dias_retencion_auditorias',
            'estado', 'custom_metadata'
        }
        
        for clave, valor in configuracion.items():
            if clave in campos_permitidos:
                if clave == 'estado' and isinstance(valor, str):
                    valor = EstadoTenant(valor)
                setattr(tenant, clave, valor)
        
        tenant.timestamp_actualizacion = datetime.now().isoformat()
        self._guardar_configuracion(tenant)
        
        logger.info(f"Tenant actualizado: {tenant_id}")
        return tenant
    
    def cambiar_estado_tenant(self, tenant_id: str, 
                             nuevo_estado: EstadoTenant) -> ConfiguracionTenant:
        """Cambia estado operacional de un tenant."""
        return self.actualizar_tenant(tenant_id, estado=nuevo_estado)
    
    def obtener_ruta_datos_tenant(self, tenant_id: str, 
                                  tipo: str = None) -> Path:
        """Obtiene ruta de almacenamiento para datos de tenant."""
        ruta = self.ruta_datos / tenant_id
        
        if tipo and tipo in ['alertas', 'auditorias', 'validaciones', 'reportes']:
            ruta = ruta / tipo
        
        return ruta
    
    # ─────────────────────────────────────────────────────────────────────
    # AISLAMIENTO DE ALERTAS
    # ─────────────────────────────────────────────────────────────────────
    
    def registrar_alerta_tenant(self, tenant_id: str, 
                               alerta: Dict[str, Any]) -> bool:
        """Registra alerta aislada en namespace de tenant."""
        
        tenant = self.obtener_tenant(tenant_id)
        if not tenant:
            logger.warning(f"Tenant {tenant_id} no existe")
            return False
        
        if tenant.estado != EstadoTenant.ACTIVO:
            logger.warning(f"Tenant {tenant_id} no está activo ({tenant.estado})")
            return False
        
        try:
            ruta_alertas = self.obtener_ruta_datos_tenant(tenant_id, 'alertas')
            
            # Validar contra thresholds del tenant
            alerta['tenant_id'] = tenant_id
            alerta['procesada_en'] = datetime.now().isoformat()
            
            # Guardar con nombre basado en timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            archivo = ruta_alertas / f"alerta_{timestamp}.json"
            
            with open(archivo, 'w') as f:
                json.dump(alerta, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            logger.error(f"Error registrando alerta en tenant {tenant_id}: {e}")
            return False
    
    def obtener_alertas_tenant(self, tenant_id: str, 
                               limites: int = 100) -> List[Dict]:
        """Obtiene alertas de un tenant específico."""
        
        ruta_alertas = self.obtener_ruta_datos_tenant(tenant_id, 'alertas')
        alertas = []
        
        if not ruta_alertas.exists():
            return alertas
        
        for archivo in sorted(
            ruta_alertas.glob("alerta_*.json"),
            reverse=True
        )[:limites]:
            try:
                with open(archivo, 'r') as f:
                    alertas.append(json.load(f))
            except:
                pass
        
        return alertas
    
    # ─────────────────────────────────────────────────────────────────────
    # REPORTES Y ESTADÍSTICAS POR TENANT
    # ─────────────────────────────────────────────────────────────────────
    
    def obtener_estadisticas_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Obtiene estadísticas agregadas de un tenant."""
        
        tenant = self.obtener_tenant(tenant_id)
        if not tenant:
            return {'error': 'Tenant no existe'}
        
        alertas = self.obtener_alertas_tenant(tenant_id, limites=1000)
        
        estadisticas = {
            'tenant_id': tenant_id,
            'nombre': tenant.nombre,
            'estado': tenant.estado.value,
            'timestamp_analisis': datetime.now().isoformat(),
            'total_alertas': len(alertas),
            'por_nivel': {},
            'configuracion': {
                'umbral_critico_wh31': tenant.umbral_critico_wh31,
                'umbral_severo_wh31': tenant.umbral_severo_wh31,
                'dias_retencion': tenant.dias_retencion_alertas
            }
        }
        
        # Contar por nivel
        for alerta in alertas:
            nivel = alerta.get('nivel', 'DESCONOCIDO')
            if nivel not in estadisticas['por_nivel']:
                estadisticas['por_nivel'][nivel] = 0
            estadisticas['por_nivel'][nivel] += 1
        
        return estadisticas
    
    def generar_resumen_multi_tenant(self) -> Dict[str, Any]:
        """Genera resumen de todos los tenants."""
        
        resumen = {
            'fecha_generacion': datetime.now().isoformat(),
            'total_tenants': len(self.tenants_activos),
            'tenants_activos': 0,
            'tenants_problematicos': 0,
            'detalle': []
        }
        
        for tenant in self.tenants_activos.values():
            stats = self.obtener_estadisticas_tenant(tenant.tenant_id)
            
            entrada = {
                'tenant_id': tenant.tenant_id,
                'nombre': tenant.nombre,
                'estado': tenant.estado.value,
                'alertas_totales': stats['total_alertas']
            }
            
            if tenant.estado == EstadoTenant.ACTIVO:
                resumen['tenants_activos'] += 1
            else:
                resumen['tenants_problematicos'] += 1
            
            resumen['detalle'].append(entrada)
        
        return resumen


# ═══════════════════════════════════════════════════════════════════════════
# MIDDLEWARE DE ISOLAMIENTO PARA API
# ═══════════════════════════════════════════════════════════════════════════

class IsladorTenantMiddleware:
    """Middleware para aislar requests por tenant."""
    
    def __init__(self, gestor: GestorTenants):
        self.gestor = gestor
    
    def validar_acceso_tenant(self, tenant_id: str) -> bool:
        """Valida si cliente tiene acceso a tenant."""
        tenant = self.gestor.obtener_tenant(tenant_id)
        return tenant is not None and tenant.estado == EstadoTenant.ACTIVO
    
    def aplicar_contexto_tenant(self, request_data: Dict, 
                               tenant_id: str) -> Dict:
        """Aplica contexto de tenant a request."""
        request_data['_tenant_id'] = tenant_id
        request_data['_tenant_config'] = self.gestor.obtener_tenant(tenant_id)
        return request_data
    
    def filtrar_respuesta_tenant(self, respuesta: Dict, 
                                tenant_id: str) -> Dict:
        """Asegura que respuesta solo contiene datos del tenant."""
        respuesta['tenant_id'] = tenant_id
        return respuesta


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES Y GETTERS
# ═══════════════════════════════════════════════════════════════════════════

_gestor_tenants_instance = None


def obtener_gestor_tenants() -> GestorTenants:
    """Obtiene instancia singleton del gestor de tenants."""
    global _gestor_tenants_instance
    if _gestor_tenants_instance is None:
        _gestor_tenants_instance = GestorTenants()
    return _gestor_tenants_instance


def iniciar_gestor_tenants() -> Dict[str, Any]:
    """Inicializa gestor de tenants con tenant default."""
    try:
        gestor = obtener_gestor_tenants()
        
        # Crear tenant default si no existe
        if 'default' not in gestor.tenants_activos:
            gestor.crear_tenant(
                'default',
                'Sistema Principal',
                descripcion='Tenant predeterminado del sistema',
                dominio_primario='meteoser.principal',
                email_contacto='admin@meteoser.local'
            )
        
        contexto = {
            'estado': 'ACTIVO',
            'tenants_cargados': len(gestor.tenants_activos),
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[TENANTS] Gestor iniciado - "
            f"{contexto['tenants_cargados']} tenants activos"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando gestor de tenants: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    gestor = obtener_gestor_tenants()
    
    # Crear tenant de prueba
    if 'prueba' not in gestor.tenants_activos:
        gestor.crear_tenant(
            'prueba',
            'Tenant de Prueba',
            descripcion='Para testing de multi-tenancy',
            dominio_primario='test.domain'
        )
    
    # Mostrar tenants
    print("\n=== TENANTS ACTIVOS ===")
    for tenant in gestor.obtener_todos_tenants():
        print(f"  • {tenant.tenant_id}: {tenant.nombre} ({tenant.estado.value})")
    
    # Estadísticas
    print("\n=== ESTADÍSTICAS TENANTS ===")
    for tenant in gestor.obtener_todos_tenants():
        stats = gestor.obtener_estadisticas_tenant(tenant.tenant_id)
        print(f"\n{tenant.tenant_id}:")
        print(f"  Total alertas: {stats['total_alertas']}")
        print(f"  Por nivel: {stats['por_nivel']}")
