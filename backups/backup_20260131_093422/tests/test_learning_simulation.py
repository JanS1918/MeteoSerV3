import pytest

def test_learning_simulation_import():
    import core.learning.learning_simulation as m
    assert hasattr(m, "LearningEngine")
    assert hasattr(m, "SimulationEngine")