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
            logger.error(f"[ERROR] Contrato no encontrado: {contract_path}")
            return None
        
        try:
            content = path.read_text(encoding="utf-8")
            
            if path.suffix in (".json",):
                contract = json.loads(content)
            elif path.suffix in (".yaml", ".yml"):
                contract = yaml.safe_load(content)
            else:
                logger.error(f"[ERROR] Formato no soportado: {path.suffix}")
                return None
            
            # Validar schema básico
            is_valid, errors = self.validate_contract(contract)
            if is_valid:
                contract_id = contract.get("id", path.stem)
                self.loaded_contracts[contract_id] = contract
                logger.info(f"[OK] Contrato cargado: {contract_id}")
                return contract
            else:
                logger.error(f"[ERROR] Contrato inválido: {contract_path}")
                for error in errors:
                    logger.error(f"   - {error}")
                return None
                
        except Exception as e:
            logger.error(f"[ERROR] Error cargando contrato {contract_path}: {e}")
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
                logger.error(f"[ERROR] {error}")
                errors.append(error)
        
        # Validar tipo
        valid_types = ["sensor", "actuator", "service", "component"]
        if contract.get("type") not in valid_types:
            error = f"Tipo inválido: {contract.get('type')}"
            logger.error(f"[ERROR] {error}")
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

    def save_contract(self, contract: Dict, filename: Optional[str] = None) -> Optional[str]:
        """Persiste un contrato en disco (JSON por defecto)."""
        contract_id = contract.get("id")
        if not contract_id:
            logger.error("[ERROR] Contrato sin id, no se puede guardar")
            return None
        file_path = self.contracts_dir / (filename or f"{contract_id}.json")
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
            self.loaded_contracts[contract_id] = contract
            logger.info(f"[GUARDAR] Contrato guardado: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"[ERROR] Error guardando contrato {contract_id}: {e}")
            return None

    def update_contract(self, contract_id: str, updates: Dict[str, Any]) -> Optional[Dict]:
        """Actualiza un contrato existente y lo persiste."""
        contract = self.loaded_contracts.get(contract_id)
        if not contract:
            logger.error(f"[ERROR] Contrato no cargado: {contract_id}")
            return None
        contract.update(updates)
        saved_path = self.save_contract(contract)
        return contract if saved_path else None

    def delete_contract(self, contract_id: str) -> bool:
        """Elimina un contrato del disco y memoria."""
        contract_file = self.contracts_dir / f"{contract_id}.json"
        try:
            if contract_file.exists():
                contract_file.unlink()
            self.loaded_contracts.pop(contract_id, None)
            logger.info(f"🗑️ Contrato eliminado: {contract_id}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Error eliminando contrato {contract_id}: {e}")
            return False
    
    def generate_driver_scaffold(self, contract: Dict) -> str:
        """Genera scaffold de driver Python desde un contrato"""
        contract_id = contract["id"]
        contract_name = contract["name"]
        contract_type = contract["type"]
        protocol_info = contract.get("protocol", {})

        lines = [
            '"""',
            f'Driver para {contract_name}',
            f'Generado automáticamente desde contrato: {contract_id}',
            f'Tipo: {contract_type}',
        ]

        if protocol_info:
            if isinstance(protocol_info, dict):
                lines.append(f'Protocolo: {protocol_info.get("type", "unknown")}')
            else:
                lines.append(f'Protocolo: {protocol_info}')

        lines.extend([
            '"""',
            '',
            'import json',
            'import logging',
            'from datetime import datetime',
            'from pathlib import Path',
            'from typing import Dict, Any, Optional',
            'from urllib import request as _url_request',
            'from urllib.error import URLError',
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
            '        self.protocol = config.get("protocol") or {}',
            f'        self.default_protocol = {protocol_info!r}',
            '        logger.info(f"🔌 Driver {self.contract_id} inicializado")',
            '',
            '    def _get_protocol(self) -> Dict[str, Any]:',
            '        if isinstance(self.protocol, dict) and self.protocol:',
            '            return self.protocol',
            '        if isinstance(self.default_protocol, dict):',
            '            return self.default_protocol',
            '        return {"type": str(self.default_protocol)} if self.default_protocol else {}',
            '',
            '    def _read_from_file(self, path: str) -> Optional[Dict[str, Any]]:',
            '        try:',
            '            file_path = Path(path)',
            '            if not file_path.exists():',
            '                logger.error(f"[ERROR] Archivo no encontrado: {file_path}")',
            '                return None',
            '            return json.loads(file_path.read_text(encoding="utf-8"))',
            '        except Exception as e:',
            '            logger.error(f"[ERROR] Error leyendo archivo {path}: {e}")',
            '            return None',
            '',
            '    def _write_to_file(self, path: str, data: Dict[str, Any]) -> bool:',
            '        try:',
            '            file_path = Path(path)',
            '            file_path.parent.mkdir(parents=True, exist_ok=True)',
            '            file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")',
            '            return True',
            '        except Exception as e:',
            '            logger.error(f"[ERROR] Error escribiendo archivo {path}: {e}")',
            '            return False',
            '',
            '    def _read_from_http(self, url: str) -> Optional[Dict[str, Any]]:',
            '        try:',
            '            with _url_request.urlopen(url, timeout=10) as resp:',
            '                payload = resp.read().decode("utf-8")',
            '            return json.loads(payload)',
            '        except (URLError, json.JSONDecodeError) as e:',
            '            logger.error(f"[ERROR] Error HTTP leyendo {url}: {e}")',
            '            return None',
            '',
            '    def _write_to_http(self, url: str, data: Dict[str, Any]) -> bool:',
            '        try:',
            '            payload = json.dumps(data).encode("utf-8")',
            '            req = _url_request.Request(url, data=payload, headers={"Content-Type": "application/json"})',
            '            with _url_request.urlopen(req, timeout=10) as resp:',
            '                _ = resp.read()',
            '            return True',
            '        except URLError as e:',
            '            logger.error(f"[ERROR] Error HTTP escribiendo {url}: {e}")',
            '            return False',
            '',
            '    def _read_raw(self) -> Optional[Dict[str, Any]]:',
            '        proto = self._get_protocol()',
            '        proto_type = (proto.get("type") or "file").lower()',
            '        if proto_type == "file":',
            '            path = proto.get("path") or self.config.get("data_file")',
            '            if not path:',
            '                logger.error("[ERROR] Protocolo file requiere path o data_file")',
            '                return None',
            '            return self._read_from_file(path)',
            '        if proto_type in ("http", "https"):',
            '            url = proto.get("url") or self.config.get("url")',
            '            if not url:',
            '                logger.error("[ERROR] Protocolo HTTP requiere url")',
            '                return None',
            '            return self._read_from_http(url)',
            '        logger.error(f"[ERROR] Protocolo no soportado para lectura: {proto_type}")',
            '        return None',
            '',
            '    def _write_raw(self, data: Dict[str, Any]) -> bool:',
            '        proto = self._get_protocol()',
            '        proto_type = (proto.get("type") or "file").lower()',
            '        if proto_type == "file":',
            '            path = proto.get("path") or self.config.get("data_file")',
            '            if not path:',
            '                logger.error("[ERROR] Protocolo file requiere path o data_file")',
            '                return False',
            '            return self._write_to_file(path, data)',
            '        if proto_type in ("http", "https"):',
            '            url = proto.get("url") or self.config.get("url")',
            '            if not url:',
            '                logger.error("[ERROR] Protocolo HTTP requiere url")',
            '                return False',
            '            return self._write_to_http(url, data)',
            '        logger.error(f"[ERROR] Protocolo no soportado para escritura: {proto_type}")',
            '        return False',
        ])

        if "fields" in contract:
            for field in contract["fields"]:
                field_name = field["name"]
                field_unit = field.get("unit", "valor")
                field_method = field_name.lower().replace(" ", "_")
                lines.append('')
                lines.append(f'    def read_{field_method}(self) -> Optional[Any]:')
                lines.append(f'        """Lee {field_name} ({field_unit})"""')
                lines.append('        data = self.read()')
                lines.append(f'        return data.get("{field_name}") if data else None')

        lines.append('')
        lines.append('    def read(self) -> Optional[Dict[str, Any]]:')
        lines.append('        """Lee datos del sensor/componente"""')
        lines.append('        raw = self._read_raw()')
        lines.append('        if raw is None:')
        lines.append('            return None')
        lines.append('        data = dict(raw) if isinstance(raw, dict) else {}')
        lines.append('        data.setdefault("timestamp", datetime.utcnow().isoformat())')
        lines.append('        data.setdefault("valid", True)')

        if "fields" in contract:
            lines.append('        # Completar campos esperados del contrato')
            for field in contract["fields"]:
                field_name = field["name"]
                lines.append(f'        data.setdefault("{field_name}", None)')

        lines.append('        return data')
        lines.append('')
        lines.append('    def write(self, data: Dict[str, Any]) -> bool:')
        lines.append('        """Escribe datos al actuador/componente (si aplica)"""')
        lines.append('        payload = dict(data)')
        lines.append('        payload.setdefault("timestamp", datetime.utcnow().isoformat())')
        lines.append('        return self._write_raw(payload)')
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

    def generate_assets(self, contract_id: str, output_dir: str,
                        tests_dir: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Genera driver y tests para un contrato ya cargado y los guarda en disco."""
        contract = self.get_contract(contract_id)
        if not contract:
            return {"driver_path": None, "test_path": None, "error": "Contrato no cargado"}
        from .codegen import CodeGenerator
        generator = CodeGenerator()
        return generator.generate_driver_assets(contract, output_dir, tests_dir=tests_dir)
