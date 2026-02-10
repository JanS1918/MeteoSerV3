"""
Tests unitarios mínimos para detector, fallback e integraciones
"""

import pytest
from core.validation.anomaly_detector import AnomalyDetector
from core.validation.fallback_isa import FallbackISA


class MockBus:
    def __init__(self):
        self.data = {}

    def publicar(self, key, value, unit):
        self.data[key] = {"valor": value, "unidad": unit}


class MockSystem:
    def __init__(self):
        self.data = {"temperatura": 15.0, "humedad": 50.0, "presion_barometrica": 1013.0}
        self.location = {"latitud": 45.0, "altitud": 100.0}


class TestAnomalyDetector:
    
    @pytest.fixture
    def detector(self):
        bus = MockBus()
        system = MockSystem()
        return AnomalyDetector(bus, system)
    
    @pytest.mark.asyncio
    async def test_normal_measurement(self, detector):
        """Test que una medición normal retorna OK."""
        measurement = {"temperatura": 20.0, "humedad": 60.0, "presion_barometrica": 1013.0}
        result = await detector.detect(measurement)
        assert result["status"] == "OK"
        assert result["score"] < 0.5
    
    @pytest.mark.asyncio
    async def test_out_of_range_temperature(self, detector):
        """Test que temperatura fuera de rango retorna DUDOSO."""
        measurement = {"temperatura": 100.0, "humedad": 50.0, "presion_barometrica": 1013.0}
        result = await detector.detect(measurement)
        assert result["status"] == "DUDOSO"
        assert "valor_fuera_rango_fisico" in result["reasons"]
    
    @pytest.mark.asyncio
    async def test_temporal_jump(self, detector):
        """Test que salto temporal se detecta."""
        measurement1 = {"temperatura": 15.0, "humedad": 50.0, "presion_barometrica": 1013.0}
        measurement2 = {"temperatura": 35.0, "humedad": 50.0, "presion_barometrica": 1013.0}
        
        await detector.detect(measurement1)
        result = await detector.detect(measurement2)
        
        assert result["status"] == "DUDOSO"
        assert "salto_temporal_imposible" in result["reasons"]


class TestFallbackISA:
    
    @pytest.fixture
    def fallback(self):
        system = MockSystem()
        return FallbackISA(system, {"AUTO_FALLBACK": False})
    
    def test_isa_pressure_sea_level(self, fallback):
        """Test presión ISA a nivel del mar."""
        p = fallback.compute_isa_pressure(0)
        assert abs(p - 101325) < 1  # Tolerancia de 1 Pa
    
    def test_isa_temperature_sea_level(self, fallback):
        """Test temperatura ISA a nivel del mar."""
        t = fallback.compute_isa_temperature(0)
        assert abs(t - 15.0) < 0.1
    
    def test_isa_pressure_altitude(self, fallback):
        """Test presión ISA a 1000m."""
        p = fallback.compute_isa_pressure(1000)
        assert 85000 < p < 92000  # Rango aproximado
    
    @pytest.mark.asyncio
    async def test_fallback_suggest_mode(self, fallback):
        """Test que fallback en modo suggest no altera datos."""
        location = {"altitud": 100}
        result = await fallback.get_fallback("sensor_1", "presion", location, mode="suggest")
        
        assert result["source"] == "ISA_MODEL"
        assert result["mode"] == "suggest"
        assert result["value"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
