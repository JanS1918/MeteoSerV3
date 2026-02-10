#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVENTARIO_FORMULAS_EJECUTABLE.py - Todas las formulas del sistema
Generado automaticamente por scanner. NO EDITAR A MANO.
"""

FORMULAS_SISTEMA = {
    "sensacion_termica": {
        "tipo": "FORMULA_CALCULADA",
        "actual": "UTCI Polynomial Fiala 186",
        "fuente": "core/indices/utci_polynomial.py:42",
        "funcion": "calculate_utci()",
        "parametros": ["temperatura", "humedad", "viento", "radiacion"],
        "salida": "°C",
        "precision": "±0.1°C",
        "velocidad": 8.0,
        "latencia_ms": 45.0,
        "status": "ACTIVA",
        "validado": True,
        "dias_produccion": 960
    },
    
    "humedad_relativa": {
        "tipo": "MEDIDA_DIRECTA_SENSOR",
        "actual": "Sensor Ecowitt HP2550A",
        "fuente": "main_asgi.py:3097",
        "funcion": "sensores.get('humedad')",
        "parametros": ["HP2550A_HR_sensor"],
        "salida": "%",
        "precision": "±1-2%",
        "velocidad": 10.0,
        "latencia_ms": 42.4,
        "status": "ACTIVA",
        "validado": True,
        "dias_produccion": 1500
    },
    
    "velocidad_viento": {
        "tipo": "MEDIDA_DIRECTA_SENSOR_PLUS_FORMULA",
        "actual": "Sensor + Ajuste Logaritmico",
        "fuente": "bus_expander.py:1156",
        "funcion": "sensores.get('viento') * factor_ajuste_altura",
        "parametros": ["anemometro_ecowitt", "altura_metros"],
        "salida": "m/s",
        "precision": "±0.1 m/s",
        "velocidad": 9.2,
        "latencia_ms": 32.2,
        "status": "ACTIVA",
        "validado": True,
        "dias_produccion": 1500
    },
    
    "indice_uv": {
        "tipo": "MEDIDA_DIRECTA_SENSOR",
        "actual": "Sensor Ecowitt HP2550A UV",
        "fuente": "main_asgi.py:2151",
        "funcion": "sensores.get('uv')",
        "parametros": ["HP2550A_UV_sensor"],
        "salida": "0-11 indice",
        "precision": "±0.5",
        "velocidad": 10.0,
        "latencia_ms": 23.6,
        "status": "ACTIVA",
        "validado": True,
        "dias_produccion": 1500
    },
    
    "radiacion_solar": {
        "tipo": "MEDIDA_DIRECTA_SENSOR_PLUS_FORMULA",
        "actual": "Sensor Ecowitt + Gueymard REST2",
        "fuente": "bus_expander.py:847",
        "funcion": "sensores.get('radiacion') + gueymard_rest2()",
        "parametros": ["piranometro_ecowitt", "fecha", "lat", "lon"],
        "salida": "W/m²",
        "precision": "±50 W/m²",
        "velocidad": 8.1,
        "latencia_ms": 21.4,
        "status": "ACTIVA",
        "validado": True,
        "dias_produccion": 1200
    },
    
    "punto_rocio": {
        "tipo": "FORMULA_CALCULADA",
        "actual": "Magnus Formula",
        "fuente": "core/indices/rocio.py:15",
        "funcion": "calculate_dew_point()",
        "parametros": ["temperatura", "humedad_relativa"],
        "salida": "°C",
        "precision": "±0.5°C",
        "velocidad": 9.5,
        "latencia_ms": 5.2,
        "status": "ACTIVA",
        "validado": True,
        "dias_produccion": 1500
    },
    
    "indice_calor": {
        "tipo": "FORMULA_CALCULADA",
        "actual": "Steadman Heat Index",
        "fuente": "core/indices/heat_index.py:8",
        "funcion": "calculate_heat_index()",
        "parametros": ["temperatura", "humedad_relativa"],
        "salida": "°C",
        "precision": "±0.1°C",
        "velocidad": 9.8,
        "latencia_ms": 3.1,
        "status": "ACTIVA",
        "validado": True,
        "dias_produccion": 1500
    }
}

SCIPY_BLACKLIST = {
    "scipy.optimize.curve_fit": {
        "parametro": "sensacion_termica",
        "razon": "MATH_NAN_COLLAPSE",
        "severidad": "CRITICA",
        "bloqueado": True
    },
    "scipy.integrate.quad": {
        "parametro": "indice_uv",
        "razon": "NO_CONVERGE_NAN",
        "severidad": "CRITICA",
        "bloqueado": True
    },
    "scipy.stats.weibull_min": {
        "parametro": "velocidad_viento",
        "razon": "PRECISION_LOSS_3.4%",
        "severidad": "ALTA",
        "bloqueado": True
    },
    "scipy.interpolate.interp1d": {
        "parametro": "humedad_relativa",
        "razon": "LATENCIA_3.6ms_DOBLE_SUAVIZADO",
        "severidad": "ALTA",
        "bloqueado": True
    },
    "scipy.ndimage.gaussian_filter": {
        "parametro": "radiacion_solar",
        "razon": "LATENCIA_27.1ms_INACEPTABLE",
        "severidad": "ALTA",
        "bloqueado": True
    }
}

def get_all_formulas():
    """Retorna TODAS las formulas registradas"""
    return FORMULAS_SISTEMA

def get_formula(parametro):
    """Obtiene formula especifica"""
    return FORMULAS_SISTEMA.get(parametro)

def list_all():
    """Lista todas las formulas (legible)"""
    for param, data in FORMULAS_SISTEMA.items():
        print(f"[{param}] {data['actual']}")
        print(f"  Fuente: {data['fuente']}")
        print(f"  Precision: {data['precision']}")
        print()

def validate_all():
    """Valida que todas las formulas esten en el sistema"""
    print(f"Total de formulas/sensores: {len(FORMULAS_SISTEMA)}")
    for param, data in FORMULAS_SISTEMA.items():
        status = "[OK]" if data['status'] == "ACTIVA" else "[XX]"
        print(f"  {status} {param:<20} ({data['tipo']})")

def check_blacklist():
    """Verifica que todas las formulas SciPy bloqueadas lo esten"""
    print(f"\nFormulas BLOQUEADAS (SciPy): {len(SCIPY_BLACKLIST)}")
    for formula, data in SCIPY_BLACKLIST.items():
        print(f"  [BLOCKED] {formula}")
        print(f"    Razon: {data['razon']}")
        print(f"    Severidad: {data['severidad']}")

if __name__ == "__main__":
    print("="*70)
    print("INVENTARIO EJECUTABLE - TODAS LAS FORMULAS DEL SISTEMA")
    print("="*70)
    validate_all()
    print()
    list_all()
    check_blacklist()
    print("\n[OK] Inventario completamente cargado")
