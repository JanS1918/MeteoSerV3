"""
MeteoSer AI Dialog Manager - Gestor de Diálogo Avanzado
========================================================

Interfaz conversacional inteligente específica para MeteoSer.
Refactorizado desde meteoser_ia/block_f.py con capacidades extendidas.
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import os
import requests

logger = logging.getLogger(__name__)


@dataclass
class DialogContext:
    """Contexto de conversación"""
    session_id: str
    user_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    slots: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DialogManager:
    """
    Gestor de diálogo avanzado para MeteoSer.
    
    Capacidades:
    - NLU específico de MeteoSer (sensores, motores, índices)
    - Acceso completo al Bus para consultas
    - Integración con LLM externo para preguntas complejas
    - Contexto persistente entre sesiones
    """
    
    def __init__(self, bus=None, knowledge_manager=None, explainer=None):
        self.bus = bus
        self.knowledge_manager = knowledge_manager
        self.explainer = explainer
        
        self.sessions: Dict[str, DialogContext] = {}
        self.intent_handlers: Dict[str, Callable] = {}
        
        # Configuración LLM externo
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openai/gpt-3.5-turbo"
        
        self._register_default_handlers()
        
        logger.info("💬 DialogManager inicializado")
    
    def _register_default_handlers(self) -> None:
        """Registra handlers de intenciones por defecto"""
        self.intent_handlers.update({
            "greeting": self._handle_greeting,
            "ask_sensor": self._handle_ask_sensor,
            "ask_status": self._handle_ask_status,
            "ask_motor": self._handle_ask_motor,
            "ask_explanation": self._handle_ask_explanation,
            "ask_history": self._handle_ask_history,
            "ask_contract": self._handle_ask_contract,
            "system_command": self._handle_system_command,
            "fallback": self._handle_fallback,
        })
    
    def register_intent_handler(self, intent: str, handler: Callable) -> None:
        """Registra un handler personalizado para una intención"""
        self.intent_handlers[intent] = handler
        logger.info(f"📝 Handler registrado para intención: {intent}")
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Crea una nueva sesión de diálogo"""
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.sessions[session_id] = DialogContext(session_id=session_id, user_id=user_id)
        logger.info(f"🆕 Sesión creada: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[DialogContext]:
        """Obtiene contexto de sesión"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"🗑️ Sesión eliminada: {session_id}")
            return True
        return False
    
    def classify_intent(self, text: str, context: Optional[DialogContext] = None) -> Dict[str, Any]:
        """Clasifica la intención del usuario (NLU simple)"""
        text_lower = text.lower()
        
        # Saludos
        if any(w in text_lower for w in ["hola", "buenos días", "buenas tardes", "hey"]):
            return {"intent": "greeting", "confidence": 0.9, "entities": {}}
        
        # Consultas sobre sensores
        if any(w in text_lower for w in ["sensor", "temperatura", "humedad", "presión", "viento"]):
            entities = {}
            if "temperatura" in text_lower:
                entities["sensor_type"] = "temperatura"
            elif "humedad" in text_lower:
                entities["sensor_type"] = "humedad"
            elif "presión" in text_lower:
                entities["sensor_type"] = "presión"
            
            return {"intent": "ask_sensor", "confidence": 0.85, "entities": entities}
        
        # Estado del sistema
        if any(w in text_lower for w in ["estado", "status", "cómo está", "funcionando"]):
            return {"intent": "ask_status", "confidence": 0.85, "entities": {}}
        
        # Motores y cálculos
        if any(w in text_lower for w in ["motor", "cálculo", "fórmula", "índice"]):
            return {"intent": "ask_motor", "confidence": 0.8, "entities": {}}
        
        # Explicaciones
        if any(w in text_lower for w in ["explica", "qué es", "cómo funciona", "por qué"]):
            return {"intent": "ask_explanation", "confidence": 0.85, "entities": {}}
        
        # Historial
        if any(w in text_lower for w in ["historial", "histórico", "antes", "ayer"]):
            return {"intent": "ask_history", "confidence": 0.8, "entities": {}}
        
        # Contratos
        if any(w in text_lower for w in ["contrato", "componente", "añadir sensor"]):
            return {"intent": "ask_contract", "confidence": 0.8, "entities": {}}
        
        # Comandos de sistema
        if any(w in text_lower for w in ["reinicia", "actualiza", "ejecuta", "detén"]):
            return {"intent": "system_command", "confidence": 0.85, "entities": {}}
        
        # Fallback (delegar a LLM externo)
        return {"intent": "fallback", "confidence": 0.5, "entities": {}}
    
    def process_message(self, session_id: str, text: str) -> Dict[str, Any]:
        """Procesa un mensaje del usuario"""
        # Obtener o crear sesión
        context = self.get_session(session_id)
        if not context:
            session_id = self.create_session()
            context = self.get_session(session_id)
        
        # Actualizar actividad
        context.last_active = time.time()
        
        # Clasificar intención
        nlu = self.classify_intent(text, context)
        intent = nlu["intent"]
        
        # Obtener handler
        handler = self.intent_handlers.get(intent, self._handle_fallback)
        
        # Ejecutar handler
        logger.info(f"💬 Procesando mensaje: '{text[:50]}...' → intent={intent}")
        
        try:
            response = handler(context, nlu, text)
            
            # Guardar en historial
            context.history.append({
                "timestamp": time.time(),
                "user_message": text,
                "nlu": nlu,
                "response": response,
            })
            
            return {
                "session_id": session_id,
                "text": response,
                "intent": intent,
                "confidence": nlu["confidence"],
            }
        
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            return {
                "session_id": session_id,
                "text": "Lo siento, ocurrió un error procesando tu mensaje.",
                "error": str(e),
            }
    
    # ========== HANDLERS DE INTENCIONES ==========
    
    def _handle_greeting(self, context: DialogContext, nlu: Dict, text: str) -> str:
        """Handler para saludos"""
        return "Hola, soy el asistente de MeteoSer. ¿En qué puedo ayudarte hoy?"
    
    def _handle_ask_sensor(self, context: DialogContext, nlu: Dict, text: str) -> str:
        """Handler para consultas sobre sensores"""
        if not self.bus:
            return "No tengo acceso al Bus para consultar sensores."
        
        sensor_type = nlu["entities"].get("sensor_type")
        
        if sensor_type:
            # Buscar valores en el Bus
            matching_keys = [k for k in self.bus.leer_todas().keys() 
                           if sensor_type in k.lower()]
            
            if matching_keys:
                response = f"Valores de {sensor_type}:\n"
                for key in matching_keys[:5]:  # Limitar a 5
                    value = self.bus.leer(key)
                    response += f"- {key}: {value}\n"
                return response
            else:
                return f"No encontré valores de {sensor_type} en el Bus."
        else:
            # Listar sensores disponibles
            all_keys = list(self.bus.leer_todas().keys())
            return f"Hay {len(all_keys)} valores en el Bus. ¿Qué sensor específico te interesa?"
    
    def _handle_ask_status(self, context: DialogContext, nlu: Dict, text: str) -> str:
        """Handler para consultas de estado del sistema"""
        if not self.bus:
            return "No tengo acceso al estado del sistema."
        
        # Obtener métricas del Bus
        all_values = self.bus.leer_todas()
        
        status = f"📊 Estado de MeteoSer:\n"
        status += f"- Valores en Bus: {len(all_values)}\n"
        
        # Buscar métricas específicas
        if "ai_orchestrator_status" in all_values:
            status += f"- IA Orchestrator: {all_values['ai_orchestrator_status']}\n"
        
        return status
    
    def _handle_ask_motor(self, context: DialogContext, nlu: Dict, text: str) -> str:
        """Handler para consultas sobre motores y cálculos"""
        if not self.bus:
            return "No tengo acceso a la información de motores."
        
        # Buscar motores en el Bus
        motor_keys = [k for k in self.bus.leer_todas().keys() if "motor_" in k]
        
        if motor_keys:
            return f"Hay {len(motor_keys)} motores activos. Ejemplos: {', '.join(motor_keys[:5])}"
        else:
            return "No encontré información de motores en este momento."
    
    def _handle_ask_explanation(self, context: DialogContext, nlu: Dict, text: str) -> str:
        """Handler para solicitudes de explicación"""
        if self.explainer:
            # Delegar al Explainer
            return self.explainer.explain(text, self.bus)
        else:
            return "El módulo de explicaciones no está disponible."
    
    def _handle_ask_history(self, context: DialogContext, nlu: Dict, text: str) -> str:
        """Handler para consultas de historial"""
        if self.knowledge_manager:
            history = self.knowledge_manager.get_history(limit=5)
            if history:
                response = "Últimos eventos:\n"
                for entry in history:
                    response += f"- {entry['event_type']}: {entry['data']}\n"
                return response
            else:
                return "No hay historial disponible."
        else:
            return "El historial no está disponible."
    
    def _handle_ask_contract(self, context: DialogContext, nlu: Dict, text: str) -> str:
        """Handler para consultas sobre contratos"""
        if self.knowledge_manager:
            contracts = self.knowledge_manager.list_contracts()
            if contracts:
                return f"Hay {len(contracts)} contratos registrados."
            else:
                return "No hay contratos registrados aún."
        else:
            return "El gestor de contratos no está disponible."
    
    def _handle_system_command(self, context: DialogContext, nlu: Dict, text: str) -> str:
        """Handler para comandos de sistema"""
        return "Los comandos de sistema requieren confirmación adicional por seguridad."
    
    def _handle_fallback(self, context: DialogContext, nlu: Dict, text: str) -> str:
        """Handler fallback: delega a LLM externo"""
        if not self.api_key:
            return "Lo siento, no entendí tu pregunta. ¿Puedes reformularla?"
        
        try:
            # Construir contexto de MeteoSer para el LLM
            system_prompt = """Eres el asistente inteligente de MeteoSer, un sistema meteorológico avanzado.
Tienes conocimiento sobre sensores, motores de cálculo, índices meteorológicos, contratos de componentes.
Responde de forma clara y técnica, específicamente sobre MeteoSer."""
            
            # Añadir contexto del Bus si está disponible
            if self.bus:
                bus_summary = f"Actualmente hay {len(self.bus.leer_todas())} valores en el Bus del sistema."
                system_prompt += f"\n\n{bus_summary}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.7,
                "max_tokens": 300,
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                return answer
            else:
                logger.error(f"❌ Error LLM: {response.status_code}")
                return "Lo siento, no pude procesar tu pregunta en este momento."
        
        except Exception as e:
            logger.error(f"❌ Error en fallback: {e}")
            return "Lo siento, no entendí tu pregunta. ¿Puedes ser más específico sobre MeteoSer?"
    
    def get_status(self) -> Dict:
        """Retorna estado del gestor de diálogo"""
        return {
            "sessions_active": len(self.sessions),
            "intents_registered": len(self.intent_handlers),
            "llm_configured": bool(self.api_key),
            "bus_connected": self.bus is not None,
        }
