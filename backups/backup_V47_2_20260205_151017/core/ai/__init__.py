"""
MeteoSer AI Orchestrator - Sistema de IA Interna Completo
==========================================================

Módulos principales:
- orchestrator: Núcleo central, loop asíncrono, coordinación
- knowledge: Gestor de conocimiento, contratos, arquitectura
- contracts: Parser de contratos JSON/YAML
- codegen: Generación de código con LLM externo
- autoheal: Autocuración y recuperación de errores
- updater: Actualización autónoma de software/firmware
- dialog: Diálogo avanzado y NLU específico
- explainer: Explicabilidad total del sistema
"""

from .orchestrator import AIOrchestrator, get_orchestrator
from .knowledge import KnowledgeManager
from .contracts import ContractParser
from .codegen import CodeGenerator
from .autoheal import AutoHealEngine
from .updater import UpdaterEngine
from .dialog import DialogManager
from .explainer import Explainer

__all__ = [
    "AIOrchestrator",
    "get_orchestrator",
    "KnowledgeManager",
    "ContractParser",
    "CodeGenerator",
    "AutoHealEngine",
    "UpdaterEngine",
    "DialogManager",
    "Explainer",
]

__version__ = "1.0.0"
