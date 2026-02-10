"""
MeteoSer AI Explainer - Sistema de Explicabilidad
==================================================

Genera explicaciones en lenguaje natural sobre cualquier aspecto de MeteoSer.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
import os
import requests

try:
    from core.config.secrets_vault import get_vault
    _HAS_VAULT = True
except ImportError:
    _HAS_VAULT = False

logger = logging.getLogger(__name__)


class Explainer:
    """
    Sistema de explicabilidad para MeteoSer.
    
    Capacidades:
    - Explicar fórmulas y cálculos en lenguaje natural
    - Explicar valores del Bus con contexto
    - Explicar motores y su lógica
    - Explicar componentes y su funcionamiento
    - Integración con LLM para explicaciones complejas
    """
    
    def __init__(self, knowledge_manager=None):
        self.knowledge_manager = knowledge_manager
        
        try:
            from core.config.env_loader import load_dotenv
            load_dotenv()
        except Exception:
            pass
        
        # Configuración LLM externo - usar vault cifrado
        provider_env = os.getenv("METEOSER_LLM_PROVIDER")
        vault = get_vault() if _HAS_VAULT else None

        groq_key = (vault.get_api_key("GROQ_API_KEY", "GROQ_API_KEY") if vault else None) or os.environ.get("GROQ_API_KEY", "")
        openrouter_key = (vault.get_openrouter_key() if vault else None) or os.environ.get("OPENROUTER_API_KEY", "")
        provider_choice = (provider_env or ("groq" if groq_key else "openrouter")).lower()

        if provider_choice == "groq":
            self.api_key = groq_key
            self.api_url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
            self.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        else:
            self.api_key = openrouter_key
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = "openai/gpt-3.5-turbo"
        
        # Catálogo de explicaciones predefinidas
        self.explanations = {
            "temperatura": "La temperatura es una medida del calor o frío del ambiente, generalmente en grados Celsius (°C).",
            "humedad": "La humedad relativa es el porcentaje de vapor de agua en el aire respecto al máximo que podría contener a esa temperatura.",
            "presión": "La presión atmosférica es la fuerza por unidad de superficie ejercida por el peso de la atmósfera, medida en hPa o mbar.",
            "viento": "El viento es el movimiento del aire respecto a la superficie terrestre, caracterizado por velocidad (m/s o km/h) y dirección.",
            "utci": "El UTCI (Universal Thermal Climate Index) es un índice de sensación térmica que considera temperatura, humedad, viento y radiación solar.",
            "dewpoint": "El punto de rocío es la temperatura a la que el vapor de agua se condensaría en gotas (rocío), dada la humedad actual.",
            "heatindex": "El índice de calor combina temperatura y humedad para estimar la sensación térmica en condiciones calurosas.",
            "windchill": "El windchill es la temperatura que se siente por el efecto del viento en condiciones frías.",
        }
        
        logger.info("📚 Explainer inicializado")
    
    def explain(self, query: str, bus=None) -> str:
        """
        Genera una explicación en lenguaje natural.
        
        Args:
            query: Pregunta o concepto a explicar
            bus: Instancia del Bus para contexto adicional
        
        Returns:
            Explicación en texto plano
        """
        query_lower = query.lower()
        
        # 1. Buscar en explicaciones predefinidas
        for key, explanation in self.explanations.items():
            if key in query_lower:
                logger.info(f"📖 Explicación predefinida encontrada: {key}")
                return explanation
        
        # 2. Buscar en knowledge_manager
        if self.knowledge_manager:
            km_explanation = self._explain_from_knowledge(query_lower)
            if km_explanation:
                return km_explanation
        
        # 3. Buscar en el Bus
        if bus:
            bus_explanation = self._explain_from_bus(query_lower, bus)
            if bus_explanation:
                return bus_explanation
        
        # 4. Delegar a LLM externo
        return self._explain_with_llm(query, bus)
    
    def _explain_from_knowledge(self, query: str) -> Optional[str]:
        """Busca explicaciones en el knowledge manager"""
        try:
            # Buscar en contratos
            contracts = self.knowledge_manager.list_contracts()
            for contract in contracts:
                if contract["name"].lower() in query or contract["id"].lower() in query:
                    return f"Contrato {contract['name']} (tipo: {contract['type']}): {contract.get('description', 'Sin descripción')}"
            
            # Buscar en arquitectura
            architecture = self.knowledge_manager.get_architecture()
            for module_name, module_info in architecture.get("modules", {}).items():
                if module_name.lower() in query:
                    deps = module_info.get("dependencies", [])
                    return f"Módulo {module_name}: {module_info.get('description', 'Sin descripción')}. Dependencias: {', '.join(deps) if deps else 'ninguna'}."
            
            # Buscar en reglas
            rules = self.knowledge_manager.list_rules()
            for rule_key in rules:
                if rule_key.lower() in query:
                    rule_value = self.knowledge_manager.get_rule(rule_key)
                    return f"Regla {rule_key}: {rule_value}"
            
            return None
        
        except Exception as e:
            logger.error(f"[ERROR] Error buscando en knowledge: {e}")
            return None
    
    def _explain_from_bus(self, query: str, bus) -> Optional[str]:
        """Busca explicaciones en el Bus"""
        try:
            all_values = bus.leer_todas()
            
            # Buscar claves que coincidan con la query
            matching_keys = [k for k in all_values.keys() if query in k.lower()]
            
            if matching_keys:
                explanations = []
                for key in matching_keys[:3]:  # Limitar a 3
                    value = all_values[key]
                    explanations.append(f"{key} = {value}")
                
                return "Valores encontrados en el Bus:\n" + "\n".join(explanations)
            
            return None
        
        except Exception as e:
            logger.error(f"[ERROR] Error buscando en Bus: {e}")
            return None
    
    def _explain_with_llm(self, query: str, bus=None) -> str:
        """Genera explicación usando LLM externo"""
        if not self.api_key:
            return "No puedo generar una explicación detallada en este momento."
        
        try:
            # Construir contexto
            system_prompt = """Eres un experto en MeteoSer, un sistema meteorológico avanzado.
Explica conceptos técnicos de forma clara y accesible, pero precisa.
Tu audiencia son técnicos y usuarios interesados en meteorología."""
            
            # Añadir contexto del Bus si está disponible
            context_info = ""
            if bus:
                all_values = bus.leer_todas()
                context_info = f"\n\nContexto actual: El sistema tiene {len(all_values)} valores activos en el Bus."
                
                # Buscar valores relacionados
                query_words = re.findall(r'\w+', query.lower())
                related = []
                for key in all_values.keys():
                    if any(word in key.lower() for word in query_words):
                        related.append(f"{key}={all_values[key]}")
                
                if related:
                    context_info += f"\nValores relacionados: {', '.join(related[:5])}"
            
            full_query = query + context_info
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Explica: {full_query}"}
                ],
                "temperature": 0.7,
                "max_tokens": 400,
            }
            
            logger.info(f"🤖 Consultando LLM para explicar: {query[:50]}...")
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                explanation = result["choices"][0]["message"]["content"]
                logger.info("[OK] Explicación generada con LLM")
                return explanation
            else:
                logger.error(f"[ERROR] Error LLM: {response.status_code}")
                return "No pude generar una explicación completa en este momento."
        
        except Exception as e:
            logger.error(f"[ERROR] Error generando explicación: {e}")
            return "Ocurrió un error al generar la explicación."
    
    def explain_formula(self, formula_name: str, variables: Dict[str, float]) -> str:
        """
        Explica una fórmula paso a paso.
        
        Args:
            formula_name: Nombre de la fórmula (ej: "utci", "dewpoint")
            variables: Variables y sus valores actuales
        
        Returns:
            Explicación detallada de la fórmula y cálculo
        """
        # Catálogo de fórmulas conocidas
        formulas = {
            "dewpoint": {
                "description": "Punto de rocío usando aproximación Magnus-Tetens",
                "formula": "Td = (b * α) / (a - α), donde α = ln(RH/100) + (a*T)/(b+T)",
                "constants": {"a": 17.27, "b": 237.7},
            },
            "heatindex": {
                "description": "Índice de calor (Heat Index) usando ecuación de Rothfusz",
                "formula": "HI = función polinómica de T y RH",
                "constants": {},
            },
            "utci": {
                "description": "Universal Thermal Climate Index - sensación térmica universal",
                "formula": "UTCI = polinomio de 6º grado con T, RH, viento y radiación",
                "constants": {},
            },
        }
        
        formula_info = formulas.get(formula_name.lower())
        
        if not formula_info:
            return f"No tengo información sobre la fórmula '{formula_name}'."
        
        explanation = f"📐 Fórmula: {formula_name.upper()}\n"
        explanation += f"Descripción: {formula_info['description']}\n\n"
        explanation += f"Fórmula: {formula_info['formula']}\n\n"
        
        if formula_info['constants']:
            explanation += "Constantes:\n"
            for const_name, const_value in formula_info['constants'].items():
                explanation += f"  {const_name} = {const_value}\n"
        
        if variables:
            explanation += "\nVariables actuales:\n"
            for var_name, var_value in variables.items():
                explanation += f"  {var_name} = {var_value}\n"
        
        return explanation
    
    def explain_motor(self, motor_name: str, bus=None) -> str:
        """
        Explica qué hace un motor específico.
        
        Args:
            motor_name: Nombre del motor
            bus: Instancia del Bus para leer estado
        
        Returns:
            Explicación del motor
        """
        # Catálogo de motores conocidos
        motors = {
            "motor_dewpoint": "Calcula el punto de rocío a partir de temperatura y humedad",
            "motor_heatindex": "Calcula el índice de calor para estimar sensación térmica en calor",
            "motor_windchill": "Calcula el windchill para estimar sensación térmica en frío",
            "motor_utci": "Calcula el UTCI (índice de sensación térmica universal)",
            "motor_sun": "Calcula posición solar (azimut, elevación)",
            "motor_radiation": "Estima radiación solar teórica",
        }
        
        motor_name_clean = motor_name.lower().replace("_", "").replace("-", "")
        
        # Buscar descripción
        description = None
        for known_motor, desc in motors.items():
            if motor_name_clean in known_motor.replace("_", ""):
                description = desc
                break
        
        if not description:
            description = f"Motor de cálculo '{motor_name}'"
        
        explanation = f"🔧 {description}\n"
        
        # Buscar valores del motor en el Bus
        if bus:
            all_values = bus.leer_todas()
            motor_values = {k: v for k, v in all_values.items() if motor_name.lower() in k.lower()}
            
            if motor_values:
                explanation += "\nValores actuales:\n"
                for key, value in motor_values.items():
                    explanation += f"  {key} = {value}\n"
        
        return explanation
    
    def add_explanation(self, key: str, text: str) -> None:
        """Añade una explicación al catálogo"""
        self.explanations[key.lower()] = text
        logger.info(f"📝 Explicación añadida: {key}")
    
    def get_status(self) -> Dict:
        """Retorna estado del explainer"""
        return {
            "explanations_count": len(self.explanations),
            "llm_configured": bool(self.api_key),
            "knowledge_connected": self.knowledge_manager is not None,
        }
