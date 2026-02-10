#!/usr/bin/env python
"""
AUDITORÍA FASE 1: Mapeo real de subfactores publicados en el bus.
Identifica promesas vacías vs implementación real.
"""

import ast
import re
from pathlib import Path
from collections import defaultdict

BUS_FILE = Path("core/system/bus_expander.py")

# ═════════════════════════════════════════════════════════════════════════════
# 1. PARSE bus_expander.py para contar calls a self.bus.publicar()
# ═════════════════════════════════════════════════════════════════════════════

with open(BUS_FILE, 'r', encoding='utf-8') as f:
    contenido = f.read()

# Contar líneas con self.bus.publicar
publicar_calls = re.findall(r'self\.bus\.publicar\("([^"]+)"', contenido)
publicar_unicos = set(publicar_calls)

print("="*80)
print("AUDITORIA FASE 1: BUS_EXPANDER.PY")
print("="*80)
print(f"\n[OK] Calls a self.bus.publicar(): {len(publicar_calls)} lineas")
print(f"[OK] Keys UNICOS publicados: {len(publicar_unicos)}")
print(f"\n  Primeros 20 keys unicos:")
for i, key in enumerate(sorted(publicar_unicos)[:20], 1):
    print(f"  {i:2}. {key}")

# ═════════════════════════════════════════════════════════════════════════════
# 2. BUSCAR PROMESAS NO CUMPLIDAS (métodos sin cuerpo)
# ═════════════════════════════════════════════════════════════════════════════

promesas_vacias = []
promesas_parciales = []

# Buscar definiciones de método _publish_*
metodos_regex = r'async def (_publish_[^(]+)\([^)]*\):(.*?)(?=async def|$)'
matches = re.finditer(metodos_regex, contenido, re.DOTALL)

for match in matches:
    method_name = match.group(1)
    body = match.group(2)
    
    # Contar líneas de código real (excluyendo docstrings, comentarios, espacios)
    lines = [l.strip() for l in body.split('\n') if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('"""') and not l.strip().startswith("'''")]
    real_code_lines = [l for l in lines if not l.startswith('"""') and not l.startswith("'''")]
    
    # Si has solo try/except o pocas líneas, es promesa vacía
    if len(real_code_lines) < 3:
        promesas_vacias.append((method_name, len(real_code_lines)))
    elif 'placeholder' in body.lower() or 'todo' in body.lower() or 'pass' in body:
        promesas_parciales.append((method_name, len(real_code_lines)))

print(f"\n\n{'='*80}")
print("PROMESAS VACIAS (metodos _publish con <3 lineas):")
print(f"{'='*80}")
for method, lineas in promesas_vacias[:10]:
    print(f"  [X] {method}: {lineas} lineas")

print(f"\n\nPROMESAS PARCIALES (con TODO/placeholder):")
print(f"{'='*80}")
for method, lineas in promesas_parciales[:10]:
    print(f"  [!] {method}: {lineas} lineas")

# ═════════════════════════════════════════════════════════════════════════════
# 3. CONTAR SUBFACTORES POR SECCIÓN
# ═════════════════════════════════════════════════════════════════════════════

# Buscar comentarios de secciones (SECCIÓN X)
secciones = re.finditer(r'# SECCIÓN (\d+):?\s*(.+?)(?=# SECCIÓN|\Z)', contenido, re.IGNORECASE | re.DOTALL)

print(f"\n\n{'='*80}")
print("COBERTURA POR SECCION:")
print(f"{'='*80}")

for match in secciones:
    seccion_num = match.group(1)
    seccion_content = match.group(2)
    
    # Contar publicar calls en esta seccion
    calls_seccion = len(re.findall(r'self\.bus\.publicar', seccion_content))
    
    # Extraer descripcion de seccion
    desc_match = re.search(r'# SECCION \d+:?\s*([^\n]+)', seccion_content)
    desc = desc_match.group(1) if desc_match else "Desconocida"
    
    print(f"  Seccion {seccion_num}: {desc}")
    print(f"    -> {calls_seccion} subfactores publicados")

# ═════════════════════════════════════════════════════════════════════════════
# 4. ANALISIS BRUTO: Cuantos subfactores realmente se publican?
# ═════════════════════════════════════════════════════════════════════════════

print(f"\n\n{'='*80}")
print("RESUMEN FINAL:")
print(f"{'='*80}")
print(f"  [OK] Keys unicos publicados: {len(publicar_unicos)}")
print(f"  [OK] Metodos _publish implementados: {len(list(re.finditer(r'async def _publish_', contenido)))}")
print(f"  [X] Metodos _publish vacios: {len(promesas_vacias)}")
print(f"  [!] Metodos _publish parciales: {len(promesas_parciales)}")
print(f"\n  PREDICCION REALIDAD:")
print(f"     Si {len(publicar_unicos)} keys se publican realmente,")
print(f"     pero se prometen 372-2000 subfactores...")
print(f"     -> BRECHA = {2000 - len(publicar_unicos)} subfactores FALTANTES O FALSOS")
print(f"\n  CONCLUSION: El bus publica ~{len(publicar_unicos)} de los 2000 prometidos.")
print(f"     Eso es solo {len(publicar_unicos)*100/2000:.1f}% de cobertura.")

# Guardar lista completa
with open("bus_subfactores_reales.txt", "w", encoding='utf-8') as f:
    f.write("SUBFACTORES REALES PUBLICADOS EN EL BUS:\n")
    f.write("="*80 + "\n\n")
    for i, key in enumerate(sorted(publicar_unicos), 1):
        f.write(f"{i:3}. {key}\n")

print(f"\n  Archivo guardado en: bus_subfactores_reales.txt")
