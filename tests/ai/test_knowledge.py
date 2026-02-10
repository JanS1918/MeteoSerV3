"""
Tests para KnowledgeManager
"""

import pytest
import os
import json
import tempfile
import shutil
from core.ai.knowledge import KnowledgeManager


@pytest.fixture
def temp_data_dir():
    """Directorio temporal para tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_knowledge_manager_initialization(temp_data_dir):
    """Inicialización del knowledge manager"""
    km = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    assert os.path.exists(temp_data_dir)
    assert km.contracts == {}
    assert km.architecture == {}


def test_register_contract(temp_data_dir):
    """Registrar un contrato"""
    km = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    contract_data = {
        "id": "sensor_test",
        "name": "Test Sensor",
        "type": "sensor",
        "version": "1.0.0"
    }
    
    km.register_contract(contract_data)
    
    assert "sensor_test" in km.contracts
    retrieved = km.get_contract("sensor_test")
    assert retrieved["name"] == "Test Sensor"


def test_list_contracts(temp_data_dir):
    """Listar todos los contratos"""
    km = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    km.register_contract({
        "id": "sensor_1",
        "name": "Sensor 1",
        "type": "sensor",
        "version": "1.0"
    })
    
    km.register_contract({
        "id": "actuator_1",
        "name": "Actuator 1",
        "type": "actuator",
        "version": "1.0"
    })
    
    contracts = km.list_contracts()
    
    assert len(contracts) == 2


def test_update_architecture(temp_data_dir):
    """Actualizar arquitectura"""
    km = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    arch_data = {
        "modules": {
            "module_a": {"version": "1.0"},
            "module_b": {"version": "2.0"}
        }
    }
    
    km.update_architecture(arch_data)
    
    arch = km.get_architecture()
    assert "module_a" in arch["modules"]


def test_record_change(temp_data_dir):
    """Registrar cambios en el historial"""
    km = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    km.record_change("test_event", {"value": 123})
    
    history = km.get_history(limit=1)
    
    assert len(history) == 1
    assert history[0]["event_type"] == "test_event"


def test_set_rule(temp_data_dir):
    """Establecer reglas"""
    km = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    km.set_rule("max_temperature", 35.0)
    
    value = km.get_rule("max_temperature")
    assert value == 35.0


def test_search(temp_data_dir):
    """Buscar en el conocimiento"""
    km = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    km.register_contract({
        "id": "temp_sensor",
        "name": "Temperature Sensor",
        "type": "sensor",
        "version": "1.0",
        "description": "Measures ambient temperature"
    })
    
    results = km.search("temperature")
    
    assert "contracts" in results
    assert len(results["contracts"]) > 0


def test_persistence(temp_data_dir):
    """Verificar persistencia a disco"""
    km1 = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    km1.register_contract({
        "id": "persistent_contract",
        "name": "Persistent",
        "type": "sensor",
        "version": "1.0"
    })
    
    # Crear nuevo instance y verificar que carga desde disco
    km2 = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    contract = km2.get_contract("persistent_contract")
    assert contract is not None
    assert contract["name"] == "Persistent"


def test_history_limit(temp_data_dir):
    """El historial debe limitarse a 1000 entradas"""
    km = KnowledgeManager(knowledge_dir=temp_data_dir)
    
    # Añadir 1100 entradas
    for i in range(1100):
        km.record_change(f"event_{i}", {"index": i})
    
    history = km.get_history(limit=2000)
    
    # Debe tener máximo 1000
    assert len(history) <= 1000
