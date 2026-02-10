#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════════════════════════
[GUARDIAN] VERIFICADOR FINAL - ACORAZADO DE MONTURIOL V3
════════════════════════════════════════════════════════════════════════════════

Verifica que TODOS los componentes están en su lugar antes de arrancar.
"""

import sys
from pathlib import Path
import json

def verificar_archivos():
    """Verificar que todos los archivos críticos existen"""
    print("\n📁 VERIFICACIÓN DE ARCHIVOS:")
    print("=" * 70)
    
    archivos = {
        "core/indices/deardorff_v46_5_final_sentencia.py": "Modelo Deardorff V46.5 FINAL",
        "core/integration/integrador_always_on.py": "Integrador Always-On",
        "main_asgi.py": "Servidor principal (inyección verificada)",
    }
    
    ok = True
    for archivo, descripcion in archivos.items():
        p = Path(archivo)
        if p.exists():
            size = p.stat().st_size
            print(f"[OK] {descripcion}")
            print(f"   └─ {archivo} ({size:,} bytes)")
        else:
            print(f"[ERROR] {descripcion} - NO ENCONTRADO")
            print(f"   └─ {archivo}")
            ok = False
    
    return ok

def verificar_inyeccion():
    """Verificar que el integrador está inyectado en main_asgi.py"""
    print("\n🔌 VERIFICACIÓN DE INYECCIÓN EN main_asgi.py:")
    print("=" * 70)
    
    with open("main_asgi.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    checks = {
        "integrador_always_on": "Import del integrador",
        "ejecutar_integrador_automatico": "Función main del integrador",
        "Integrador Always-On": "Comentario de identificación",
        "gap histórico": "Funcionalidad de recuperación",
    }
    
    ok = True
    for busqueda, descripcion in checks.items():
        if busqueda in content:
            print(f"[OK] {descripcion}")
            print(f"   └─ '{busqueda}' encontrado")
        else:
            print(f"[ERROR] {descripcion} - NO ENCONTRADO")
            print(f"   └─ '{busqueda}' no aparece en main_asgi.py")
            ok = False
    
    return ok

def verificar_imports():
    """Verificar que los módulos se pueden importar"""
    print("\n📦 VERIFICACIÓN DE IMPORTS:")
    print("=" * 70)
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    modules = {
        "core.integration.integrador_always_on": "ejecutar_integrador_automatico",
        "core.indices.deardorff_v46_5_final_sentencia": "calcular_temperatura_minima_v46_5_final",
    }
    
    ok = True
    for modulo, funcion in modules.items():
        try:
            mod = __import__(modulo, fromlist=[funcion])
            func = getattr(mod, funcion)
            print(f"[OK] {modulo}")
            print(f"   └─ {funcion} cargada correctamente")
        except Exception as e:
            print(f"[ERROR] {modulo}")
            print(f"   └─ Error: {e}")
            ok = False
    
    return ok

def verificar_estructura_datos():
    """Verificar que existen directorios de datos"""
    print("\n📂 VERIFICACIÓN DE ESTRUCTURA DE DATOS:")
    print("=" * 70)
    
    directorios = {
        "data": "Histórico y recuperación",
        "logs": "Logs del sistema",
        "core": "Código del core",
        "core/integration": "Módulos de integración",
        "core/indices": "Modelos de índices",
    }
    
    ok = True
    for directorio, descripcion in directorios.items():
        p = Path(directorio)
        if p.exists() and p.is_dir():
            print(f"[OK] {descripcion}")
            print(f"   └─ {directorio}/")
        else:
            print(f"[ERROR] {descripcion}")
            print(f"   └─ {directorio}/ NO EXISTE")
            ok = False
    
    return ok

def verificar_deardorff():
    """Verificar que Deardorff V46.5 FINAL tiene las mejoras"""
    print("\n🔬 VERIFICACIÓN DE MEJORAS DEARDORFF V46.5:")
    print("=" * 70)
    
    with open("core/indices/deardorff_v46_5_final_sentencia.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    mejoras = {
        "k_s\": 2.2": "κ = 2.2 W/(m·K) ✓",
        "InerciaTermicaEdificio": "Inercia térmica edificio ✓",
        "generar_hash_adn_geografia": "ADN geográfico hash ✓",
        "ocaso_topografico_bloquea_evaporacion": "Sincronización ocaso-evaporación ✓",
    }
    
    ok = True
    for busqueda, descripcion in mejoras.items():
        if busqueda in content:
            print(f"[OK] {descripcion}")
        else:
            print(f"[ERROR] {descripcion} - NO ENCONTRADO")
            ok = False
    
    return ok

def verificar_integrador():
    """Verificar que integrador tiene todas las clases"""
    print("\n[REINICIO] VERIFICACIÓN DE INTEGRADOR ALWAYS-ON:")
    print("=" * 70)
    
    with open("core/integration/integrador_always_on.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    clases = {
        "class DetectorGapsHistoricos": "Detector de gaps históricos",
        "class RecuperadorAutomatico": "Recuperador automático",
        "class ProcesadorDatosBrutos": "Procesador de datos",
        "async def ejecutar_integrador_automatico": "Función main async",
    }
    
    ok = True
    for busqueda, descripcion in clases.items():
        if busqueda in content:
            print(f"[OK] {descripcion}")
        else:
            print(f"[ERROR] {descripcion} - NO ENCONTRADO")
            ok = False
    
    return ok

def main():
    print("""
    ════════════════════════════════════════════════════════════════════════════════
    [GUARDIAN]  VERIFICADOR FINAL - ACORAZADO DE MONTURIOL V3
    ════════════════════════════════════════════════════════════════════════════════
    """)
    
    resultados = {
        "Archivos críticos": verificar_archivos(),
        "Inyección en main_asgi.py": verificar_inyeccion(),
        "Imports de módulos": verificar_imports(),
        "Estructura de datos": verificar_estructura_datos(),
        "Mejoras Deardorff V46.5": verificar_deardorff(),
        "Integrador Always-On": verificar_integrador(),
    }
    
    print("\n" + "=" * 70)
    print("[STATS] RESUMEN FINAL:")
    print("=" * 70)
    
    todos_ok = True
    for categoria, resultado in resultados.items():
        estado = "[OK] OK" if resultado else "[ERROR] PROBLEMAS"
        print(f"{estado}: {categoria}")
        todos_ok = todos_ok and resultado
    
    print("=" * 70)
    
    if todos_ok:
        print("""
    ✨ VERIFICACIÓN COMPLETADA - SISTEMA LISTO PARA OPERACIÓN ✨
    
    Puedes arrancar el servidor:
    $ python main_asgi.py
    
    O verificar una vez más:
    $ python verificar_integracion.py
        """)
        return 0
    else:
        print("""
    [ERROR] PROBLEMAS DETECTADOS - REVISAR ARRIBA
    
    Por favor verifica:
    1. Que todos los archivos existen
    2. Que la inyección está en main_asgi.py
    3. Que los módulos se importan correctamente
        """)
        return 1

if __name__ == "__main__":
    sys.exit(main())
