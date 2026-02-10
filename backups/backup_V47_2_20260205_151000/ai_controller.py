"""
ai_controller.py - Controlador principal de IA para integración con main_asgi.py
================================================================================

Inicializa y gestiona todos los subsistemas de IA.
"""

import logging
import asyncio
from typing import Dict, Any
from core.ai import (
    get_orchestrator,
    KnowledgeManager,
    ContractParser,
    CodeGenerator,
    AutoHealEngine,
    UpdaterEngine,
    DialogManager,
    Explainer
)

logger = logging.getLogger(__name__)


class AIController:
    """
    Controlador central de IA para MeteoSer.
    
    Gestiona todos los subsistemas de IA y expone endpoints.
    """
    
    def __init__(self, bus=None, config_dir: str = "data", contracts_dir: str = "contracts"):
        self.bus = bus
        self.config_dir = config_dir
        self.contracts_dir = contracts_dir
        
        # Subsistemas
        self.orchestrator = None
        self.knowledge = None
        self.contract_parser = None
        self.codegen = None
        self.autoheal = None
        self.updater = None
        self.dialog = None
        self.explainer = None
        
        self.initialized = False
        
        logger.info("🤖 AIController creado")
    
    async def initialize(self) -> bool:
        """Inicializa todos los subsistemas de IA"""
        try:
            logger.info("🚀 Inicializando subsistemas de IA...")
            
            # 1. Knowledge Manager (primero, otros dependen de él)
            self.knowledge = KnowledgeManager(knowledge_dir=str(self.config_dir))
            logger.info("✅ KnowledgeManager inicializado")
            
            # 2. Contract Parser
            self.contract_parser = ContractParser(contracts_dir=self.contracts_dir)
            logger.info("✅ ContractParser inicializado")
            
            # 3. Code Generator (usa API key del ambiente)
            self.codegen = CodeGenerator()
            logger.info("✅ CodeGenerator inicializado")
            
            # 4. Auto-Heal Engine
            self.autoheal = AutoHealEngine()
            logger.info("✅ AutoHealEngine inicializado")
            
            # 5. Updater Engine
            self.updater = UpdaterEngine()
            logger.info("✅ UpdaterEngine inicializado")
            
            # 6. Explainer
            self.explainer = Explainer(knowledge_manager=self.knowledge)
            logger.info("✅ Explainer inicializado")
            
            # 7. Dialog Manager
            self.dialog = DialogManager(
                bus=self.bus,
                knowledge_manager=self.knowledge,
                explainer=self.explainer
            )
            logger.info("✅ DialogManager inicializado")
            
            # 8. Orchestrator (último, coordina todo)
            self.orchestrator = get_orchestrator()
            
            # Registrar subsistemas en el orchestrator
            self.orchestrator.register_subsystem("knowledge", self.knowledge)
            self.orchestrator.register_subsystem("contracts", self.contract_parser)
            self.orchestrator.register_subsystem("codegen", self.codegen)
            self.orchestrator.register_subsystem("autoheal", self.autoheal)
            self.orchestrator.register_subsystem("updater", self.updater)
            self.orchestrator.register_subsystem("dialog", self.dialog)
            self.orchestrator.register_subsystem("explainer", self.explainer)
            
            # Registrar Bus si está disponible
            if self.bus:
                self.orchestrator.bus = self.bus
                logger.info("✅ Bus registrado en orchestrator")
            
            # Iniciar orchestrator (ejecuta en background)
            self.orchestrator.start_sync()
            logger.info("✅ Orchestrator iniciado")
            
            self.initialized = True
            logger.info("🎉 Sistema de IA completamente inicializado")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Error inicializando IA: {e}")
            return False
    
    async def shutdown(self):
        """Apaga todos los subsistemas de IA"""
        try:
            logger.info("🛑 Apagando sistema de IA...")
            
            if self.orchestrator:
                self.orchestrator.stop()
                logger.info("✅ Orchestrator detenido")
            
            logger.info("✅ Sistema de IA apagado")
        
        except Exception as e:
            logger.error(f"❌ Error apagando IA: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado de todos los subsistemas"""
        status = {
            "initialized": self.initialized,
            "subsystems": {}
        }
        
        if self.initialized:
            try:
                if self.orchestrator:
                    status["subsystems"]["orchestrator"] = self.orchestrator.get_status()
                
                if self.knowledge:
                    status["subsystems"]["knowledge"] = self.knowledge.get_status()
                
                if self.autoheal:
                    status["subsystems"]["autoheal"] = self.autoheal.get_status()
                
                if self.updater:
                    status["subsystems"]["updater"] = self.updater.get_status()
                
                if self.dialog:
                    status["subsystems"]["dialog"] = self.dialog.get_status()
                
                if self.explainer:
                    status["subsystems"]["explainer"] = self.explainer.get_status()
            
            except Exception as e:
                logger.error(f"❌ Error obteniendo status: {e}")
                status["error"] = str(e)
        
        return status
    
    def process_dialog(self, session_id: str, message: str) -> Dict[str, Any]:
        """Procesa un mensaje de diálogo"""
        if not self.dialog:
            return {"error": "Dialog manager not initialized"}
        
        return self.dialog.process_message(session_id, message)
    
    def explain(self, query: str) -> str:
        """Genera una explicación"""
        if not self.explainer:
            return "Explainer not initialized"
        
        return self.explainer.explain(query, self.bus)
    
    def list_contracts(self) -> list:
        """Lista todos los contratos"""
        if not self.knowledge:
            return []
        
        return self.knowledge.list_contracts()
    
    def schedule_autoheal_scan(self):
        """Programa un escaneo de auto-curación"""
        if not self.orchestrator or not self.autoheal:
            return None
        
        def scan_task():
            issues = self.autoheal.scan_logs("logs")
            logger.info(f"🔍 Scan completado: {len(issues)} problemas detectados")
            return issues
        
        return self.orchestrator.schedule_task(
            name="autoheal_scan",
            callback=scan_task,
            priority=7
        )
    
    def schedule_contract_scan(self):
        """Programa un escaneo de contratos"""
        if not self.orchestrator or not self.contract_parser:
            return None
        
        def scan_task():
            contracts = self.contract_parser.scan_contracts_dir(self.contracts_dir)
            logger.info(f"📄 Scan de contratos: {len(contracts)} encontrados")
            
            # Registrar en knowledge
            for contract in contracts:
                self.knowledge.register_contract(contract)
            
            return contracts
        
        return self.orchestrator.schedule_task(
            name="contract_scan",
            callback=scan_task,
            priority=5
        )


# Instancia global (opcional, para acceso fácil)
_ai_controller: AIController = None


def get_ai_controller() -> AIController:
    """Obtiene la instancia global del controlador de IA"""
    global _ai_controller
    return _ai_controller


def initialize_ai_controller(bus=None, config_dir: str = "data", contracts_dir: str = "contracts") -> AIController:
    """Inicializa el controlador global de IA"""
    global _ai_controller
    
    if _ai_controller is None:
        _ai_controller = AIController(bus=bus, config_dir=config_dir, contracts_dir=contracts_dir)
    
    return _ai_controller
