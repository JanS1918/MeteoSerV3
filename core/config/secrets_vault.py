"""
Gestor centralizado de API Keys con cifrado
Almacena todas las claves de forma segura y las proporciona a todos los componentes
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Añadir el directorio raíz al path para importar meteoser_ia
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from meteoser_ia.block_e import SECRETS_MANAGER
    from cryptography.fernet import Fernet
    _HAS_CRYPTO = True
except ImportError:
    SECRETS_MANAGER = None
    Fernet = None
    _HAS_CRYPTO = False

logger = logging.getLogger("meteoser.secrets_vault")

class SecretsVault:
    """Gestor centralizado de claves API cifradas"""
    
    def __init__(self):
        self._initialized = False
        self._fallback_to_env = True
        
    def initialize(self) -> bool:
        """Inicializa el gestor de secretos con la clave maestra"""
        if self._initialized:
            return True
            
        if not _HAS_CRYPTO or SECRETS_MANAGER is None:
            logger.warning("cryptography no disponible. Las claves se leerán solo de variables de entorno.")
            return False
            
        # Intentar cargar la clave maestra desde variable de entorno
        if SECRETS_MANAGER.load_master_key_from_env("METEOSER_MASTER_KEY"):
            try:
                SECRETS_MANAGER.load_from_disk()
                self._initialized = True
                logger.info("✓ Secretos cargados desde almacén cifrado")
                return True
            except Exception as e:
                logger.warning(f"No se pudo cargar secretos desde disco: {e}")
                # Continuar para permitir crear nuevos secretos
                self._initialized = True
                return True
        else:
            # Generar clave maestra temporal si no existe
            logger.info("Generando clave maestra temporal (se perderá al reiniciar)")
            master_key = Fernet.generate_key()
            SECRETS_MANAGER.set_master_key(master_key)
            self._initialized = True
            return True
    
    def get_api_key(self, key_name: str, env_var: Optional[str] = None) -> Optional[str]:
        """
        Obtiene una API key del almacén cifrado o de variables de entorno
        
        Args:
            key_name: Nombre de la clave en el almacén cifrado
            env_var: Nombre de la variable de entorno (fallback)
        
        Returns:
            La clave API o None si no se encuentra
        """
        # Primero intentar desde el almacén cifrado
        if self._initialized and SECRETS_MANAGER:
            secret = SECRETS_MANAGER.get_secret(key_name)
            if secret and secret.strip():
                return secret.strip()
        
        # Fallback a variable de entorno
        if self._fallback_to_env and env_var:
            env_value = os.getenv(env_var, "").strip()
            if env_value:
                return env_value
        
        return None
    
    def set_api_key(self, key_name: str, value: str) -> bool:
        """
        Almacena una API key de forma cifrada
        
        Args:
            key_name: Nombre de la clave
            value: Valor de la clave
        
        Returns:
            True si se almacenó correctamente
        """
        if not self._initialized:
            self.initialize()
        
        if not SECRETS_MANAGER:
            logger.error("SecretsManager no disponible")
            return False
        
        try:
            SECRETS_MANAGER.set_secret(key_name, value)
            logger.info(f"✓ Clave '{key_name}' almacenada de forma segura")
            return True
        except Exception as e:
            logger.error(f"Error al guardar clave '{key_name}': {e}")
            return False
    
    def delete_api_key(self, key_name: str) -> bool:
        """Elimina una API key del almacén cifrado"""
        if not self._initialized or not SECRETS_MANAGER:
            return False
        
        try:
            return SECRETS_MANAGER.delete_secret(key_name)
        except Exception as e:
            logger.error(f"Error al eliminar clave '{key_name}': {e}")
            return False
    
    # Métodos de conveniencia para claves específicas
    
    def get_openrouter_key(self) -> Optional[str]:
        """Obtiene la clave de OpenRouter"""
        return self.get_api_key("OPENROUTER_API_KEY", "OPENROUTER_API_KEY")
    
    def set_openrouter_key(self, value: str) -> bool:
        """Almacena la clave de OpenRouter"""
        return self.set_api_key("OPENROUTER_API_KEY", value)
    
    def get_srtm_key(self) -> Optional[str]:
        """Obtiene la clave de SRTM"""
        return self.get_api_key("METEOSER_SRTM_API_KEY", "METEOSER_SRTM_API_KEY")
    
    def set_srtm_key(self, value: str) -> bool:
        """Almacena la clave de SRTM"""
        return self.set_api_key("METEOSER_SRTM_API_KEY", value)
    
    def get_openweather_key(self) -> Optional[str]:
        """Obtiene la clave de OpenWeather"""
        return self.get_api_key("OPENWEATHER_API_KEY", "OPENWEATHER_API_KEY")
    
    def set_openweather_key(self, value: str) -> bool:
        """Almacena la clave de OpenWeather"""
        return self.set_api_key("OPENWEATHER_API_KEY", value)


# Instancia global única
_vault_instance: Optional[SecretsVault] = None

def get_vault() -> SecretsVault:
    """Obtiene la instancia global del vault de secretos"""
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = SecretsVault()
        _vault_instance.initialize()
    return _vault_instance
