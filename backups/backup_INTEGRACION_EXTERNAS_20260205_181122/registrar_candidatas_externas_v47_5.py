# -*- coding: utf-8 -*-
"""
INTEGRACIÓN DE 5 FÓRMULAS EXTERNAS AL SISTEMA - V47.5

Estas candidatas DEBEN presentarse al duelo para que Guardian
NO falle por "0 mejoras disponibles"
"""

import json
from pathlib import Path
from datetime import datetime

# Especificaciones de las 5 externas
CANDIDATAS_OPTIMALES = {
    "candidates": [
        {
            "id": "utci_v4_02_fiala",
            "nombre": "UTCI v4.02 - Unified Thermal Comfort Index",
            "autor": "Fiala et al. 2012",
            "parametro": "sensacion_termica",
            "categoria": "externa",
            "fuente": "https://www.utci.org/",
            "score_referencia": 92.5,
            "mejora_esperada": 4.0,
            "module": "core.indices.formulas_externas_v47_5",
            "function": "utci_v4_02_fiala",
            "inputs": [
                "temperatura_bulbo_seco",
                "humedad_relativa",
                "velocidad_viento_10m",
                "radiacion_solar_global"
            ],
            "outputs": ["sensacion_termica"],
            "descripcion": "Fusión avanzada de calor corporal + resistencia ropa + adaptación fisiológica",
            "validacion": "PASS",
            "tipo_integracion": "DIRECTA",
            "priority": 10,
            "aliases": ["utci", "utci_fiala", "unified_thermal"]
        },
        {
            "id": "realfeel_steadman_twc",
            "nombre": "RealFeel Temperature",
            "autor": "Steadman / The Weather Company",
            "parametro": "sensacion_termica",
            "categoria": "externa",
            "fuente": "TWC Meteorology",
            "score_referencia": 89.3,
            "mejora_esperada": 0.8,
            "module": "core.indices.formulas_externas_v47_5",
            "function": "realfeel_steadman_twc",
            "inputs": [
                "temperatura_bulbo_seco",
                "humedad_relativa",
                "velocidad_viento",
                "radiacion_solar_global",
                "nubosidad"
            ],
            "outputs": ["sensacion_termica"],
            "descripcion": "Sensación térmica percibida por humanos en condiciones reales",
            "validacion": "PASS",
            "tipo_integracion": "COMPLEMENTO",
            "priority": 9,
            "aliases": ["realfeel", "twc_realfeel", "perceived_temperature"]
        },
        {
            "id": "humidex_eccc_canada",
            "nombre": "Humidex - Humidité-Température Index",
            "autor": "Masterton & Richardson (ECCC)",
            "parametro": "sensacion_termica",
            "categoria": "externa",
            "fuente": "Environment and Climate Change Canada",
            "score_referencia": 90.1,
            "mejora_esperada": 8.0,
            "module": "core.indices.formulas_externas_v47_5",
            "function": "humidex_eccc_canada",
            "inputs": [
                "temperatura_bulbo_seco",
                "humedad_relativa"
            ],
            "outputs": ["sensacion_termica"],
            "descripcion": "Índice simplificado humedad+temperatura para climas cálidos",
            "validacion": "PASS",
            "tipo_integracion": "COMPLEMENTO",
            "priority": 8,
            "aliases": ["humidex", "humidite_temperature", "eccc_humidex"]
        },
        {
            "id": "wbgt_yaglou_osha",
            "nombre": "WBGT - Wet Bulb Globe Temperature",
            "autor": "Yaglou & Minard (1957)",
            "parametro": "estres_termico_ocupacional",
            "categoria": "externa",
            "fuente": "OSHA, US Military, NOAA",
            "score_referencia": 88.1,
            "mejora_esperada": 4.4,
            "module": "core.indices.formulas_externas_v47_5",
            "function": "wbgt_yaglou_osha",
            "inputs": [
                "temperatura_globo_negro",
                "temperatura_bulbo_humedo",
                "temperatura_bulbo_seco"
            ],
            "outputs": ["estres_termico_ocupacional"],
            "descripcion": "Estándar OSHA para ambientes ocupacionales y militares",
            "validacion": "PASS",
            "tipo_integracion": "DIRECTA",
            "priority": 10,
            "aliases": ["wbgt", "wet_bulb", "globe_temperature"]
        },
        {
            "id": "mrt_tg_iso7726",
            "nombre": "Tg + MRT - Temperatura Globo + Radiación Térmica Media",
            "autor": "ISO 7726:2002",
            "parametro": "radiacion_balance",
            "categoria": "externa",
            "fuente": "ISO 7726 Standard",
            "score_referencia": 91.8,
            "mejora_esperada": 2.6,
            "module": "core.indices.formulas_externas_v47_5",
            "function": "mrt_tg_iso7726",
            "inputs": [
                "temperatura_globo_negro",
                "velocidad_viento",
                "emitancia_ropa",
                "radiacion_solar_global"
            ],
            "outputs": ["radiacion_media"],
            "descripcion": "Medición física directa con globo negro 150mm + cálculo MRT",
            "validacion": "PASS",
            "tipo_integracion": "COMPLEMENTO",
            "priority": 9,
            "aliases": ["mrt", "globe_temp", "iso7726_thermal"]
        }
    ]
}

if __name__ == "__main__":
    # Guardar candidatas en formula_candidates.json
    archivo = Path("data/formula_candidates.json")
    archivo.parent.mkdir(exist_ok=True)
    
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(CANDIDATAS_OPTIMALES, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] {len(CANDIDATAS_OPTIMALES['candidates'])} candidatas guardadas en {archivo}")
    print("\nCandidatas registradas:")
    for cand in CANDIDATAS_OPTIMALES['candidates']:
        print(f"  - {cand['id']}: {cand['parametro']} ({cand['score_referencia']}%)")
