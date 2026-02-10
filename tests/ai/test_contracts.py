"""
Tests para ContractParser
"""

import pytest
import json
import tempfile
import os
from core.ai.contracts import ContractParser


@pytest.fixture
def temp_contracts_dir():
    """Directorio temporal para contratos de test"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_contract():
    """Contrato de ejemplo"""
    return {
        "id": "temp_sensor_v1",
        "name": "Temperature Sensor",
        "type": "sensor",
        "version": "1.0.0",
        "description": "Measures ambient temperature",
        "fields": [
            {
                "name": "temperature",
                "type": "float",
                "unit": "celsius",
                "range": [-40, 85]
            }
        ],
        "protocol": {
            "type": "i2c",
            "address": "0x48"
        }
    }


def test_parser_initialization():
    """Inicialización del parser"""
    parser = ContractParser()
    assert parser is not None


def test_validate_contract_valid(sample_contract):
    """Validar contrato válido"""
    parser = ContractParser()
    
    is_valid, errors = parser.validate_contract(sample_contract)
    
    assert is_valid is True
    assert len(errors) == 0


def test_validate_contract_missing_required():
    """Detectar campos obligatorios faltantes"""
    parser = ContractParser()
    
    invalid_contract = {
        "name": "Test",
        # Falta id, type, version
    }
    
    is_valid, errors = parser.validate_contract(invalid_contract)
    
    assert is_valid is False
    assert len(errors) > 0


def test_validate_contract_invalid_type():
    """Detectar tipo de contrato inválido"""
    parser = ContractParser()
    
    invalid_contract = {
        "id": "test",
        "name": "Test",
        "type": "invalid_type",  # Tipo no válido
        "version": "1.0"
    }
    
    is_valid, errors = parser.validate_contract(invalid_contract)
    
    assert is_valid is False
    assert "type" in str(errors).lower()


def test_load_contract_json(temp_contracts_dir, sample_contract):
    """Cargar contrato desde archivo JSON"""
    parser = ContractParser()
    
    # Crear archivo JSON
    contract_file = os.path.join(temp_contracts_dir, "sensor.json")
    with open(contract_file, 'w') as f:
        json.dump(sample_contract, f)
    
    loaded_contract = parser.load_contract(contract_file)
    
    assert loaded_contract["id"] == sample_contract["id"]
    assert loaded_contract["name"] == sample_contract["name"]


def test_scan_contracts_dir(temp_contracts_dir, sample_contract):
    """Escanear directorio de contratos"""
    parser = ContractParser()
    
    # Crear múltiples contratos
    for i in range(3):
        contract = sample_contract.copy()
        contract["id"] = f"sensor_{i}"
        
        contract_file = os.path.join(temp_contracts_dir, f"sensor_{i}.json")
        with open(contract_file, 'w') as f:
            json.dump(contract, f)
    
    contracts = parser.scan_contracts_dir(temp_contracts_dir)
    
    assert len(contracts) == 3


def test_generate_driver_scaffold(sample_contract):
    """Generar scaffold de driver"""
    parser = ContractParser()
    
    driver_code = parser.generate_driver_scaffold(sample_contract)
    
    assert "class TemperatureSensorDriver" in driver_code
    assert "def read_temperature" in driver_code
    assert "i2c" in driver_code.lower()


def test_generate_test_scaffold(sample_contract):
    """Generar scaffold de test"""
    parser = ContractParser()
    
    test_code = parser.generate_test_scaffold(sample_contract)
    
    assert "def test_" in test_code
    assert "assert" in test_code
    assert sample_contract["name"] in test_code or "driver" in test_code.lower()


def test_extract_metadata(sample_contract):
    """Extraer metadata del contrato"""
    parser = ContractParser()
    
    metadata = parser.extract_metadata(sample_contract)
    
    assert "fields" in metadata
    assert len(metadata["fields"]) == 1
    assert metadata["fields"][0]["name"] == "temperature"
    assert metadata["protocol"]["type"] == "i2c"
