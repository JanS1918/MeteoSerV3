# --- Utilidad para volcar valores físicos publicados en el bus ---
def exportar_valores_fisicos_bus_a_archivo(archivo_destino=None):
    from core.bus.bus_capas_informacion import obtener_bus
    bus = obtener_bus()
    fisicos = bus.query('core:contexto.fisica.*')
    listado = {f.variable: f.valor for f in fisicos}
    import json
    destino = archivo_destino or 'physical_constants_bus_dump.json'
    with open(destino, 'w', encoding='utf-8') as f:
        json.dump(listado, f, indent=2, ensure_ascii=False)
    return destino
# physical_constants_bus.py
"""
Archivo centralizado de constantes y fórmulas físicas volcadas en el bus.
Cada parámetro incluye valor, fórmula, unidades, fuente científica y justificación.

Formato:
{
    'parametro': {
        'valor': ...,
        'unidad': ...,
        'fórmula': ...,
        'fuente': ...,
        'justificación': ...
    },
    ...
}

Ejemplo de uso:
from physical_constants_bus import PHYSICAL_CONSTANTS
valor = PHYSICAL_CONSTANTS['capacidad_calorica_suelo']['valor']
"""

PHYSICAL_CONSTANTS = {
    'capacidad_calorica_suelo': {
        'valor': 870,
        'unidad': 'J/kg·K',
        'fórmula': 'Valor suelo mineral típico (2025)',
        'fuente': 'IPCC AR6 WG1, ScienceDirect',
        'enlace': 'https://www.ipcc.ch/report/ar6/wg1/',
        'justificación': 'Valor actualizado para suelos minerales agrícolas según IPCC AR6 y revisión científica 2025.'
    },
    'conductividad_suelo_wm2k': {
        'valor': 1.7,
        'unidad': 'W/m·K',
        'fórmula': 'Suelo mineral húmedo (2025)',
        'fuente': 'IPCC AR6 WG1, ScienceDirect',
        'enlace': 'https://www.ipcc.ch/report/ar6/wg1/',
        'justificación': 'Valor óptimo para suelos agrícolas húmedos según IPCC AR6 y revisión peer-reviewed.'
    },
    'densidad_suelo': {
        'valor': 1350,
        'unidad': 'kg/m³',
        'fórmula': 'Suelo mineral agrícola (2025)',
        'fuente': 'FAO, ScienceDirect',
        'enlace': 'https://www.fao.org/',
        'justificación': 'Valor actualizado para suelos agrícolas compactos según FAO y revisión científica.'
    },
    'albedo_suelo': {
        'valor': 0.16,
        'unidad': '-',
        'fórmula': 'Suelo agrícola global (2025)',
        'fuente': 'IPCC AR6 WG1',
        'enlace': 'https://www.ipcc.ch/report/ar6/wg1/',
        'justificación': 'Valor medio global para suelos agrícolas según IPCC AR6.'
    },
    'emisividad_suelo': {
        'valor': 0.96,
        'unidad': '-',
        'fórmula': 'Suelo mineral agrícola (2025)',
        'fuente': 'IPCC AR6 WG1, ScienceDirect',
        'enlace': 'https://www.ipcc.ch/report/ar6/wg1/',
        'justificación': 'Valor óptimo para suelos agrícolas según IPCC AR6 y revisión peer-reviewed.'
    },
    'capacidad_calorica_aire': {
        'valor': 1006,
        'unidad': 'J/kg·K',
        'fórmula': 'Cp aire seco a 20°C (2026)',
        'fuente': 'NIST, IPCC AR6',
        'enlace': 'https://www.nist.gov/',
        'justificación': 'Valor estándar internacional actualizado para aire seco.'
    },
    'densidad_aire': {
        'valor': 1.188,
        'unidad': 'kg/m³',
        'fórmula': 'Aire seco a 20°C y 1 atm (2026)',
        'fuente': 'NIST, IPCC AR6',
        'enlace': 'https://www.nist.gov/',
        'justificación': 'Condiciones estándar actualizadas según NIST y IPCC AR6.'
    },
    'conductividad_aire': {
        'valor': 0.026,
        'unidad': 'W/m·K',
        'fórmula': 'Aire seco a 20°C (2026)',
        'fuente': 'NIST, ScienceDirect',
        'enlace': 'https://www.nist.gov/',
        'justificación': 'Valor estándar actualizado para aire seco.'
    },
    'calor_latente_vaporizacion_agua': {
        'valor': 2256000,
        'unidad': 'J/kg',
        'fórmula': 'A 100°C y 1 atm (2026)',
        'fuente': 'IAPWS, NIST',
        'enlace': 'https://www.iapws.org/',
        'justificación': 'Valor internacional actualizado para el agua pura.'
    },
    'calor_latente_fusion_agua': {
        'valor': 333700,
        'unidad': 'J/kg',
        'fórmula': 'A 0°C y 1 atm (2026)',
        'fuente': 'IAPWS, NIST',
        'enlace': 'https://www.iapws.org/',
        'justificación': 'Valor internacional actualizado para el agua pura.'
    },
    'calor_latente_sublimacion_agua': {
        'valor': 2834000,
        'unidad': 'J/kg',
        'fórmula': 'A 0°C y 1 atm (2026)',
        'fuente': 'IAPWS, NIST',
        'enlace': 'https://www.iapws.org/',
        'justificación': 'Valor internacional actualizado para el agua pura.'
    },
    'capacidad_calorica_agua': {
        'valor': 4184,
        'unidad': 'J/kg·K',
        'fórmula': 'A 25°C (2026)',
        'fuente': 'IAPWS, NIST',
        'enlace': 'https://www.iapws.org/',
        'justificación': 'Valor estándar internacional actualizado.'
    },
    'capacidad_calorica_hielo': {
        'valor': 2090,
        'unidad': 'J/kg·K',
        'fórmula': 'A 0°C (2026)',
        'fuente': 'IAPWS, NIST',
        'enlace': 'https://www.iapws.org/',
        'justificación': 'Valor estándar internacional actualizado.'
    },
    'capacidad_calorica_vapor_agua': {
        'valor': 2010,
        'unidad': 'J/kg·K',
        'fórmula': 'A 100°C (2026)',
        'fuente': 'IAPWS, NIST',
        'enlace': 'https://www.iapws.org/',
        'justificación': 'Valor estándar internacional actualizado.'
    },
}
