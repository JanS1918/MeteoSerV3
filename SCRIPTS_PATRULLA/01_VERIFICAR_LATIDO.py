#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 1: VERIFICAR PRIMER LATIDO
Script de captura inicial del MQTT
"""

import time
import sys
import os

# Agregar path del proyecto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from core.system.bus_expander import BusExpander
    from core.integration.ecowitt_receiver import actualizar_sensores_ecowitt
except ImportError as e:
    print(f"ERROR: No se puede importar módulos: {e}")
    print(f"Path: {sys.path}")
    sys.exit(1)

def verificar_latido():
    """Captura primer ciclo de datos del Bus"""
    
    print("="*80)
    print("FASE 1: VERIFICAR PRIMER LATIDO")
    print("="*80)
    print("\nEscuchando primer ciclo MQTT del Acorazado...\n")
    
    try:
        bus = BusExpander()
    except Exception as e:
        print(f"ERROR inicializando Bus: {e}")
        return False
    
    ciclos_exitosos = 0
    max_intentos = 10
    
    for ciclo in range(max_intentos):
        try:
            temp = bus.leer("temperatura_c")
            presion = bus.leer("presion_relativa_hpa")
            humedad = bus.leer("humedad_exterior_pct")
            viento = bus.leer("velocidad_viento_ms")
            radiacion = bus.leer("radiacion_w_m2")
            
            timestamp = time.time()
            
            print(f"[Ciclo {ciclo+1}] {timestamp:.2f}")
            print(f"  • Temperatura: {temp} °C" if temp else "  • Temperatura: [NULO]")
            print(f"  • Presión: {presion} hPa" if presion else "  • Presión: [NULO]")
            print(f"  • Humedad: {humedad} %" if humedad else "  • Humedad: [NULO]")
            print(f"  • Viento: {viento} m/s" if viento else "  • Viento: [NULO]")
            print(f"  • Radiación: {radiacion} W/m²" if radiacion else "  • Radiación: [NULO]")
            
            # Validar tipos
            if temp is not None:
                print(f"  [OK] Temperatura es {type(temp).__name__}")
                if isinstance(temp, float):
                    ciclos_exitosos += 1
            
            print()
            
        except Exception as e:
            print(f"ERROR ciclo {ciclo+1}: {e}\n")
        
        time.sleep(2)
    
    print("="*80)
    print(f"RESULTADO: {ciclos_exitosos}/{max_intentos} ciclos exitosos")
    
    if ciclos_exitosos > 0:
        print("[OK] LATIDO CONFIRMADO - Datos llegando al Bus")
        print("[STATS] Status: LISTO PARA SIGUIENTE FASE")
        return True
    else:
        print("[ERROR] ERROR - No se recibe datos del Bus")
        print("[WARNING]  Verificar MQTT y ecowitt_receiver")
        return False

if __name__ == "__main__":
    success = verificar_latido()
    sys.exit(0 if success else 1)
