#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUDITORÍA EXHAUSTIVA V3 - Python Puro, Sin Dependencias Externas
"""

import sys
import os
from pathlib import Path
import json
from collections import defaultdict

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

PROJECT_ROOT = Path(__file__).parent.parent.parent

print("\n╔" + "="*78 + "╗")
print("║" + "AUDITORÍA EXHAUSTIVA - BÚSQUEDA PYTHON PURA".center(78) + "║")
print("╚" + "="*78 + "╝\n")

# Conceptos a auditar
CONCEPTOS = {
    "SENSORES_PRINCIPALES": [
        "temperatura", "humedad", "presion", "viento", "lluvia", "radiacion"
    ],
    "INDICES_CIENTÍFICOS": [
        "punto_rocio", "sensacion_termica", "UTCI", "evapotranspiracion",
        "densidad_aire", "presion_vapor", "humedad_absoluta"
    ],
    "SISTEMAS_IA": [
        "learning_engine", "evolution_engine", "self_mod_engine", "LSTM"
    ],
    "BUS_Y_INTELIGENCIA": [
        "consumir_elite", "publicar_elite", "formula_hierarchy",
        "BusExpander", "GrifoInteligente"
    ],
    "VALIDACION": [
        "validate", "consistency", "precision", "calibration"
    ],
    "CETRERIA": [
        "cetreria", "visibilidad_terreno", "termales"
    ],
    "UBICACION": [
        "SRTM", "ubicacion", "geocodif", "gravedad"
    ]
}

print("FASE 1: Escaneando archivos Python")
print("─"*80)

# Escanear archivos Python
py_files = list(PROJECT_ROOT.glob("**/*.py"))
py_files = [f for f in py_files if '__pycache__' not in str(f) and '.venv' not in str(f)]
print(f"Encontrados: {len(py_files)} archivos Python")

# Escanear archivos MD
md_files = list(PROJECT_ROOT.glob("**/*.md"))
print(f"Encontrados: {len(md_files)} archivos Markdown")

print("\nFASE 2: Buscando conceptos en código")
print("─"*80)

# Cargar contenido (solo el necesario)
py_content_map = {}
for py_file in py_files:
    try:
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            py_content_map[str(py_file.relative_to(PROJECT_ROOT))] = content
    except Exception as e:
        pass

print(f"[OK] Cargados {len(py_content_map)} archivos en memoria")

md_content_map = {}
for md_file in md_files:
    try:
        with open(md_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            md_content_map[str(md_file.relative_to(PROJECT_ROOT))] = content
    except:
        pass

print(f"[OK] Cargados {len(md_content_map)} documentos en memoria")

# ═══════════════════════════════════════════════════════════════════════════════
# AUDITAR
# ═══════════════════════════════════════════════════════════════════════════════

print("\nFASE 3: Auditando cada concepto")
print("─"*80)

resultados = {}
total_implementado = 0
total_documentado_solo = 0
total_no_encontrado = 0

for categoria, items in CONCEPTOS.items():
    print(f"\n{categoria}:")
    resultados[categoria] = {
        "implementado": [],
        "documentado_solo": [],
        "no_encontrado": []
    }
    
    for item in items:
        item_lower = item.lower()
        
        # Buscar en código
        en_codigo = any(item_lower in content for content in py_content_map.values())
        
        # Buscar en docs
        en_docs = any(item_lower in content for content in md_content_map.values())
        
        if en_codigo:
            print(f"  [OK] {item}")
            resultados[categoria]["implementado"].append(item)
            total_implementado += 1
        elif en_docs:
            print(f"  [WARNING]  {item} (solo en docs)")
            resultados[categoria]["documentado_solo"].append(item)
            total_documentado_solo += 1
        else:
            print(f"  [ERROR] {item}")
            resultados[categoria]["no_encontrado"].append(item)
            total_no_encontrado += 1

# ═══════════════════════════════════════════════════════════════════════════════
# REPORTE FINAL
# ═══════════════════════════════════════════════════════════════════════════════

total = total_implementado + total_documentado_solo + total_no_encontrado

print("\n" + "="*80)
print("RESULTADO FINAL")
print("="*80)

print(f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│                        MATRIZ DE REALIDAD DEL SISTEMA                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [OK] IMPLEMENTADO EN CÓDIGO:        {total_implementado:3d} ({total_implementado*100/total:5.1f}%)                           │
│  [WARNING]  SOLO DOCUMENTADO:             {total_documentado_solo:3d} ({total_documentado_solo*100/total:5.1f}%)                           │
│  [ERROR] NO ENCONTRADO:                 {total_no_encontrado:3d} ({total_no_encontrado*100/total:5.1f}%)                           │
│  ──────────────────────────────────────────────────                           │
│  TOTAL CONCEPTOS AUDITADOS:        {total:3d}                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
""")

# Desglose por categoría
print("\nDESGLOSE POR CATEGORÍA:")
print("─"*80)

for categoria in sorted(resultados.keys()):
    r = resultados[categoria]
    total_cat = len(r["implementado"]) + len(r["documentado_solo"]) + len(r["no_encontrado"])
    impl_pct = len(r["implementado"])*100/total_cat if total_cat > 0 else 0
    
    print(f"\n{categoria}: {impl_pct:.0f}% implementado")
    
    if r["implementado"]:
        print(f"  [OK] Implementado ({len(r['implementado'])}):")
        for item in r["implementado"]:
            print(f"     • {item}")
    
    if r["documentado_solo"]:
        print(f"  [WARNING]  Solo Documentado ({len(r['documentado_solo'])}):")
        for item in r["documentado_solo"]:
            print(f"     • {item}")
    
    if r["no_encontrado"]:
        print(f"  [ERROR] No Encontrado ({len(r['no_encontrado'])}):")
        for item in r["no_encontrado"]:
            print(f"     • {item}")

# ═══════════════════════════════════════════════════════════════════════════════
# VEREDICTO
# ═══════════════════════════════════════════════════════════════════════════════

porcentaje = total_implementado*100/total if total > 0 else 0

print("\n" + "="*80)
print("VEREDICTO FINAL")
print("="*80)

if porcentaje >= 85:
    print(f"""
🛰️  SISTEMA ALTAMENTE CONFIABLE

[OK] {porcentaje:.0f}% de los conceptos documentados están implementados.

RECOMENDACIÓN: PRODUCCIÓN CON TOTAL CONFIANZA
""")
elif porcentaje >= 70:
    print(f"""
[WARNING]  SISTEMA FUNCIONAL CON PROMESAS PENDIENTES

[OK] {porcentaje:.0f}% de los conceptos están implementados.
[ERROR] {total_documentado_solo} conceptos están SOLO documentados, sin código.

RECOMENDACIÓN: REVISAR E IMPLEMENTAR PROMESAS PENDIENTES
""")
elif porcentaje >= 50:
    print(f"""
[CRITICAL] SISTEMA CON MUCHO TRABAJO PENDIENTE

[OK] Solo {porcentaje:.0f}% implementado.
[ERROR] {total_documentado_solo + total_no_encontrado} conceptos sin implementar.

RECOMENDACIÓN: PRIORIZAR IMPLEMENTACIONES CRÍTICAS ANTES DE PRODUCCIÓN
""")
else:
    print(f"""
🚫 SISTEMA PRINCIPALMENTE DOCUMENTACIÓN SIN CÓDIGO

[OK] Solo {porcentaje:.0f}% implementado.
[ERROR] {total_documentado_solo + total_no_encontrado} conceptos sin implementar.

RECOMENDACIÓN: COMENZAR IMPLEMENTACIÓN DESDE CERO
""")

print("="*80)

# Guardar JSON
reporte_json = {
    "timestamp": "2026-02-04",
    "tipo_auditoria": "EXHAUSTIVA",
    "archivos_analizados": {
        "archivos_python": len(py_content_map),
        "archivos_markdown": len(md_content_map),
        "archivos_total": len(py_content_map) + len(md_content_map)
    },
    "resumen": {
        "implementado": total_implementado,
        "solo_documentado": total_documentado_solo,
        "no_encontrado": total_no_encontrado,
        "total": total,
        "porcentaje_real": f"{porcentaje:.1f}%"
    },
    "resultados_por_categoria": {
        cat: {
            "implementado": len(r["implementado"]),
            "solo_documentado": len(r["documentado_solo"]),
            "no_encontrado": len(r["no_encontrado"])
        }
        for cat, r in resultados.items()
    },
    "detalle_items": resultados
}

reporte_file = PROJECT_ROOT / "AUDITORIA_EXHAUSTIVA_RESULTADO.json"
with open(reporte_file, 'w', encoding='utf-8') as f:
    json.dump(reporte_json, f, indent=2, ensure_ascii=False)

print(f"\n[OK] Reporte detallado guardado: AUDITORIA_EXHAUSTIVA_RESULTADO.json")
