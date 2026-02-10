"""
MeteoSer AI Knowledge Manager - Gestor de Conocimiento
=======================================================

Gestiona toda la base de conocimiento del sistema:
- Contratos de sensores y componentes
- Arquitectura del sistema (módulos, dependencias)
- Historial de cambios y versiones
- Reglas y políticas operativas
- Metadatos y estadísticas
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """Gestor centralizado del conocimiento de MeteoSer"""
    
    def __init__(self, knowledge_dir: str = "data/ai_knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos de persistencia
        self.contracts_file = self.knowledge_dir / "contracts.json"
        self.architecture_file = self.knowledge_dir / "architecture.json"
        self.history_file = self.knowledge_dir / "history.json"
        self.rules_file = self.knowledge_dir / "rules.json"
        
        # Caché en memoria
        self.contracts: Dict[str, Dict] = {}
        self.architecture: Dict = {}
        self.history: List[Dict] = []
        self.rules: Dict[str, Any] = {}
        
        self._load_all()
        logger.info(f"📚 KnowledgeManager inicializado (dir={knowledge_dir})")
    
    def _load_all(self) -> None:
        """Carga todo el conocimiento desde disco"""
        try:
            if self.contracts_file.exists():
                self.contracts = json.loads(self.contracts_file.read_text(encoding="utf-8"))
            
            if self.architecture_file.exists():
                self.architecture = json.loads(self.architecture_file.read_text(encoding="utf-8"))
            
            if self.history_file.exists():
                self.history = json.loads(self.history_file.read_text(encoding="utf-8"))
            
            if self.rules_file.exists():
                self.rules = json.loads(self.rules_file.read_text(encoding="utf-8"))
            
            logger.info(f"✅ Conocimiento cargado: {len(self.contracts)} contratos, "
                       f"{len(self.history)} entradas de historial")
        except Exception as e:
            logger.warning(f"⚠️ Error cargando conocimiento: {e}")
    
    def _save_contracts(self) -> None:
        """Guarda contratos a disco"""
        self.contracts_file.write_text(json.dumps(self.contracts, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def _save_architecture(self) -> None:
        """Guarda arquitectura a disco"""
        self.architecture_file.write_text(json.dumps(self.architecture, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def _save_history(self) -> None:
        """Guarda historial a disco"""
        self.history_file.write_text(json.dumps(self.history, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def _save_rules(self) -> None:
        """Guarda reglas a disco"""
        self.rules_file.write_text(json.dumps(self.rules, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # ========== CONTRATOS ==========
    
    def register_contract(self, contract_id_or_data, contract_data: Optional[Dict] = None) -> None:
        """Registra un contrato de sensor/componente
        
        Acepta:
            - register_contract(dict) donde dict contiene 'id'
            - register_contract(contract_id, contract_data)
        """
        if contract_data is None:
            # Primer argumento es un dict con 'id' dentro
            contract_data = contract_id_or_data
            contract_id = contract_data.get("id")
            if not contract_id:
                raise ValueError("El dict debe contener 'id'")
        else:
            # Forma tradicional (contract_id, contract_data)
            contract_id = contract_id_or_data
        
        self.contracts[contract_id] = {
            **contract_data,
            "registered_at": datetime.now().isoformat(),
            "checksum": self._compute_checksum(contract_data)
        }
        self._save_contracts()
        self._add_history_entry("contract_registered", {"contract_id": contract_id})
        logger.info(f"📝 Contrato registrado: {contract_id}")
    
    def get_contract(self, contract_id: str) -> Optional[Dict]:
        """Obtiene un contrato por ID"""
        return self.contracts.get(contract_id)
    
    def list_contracts(self, filter_type: Optional[str] = None) -> List[Dict]:
        """Lista contratos, opcionalmente filtrados por tipo"""
        contracts = list(self.contracts.values())
        if filter_type:
            contracts = [c for c in contracts if c.get("type") == filter_type]
        return contracts
    
    def delete_contract(self, contract_id: str) -> bool:
        """Elimina un contrato"""
        if contract_id in self.contracts:
            del self.contracts[contract_id]
            self._save_contracts()
            self._add_history_entry("contract_deleted", {"contract_id": contract_id})
            logger.info(f"🗑️ Contrato eliminado: {contract_id}")
            return True
        return False
    
    # ========== ARQUITECTURA ==========
    
    def update_architecture(self, key_or_dict, value: Any = None) -> None:
        """Actualiza un aspecto de la arquitectura
        
        Acepta:
            - update_architecture(key, value) para actualizar una clave
            - update_architecture(dict) para actualizar múltiples claves
        """
        if isinstance(key_or_dict, dict):
            # Actualizar múltiples claves
            for key, val in key_or_dict.items():
                self.architecture[key] = {
                    "value": val,
                    "updated_at": datetime.now().isoformat()
                }
            logger.info(f"🏗️ Arquitectura actualizada: {len(key_or_dict)} claves")
        else:
            # Actualizar una clave
            key = key_or_dict
            self.architecture[key] = {
                "value": value,
                "updated_at": datetime.now().isoformat()
            }
            logger.info(f"🏗️ Arquitectura actualizada: {key}")
        
        self._save_architecture()
    
    def get_architecture(self, key: Optional[str] = None) -> Any:
        """Obtiene arquitectura completa o una clave específica"""
        if key:
            return self.architecture.get(key, {}).get("value")
        return {k: v["value"] for k, v in self.architecture.items()}
    
    def register_module(self, module_name: str, module_info: Dict) -> None:
        """Registra un módulo del sistema"""
        if "modules" not in self.architecture:
            self.architecture["modules"] = {"value": {}, "updated_at": datetime.now().isoformat()}
        
        self.architecture["modules"]["value"][module_name] = {
            **module_info,
            "registered_at": datetime.now().isoformat()
        }
        self._save_architecture()
        logger.info(f"📦 Módulo registrado: {module_name}")
    
    # ========== HISTORIAL ==========
    
    def _add_history_entry(self, event_type: str, data: Dict) -> None:
        """Añade una entrada al historial"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.history.append(entry)
        
        # Limitar historial a últimas 1000 entradas
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        self._save_history()
    
    def get_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Obtiene historial, opcionalmente filtrado por tipo"""
        history = self.history
        if event_type:
            history = [e for e in history if e["event_type"] == event_type]
        return history[-limit:]
    
    def record_change(self, event_type: str, data_or_description, metadata: Dict = None) -> None:
        """Registra un cambio en el sistema
        
        Acepta:
            - record_change(event_type, description_string) -> usa como descripción
            - record_change(event_type, data_dict) -> usa como datos
            - record_change(event_type, description_string, metadata_dict)
        """
        if isinstance(data_or_description, dict):
            # Es un dict de datos
            data = data_or_description
            description = data.get("description", "")
            meta = data.get("metadata", {})
        else:
            # Es una string de descripción
            description = data_or_description
            data = {"description": description}
            meta = metadata or {}
        
        self._add_history_entry(event_type, {
            "description": description,
            "metadata": meta,
            **data
        })
        logger.info(f"📝 Cambio registrado: {event_type} - {description}")
    
    # ========== REGLAS Y POLÍTICAS ==========
    
    def set_rule(self, rule_id: str, rule_data) -> None:
        """Define una regla operativa
        
        Args:
            rule_id: ID de la regla
            rule_data: Dict con los datos, o cualquier valor (se envuelve en {"value": value})
        """
        if isinstance(rule_data, dict):
            data = rule_data
        else:
            # Envolver valor no-dict
            data = {"value": rule_data}
        
        self.rules[rule_id] = {
            **data,
            "created_at": datetime.now().isoformat()
        }
        self._save_rules()
        logger.info(f"📋 Regla definida: {rule_id}")
    
    def get_rule(self, rule_id: str) -> Optional[Any]:
        """Obtiene una regla por ID
        
        Retorna:
            - El valor directo si fue establecido como valor simple
            - El dict completo si fue establecido como dict
        """
        rule = self.rules.get(rule_id)
        if rule is None:
            return None
        
        # Si tiene exactamente 2 keys y una es "created_at", es un valor simple envuelto
        if len(rule) == 2 and "created_at" in rule and "value" in rule:
            return rule["value"]
        
        # Si tiene "value" key entre otras, también es probablemente un valor simple
        if "value" in rule and len(rule) > 1 and list(rule.keys())[0] != "created_at":
            return rule["value"]
        
        # Si tiene "value" como única key además de metadatos, retorna valor
        if "value" in rule:
            return rule["value"]
        
        # De lo contrario retorna el dict completo
        return rule
    
    def list_rules(self, category: Optional[str] = None) -> List[Dict]:
        """Lista reglas, opcionalmente filtradas por categoría"""
        rules = list(self.rules.values())
        if category:
            rules = [r for r in rules if r.get("category") == category]
        return rules
    
    # ========== UTILIDADES ==========
    
    def _compute_checksum(self, data: Any) -> str:
        """Calcula checksum SHA256 de datos"""
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def search(self, query: str, scope: str = "all") -> Dict:
        """Búsqueda textual en el conocimiento
        
        Returns:
            Dict con keys "contracts", "history", "rules" según scope
        """
        results = {
            "contracts": [],
            "history": [],
            "rules": []
        }
        query_lower = query.lower()
        
        if scope in ("all", "contracts"):
            for cid, contract in self.contracts.items():
                if query_lower in json.dumps(contract).lower():
                    results["contracts"].append({"id": cid, "data": contract})
        
        if scope in ("all", "history"):
            for entry in self.history:
                if query_lower in json.dumps(entry).lower():
                    results["history"].append(entry)
        
        if scope in ("all", "rules"):
            for rid, rule in self.rules.items():
                if query_lower in json.dumps(rule).lower():
                    results["rules"].append({"id": rid, "data": rule})
        
        return results
    
    def get_status(self) -> Dict:
        """Retorna estado del gestor de conocimiento"""
        return {
            "contracts_count": len(self.contracts),
            "history_entries": len(self.history),
            "rules_count": len(self.rules),
            "architecture_keys": len(self.architecture),
            "storage_path": str(self.knowledge_dir),
        }
    
    def export_knowledge(self, output_path: str) -> None:
        """Exporta todo el conocimiento a un único archivo JSON"""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "contracts": self.contracts,
            "architecture": self.architecture,
            "history": self.history,
            "rules": self.rules,
        }
        Path(output_path).write_text(json.dumps(export_data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"💾 Conocimiento exportado a: {output_path}")
    
    def import_knowledge(self, input_path: str) -> None:
        """Importa conocimiento desde un archivo JSON"""
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
        self.contracts.update(data.get("contracts", {}))
        self.architecture.update(data.get("architecture", {}))
        self.history.extend(data.get("history", []))
        self.rules.update(data.get("rules", {}))
        
        self._save_contracts()
        self._save_architecture()
        self._save_history()
        self._save_rules()
        
        logger.info(f"📥 Conocimiento importado desde: {input_path}")
