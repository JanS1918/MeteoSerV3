#!/usr/bin/env python3
"""
[BUSCAR] AUDITOR DE REDUNDANCIA - Bus de Estado Global V2.0
Verifica que el sistema cumple con el mandato de CERO REDUNDANCIA.
"""

import sys
import os
import json

# Añadir raíz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.indices.bus_estado_global import GRAFO_DEPENDENCIAS_V20, BusEstadoGlobal

def analizar_grafo_dependencias():
    """Analiza el grafo estático de dependencias."""
    print("=" * 80)
    print("[STATS] ANÁLISIS ESTÁTICO DEL GRAFO DE DEPENDENCIAS")
    print("=" * 80)
    print()
    
    # Contar productores por variable
    productores = {}
    for pred_id, info in GRAFO_DEPENDENCIAS_V20.items():
        for var in info["publica"]:
            if var not in productores:
                productores[var] = []
            productores[var].append(pred_id)
    
    # Detectar múltiples productores (VIOLACIÓN CRÍTICA)
    multiples_productores = {var: prods for var, prods in productores.items() if len(prods) > 1}
    
    if multiples_productores:
        print("[ERROR] VIOLACIÓN CRÍTICA: Variables con múltiples productores")
        print("   (Cada variable debe tener UN SOLO productor)")
        print()
        for var, prods in multiples_productores.items():
            print(f"   [WARNING]  `{var}`: {len(prods)} productores")
            for prod in prods:
                print(f"      - {prod}")
        print()
        return False
    else:
        print("[OK] INTEGRIDAD: Cada variable tiene UN SOLO productor")
        print()
    
    # Análisis de reutilización
    consumos = {}
    for pred_id, info in GRAFO_DEPENDENCIAS_V20.items():
        for var in info["consume"]:
            if var not in consumos:
                consumos[var] = []
            consumos[var].append(pred_id)
    
    print("📈 TOP 10 VARIABLES MÁS REUTILIZADAS:")
    print()
    top_reutilizadas = sorted(consumos.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for var, consumidores in top_reutilizadas:
        print(f"   {len(consumidores):2d}x `{var}`")
    print()
    
    # Predicciones base (fuentes de verdad)
    predicciones_base = [pred_id for pred_id, info in GRAFO_DEPENDENCIAS_V20.items() 
                         if not info["consume"]]
    print(f"[TARGET] PREDICCIONES BASE (Fuentes de Verdad): {len(predicciones_base)}")
    for pred in predicciones_base:
        vars_publicadas = ", ".join([f"`{v}`" for v in GRAFO_DEPENDENCIAS_V20[pred]["publica"]])
        print(f"   - {pred}: {vars_publicadas}")
    print()
    
    return True

def verificar_cobertura_codigo():
    """Verifica qué predicciones ya implementan el patrón Bus."""
    print("=" * 80)
    print("🔧 VERIFICACIÓN DE IMPLEMENTACIÓN EN CÓDIGO")
    print("=" * 80)
    print()
    
    env_indices_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'indices', 'environmental_indices.py')
    
    if not os.path.exists(env_indices_path):
        print(f"[ERROR] No se encuentra: {env_indices_path}")
        return False
    
    with open(env_indices_path, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Detectar métodos que publican en el Bus
    publicadores = []
    consumidores = []
    
    for linea in contenido.split('\n'):
        if 'self._bus.publicar(' in linea or 'bus.publicar(' in linea:
            publicadores.append(linea.strip())
        if 'self._bus.consumir(' in linea or 'bus.consumir(' in linea:
            consumidores.append(linea.strip())
    
    print(f"📤 PUBLICACIONES DETECTADAS: {len(publicadores)}")
    print(f"📥 CONSUMOS DETECTADOS: {len(consumidores)}")
    print()
    
    if len(publicadores) == 0:
        print("[WARNING]  ADVERTENCIA: No se detectaron publicaciones al Bus")
        print("   El sistema aún no está integrado completamente")
        return False
    
    print("[OK] Sistema parcialmente integrado con el Bus")
    print()
    
    return True

def generar_recomendaciones():
    """Genera recomendaciones basadas en el análisis."""
    print("=" * 80)
    print("💡 RECOMENDACIONES")
    print("=" * 80)
    print()
    
    print("1. CONVERSIÓN MASIVA:")
    print("   - Identificar métodos que calculan variables del GRAFO")
    print("   - Aplicar patrón: consumir → calcular → publicar")
    print("   - Priorizar variables con mayor reutilización")
    print()
    
    print("2. SUBFÓRMULAS (Muñecas Rusas):")
    print("   - Identificar cálculos intermedios útiles")
    print("   - Publicar subfórmulas para reutilización")
    print("   - Ejemplo: densidad_aire publica también temp_virtual, Z")
    print()
    
    print("3. AUDITORÍA DINÁMICA:")
    print("   - Ejecutar sistema completo con datos reales")
    print("   - Verificar estadísticas: eficiencia_reutilizacion >= 90%")
    print("   - Inspeccionar logs del Bus para detectar anomalías")
    print()
    
    print("4. TESTING:")
    print("   - Crear test que verifique que cada variable se publica UNA VEZ")
    print("   - Validar que consumidores no recalculan")
    print("   - Comparar tiempos: pre-Bus vs post-Bus")
    print()

def main():
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "AUDITOR DE REDUNDANCIA V2.0" + " " * 31 + "║")
    print("║" + " " * 15 + "Bus de Estado Global - Análisis Estático" + " " * 23 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    exito = True
    
    # Análisis del grafo
    if not analizar_grafo_dependencias():
        exito = False
    
    # Verificación de código
    if not verificar_cobertura_codigo():
        exito = False
    
    # Recomendaciones
    generar_recomendaciones()
    
    print("=" * 80)
    if exito:
        print("[OK] AUDITORÍA COMPLETADA: Sistema estructuralmente correcto")
        print("   Continuar con conversión masiva de predicciones")
    else:
        print("[WARNING]  AUDITORÍA INCOMPLETA: Revisar violaciones detectadas")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
