import pytest

def test_integration_manager_import():
    import core.integration.integration_manager as m
    assert hasattr(m, "IntegrationManager")