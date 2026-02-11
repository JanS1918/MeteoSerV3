"""
═══════════════════════════════════════════════════════════════════════════════
STEP 28: VALIDACIÓN Y SANITIZACIÓN DE DATOS EN TIEMPO REAL
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Validar datos entrantes
  - Prevenir inyecciones
  - Esquemas predefinidos
  - Reportar errores de validación claramente

Fecha: 2026-02-11
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TipoValidacion(str, Enum):
    """Tipos de validación."""
    REQUERIDO = "REQUERIDO"
    STRING = "STRING"
    NUMERO = "NUMERO"
    ENTERO = "ENTERO"
    FLOTANTE = "FLOTANTE"
    BOOLEANO = "BOOLEANO"
    EMAIL = "EMAIL"
    URL = "URL"
    FECHA = "FECHA"
    ENUM = "ENUM"
    LISTA = "LISTA"
    DICCIONARIO = "DICCIONARIO"
    RANGO = "RANGO"
    PATRON = "PATRON"


class ErrorValidacion(Exception):
    """Excepción de validación."""
    pass


class CampoValidacion:
    """Define reglas de validación para un campo."""
    
    def __init__(self,
                 nombre: str,
                 tipo: TipoValidacion,
                 requerido: bool = True,
                 default: Any = None,
                 opciones: Dict[str, Any] = None):
        
        self.nombre = nombre
        self.tipo = tipo
        self.requerido = requerido
        self.default = default
        self.opciones = opciones or {}
    
    def validar(self, valor: Any) -> tuple[bool, Optional[str]]:
        """Valida un valor."""
        
        # Verificar requerido
        if valor is None or valor == "":
            if self.requerido:
                return False, f"Campo {self.nombre} es requerido"
            return True, None
        
        # Validar tipo
        return self._validar_tipo(valor)
    
    def _validar_tipo(self, valor: Any) -> tuple[bool, Optional[str]]:
        """Valida según tipo."""
        
        try:
            if self.tipo == TipoValidacion.STRING:
                if not isinstance(valor, str):
                    return False, f"{self.nombre} debe ser string"
                
                # Verificar longitud
                if 'min_len' in self.opciones:
                    if len(valor) < self.opciones['min_len']:
                        return False, f"{self.nombre} muy corto"
                
                if 'max_len' in self.opciones:
                    if len(valor) > self.opciones['max_len']:
                        return False, f"{self.nombre} muy largo"
            
            elif self.tipo == TipoValidacion.NUMERO:
                try:
                    float(valor)
                except:
                    return False, f"{self.nombre} debe ser número"
            
            elif self.tipo == TipoValidacion.ENTERO:
                try:
                    int(valor)
                except:
                    return False, f"{self.nombre} debe ser entero"
            
            elif self.tipo == TipoValidacion.EMAIL:
                patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(patron, valor):
                    return False, f"{self.nombre} no es email válido"
            
            elif self.tipo == TipoValidacion.URL:
                patron = r'^https?://'
                if not re.match(patron, valor):
                    return False, f"{self.nombre} no es URL válida"
            
            elif self.tipo == TipoValidacion.FECHA:
                try:
                    datetime.fromisoformat(valor)
                except:
                    return False, f"{self.nombre} no es fecha válida (ISO 8601)"
            
            elif self.tipo == TipoValidacion.ENUM:
                valores_permitidos = self.opciones.get('valores', [])
                if valor not in valores_permitidos:
                    return False, f"{self.nombre} valor no permitido"
            
            elif self.tipo == TipoValidacion.RANGO:
                num = float(valor)
                min_val = self.opciones.get('min')
                max_val = self.opciones.get('max')
                
                if min_val is not None and num < min_val:
                    return False, f"{self.nombre} menor que mínimo ({min_val})"
                if max_val is not None and num > max_val:
                    return False, f"{self.nombre} mayor que máximo ({max_val})"
            
            elif self.tipo == TipoValidacion.PATRON:
                patron = self.opciones.get('patron', '')
                if not re.match(patron, str(valor)):
                    return False, f"{self.nombre} no cumple patrón requerido"
            
            elif self.tipo == TipoValidacion.LISTA:
                if not isinstance(valor, list):
                    return False, f"{self.nombre} debe ser lista"
                
                if 'min_items' in self.opciones:
                    if len(valor) < self.opciones['min_items']:
                        return False, f"{self.nombre} tiene muy pocos items"
            
            elif self.tipo == TipoValidacion.DICCIONARIO:
                if not isinstance(valor, dict):
                    return False, f"{self.nombre} debe ser diccionario"
            
            return True, None
        
        except Exception as e:
            return False, f"Error validando {self.nombre}: {str(e)}"


class EsquemaValidacion:
    """Define esquema de validación para datos complejos."""
    
    def __init__(self, nombre_esquema: str):
        self.nombre_esquema = nombre_esquema
        self.campos: Dict[str, CampoValidacion] = {}
        self.errores_acumulados: List[str] = []
    
    def agregar_campo(self, campo: CampoValidacion):
        """Agrega campo de validación."""
        self.campos[campo.nombre] = campo
    
    def validar_datos(self, datos: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Valida datos contra esquema."""
        
        self.errores_acumulados = []
        
        for nombre_campo, campo in self.campos.items():
            valor = datos.get(nombre_campo)
            
            valido, error = campo.validar(valor)
            
            if not valido:
                self.errores_acumulados.append(error)
        
        return len(self.errores_acumulados) == 0, self.errores_acumulados
    
    def obtener_reporte_validacion(self) -> Dict[str, Any]:
        """Obtiene reporte de validación."""
        
        return {
            'esquema': self.nombre_esquema,
            'campos_definidos': len(self.campos),
            'errores': self.errores_acumulados,
            'es_valido': len(self.errores_acumulados) == 0,
            'timestamp': datetime.now().isoformat()
        }


class SanitizadorDatos:
    """Sanitiza datos para prevenir inyecciones."""
    
    @staticmethod
    def sanitizar_string(valor: str, permitir_espacios: bool = True) -> str:
        """Sanitiza string."""
        
        if not isinstance(valor, str):
            return str(valor)
        
        # Remover caracteres peligrosos
        caracteres_peligrosos = ['<', '>', '"', "'", '%', ';', '\\']
        
        resultado = valor
        for char in caracteres_peligrosos:
            resultado = resultado.replace(char, '')
        
        # Remover espacios múltiples
        if permitir_espacios:
            resultado = ' '.join(resultado.split())
        
        return resultado.strip()
    
    @staticmethod
    def sanitizar_sql(valor: str) -> str:
        """Sanitiza para SQL (básico)."""
        
        # NOTA: Usar prepared statements en vez de esto en producción
        valor = valor.replace("'", "''")
        valor = valor.replace('"', '""')
        
        return valor
    
    @staticmethod
    def sanitizar_json(valor: str) -> str:
        """Sanitiza JSON."""
        
        # Escapar caracteres especiales
        valor = valor.replace('\\', '\\\\')
        valor = valor.replace('"', '\\"')
        valor = valor.replace('\n', '\\n')
        valor = valor.replace('\r', '\\r')
        
        return valor
    
    @staticmethod
    def sanitizar_diccionario(datos: Dict[str, Any],
                             sanitizadores: Dict[str, callable] = None) -> Dict[str, Any]:
        """Sanitiza diccionario completo."""
        
        resultado = {}
        
        for clave, valor in datos.items():
            # Sanitizar clave
            clave_limpia = SanitizadorDatos.sanitizar_string(str(clave))
            
            # Sanitizar valor si es string
            if isinstance(valor, str):
                # Usar sanitizador específico si existe
                if sanitizadores and clave in sanitizadores:
                    valor_limpio = sanitizadores[clave](valor)
                else:
                    valor_limpio = SanitizadorDatos.sanitizar_string(valor)
            elif isinstance(valor, dict):
                valor_limpio = SanitizadorDatos.sanitizar_diccionario(valor)
            elif isinstance(valor, list):
                valor_limpio = [
                    SanitizadorDatos.sanitizar_string(str(item))
                    if isinstance(item, str) else item
                    for item in valor
                ]
            else:
                valor_limpio = valor
            
            resultado[clave_limpia] = valor_limpio
        
        return resultado


class ValidadorAlertas:
    """Validador especializado para alertas."""
    
    @staticmethod
    def crear_esquema_alerta() -> EsquemaValidacion:
        """Crea esquema de validación para alertas."""
        
        esquema = EsquemaValidacion("Alerta")
        
        esquema.agregar_campo(CampoValidacion(
            "tipo_alerta",
            TipoValidacion.ENUM,
            opciones={'valores': ['CRITICA', 'ADVERTENCIA', 'INFORMACION']}
        ))
        
        esquema.agregar_campo(CampoValidacion(
            "sensor_id",
            TipoValidacion.STRING,
            opciones={'max_len': 50}
        ))
        
        esquema.agregar_campo(CampoValidacion(
            "valor",
            TipoValidacion.NUMERO,
            opciones={'min': -50, 'max': 150}
        ))
        
        esquema.agregar_campo(CampoValidacion(
            "timestamp",
            TipoValidacion.FECHA
        ))
        
        esquema.agregar_campo(CampoValidacion(
            "descripcion",
            TipoValidacion.STRING,
            requerido=False,
            opciones={'max_len': 500}
        ))
        
        return esquema


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_esquemas_cache: Dict[str, EsquemaValidacion] = {}


def obtener_esquema_alerta() -> EsquemaValidacion:
    """Obtiene esquema de alerta (cached)."""
    if 'alerta' not in _esquemas_cache:
        _esquemas_cache['alerta'] = ValidadorAlertas.crear_esquema_alerta()
    
    return _esquemas_cache['alerta']


def iniciar_validadores() -> Dict[str, Any]:
    """Inicializa sistema de validación."""
    try:
        # Pre-cargar esquemas
        esquema_alerta = obtener_esquema_alerta()
        
        contexto = {
            'estado': 'ACTIVO',
            'esquemas_precargados': 1,
            'sanitizadores_activos': True,
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info("[VALIDATOR] Sistema de validación iniciado")
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando validadores: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
