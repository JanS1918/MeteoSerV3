"""
Configura variables de entorno LLM desde .env o variables del sistema.
No imprime claves, solo valida presencia.
"""
from __future__ import annotations

import os

from pathlib import Path

try:
    from core.config.secrets_vault import get_vault
    _HAS_VAULT = True
except ImportError:
    get_vault = None
    _HAS_VAULT = False


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"

    _load_env_file(env_path)


    vault = get_vault() if _HAS_VAULT else None
    provider = os.getenv("METEOSER_LLM_PROVIDER")
    groq_key = (vault.get_api_key("GROQ_API_KEY", "GROQ_API_KEY") if vault else None) or os.getenv("GROQ_API_KEY")
    openrouter_key = (vault.get_openrouter_key() if vault else None) or os.getenv("OPENROUTER_API_KEY")

    if not provider:
        if groq_key:
            provider = "groq"
            os.environ["METEOSER_LLM_PROVIDER"] = provider
        elif openrouter_key:
            provider = "openrouter"
            os.environ["METEOSER_LLM_PROVIDER"] = provider

    print("LLM provider:", provider or "(sin configurar)")
    print("GROQ_API_KEY:", "OK" if groq_key else "MISSING")
    print("OPENROUTER_API_KEY:", "OK" if openrouter_key else "MISSING")


if __name__ == "__main__":
    main()
