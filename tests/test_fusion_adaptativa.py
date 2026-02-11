"""
═══════════════════════════════════════════════════════════════════════════════
TESTS: FUSIÓN ADAPTATIVA DE SENSORES WH65 + WH31
═══════════════════════════════════════════════════════════════════════════════

Suite de pruebas para la fusión adaptativa de sensores.
"""

import pytest
from core.sensors.adaptive_sensor_fusion import (
    media_adaptativa,
    detectar_anomalia,
    generar_alerta_anomalia,
    detectar_microclima,
    evaluar_sesgo_radiacion_wh65
)
from core.sensors.fusion_config import ConfiguracionFusion


class TestFusionAdaptativa:
    """Tests de fusión básica."""
    
    def test_media_confort_prioriza_wh31(self):
        """Test: Contexto confort prioriza WH31 (sombría)."""
        # WH65: 25°C (soleado)
        # WH31: 20°C (sombrío)
        # Contexto: confort (debería pesar más WH31)
        fusion = media_adaptativa(25.0, 50.0, 20.0, 60.0, contexto='confort')
        
        # Con pesos 0.3 WH65 + 0.7 WH31 = 0.3*25 + 0.7*20 = 7.5 + 14 = 21.5
        assert fusion.temperatura_media == pytest.approx(21.5, abs=0.1)
        assert fusion.peso_wh65_temp == 0.3
        assert fusion.peso_wh31_temp == 0.7
        assert not fusion.anomalia
    
    def test_media_lluvia_prioriza_wh65(self):
        """Test: Contexto lluvia prioriza WH65 (expuesto)."""
        fusion = media_adaptativa(25.0, 50.0, 20.0, 60.0, contexto='lluvia')
        
        # Con pesos 0.7 WH65 + 0.3 WH31 = 0.7*25 + 0.3*20 = 17.5 + 6 = 23.5
        assert fusion.temperatura_media == pytest.approx(23.5, abs=0.1)
        assert fusion.peso_wh65_temp == 0.7
        assert fusion.peso_wh31_temp == 0.3
        assert not fusion.anomalia
    
    def test_humedad_clamped_0_100(self):
        """Test: Humedad siempre clamped a [0, 100]."""
        fusion = media_adaptativa(20.0, 120.0, 20.0, 80.0, contexto='confort')
        assert 0 <= fusion.humedad_media <= 100
    
    def test_contexto_inexistente_usa_default(self):
        """Test: Contexto no reconocido usa default."""
        fusion = media_adaptativa(25.0, 50.0, 20.0, 60.0, contexto='contexto_inexistente')
        assert fusion.contexto == 'prediccion_general'


class TestDeteccionAnomalias:
    """Tests de detección de anomalías."""
    
    def test_anomalia_temperatura_grande(self):
        """Test: Diferencia de temperatura >15°C es anomalía."""
        anomalia, razon = detectar_anomalia(30.0, 50.0, 10.0, 60.0)
        assert anomalia
        assert "temperatura" in razon.lower()
    
    def test_anomalia_humedad_grande(self):
        """Test: Diferencia de humedad >40% es anomalía."""
        anomalia, razon = detectar_anomalia(20.0, 80.0, 20.0, 20.0)
        assert anomalia
        assert "humedad" in razon.lower()
    
    def test_no_anomalia_normal(self):
        """Test: Valores normales sin anomalía."""
        anomalia, razon = detectar_anomalia(20.0, 60.0, 18.0, 65.0)
        assert not anomalia
    
    def test_alerta_anomalia_generada(self):
        """Test: Se genera alerta cuando hay anomalía."""
        alerta = generar_alerta_anomalia(30.0, 50.0, 10.0, 60.0)
        assert alerta is not None
        assert alerta['tipo'] == 'anomalia_sensores'
        assert 'razon' in alerta


class TestDeteccionMicroclima:
    """Tests de detección de microclima."""
    
    def test_microclima_zona_fresca_humeda(self):
        """Test: Detectar zona fresca y húmeda (WH31)."""
        # WH65: 25°C, 50% H (soleado)
        # WH31: 20°C, 70% H (sombrío)
        microclima = detectar_microclima(25.0, 50.0, 20.0, 70.0)
        
        assert microclima is not None
        assert 'FRESCA' in microclima['tipo'] or 'HUMEDA' in microclima['tipo']
    
    def test_sin_microclima_differences_pequenas(self):
        """Test: Sin microclima si diferencias pequeñas."""
        # Diferencias < 3°C y < 15% H
        microclima = detectar_microclima(20.0, 60.0, 19.5, 62.0)
        assert microclima is None
    
    def test_microclima_recomendacion(self):
        """Test: Microclima incluye recomendación."""
        microclima = detectar_microclima(25.0, 50.0, 18.0, 75.0)
        assert microclima is not None
        assert 'recomendacion' in microclima


class TestSessionoRadiacion:
    """Tests de evaluación de sesgo por radiación."""
    
    def test_sesgo_probable_alta_radiacion(self):
        """Test: Sesgo probable con radiación alta y ΔT>3°C."""
        sesgo = evaluar_sesgo_radiacion_wh65(25.0, 20.0, radiacion_w_m2=600)
        assert sesgo['sesgo_radiacion_probable']
        assert 'Considerar usar WH31' in sesgo['recomendacion']
    
    def test_sin_sesgo_radiacion_baja(self):
        """Test: Sin sesgo si radiación baja."""
        sesgo = evaluar_sesgo_radiacion_wh65(25.0, 20.0, radiacion_w_m2=100)
        assert not sesgo['sesgo_radiacion_probable']


class TestConfiguracionDinamica:
    """Tests del gestor de configuración."""
    
    def test_obtener_ponderacion_confort(self):
        """Test: Obtener ponderación para contexto."""
        config = ConfiguracionFusion()
        peso_wh65 = config.obtener_peso_temperatura('confort', 'wh65')
        peso_wh31 = config.obtener_peso_temperatura('confort', 'wh31')
        
        assert peso_wh65 + peso_wh31 == pytest.approx(1.0, abs=0.001)
        assert 0 <= peso_wh65 <= 1
        assert 0 <= peso_wh31 <= 1
    
    def test_obtener_umbral_anomalia(self):
        """Test: Obtener umbrales de anomalía."""
        config = ConfiguracionFusion()
        umbral_temp = config.obtener_umbral_anomalia_temperatura()
        umbral_hum = config.obtener_umbral_anomalia_humedad()
        
        assert umbral_temp > 0
        assert umbral_hum > 0
    
    def test_recargar_configuracion(self):
        """Test: Recargar configuración."""
        config = ConfiguracionFusion()
        resultado = config.recargar()
        assert isinstance(resultado, bool)


# Script de prueba simple si se ejecuta directamente
if __name__ == "__main__":
    print("Ejecutando tests de fusión adaptativa...")
    pytest.main([__file__, "-v", "--tb=short"])
