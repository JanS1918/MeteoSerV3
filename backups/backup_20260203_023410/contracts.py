"""
MeteoSer AI Contract Parser - Parser de Contratos
==================================================

Parse

a y valida contratos de sensores/componentes en JSON/YAML.
Genera código de integración automáticamente.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

logger = logging.getLogger(__name__)


class ContractParser:
    """Parser y validador de contratos de sensores/componentes"""
    
    def __init__(self, contracts_dir: str = "contracts"):
        self.contracts_dir = Path(contracts_dir)
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_contracts: Dict[str, Dict] = {}
        
        logger.info(f"📄 ContractParser inicializado (dir={contracts_dir})")
    
    def load_contract(self, contract_path: str) -> Optional[Dict]:
        """Carga un contrato desde archivo JSON o YAML"""
        path = Path(contract_path)
        
        if not path.exists():
            logger.error(f"❌ Contrato no encontrado: {contract_path}")
            return None
        
        try:
            content = path.read_text(encoding="utf-8")
            
            if path.suffix in (".json",):
                contract = json.loads(content)
            elif path.suffix in (".yaml", ".yml"):
                contract = yaml.safe_load(content)
            else:
                logger.error(f"❌ Formato no soportado: {path.suffix}")
                return None
            
            # Validar schema básico
            is_valid, errors = self.validate_contract(contract)
            if is_valid:
                contract_id = contract.get("id", path.stem)
                self.loaded_contracts[contract_id] = contract
                logger.info(f"✅ Contrato cargado: {contract_id}")
                return contract
            else:
                logger.error(f"❌ Contrato inválido: {contract_path}")
                for error in errors:
                    logger.error(f"   - {error}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error cargando contrato {contract_path}: {e}")
            return None
    
    def validate_contract(self, contract: Dict) -> tuple:
        """Valida que un contrato tenga los campos requeridos
        
        Returns:
            (bool, list): (is_valid, errors_list)
        """
        required_fields = ["id", "name", "type", "version"]
        errors = []
        
        for field in required_fields:
            if field not in contract:
                error = f"Campo requerido ausente: {field}"
                logger.error(f"❌ {error}")
                errors.append(error)
        
        # Validar tipo
        valid_types = ["sensor", "actuator", "service", "component"]
        if contract.get("type") not in valid_types:
            error = f"Tipo inválido: {contract.get('type')}"
            logger.error(f"❌ {error}")
            errors.append(error)
        
        return (len(errors) == 0, errors)
    
    def scan_contracts_dir(self, contracts_dir: Optional[str] = None) -> List[str]:
        """Escanea el directorio de contratos y carga todos los encontrados
        
        Args:
            contracts_dir: Directorio opcional a usar; si se proporciona, actualiza self.contracts_dir
        """
        if contracts_dir:
            self.contracts_dir = Path(contracts_dir)
            self.contracts_dir.mkdir(parents=True, exist_ok=True)
        
        contract_files = list(self.contracts_dir.glob("*.json")) + \
                        list(self.contracts_dir.glob("*.yaml")) + \
                        list(self.contracts_dir.glob("*.yml"))
        
        loaded = []
        for contract_file in contract_files:
            contract = self.load_contract(str(contract_file))
            if contract:
                loaded.append(contract["id"])
        
        logger.info(f"📦 Contratos escaneados: {len(loaded)} encontrados")
        return loaded
    
    def get_contract(self, contract_id: str) -> Optional[Dict]:
        """Obtiene un contrato cargado por ID"""
        return self.loaded_contracts.get(contract_id)
    
    def generate_driver_scaffold(self, contract: Dict) -> str:
        """Genera scaffold de driver Python desde un contrato"""
        contract_id = contract["id"]
        contract_name = contract["name"]
        contract_type = contract["type"]
        protocol_info = contract.get("protocol", {})
        
        # Template básico - usar construction de string para evitar conflictos
        lines = [
            '"""',
            f'Driver para {contract_name}',
            f'Generado automáticamente desde contrato: {contract_id}',
            f'Tipo: {contract_type}',
        ]
        
        # Añadir info del protocolo
        if protocol_info:
            if isinstance(protocol_info, dict):
                lines.append(f'Protocolo: {protocol_info.get("type", "unknown")}')
            else:
                lines.append(f'Protocolo: {protocol_info}')
        
        lines.extend([
            '"""',
            '',
            'import logging',
            'from typing import Dict, Any, Optional',
            '',
            'logger = logging.getLogger(__name__)',
            '',
            '',
            f'class {contract_name.replace(" ", "")}Driver:',
            f'    """Driver para {contract_name}"""',
            '',
            '    def __init__(self, config: Dict[str, Any]):',
            '        self.config = config',
            f'        self.contract_id = "{contract_id}"',
            '        logger.info(f"🔌 Driver {self.contract_id} inicializado")',
        ])
        
        # Generar métodos de lectura por campo
        if "fields" in contract:
            for field in contract["fields"]:
                field_name = field["name"]
                field_unit = field.get("unit", "valor")
                field_method = field_name.lower().replace(" ", "_")
                lines.append('')
                lines.append(f'    def read_{field_method}(self) -> Optional[Any]:')
                lines.append(f'        """Lee {field_name} ({field_unit})"""')
                lines.append('        try:')
                lines.append(f'            # TODO: Implementar lectura real de {field_name}')
                lines.append('            value = None')
                lines.append('            return value')
                lines.append('        except Exception as e:')
                lines.append(f'            logger.error(f"❌ Error leyendo {field_method}: {{e}}")')
                lines.append('            return None')
        
        lines.append('')
        lines.append('    def read(self) -> Optional[Dict[str, Any]]:')
        lines.append('        """Lee datos del sensor/componente"""')
        lines.append('        try:')
        lines.append('            # TODO: Implementar lectura real')
        lines.append('            data = {')
        lines.append('                "timestamp": None,  # Añadir timestamp')
        lines.append('                "valid": True,')
        lines.append('            }')
        lines.append('')
        lines.append('            # Añadir campos según contrato')
        
        # Añadir campos del contrato
        if "fields" in contract:
            for field in contract["fields"]:
                field_name = field["name"]
                field_unit = field.get("unit", "valor")
                lines.append(f'            data["{field_name}"] = None  # {field_unit}')
        
        lines.append('')
        lines.append('            return data')
        lines.append('        except Exception as e:')
        lines.append('            logger.error(f"❌ Error leyendo {self.contract_id}: {e}")')
        lines.append('            return None')
        lines.append('')
        lines.append('    def write(self, data: Dict[str, Any]) -> bool:')
        lines.append('        """Escribe datos al actuador/componente (si aplica)"""')
        lines.append('        try:')
        lines.append('            # TODO: Implementar escritura real')
        lines.append('            logger.info(f"✍️ Escritura a {self.contract_id}: {data}")')
        lines.append('            return True')
        lines.append('        except Exception as e:')
        lines.append('            logger.error(f"❌ Error escribiendo a {self.contract_id}: {e}")')
        lines.append('            return False')
        lines.append('')
        lines.append('    def close(self) -> None:')
        lines.append('        """Cierra conexión al componente"""')
        lines.append('        logger.info(f"🔌 Driver {self.contract_id} cerrado")')
        
        return '\n'.join(lines)
    
    def generate_test_scaffold(self, contract: Dict) -> str:
        """Genera test unitario básico para el driver"""
        contract_id = contract["id"]
        contract_name = contract["name"]
        class_name = contract_name.replace(" ", "")
        
        # Construir template de forma segura
        lines = [
            '"""',
            f'Test para driver de {contract_name}',
            f'Generado automáticamente desde contrato: {contract_id}',
            '"""',
            '',
            'import pytest',
            f'from {contract_id}_driver import {class_name}Driver',
            '',
            '',
            f'def test_{contract_id}_initialization():',
            '    """Test de inicialización del driver"""',
            '    config = {"mode": "test"}',
            f'    driver = {class_name}Driver(config)',
            f'    assert driver.contract_id == "{contract_id}"',
            '',
            '',
            f'def test_{contract_id}_read():',
            '    """Test de lectura de datos"""',
            '    config = {"mode": "test"}',
            f'    driver = {class_name}Driver(config)',
            '    data = driver.read()',
            '',
            '    assert data is not None',
            '    assert "valid" in data',
            '    assert "timestamp" in data',
            '',
            '',
            f'def test_{contract_id}_close():',
            '    """Test de cierre del driver"""',
            '    config = {"mode": "test"}',
            f'    driver = {class_name}Driver(config)',
            '    driver.close()  # No debe lanzar excepciones',
        ]
        
        return '\n'.join(lines)
    
    def extract_metadata(self, contract: Dict) -> Dict:
        """Extrae metadatos relevantes del contrato"""
        metadata = {
            "id": contract["id"],
            "name": contract["name"],
            "type": contract["type"],
            "version": contract["version"],
            "protocol": contract.get("protocol", "unknown"),
            "fields_count": len(contract.get("fields", [])),
            "bus_prefix": contract.get("bus_prefix", contract["id"]),
        }
        
        # Extraer rangos y unidades de campos
        if "fields" in contract:
            metadata["fields"] = [
                {
                    "name": f["name"],
                    "unit": f.get("unit", "valor"),
                    "range": f.get("range"),
                    "type": f.get("data_type", "float"),
                }
                for f in contract["fields"]
            ]
        
        return metadata
    
    def get_status(self) -> Dict:
        """Retorna estado del parser"""
        return {
            "contracts_loaded": len(self.loaded_contracts),
            "contracts_dir": str(self.contracts_dir),
            "contract_ids": list(self.loaded_contracts.keys()),
        }
