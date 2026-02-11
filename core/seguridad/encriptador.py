"""
═══════════════════════════════════════════════════════════════════════════════
STEP 30: ENCRIPTACIÓN DE DATOS SENSIBLES
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Encriptar datos en reposo
  - Encriptar datos en tránsito (TLS)
  - Gestión segura de secretos
  - Cumplimiento GDPR/HIPAA

Fecha: 2026-02-11
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64

logger = logging.getLogger(__name__)


class GestorEncriptacion:
    """Gestor de encriptación de datos sensibles."""
    
    def __init__(self):
        self.clave_maestra = self._obtener_clave_maestra()
        self.cipher = Fernet(self.clave_maestra) if self.clave_maestra else None
        self.datos_encriptados: Dict[str, str] = {}
    
    def _obtener_clave_maestra(self) -> Optional[bytes]:
        """Obtiene clave maestra del entorno."""
        
        try:
            # Intenta obtener clave predefinida
            clave_env = os.getenv('ENCRYPTION_KEY')
            
            if clave_env:
                return base64.urlsafe_b64encode(
                    clave_env.encode()[:32].ljust(32, b'0')
                )
            
            # Generar clave desde contraseña maestra
            contraseña_maestra = os.getenv(
                'MASTER_PASSWORD',
                'default-insecure-password'
            )
            
            clave = self._derivar_clave_pbkdf2(contraseña_maestra)
            
            logger.warning(
                "[SECURITY] Usando clave derivada de contraseña, "
                "configura ENCRYPTION_KEY en producción"
            )
            
            return clave
        
        except Exception as e:
            logger.error(f"Error obteniendo clave maestra: {e}")
            return None
    
    def _derivar_clave_pbkdf2(self, contraseña: str) -> bytes:
        """Deriva clave usando PBKDF2."""
        
        salt = os.getenv('ENCRYPTION_SALT', 'default-salt').encode()
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        clave_derivada = base64.urlsafe_b64encode(
            kdf.derive(contraseña.encode())
        )
        
        return clave_derivada
    
    def encriptar_datos(self, datos: str) -> str:
        """Encripta datos sensibles."""
        
        if not self.cipher:
            logger.warning(
                "[SECURITY] Encriptación no disponible, "
                "datos sin proteger"
            )
            return datos
        
        try:
            datos_bytes = datos.encode('utf-8')
            datos_encriptados = self.cipher.encrypt(datos_bytes)
            
            # Convertir a string para almacenamiento
            resultado = base64.urlsafe_b64encode(
                datos_encriptados
            ).decode('utf-8')
            
            return resultado
        
        except Exception as e:
            logger.error(f"Error encriptando datos: {e}")
            return datos
    
    def desencriptar_datos(self, datos_encriptados: str) -> str:
        """Desencripta datos sensibles."""
        
        if not self.cipher:
            logger.warning("[SECURITY] Encriptación no disponible")
            return datos_encriptados
        
        try:
            # Decodificar desde almacenamiento
            datos_bytes = base64.urlsafe_b64decode(
                datos_encriptados.encode('utf-8')
            )
            
            datos_desencriptados = self.cipher.decrypt(datos_bytes)
            
            return datos_desencriptados.decode('utf-8')
        
        except Exception as e:
            logger.error(f"Error desencriptando datos: {e}")
            return ""
    
    def almacenar_secreto(self, nombre: str, valor: str) -> bool:
        """Almacena secreto encriptado."""
        
        try:
            encriptado = self.encriptar_datos(valor)
            self.datos_encriptados[nombre] = encriptado
            
            logger.info(f"[SECURITY] Secreto '{nombre}' almacenado")
            
            return True
        
        except Exception as e:
            logger.error(f"Error almacenando secreto: {e}")
            return False
    
    def recuperar_secreto(self, nombre: str) -> Optional[str]:
        """Recupera secreto desencriptado."""
        
        try:
            encriptado = self.datos_encriptados.get(nombre)
            
            if not encriptado:
                logger.warning(f"[SECURITY] Secreto '{nombre}' no encontrado")
                return None
            
            desencriptado = self.desencriptar_datos(encriptado)
            
            return desencriptado
        
        except Exception as e:
            logger.error(f"Error recuperando secreto: {e}")
            return None
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas de encriptación."""
        
        return {
            'encriptacion_activa': self.cipher is not None,
            'secretos_almacenados': len(self.datos_encriptados),
            'secretos': list(self.datos_encriptados.keys()),
            'timestamp': datetime.now().isoformat()
        }


class GestorSecretos:
    """Gestor centralizado de secretos."""
    
    def __init__(self):
        self.secretos: Dict[str, str] = {}
        self.encriptador = GestorEncriptacion()
        self._cargar_secretos_fromchenv()
    
    def _cargar_secretos_fromchenv(self):
        """Carga secretos desde variables de entorno."""
        
        secretos_env = [
            'DATABASE_URL',
            'REDIS_PASSWORD',
            'API_KEY_TELEGRAM',
            'API_KEY_DISCORD',
            'API_KEY_SLACK',
            'JWT_SECRET',
            'WEBHOOK_SECRET'
        ]
        
        for clave in secretos_env:
            valor = os.getenv(clave)
            if valor:
                self.almacenar_secreto(clave, valor)
        
        logger.info(
            f"[SECURITY] {len(self.secretos)} secretos cargados "
            f"del entorno"
        )
    
    def almacenar_secreto(self, nombre: str, valor: str) -> bool:
        """Almacena secreto de forma segura."""
        
        if self.encriptador.almacenar_secreto(nombre, valor):
            self.secretos[nombre] = "ENCRIPTADO"
            logger.info(f"[SECURITY] Secreto '{nombre}' guardado")
            return True
        
        return False
    
    def obtener_secreto(self, nombre: str) -> Optional[str]:
        """Obtiene secreto desencriptado."""
        
        return self.encriptador.recuperar_secreto(nombre)
    
    def secreto_existe(self, nombre: str) -> bool:
        """Verifica si secreto existe."""
        
        return nombre in self.datos_encriptados
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas."""
        
        return {
            'estado': 'ACTIVO',
            'secretos_total': len(self.secretos),
            'encriptacion': self.encriptador.obtener_estadisticas(),
            'timestamp': datetime.now().isoformat()
        }


class ValidadorSeguridad:
    """Valida requisitos de seguridad."""
    
    @staticmethod
    def verificar_https_requerido() -> bool:
        """Verifica si HTTPS es requerido."""
        
        return os.getenv('REQUIRE_HTTPS', 'true').lower() == 'true'
    
    @staticmethod
    def verificar_tls_version() -> str:
        """Obtiene versión mínima de TLS."""
        
        return os.getenv('TLS_MIN_VERSION', 'TLSv1.2')
    
    @staticmethod
    def obtener_headers_seguridad() -> Dict[str, str]:
        """Obtiene headers de seguridad recomendados."""
        
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }


# ═══════════════════════════════════════════════════════════════════════════
# INICIALIZADORES
# ═══════════════════════════════════════════════════════════════════════════

_gestor_encriptacion_instance = None
_gestor_secretos_instance = None


def obtener_gestor_encriptacion() -> GestorEncriptacion:
    """Obtiene instancia singleton."""
    global _gestor_encriptacion_instance
    if _gestor_encriptacion_instance is None:
        _gestor_encriptacion_instance = GestorEncriptacion()
    
    return _gestor_encriptacion_instance


def obtener_gestor_secretos() -> GestorSecretos:
    """Obtiene instancia singleton."""
    global _gestor_secretos_instance
    if _gestor_secretos_instance is None:
        _gestor_secretos_instance = GestorSecretos()
    
    return _gestor_secretos_instance


def iniciar_encriptacion_y_secretos() -> Dict[str, Any]:
    """Inicializa encriptación y gestión de secretos."""
    try:
        encriptador = obtener_gestor_encriptacion()
        gestor_secretos = obtener_gestor_secretos()
        
        contexto = {
            'estado': 'ACTIVO',
            'encriptacion': {
                'activa': encriptador.cipher is not None,
                'tipo': 'Fernet (AES-128)',
                'derivacion_clave': 'PBKDF2'
            },
            'secretos': {
                'total_cargados': len(gestor_secretos.secretos),
                'fuentes': 'Variables de entorno'
            },
            'headers_seguridad': {
                'https_requerido': ValidadorSeguridad.verificar_https_requerido(),
                'tls_version': ValidadorSeguridad.verificar_tls_version()
            },
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            "[SECURITY] Encriptación y gestión de secretos iniciadas"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando encriptación: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
