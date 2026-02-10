"""
Tests para las mejoras TIER 1-3 (Config, ISA, Cache, etc.)
"""
import pytest
import json
import tempfile
from pathlib import Path

from core.system.constants import ESTACION


# ============================================================================
# TESTS [1.1] CONFIG DINÁMICA
# ============================================================================

def test_config_loader_basico():
    """Test que carga config_estacion.json correctamente."""
    from core.config.config_loader import ConfigEstacion
    
    config = ConfigEstacion("data/config_estacion.json")
    assert config.get("estacion.nombre") == "Argentona_V3"
    assert config.get("ubicacion.latitud_grados") == ESTACION.LATITUD
    assert config.get("ubicacion.longitud_grados") == ESTACION.LONGITUD


def test_config_ubicacion():
    """Test que obtiene datos de ubicación."""
    from core.config.config_loader import ConfigEstacion
    
    config = ConfigEstacion("data/config_estacion.json")
    ubi = config.get_ubicacion()
    
    assert ubi["latitud"] == ESTACION.LATITUD
    assert ubi["altitud_suelo_m"] == 105.0
    assert ubi["altura_sobre_suelo_m"] == 13.0
    assert ubi["altitud_sensor_m"] == ESTACION.ALTITUD


def test_config_terreno():
    """Test que obtiene datos de terreno."""
    from core.config.config_loader import ConfigEstacion
    
    config = ConfigEstacion("data/config_estacion.json")
    terreno = config.get_terreno()
    
    assert terreno["z0_calle_m"] == 0.5
    assert terreno["z0_terraza_m"] == 0.03
    assert terreno["tipo_terreno"] == "zona urbana costanera"


def test_config_get_con_ruta_puntos():
    """Test acceso con notación de puntos."""
    from core.config.config_loader import ConfigEstacion
    
    config = ConfigEstacion("data/config_estacion.json")
    
    # Acceso profundo
    lat = config.get("ubicacion.latitud_grados")
    assert lat == ESTACION.LATITUD
    
    # Con default
    valor = config.get("inexistente.valor.profundo", -999)
    assert valor == -999


# ============================================================================
# TESTS [1.2] ISA FALLBACK DINÁMICO
# ============================================================================

def test_isa_dinamica_nivel_mar():
    """Test ISA a nivel del mar (debe ser ~1013.25)."""
    from core.atmosphere.isa_calculator import presion_isa_dinamica
    
    p = presion_isa_dinamica(0)
    assert abs(p - 1013.25) < 0.01


def test_isa_dinamica_argentona():
    """Test ISA en Argentona (96 m)."""
    from core.atmosphere.isa_calculator import presion_isa_dinamica
    
    p = presion_isa_dinamica(96)
    # Debería ser ~1001.7 hPa (cálculo correcto de ISA)
    assert 1000 < p < 1003


def test_isa_dinamica_la_paz():
    """Test ISA en La Paz (3640 m) - caso crítico."""
    from core.atmosphere.isa_calculator import presion_isa_dinamica
    
    p = presion_isa_dinamica(3640)
    # Debería ser ~650 hPa (NO 1013.25 como antes!)
    assert 640 < p < 660
    # Verificar que NO es valor hardcodeado
    assert p != 1013.25


def test_presion_isa_fallback_con_persistencia():
    """Test que presion_fallback prefiere persistencia sobre ISA."""
    from core.atmosphere.isa_calculator import presion_isa_fallback
    
    # Con presión anterior válida
    p, razon = presion_isa_fallback(96, presion_ultima_valida=1010.5)
    assert p == 1010.5
    assert "persistencia" in razon
    
    # Sin presión anterior (usa ISA)
    p2, razon2 = presion_isa_fallback(96)
    assert 1000 < p2 < 1003  # ISA a 96m ≈ 1001.7 hPa
    assert "isa_dinamica" in razon2


def test_validar_presion_isa():
    """Test validación de presión vs ISA."""
    from core.atmosphere.isa_calculator import validar_presion_isa
    
    # Dentro de rango
    es_valida, msg = validar_presion_isa(1010.0, altitud_m=96)
    assert es_valida
    assert "OK" in msg
    
    # Fuera de rango (muy baja)
    es_valida2, msg2 = validar_presion_isa(800.0, altitud_m=96)
    assert not es_valida2
    assert "BAJA" in msg2


# ============================================================================
# TESTS [2.1] CACHÉ DE CONSTANTES
# ============================================================================

def test_cache_constantes_basico():
    """Test que caché almacena y retorna correctamente."""
    from core.indices.physics_engine_cached import CacheConstantes
    
    cache = CacheConstantes(ttl_segundos=60)
    
    # Set y Get
    cache.set("test_key", {"valor": 123})
    cached = cache.get("test_key")
    
    assert cached is not None
    assert cached["valor"] == 123


def test_cache_constantes_vencimiento():
    """Test que caché respeta TTL."""
    from core.indices.physics_engine_cached import CacheConstantes
    import time
    
    cache = CacheConstantes(ttl_segundos=1)  # 1 segundo
    cache.set("test_key", {"valor": 123})
    
    # Inmediato: debe estar en caché
    assert cache.get("test_key") is not None
    
    # Después de esperar: debe haber expirado
    time.sleep(1.1)
    assert cache.get("test_key") is None


def test_physics_engine_cached_basico():
    """Test que PhysicsEngineCached calcula y cachea."""
    from core.indices.physics_engine_cached import PhysicsEngineCached
    
    engine = PhysicsEngineCached(temperatura_k=288.15, presion_pa=101325,
                                 humedad_fraccion=0.5, ttl_segundos=60)
    
    # Primer cálculo (miss)
    c1 = engine.obtener_todas_constantes(altitud_m=0)
    assert c1 is not None
    # Verificar que contiene claves de constantes
    assert "densidad_aire_cipm_2007" in c1 or "conductividad_mason_saxena" in c1
    assert engine.cache.misses == 1
    
    # Segundo cálculo (hit)
    c2 = engine.obtener_todas_constantes(altitud_m=0)
    assert engine.cache.hits == 1


def test_physics_engine_cached_actualizar():
    """Test que actualizar parámetros limpia caché."""
    from core.indices.physics_engine_cached import PhysicsEngineCached
    
    engine = PhysicsEngineCached(temperatura_k=288.15, presion_pa=101325,
                                 humedad_fraccion=0.5)
    
    engine.obtener_todas_constantes()  # 1 miss
    assert engine.cache.misses == 1
    
    engine.actualizar_parametros(temperatura_k=300.0)  # Cambia T
    engine.obtener_todas_constantes()  # Debe recalcular (nueva miss)
    assert engine.cache.misses == 2


# ============================================================================
# TESTS [2.2] SENSOR VIRTUAL ALTURA
# ============================================================================

def test_sensor_virtual_altura_basico():
    """Test que sensor virtual almacena altura."""
    from core.sensors.sensor_virtual_altura import SensorVirtualAltura
    
    sensor = SensorVirtualAltura()
    sensor.altura_efectiva_m = 2.0
    sensor.z0_m = 0.5
    
    assert sensor.obtener_altura_efectiva() == 2.0
    assert sensor.obtener_z0() == 0.5


def test_sensor_virtual_altura_desde_contexto():
    """Test que sensor se actualiza desde contexto."""
    from core.sensors.sensor_virtual_altura import SensorVirtualAltura
    from core.context.contexto_maestro_global import ContextoMaestro
    
    contexto = ContextoMaestro(
        sensor_height_above_ground=5.0,
        elevation_ground=100.0,
        elevation_total=105.0
    )
    
    sensor = SensorVirtualAltura()
    sensor.actualizar_desde_contexto(contexto)
    
    assert sensor.altura_efectiva_m == 5.0
    assert sensor.elevacion_sensor_m == 105.0


# ============================================================================
# TESTS [3.1] VALIDACIÓN EN CASCADA
# ============================================================================

def test_validador_cascada_todo_ok():
    """Test validador cuando todos los sensores están OK."""
    from core.validation.sensor_validator_cascada import ValidadorCascada
    
    validador = ValidadorCascada()
    sensores = {
        "temperatura_c": 20.0,
        "humedad_pct": 65.0,
        "presion_hpa": 1010.0,
        "viento_ms": 3.5,
        "radiacion_w_m2": 500.0,  # Agregado para ET0
    }
    
    resultado = validador.validar_sensores(sensores)
    
    # Al menos debe haber algunos índices disponibles
    assert resultado["cascada_valida"]
    assert len(resultado["indices_disponibles"]) >= 3


def test_validador_cascada_presion_rota():
    """Test validador cuando presión está fuera de rango."""
    from core.validation.sensor_validator_cascada import ValidadorCascada
    
    validador = ValidadorCascada()
    sensores = {
        "temperatura_c": 20.0,
        "humedad_pct": 65.0,
        "presion_hpa": 50.0,  # ¡Fuera de rango!
        "viento_ms": 3.5,
    }
    
    resultado = validador.validar_sensores(sensores)
    
    assert not resultado["sensores_validos"]["presion_hpa"]
    assert "utci" in [b["indice"] for b in resultado["indices_bloqueados"]]
    assert "monin_obukhov" in [b["indice"] for b in resultado["indices_bloqueados"]]


def test_dependencia_sensor():
    """Test que dependencias están definidas correctamente."""
    from core.validation.sensor_validator_cascada import DependenciaSensor
    
    # UTCI depende de 4 sensores
    deps = DependenciaSensor.obtener_dependencias("utci")
    assert len(deps) == 4
    assert "temperatura" in deps
    assert "presion" in deps
    
    # Temperatura no depende de nada
    deps_temp = DependenciaSensor.obtener_dependencias("temperatura")
    assert len(deps_temp) == 0


# ============================================================================
# TESTS [3.2] DETECCIÓN DE OUTLIERS
# ============================================================================

def test_detector_outliers_iqr():
    """Test detección IQR de outliers."""
    from core.validation.outlier_detector import DetectorOutliers
    
    detector = DetectorOutliers(historial_max=100, iqr_multiplicador=1.5)
    
    # Agregar datos normales
    for i in range(20):
        detector.agregar_muestra("temperatura", 20.0 + i * 0.1)
    
    # Valor normal no debe detectar
    es_outlier, msg = detector.detectar_iqr("temperatura", 22.0)
    assert not es_outlier
    
    # Valor extremo debe detectar
    es_outlier2, msg2 = detector.detectar_iqr("temperatura", 100.0)
    assert es_outlier2


def test_detector_outliers_pegado():
    """Test detección de sensor pegado."""
    from core.validation.outlier_detector import DetectorOutliers
    
    detector = DetectorOutliers()
    
    # Agregar datos normales
    for i in range(5):
        detector.agregar_muestra("temperatura", 20.0 + i * 0.1)
    
    # Agregar 5 valores iguales (sensor pegado)
    for _ in range(5):
        detector.agregar_muestra("temperatura", 25.0)
    
    es_pegado, msg = detector.detectar_pegado("temperatura", 25.0)
    assert es_pegado
    assert "pegado" in msg


def test_detector_outliers_estadisticas():
    """Test estadísticas del detector."""
    from core.validation.outlier_detector import DetectorOutliers
    
    detector = DetectorOutliers()
    
    # Agregar datos
    for i in range(50):
        detector.agregar_muestra("temperatura", 20.0 + i * 0.5)
    
    stats = detector.obtener_estadisticas("temperatura")
    
    assert stats["muestras"] == 50
    assert "media" in stats
    assert "desv_std" in stats
    assert stats["minimo"] == 20.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
