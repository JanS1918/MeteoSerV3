#!/usr/bin/env python3
"""
🔧 CONVERSIÓN MASIVA AL PATRÓN BUS
Aplica el patrón de consumir/publicar del Bus a todos los métodos de cálculo.
"""

import sys
import os
import re

# Añadir raíz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mapa de métodos a convertir según GRAFO_DEPENDENCIAS_V20
CONVERSIONES = {
    # Métodos que ya están convertidos (skip)
    "punto_rocio": "DONE",
    "nubosidad_estimada": "DONE",
    "nubosidad": "DONE",
    "_obtener_densidad_aire": "DONE",
    
    # Métodos pendientes de conversión (indicar qué publican y consumen)
    "evapotranspiracion_penman_monteith": {
        "publica": ["et0_penman", "kcb", "ke", "deficit_presion_vapor"],
        "consume": ["punto_rocio", "densidad_aire_kg_m3", "radiacion_neta"]
    },
    "indice_utci": {
        "publica": ["utci", "temp_radiante_media", "velocidad_viento_corregida"],
        "consume": ["punto_rocio", "densidad_aire_kg_m3", "radiacion_neta"]
    },
    # ... más métodos
}

def generar_patron_bus(nombre_metodo, info):
    """
    Genera el código del patrón Bus para un método.
    
    Args:
        nombre_metodo: Nombre del método a convertir
        info: Dict con 'publica' y 'consume'
        
    Returns:
        str: Código generado con el patrón Bus
    """
    consumes = info.get("consume", [])
    publica = info.get("publica", [])
    
    # Header con comentario
    patron = f"""
    # [FAST] CASCADA: Consumir del bus si ya existe
    if self._bus and self._bus.existe("{publica[0] if publica else nombre_metodo}"):
        valor_bus = self._bus.consumir("{publica[0] if publica else nombre_metodo}", "{nombre_metodo}")
        return {{
            "valor": valor_bus,
            "estimado": False,
            "explicacion": "Heredado del Bus de Estado Global (calculado previamente)",
            "fuente_cascada": True
        }}
    
"""
    
    # Consumos de dependencias
    for dep in consumes:
        patron += f"""
    # Consumir {dep} del Bus
    {dep}_bus = self._bus.consumir("{dep}", "{nombre_metodo}") if self._bus else None
"""
    
    # Al final del método, antes del return, insertar publicaciones
    publicaciones = "\n"
    for var in publica:
        publicaciones += f"""
    # [FAST] CASCADA: Publicar {var}
    if self._bus:
        self._bus.publicar(
            "{var}",
            {var}_valor,  # Variable calculada
            "{nombre_metodo}",
            {{"formula": "TODO", "metodo": "{nombre_metodo}"}}
        )
"""
    
    return patron, publicaciones

def main():
    print("=" * 80)
    print("🔧 CONVERSIÓN MASIVA AL PATRÓN BUS")
    print("=" * 80)
    print()
    print("NOTA: Este script genera patrones de código.")
    print("      La integración manual es necesaria para cada método.")
    print()
    
    # Generar código de ejemplo para un método
    print("Ejemplo de código generado para evapotranspiracion_penman_monteith:")
    print("-" * 80)
    patron, publicaciones = generar_patron_bus(
        "evapotranspiracion_penman_monteith",
        CONVERSIONES["evapotranspiracion_penman_monteith"]
    )
    print(patron)
    print("# ... código del método original ...")
    print(publicaciones)
    print("-" * 80)
    print()
    print("Para conversión completa, aplicar este patrón a cada método.")
    print("Total de métodos a convertir:", len([k for k, v in CONVERSIONES.items() if v != "DONE"]))

if __name__ == "__main__":
    main()
