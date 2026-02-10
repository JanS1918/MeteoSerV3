# -*- coding: utf-8 -*-
r"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     ÍNDICE MAESTRO DE AUDITORÍAS                            ║
║                        MeteoSerV3 - Febrero 2026                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

PROPÓSITO:
Registro completo de todas las auditorías solicitadas durante el desarrollo.
NO ejecuta auditorías ni guarda datos - solo mantiene el ÍNDICE de nombres
para poder lanzar "batidas de auditorías" cuando se requiera.

MODO DE USO:
1. python SCRIPTS_PATRULLA\INDICE_MAESTRO_AUDITORIAS.py --list
   → Muestra todas las auditorías disponibles
   
2. python SCRIPTS_PATRULLA\INDICE_MAESTRO_AUDITORIAS.py --run NOMBRE
   → Ejecuta auditoría específica
   
3. python SCRIPTS_PATRULLA\INDICE_MAESTRO_AUDITORIAS.py --run-all
   → Ejecuta TODAS las auditorías secuencialmente (batida completa)
   
4. python SCRIPTS_PATRULLA\INDICE_MAESTRO_AUDITORIAS.py --run-category CATEGORIA
   → Ejecuta todas las auditorías de una categoría

ÚLTIMA ACTUALIZACIÓN: 03-Feb-2026 (Post Unificación de Hierro V27-V28)
"""

import sys
import subprocess
from pathlib import Path

# ============================================================================
# REGISTRO MAESTRO DE AUDITORÍAS
# ============================================================================

AUDITORIAS = {
    # ────────────────────────────────────────────────────────────────────
    # CATEGORÍA: SALUD DEL SISTEMA
    # ────────────────────────────────────────────────────────────────────
    "VERIFICAR_LATIDO": {
        "categoria": "salud_sistema",
        "script": "01_VERIFICAR_LATIDO.py",
        "descripcion": "Verifica que el sistema esté vivo y respondiendo",
        "frecuencia_recomendada": "cada_inicio",
        "tiempo_estimado": "< 5 segundos"
    },
    
    "VERIFICACION_BUS_VIVO": {
        "categoria": "salud_sistema",
        "script": "08_VERIFICACION_BUS_VIVO.py",
        "descripcion": "Verifica que el Bus de Estado Global esté operacional",
        "frecuencia_recomendada": "diaria",
        "tiempo_estimado": "< 10 segundos"
    },
    
    "REPORTE_ESTABILIDAD": {
        "categoria": "salud_sistema",
        "script": "05_REPORTE_ESTABILIDAD.py",
        "descripcion": "Genera reporte completo de estabilidad del sistema",
        "frecuencia_recomendada": "semanal",
        "tiempo_estimado": "30-60 segundos"
    },
    
    # ────────────────────────────────────────────────────────────────────
    # CATEGORÍA: AUDITORÍAS DE PRECISIÓN (IEEE754 / 64-BIT)
    # ────────────────────────────────────────────────────────────────────
    "AUDIT_CASCADA_64BIT": {
        "categoria": "precision",
        "script": "02_AUDIT_CASCADA_64BIT.py",
        "descripcion": "Audita precisión float64 en toda la cadena de cálculo",
        "frecuencia_recomendada": "post_cambios_criticos",
        "tiempo_estimado": "2-5 minutos"
    },
    
    "VERIFICACION_RAPIDA_8DEC_BUS": {
        "categoria": "precision",
        "script": "07_VERIFICACION_RAPIDA_8DEC_BUS.py",
        "descripcion": "Verifica precisión de 8 decimales en coordenadas del Bus",
        "frecuencia_recomendada": "post_cambios_coordenadas",
        "tiempo_estimado": "< 15 segundos"
    },
    
    # ────────────────────────────────────────────────────────────────────
    # CATEGORÍA: AUDITORÍAS DE COHERENCIA (UNIFICACIÓN DE HIERRO)
    # ────────────────────────────────────────────────────────────────────
    "TEST_COHERENCIA_CRUZADA_V27": {
        "categoria": "coherencia",
        "script": "11_TEST_COHERENCIA_CRUZADA_V27.py",
        "descripcion": "Valida coherencia cruzada post-unificación V27.0",
        "frecuencia_recomendada": "post_unificacion",
        "tiempo_estimado": "15-30 segundos"
    },
    
    "TEST_VALIDACION_FINAL": {
        "categoria": "coherencia",
        "script": "11_TEST_VALIDACION_FINAL.py",
        "descripcion": "Validación simplificada de constants.py",
        "frecuencia_recomendada": "cada_inicio",
        "tiempo_estimado": "< 5 segundos"
    },
    
    "AUDITORIA_BUS_COUNTS": {
        "categoria": "coherencia",
        "script": "12_AUDITORIA_BUS_COUNTS.py",
        "descripcion": "Cuenta lecturas/publicaciones del Bus (TOP-20 cada uno)",
        "frecuencia_recomendada": "post_cambios_arquitectura",
        "tiempo_estimado": "30-60 segundos"
    },
    
    # ────────────────────────────────────────────────────────────────────
    # CATEGORÍA: AUDITORÍAS EXTENSIVAS (ANÁLISIS PROFUNDO)
    # ────────────────────────────────────────────────────────────────────
    "AUDITORIA_EXTENSIVA": {
        "categoria": "analisis_profundo",
        "script": "09_AUDITORIA_EXTENSIVA.py",
        "descripcion": "Análisis profundo de fórmulas, unidades, patrones",
        "frecuencia_recomendada": "mensual",
        "tiempo_estimado": "5-10 minutos"
    },
    
    "AUDITORIA_VALIDATOR_FASE2": {
        "categoria": "analisis_profundo",
        "script": "10_AUDITORIA_VALIDATOR_FASE2.py",
        "descripcion": "Validación exhaustiva Fase 2 (post-implementación)",
        "frecuencia_recomendada": "post_fase_desarrollo",
        "tiempo_estimado": "2-5 minutos"
    },
    
    # ────────────────────────────────────────────────────────────────────
    # CATEGORÍA: DOCUMENTACIÓN Y CERTIFICACIÓN
    # ────────────────────────────────────────────────────────────────────
    "LIBRO_BLANCO_ESTACION": {
        "categoria": "documentacion",
        "script": "13_LIBRO_BLANCO_ESTACION.py",
        "descripcion": "Genera catálogo completo de 1147+ parámetros publicados",
        "frecuencia_recomendada": "post_cambios_parametros",
        "tiempo_estimado": "60-90 segundos"
    },
    
    "SHA256_SOBERANIA_ABSOLUTA": {
        "categoria": "certificacion",
        "script": "14_SHA256_SOBERANIA_ABSOLUTA.py",
        "descripcion": "Genera sello criptográfico SHA256 del proyecto completo",
        "frecuencia_recomendada": "pre_release",
        "tiempo_estimado": "30-60 segundos"
    },
    
    "SELLO_DEFINITIVO_SHA256": {
        "categoria": "certificacion",
        "script": "06_SELLO_DEFINITIVO_SHA256.py",
        "descripcion": "Sello SHA256 de integridad del sistema",
        "frecuencia_recomendada": "pre_deployment",
        "tiempo_estimado": "20-40 segundos"
    },
    
    # ────────────────────────────────────────────────────────────────────
    # CATEGORÍA: NOTIFICACIONES Y ALERTAS
    # ────────────────────────────────────────────────────────────────────
    "NOTIFICACION_PATRULLA": {
        "categoria": "alertas",
        "script": "04_NOTIFICACION_PATRULLA.py",
        "descripcion": "Sistema de notificaciones de patrulla operacional",
        "frecuencia_recomendada": "on_demand",
        "tiempo_estimado": "< 5 segundos"
    },
}

# ============================================================================
# AGRUPACIONES LÓGICAS (para batidas especializadas)
# ============================================================================

BATIDAS_PRECONFIGURADAS = {
    "batida_rapida": [
        "VERIFICAR_LATIDO",
        "TEST_VALIDACION_FINAL",
        "VERIFICACION_BUS_VIVO"
    ],
    "batida_precision": [
        "AUDIT_CASCADA_64BIT",
        "VERIFICACION_RAPIDA_8DEC_BUS"
    ],
    "batida_coherencia": [
        "TEST_COHERENCIA_CRUZADA_V27",
        "AUDITORIA_BUS_COUNTS"
    ],
    "batida_profunda": [
        "AUDITORIA_EXTENSIVA",
        "AUDITORIA_VALIDATOR_FASE2",
        "REPORTE_ESTABILIDAD"
    ],
    "batida_certificacion": [
        "LIBRO_BLANCO_ESTACION",
        "SHA256_SOBERANIA_ABSOLUTA",
        "SELLO_DEFINITIVO_SHA256"
    ],
    "batida_completa": list(AUDITORIAS.keys())  # TODAS
}

# ============================================================================
# MOTOR DE EJECUCIÓN
# ============================================================================

def listar_auditorias():
    """Muestra todas las auditorías disponibles"""
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║           AUDITORÍAS DISPONIBLES - MeteoSerV3                          ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝\n")
    
    categorias = {}
    for nombre, info in AUDITORIAS.items():
        cat = info["categoria"]
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append((nombre, info))
    
    for cat in sorted(categorias.keys()):
        print(f"\n📁 {cat.upper().replace('_', ' ')}")
        print("─" * 78)
        for nombre, info in categorias[cat]:
            print(f"  • {nombre}")
            print(f"    Script: {info['script']}")
            print(f"    {info['descripcion']}")
            print(f"    Frecuencia: {info['frecuencia_recomendada']} | Tiempo: {info['tiempo_estimado']}")
    
    print("\n\n📦 BATIDAS PRECONFIGURADAS")
    print("─" * 78)
    for batida, nombres in BATIDAS_PRECONFIGURADAS.items():
        print(f"  • {batida}: {len(nombres)} auditorías")


def ejecutar_auditoria(nombre):
    """Ejecuta una auditoría específica"""
    if nombre not in AUDITORIAS:
        print(f"[ERROR] Auditoría '{nombre}' no encontrada")
        return False
    
    info = AUDITORIAS[nombre]
    script_path = Path(__file__).parent / info["script"]
    
    if not script_path.exists():
        print(f"[ERROR] Script no encontrado: {script_path}")
        return False
    
    print(f"\n{'='*78}")
    print(f"[BUSCAR] EJECUTANDO: {nombre}")
    print(f"📄 Script: {info['script']}")
    print(f"⏱️  Tiempo estimado: {info['tiempo_estimado']}")
    print(f"{'='*78}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=script_path.parent.parent,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n[OK] {nombre} completada exitosamente")
            return True
        else:
            print(f"\n[WARNING] {nombre} terminó con código de salida {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error ejecutando {nombre}: {e}")
        return False


def ejecutar_batida(batida_nombre):
    """Ejecuta una batida preconfigurada"""
    if batida_nombre not in BATIDAS_PRECONFIGURADAS:
        print(f"[ERROR] Batida '{batida_nombre}' no encontrada")
        return
    
    nombres = BATIDAS_PRECONFIGURADAS[batida_nombre]
    total = len(nombres)
    exitosas = 0
    
    print(f"\n{'╔'+'═'*76+'╗'}")
    print(f"║  BATIDA: {batida_nombre.upper():64} ║")
    print(f"║  Total auditorías: {total:54} ║")
    print(f"{'╚'+'═'*76+'╝'}\n")
    
    for i, nombre in enumerate(nombres, 1):
        print(f"\n[{i}/{total}] ", end="")
        if ejecutar_auditoria(nombre):
            exitosas += 1
    
    print(f"\n\n{'='*78}")
    print(f"[STATS] RESUMEN DE BATIDA: {batida_nombre}")
    print(f"{'='*78}")
    print(f"[OK] Exitosas: {exitosas}/{total}")
    print(f"[ERROR] Fallidas:  {total - exitosas}/{total}")
    print(f"{'='*78}\n")


def ejecutar_categoria(categoria):
    """Ejecuta todas las auditorías de una categoría"""
    nombres = [n for n, i in AUDITORIAS.items() if i["categoria"] == categoria]
    if not nombres:
        print(f"[ERROR] Categoría '{categoria}' no tiene auditorías")
        return
    
    print(f"\n{'╔'+'═'*76+'╗'}")
    print(f"║  CATEGORÍA: {categoria.upper():61} ║")
    print(f"║  Total auditorías: {len(nombres):54} ║")
    print(f"{'╚'+'═'*76+'╝'}\n")
    
    exitosas = 0
    for i, nombre in enumerate(nombres, 1):
        print(f"\n[{i}/{len(nombres)}] ", end="")
        if ejecutar_auditoria(nombre):
            exitosas += 1
    
    print(f"\n\n{'='*78}")
    print(f"[STATS] RESUMEN CATEGORÍA: {categoria}")
    print(f"{'='*78}")
    print(f"[OK] Exitosas: {exitosas}/{len(nombres)}")
    print(f"[ERROR] Fallidas:  {len(nombres) - exitosas}/{len(nombres)}")
    print(f"{'='*78}\n")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "--list":
        listar_auditorias()
        
    elif sys.argv[1] == "--run" and len(sys.argv) == 3:
        ejecutar_auditoria(sys.argv[2])
        
    elif sys.argv[1] == "--run-batida" and len(sys.argv) == 3:
        ejecutar_batida(sys.argv[2])
        
    elif sys.argv[1] == "--run-category" and len(sys.argv) == 3:
        ejecutar_categoria(sys.argv[2])
        
    elif sys.argv[1] == "--run-all":
        ejecutar_batida("batida_completa")
        
    else:
        print("\n[ERROR] Uso incorrecto\n")
        print("Opciones válidas:")
        print("  --list                          → Lista todas las auditorías")
        print("  --run NOMBRE                    → Ejecuta auditoría específica")
        print("  --run-batida NOMBRE_BATIDA      → Ejecuta batida preconfigurada")
        print("  --run-category CATEGORIA        → Ejecuta todas de una categoría")
        print("  --run-all                       → Ejecuta TODAS las auditorías")
        print("\nBatidas disponibles:")
        for batida in BATIDAS_PRECONFIGURADAS.keys():
            print(f"  - {batida}")
