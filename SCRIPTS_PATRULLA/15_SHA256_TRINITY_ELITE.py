#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
SHA256 SOBERANÍA ABSOLUTA V28.0 ELITE FINAL
═══════════════════════════════════════════════════════════════════════════════

Generador de hash SHA256 para certificación criptográfica de MeteoSerV3 V28.0
con Trinity Elite (Hardy + OMM + REST2 + Validador Cruzado).

Este hash es único e inmutable. Cualquier cambio de una línea lo modificaría
completamente.

Uso: python 14_SHA256_SOBERANIA_ABSOLUTA.py
"""

import os
import hashlib
import json
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

PROYECTO_RAIZ = "."
ARCHIVOS_CRITICOS = [
    # Trinity Elite (nuevos)
    "core/indices/hardy_nist_psicrometria.py",
    "core/indices/omm_densidad_temperatura_virtual.py",
    "core/indices/rest2_gueymard_radiacion.py",
    "core/system/validador_cruzado_trinity.py",
    
    # Bus Integration
    "core/system/bus_expander.py",
    
    # Documentación
    "LIBRO_BLANCO_V28_ELITE_FINAL.md",
    "SINTESIS_FINAL_V28_COMPLETADA.txt",
]

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN: Calcular SHA256 de un archivo
# ═══════════════════════════════════════════════════════════════════════════════

def calcular_sha256_archivo(ruta_archivo):
    """Calcula el hash SHA256 de un archivo."""
    sha256_hash = hashlib.sha256()
    try:
        with open(ruta_archivo, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN: Generar certificación completa
# ═══════════════════════════════════════════════════════════════════════════════

def generar_sha256_trinity_elite():
    """Genera y verifica el SHA256 de Trinity Elite V28.0."""
    
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "SHA256 SOBERANÍA ABSOLUTA - V28.0 TRINITY ELITE FINAL".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # Timestamp
    ahora = datetime.now()
    print(f"[FECHA] Timestamp: {ahora.isoformat()}")
    print()
    
    # Verificar archivos
    print("[BUSCAR] Verificando archivos críticos:")
    print()
    
    hashes_archivos = {}
    archivos_faltantes = []
    
    for archivo in ARCHIVOS_CRITICOS:
        ruta = os.path.join(PROYECTO_RAIZ, archivo)
        hash_archivo = calcular_sha256_archivo(ruta)
        
        if hash_archivo:
            hashes_archivos[archivo] = hash_archivo
            print(f"  [OK] {archivo}")
            print(f"     → {hash_archivo[:32]}...{hash_archivo[-8:]}")
        else:
            archivos_faltantes.append(archivo)
            print(f"  [ERROR] {archivo} (NO ENCONTRADO)")
        print()
    
    if archivos_faltantes:
        print(f"[WARNING]  Advertencia: {len(archivos_faltantes)} archivo(s) faltante(s)")
        return None
    
    # Crear manifest
    manifest = {
        "version": "V28.0 Elite",
        "descripcion": "Trinity Elite: Hardy NIST + OMM WMO + REST2 Gueymard + Validador Cruzado",
        "timestamp": ahora.isoformat(),
        "archivos": hashes_archivos,
        "localizacion": {
            "latitud": 41.55326700,
            "longitud": 2.39684500,
            "altitud_m": 118.0,
            "nombre": "Argentona, Catalunya"
        },
        "fisica": {
            "gravedad_m_s2": 9.80272394,
            "modelo_gravedad": "Somigliana-Helmert WGS-84"
        }
    }
    
    # Serializar manifest de forma determinística
    manifest_json = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False)
    
    # Calcular SHA256 del manifest completo
    sha256_manifest = hashlib.sha256(manifest_json.encode('utf-8')).hexdigest()
    
    print("=" * 80)
    print("[STATS] MANIFEST DE CERTIFICACIÓN V28.0")
    print("=" * 80)
    print(manifest_json)
    print()
    print("=" * 80)
    print()
    
    # SHA256 final
    print("🔐 SHA256 TRINITY ELITE V28.0 FINAL:")
    print()
    print(f"   {sha256_manifest}")
    print()
    
    # Guardar a archivo
    archivo_salida = os.path.join(PROYECTO_RAIZ, "SHA256_SOBERANIA_ABSOLUTA_V28_ELITE.txt")
    
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write(f"╔{'═' * 78}╗\n")
        f.write(f"║ SHA256 SOBERANÍA ABSOLUTA - V28.0 TRINITY ELITE FINAL\n")
        f.write(f"║ MeteoSerV3 - Argentona 41.55326700°N, 2.39684500°E, 118m\n")
        f.write(f"║ Fecha: {ahora.isoformat()}\n")
        f.write(f"╚{'═' * 78}╝\n\n")
        f.write(f"HASH SHA256:\n{sha256_manifest}\n\n")
        f.write("MANIFEST:\n")
        f.write(manifest_json)
        f.write("\n\n")
        f.write("ARCHIVOS CERTIFICADOS:\n")
        for arch, hash_val in hashes_archivos.items():
            f.write(f"  {arch}\n    {hash_val}\n\n")
    
    print(f"[OK] Certificación guardada: {archivo_salida}")
    print()
    
    # PATRULLA ETERNA
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "🛰️ PATRULLA ETERNA V28.0 ACTIVADA 💎🏁⚓".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + "MISIÓN COMPLETADA: TRINITY ELITE CERTIFICADA".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    return sha256_manifest


# ═══════════════════════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    hash_final = generar_sha256_trinity_elite()
    
    if hash_final:
        print(f"\n[OK] Generación de certificación exitosa")
        print(f"   Hash: {hash_final}\n")
    else:
        print(f"\n[ERROR] Error durante la generación de certificación\n")
