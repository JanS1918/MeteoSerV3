#!/usr/bin/env python
"""
Análisis: ¿Cómo se MIDEN actualmente los parámetros sin fórmula?
humedad_relativa, indice_uv, velocidad_viento, radiacion_solar
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from core.system.bus_expander import BusExpander

# Ver qué publica el bus actualmente
print("=" * 80)
print("ANALISIS: ¿DONDE VIENEN LOS DATOS ACTUALMENTE?")
print("=" * 80)

# Leer bus_expander para ver qué publica
bus_expander_code = Path('core/system/bus_expander.py').read_text(encoding='utf-8')

parametros_search = {
    'humedad_relativa': ['publicar.*humedad', 'humedad.*pct', 'self.bus.*humedad'],
    'indice_uv': ['publicar.*uv', 'indice_uv', 'radiacion.*uv'],
    'velocidad_viento': ['publicar.*viento', 'wind.*speed', 'velocidad.*viento'],
    'radiacion_solar': ['publicar.*radiacion', 'radiacion_solar', 'solar.*rad']
}

print("\nBusqueda de PUBLICACIONES en bus_expander:")
print("-" * 80)

# Buscar líneas donde se publican estos parámetros
lines = bus_expander_code.split('\n')
for i, line in enumerate(lines, 1):
    if 'publicar' in line.lower():
        if any(x in line.lower() for x in ['humedad', 'uv', 'viento', 'radiacion']):
            print(f"Linea {i}: {line.strip()[:100]}")

print("\n\n" + "=" * 80)
print("ANÁLISIS: FUENTES DE DATOS")
print("=" * 80)

# Ver qué datos obliga el sistema
print("""
TEORICAMENTE:

1. humedad_relativa: 
   - En BUS_DATA_CONTRACT.py hay especificacion
   - En bus_expander publica "humedad_raw" y derivados
   - PERO: No hay formula en FORMULA_HIERARCHY
   - ORIGEN: Sensor directo (Ecowitt recibe "humidity" o "rh")
   
2. indice_uv:
   - NO en BUS_DATA_CONTRACT
   - NO en bus_expander (no hay publicacion UV)
   - ORIGEN: ¿Sensor directo? ¿No se calcula?
   
3. velocidad_viento:
   - En BUS_DATA_CONTRACT: "wind_speed", "wind_kph", etc
   - En bus_expander: multiplas versiones (raw, ajustado, corregido)
   - PERO: No hay formula en FORMULA_HIERARCHY
   - ORIGEN: Sensor directo (Ecowitt recibe "wind")
   
4. radiacion_solar:
   - En BUS_DATA_CONTRACT: "radiacion_solar"
   - En bus_expander: Hay calculo via SRTM + Gueymard
   - PERO: No en FORMULA_HIERARCHY como ELITE
   - ORIGEN: Sensor + calculo teorico Gueymard
""")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
NO HAY "FORMULAS" porque son MEDIDAS DIRECTAS del sensor (Ecowitt):

- humedad_relativa: El sensor MIDE directamente HR% 
- velocidad_viento: El sensor MIDE directamente viento m/s
- indice_uv: El sensor MIDE directamente UV (si tiene sensor UV)
- radiacion_solar: El sensor MIDE directamente W/m² (si tiene piranómetro)

Las "fórmulas" en FORMULA_HIERARCHY son para CALCULAR indices derivados
como UTCI, punto de rocío, etc que REQUIEREN formulas.

La pregunta correcta es:
  "¿SciPy puede MEJORAR o FILTRAR estos datos sensados?"
  
La respuesta es SÍ, pero de forma diferente:
  - SciPy puede CALIBRAR (ajustar datos ruidosos)
  - SciPy puede INTERPOLAR (llenar gaps)
  - SciPy puede DISTRIBUIR (Weibull para viento)
  - SciPy puede FILTRAR (Gaussian para radiación)

PERO NO SON "FÓRMULAS" de calculo, son PROCESADORES de datos sensados.
""")
