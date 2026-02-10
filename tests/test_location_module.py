"""
✅ Tests de Validación - Módulo de Ubicación y Astronomía

Verifica que:
1. El módulo de ubicación funciona correctamente
2. Detecta ubicación en múltiples fuentes
3. Calcula correctamente radiación teórica
4. Los amanecer/atardecer son coherentes
5. No hay pérdida de funcionalidades
"""

import pytest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.location import (
    coords_valid,
    parse_coord,
    coords_es_spain,
    detect_location,
    arco_solar,
    radiacion_teorica,
    hhmm_a_minutos,
    minutos_a_hhmm,
)


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE VALIDACIÓN BÁSICA
# ═══════════════════════════════════════════════════════════════════════════

class TestCoordsValidation:
    """Testa validación de coordenadas."""
    
    def test_coords_valid_true(self):
        """Coordenadas válidas."""
        assert coords_valid(41.553267, 2.396845) is True  # Argentona
        assert coords_valid(40.4168, -3.7038) is True     # Madrid
        assert coords_valid(0, 0) is True                 # Ecuador/Meridiano
        assert coords_valid(-90, 0) is True               # Polo sur
        assert coords_valid(90, 180) is True              # Polo norte
    
    def test_coords_valid_false(self):
        """Coordenadas inválidas."""
        assert coords_valid(91, 0) is False               # Lat fuera de rango
        assert coords_valid(0, 181) is False              # Lon fuera de rango
        assert coords_valid(None, 0) is False             # Lat None
        assert coords_valid(0, None) is False             # Lon None
        assert coords_valid(None, None) is False
        assert coords_valid("abc", "xyz") is False
    
    def test_coords_as_strings(self):
        """Coordenadas como strings (sin comas)."""
        assert coords_valid("41.5", "2.4") is True
        assert coords_valid("41.5507", "-2.396845") is True
        # Nota: coords_valid NO procesa comas, solo parse_coord lo hace


class TestParseCoord:
    """Tests de parseo de coordenadas."""
    
    def test_parse_decimal(self):
        """Parsear formato decimal."""
        assert parse_coord("41.5507") == 41.5507
        assert parse_coord("2.396845") == 2.396845
        assert parse_coord("-2.396845") == -2.396845
    
    def test_parse_coma_decimal(self):
        """Parsear con coma decimal."""
        assert parse_coord("41,5507") == 41.5507
        assert parse_coord("2,396845") == 2.396845
    
    def test_parse_with_cardinal(self):
        """Parsear con cardinales."""
        assert parse_coord("41.5507N") == 41.5507
        assert parse_coord("41.5507n") == 41.5507
        assert parse_coord("41.5507S") == -41.5507
        assert parse_coord("41.5507s") == -41.5507
        assert parse_coord("2.3968E") == 2.3968
        assert parse_coord("2.3968W") == -2.3968
        assert parse_coord("2.3968O") == -2.3968    # Oeste
    
    def test_parse_invalid(self):
        """Parsear inválido."""
        assert parse_coord(None) is None
        assert parse_coord("abc") is None
        assert parse_coord("") is None


class TestCoordsEsSpain:
    """Tests de validación España."""
    
    def test_spain_true(self):
        """Coordenadas dentro de España."""
        assert coords_es_spain(41.553267, 2.396845) is True  # Argentona
        assert coords_es_spain(40.4168, -3.7038) is True     # Madrid
        assert coords_es_spain(43.2965, -8.2283) is True     # Galicia
        assert coords_es_spain(39.5696, 2.6502) is True      # Mallorca
    
    def test_spain_false(self):
        """Coordenadas fuera de España."""
        assert coords_es_spain(48.856614, 2.352222) is False  # París
        assert coords_es_spain(40.7128, -74.0060) is False    # Nueva York
        assert coords_es_spain(51.5074, -0.1278) is False     # Londres
        assert coords_es_spain(0, 0) is False                 # Ecuador
        assert coords_es_spain("abc", "xyz") is False


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE CÁLCULOS ASTRONÓMICOS
# ═══════════════════════════════════════════════════════════════════════════

class TestArcoSolar:
    """Tests de cálculo de arco solar."""
    
    def test_arco_solar_equinoccio(self):
        """Arco solar en equinoccios (≈ 180°)."""
        # 21 de marzo (día 80) - equinoccio
        arc_march = arco_solar(41.5, 80)
        assert 170 <= arc_march <= 190  # Aproximadamente 180°
        
        # 21 de septiembre (día 264) - equinoccio
        arc_sept = arco_solar(41.5, 264)
        assert 170 <= arc_sept <= 190
    
    def test_arco_solar_solsticio_verano(self):
        """Arco solar en solsticio de verano (máximo)."""
        # 21 de junio (día 172)
        arc_summer = arco_solar(41.5, 172)
        assert arc_summer > 180  # Más largo que equinoccio
        assert arc_summer < 300
    
    def test_arco_solar_solsticio_invierno(self):
        """Arco solar en solsticio de invierno (mínimo)."""
        # 21 de diciembre (día 355)
        arc_winter = arco_solar(41.5, 355)
        assert arc_winter < 180  # Más corto que equinoccio
        assert arc_winter > 0
    
    def test_arco_solar_ecuador(self):
        """Arco solar en Ecuador (siempre ≈ 180°)."""
        for day in [1, 80, 172, 264, 355]:
            arc = arco_solar(0, day)
            assert 175 <= arc <= 185  # Casi constante


class TestRadiacionTeorica:
    """Tests de radiación teórica."""
    
    def test_radiacion_mediodia(self):
        """Radiación máxima al mediodía."""
        # Día del equinoccio, mediodía, latitud moderada
        rad_noon = radiacion_teorica(41.5, 80, 12.0)
        assert rad_noon > 500  # Debe ser significativa
    
    def test_radiacion_noche(self):
        """Radiación nula de noche."""
        # Mediodía UTC-8 (madrugada en España)
        rad_night = radiacion_teorica(41.5, 80, 4.0)
        assert rad_night == 0  # El sol está bajo el horizonte
    
    def test_radiacion_amanecer_atardecer(self):
        """Radiación baja en amanecer/atardecer."""
        rad_dawn = radiacion_teorica(41.5, 80, 6.0)   # Amanecer aprox
        rad_dusk = radiacion_teorica(41.5, 80, 18.0)  # Atardecer aprox
        assert 0 <= rad_dawn < 200
        assert 0 <= rad_dusk < 200


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE UTILIDADES DE TIEMPO
# ═══════════════════════════════════════════════════════════════════════════

class TestTimeConversions:
    """Tests de conversiones HH:MM ↔ minutos."""
    
    def test_hhmm_a_minutos(self):
        """Convertir HH:MM a minutos."""
        assert hhmm_a_minutos("00:00") == 0
        assert hhmm_a_minutos("06:15") == 375
        assert hhmm_a_minutos("12:30") == 750
        assert hhmm_a_minutos("23:59") == 1439
    
    def test_hhmm_a_minutos_invalid(self):
        """HH:MM inválido."""
        assert hhmm_a_minutos(None) is None
        assert hhmm_a_minutos("") is None
        assert hhmm_a_minutos("abc") is None
        # Nota: "25:00" retorna 1500 (no hace wrap, lo hace minutos_a_hhmm)
    
    def test_minutos_a_hhmm(self):
        """Convertir minutos a HH:MM."""
        assert minutos_a_hhmm(0) == "00:00"
        assert minutos_a_hhmm(375) == "06:15"
        assert minutos_a_hhmm(750) == "12:30"
        assert minutos_a_hhmm(1439) == "23:59"
    
    def test_minutos_a_hhmm_wrap(self):
        """Minutos con wrap."""
        assert minutos_a_hhmm(1440) == "00:00"  # 24h = 0h
        assert minutos_a_hhmm(1500) == "01:00"  # 25h = 1h
    
    def test_roundtrip_conversion(self):
        """Test roundtrip HH:MM → min → HH:MM."""
        for hhmm in ["06:15", "12:30", "23:59", "00:00"]:
            minutos = hhmm_a_minutos(hhmm)
            hhmm_back = minutos_a_hhmm(minutos)
            assert hhmm_back == hhmm


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN
# ═══════════════════════════════════════════════════════════════════════════

class TestDetectLocationIntegration:
    """Tests de detección de ubicación."""
    
    def test_detect_location_fallback(self):
        """Detección fallback (sin config, sin sensores)."""
        class FakeSystem:
            sensores = {}
        
        loc = detect_location(FakeSystem())
        assert loc["lat"] == 41.553267  # Argentona (fallback)
        assert loc["lon"] == 2.396845
        assert loc["origen"] == "fallback"
    
    def test_detect_location_with_sensores(self):
        """Detección desde sensores."""
        class FakeSystem:
            sensores = {"latitud": "41.553267", "longitud": "2.396845"}
        
        loc = detect_location(FakeSystem())
        assert loc["lat"] == 41.553267
        assert loc["lon"] == 2.396845
        assert loc["origen"] == "sensor"


# ═══════════════════════════════════════════════════════════════════════════
# TESTS SMOKE (Funcionalidad básica)
# ═══════════════════════════════════════════════════════════════════════════

def test_smoke_import():
    """Smoke test: módulo se importa sin errores."""
    assert coords_valid is not None
    assert parse_coord is not None
    assert arco_solar is not None
    assert radiacion_teorica is not None


def test_smoke_argentona():
    """Smoke test: Cálculos en Argentona."""
    # Argumentona: 41.5507°N, 2.3968°E
    today = datetime.now().timetuple().tm_yday
    
    # Cálculos
    arc = arco_solar(41.5507, today)
    rad = radiacion_teorica(41.5507, today, 12.0)
    
    assert arc > 0
    assert rad > 0  # Al mediodía debe haber radiación


def test_integration_full_flow():
    """Smoke test: flujo completo."""
    # 1. Detectar ubicación
    class FakeSystem:
        sensores = {}
    
    loc = detect_location(FakeSystem())
    assert coords_valid(loc["lat"], loc["lon"])
    
    # 2. Calcular arco solar
    today = datetime.now().timetuple().tm_yday
    arc = arco_solar(loc["lat"], today)
    assert arc > 0
    
    # 3. Calcular radiación
    rad = radiacion_teorica(loc["lat"], today, 12.0)
    assert rad >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
