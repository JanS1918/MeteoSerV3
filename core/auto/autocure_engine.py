"""
Módulo de autocuración, autoexpansión y automejora para MeteoSer
Utiliza IA externa gratuita (HuggingFace, OpenRouter, etc) para analizar y corregir código, JS, configuración y sugerir mejoras.
Se activa automáticamente ante errores, fallos o eventos de mejora.
"""
import json
import requests
import traceback
import os
from datetime import datetime

# Proveedores IA gratuitos (puedes añadir más)
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/bigcode/starcoder"
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "")  # Puedes poner tu key gratuita aquí
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
import os
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")  # Migrado a variable de entorno

class AutoCureEngine:
    def __init__(self):
        self.providers = [self.huggingface_code_fix, self.openrouter_code_fix]

    def autocure(self, error_text, code_snippet=None, language="python", context=None):
        """Intenta autocorregir el error usando todos los proveedores disponibles."""
        for provider in self.providers:
            try:
                suggestion = provider(error_text, code_snippet, language, context)
                if suggestion:
                    return suggestion
            except Exception:
                continue
        return None

    def huggingface_code_fix(self, error_text, code_snippet, language, context):
        if not HUGGINGFACE_API_KEY:
            return None
        prompt = f"Corrige el siguiente error de {language}:\nError: {error_text}\nCódigo:\n{code_snippet or ''}\nContexto:\n{context or ''}\n" 
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        response = requests.post(HUGGINGFACE_API_URL, headers=headers, json={"inputs": prompt})
        if response.status_code == 200:
            return response.json().get("generated_text")
        return None

    def openrouter_code_fix(self, error_text, code_snippet, language, context):
        if not OPENROUTER_API_KEY:
            return None
        prompt = f"Corrige el siguiente error de {language}:\nError: {error_text}\nCódigo:\n{code_snippet or ''}\nContexto:\n{context or ''}\n" 
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get("choices", [{}])[0].get("message", {}).get("content")
        return None

    def _enqueue_suggestion(self, kind: str, suggestion_text: str) -> bool:
        """Guarda sugerencias en un archivo de cola para revisión/aplicación."""
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            queue_path = os.path.join(data_dir, "autocure_queue.json")

            item = {
                "kind": kind,
                "timestamp": datetime.utcnow().isoformat(),
                "suggestion": suggestion_text,
            }

            if os.path.exists(queue_path):
                with open(queue_path, "r", encoding="utf-8") as f:
                    queue = json.load(f)
            else:
                queue = []

            queue.append(item)
            with open(queue_path, "w", encoding="utf-8") as f:
                json.dump(queue, f, ensure_ascii=False, indent=2)
            return True
        except Exception as exc:
            print(f"Error guardando sugerencia de autocuración: {exc}")
            return False

    def autoexpand(self, suggestion_text):
        """Registra sugerencias de expansión para aplicación posterior."""
        return self._enqueue_suggestion("autoexpand", suggestion_text)

    def automejora(self, suggestion_text):
        """Registra sugerencias de mejora para aplicación posterior."""
        return self._enqueue_suggestion("automejora", suggestion_text)

    def handle_error(self, error, code_snippet=None, language="python", context=None):
        error_text = str(error)
        tb = traceback.format_exc()
        suggestion = self.autocure(error_text + "\n" + tb, code_snippet, language, context)
        if suggestion:
            # Aquí puedes aplicar el parche automáticamente si es seguro
            print("Sugerencia de autocuración:", suggestion)
        else:
            print("No se pudo autocurar el error automáticamente.")

# Ejemplo de uso:
# engine = AutoCureEngine()
# engine.handle_error(Exception("SyntaxError: unexpected EOF while parsing"), code_snippet="def foo():\n    print('hola'", language="python")
