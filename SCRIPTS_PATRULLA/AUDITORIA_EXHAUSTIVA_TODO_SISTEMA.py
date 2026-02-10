#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
AUDITORIA_EXHAUSTIVA_TODO_SISTEMA.py - Comparación Documentación vs Código
═══════════════════════════════════════════════════════════════════════════════

Analiza TODOS los documentos .md del sistema y verifica si los conceptos
documentados existen realmente en el código.

Genera matriz: [OK] (Implementado) | [WARNING] (Parcial) | [ERROR] (Solo Documentado)

Fecha: 4 FEB 2026
Versión: EXHAUSTIVA FINAL
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
from pathlib import Path
from collections import defaultdict
import json
import re

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, List, Tuple, Set

print("╔" + "="*78 + "╗")
print("║" + " "*78 + "║")
print("║" + "AUDITORÍA EXHAUSTIVA - DOCUMENTACIÓN vs CÓDIGO".center(78) + "║")
print("║" + "MeteoSerV3 - 4 FEB 2026".center(78) + "║")
print("║" + " "*78 + "║")
print("╚" + "="*78 + "╝")

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 1: ESCANEAR ARCHIVOS .MD
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("FASE 1: ESCANEANDO ARCHIVOS DE DOCUMENTACIÓN")
print("="*80)

md_files = sorted(PROJECT_ROOT.rglob("*.md"))
print(f"[OK] {len(md_files)} archivos .md encontrados")

# Archivos .md críticos a auditar (no todos los 414, solo los principales)
CRITICAL_MD_FILES = [
    "README.md",
    "LEEME_PRIMERO.txt",
    "COMO_INICIAR.txt",
    "RESUMEN_EJECUTIVO.txt",
    "docs/MAPA_DEPENDENCIAS_V20.json",
    "ARBOL_DECISION_SENSACION_TERMICA.md",
    "CAMBIO_ESTRATEGICO_UTCI_27ENE.md",
    "ESTRATEGIA_MEJOR_FORMULA.md",
    "GUIA_RAPIDA_EJECUCION.md",
    "RESUMEN_CAMBIOS_27ENE.md",
    "VALIDACION_FINAL.md",
    "TEST_UTCI_ESTIMACION.md",
    "UTCI_DUAL_IMPLEMENTACION.md",
    "SRTM_CIMIENTO_GLOBAL.md",
    "CEREBRO_ESPACIO_TEMPORAL_COMPLETADO.md",
    "RESPUESTAS_FINALES_27ENE.md",
]

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 2: EXTRAER CONCEPTOS CLAVE
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("FASE 2: EXTRAYENDO CONCEPTOS PRINCIPALES")
print("="*80)

# Conceptos Clave a Auditar (extraídos de documentación)
CONCEPTOS_AUDITADOS = {
    "SENSORES": {
        "items": ["temperatura", "humedad", "presion", "viento", "lluvia", "radiacion", "uv", "rayos", "altitud"],
        "buscar_en": ["class", "def", "sensor"]
    },
    "INDICES_DERIVADOS": {
        "items": [
            "punto_rocio", "sensacion_termica", "UTCI", "WBGT", "PMV", "VPD",
            "evapotranspiracion", "densidad_aire", "humedad_absoluta", "radiacion_neta",
            "indices_termicos", "confort_general", "riesgo_helada", "riesgo_lluvia",
            "viento_cetreria", "visibilidad", "nubosidad", "presion_vapor"
        ],
        "buscar_en": ["def", "class", "FORMULA_HIERARCHY"]
    },
    "SISTEMAS_IA": {
        "items": [
            "learning_engine", "evolution_engine", "self_mod_engine", "simulation_engine",
            "prediction_engine", "integration_manager", "config_manager"
        ],
        "buscar_en": ["class", "import"]
    },
    "BUS_INTELIGENTE": {
        "items": [
            "Bus V3", "Bus Capas Información", "Grifo Inteligente", "consumir_elite", 
            "publicar_elite", "formula_hierarchy", "BusExpander"
        ],
        "buscar_en": ["class", "def"]
    },
    "ENDPOINTS_API": {
        "items": [
            "/estado", "/sensores", "/indices", "/recomendaciones", "/alarmas",
            "/ecowitt", "/prediccion", "/historico"
        ],
        "buscar_en": ["@app", "async def"]
    },
    "VALIDACION": {
        "items": [
            "validacion_fisica", "consistencia_termodinamica", "rango_validez",
            "precision_cientifica", "calibracion"
        ],
        "buscar_en": ["validate", "check", "class"]
    },
    "CETRERIA": {
        "items": [
            "viento_cetreria", "visibilidad_terreno", "termales_probabilidad",
            "indices_cetreria", "confort_ave"
        ],
        "buscar_en": ["cetreria", "def"]
    },
    "UBICACION": {
        "items": [
            "detectar_ubicacion", "SRTM", "geocodificacion", "coordenadas_argentina",
            "constitucion_fisica", "gravedad_local"
        ],
        "buscar_en": ["def", "class"]
    },
    "PREDICCION": {
        "items": [
            "prediccion_horaria", "prediccion_diaria", "LSTM", "neural_network",
            "forecast_engine"
        ],
        "buscar_en": ["prediction", "LSTM", "class"]
    },
    "ALERTAS": {
        "items": [
            "Centinela", "alertas_meteorologicas", "riesgo_tormenta", "alerta_helada",
            "alerta_lluvias", "sistema_alarmas"
        ],
        "buscar_en": ["alert", "centinela", "class"]
    }
}

print(f"[OK] {len(CONCEPTOS_AUDITADOS)} categorías de conceptos a auditar")
total_items = sum(len(cat["items"]) for cat in CONCEPTOS_AUDITADOS.values())
print(f"[OK] {total_items} items específicos a verificar")

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 3: BUSCAR IMPLEMENTACIONES EN CÓDIGO
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("FASE 3: BUSCANDO IMPLEMENTACIONES EN CÓDIGO")
print("="*80)

# Scanear todos los archivos Python
py_files = sorted(PROJECT_ROOT.rglob("*.py"))
py_files = [f for f in py_files if '__pycache__' not in str(f) and '.venv' not in str(f)]
print(f"📂 {len(py_files)} archivos Python encontrados")

# Usar grep en lugar de cargar archivos (mucho más eficiente)
import subprocess

def buscar_patron_en_codigo(patron: str) -> int:
    """Busca un patrón en todos los archivos Python"""
    try:
        result = subprocess.run(
            ['findstr', '/R', '/M', '/S', patron, str(PROJECT_ROOT / 'core'), str(PROJECT_ROOT / '*.py')],
            capture_output=True,
            timeout=5
        )
        return len(result.stdout.decode().split('\n')) if result.stdout else 0
    except:
        return 0

print(f"[OK] Búsqueda en código usando findstr (Windows)")


# ═══════════════════════════════════════════════════════════════════════════════
# FASE 4: VERIFICAR CADA CONCEPTO
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("FASE 4: VERIFICACIÓN DETALLADA")
print("="*80)

resultados = {}

for categoria, config in CONCEPTOS_AUDITADOS.items():
    resultados[categoria] = {
        "implementado_100": [],
        "parcialmente_implementado": [],
        "solo_documentado": [],
        "no_encontrado": []
    }
    
    print(f"\n📋 {categoria}:")
    
    for item in config["items"]:
        item_lower = item.lower().replace("_", " ").replace("-", " ")
        encontrado = False
        parcial = False
        
        # Buscar en archivos Python
        for file_path, content in py_content.items():
            # Búsqueda exacta
            if f'def {item}' in content or f'class {item}' in content:
                encontrado = True
                break
            # Búsqueda flexible
            if item_lower in content.lower():
                parcial = True
        
        # Buscar en archivos .md críticos
        for md_file in CRITICAL_MD_FILES:
            full_md = PROJECT_ROOT / md_file
            if full_md.exists():
                try:
                    with open(full_md, 'r', encoding='utf-8', errors='ignore') as f:
                        md_content = f.read()
                        if item in md_content or item_lower in md_content.lower():
                            if encontrado:
                                pass  # Ya encontrado en código
                            elif parcial:
                                parcial = True
                except:
                    pass
        
        # Clasificar
        if encontrado:
            resultados[categoria]["implementado_100"].append(item)
            print(f"  [OK] {item}")
        elif parcial:
            resultados[categoria]["parcialmente_implementado"].append(item)
            print(f"  [WARNING]  {item}")
        else:
            resultados[categoria]["solo_documentado"].append(item)
            print(f"  [ERROR] {item}")

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 5: GENERANDO REPORTE FINAL
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("FASE 5: REPORTE EJECUTIVO FINAL")
print("="*80)

total_100 = sum(len(r["implementado_100"]) for r in resultados.values())
total_parcial = sum(len(r["parcialmente_implementado"]) for r in resultados.values())
total_doc = sum(len(r["solo_documentado"]) for r in resultados.values())
total_no = sum(len(r["no_encontrado"]) for r in resultados.values())
total_items_verificados = total_100 + total_parcial + total_doc + total_no

print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│ MATRIZ DE REALIDAD - SISTEMA METEOSERV3                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [OK] IMPLEMENTADO 100%:          {total_100:3d} ({total_100*100/total_items_verificados:5.1f}%)                                │
│  [WARNING]  PARCIALMENTE:             {total_parcial:3d} ({total_parcial*100/total_items_verificados:5.1f}%)                                │
│  [ERROR] SOLO DOCUMENTADO:          {total_doc:3d} ({total_doc*100/total_items_verificados:5.1f}%)                                │
│  🚫 NO ENCONTRADO:             {total_no:3d} ({total_no*100/total_items_verificados:5.1f}%)                                │
│  ──────────────────────────────────────────────                            │
│  TOTAL CONCEPTOS AUDITADOS:    {total_items_verificados:3d}                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "─"*80)
print("DESGLOSE POR CATEGORÍA:")
print("─"*80 + "\n")

for categoria in sorted(resultados.keys()):
    r = resultados[categoria]
    total_cat = sum(len(r[k]) for k in r)
    print(f"\n{categoria}:")
    print(f"  [OK] Implementado: {len(r['implementado_100'])}/{total_cat}")
    if r['implementado_100']:
        for item in r['implementado_100'][:3]:
            print(f"     - {item}")
        if len(r['implementado_100']) > 3:
            print(f"     ... y {len(r['implementado_100'])-3} más")
    
    if r['parcialmente_implementado']:
        print(f"  [WARNING]  Parcial: {len(r['parcialmente_implementado'])}")
        for item in r['parcialmente_implementado'][:2]:
            print(f"     - {item}")
        if len(r['parcialmente_implementado']) > 2:
            print(f"     ... y {len(r['parcialmente_implementado'])-2} más")
    
    if r['solo_documentado']:
        print(f"  [ERROR] Solo Documentado: {len(r['solo_documentado'])}")
        for item in r['solo_documentado'][:2]:
            print(f"     - {item}")
        if len(r['solo_documentado']) > 2:
            print(f"     ... y {len(r['solo_documentado'])-2} más")

# ═══════════════════════════════════════════════════════════════════════════════
# Exportar JSON
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("GUARDANDO REPORTE DETALLADO")
print("="*80)

reporte_json = {
    "fecha": "2026-02-04",
    "tipo_auditoria": "EXHAUSTIVA",
    "archivos_analizados": {
        "md_files": len(md_files),
        "py_files": len(py_files),
        "py_cargados_memoria": len(py_content)
    },
    "resumen": {
        "implementado_100": total_100,
        "parcialmente": total_parcial,
        "solo_documentado": total_doc,
        "no_encontrado": total_no,
        "total": total_items_verificados,
        "porcentaje_real": f"{total_100*100/total_items_verificados:.1f}%"
    },
    "resultados_por_categoria": resultados
}

# Guardar
reporte_file = PROJECT_ROOT / "AUDITORIA_EXHAUSTIVA_RESULTADO.json"
with open(reporte_file, 'w', encoding='utf-8') as f:
    json.dump(reporte_json, f, indent=2, ensure_ascii=False)

print(f"[OK] Reporte guardado: {reporte_file}")

# ═══════════════════════════════════════════════════════════════════════════════
# VEREDICTO FINAL
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "="*80)
print("VEREDICTO FINAL")
print("="*80)

porcentaje_real = total_100*100/total_items_verificados if total_items_verificados > 0 else 0

if porcentaje_real >= 90:
    print(f"""
🛰️ SISTEMA ALTAMENTE CONFIABLE

MeteoSerV3 tiene {porcentaje_real:.1f}% de sus conceptos documentados
realmente implementados en código.

[OK] RECOMENDACIÓN: PRODUCCIÓN CON CONFIANZA
""")
elif porcentaje_real >= 70:
    print(f"""
[WARNING]  SISTEMA PARCIALMENTE CONFIABLE

MeteoSerV3 tiene {porcentaje_real:.1f}% de implementación.

{total_doc} conceptos prometidos aún no están en código.

[WARNING]  RECOMENDACIÓN: REVISAR ANTES DE PRODUCCIÓN COMPLETA
""")
else:
    print(f"""
[CRITICAL] SISTEMA CON GRANDES PROMESAS SIN IMPLEMENTAR

MeteoSerV3 solo tiene {porcentaje_real:.1f}% de lo prometido en código.

{total_doc} conceptos solo están documentados.
{total_no} conceptos no fueron encontrados en ningún lado.

[ERROR] RECOMENDACIÓN: IMPLEMENTAR ANTES DE PRODUCCIÓN
""")

print("\n" + "="*80)
print(f"Auditoría completada - {len(CONCEPTOS_AUDITADOS)} categorías analizadas")
print("="*80)
