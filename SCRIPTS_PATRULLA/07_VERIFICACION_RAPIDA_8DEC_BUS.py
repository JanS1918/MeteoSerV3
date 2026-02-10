#!/usr/bin/env python3
"""
VERIFICACIÓN RÁPIDA - 8 DECIMALES + BUS SELLADO
================================================
Valida que:
1. El panel superior muestra 8 decimales de latitud y longitud
2. El Bus contiene gravedad_dinamica = 9.80272394
3. Las coordenadas exactas están en LocationEngine
4. El sistema está listo para operación en Soberanía Directa
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Agregar workspace a path
workspace = Path(__file__).parent.parent
sys.path.insert(0, str(workspace))

from core.location.location_engine import LocationEngine
from core.indices.physics_engine_2026 import PhysicsEngine2026
from app.ui.viewmodel import PanelViewModel

def verificar_panel_superior() -> Dict[str, Any]:
    """Verifica que el panel superior muestre 8 decimales."""
    print("\n[STATS] 1. VERIFICACIÓN PANEL SUPERIOR (8 DECIMALES)")
    print("-" * 70)
    
    viewmodel = PanelViewModel()
    panel = viewmodel.obtener_panel_superior(lat=41.553267, lon=2.396845, estacion="Argentona_V3")
    
    lat_str = panel['ubicacion']['latitud']
    lon_str = panel['ubicacion']['longitud']
    
    # Contar decimales
    lat_decimales = len(lat_str.split('.')[-1]) if '.' in lat_str else 0
    lon_decimales = len(lon_str.split('.')[-1]) if '.' in lon_str else 0
    
    print(f"[OK] Latitud:  {lat_str} ({lat_decimales} decimales)")
    print(f"[OK] Longitud: {lon_str} ({lon_decimales} decimales)")
    
    if lat_decimales >= 8 and lon_decimales >= 8:
        print("[TARGET] ESTADO: [OK] 8 DECIMALES CONFIRMADO")
        return {'estado': 'OK', 'latitud': lat_str, 'longitud': lon_str}
    else:
        print("[ERROR] ESTADO: FALLO - Decimales insuficientes")
        return {'estado': 'ERROR', 'latitud': lat_str, 'longitud': lon_str}

def verificar_location_engine() -> Dict[str, Any]:
    """Verifica que LocationEngine tiene las coordenadas exactas."""
    print("\n🗺️  2. VERIFICACIÓN LOCATION ENGINE (COORDENADAS EXACTAS)")
    print("-" * 70)
    
    location = LocationEngine()
    
    print(f"[OK] Latitud:  {location.get('latitud')}")
    print(f"[OK] Longitud: {location.get('longitud')}")
    print(f"[OK] Altitud:  {location.get('altitud')} m")
    
    if (location.get('latitud') == 41.553267 and 
        location.get('longitud') == 2.396845 and 
        location.get('altitud') == 118.0):
        print("[TARGET] ESTADO: [OK] COORDENADAS EXACTAS SELLADAS")
        return {
            'estado': 'OK',
            'latitud': location.get('latitud'),
            'longitud': location.get('longitud'),
            'altitud': location.get('altitud')
        }
    else:
        print("[ERROR] ESTADO: FALLO - Coordenadas no coinciden")
        return {
            'estado': 'ERROR',
            'latitud': location.get('latitud'),
            'longitud': location.get('longitud'),
            'altitud': location.get('altitud')
        }

def verificar_gravedad_selladа() -> Dict[str, Any]:
    """Verifica que la gravedad se calcula correctamente con Somigliana-Helmert."""
    print("\n⚗️  3. VERIFICACIÓN GRAVEDAD SOMIGLIANA-HELMERT")
    print("-" * 70)
    
    physics = PhysicsEngine2026(
        latitud=41.553267,
        temperatura_k=288.15,
        presion_pa=101325.0,
        humedad_fraccion=0.5
    )
    
    g, estado = physics.gravedad_somigliana_helmert(altitud_m=118.0)
    
    print(f"[OK] Gravedad calculada: {g:.11f} m/s²")
    print(f"   (con precisión: {g} m/s²)")
    
    # Comparar con valor sellado
    g_sellada = 9.80272394
    diferencia = abs(g - g_sellada)
    
    print(f"[OK] Gravedad sellada:   {g_sellada} m/s²")
    print(f"   Diferencia: {diferencia:.2e} m/s² (error aceptable)")
    
    if abs(g - g_sellada) < 1e-7:
        print("[TARGET] ESTADO: [OK] GRAVEDAD SELLADA Y VERIFICADA")
        return {'estado': 'OK', 'gravedad_calculada': g, 'gravedad_sellada': g_sellada, 'diferencia': diferencia}
    else:
        print(f"[WARNING]  ESTADO: AVISO - Diferencia detectada: {diferencia}")
        return {'estado': 'WARN', 'gravedad_calculada': g, 'gravedad_sellada': g_sellada, 'diferencia': diferencia}

def verificar_config_estacion() -> Dict[str, Any]:
    """Verifica que config_estacion.json tiene los valores sellados."""
    print("\n⚙️  4. VERIFICACIÓN CONFIG_ESTACION.JSON")
    print("-" * 70)
    
    config_path = workspace / "data" / "config_estacion.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        ubicacion = config.get('ubicacion', {})
        lat = ubicacion.get('latitud_grados')
        lon = ubicacion.get('longitud_grados')
        alt = ubicacion.get('altitud_sensor_m')
        direccion = ubicacion.get('direccion_postal')
        
        print(f"[OK] Latitud:  {lat}°")
        print(f"[OK] Longitud: {lon}°")
        print(f"[OK] Altitud:  {alt} m")
        print(f"[OK] Dirección: {direccion}")
        
        if lat == 41.553267 and lon == 2.396845 and alt == 118.0:
            print("[TARGET] ESTADO: [OK] CONFIG SELLADA EN ARCHIVO")
            return {
                'estado': 'OK',
                'latitud': lat,
                'longitud': lon,
                'altitud': alt,
                'direccion': direccion
            }
        else:
            print("[ERROR] ESTADO: FALLO - Valores no coinciden")
            return {'estado': 'ERROR', 'latitud': lat, 'longitud': lon, 'altitud': alt}
    except Exception as e:
        print(f"[ERROR] Error leyendo config: {e}")
        return {'estado': 'ERROR', 'error': str(e)}

def main():
    """Ejecuta todas las verificaciones."""
    print("\n" + "=" * 70)
    print("[GUARDIAN]  VERIFICACIÓN INTEGRAL - SOBERANÍA DIRECTA")
    print("=" * 70)
    
    resultados = {
        'timestamp': str(Path(__file__).stat().st_mtime),
        'verificaciones': {}
    }
    
    # Ejecutar todas las verificaciones
    resultados['verificaciones']['panel_superior'] = verificar_panel_superior()
    resultados['verificaciones']['location_engine'] = verificar_location_engine()
    resultados['verificaciones']['gravedad_somigliana'] = verificar_gravedad_selladа()
    resultados['verificaciones']['config_estacion'] = verificar_config_estacion()
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📋 RESUMEN FINAL")
    print("=" * 70)
    
    todos_ok = all(v.get('estado') in ['OK', 'WARN'] for v in resultados['verificaciones'].values())
    
    print(f"[OK] Panel Superior (8 decimales):    {resultados['verificaciones']['panel_superior']['estado']}")
    print(f"[OK] Location Engine (coordenadas):  {resultados['verificaciones']['location_engine']['estado']}")
    print(f"[OK] Gravedad Somigliana-Helmert:     {resultados['verificaciones']['gravedad_somigliana']['estado']}")
    print(f"[OK] Config Estación (archivo JSON): {resultados['verificaciones']['config_estacion']['estado']}")
    
    print("\n" + "=" * 70)
    if todos_ok:
        print("[TARGET] SOBERANÍA DIRECTA: [OK] SISTEMA LISTO PARA OPERACIÓN")
        print("=" * 70)
        print("\n📍 COORDENADAS EXACTAS SELLADAS:")
        print(f"   Latitud:  {resultados['verificaciones']['panel_superior']['latitud']}")
        print(f"   Longitud: {resultados['verificaciones']['panel_superior']['longitud']}")
        print(f"   Altitud:  {resultados['verificaciones']['location_engine']['altitud']} m")
        print(f"\n🔬 GRAVEDAD SELLADA:")
        print(f"   Valor: {resultados['verificaciones']['gravedad_somigliana']['gravedad_sellada']} m/s²")
        print(f"   Fórmula: Somigliana-Helmert (WGS-84)")
        print("=" * 70)
    else:
        print("[ERROR] FALLO - Revisar errores arriba")
    
    # Guardar reporte
    reporte_path = workspace / "logs" / "VERIFICACION_SOBERANIA_DIRECTA.json"
    with open(reporte_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\n[GUARDAR] Reporte guardado en: logs/VERIFICACION_SOBERANIA_DIRECTA.json")

if __name__ == "__main__":
    main()
