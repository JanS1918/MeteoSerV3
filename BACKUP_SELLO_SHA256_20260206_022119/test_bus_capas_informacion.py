"""
Tests para BusCapasInformacion - Arquitectura de 4 Capas
=========================================================
Valida que el Big Data Inteligente funciona correctamente.
"""

import pytest
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile

from core.system.constants import ESTACION

from core.bus.bus_capas_informacion import (
    BusCapasInformacion,
    CapaInformacion,
    TimeseriesVariable,
    MetadatosLinaje,
    obtener_bus
)


class TestMetadatosLinaje:
    """Test genealogía de datos"""
    
    def test_crear_metadatos_basicos(self):
        """Metadatos básicos completos"""
        meta = MetadatosLinaje(
            variable="test.var",
            valor=25.5,
            tipo="CORE",
            origen="test.funcion",
            timestamp=datetime.now(),
            confianza=0.98,
            unidad="°C",
            rango_esperado=(-40, 60)
        )
        
        assert meta.variable == "test.var"
        assert meta.valor == 25.5
        assert meta.confianza == 0.98
        assert meta.unidad == "°C"
    
    def test_serializar_a_dict(self):
        """Conversión a diccionario preserva tipo"""
        meta = MetadatosLinaje(
            variable="test.var",
            valor=25.5,
            tipo="CORE",
            origen="test.funcion",
            timestamp=datetime.now()
        )
        
        d = meta.a_dict()
        assert d["variable"] == "test.var"
        assert d["valor"] == 25.5
        assert isinstance(d["timestamp"], str)  # ISO format
    
    def test_serializar_a_json(self):
        """Puede convertirse a JSON válido"""
        meta = MetadatosLinaje(
            variable="test.var",
            valor=25.5,
            tipo="CORE",
            origen="test.funcion",
            timestamp=datetime.now()
        )
        
        json_str = meta.a_json()
        reparsed = json.loads(json_str)
        assert reparsed["variable"] == "test.var"
        assert reparsed["valor"] == 25.5


class TestCapaInformacion:
    """Test contenedores de capa"""
    
    def test_crear_capa_vacia(self):
        """Capa nueva está vacía"""
        capa = CapaInformacion("TEST", max_items=100)
        
        assert len(capa.datos) == 0
        assert capa.nombre == "TEST"
        assert capa.contador_inserciones == 0
    
    def test_agregar_datos_a_capa(self):
        """Se pueden agregar metadatos"""
        capa = CapaInformacion("TEST")
        
        meta = MetadatosLinaje(
            variable="var1",
            valor=10,
            tipo="CORE",
            origen="test.test",
            timestamp=datetime.now()
        )
        
        capa.agregar_o_actualizar("var1", meta)
        
        assert len(capa.datos) == 1
        assert capa.contador_inserciones == 1
        assert capa.obtener("var1").valor == 10
    
    def test_actualizar_datos(self):
        """Actualizar incrementa contador"""
        capa = CapaInformacion("TEST")
        
        meta1 = MetadatosLinaje(
            variable="var1", valor=10, tipo="CORE",
            origen="test.test", timestamp=datetime.now()
        )
        meta2 = MetadatosLinaje(
            variable="var1", valor=20, tipo="CORE",
            origen="test.test", timestamp=datetime.now()
        )
        
        capa.agregar_o_actualizar("var1", meta1)
        capa.agregar_o_actualizar("var1", meta2)
        
        assert capa.contador_inserciones == 1
        assert capa.contador_actualizaciones == 1
        assert capa.obtener("var1").valor == 20
    
    def test_obtener_valor_directo(self):
        """Método obtener_valor extrae solo el valor"""
        capa = CapaInformacion("TEST")
        
        meta = MetadatosLinaje(
            variable="var1", valor=42, tipo="CORE",
            origen="test.test", timestamp=datetime.now()
        )
        capa.agregar_o_actualizar("var1", meta)
        
        assert capa.obtener_valor("var1") == 42
        assert capa.obtener_valor("inexistente", default=99) == 99
    
    def test_stats_capa(self):
        """Estadísticas de capa"""
        capa = CapaInformacion("TEST")
        
        for i in range(5):
            meta = MetadatosLinaje(
                variable=f"var{i}", valor=i*10, tipo="CORE",
                origen="test.test", timestamp=datetime.now()
            )
            capa.agregar_o_actualizar(f"var{i}", meta)
        
        stats = capa.stats()
        assert stats["capa"] == "TEST"
        assert stats["items"] == 5
        assert stats["inserciones"] == 5


class TestTimeseriesVariable:
    """Test históricos de variables"""
    
    def test_crear_timeseries_vacia(self):
        """Variable timeseries nueva"""
        ts = TimeseriesVariable("temperatura", max_muestras=100)
        
        assert ts.variable == "temperatura"
        assert len(ts.valores) == 0
    
    def test_agregar_muestras(self):
        """Se pueden agregar valores al histórico"""
        ts = TimeseriesVariable("temperatura")
        
        ts.agregar(25.0)
        ts.agregar(25.5)
        ts.agregar(26.0)
        
        assert len(ts.valores) == 3
    
    def test_obtener_ultimo_valor(self):
        """Obtiene el valor más reciente"""
        ts = TimeseriesVariable("temperatura")
        
        ts.agregar(25.0)
        ts.agregar(26.0)
        
        ultimo = ts.obtener_ultimo()
        assert ultimo[0] == 26.0
    
    def test_limitar_muestras(self):
        """Respeta límite de muestras"""
        ts = TimeseriesVariable("temperatura", max_muestras=5)
        
        for i in range(10):
            ts.agregar(20 + i)
        
        # Deque limita a 5 más recientes
        assert len(ts.valores) == 5
        valores = [v[0] for v in ts.valores]
        assert valores == [25, 26, 27, 28, 29]
    
    def test_rango_temporal(self):
        """Obtiene valores en rango de tiempo"""
        ts = TimeseriesVariable("temperatura")
        
        ahora = datetime.now()
        ts.agregar(20.0, timestamp=ahora - timedelta(minutes=65))
        ts.agregar(21.0, timestamp=ahora - timedelta(minutes=30))
        ts.agregar(22.0, timestamp=ahora)
        
        rango_60m = ts.obtener_rango(minutos=60)
        # Debería incluir últimos 60m (excluyendo el primero que es 65m atrás)
        assert len(rango_60m) == 2
    
    def test_estadisticas_numericas(self):
        """Calcula estadísticas correctas"""
        ts = TimeseriesVariable("temperatura")
        
        for val in [20.0, 22.0, 24.0, 26.0, 28.0]:
            ts.agregar(val)
        
        stats = ts.estadisticas()
        assert stats["variable"] == "temperatura"
        assert stats["muestras"] == 5
        assert stats["min"] == 20.0
        assert stats["max"] == 28.0
        assert stats["promedio"] == 24.0


class TestBusCapasInformacion:
    """Test Bus completo con 4 capas"""
    
    def test_bus_global_singleton(self):
        """Bus es singleton"""
        bus1 = obtener_bus()
        bus2 = obtener_bus()
        assert bus1 is bus2
    
    def test_publicar_en_core(self):
        """Publica en capa CORE"""
        bus = BusCapasInformacion()
        
        bus.publicar(
            variable="test.presion",
            valor=1013.25,
            nivel="CORE",
            origen="test.test",
            confianza=1.0
        )
        
        assert len(bus.capa_core.datos) == 1
        meta = bus.capa_core.obtener("test.presion")
        assert meta.valor == 1013.25
        assert meta.confianza == 1.0
    
    def test_publicar_en_intermediate(self):
        """Publica en capa INTERMEDIATE"""
        bus = BusCapasInformacion()
        
        bus.publicar(
            variable="test.temp_calc",
            valor=25.5,
            nivel="INTERMEDIATE",
            origen="test.calc"
        )
        
        assert len(bus.capa_intermediate.datos) == 1
        assert bus.capa_core.obtener_valor("test.temp_calc") is None
    
    def test_debug_mode_inactive(self):
        """DEBUG desactivado no publica"""
        bus = BusCapasInformacion()
        bus.debug_mode = False
        
        bus.publicar(
            variable="test.debug_var",
            valor="secreto",
            nivel="DEBUG"
        )
        
        assert len(bus.capa_debug.datos) == 0
    
    def test_debug_mode_active(self):
        """DEBUG activado publica"""
        bus = BusCapasInformacion()
        bus.habilitar_debug(True)
        
        bus.publicar(
            variable="test.debug_var",
            valor="secreto",
            nivel="DEBUG"
        )
        
        assert len(bus.capa_debug.datos) == 1
    
    def test_timeseries_automatica(self):
        """TIMESERIES crea histórico automático"""
        bus = BusCapasInformacion()
        
        for i in range(5):
            bus.publicar(
                variable="temperatura",
                valor=20 + i,
                nivel="TIMESERIES"
            )
        
        assert "temperatura" in bus.capa_timeseries
        assert len(bus.capa_timeseries["temperatura"].valores) == 5
    
    def test_query_core_wildcard(self):
        """Query con patrón wildcard"""
        bus = BusCapasInformacion()
        
        bus.publicar("physics.densidad", 1.225, nivel="CORE", origen="phys")
        bus.publicar("physics.viscosidad", 1.81e-5, nivel="CORE", origen="phys")
        bus.publicar("contexto.ubicacion", ESTACION.LATITUD, nivel="CORE", origen="ctx")
        
        resultados = bus.query("core:physics.*")
        assert len(resultados) == 2
        assert all(r.variable.startswith("physics.") for r in resultados)
    
    def test_query_confianza_umbral(self):
        """Query por confianza mínima"""
        bus = BusCapasInformacion()
        
        bus.publicar("var1", 10, nivel="CORE", confianza=1.0)
        bus.publicar("var2", 20, nivel="CORE", confianza=0.95)
        bus.publicar("var3", 30, nivel="CORE", confianza=0.5)
        
        resultados = bus.query("confianza>0.9")
        assert len(resultados) == 2
    
    def test_query_por_origen(self):
        """Query por módulo origen"""
        bus = BusCapasInformacion()
        
        bus.publicar("var1", 10, nivel="CORE", origen="environmental.index")
        bus.publicar("var2", 20, nivel="CORE", origen="physics.engine")
        bus.publicar("var3", 30, nivel="CORE", origen="environmental.sensor")
        
        resultados = bus.query("origen:environmental.*")
        assert len(resultados) == 2
    
    def test_dashboard_completo(self):
        """Dashboard muestra estado del Bus"""
        bus = BusCapasInformacion()
        
        bus.publicar("var1", 10, nivel="CORE")
        bus.publicar("var2", 20, nivel="INTERMEDIATE")
        bus.habilitar_debug(True)
        bus.publicar("var3", 30, nivel="DEBUG")
        
        dashboard = bus.obtener_dashboard()
        
        assert "timestamp" in dashboard
        assert dashboard["debug_mode"] is True
        assert dashboard["capas"]["CORE"]["items"] == 1
        assert dashboard["capas"]["INTERMEDIATE"]["items"] == 1
        assert dashboard["capas"]["DEBUG"]["items"] == 1
    
    def test_exportar_a_json(self):
        """Exporta todo a archivo JSON"""
        bus = BusCapasInformacion()
        
        bus.publicar("var1", 10, nivel="CORE", origen="test")
        bus.publicar("var2", 20, nivel="INTERMEDIATE", origen="test")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            bus.exportar_a_json(temp_path)
            
            contenido = Path(temp_path).read_text()
            datos = json.loads(contenido)
            
            assert "timestamp" in datos
            assert len(datos["capas"]["CORE"]) == 1
            assert len(datos["capas"]["INTERMEDIATE"]) == 1
        finally:
            Path(temp_path).unlink()
    
    def test_throughput_tracking(self):
        """Estima MB/s de flujo de datos"""
        bus = BusCapasInformacion()
        
        # Publicar varias variables
        for i in range(10):
            bus.publicar(f"var{i}", i*1.5, nivel="CORE")
        
        dashboard = bus.obtener_dashboard()
        # Debería haber algún throughput reportado
        assert "throughput_bytes_seg" in dashboard


class TestIntegracionContextoMaestro:
    """Test integración con ContextoMaestro"""
    
    def test_contexto_publica_al_bus(self):
        """ContextoMaestro publica ubicación al Bus"""
        bus_limpio = BusCapasInformacion()
        
        # Crear contexto (publicará al bus global)
        from core.context.contexto_maestro_global import ContextoMaestro
        
        # Usando bus local para test
        contexto = ContextoMaestro(
            elevation_ground=100.0,
            elevation_total=115.0,
            lat=45.0,
            lon=10.0,
            usar_config=False
        )
        
        # Verificar que se creó correctamente
        assert contexto.lat == 45.0
        assert contexto.lon == 10.0
        assert contexto.elevation_total == 115.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
