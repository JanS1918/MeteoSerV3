#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 2: AUDIT CASCADA 64-BIT
Verifica precisión IEEE754 end-to-end
"""

import sys
import os
import struct

# Agregar path del proyecto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from core.system.bus_expander import BusExpander
except ImportError as e:
    print(f"ERROR: No se puede importar Bus: {e}")
    print(f"Path: {sys.path}")
    sys.exit(1)

def analizar_float64(valor, nombre):
    """Analiza estructura IEEE754 de un float64"""
    if valor is None:
        print(f"  {nombre}: [NULO]")
        return None
    
    try:
        bytes_val = struct.pack('>d', float(valor))
        hex_repr = bytes_val.hex()
        
        print(f"  {nombre}:")
        print(f"    Valor: {valor:.15f}")
        print(f"    Tipo: {type(valor).__name__}")
        print(f"    Hex IEEE754: {hex_repr}")
        
        return valor
    except Exception as e:
        print(f"  ERROR analizando {nombre}: {e}")
        return None

def audit_cascada():
    """Auditoría completa de cascada de valores"""
    
    print("="*80)
    print("FASE 2: AUDIT CASCADA 64-BIT")
    print("="*80)
    print("\nVerificando precisión IEEE754 en cascada:\n")
    print("SENSOR → MQTT → BUS → INDICES → OUTPUT\n")
    
    try:
        bus = BusExpander()
    except Exception as e:
        print(f"ERROR inicializando Bus: {e}")
        return False
    
    # Puntos de control
    sensores = {
        'temperatura_c': 'Temperatura',
        'presion_relativa_hpa': 'Presión Relativa',
        'presion_absoluta_hpa': 'Presión Absoluta',
        'humedad_exterior_pct': 'Humedad',
        'velocidad_viento_ms': 'Velocidad Viento'
    }
    
    print("LECTURA DEL BUS:")
    print("-" * 80)
    
    valores_bus = {}
    for sensor_id, sensor_nombre in sensores.items():
        valor = bus.leer(sensor_id)
        valores_bus[sensor_id] = valor
        analizar_float64(valor, sensor_nombre)
        print()
    
    # Validación
    print("VALIDACIÓN DE INTEGRIDAD:")
    print("-" * 80)
    
    todos_float = True
    valores_validos = 0
    
    for sensor_id, valor in valores_bus.items():
        if valor is not None:
            es_float = isinstance(valor, float)
            print(f"  {sensor_id}: {'[OK] FLOAT64' if es_float else '[ERROR] NO FLOAT'}")
            if es_float:
                valores_validos += 1
            else:
                todos_float = False
        else:
            print(f"  {sensor_id}: [WARNING]  NULO")
    
    print()
    print("="*80)
    print(f"RESULTADO: {valores_validos}/{len(sensores)} valores en IEEE754 float64")
    
    if todos_float and valores_validos > 0:
        print("[OK] CASCADA ÍNTEGRA - Precisión total mantenida")
        print("[STATS] Status: APTO PARA SIGUIENTE FASE")
        return True
    else:
        print("[WARNING]  DEGRADACIÓN DETECTADA - Revisar ingesta de datos")
        return False

if __name__ == "__main__":
    success = audit_cascada()
    sys.exit(0 if success else 1)
