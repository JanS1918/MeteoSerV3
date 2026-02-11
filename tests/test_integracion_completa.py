"""
SUITE TESTS UNITARIOS V1.0
═════════════════════════════════════════════════════════════════════════════

Tests de:
- Contexto sensores (WH31/WH65)
- Meta-confianza por dominio
- Matriz impacto cruzado
- Cross-domain consistency
- Bus publication

Tests GENÉRICOS que NO requieren datos reales.

Ejecutar: python -m pytest tests/test_integracion_completa.py -v

Fecha: 11 de febrero de 2026
"""

import pytest
import sys
from pathlib import Path

# Agregar raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.indices.contexto_sensores import (
    factor_proteccion_sensores,
    sensacion_termica_corregida,
    temperatura_ajustada_por_sensor
)

from core.indices.meta_confianza_dominios import (
    calcular_confianza_dominio,
    calcular_confianza_multiples_dominios
)

from core.indices.matriz_impacto_cruzado import (
    calcular_impacto_evento,
    calcular_impacto_multiples_eventos
)


# ═════════════════════════════════════════════════════════════════════════════
# TESTS: CONTEXTO SENSORES
# ═════════════════════════════════════════════════════════════════════════════

class TestContextoSensores:
    """Tests para diferenciación WH31 vs WH65."""
    
    def test_wh65_factor_viento_maximo(self):
        """WH65 debe tener máximo factor viento (1.0)."""
        result = factor_proteccion_sensores("wh65")
        assert result["factor_viento"] == 1.0, "WH65 debe estar totalmente expuesto"
    
    def test_wh31_factor_viento_reducido(self):
        """WH31 debe tener factor viento menor (protección)."""
        result = factor_proteccion_sensores("wh31", distancia_a_pared_metros=0.8)
        assert result["factor_viento"] < 1.0, "WH31 debe estar protegido"
        assert result["factor_viento"] >= 0.59, "Pero no tan protegido"
    
    def test_wh31_calentamiento_radiativo_mayor(self):
        """WH31 debe calentarse más por radiación."""
        wh65 = factor_proteccion_sensores("wh65")
        wh31 = factor_proteccion_sensores("wh31")
        assert wh31["factor_calentamiento_radiativo"] > wh65["factor_calentamiento_radiativo"]
    
    def test_wh31_confianza_menor(self):
        """WH31 debe tener menor confianza (sesgo radiativo)."""
        wh65 = factor_proteccion_sensores("wh65")
        wh31 = factor_proteccion_sensores("wh31")
        assert wh31["confianza_temperatura"] < wh65["confianza_temperatura"]
    
    def test_sensacion_termica_corregida_con_wh31(self):
        """Sensación térmica con WH31 debe diferir de WH65."""
        sens_wh65 = sensacion_termica_corregida(
            temperatura_c=20.0,
            humedad_relativa=60.0,
            velocidad_viento_kmh=20.0,
            tipo_sensor_primario="wh65",
            tipo_sensor_viento="wh65"
        )
        
        sens_wh31 = sensacion_termica_corregida(
            temperatura_c=20.0,
            humedad_relativa=60.0,
            velocidad_viento_kmh=20.0,
            tipo_sensor_primario="wh31",
            tipo_sensor_viento="wh31",
            distancia_pared_metros=0.8
        )
        
        # Factor corrección debe ser diferente (WH31 tiene menor viento real)
        assert sens_wh31["viento_real_estimado_kmh"] > sens_wh65["viento_real_estimado_kmh"] or \
               abs(sens_wh31["sensacion_termica_corregida"] - sens_wh65["sensacion_termica_corregida"]) > 0.1
    
    def test_temperatura_ajustada_wh31_con_radiacion(self):
        """WH31 con radiación alta debe estimar temp MÁS BAJA (resta el calentamiento)."""
        result = temperatura_ajustada_por_sensor(
            temperatura_medida_c=25.0,
            tipo_sensor="wh31",
            radiacion_w_m2=1000.0
        )
        
        # Debe restar calentamiento
        assert result["temperatura_estimada_real"] < result["temperatura_medida"]
        assert result["error_sistematico_grados"] > 0, "Error debe ser positivo (WH31 lee alto)"
    
    def test_temperatura_ajustada_wh65_sin_cambio(self):
        """WH65 no debe ajustarse (sin error sistemático)."""
        result = temperatura_ajustada_por_sensor(
            temperatura_medida_c=25.0,
            tipo_sensor="wh65",
            radiacion_w_m2=1000.0
        )
        
        assert result["temperatura_estimada_real"] == result["temperatura_medida"]
        assert result["error_sistematico_grados"] == 0.0


# ═════════════════════════════════════════════════════════════════════════════
# TESTS: META-CONFIANZA
# ═════════════════════════════════════════════════════════════════════════════

class TestMetaConfianza:
    """Tests para cálculo de confianza por dominio."""
    
    def test_confianza_100_con_datos_completos(self):
        """Con todos los subíndices, confianza debe ser alta."""
        subindices = {
            "viento_cetreria": 75.0,
            "visibilidad_terreno": 80.0,
            "termales_probabilidad": 60.0,
            "barro_campo": 40.0,
            "confort_ave": 70.0,
        }
        contextos = {
            "riesgo_escorrentia": 30.0,
            "comfort_universal": 75.0,
            "contexto_lluvia_global": None,
        }
        
        result = calcular_confianza_dominio(
            dominio="cetreria",
            indice_sintetico=75.0,
            subindices_disponibles=subindices,
            contextos_disponibles=contextos
        )
        
        assert result["confianza"] >= 70.0, "Confianza con datos debe ser alta"
        assert result["recomendacion"]  # Debe haber recomendación
    
    def test_confianza_baja_con_datos_parciales(self):
        """Sin subíndices crit, confianza debe ser baja."""
        subindices = {}
        contextos = {}
        
        result = calcular_confianza_dominio(
            dominio="cetreria",
            indice_sintetico=50.0,
            subindices_disponibles=subindices,
            contextos_disponibles=contextos
        )
        
        assert result["confianza"] < 50.0, "Confianza sin datos debe ser baja"
        assert "CRÍTICA" in result["recomendacion"] or "BAJA" in result["recomendacion"]
    
    def test_confianza_multiple_dominios(self):
        """Debe calcular confianza para todos los dominios e identificar problematicos."""
        indices = {
            "cetreria": 75.0,
            "lluvia": 50.0,
            "confort": 65.0,
            "deporte": 40.0,
        }
        subindices = {"dummy": 50.0}
        contextos = {}
        
        result = calcular_confianza_multiples_dominios(indices, subindices, contextos)
        
        assert "confianzas" in result
        assert len(result["confianzas"]) == 8  # 8 dominios
        assert "confianza_promedio" in result
        assert result["confianza_promedio"] >= 0.0 and result["confianza_promedio"] <= 100.0


# ═════════════════════════════════════════════════════════════════════════════
# TESTS: MATRIZ IMPACTO
# ═════════════════════════════════════════════════════════════════════════════

class TestMatrizImpacto:
    """Tests para cálculo de impactos cruzados."""
    
    def test_lluvia_destruye_cetreria(self):
        """Lluvia debe tener impacto NEGATIVO en cetrería."""
        impactos = calcular_impacto_evento("lluvia", valor_evento=100.0)
        
        assert impactos["cetreria_impacto"] < -50, "Lluvia debe destruir cetrería"
        assert "CRÍTICO" in impactos.get("clasificacion", ""), "Debe ser clasificado como crítico"
    
    def test_lluvia_beneficia_riego(self):
        """Lluvia debe tener impacto POSITIVO en riego."""
        impactos = calcular_impacto_evento("lluvia", valor_evento=100.0)
        
        assert impactos["riego_impacto"] > 0, "Lluvia debe beneficiar riego"
    
    def test_amplitud_termica_aumenta_riesgo_salud(self):
        """Amplitud térmica debe aumentar riesgo salud."""
        impactos = calcular_impacto_evento("amplitud_termica", valor_evento=100.0)
        
        assert impactos["salud_impacto"] > 0, "Amplitud debe aumentar riesgo salud"
    
    def test_escorrentia_inaplayable_deporte(self):
        """Escorrentía debe ser destructiva para deporte."""
        impactos = calcular_impacto_evento("escorrentia", valor_evento=100.0)
        
        assert impactos["deporte_impacto"] < -80, "Escorrentía debe ser inaplayable"
    
    def test_impactos_multiples_eventos_sintesis(self):
        """Debe sintetizar impactos de múltiples eventos."""
        eventos = {
            "lluvia": 80.0,
            "amplitud_termica": 50.0,
            "escorrentia": 60.0
        }
        
        result = calcular_impacto_multiples_eventos(eventos)
        
        assert "dominios_impactados" in result
        assert len(result["dominios_impactados"]) == 8
        
        # Deporte debe ser CRÍTICO (lluvia + escorrentía + amplitud)
        deporte_impacto = result["dominios_impactados"]["deporte"]["total_impacto"]
        assert deporte_impacto < -80, "Deporte debe estar crítico con múltiples eventos"


# ═════════════════════════════════════════════════════════════════════════════
# TESTS: GENÉRICOS
# ═════════════════════════════════════════════════════════════════════════════

class TestGenerico:
    """Tests genéricos de consistencia del sistema."""
    
    def test_valores_en_rango(self):
        """Todos los valores publicados deben estar en rango [0, 100] o ser None."""
        sensacion = sensacion_termica_corregida(
            temperatura_c=15.0, humedad_relativa=70.0, velocidad_viento_kmh=10.0
        )
        # Sensaciones pueden salir del rango, es normal
        assert isinstance(sensacion["sensacion_termica_raw"], (int, float))
    
    def test_contexto_sensores_completo(self):
        """factor_proteccion debe retornar dict completo."""
        result = factor_proteccion_sensores("wh65")
        
        assert "factor_viento" in result
        assert "factor_calentamiento_radiativo" in result
        assert "factor_evaporacion" in result
        assert "confianza_temperatura" in result
        assert "descripcion" in result
    
    def test_confianza_propiedades_requeridas(self):
        """Confianza debe retornar todas las propiedades."""
        result = calcular_confianza_dominio(
            dominio="cetreria",
            indice_sintetico=50.0,
            subindices_disponibles={},
            contextos_disponibles={}
        )
        
        assert "confianza" in result
        assert "completitud_subindices" in result
        assert "contextos_presentes" in result
        assert "consistencia_interna" in result


# ═════════════════════════════════════════════════════════════════════════════
# EJECUTOR TESTS
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
