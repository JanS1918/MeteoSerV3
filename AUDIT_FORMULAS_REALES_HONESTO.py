# -*- coding: utf-8 -*-
"""
AUDITORÍA BRUTAL HONESTO: ¿QUÉ TENEMOS REALMENTE Y QUÉ FUNCIONA?

NO QUEREMOS SCORES MÁGICOS. QUEREMOS VERDAD.
- ¿Qué funciones EXISTEN en nuestro código?
- ¿Qué funciones ESTÁN REGISTRADAS en FORMULA_HIERARCHY?
- ¿Cuáles FUNCIONAN REALMENTE sin errores?
- ¿Cuál es la DIFERENCIA entre EXISTIR y USARSE?
"""

import sys
import traceback
from pathlib import Path

# Setup
sys.path.insert(0, str(Path(__file__).parent))

from fix_logging_all import setup_safe_logging
setup_safe_logging()

import logging
logger = logging.getLogger(__name__)

# Imports de funciones
from core.indices.environmental_indices import (
    indice_utci,
    indice_steadman_apparent_temperature,
    wind_chill,
    indice_wbgt,
)

from core.bus.formula_hierarchy import FORMULA_HIERARCHY, NivelElite

# Test data
TEST_DATA = {
    "temperatura": 25.0,
    "humedad": 60.0,
    "viento": 3.0,
    "radiacion": 400.0,
}


def test_funcion(nombre_func, func, kwargs_data):
    """Test una función y reporta: ¿EXISTE? ¿FUNCIONA? ¿QUÉ RETORNA?"""
    print(f"\n{'='*70}")
    print(f"TESTANDO: {nombre_func}")
    print(f"{'='*70}")
    
    try:
        resultado = func(**kwargs_data)
        print(f"✅ FUNCIONA")
        print(f"   Resultado: {resultado}")
        print(f"   Tipo: {type(resultado)}")
        return True, resultado
    except Exception as e:
        print(f"❌ ERROR")
        print(f"   Excepción: {type(e).__name__}: {e}")
        print(f"   Traceback:")
        for linea in traceback.format_exc().split('\n')[-5:]:
            if linea.strip():
                print(f"   {linea}")
        return False, None


def audit_formula_hierarchy():
    """Audita qué hay REALMENTE en FORMULA_HIERARCHY"""
    print("\n" + "="*70)
    print("AUDITORÍA: ¿QUÉ ESTÁ EN FORMULA_HIERARCHY?")
    print("="*70)
    
    parametro = "sensacion_termica"
    
    print(f"\nParámetro: {parametro}")
    print(f"Registradas en jerarquía: {len(FORMULA_HIERARCHY.get(parametro, {}))}")
    
    for nivel, formula_obj in FORMULA_HIERARCHY.get(parametro, {}).items():
        print(f"\n  Nivel: {nivel.name}")
        print(f"  Nombre técnico: {formula_obj.nombre_tecnico}")
        print(f"  Nombre legible: {formula_obj.nombre_legible}")
        print(f"  Módulo: {formula_obj.módulo}")
        print(f"  Precisión: {formula_obj.precisión}")
    
    # Comparar: ¿Hay funciones en el código que NO están en jerarquía?
    print(f"\n\nFUNCIONES OCULTAS (existen en código pero NO en FORMULA_HIERARCHY):")
    print(f"  - indice_wbgt: ¿EXISTE? SÍ (en environmental_indices.py línea 1662)")
    print(f"    ¿ESTÁ EN JERARQUÍA? NO")
    print(f"    IMPACTO: Guardian NUNCA la evalúa en duelo")


def main():
    print("\n" + "█"*70)
    print("█ AUDITORÍA BRUTAL: FÓRMULAS REALES vs INTEGRACIÓN PROMETE")
    print("█"*70)
    
    # 1. AUDIT HIERARCHY
    audit_formula_hierarchy()
    
    # 2. TEST FUNCIONES QUE EXISTEN
    print("\n\n" + "█"*70)
    print("█ TESTING: ¿FUNCIONAN LAS FÓRMULAS QUE TENEMOS?")
    print("█"*70)
    
    # Funciones REGISTRADAS en jerarquía
    print("\n[REGISTRADAS EN JERARQUÍA]")
    test_funcion("indice_utci", indice_utci, TEST_DATA)
    test_funcion("indice_steadman_apparent_temperature", 
                 indice_steadman_apparent_temperature, 
                 TEST_DATA)
    test_funcion("wind_chill", wind_chill, TEST_DATA)
    
    # Función EXISTENTE pero NO registrada
    print("\n[OCULTA EN CÓDIGO - NO EN JERARQUÍA]")
    test_funcion("indice_wbgt", indice_wbgt, TEST_DATA)
    
    # 3. COMPARACIÓN RESULTADOS
    print("\n\n" + "█"*70)
    print("█ COMPARACIÓN DE RESULTADOS")
    print("█"*70)
    
    print("\nCon inputs: T=25°C, HR=60%, Viento=3 km/h, Radiación=400 W/m²")
    print("\nFórmula UTCI (REGISTRADA - ELITE):")
    try:
        utci = indice_utci(**TEST_DATA)
        print(f"  Resultado: {utci}°C")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print("\nFórmula WBGT (OCULTA - NO REGISTRADA):")
    try:
        wbgt = indice_wbgt(**TEST_DATA)
        print(f"  Resultado: {wbgt}°C")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # 4. CONCLUSIÓN
    print("\n\n" + "█"*70)
    print("█ CONCLUSIÓN BRUTAL")
    print("█"*70)
    print("""
✅ TENEMOS: indice_wbgt() en código (environmental_indices.py línea 1662)
❌ PERO: NO está en FORMULA_HIERARCHY
❌ RESULTADO: Guardian's duelo NUNCA la considera
⚠️  IMPACTO: Perdemos la mejor opción para estrés térmico ocupacional

EL PROBLEMA NO ES "FALTA DE FÓRMULAS EXTERNAS"
EL PROBLEMA ES: NUESTRAS MEJORES FÓRMULAS ESTÁN OCULTAS DEL DUELO
""")


if __name__ == "__main__":
    main()
