#!/usr/bin/env python3
"""
AUDITORÍA EXTENSIVA COMPLETA - FASE 2
=====================================

Preguntas sistemáticas:

1. ¿Se redondean coordenadas en algún lado?
2. ¿Se publica gravedad EN EL BUS realmente?
3. ¿Hay dos fórmulas de gravedad diferentes?
4. ¿Qué datos se consultan más?
5. ¿Hay inconsistencias en cálculos?
6. ¿Cuáles módulos LEEN del Bus vs calcular por su cuenta?
7. ¿Hay hardcoded valores que NO están en el Bus?
"""

import json
import re
from pathlib import Path
from collections import defaultdict

workspace = Path(__file__).parent.parent

# ================================================================
# 1. AUDITORÍA DE REDONDEOS EN COORDENADAS
# ================================================================

print("\n" + "="*80)
print("📋 AUDITORÍA 1: REDONDEOS DE COORDENADAS")
print("="*80)

# Buscar patrones de redondeo en coordenadas
redondeo_patterns = [
    r'round\(.*(?:lat|lon|coord).*\)',
    r'\.round\(\)',
    r'f.*{.*:\.2f}.*(?:lat|lon)',
    r'f.*{.*:\.1f}.*(?:lat|lon)',
    r'f.*{.*:\.0f}.*(?:lat|lon)',
]

redondeos_encontrados = []

# Archivos a auditar
archivos_python = list((workspace / "core").rglob("*.py"))
archivos_python += list((workspace / "app").rglob("*.py"))
archivos_python += [(workspace / "main_asgi.py")]

for archivo in archivos_python:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
            lineas = contenido.split('\n')
            for i, linea in enumerate(lineas, 1):
                # Buscar redondeos asociados a coords
                if any(p in linea.lower() for p in ['lat', 'lon', 'coordenada', 'ubicacion']):
                    if 'round(' in linea or ':.0f' in linea or ':.1f' in linea or ':.2f' in linea:
                        if 'format' in linea or 'str' in linea or 'f"' in linea or "f'" in linea:
                            redondeos_encontrados.append({
                                'archivo': str(archivo.relative_to(workspace)),
                                'linea': i,
                                'contenido': linea.strip()
                            })
    except:
        pass

print(f"\n[BUSCAR] Redondeos encontrados en coordenadas: {len(redondeos_encontrados)}")
for item in redondeos_encontrados[:10]:
    print(f"  [ERROR] {item['archivo']}:{item['linea']}")
    print(f"     {item['contenido'][:80]}")

# ================================================================
# 2. AUDITORÍA: ¿SE PUBLICA GRAVEDAD EN BUS?
# ================================================================

print("\n" + "="*80)
print("📋 AUDITORÍA 2: PUBLICACIÓN DE GRAVEDAD EN BUS")
print("="*80)

bus_publicos = []
bus_lectura = []

try:
    bus_expander = workspace / "core" / "system" / "bus_expander.py"
    with open(bus_expander, 'r', encoding='utf-8') as f:
        contenido = f.read()
        lineas = contenido.split('\n')
        
        # Buscar publicaciones de gravedad
        for i, linea in enumerate(lineas, 1):
            if 'publicar' in linea.lower() and 'gravedad' in linea.lower():
                bus_publicos.append((i, linea.strip()))
            if 'leer' in linea.lower() and 'gravedad' in linea.lower():
                bus_lectura.append((i, linea.strip()))

except Exception as e:
    print(f"Error leyendo bus_expander: {e}")

print(f"\n[OK] Líneas donde se PUBLICA gravedad en Bus:")
for linea, contenido in bus_publicos:
    print(f"  Línea {linea}: {contenido[:70]}")

print(f"\n[OK] Líneas donde se LEE gravedad del Bus:")
for linea, contenido in bus_lectura:
    print(f"  Línea {linea}: {contenido[:70]}")

# ================================================================
# 3. AUDITORÍA: MÚLTIPLES FÓRMULAS DE GRAVEDAD
# ================================================================

print("\n" + "="*80)
print("📋 AUDITORÍA 3: FÓRMULAS DE GRAVEDAD (¿Hay duplicadas?)")
print("="*80)

formulas_gravedad = defaultdict(list)

for archivo in archivos_python:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
            lineas = contenido.split('\n')
            
            for i, linea in enumerate(lineas, 1):
                # Detectar cálculos de gravedad
                if 'gravedad' in linea.lower() or 'somigliana' in linea.lower():
                    if '=' in linea and not linea.strip().startswith('#'):
                        if any(x in linea for x in ['9.81', '9.80', 'somigliana', 'helmert']):
                            formula_type = 'DESCONOCIDA'
                            if '9.81' in linea:
                                formula_type = 'CONSTANTE 9.81'
                            elif '9.80665' in linea:
                                formula_type = 'ISA REFERENCE (historical)'
                            elif '9.80272394' in linea:
                                formula_type = 'SOMIGLIANA-HELMERT REAL'
                            elif 'somigliana' in linea.lower():
                                formula_type = 'SOMIGLIANA (cálculo)'
                            
                            formulas_gravedad[formula_type].append(
                                (str(archivo.relative_to(workspace)), i, linea.strip())
                            )
    except:
        pass

print("\n🔬 Fórmulas de gravedad encontradas:")
for formula_type, ubicaciones in sorted(formulas_gravedad.items()):
    print(f"\n  {formula_type}: {len(ubicaciones)} ocurrencias")
    for archivo, linea, contenido in ubicaciones[:3]:
        print(f"    ✓ {archivo}:{linea} → {contenido[:60]}")

# ================================================================
# 4. DATOS MÁS CONSULTADOS (Top 10)
# ================================================================

print("\n" + "="*80)
print("📋 AUDITORÍA 4: DATOS MÁS CONSULTADOS")
print("="*80)

consultas = defaultdict(int)

for archivo in archivos_python:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
            
            # Buscar .get() calls
            matches = re.findall(r'\.get\(["\']([a-z_]+)["\']', contenido)
            for match in matches:
                consultas[match] += 1
                
            # Buscar self.bus.leer()
            matches = re.findall(r'\.leer\(["\']([a-z_]+)["\']', contenido)
            for match in matches:
                consultas[f"BUS: {match}"] += 1
                
            # Buscar indices[...]
            matches = re.findall(r'indices\[["\']([a-z_]+)["\']', contenido)
            for match in matches:
                consultas[f"INDICES: {match}"] += 1
    except:
        pass

print("\n[STATS] Top 20 datos más consultados:")
sorted_consultas = sorted(consultas.items(), key=lambda x: x[1], reverse=True)
for dato, count in sorted_consultas[:20]:
    print(f"  {count:3d}x → {dato}")

# ================================================================
# 5. MÓDULOS QUE LEEN DEL BUS vs CALCULAN LOCALMENTE
# ================================================================

print("\n" + "="*80)
print("📋 AUDITORÍA 5: ¿LEEN DEL BUS O CALCULAN LOCALMENTE?")
print("="*80)

print("\n[BUSCAR] Buscando módulos que LEE

N del Bus...")
archivos_con_bus_leer = []

for archivo in archivos_python:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            if 'self.bus.leer' in f.read() or 'bus.leer' in f.read():
                archivos_con_bus_leer.append(str(archivo.relative_to(workspace)))
    except:
        pass

print(f"\nMódulos que LEE del Bus: {len(archivos_con_bus_leer)}")
for archivo in sorted(archivos_con_bus_leer)[:15]:
    print(f"  [OK] {archivo}")

# ================================================================
# 6. HARDCODED VALUES NO EN BUS
# ================================================================

print("\n" + "="*80)
print("📋 AUDITORÍA 6: ¿HAY HARDCODED VALUES FUERA DEL BUS?")
print("="*80)

hardcoded = defaultdict(list)

for archivo in archivos_python:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
            lineas = contenido.split('\n')
            
            for i, linea in enumerate(lineas, 1):
                # Buscar constantes sin ser de Bus
                if ' = ' in linea and not linea.strip().startswith('#'):
                    # Valores físicos importantes
                    valores_criticos = ['9.8', '101325', '287.05', '1.4', '0.622', '8.314']
                    for valor in valores_criticos:
                        if valor in linea and 'bus' not in linea.lower():
                            if 'const' not in linea.lower() and 'import' not in linea:
                                hardcoded[valor].append(
                                    (str(archivo.relative_to(workspace)), i, linea.strip()[:70])
                                )
    except:
        pass

print("\n[WARNING]  Valores física críticos SIN leer del Bus:")
for valor, ubicaciones in sorted(hardcoded.items()):
    if ubicaciones:
        print(f"\n  Valor '{valor}': {len(ubicaciones)} ocurrencias")
        for archivo, linea, contenido in ubicaciones[:3]:
            print(f"    {archivo}:{linea} → {contenido}")

# ================================================================
# 7. INCONSISTENCIAS EN CÁLCULOS (MISMA VARIABLE, DIFERENTES VALORES)
# ================================================================

print("\n" + "="*80)
print("📋 AUDITORÍA 7: INCONSISTENCIAS EN CÁLCULOS")
print("="*80)

print("\n[BUSCAR] Buscando cálculos de presión_nivel_mar con diferentes fórmulas...")

archivos_presion = []
for archivo in archivos_python:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
            if 'presion_nivel_mar' in contenido or 'presion_nl_m' in contenido:
                lineas = contenido.split('\n')
                for i, linea in enumerate(lineas, 1):
                    if 'presion_nivel_mar' in linea or 'presion_nl_m' in linea:
                        if '=' in linea and not linea.strip().startswith('#'):
                            archivos_presion.append({
                                'archivo': str(archivo.relative_to(workspace)),
                                'linea': i,
                                'contenido': linea.strip()[:90]
                            })
    except:
        pass

print(f"\nCálculos de presión_nivel_mar encontrados: {len(archivos_presion)}")
for item in archivos_presion[:10]:
    print(f"  {item['archivo']}:{item['linea']}")
    print(f"     {item['contenido']}")

# ================================================================
# 8. ANÁLISIS FINAL DE BUS vs FALLBACK
# ================================================================

print("\n" + "="*80)
print("📋 AUDITORÍA 8: PATRÓN BUS vs FALLBACK")
print("="*80)

bus_leer_patterns = defaultdict(int)

for archivo in archivos_python:
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
            
            # Detectar patrón bus.leer(...) or ...
            matches = re.findall(r'\.leer\(["\']([^"\']+)["\']\)\s+or\s+([0-9.]+)', contenido)
            for clave, fallback in matches:
                bus_leer_patterns[f"{clave} → fallback {fallback}"] += 1
    except:
        pass

print(f"\nPatrones BUS + FALLBACK encontrados:")
for patron, count in sorted(bus_leer_patterns.items(), key=lambda x: x[1], reverse=True):
    print(f"  {count}x → {patron}")

# ================================================================
# REPORTE FINAL
# ================================================================

print("\n" + "="*80)
print("[TARGET] HALLAZGOS CRÍTICOS RESUMIDOS")
print("="*80)

print(f"""
1️⃣  REDONDEOS DE COORDENADAS: {len(redondeos_encontrados)} instancias
    [WARNING]  Ver líneas específicas arriba

2️⃣  PUBLICACIÓN DE GRAVEDAD EN BUS: {len(bus_publicos)} líneas
    [OK] Si < 3: GRAVE - No se está publicando
    [OK] Si ≥ 3: OK - Se publica en múltiples puntos

3️⃣  FÓRMULAS DE GRAVEDAD DIFERENTES:
    - CONSTANTE 9.81: {len(formulas_gravedad.get('CONSTANTE 9.81', []))} 
    - ISA REFERENCE (historical): {len(formulas_gravedad.get('ISA REFERENCE (historical)', []))} 
    - SOMIGLIANA REAL: {len(formulas_gravedad.get('SOMIGLIANA-HELMERT REAL', []))} 

4️⃣  TOP 5 DATOS MÁS CONSULTADOS:
    {', '.join([f'{d[0]}({d[1]}x)' for d in sorted_consultas[:5]])}

5️⃣  MÓDULOS QUE LEEN DEL BUS: {len(archivos_con_bus_leer)}
    [OK] Si ≥ 20: OK - Amplio uso
    [WARNING]  Si < 10: DÉBIL - Pocos módulos usan Bus

6️⃣  VALORES HARDCODED: {sum(len(v) for v in hardcoded.values())} ocurrencias
    [WARNING]  Estos deberían estar en Bus o Physics Engine

7️⃣  CÁLCULOS DE PRESIÓN: {len(archivos_presion)} ubicaciones
    [WARNING]  ¿Todas usan misma fórmula?

8️⃣  PATRONES BUS+FALLBACK: {len(bus_leer_patterns)} diferentes patrones
""")

print("\n" + "="*80)
print("[OK] AUDITORÍA COMPLETADA")
print("="*80)
