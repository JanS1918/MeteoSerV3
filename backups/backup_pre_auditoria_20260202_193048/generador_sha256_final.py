"""
generador_sha256_final.py
==========================
Genera el SHA256 definitivo de todos los módulos V2.6
y crea el archivo de bloqueo BIBLIA_V26_FINAL.lock
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime


def calcular_sha256_archivo(filepath):
    """Calcula SHA256 de un archivo"""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for bloque in iter(lambda: f.read(4096), b""):
                sha256.update(bloque)
        return sha256.hexdigest()
    except Exception as e:
        return f"ERROR: {e}"


def generar_sello_definitivo():
    """Genera el sello SHA256 definitivo"""
    print("="*70)
    print("GENERANDO SHA256 DEFINITIVO - ACORAZADO ARGENTONA V2.6")
    print("="*70)
    print("")
    
    modulos_criticos = [
        "elite_motors_v25.py",
        "bucholtz_rayleigh_v25.py",
        "vector_aproximacion_v26.py",
        "integracion_elite_motors_v25.py",
        "core/correccion_geofisica_v26.py",
        "protocolo_certificacion_arranque_v26.py"
    ]
    
    hashes = {}
    
    for modulo in modulos_criticos:
        path = Path(modulo)
        if path.exists():
            hash_sha256 = calcular_sha256_archivo(path)
            hashes[modulo] = hash_sha256
            print(f"[SHA256] {modulo}")
            print(f"         {hash_sha256}")
            print("")
        else:
            hashes[modulo] = "ARCHIVO_NO_ENCONTRADO"
            print(f"[WARN] {modulo}: NO ENCONTRADO")
            print("")
    
    # Hash maestro
    hash_maestro = hashlib.sha256(
        json.dumps(hashes, sort_keys=True).encode()
    ).hexdigest()
    
    print("="*70)
    print("HASH MAESTRO:")
    print(hash_maestro)
    print("="*70)
    print("")
    
    # Crear archivo de bloqueo
    bloqueo = {
        "version": "2.6",
        "fecha_sello": datetime.now().isoformat(),
        "hash_maestro": hash_maestro,
        "modulos": hashes,
        "metrologia": {
            "factor_z": 0.999996,
            "desviacion_ideal_pct": 0.0004,
            "angulo_ekman_grados": 22.5,
            "rugosidad_argentona": 0.15,
            "declinacion_magnetica_grados": 2.0,
            "densidad_diferencial_g_m3": 13.96
        },
        "estado": "SELLADO_Y_BLOQUEADO"
    }
    
    with open("BIBLIA_V26_FINAL.lock", "w", encoding="utf-8") as f:
        json.dump(bloqueo, f, indent=2, ensure_ascii=False)
    
    print("="*70)
    print("ARCHIVO DE BLOQUEO CREADO: BIBLIA_V26_FINAL.lock")
    print("="*70)
    print("")
    
    # Mostrar contenido
    print("CONTENIDO DEL SELLO:")
    print(json.dumps(bloqueo, indent=2, ensure_ascii=False))
    print("")
    
    return bloqueo


if __name__ == "__main__":
    sello = generar_sello_definitivo()
    
    print("")
    print("="*70)
    print("ACORAZADO ARGENTONA V2.6 - SELLADO DEFINITIVAMENTE")
    print("="*70)
    print(f"Hash Maestro: {sello['hash_maestro']}")
    print(f"Fecha: {sello['fecha_sello']}")
    print(f"Estado: {sello['estado']}")
    print("="*70)
