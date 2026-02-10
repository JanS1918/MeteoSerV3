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

logger = logging.getLogger(__name__)


class CodeGenerator:
    """Generador de código asistido por LLM externo"""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openrouter"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.provider = provider
        self.model = "openai/gpt-3.5-turbo"  # Modelo por defecto
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        self.templates_dir = Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        self.generation_history: List[Dict] = []
        
        logger.info(f"🤖 CodeGenerator inicializado (provider={provider})")
    
    def generate_code(self, prompt: str, language: str = "python",
                     context: Optional[Dict] = None, use_llm: bool = True) -> Tuple[Optional[str], Optional[str]]:
        """
        Genera código desde un prompt.
        
        Returns:
            (code, error): Código generado o None si falla, mensaje de error si hay
        """
        if use_llm and self.api_key:
            return self._generate_with_llm(prompt, language, context)
        else:
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

import logging

logger = logging.getLogger(__name__)

class GeneratedDriver:
    """Driver generado"""
    
    def __init__(self, config):
        self.config = config
        logger.info("Driver inicializado")
    
    def read(self):
        """Lee datos"""
        # TODO: Implementar
        return {"valid": True}
    
    def close(self):
        """Cierra driver"""
        logger.info("Driver cerrado")
'''
            return code, None
        
        # Template genérico
        code = '''"""
Código generado automáticamente
"""

import logging

logger = logging.getLogger(__name__)

# TODO: Implementar funcionalidad
'''
        return code, None
    
    def _extract_code_from_markdown(self, text: str) -> str:
        """Extrae código de bloques markdown```"""
        # Buscar bloques de código
        pattern = r'```(?:python)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Si no hay bloques, retornar todo
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
            Path(output_path).write_text(code, encoding="utf-8")
            logger.info(f"💾 Código guardado en: {output_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando código: {e}")
            return False
    
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
