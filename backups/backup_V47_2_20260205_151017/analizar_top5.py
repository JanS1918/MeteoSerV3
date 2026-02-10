#!/usr/bin/env python3
"""Analisis de TOP 5 peticiones en el Bus V30.0"""

import sys
import random
sys.path.insert(0, '.')

from core.bus.bus_compactor import CompactorBus
from core.bus.whitelist_sagrados_v30 import WhitelistSagradosV30
from core.bus.bus_capas_informacion import obtener_bus

def main():
    bus = obtener_bus()
    compactor = CompactorBus()

    # Parámetros comunes (simulan la carga real del sistema)
    parametros_comunes = [
        'temperatura', 'humedad', 'presion', 'viento', 'lluvia',
        'radiacion_solar', 'utci', 'pmv', 'wbgt', 'gravedad_argentona',
        'hardy_temperatura_bulbo_humedo', 'omm_densidad_temperatura_virtual',
        'rest2_irradiancia_global_horizontal', 'altitud', 'latitud',
        'sistema_cpu_carga', 'sistema_salud_general', 'riesgo_helada',
        'sensacion_termica', 'punto_rocio'
    ]

    # Pesos realistas (algunos parámetros se usan más que otros)
    pesos = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1.5, 1.5, 1.5, 1, 1, 0.5]

    random.seed(42)
    
    # Simular 100 ciclos de acceso
    for ciclo in range(100):
        # Cada ciclo, 50 accesos a parámetros
        for param in random.choices(parametros_comunes, weights=pesos, k=50):
            compactor.rastrear_acceso(param)
            bus.publicar(param, random.random() * 100, nivel='CORE')

    stats = compactor.obtener_estadisticas_detalladas()

    print()
    print('='*80)
    print('TOP 5 PARAMETROS MAS ACCEDIDOS EN EL BUS V30.0')
    print('='*80)

    top_5 = stats['top_10_parametros_accedidos'][:5]

    if top_5:
        print()
        for i, param in enumerate(top_5, 1):
            nombre = param['nombre']
            accesos = param['accesos']
            es_sagrado = WhitelistSagradosV30.es_sagrado(nombre)
            estado = 'TIER 1 (Sagrado)' if es_sagrado else 'TIER 2/3'
            print(f'{i}. {nombre:<45} Accesos: {accesos:>6}  {estado}')
        print()
    else:
        print('NO HAY ESTADISTICAS DISPONIBLES')

    print('='*80)
    print(f'Total ciclos: {stats["ciclos_procesados"]}')
    print()

if __name__ == "__main__":
    main()
