#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 5: REPORTE ESTABILIDAD 10 MINUTOS
Análisis estadístico de precisión tras patrulla
"""

import time
import statistics
import sys
import os

# Agregar path del proyecto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from core.system.bus_expander import BusExpander
except ImportError as e:
    print(f"ERROR: No se puede importar Bus: {e}")
    print(f"Path: {sys.path}")
    sys.exit(1)

def reporte_estabilidad(duracion_seg=60):  # Para test: 60 seg en lugar de 600
    """
    Capturar N muestras y analizar estabilidad
    """
    
    print("="*80)
    print(f"FASE 5: REPORTE ESTABILIDAD ({duracion_seg} segundos)")
    print("="*80)
    print(f"\nCapturando {duracion_seg} muestras de datos...\n")
    
    try:
        bus = BusExpander()
    except Exception as e:
        print(f"ERROR inicializando Bus: {e}")
        return False
    
    # Contenedores de datos
    datos = {
        'temperatura': [],
        'presion': [],
        'humedad': []
    }
    
    sensores_map = {
        'temperatura': 'temperatura_c',
        'presion': 'presion_relativa_hpa',
        'humedad': 'humedad_exterior_pct'
    }
    
    # Captura
    for i in range(duracion_seg):
        for nombre_local, sensor_id in sensores_map.items():
            valor = bus.leer(sensor_id)
            if valor is not None:
                datos[nombre_local].append(valor)
        
        if (i + 1) % 10 == 0 or (i + 1) == duracion_seg:
            print(f"  [{i+1:3d}/{duracion_seg}] muestras capturadas...")
        
        time.sleep(1)
    
    # Análisis
    print("\n" + "="*80)
    print("ANÁLISIS ESTADÍSTICO")
    print("="*80)
    
    resultados_ok = 0
    
    for nombre, valores in datos.items():
        if len(valores) < 2:
            print(f"\n{nombre.upper()}: [WARNING]  INSUFICIENTES MUESTRAS ({len(valores)})")
            continue
        
        media = statistics.mean(valores)
        desv = statistics.stdev(valores)
        min_val = min(valores)
        max_val = max(valores)
        varianza = desv ** 2
        
        # Deltas
        diffs = [abs(valores[i+1] - valores[i]) for i in range(len(valores)-1)]
        avg_diff = statistics.mean(diffs)
        max_diff = max(diffs)
        
        print(f"\n{nombre.upper()}:")
        print(f"  Media:           {media:.10f}")
        print(f"  Desv. Estándar:  {desv:.10f}")
        print(f"  Varianza:        {varianza:.10e}")
        print(f"  Rango:           [{min_val:.10f}, {max_val:.10f}]")
        print(f"  Delta promedio:  {avg_diff:.10f}")
        print(f"  Delta máximo:    {max_diff:.10f}")
        print(f"  Muestras:        {len(valores)}")
        
        # Criterios de evaluación
        if desv < 0.1 and avg_diff < 0.001:
            print(f"  Status: [OK] EXCELENTE (señal muy estable)")
            resultados_ok += 1
        elif desv < 1.0 and avg_diff < 0.01:
            print(f"  Status: [OK] BUENA (señal estable)")
            resultados_ok += 1
        elif desv < 5.0:
            print(f"  Status: [WARNING]  MODERADA (ruido residual)")
        else:
            print(f"  Status: [ERROR] INESTABLE (alta variancia)")
    
    # Resumen
    print("\n" + "="*80)
    print(f"RESULTADO: {resultados_ok}/3 sensores con estabilidad BUENA/EXCELENTE")
    
    if resultados_ok >= 2:
        print("[OK] PATRULLA ESTABLE - Acorazado operacional")
        print("[STATS] Status: APTO PARA VIGILANCIA CONTINUA")
        return True
    else:
        print("[WARNING]  PATRULLA INESTABLE - Revisar configuración")
        return False

if __name__ == "__main__":
    # Para test rápido: 60 seg; para producción: 600 seg (10 min)
    duracion = 60  # Cambiar a 600 para patrulla real
    success = reporte_estabilidad(duracion_seg=duracion)
    sys.exit(0 if success else 1)
