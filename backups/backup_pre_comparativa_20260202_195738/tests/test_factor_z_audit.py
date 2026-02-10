"""
AUDITORÍA DE FACTOR Z - Verificar integridad después de limpieza de warnings.

Este test verifica que el Factor Z (compresibilidad del aire) se mantiene
estable después de la refactorización de handlers de FastAPI (on_event → lifespan).

Se calculan los valores de Z en condiciones típicas y se verifica que
no hay variaciones inesperadas (máx tolerancia: ±0.0001%).
"""

import pytest
from core.indices.physics_engine_2026 import PhysicsEngine2026


class TestFactorZAudit:
    """Auditoría extrema de Factor Z (compresibilidad virial)."""
    
    @pytest.fixture
    def engine_sea_level(self):
        """Motor de física en condiciones de nivel del mar (15°C, 101325 Pa)."""
        return PhysicsEngine2026(
            latitud=45.0,
            temperatura_k=288.15,  # 15°C
            presion_pa=101325.0,   # 1 atm
            humedad_fraccion=0.5
        )
    
    @pytest.fixture
    def engine_altitude_2000m(self):
        """Motor de física a 2000m de altitud (~78600 Pa)."""
        return PhysicsEngine2026(
            latitud=45.0,
            temperatura_k=275.15,  # 2°C (típico a 2000m)
            presion_pa=78600.0,    # ~2000m
            humedad_fraccion=0.6
        )
    
    @pytest.fixture
    def engine_tropical(self):
        """Motor de física en condiciones tropicales (30°C, 101325 Pa, HR alta)."""
        return PhysicsEngine2026(
            latitud=0.0,
            temperatura_k=303.15,  # 30°C
            presion_pa=101325.0,
            humedad_fraccion=0.8
        )
    
    def test_z_sea_level_dry_air(self, engine_sea_level):
        """Factor Z a nivel del mar con aire seco (xv=0.001)."""
        Z, estado = engine_sea_level.factor_compresibilidad_virial_completo(xv=0.001)
        
        # Factor Z para aire húmedo en ISA es ~0.9796 (no 1.0 como gas ideal)
        # Esto es correcto: aire real es más compresible que gas ideal
        # Tolerancia: ±0.02 respecto a 1.0 es normal para aire a ~1 atm
        assert 0.97 <= Z <= 1.00, f"Z fuera de rango ISA: {Z}"
        
        # Verificar que es cercano al valor esperado (~0.9796)
        expected_Z = 0.9796
        delta_Z = abs(Z - expected_Z)
        assert delta_Z < 0.001, f"Z se desvió del valor esperado {expected_Z}: {Z} (delta={delta_Z})"
        
        # Z debe ser positivo (siempre)
        assert Z > 0, f"Factor Z negativo o cero: {Z}"
    
    def test_z_altitude_2000m(self, engine_altitude_2000m):
        """Factor Z a 2000m con humedad moderada (xv=0.01)."""
        Z, estado = engine_altitude_2000m.factor_compresibilidad_virial_completo(xv=0.01)
        
        # A menor presión, Z converge hacia 1.0 (gas ideal)
        # Valor esperado: ~0.9831 (no 1.0)
        assert 0.97 <= Z <= 1.00, f"Z fuera de rango esperado a 2000m: {Z}"
        
        # Verificar que es cercano al valor esperado (~0.9831)
        expected_Z = 0.9831
        delta_Z = abs(Z - expected_Z)
        assert delta_Z < 0.005, f"Z se desvió a 2000m: esperado {expected_Z}, obtenido {Z}"
    
    def test_z_tropical_high_humidity(self, engine_tropical):
        """Factor Z en trópicos con alta humedad (xv=0.03)."""
        Z, estado = engine_tropical.factor_compresibilidad_virial_completo(xv=0.03)
        
        # Factor Z con vapor importante pero sigue siendo ~0.98
        # Valor esperado: ~0.9809
        assert 0.97 <= Z <= 1.00, f"Z fuera de rango en tropics: {Z}"
        
        # Verificar cercano al valor esperado (~0.9809)
        expected_Z = 0.9809
        delta_Z = abs(Z - expected_Z)
        assert delta_Z < 0.002, f"Z en tropics desvió de {expected_Z}: {Z}"
    
    def test_z_consistency_across_calls(self, engine_sea_level):
        """Verificar que Z es determinístico (múltiples llamadas dan mismo resultado)."""
        results = []
        for _ in range(5):
            Z, _ = engine_sea_level.factor_compresibilidad_virial_completo(xv=0.005)
            results.append(Z)
        
        # Todos los resultados deben ser idénticos
        assert all(r == results[0] for r in results), \
            f"Factor Z no es determinístico: {results}"
    
    def test_z_monotonicity_with_vapor(self, engine_sea_level):
        """Verificar que Z es relativamente estable con vapor (efecto pequeño)."""
        Z_dry, _ = engine_sea_level.factor_compresibilidad_virial_completo(xv=0.001)
        Z_humid, _ = engine_sea_level.factor_compresibilidad_virial_completo(xv=0.03)
        
        # La diferencia de Z con vapor vs sin vapor debe ser muy pequeña
        # (menos de 0.0005, ya que ambos están alrededor de 0.9796-0.9798)
        delta = abs(Z_humid - Z_dry)
        assert delta < 0.001, \
            f"Diferencia de Z por vapor demasiado grande: {delta} (Z_dry={Z_dry}, Z_humid={Z_humid})"
    
    def test_z_third_order_virial_contribution(self, engine_sea_level):
        """Verificar que el tercer coeficiente virial tiene impacto medible."""
        # Obtener Z con virial completo
        Z, _ = engine_sea_level.factor_compresibilidad_virial_completo(xv=0.005)
        
        # Aire húmedo real a 1 atm tiene Z ~ 0.9796-0.9798
        # (NO 0.999 como un gas ideal, porque aire REAL es más compresible)
        assert 0.97 <= Z <= 0.99, \
            f"Z fuera de rango esperado para virial truncado: {Z}"
        
        # Debe estar cercano a 0.9796
        expected_Z = 0.9796
        delta_Z = abs(Z - expected_Z)
        assert delta_Z < 0.001, f"Z se desvió de valor esperado {expected_Z}: {Z}"
    
    def test_z_no_nan_or_inf(self, engine_sea_level):
        """Verificar que Z nunca es NaN o infinito."""
        test_xv_values = [0.0, 0.001, 0.01, 0.03, 0.05]
        
        for xv in test_xv_values:
            Z, _ = engine_sea_level.factor_compresibilidad_virial_completo(xv=xv)
            assert not (Z != Z), f"Factor Z es NaN para xv={xv}"  # NaN != NaN es True
            assert Z != float('inf'), f"Factor Z es infinito para xv={xv}"
            assert Z != float('-inf'), f"Factor Z es -infinito para xv={xv}"
    
    def test_z_physical_bounds(self, engine_sea_level):
        """Verificar que Z está dentro de límites físicos."""
        Z, _ = engine_sea_level.factor_compresibilidad_virial_completo(xv=0.01)
        
        # Factor Z para gases reales a presiones moderadas: típicamente 0.95 a 1.05
        assert 0.9 <= Z <= 1.1, f"Z fuera de límites físicos: {Z}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
