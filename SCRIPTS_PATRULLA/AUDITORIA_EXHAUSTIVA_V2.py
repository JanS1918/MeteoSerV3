#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUDITORÍA EXHAUSTIVA V2 - Rápida y Eficiente
Documentación vs Código - Todo MeteoSerV3
"""

import sys
import os
from pathlib import Path
import subprocess
import json

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

PROJECT_ROOT = Path(__file__).parent.parent.parent

print("\n╔" + "="*78 + "╗")
print("║" + "AUDITORÍA EXHAUSTIVA DEL SISTEMA - METODOLOGÍA GREP".center(78) + "║")
print("╚" + "="*78 + "╝\n")

# Conceptos a auditar (extraídos de documentación más importante)
CONCEPTOS = {
    "SENSORES_PRINCIPALES": [
        "temperatura", "humedad", "presion", "viento", "lluvia", "radiacion"
    ],
    "INDICES_CIENTÍFICOS": [
        "punto_rocio", "sensacion_termica", "UTCI", "evapotranspiracion",
        "densidad_aire", "presion_vapor", "humedad_absoluta"
    ],
    "SISTEMAS_IA": [
        "learning_engine", "evolution_engine", "self_mod_engine",
        "LSTM", "neural"
    ],
    "BUS_Y_INTELIGENCIA": [
        "consumir_elite", "publicar_elite", "formula_hierarchy", "BusExpander",
        "GrifoInteligente"
    ],
    "API_ENDPOINTS": [
        "/estado", "/sensores", "/indices", "/recomendaciones", "/ecowitt"
    ],
    "VALIDACION": [
        "validar", "validate", "consistencia", "rango_validez", "calibracion"
    ],
    "CETRERIA": [
        "viento_cetreria", "visibilidad_terreno", "termales_probabilidad"
    ],
    "UBICACION": [
        "SRTM", "detectar_ubicacion", "geocodificacion", "gravedad_local"
    ]
}

def buscar_en_codigo(patron: str) -> bool:
    """Busca un patrón en el código Python"""
    try:
        # Buscar en archivos Python recursivamente
        result = subprocess.run(
            f'findstr /R /S /I "{patron}" "{PROJECT_ROOT}\\core\\*" "{PROJECT_ROOT}\\*.py" > nul 2>&1',
            shell=True,
            timeout=3
        )
        return result.returncode == 0
    except:
        return False

def buscar_en_docs(patron: str) -> bool:
    """Busca un patrón en documentos .md"""
    try:
        result = subprocess.run(
            f'findstr /R /S /I "{patron}" "{PROJECT_ROOT}\\*.md" "{PROJECT_ROOT}\\docs\\*" > nul 2>&1',
            shell=True,
            timeout=3
        )
        return result.returncode == 0
    except:
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# AUDITAR
# ═══════════════════════════════════════════════════════════════════════════════

resultados = {}
total_implementado = 0
total_documentado_solo = 0
total_no_encontrado = 0

for categoria, items in CONCEPTOS.items():
    print(f"\n📋 {categoria}:")
    resultados[categoria] = {"implementado": 0, "documentado": 0, "no_encontrado": 0}
    
    for item in items:
        en_codigo = buscar_en_codigo(item)
        en_docs = buscar_en_docs(item)
        
        if en_codigo:
            print(f"  [OK] {item}")
            resultados[categoria]["implementado"] += 1
            total_implementado += 1
        elif en_docs:
            print(f"  [ERROR] {item} (solo documentado)")
            resultados[categoria]["documentado"] += 1
            total_documentado_solo += 1
        else:
            print(f"  🚫 {item} (no encontrado)")
            resultados[categoria]["no_encontrado"] += 1
            total_no_encontrado += 1

# ═══════════════════════════════════════════════════════════════════════════════
# REPORTE
# ═══════════════════════════════════════════════════════════════════════════════

total = total_implementado + total_documentado_solo + total_no_encontrado

print("\n" + "="*80)
print("RESULTADO FINAL")
print("="*80)

print(f"""
[OK] IMPLEMENTADO EN CÓDIGO:        {total_implementado:3d} ({total_implementado*100/total:5.1f}%)
[ERROR] SOLO DOCUMENTADO:             {total_documentado_solo:3d} ({total_documentado_solo*100/total:5.1f}%)
🚫 NO ENCONTRADO:                {total_no_encontrado:3d} ({total_no_encontrado*100/total:5.1f}%)
─────────────────────────────────────────────────
TOTAL CONCEPTOS:                 {total:3d}
""")

# VEREDICTO
porcentaje = total_implementado*100/total if total > 0 else 0

print("\n" + "="*80)
if porcentaje >= 85:
    print(f"🛰️  SISTEMA ALTAMENTE CONFIABLE ({porcentaje:.0f}% implementado)")
elif porcentaje >= 70:
    print(f"[WARNING]  SISTEMA FUNCIONAL CON PROMESAS PENDIENTES ({porcentaje:.0f}% implementado)")
else:
    print(f"[CRITICAL] SISTEMA CON MUCHO DOCUMENTADO SIN IMPLEMENTAR ({porcentaje:.0f}% implementado)")

print("="*80)

# Guardar JSON
with open(PROJECT_ROOT / "AUDITORIA_EXHAUSTIVA_RESULTADO.json", 'w') as f:
    json.dump({
        "total": total,
        "implementado": total_implementado,
        "solo_documentado": total_documentado_solo,
        "no_encontrado": total_no_encontrado,
        "porcentaje_real": f"{porcentaje:.1f}%",
        "categorias": resultados
    }, f, indent=2)

print("\n[OK] Reporte guardado en AUDITORIA_EXHAUSTIVA_RESULTADO.json")
