#!/usr/bin/env python3
"""
🗺️ GENERADOR DE MAPA DE DEPENDENCIAS - Bus de Estado Global
Exporta el GRAFO_DEPENDENCIAS_V20 a JSON y Markdown.
Permite auditar CERO REDUNDANCIA en el sistema.
"""

import sys
import os

# Añadir raíz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.indices.bus_estado_global import exportar_mapa_dependencias

def main():
    print("=" * 80)
    print("🗺️  EXPORTANDO MAPA DE DEPENDENCIAS V2.0")
    print("=" * 80)
    print()
    
    # Ruta de salida
    ruta_docs = os.path.join(os.path.dirname(__file__), '..', 'docs')
    os.makedirs(ruta_docs, exist_ok=True)
    
    # Exportar a JSON y Markdown
    json_path, md_path = exportar_mapa_dependencias(ruta_docs)
    
    print(f"[OK] JSON exportado: {json_path}")
    print(f"[OK] Markdown exportado: {md_path}")
    print()
    print("=" * 80)
    print("[BUSCAR] AUDITORÍA:")
    print("   - Cada predicción tiene declaradas sus dependencias 'consume'")
    print("   - Cada predicción declara qué variables 'publica'")
    print("   - El Bus garantiza que cada variable se calcula UNA SOLA VEZ")
    print("   - Verificar estadísticas del Bus tras ejecución completa")
    print("=" * 80)

if __name__ == "__main__":
    main()
