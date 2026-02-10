#!/usr/bin/env python3
"""Top 5 de peticiones en el Bus V30.0"""

import json
from pathlib import Path
from collections import defaultdict

def analizar_top_peticiones():
    """Analiza y retorna el top 5 de peticiones en el bus"""
    
    # Intentar leer del bus_compactor
    try:
        from core.bus.bus_compactor import BusCompactor
        compactor = BusCompactor()
        stats = compactor.obtener_estadisticas_detalladas()
        
        print("\n" + "="*80)
        print("TOP 5 PARAMETROS MAS ACCEDIDOS EN EL BUS V30.0")
        print("="*80)
        
        top_5 = stats['top_10_parametros_accedidos'][:5]
        
        for i, param in enumerate(top_5, 1):
            nombre = param['nombre']
            accesos = param['accesos']
            print(f"\n{i}. [{nombre}]")
            print(f"   Accesos: {accesos}")
            
            # Verificar si es Tier 1 (sagrado)
            from core.bus.whitelist_sagrados_v30 import WhitelistSagradosV30
            es_sagrado = WhitelistSagradosV30.es_sagrado(nombre)
            if es_sagrado:
                cat = WhitelistSagradosV30.obtener_categoria(nombre)
                print(f"   Estado: TIER 1 (Sagrado) - {cat.value if cat else 'N/A'}")
            else:
                print(f"   Estado: TIER 2/3 (No sagrado)")
        
        print("\n" + "="*80)
        print(f"Total ciclos procesados: {stats['ciclos_procesados']}")
        print(f"Deduplicaciones: {stats['deduplicaciones_totales']}")
        print(f"Compresiones: {stats['compresiones_totales']}")
        print("="*80 + "\n")
        
        return top_5
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    analizar_top_peticiones()
