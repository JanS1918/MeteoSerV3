"""
MeteoSer AI Code Generator - Generador de Código con IA Externa
================================================================

Genera código Python usando LLM externo (OpenRouter, HuggingFace, etc.).
Valida sintaxis, ejecuta tests, y aplica templates.
"""

import ast
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests

try:
    from core.config.secrets_vault import get_vault
    _HAS_VAULT = True
except ImportError:
    _HAS_VAULT = False

logger = logging.getLogger(__name__)


class CodeGenerator:
    """Generador de código asistido por LLM externo"""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openrouter"):
        try:
            from core.config.env_loader import load_dotenv
            load_dotenv()
        except Exception:
            pass
        provider_env = os.getenv("METEOSER_LLM_PROVIDER")
        vault = get_vault() if _HAS_VAULT else None

        groq_key = ""
        openrouter_key = ""
        if not api_key:
            if vault:
                groq_key = vault.get_api_key("GROQ_API_KEY", "GROQ_API_KEY") or ""
                openrouter_key = vault.get_openrouter_key() or ""
            else:
                groq_key = os.environ.get("GROQ_API_KEY", "")
                openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

        if provider_env:
            self.provider = provider_env.lower()
        else:
            self.provider = ("groq" if groq_key else ("openrouter" if openrouter_key else (provider or "openrouter"))).lower()

        # Obtener API key del vault cifrado o variables de entorno según provider
        if api_key:
            self.api_key = api_key
        elif self.provider == "groq":
            self.api_key = groq_key
        else:
            self.api_key = openrouter_key

        if self.provider == "groq":
            self.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
            self.api_url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        else:
            self.model = "openai/gpt-3.5-turbo"  # Modelo por defecto
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"

        # Fallback: Llama local
        self.llama_local_url = os.environ.get("LLAMA_LOCAL_URL", "http://localhost:8081/v1/completions")
        self.llama_local_enabled = False
        if not self.api_key:
            # Intentar detectar Llama local
            try:
                resp = requests.get(self.llama_local_url, timeout=2)
                if resp.status_code == 200:
                    self.llama_local_enabled = True
                    self.provider = "llama-local"
                    logger.info("🤖 Llama local detectado, usando como fallback de IA.")
            except Exception:
                logger.warning("No se detectó Llama local. IA en modo local (template)")
                # Aquí podrías notificar por Telegram si está disponible
                try:
                    from core.integration.telegram_bot import send_telegram_message
                    send_telegram_message("⚠️ IA en modo local: sin API key ni Llama local. Solo templates.")
                except Exception as e:
                    logger.error(f"Error notificando por Telegram: {e}")

        self.templates_dir = Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)

        self.generation_history: List[Dict] = []

        logger.info(f"🤖 CodeGenerator inicializado (provider={self.provider})")
    
    def generate_code(self, prompt: str, language: str = "python",
                     context: Optional[Dict] = None, use_llm: bool = True) -> Tuple[Optional[str], Optional[str]]:
        """
        Genera código desde un prompt.
        
        Returns:
            (code, error): Código generado o None si falla, mensaje de error si hay
        """
        if use_llm:
            if self.api_key:
                return self._generate_with_llm(prompt, language, context)
            elif self.llama_local_enabled:
                return self._generate_with_llama_local(prompt, language, context)
        return self._generate_with_template(prompt, context)

    def _generate_with_llama_local(self, prompt: str, language: str, context: Optional[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """Genera código usando Llama local"""
        try:
            system_prompt = f"""Eres un experto en generar código {language} para el sistema MeteoSer.\nGenera código limpio, bien documentado, con manejo de errores y logging.\nResponde SOLO con el código, sin explicaciones adicionales."""
            if context:
                system_prompt += f"\n\nContexto adicional:\n{context}"
            user_prompt = f"Genera código {language} para: {prompt}"
            data = {
                "model": "llama-cpp-local",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
            }
            logger.info(f"🤖 Consultando Llama local para generar código: {prompt[:50]}...")
            response = requests.post(self.llama_local_url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                code = result["choices"][0]["message"]["content"]
                code = self._extract_code_from_markdown(code)
                self.generation_history.append({
                    "prompt": prompt,
                    "code": code,
                    "status": "success",
                    "provider": self.provider,
                })
                logger.info(f"✅ Código generado exitosamente (Llama local, {len(code)} chars)")
                return code, None
            else:
                error = f"Error Llama local: {response.status_code} {response.text}"
                logger.error(f"❌ {error}")
                return self._generate_with_template(prompt, context)
        except Exception as e:
            error = f"Excepción al generar código con Llama local: {e}"
            logger.error(f"❌ {error}")
            return self._generate_with_template(prompt, context)
    
    def _generate_with_llm(self, prompt: str, language: str,
                          context: Optional[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """Genera código usando LLM externo"""
        try:
            # Construir prompt completo
            system_prompt = f"""Eres un experto en generar código {language} para el sistema MeteoSer.
Genera código limpio, bien documentado, con manejo de errores y logging.
Responde SOLO con el código, sin explicaciones adicionales."""

            if context:
                system_prompt += f"\n\nContexto adicional:\n{context}"
            
            user_prompt = f"Genera código {language} para: {prompt}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,  # Más determinista
                "max_tokens": 2000,
            }
            
            logger.info(f"🤖 Consultando LLM para generar código: {prompt[:50]}...")
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                code = result["choices"][0]["message"]["content"]
                
                # Extraer código si viene con markdown
                code = self._extract_code_from_markdown(code)
                
                # Guardar en historial
                self.generation_history.append({
                    "prompt": prompt,
                    "code": code,
                    "status": "success",
                    "provider": self.provider,
                })
                
                logger.info(f"✅ Código generado exitosamente ({len(code)} chars)")
                return code, None
            else:
                error = f"Error LLM: {response.status_code} {response.text}"
                logger.error(f"❌ {error}")
                
                # Fallback a template
                logger.info("🔄 Fallback a template...")
                return self._generate_with_template(prompt, context)
                
        except Exception as e:
            error = f"Excepción al generar código: {e}"
            logger.error(f"❌ {error}")
            
            # Fallback a template
            return self._generate_with_template(prompt, context)
    
    def _generate_with_template(self, prompt: str,
                               context: Optional[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """Genera código usando templates locales (fallback)"""
        logger.info("📋 Generando código desde template...")
        
        # Template básico de driver
        if "driver" in prompt.lower():
            code = '''"""
Driver generado automáticamente
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class GeneratedDriver:
    """Driver generado"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("Driver inicializado")

    def _read_from_file(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            file_path = Path(path)
            if not file_path.exists():
                logger.error(f"Archivo no encontrado: {file_path}")
                return None
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Error leyendo archivo {path}: {e}")
            return None

    def _write_to_file(self, path: str, data: Dict[str, Any]) -> bool:
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Error escribiendo archivo {path}: {e}")
            return False

    def read(self) -> Optional[Dict[str, Any]]:
        """Lee datos"""
        path = self.config.get("data_file")
        if not path:
            logger.error("No hay data_file configurado")
            return None
        data = self._read_from_file(path)
        if data is None:
            return None
        data.setdefault("timestamp", datetime.utcnow().isoformat())
        data.setdefault("valid", True)
        return data

    def write(self, data: Dict[str, Any]) -> bool:
        """Escribe datos"""
        path = self.config.get("data_file")
        if not path:
            logger.error("No hay data_file configurado")
            return False
        payload = dict(data)
        payload.setdefault("timestamp", datetime.utcnow().isoformat())
        return self._write_to_file(path, payload)

    def close(self) -> None:
        """Cierra driver"""
        logger.info("Driver cerrado")
'''
            return code, None
        
        # Template genérico
        code = '''"""
Código generado automáticamente
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def run(payload: dict | None = None) -> dict:
    """Ejecuta una acción base y retorna un resultado."""
    logger.info("Ejecución base iniciada")
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "ok": True,
        "input": payload or {},
    }
'''
        return code, None
    
    def _extract_code_from_markdown(self, text: str) -> str:
        """Extrae código de bloques markdown```"""
        # Buscar bloques de código
        pattern = r'```(?:python)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Si no hay bloques, retornar todo (lógica real: lanzar excepción o devolver None)
        if not self.generation_history:
            logger.warning("No hay historial de generación para devolver código.")
            return None, "No hay código generado ni bloques disponibles."
        return text.strip()
    
    def validate_syntax(self, code: str, language: str = "python") -> Tuple[bool, Optional[str]]:
        """Valida sintaxis del código"""
        if language != "python":
            return True, None  # Solo soportamos Python por ahora
        
        try:
            ast.parse(code)
            logger.info("✅ Sintaxis válida")
            return True, None
        except SyntaxError as e:
            error = f"Error de sintaxis en línea {e.lineno}: {e.msg}"
            logger.error(f"❌ {error}")
            return False, error
    
    def run_tests(self, code_path: str, test_path: str) -> Tuple[bool, str]:
        """Ejecuta tests sobre el código generado"""
        try:
            # Ejecutar pytest
            result = subprocess.run(
                ["pytest", test_path, "-v"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            if success:
                logger.info(f"✅ Tests pasaron exitosamente")
            else:
                logger.error(f"❌ Tests fallaron:\n{output}")
            
            return success, output
            
        except Exception as e:
            error = f"Error ejecutando tests: {e}"
            logger.error(f"❌ {error}")
            return False, error
    
    def save_code(self, code: str, output_path: str) -> bool:
        """Guarda código generado a archivo"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(code, encoding="utf-8")
            logger.info(f"💾 Código guardado en: {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando código: {e}")
            return False

    def generate_and_save(self, prompt: str, output_path: str,
                          language: str = "python",
                          context: Optional[Dict] = None) -> Tuple[Optional[str], Optional[str]]:
        """Genera código y lo persiste en disco."""
        code, error = self.generate_code(prompt, language=language, context=context)
        if code is None:
            return None, error or "Error generando código"
        if not self.save_code(code, output_path):
            return None, f"No se pudo guardar código en {output_path}"
        self.generation_history.append({
            "prompt": prompt,
            "code": code,
            "status": "saved",
            "provider": self.provider,
            "output_path": str(output_path),
        })
        return code, None

    def generate_driver_assets(self, contract: Dict, output_dir: str,
                               tests_dir: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Genera driver y tests desde contrato y los escribe en disco."""
        contract_id = contract["id"]
        contract_name = contract["name"]
        driver_filename = f"{contract_id}_driver.py"
        test_filename = f"test_{contract_id}_driver.py"

        prompt_driver = (
            f"Genera un driver Python completo para un sensor llamado '{contract_name}'.\n"
            f"ID del contrato: {contract_id}\n"
            f"Tipo: {contract.get('type', 'sensor')}\n"
            f"Protocolo: {contract.get('protocol', 'I2C')}\n"
            "Incluye métodos: __init__, read(), write() (si aplica), close()."
        )
        code, error = self.generate_and_save(
            prompt_driver,
            str(Path(output_dir) / driver_filename),
            context={"contract": contract}
        )
        if code is None:
            return {"driver_path": None, "test_path": None, "error": error}

        tests_dir = tests_dir or output_dir
        prompt_test = (
            f"Genera tests unitarios con pytest para el driver {contract_id}.\n"
            f"Incluye tests de inicialización, lectura y cierre." 
        )
        _, test_error = self.generate_and_save(
            prompt_test,
            str(Path(tests_dir) / test_filename),
        )

        return {
            "driver_path": str(Path(output_dir) / driver_filename),
            "test_path": str(Path(tests_dir) / test_filename),
            "error": test_error,
        }
    
    def generate_driver_from_contract(self, contract: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Genera driver completo desde un contrato"""
        contract_id = contract["id"]
        contract_name = contract["name"]
        
        prompt = f"""Genera un driver Python completo para un sensor llamado '{contract_name}'.
ID del contrato: {contract_id}
Tipo: {contract.get('type', 'sensor')}
Protocolo: {contract.get('protocol', 'I2C')}

Campos a leer:
"""
        
        if "fields" in contract:
            for field in contract["fields"]:
                prompt += f"\n- {field['name']}: {field.get('unit', 'valor')}"
        
        prompt += "\n\nIncluye métodos: __init__, read(), write() (si aplica), close()"
        prompt += "\nUsa logging para debug y manejo de errores con try/except"
        
        return self.generate_code(prompt, context={"contract": contract})
    
    def generate_test_from_driver(self, driver_code: str, contract_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Genera tests para un driver"""
        prompt = f"""Genera tests unitarios con pytest para este driver (ID: {contract_id}):

```python
{driver_code}
```

Incluye tests para:
- Inicialización
- Lectura de datos
- Manejo de errores
- Cierre del driver
"""
        
        return self.generate_code(prompt)
    
    def fix_code(self, code: str, error: str) -> Tuple[Optional[str], Optional[str]]:
        """Intenta corregir código con errores"""
        prompt = f"""Corrige este código Python que tiene el siguiente error:

Error: {error}

Código:
```python
{code}
```

Retorna el código corregido.
"""
        
        return self.generate_code(prompt)
    
    def get_status(self) -> Dict:
        """Retorna estado del generador"""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_configured": bool(self.api_key),
            "generations_count": len(self.generation_history),
            "templates_dir": str(self.templates_dir),
        }
