"""
═══════════════════════════════════════════════════════════════════════════
[GUARDIAN] V47.0 SUMMUM ABSOLUTO - SELLO SHA-256
═══════════════════════════════════════════════════════════════════════════

PROPÓSITO:
    Generar hash SHA-256 del arsenal V47.0 completo.
    Garantiza integridad de:
    - 5 componentes V47.0
    - 3 integraciones en environmental_indices.py / bus_expander.py
    - Guardian 25 Capas
    - MOS Validator

COMPONENTES V47.0:
    1. Prata (1996) - LW radiación cielo
    2. Wright (2005) - ET nocturna
    3. UTCI v2 (Blazejczyk 2013) - Zonas extremas
    4. Deardorff V47.0 + Prata - T_min ±0.2°C
    5. Kalman Soil WH51 - Filtro ruido

INTEGRACIÓN:
    - Wright → environmental_indices.py (línea ~4325)
    - UTCI v2 → environmental_indices.py (línea ~1145)
    - Deardorff V47.0 → bus_expander.py (línea ~2262 + 2443)
    - Kalman → bus_expander.py (línea ~2836)

AUTOR: V47.0 SUMMUM
FECHA: 2025-01-28
═══════════════════════════════════════════════════════════════════════════
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

V47_COMPONENTS = {
    "formulas": [
        "core/indices/radiacion_lw_prata.py",
        "core/indices/et_nocturna_wright.py",
        "core/indices/utci_v2_blazejczyk.py",
        "core/indices/deardorff_v47_0_prata_integration.py",
        "core/indices/kalman_soil_wh51.py",
    ],
    "wrappers": [
        "core/indices/radiacion_lw_wrapper.py",
        "core/indices/et_wright_integration.py",
        "core/indices/utci_v2_wrapper.py",
    ],
    "integration_files": [
        "core/indices/environmental_indices.py",
        "core/system/bus_expander.py",
    ],
    "audit_tools": [
        "GUARDIAN_25_CAPAS_AUDITORIA_V47.py",
        "core/validation/mos_internal_validator.py",
    ],
}

MANIFEST_PATH = Path("V47_0_SUMMUM_MANIFEST.json")

# ═══════════════════════════════════════════════════════════════════════════
# 🔐 GENERADOR DE HASH
# ═══════════════════════════════════════════════════════════════════════════

def calcular_hash_archivo(filepath: Path) -> str:
    """
    Calcula SHA-256 de un archivo.
    
    Args:
        filepath: Ruta al archivo
    
    Returns:
        Hash SHA-256 hexadecimal
    """
    sha256 = hashlib.sha256()
    
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"
    except Exception as e:
        return f"ERROR: {e}"


def generar_manifest_v47() -> Dict:
    """
    Genera manifest completo con hashes de todos los componentes V47.0.
    
    Returns:
        Diccionario con manifest completo
    """
    manifest = {
        "version": "V47.0 SUMMUM ABSOLUTO",
        "timestamp": datetime.now().isoformat(),
        "componentes": {},
        "hash_global": None,
    }
    
    # Hash por categoría
    hash_acumulado = hashlib.sha256()
    
    for categoria, archivos in V47_COMPONENTS.items():
        manifest["componentes"][categoria] = {}
        
        for archivo_relativo in archivos:
            filepath = Path(archivo_relativo)
            hash_archivo = calcular_hash_archivo(filepath)
            
            manifest["componentes"][categoria][archivo_relativo] = {
                "hash": hash_archivo,
                "existe": filepath.exists(),
                "tamaño_bytes": filepath.stat().st_size if filepath.exists() else 0,
            }
            
            # Acumular para hash global
            if hash_archivo != "FILE_NOT_FOUND" and not hash_archivo.startswith("ERROR"):
                hash_acumulado.update(hash_archivo.encode())
    
    # Hash global V47.0
    manifest["hash_global"] = hash_acumulado.hexdigest()
    
    return manifest


def verificar_integridad_v47(manifest_esperado: Dict) -> Dict:
    """
    Verifica integridad del sistema V47.0 contra manifest.
    
    Args:
        manifest_esperado: Manifest de referencia
    
    Returns:
        Resultado de verificación con archivos modificados/faltantes
    """
    manifest_actual = generar_manifest_v47()
    
    resultado = {
        "integridad_ok": True,
        "hash_global_coincide": manifest_actual["hash_global"] == manifest_esperado["hash_global"],
        "archivos_modificados": [],
        "archivos_faltantes": [],
    }
    
    # Comparar por archivo
    for categoria, archivos in manifest_esperado["componentes"].items():
        for archivo, info_esperada in archivos.items():
            info_actual = manifest_actual["componentes"].get(categoria, {}).get(archivo, {})
            
            if not info_actual.get("existe", False):
                resultado["archivos_faltantes"].append(archivo)
                resultado["integridad_ok"] = False
            elif info_actual.get("hash") != info_esperada.get("hash"):
                resultado["archivos_modificados"].append(archivo)
                resultado["integridad_ok"] = False
    
    return resultado


# ═══════════════════════════════════════════════════════════════════════════
# [STATS] REPORTE VISUAL
# ═══════════════════════════════════════════════════════════════════════════

def imprimir_reporte_v47(manifest: Dict) -> None:
    """Imprime reporte visual del manifest V47.0."""
    print("\n" + "═" * 70)
    print("[GUARDIAN]  V47.0 SUMMUM ABSOLUTO - SELLO SHA-256")
    print("═" * 70)
    print(f"Timestamp: {manifest['timestamp']}")
    print(f"Hash Global: {manifest['hash_global'][:16]}...{manifest['hash_global'][-16:]}")
    print("═" * 70)
    
    for categoria, archivos in manifest["componentes"].items():
        print(f"\n📁 {categoria.upper().replace('_', ' ')}")
        print("-" * 70)
        
        for archivo, info in archivos.items():
            existe = "[OK]" if info["existe"] else "[ERROR]"
            hash_corto = info["hash"][:12] if info["hash"] != "FILE_NOT_FOUND" else "N/A"
            tamaño_kb = info["tamaño_bytes"] / 1024 if info["tamaño_bytes"] > 0 else 0
            
            print(f"  {existe} {archivo}")
            print(f"      Hash: {hash_corto}... | Tamaño: {tamaño_kb:.1f} KB")
    
    print("\n" + "═" * 70)
    print("[OK] MANIFEST V47.0 GENERADO")
    print("═" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# [LAUNCH] EJECUCIÓN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Generando SHA-256 V47.0 SUMMUM...")
    
    # Generar manifest
    manifest = generar_manifest_v47()
    
    # Guardar a disco
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # Reporte visual
    imprimir_reporte_v47(manifest)
    
    print(f"📁 Manifest guardado en: {MANIFEST_PATH}")
    print(f"🔐 Hash Global V47.0: {manifest['hash_global']}")
    
    # Estadísticas
    total_archivos = sum(len(archivos) for archivos in manifest["componentes"].values())
    archivos_ok = sum(
        1 for categoria in manifest["componentes"].values()
        for info in categoria.values()
        if info["existe"]
    )
    
    print(f"\n[STATS] Estadísticas:")
    print(f"   Total archivos: {total_archivos}")
    print(f"   Archivos OK: {archivos_ok}")
    print(f"   Archivos faltantes: {total_archivos - archivos_ok}")
    
    if archivos_ok == total_archivos:
        print("\n🎉 ¡V47.0 SUMMUM ABSOLUTO COMPLETO!")
    else:
        print("\n[WARNING] Faltan archivos por implementar")
