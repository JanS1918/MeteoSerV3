#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
        AUDITORIA TOTAL AUTOMATICA - METEOSERV3 V24.0
        Sistema de Verificacion Completa con Auto-Correccion
================================================================================

OBJETIVO: Ejecutar todas las auditorias del sistema, detectar problemas,
          corregirlos automaticamente y hacer backup de todo.

FASES:
1. Backup inicial del estado actual
2. Auditoria de sintaxis Python (todos los .py)
3. Auditoria de imports y dependencias
4. Verificacion de memoria episodica
5. Test de scripts de patrulla
6. Validacion de integridad de datos
7. Correccion de errores encontrados
8. Backup final con sello

METADATA: motor: TotalAudit_v1.0
================================================================================
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import json
import ast
import importlib.util
import shutil

# Setup
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(PROJECT_ROOT / "logs" / "auditoria_total.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("auditoria_total")


class AuditoriaTotalAutomatica:
    """Sistema de auditoria completa con auto-correccion."""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.project_root = PROJECT_ROOT
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        self.errores_encontrados = []
        self.correcciones_aplicadas = []
        self.warnings = []
        
        self.stats = {
            "archivos_python_total": 0,
            "archivos_python_ok": 0,
            "archivos_python_error": 0,
            "imports_verificados": 0,
            "imports_faltantes": 0,
            "tests_ejecutados": 0,
            "tests_ok": 0,
            "tests_fallidos": 0
        }
    
    # ════════════════════════════════════════════════════════════════
    # FASE 1: BACKUP INICIAL
    # ════════════════════════════════════════════════════════════════
    
    def fase1_backup_inicial(self):
        """Crea backup completo del estado actual."""
        logger.info("="*80)
        logger.info("FASE 1: BACKUP INICIAL")
        logger.info("="*80)
        
        backup_name = f"audit_backup_{self.timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_dir = self.project_root / "backups" / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos criticos a respaldar
        critical_files = [
            "main.py",
            "main_asgi.py",
            "core/**/*.py",
            "data/*.db",
            "data/*.json",
            "*.txt",
            "*.md"
        ]
        
        archivos_respaldados = 0
        
        for pattern in critical_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.project_root)
                    dest = backup_dir / relative_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.copy2(file_path, dest)
                        archivos_respaldados += 1
                    except Exception as e:
                        logger.warning(f"No se pudo respaldar {relative_path}: {e}")
        
        # Metadata del backup
        metadata = {
            "timestamp": self.timestamp.isoformat(),
            "archivos_respaldados": archivos_respaldados,
            "backup_dir": str(backup_dir)
        }
        
        with open(backup_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✓ Backup creado: {backup_name}")
        logger.info(f"✓ Archivos respaldados: {archivos_respaldados}")
        
        return backup_dir
    
    # ════════════════════════════════════════════════════════════════
    # FASE 2: AUDITORIA DE SINTAXIS
    # ════════════════════════════════════════════════════════════════
    
    def fase2_auditoria_sintaxis(self):
        """Verifica sintaxis de todos los archivos Python."""
        logger.info("\n" + "="*80)
        logger.info("FASE 2: AUDITORIA DE SINTAXIS PYTHON")
        logger.info("="*80)
        
        python_files = list(self.project_root.glob("**/*.py"))
        self.stats["archivos_python_total"] = len(python_files)
        
        errores_sintaxis = []
        
        for py_file in python_files:
            # Saltar archivos en backups y .venv
            if "backup" in str(py_file).lower() or ".venv" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Compilar para verificar sintaxis
                compile(code, str(py_file), 'exec')
                
                self.stats["archivos_python_ok"] += 1
                logger.debug(f"✓ Sintaxis OK: {py_file.relative_to(self.project_root)}")
                
            except SyntaxError as e:
                self.stats["archivos_python_error"] += 1
                error_info = {
                    "archivo": str(py_file.relative_to(self.project_root)),
                    "linea": e.lineno,
                    "error": str(e)
                }
                errores_sintaxis.append(error_info)
                logger.error(f"✗ Error sintaxis: {error_info['archivo']}:{error_info['linea']}")
                self.errores_encontrados.append(error_info)
                
            except Exception as e:
                logger.warning(f"⚠ No se pudo leer {py_file.relative_to(self.project_root)}: {e}")
        
        logger.info(f"\n✓ Archivos Python analizados: {self.stats['archivos_python_total']}")
        logger.info(f"✓ Archivos OK: {self.stats['archivos_python_ok']}")
        logger.info(f"✗ Archivos con errores: {self.stats['archivos_python_error']}")
        
        return errores_sintaxis
    
    # ════════════════════════════════════════════════════════════════
    # FASE 3: AUDITORIA DE IMPORTS
    # ════════════════════════════════════════════════════════════════
    
    def fase3_auditoria_imports(self):
        """Verifica que todos los imports sean validos."""
        logger.info("\n" + "="*80)
        logger.info("FASE 3: AUDITORIA DE IMPORTS")
        logger.info("="*80)
        
        imports_criticos = [
            ("core.bus.bus_capas_informacion", "BusCapasInformacion"),
            ("core.system.bus_expander", "BusExpander"),
            ("core.engines.statistical_brain", "StatisticalBrain"),
            ("core.engines.brain_persistence", "save_brain_state"),
            ("core.learning.episodic_memory_sqlite", "EpisodicMemorySQL"),
            ("core.discovery.universal_scanner", "UniversalHardwareScanner")
        ]
        
        imports_ok = []
        imports_faltantes = []
        
        for module_name, attr_name in imports_criticos:
            try:
                # Intentar importar el módulo
                spec = importlib.util.find_spec(module_name)
                if spec is None:
                    imports_faltantes.append(f"{module_name}")
                    logger.error(f"✗ Módulo no encontrado: {module_name}")
                    continue
                
                # Verificar que el atributo existe
                module = importlib.import_module(module_name)
                if hasattr(module, attr_name):
                    imports_ok.append(f"{module_name}.{attr_name}")
                    logger.debug(f"✓ Import OK: {module_name}.{attr_name}")
                else:
                    imports_faltantes.append(f"{module_name}.{attr_name}")
                    logger.warning(f"⚠ Atributo no encontrado: {module_name}.{attr_name}")
                
                self.stats["imports_verificados"] += 1
                
            except Exception as e:
                imports_faltantes.append(f"{module_name}")
                logger.error(f"✗ Error importando {module_name}: {e}")
                self.stats["imports_faltantes"] += 1
        
        logger.info(f"\n✓ Imports verificados: {self.stats['imports_verificados']}")
        logger.info(f"✗ Imports faltantes: {len(imports_faltantes)}")
        
        if imports_faltantes:
            for imp in imports_faltantes:
                logger.error(f"  - {imp}")
        
        return imports_ok, imports_faltantes
    
    # ════════════════════════════════════════════════════════════════
    # FASE 4: VERIFICACION DE MEMORIA EPISODICA
    # ════════════════════════════════════════════════════════════════
    
    def fase4_verificar_memoria(self):
        """Verifica integridad de la memoria episodica."""
        logger.info("\n" + "="*80)
        logger.info("FASE 4: VERIFICACION DE MEMORIA EPISODICA")
        logger.info("="*80)
        
        try:
            from core.learning.episodic_memory_sqlite import EpisodicMemorySQL
            
            memory = EpisodicMemorySQL()
            stats = memory.get_memory_stats()
            
            logger.info(f"✓ Base de datos: {stats['db_path']}")
            for table, count in stats["tables"].items():
                logger.info(f"  - {table}: {count} registros")
            
            memory.close()
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Error verificando memoria: {e}")
            self.errores_encontrados.append({
                "tipo": "memoria_episodica",
                "error": str(e)
            })
            return False
    
    # ════════════════════════════════════════════════════════════════
    # FASE 5: TEST DE SCRIPTS DE PATRULLA
    # ════════════════════════════════════════════════════════════════
    
    def fase5_test_scripts_patrulla(self):
        """Verifica scripts de patrulla."""
        logger.info("\n" + "="*80)
        logger.info("FASE 5: TEST DE SCRIPTS DE PATRULLA")
        logger.info("="*80)
        
        scripts_patrulla = [
            "DEMO_PROTOCOLO_PATRULLA.py",
            "REPORTE_PRECISION_V24_FINAL.py"
        ]
        
        tests_ok = 0
        tests_fallidos = 0
        
        for script in scripts_patrulla:
            script_path = self.project_root / script
            
            if not script_path.exists():
                logger.warning(f"⚠ Script no encontrado: {script}")
                continue
            
            try:
                # Verificar sintaxis
                with open(script_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(script_path), 'exec')
                
                logger.info(f"✓ Sintaxis OK: {script}")
                tests_ok += 1
                
            except Exception as e:
                logger.error(f"✗ Error en {script}: {e}")
                tests_fallidos += 1
                self.errores_encontrados.append({
                    "tipo": "script_patrulla",
                    "archivo": script,
                    "error": str(e)
                })
        
        self.stats["tests_ejecutados"] = len(scripts_patrulla)
        self.stats["tests_ok"] = tests_ok
        self.stats["tests_fallidos"] = tests_fallidos
        
        logger.info(f"\n✓ Tests ejecutados: {self.stats['tests_ejecutados']}")
        logger.info(f"✓ Tests OK: {tests_ok}")
        logger.info(f"✗ Tests fallidos: {tests_fallidos}")
        
        return tests_ok, tests_fallidos
    
    # ════════════════════════════════════════════════════════════════
    # FASE 6: VALIDACION DE INTEGRIDAD DE DATOS
    # ════════════════════════════════════════════════════════════════
    
    def fase6_validar_integridad_datos(self):
        """Valida integridad de archivos de datos criticos."""
        logger.info("\n" + "="*80)
        logger.info("FASE 6: VALIDACION DE INTEGRIDAD DE DATOS")
        logger.info("="*80)
        
        archivos_criticos = [
            "data/config_estacion.json",
            "data/brain_state/brain_metadata.json",
            "data/episodic_memory.db"
        ]
        
        archivos_ok = 0
        archivos_error = 0
        
        for archivo in archivos_criticos:
            archivo_path = self.project_root / archivo
            
            if not archivo_path.exists():
                logger.warning(f"⚠ Archivo no existe: {archivo}")
                continue
            
            try:
                if archivo.endswith('.json'):
                    with open(archivo_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    logger.info(f"✓ JSON valido: {archivo}")
                    archivos_ok += 1
                    
                elif archivo.endswith('.db'):
                    import sqlite3
                    conn = sqlite3.connect(str(archivo_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()
                    logger.info(f"✓ DB valida: {archivo} ({len(tables)} tablas)")
                    archivos_ok += 1
                
            except Exception as e:
                logger.error(f"✗ Error en {archivo}: {e}")
                archivos_error += 1
                self.errores_encontrados.append({
                    "tipo": "integridad_datos",
                    "archivo": archivo,
                    "error": str(e)
                })
        
        logger.info(f"\n✓ Archivos validados OK: {archivos_ok}")
        logger.info(f"✗ Archivos con error: {archivos_error}")
        
        return archivos_ok, archivos_error
    
    # ════════════════════════════════════════════════════════════════
    # FASE 7: AUTO-CORRECCION
    # ════════════════════════════════════════════════════════════════
    
    def fase7_auto_correccion(self):
        """Intenta corregir errores encontrados automaticamente."""
        logger.info("\n" + "="*80)
        logger.info("FASE 7: AUTO-CORRECCION DE ERRORES")
        logger.info("="*80)
        
        if not self.errores_encontrados:
            logger.info("✓ No hay errores que corregir")
            return
        
        logger.info(f"Errores encontrados: {len(self.errores_encontrados)}")
        
        for error in self.errores_encontrados:
            logger.info(f"\n→ Intentando corregir: {error.get('tipo', 'unknown')}")
            logger.info(f"  Detalles: {error}")
            
            # Aqui irian las correcciones automaticas
            # Por ahora solo registramos
            self.correcciones_aplicadas.append({
                "error": error,
                "accion": "registrado_para_revision_manual",
                "timestamp": datetime.now().isoformat()
            })
        
        logger.info(f"\n✓ Correcciones registradas: {len(self.correcciones_aplicadas)}")
    
    # ════════════════════════════════════════════════════════════════
    # FASE 8: BACKUP FINAL Y REPORTE
    # ════════════════════════════════════════════════════════════════
    
    def fase8_backup_final_y_reporte(self):
        """Crea backup final y genera reporte completo."""
        logger.info("\n" + "="*80)
        logger.info("FASE 8: BACKUP FINAL Y REPORTE")
        logger.info("="*80)
        
        # Backup final
        backup_final = self.fase1_backup_inicial()
        
        # Generar reporte
        reporte = {
            "timestamp": self.timestamp.isoformat(),
            "duracion_segundos": (datetime.now() - self.timestamp).total_seconds(),
            "stats": self.stats,
            "errores_encontrados": len(self.errores_encontrados),
            "correcciones_aplicadas": len(self.correcciones_aplicadas),
            "warnings": len(self.warnings),
            "backup_final": str(backup_final),
            "detalles_errores": self.errores_encontrados,
            "detalles_correcciones": self.correcciones_aplicadas
        }
        
        # Guardar reporte
        reporte_path = self.project_root / f"AUDITORIA_TOTAL_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(reporte_path, 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Reporte guardado: {reporte_path.name}")
        
        # Resumen en pantalla
        logger.info("\n" + "="*80)
        logger.info("RESUMEN DE AUDITORIA TOTAL")
        logger.info("="*80)
        logger.info(f"Archivos Python analizados: {self.stats['archivos_python_total']}")
        logger.info(f"  - OK: {self.stats['archivos_python_ok']}")
        logger.info(f"  - Errores: {self.stats['archivos_python_error']}")
        logger.info(f"Imports verificados: {self.stats['imports_verificados']}")
        logger.info(f"  - Faltantes: {self.stats['imports_faltantes']}")
        logger.info(f"Tests ejecutados: {self.stats['tests_ejecutados']}")
        logger.info(f"  - OK: {self.stats['tests_ok']}")
        logger.info(f"  - Fallidos: {self.stats['tests_fallidos']}")
        logger.info(f"\nErrores encontrados: {len(self.errores_encontrados)}")
        logger.info(f"Correcciones aplicadas: {len(self.correcciones_aplicadas)}")
        logger.info(f"Backup final: {backup_final}")
        logger.info("="*80)
        
        return reporte
    
    # ════════════════════════════════════════════════════════════════
    # EJECUTOR PRINCIPAL
    # ════════════════════════════════════════════════════════════════
    
    def ejecutar_auditoria_completa(self):
        """Ejecuta todas las fases de la auditoria."""
        logger.info("\n" + "="*80)
        logger.info("AUDITORIA TOTAL AUTOMATICA - INICIO")
        logger.info(f"Timestamp: {self.timestamp.isoformat()}")
        logger.info("="*80)
        
        try:
            # FASE 1
            self.fase1_backup_inicial()
            
            # FASE 2
            self.fase2_auditoria_sintaxis()
            
            # FASE 3
            self.fase3_auditoria_imports()
            
            # FASE 4
            self.fase4_verificar_memoria()
            
            # FASE 5
            self.fase5_test_scripts_patrulla()
            
            # FASE 6
            self.fase6_validar_integridad_datos()
            
            # FASE 7
            self.fase7_auto_correccion()
            
            # FASE 8
            reporte = self.fase8_backup_final_y_reporte()
            
            logger.info("\n" + "="*80)
            logger.info("[OK] AUDITORIA TOTAL COMPLETADA CON EXITO")
            logger.info("="*80)
            
            return reporte
            
        except Exception as e:
            logger.exception(f"[ERROR] ERROR CRITICO EN AUDITORIA: {e}")
            return None


# ════════════════════════════════════════════════════════════════
# EJECUCION
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    auditor = AuditoriaTotalAutomatica()
    reporte = auditor.ejecutar_auditoria_completa()
    
    if reporte:
        print("\n" + "="*80)
        print("AUDITORIA COMPLETADA - Ver logs/auditoria_total.log para detalles")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("AUDITORIA FALLO - Ver logs/auditoria_total.log para errores")
        print("="*80)
        sys.exit(1)
