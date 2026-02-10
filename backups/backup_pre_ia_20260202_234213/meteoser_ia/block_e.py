from __future__ import annotations

import json
import logging
import os
import stat
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
    _HAS_CRYPTO = True
except Exception:
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore
    _HAS_CRYPTO = False

from . import block_a

logger = logging.getLogger("meteoser_ia.block_e")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [BLOQUE E] [%(levelname)s] %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

EXTERNAL_INTEGRATION_MODE = block_a.EXTERNAL_INTEGRATION_MODE

BASE_DIR = os.path.join(os.path.dirname(__file__), "ia_security")
os.makedirs(BASE_DIR, exist_ok=True)

SECRETS_FILE = os.path.join(BASE_DIR, "secrets.enc")
SECRETS_META = os.path.join(BASE_DIR, "secrets.meta.json")

def _secure_file_write(path: str, data: bytes, mode: int = 0o600) -> None:
    tmp = f"{path}.{int(time.time()*1000)}.tmp"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        os.chmod(path, mode)
    except Exception:
        logger.warning("No se pudo fijar permisos en el fichero, comprobar manualmente.")

def _secure_file_read(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def sanitize_string(s: str) -> str:
    return s.replace("\n", " ").replace("\r", " ").strip()

def validate_config_schema(cfg: Dict[str, Any], schema: Dict[str, type]) -> bool:
    for k, t in schema.items():
        if k not in cfg:
            logger.error(f"Configuración inválida: falta clave {k}")
            return False
        if not isinstance(cfg[k], t):
            logger.error(f"Configuración inválida: clave {k} debe ser {t}, es {type(cfg[k])}")
            return False
    return True

@dataclass
class SecretsMetadata:
    created_at: float = field(default_factory=time.time)
    versions: int = 0

class SecretsManager:
    def __init__(self, secrets_file: str = SECRETS_FILE, meta_file: str = SECRETS_META) -> None:
        self.secrets_file = secrets_file
        self.meta_file = meta_file
        self._secrets: Dict[str, str] = {}
        self._meta = SecretsMetadata()
        self._fernet: Optional[Fernet] = None
        self._master_key: Optional[bytes] = None

    def load_master_key_from_env(self, env_var: str = "METEOSER_MASTER_KEY") -> bool:
        key = os.environ.get(env_var)
        if not key:
            logger.info("Clave maestra no encontrada en variables de entorno.")
            return False
        try:
            self.set_master_key(key.encode("utf-8"))
            return True
        except Exception as e:
            logger.error(f"Error al establecer clave maestra desde env: {e}")
            return False

    def set_master_key(self, key_bytes: bytes) -> None:
        if not _HAS_CRYPTO:
            raise RuntimeError("cryptography no disponible. Instala 'cryptography' para usar SecretsManager.")
        try:
            self._fernet = Fernet(key_bytes)
            self._master_key = key_bytes
            logger.info("Clave maestra establecida en memoria.")
        except Exception as e:
            raise ValueError(f"Clave maestra inválida: {e}")

    def _ensure_fernet(self) -> None:
        if not self._fernet:
            raise RuntimeError("Clave maestra no establecida. Usa set_master_key o load_master_key_from_env.")

    def load_from_disk(self) -> None:
        if not _HAS_CRYPTO:
            raise RuntimeError("cryptography no disponible; no se puede cargar secretos desde disco.")
        if not os.path.exists(self.secrets_file):
            logger.info("Fichero de secretos no encontrado en disco.")
            return
        self._ensure_fernet()
        enc = _secure_file_read(self.secrets_file)
        try:
            raw = self._fernet.decrypt(enc)
            data = json.loads(raw.decode("utf-8"))
            self._secrets = data.get("secrets", {})
            meta = data.get("meta", {})
            self._meta = SecretsMetadata(created_at=meta.get("created_at", time.time()), versions=meta.get("versions", 0))
            logger.info("Secretos cargados y descifrados desde disco.")
        except InvalidToken:
            raise RuntimeError("Clave maestra incorrecta o fichero de secretos corrupto.")
        except Exception as e:
            raise RuntimeError(f"Error al cargar secretos: {e}")

    def persist_to_disk(self) -> None:
        if EXTERNAL_INTEGRATION_MODE == block_a.ExternalIntegrationMode.MOCK:
            logger.info("Modo MOCK: no se persisten secretos en disco por seguridad.")
            return
        if not _HAS_CRYPTO:
            raise RuntimeError("cryptography no disponible; no se puede persistir secretos de forma segura.")
        self._ensure_fernet()
        payload = {"secrets": self._secrets, "meta": {"created_at": self._meta.created_at, "versions": self._meta.versions}}
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        enc = self._fernet.encrypt(raw)
        _secure_file_write(self.secrets_file, enc)
        logger.info("Secretos cifrados y persistidos en disco.")

    def set_secret(self, key: str, value: str) -> None:
        key = sanitize_string(key)
        self._secrets[key] = value
        self._meta.versions += 1
        logger.info(f"Se ha almacenado un secreto (clave={key}) en memoria. No se muestra su valor.")
        try:
            self.persist_to_disk()
        except Exception as e:
            logger.warning(f"No se pudo persistir secreto en disco: {e}")

    def get_secret(self, key: str) -> Optional[str]:
        key = sanitize_string(key)
        return self._secrets.get(key)

    def delete_secret(self, key: str) -> bool:
        key = sanitize_string(key)
        if key in self._secrets:
            del self._secrets[key]
            self._meta.versions += 1
            try:
                self.persist_to_disk()
            except Exception:
                pass
            logger.info(f"Se ha eliminado el secreto (clave={key}) de memoria.")
            return True
        return False

    def rotate_master_key(self, new_key_bytes: bytes) -> None:
        if not _HAS_CRYPTO:
            raise RuntimeError("cryptography no disponible; no se puede rotar clave maestra.")
        self._ensure_fernet()
        new_fernet = Fernet(new_key_bytes)
        self._fernet = new_fernet
        self._master_key = new_key_bytes
        try:
            self.persist_to_disk()
            logger.info("Rotación de clave maestra completada y secretos re-cifrados.")
        except Exception as e:
            logger.error(f"Error al persistir tras rotación de clave: {e}")
            raise

SECRETS_MANAGER = SecretsManager()

HARDENING_RECOMMENDATIONS = {
    "secrets": [
        "No almacenar claves en repositorios de código.",
        "Usar variables de entorno para la clave maestra y no persistirla en disco.",
        "Rotar claves periódicamente y auditar accesos.",
    ],
    "runtime": [
        "Ejecutar procesos con usuario no privilegiado.",
        "Limitar permisos de ficheros a 0o600 para secretos y 0o700 para directorios.",
        "Usar contenedores o sandboxes con límites de recursos en modo LIVE.",
    ],
    "network": [
        "Restringir salidas de red a los endpoints necesarios.",
        "Usar TLS y validación de certificados para todas las conexiones externas.",
    ],
}

def get_hardening_recommendations() -> Dict[str, Any]:
    return HARDENING_RECOMMENDATIONS

def smoke_test() -> None:
    logger.info("SMOKE TEST Bloque E: hardening y gestión de secretos (modo mock).")

    recs = get_hardening_recommendations()
    print("Recomendaciones de hardening (resumen):")
    for k, v in recs.items():
        print(f"- {k}:")
        for item in v:
            print(f"  * {item}")

    try:
        if _HAS_CRYPTO:
            key = Fernet.generate_key()
            SECRETS_MANAGER.set_master_key(key)
            SECRETS_MANAGER.set_secret("example_api_key", "S3CR3T-MOCK")
            val = SECRETS_MANAGER.get_secret("example_api_key")
            print("Secret example_api_key almacenado en memoria (no mostrado). Recuperado:", bool(val))
            SECRETS_MANAGER.delete_secret("example_api_key")
            print("Secret borrado:", True)
        else:
            print("cryptography no disponible; el gestor de secretos no persiste en este entorno.")
    except Exception as e:
        print("Error en smoke_test secrets:", e)

if __name__ == "__main__":
    smoke_test()