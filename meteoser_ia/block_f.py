from __future__ import annotations

import logging
import requests
import os
import tempfile
from pathlib import Path
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pyttsx3
import requests

from . import block_a
from . import block_b
from . import block_c

# Configuración de clave OpenRouter (puede venir de autocure_engine o variable de entorno)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

try:
    import sys
    from pathlib import Path
    # Añadir el directorio raíz al path para importar core
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from core.config.secrets_vault import get_vault
    _HAS_VAULT = True
except ImportError:
    _HAS_VAULT = False

# Configuración de clave OpenRouter - usar vault cifrado
if _HAS_VAULT:
    try:
        _vault = get_vault()
        OPENROUTER_API_KEY = _vault.get_openrouter_key() or ""
    except:
        OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
else:
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

logger = logging.getLogger("meteoser_ia.block_f")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        "[%(asctime)s] [BLOQUE F] [%(levelname)s] %(message)s"
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)

EXTERNAL_INTEGRATION_MODE = block_a.EXTERNAL_INTEGRATION_MODE

TTS_VOICE = "es-ES-Standard-A"
STT_LANGUAGE = "es-ES"

_TTS_ENGINE: Optional[pyttsx3.Engine] = None


def _get_tts_engine() -> pyttsx3.Engine:
    global _TTS_ENGINE
    if _TTS_ENGINE is None:
        engine = pyttsx3.init()
        try:
            engine.setProperty("rate", 175)
            engine.setProperty("volume", 1.0)
        except Exception:
            logging.exception("Silent except at 51 - revisar contexto")
        try:
            voices = engine.getProperty("voices") or []
            selected = None
            for v in voices:
                name = f"{getattr(v, 'name', '')} {getattr(v, 'id', '')}".lower()
                if "es" in name or "spanish" in name or "españ" in name:
                    selected = v.id
                    break
            if selected:
                engine.setProperty("voice", selected)
        except Exception:
            logging.exception("Silent except at 63 - revisar contexto")
        _TTS_ENGINE = engine
    return _TTS_ENGINE


@dataclass
class ConversationContext:
    session_id: str
    user_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    slots: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, ConversationContext] = {}

    def create_session(self, user_id: Optional[str] = None) -> ConversationContext:
        sid = f"ses_{uuid.uuid4().hex[:8]}"
        ctx = ConversationContext(session_id=sid, user_id=user_id)
        self._sessions[sid] = ctx
        logger.info(f"Sesión creada: {sid} user={user_id}")
        return ctx

    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        return self._sessions.get(session_id)

    def touch(self, session_id: str) -> None:
        s = self.get_session(session_id)
        if s:
            s.last_active = time.time()

    def list_sessions(self) -> List[ConversationContext]:
        return list(self._sessions.values())

    def delete_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Sesión eliminada: {session_id}")


SESSION_STORE = SessionStore()


def _simple_intent_classifier(text: str) -> Dict[str, Any]:
    t = text.lower().strip()
    if any(w in t for w in ["buenos días", "buenos dias", "hola"]):
        return {"intent": "greeting", "confidence": 0.9, "entities": {}}
    if any(w in t for w in ["qué me pongo", "que me pongo", "ropa", "vestir"]):
        return {"intent": "ask_clothing", "confidence": 0.9, "entities": {}}
    if any(w in t for w in ["estado", "sensores", "lecturas", "temperatura"]):
        return {"intent": "ask_status", "confidence": 0.85, "entities": {}}
    if any(w in t for w in ["desplegar", "deploy", "activar algoritmo", "activar"]):
        return {"intent": "deploy_algorithm", "confidence": 0.8, "entities": {}}
    if any(w in t for w in ["gracias", "ok", "vale"]):
        return {"intent": "ack", "confidence": 0.9, "entities": {}}
    return {"intent": "fallback", "confidence": 0.5, "entities": {}}


@dataclass
class DialogResponse:
    text: str
    tts: Optional[bytes] = None
    end_session: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class DialogManager:
    def __init__(self) -> None:
        self._intent_handlers: Dict[
            str, Callable[[ConversationContext, Dict[str, Any]], DialogResponse]
        ] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        self.register_intent_handler("greeting", self._handle_greeting)
        self.register_intent_handler("ask_clothing", self._handle_ask_clothing)
        self.register_intent_handler("ask_status", self._handle_ask_status)
        self.register_intent_handler("deploy_algorithm", self._handle_deploy_algorithm)
        self.register_intent_handler("ack", self._handle_ack)
        self.register_intent_handler("fallback", self._handle_fallback)

    def register_intent_handler(
        self,
        intent: str,
        handler: Callable[[ConversationContext, Dict[str, Any]], DialogResponse],
    ) -> None:
        self._intent_handlers[intent] = handler

    def handle_text(self, session_id: str, text: str) -> DialogResponse:
        ctx = SESSION_STORE.get_session(session_id)
        if not ctx:
            ctx = SESSION_STORE.create_session()
        SESSION_STORE.touch(session_id)
        nlu = _simple_intent_classifier(text)
        intent = nlu["intent"]
        handler = self._intent_handlers.get(intent, self._handle_fallback)
        logger.info(
            f"NLU detected intent={intent} conf={nlu['confidence']:.2f} for session={session_id}"
        )
        resp = handler(ctx, nlu)
        ctx.history.append(
            {"user": text, "nlu": nlu, "response": resp.text, "ts": time.time()}
        )
        return resp

    def _handle_greeting(
        self, ctx: ConversationContext, nlu: Dict[str, Any]
    ) -> DialogResponse:
        text = "Hola. ¿En qué puedo ayudarte hoy?"
        return DialogResponse(text=text)

    def _handle_ask_clothing(
        self, ctx: ConversationContext, nlu: Dict[str, Any]
    ) -> DialogResponse:
        logger.info("Handler: pedir recomendación de ropa al Bloque B")
        block_b.action_recommend_clothing()
        text = "He generado una recomendación de ropa basada en los datos disponibles. ¿Quieres que te la lea?"
        return DialogResponse(text=text)

    def _handle_ask_status(
        self, ctx: ConversationContext, nlu: Dict[str, Any]
    ) -> DialogResponse:
        snapshot = block_a.SENSOR_REGISTRY.snapshot()
        sensors = snapshot.sensors
        if not sensors:
            return DialogResponse(
                text="No detecto sensores registrados en este momento."
            )
        summary_lines = []
        for sid in list(sensors.keys())[:3]:
            r = block_a.read_sensor(sid)
            if r and r.valid:
                summary_lines.append(f"{sensors[sid].name}: {r.values}")
            else:
                summary_lines.append(
                    f"{sensors[sid].name}: lectura inválida o no disponible"
                )
        text = "Resumen de sensores: " + " | ".join(summary_lines)
        return DialogResponse(text=text)

    def _handle_deploy_algorithm(
        self, ctx: ConversationContext, nlu: Dict[str, Any]
    ) -> DialogResponse:
        ctx.slots["pending_deploy"] = True
        text = "He preparado el despliegue del algoritmo. Confirma con 'sí, desplegar' para continuar."
        return DialogResponse(text=text)

    def _handle_ack(
        self, ctx: ConversationContext, nlu: Dict[str, Any]
    ) -> DialogResponse:
        if ctx.slots.get("pending_deploy"):
            versions = block_c.ALGO_REPO.list_versions()
            if not versions:
                return DialogResponse(
                    text="No hay ninguna versión de algoritmo lista para desplegar."
                )
            latest = sorted(versions, key=lambda v: v.timestamp)[-1]
            ok = block_c.deploy_algorithm(latest.id)
            if ok:
                ctx.slots.pop("pending_deploy", None)
                return DialogResponse(
                    text=f"Versión {latest.id} marcada como desplegada (acción lógica)."
                )
            else:
                return DialogResponse(
                    text="No se pudo marcar la versión como desplegada."
                )
        return DialogResponse(text="Perfecto.")

    def _handle_fallback(
        self, ctx: ConversationContext, nlu: Dict[str, Any]
    ) -> DialogResponse:
        if EXTERNAL_INTEGRATION_MODE == block_a.ExternalIntegrationMode.MOCK:
            return DialogResponse(
                text="Lo siento, no he entendido. ¿Puedes reformularlo?"
            )
        # Llamada real a OpenRouter LLM
        prompt = ctx.history[-1]["user"] if ctx.history else nlu.get("text", "")
        if not prompt:
            prompt = nlu.get("text", "")
        logger.info(f"Consultando LLM externo (OpenRouter) con: {prompt}")
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente meteorológico integrado en MeteoSer. Responde en español y de forma clara.",
                },
                {"role": "user", "content": prompt},
            ],
        }
        try:
            response = requests.post(
                OPENROUTER_API_URL, headers=headers, json=data, timeout=20
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return DialogResponse(text=content)
            else:
                logger.error(
                    f"Error LLM externo: {response.status_code} {response.text}"
                )
                return DialogResponse(
                    text="No se pudo obtener respuesta de la IA externa (OpenRouter). Intenta de nuevo más tarde."
                )
        except Exception as e:
            logger.error(f"Excepción al consultar LLM externo: {e}")
            return DialogResponse(
                text="Error al conectar con la IA externa. Intenta de nuevo más tarde."
            )


DIALOG_MANAGER = DialogManager()


def synthesize_text_to_speech(text: str) -> Optional[bytes]:
    if not text:
        return None
    try:
        engine = _get_tts_engine()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            out_path = tmp.name
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        data = Path(out_path).read_bytes()
        try:
            os.remove(out_path)
        except Exception:
            logging.exception("Silent except at 243 - revisar contexto")
        if data:
            return data
    except Exception as e:
        logger.error(f"Error TTS: {e}")
    return None


def transcribe_speech_to_text(audio_bytes: bytes) -> str:
    if not audio_bytes:
        return ""
    try:
        import io
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="es-ES")
    except Exception as e:
        logger.error(f"Error STT: {e}")
        return ""


def start_session(user_id: Optional[str] = None) -> str:
    ctx = SESSION_STORE.create_session(user_id=user_id)
    return ctx.session_id


def handle_user_text(session_id: str, text: str) -> Dict[str, Any]:
    resp = DIALOG_MANAGER.handle_text(session_id, text)
    audio = synthesize_text_to_speech(resp.text)
    return {
        "text": resp.text,
        "audio": bool(audio),
        "end_session": resp.end_session,
        "metadata": resp.metadata,
    }


def handle_user_audio(session_id: str, audio_bytes: bytes) -> Dict[str, Any]:
    text = transcribe_speech_to_text(audio_bytes)
    return handle_user_text(session_id, text)


def get_session_history(session_id: str) -> List[Dict[str, Any]]:
    s = SESSION_STORE.get_session(session_id)
    if not s:
        return []
    return s.history


def redact_sensitive_text(text: str) -> str:
    import re

    return re.sub(r"[A-Za-z0-9_\-]{20,}", "[REDACTED]", text)


def smoke_test() -> None:
    logger.info("SMOKE TEST Bloque F: motor conversacional y UI (modo mock).")

    sid = start_session(user_id="sergio_test")
    print("Sesión creada:", sid)

    inputs = [
        "Buenos días",
        "¿Qué me pongo hoy?",
        "¿Cuál es el estado de los sensores?",
        "Desplegar algoritmo",
        "sí, desplegar",
        "Gracias",
    ]

    for t in inputs:
        out = handle_user_text(sid, t)
        print(f"> {t}")
        print("  ->", out["text"])
        time.sleep(0.5)

    hist = get_session_history(sid)
    print("\nHistorial de la sesión:")
    print(json.dumps(hist, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    smoke_test()
