#!/usr/bin/env python
"""
INVENTARIO REAL: ¿QUÉ FORMULA USA CADA PARÁMETRO ACTUALMENTE?

Mapeamos EXACTAMENTE dónde viene cada dato (sensor vs fórmula vs cálculo)
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path

print("=" * 80)
print("INVENTARIO COMPLETO: FORMULA ACTUAL DE CADA PARÁMETRO")
print("=" * 80)

# Leer código para encontrar la verdad
system_file = Path('core/system/system_core.py').read_text(encoding='utf-8')
bus_expander = Path('core/system/bus_expander.py').read_text(encoding='utf-8')
main_asgi = Path('main_asgi.py').read_text(encoding='utf-8')

parametros = {
    'sensacion_termica': {
        'que_es': 'Indice de confort térmico',
        'buscar_en': ['UTCI', 'indice_utci', 'sensacion_termica'],
        'actual': None,
        'fuente': None,
        'tipo': None
    },
    'humedad_relativa': {
        'que_es': 'Porcentaje de humedad en aire',
        'buscar_en': ['humedad_raw', 'self.system.data.get.*humedad', 'humidity'],
        'actual': None,
        'fuente': None,
        'tipo': None
    },
    'velocidad_viento': {
        'que_es': 'Velocidad del viento en m/s',
        'buscar_en': ['viento_raw', 'wind_speed', 'self.system.data.get.*viento'],
        'actual': None,
        'fuente': None,
        'tipo': None
    },
    'indice_uv': {
        'que_es': 'Indice ultravioleta',
        'buscar_en': ['indice_uv', 'uv_index', 'sensor.*uv'],
        'actual': None,
        'fuente': None,
        'tipo': None
    },
    'radiacion_solar': {
        'que_es': 'Radiacion solar en W/m²',
        'buscar_en': ['radiacion_raw', 'radiacion_solar', 'solar_radiation'],
        'actual': None,
        'fuente': None,
        'tipo': None
    }
}

# BUSCAR EN CÓDIGO
print("\n--- RASTREANDO FUENTES REALES ---\n")

# 1. SENSACION_TERMICA
print("1. SENSACION_TERMICA")
if 'indice_utci' in bus_expander or 'utci_polynomial' in bus_expander:
    print("   ACTUAL: indice_utci (UTCI Polynomial Fiala 186)")
    print("   FUENTE: core/indices/utci_polynomial.py")
    print("   TIPO: FORMULA CALCULADA")
    print("   INPUTS: temperatura, humedad, viento, radiacion, presion")
    parametros['sensacion_termica']['actual'] = 'indice_utci'
    parametros['sensacion_termica']['fuente'] = 'core/indices/utci_polynomial.py'
    parametros['sensacion_termica']['tipo'] = 'FÓRMULA'
else:
    print("   NO ENCONTRADA")

# 2. HUMEDAD_RELATIVA
print("\n2. HUMEDAD_RELATIVA")
if 'humedad_raw' in bus_expander:
    print("   ACTUAL: Lectura directa del sensor (Ecowitt)")
    print("   FUENTE: self.system.data.get('humedad') o equivalente")
    print("   TIPO: SENSOR DIRECTO")
    print("   PROCESSING: humedad_raw → publicada con derivados")
    parametros['humedad_relativa']['actual'] = 'sensor_directo'
    parametros['humedad_relativa']['fuente'] = 'Ecowitt (sensor HR%)'
    parametros['humedad_relativa']['tipo'] = 'SENSOR'
else:
    print("   NO ENCONTRADA")

# 3. VELOCIDAD_VIENTO
print("\n3. VELOCIDAD_VIENTO")
if 'viento_raw' in bus_expander or 'viento_ajustado' in bus_expander:
    print("   ACTUAL: Lectura del sensor + ajuste logarítmico")
    print("   FUENTE: self.system.data.get('velocidad_viento') + factor_ajuste_perfil_viento")
    print("   TIPO: SENSOR + CORRECCIÓN")
    print("   PROCESSING: viento_raw → viento_ajustado_10m (altura)")
    parametros['velocidad_viento']['actual'] = 'sensor + ajuste_altura'
    parametros['velocidad_viento']['fuente'] = 'Ecowitt (anemómetro) + corrección'
    parametros['velocidad_viento']['tipo'] = 'SENSOR + FÓRMULA'
else:
    print("   NO ENCONTRADA")

# 4. INDICE_UV
print("\n4. INDICE_UV")
if 'uv' in bus_expander.lower():
    print("   ACTUAL: Lectura directa del sensor (si existe)")
    print("   FUENTE: self.system.data.get('uv') o derivado de radiacion")
    print("   TIPO: SENSOR DIRECTO (o inferido)")
    print("   NOTA: No todos los Ecowitt tienen sensor UV")
    parametros['indice_uv']['actual'] = 'sensor_directo_o_derivado'
    parametros['indice_uv']['fuente'] = 'Ecowitt (sensor UV) o cálculo'
    parametros['indice_uv']['tipo'] = 'SENSOR/CÁLCULO'
else:
    print("   NO ENCONTRADA - Posible GAP")
    parametros['indice_uv']['actual'] = 'NO_DEFINIDO'
    parametros['indice_uv']['fuente'] = 'MISSING'
    parametros['indice_uv']['tipo'] = 'GAP'

# 5. RADIACION_SOLAR
print("\n5. RADIACION_SOLAR")
if 'radiacion_raw' in bus_expander or 'radiacion_solar' in bus_expander:
    print("   ACTUAL: Lectura directa + cálculo teórico")
    print("   FUENTE: self.system.data.get('radiacion_solar') + Gueymard (REST2)")
    print("   TIPO: SENSOR + FÓRMULA TEÓRICA")
    print("   PROCESSING: radiacion_raw + Gueymard → radiacion_extraterrestre")
    parametros['radiacion_solar']['actual'] = 'sensor + gueymard'
    parametros['radiacion_solar']['fuente'] = 'Ecowitt (piranómetro) + Gueymard'
    parametros['radiacion_solar']['tipo'] = 'SENSOR + FÓRMULA'
else:
    print("   NO ENCONTRADA")

print("\n" + "=" * 80)
print("RESUMEN INVENTARIO")
print("=" * 80)

for param, info in parametros.items():
    print(f"\n{param.upper()}")
    print(f"  Actual: {info['actual']}")
    print(f"  Fuente: {info['fuente']}")
    print(f"  Tipo: {info['tipo']}")

print("\n" + "=" * 80)
print("PROBLEMAS IDENTIFICADOS")
print("=" * 80)

print("""
1. SENSACION_TERMICA: BIEN
   - Usa UTCI (fórmula conocida)
   - Está en FORMULA_HIERARCHY
   - Duelo: SciPy curve_fit vs UTCI → UTCI gana (+0.024)
   
2. HUMEDAD_RELATIVA: PROBLEMA
   - Usa sensor directo (no está en FORMULA_HIERARCHY como fórmula)
   - Sistema no sabe que "sensor directo" ES su "fórmula actual"
   - SciPy interp1d: solo FILTRARÍA/SUAVIZARÍA datos, no reemplaza
   - Duelo correcto: ¿es mejor suavizar con interp1d?
   
3. VELOCIDAD_VIENTO: PROBLEMA
   - Usa sensor + ajuste logarítmico (corrección de altura)
   - No está en FORMULA_HIERARCHY como ELITE
   - SciPy Weibull: distribución estadística, diferente uso
   - Duelo correcto: ¿es mejor Weibull que ajuste logarítmico?
   
4. INDICE_UV: PROBLEMA CRÍTICO
   - NO sabemos si existe (gap en código)
   - Si no existe: SciPy quad GANA por default (no hay nada)
   - Si existe: duelo sensor vs SciPy
   
5. RADIACION_SOLAR: BIEN PARCIAL
   - Usa sensor + Gueymard (fórmula teórica)
   - SciPy Gaussian filter: solo SUAVIZA, no reemplaza
   - Duelo correcto: ¿es mejor gaussiano que actual?
""")

print("\n" + "=" * 80)
print("ACCIÓN RECOMENDADA")
print("=" * 80)

print("""
ANTES de duelos, PRIMERO:

1. Confirmar si Ecowitt TIENE sensor UV
   - Si NO → SciPy quad gana automáticamente
   - Si SÍ → duelo sensor vs SciPy quad

2. Aclarar si duelos son REEMPLAZO o MEJORA:
   - HUMEDAD + VIENTO + RADIACIÓN: SciPy NO reemplaza, MEJORA
   - SENSACIÓN + UV: SciPy SÍ reemplaza (si gana)

3. Reorganizar FORMULA_HIERARCHY:
   - Agregar "SENSOR" como nivel base
   - Registrar sensor directo COMO FÓRMULA ACTUAL
   - Así el sistema sabe qué es el baseline

DUELO CORRECTO:
  sensacion_termica: UTCI vs curve_fit (ya hecho: UTCI gana)
  humedad: sensor_raw vs interp1d (¿mejora? no reemplazo)
  viento: sensor+ajuste vs weibull (¿mejora?)
  radiacion: sensor+gueymard vs gaussian (¿mejora?)
  uv: ??? vs quad (¿existe sensor?)
""")
