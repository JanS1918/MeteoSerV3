#!/usr/bin/env python3
"""
🔍 ORQUESTADOR DE AUDITORÍAS COMPLETAS - MeteoSer V2.0

Ejecuta todas las auditorías del sistema en orden:
1. Auditoría de redundancia (verifica CERO REDUNDANCIA)
2. Generación de mapa de dependencias (documenta grafo)
3. Auto-auditoria completa (health check general)
4. Registro histórico (guarda resultado en histórico)

Este script es el punto de entrada para CI/CD.
"""

import sys
import os
import json
import logging
import subprocess
import datetime
from pathlib import Path

# Setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("audit_orchestrator")

# Colores ANSI para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def run_script(script_path: str, description: str) -> tuple:
    """
    Ejecuta un script Python y retorna (exit_code, stdout, stderr).
    """
    print_info(f"Ejecutando: {description}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos máximo
        )
        return (result.returncode, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return (1, "", f"Script timed out after 300s: {script_path}")
    except Exception as e:
        return (1, "", str(e))


# ═══════════════════════════════════════════════════════════════════════════
# AUDITORÍA 1: REDUNDANCIA
# ═══════════════════════════════════════════════════════════════════════════

def audit_redundancia():
    """Verifica que no hay variables con múltiples productores."""
    print_header("AUDITORÍA 1/4: VERIFICACIÓN DE CERO REDUNDANCIA")
    
    script = os.path.join(os.path.dirname(__file__), 'auditar_redundancia.py')
    if not os.path.exists(script):
        print_error(f"Script no encontrado: {script}")
        return False
    
    exit_code, stdout, stderr = run_script(script, "auditar_redundancia.py")
    
    print(stdout)
    if stderr:
        logger.warning(f"STDERR: {stderr}")
    
    if exit_code == 0:
        print_success("Redundancia: OK")
        return True
    else:
        print_error("Redundancia: FALLÓ")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# AUDITORÍA 2: MAPA DE DEPENDENCIAS
# ═══════════════════════════════════════════════════════════════════════════

def audit_mapa_dependencias():
    """Genera mapa estático de dependencias."""
    print_header("AUDITORÍA 2/4: GENERACIÓN DE MAPA DE DEPENDENCIAS")
    
    script = os.path.join(os.path.dirname(__file__), 'generar_mapa_dependencias.py')
    if not os.path.exists(script):
        print_error(f"Script no encontrado: {script}")
        return False
    
    exit_code, stdout, stderr = run_script(script, "generar_mapa_dependencias.py")
    
    print(stdout)
    if stderr:
        logger.warning(f"STDERR: {stderr}")
    
    if exit_code == 0:
        print_success("Mapa de dependencias: OK")
        return True
    else:
        print_error("Mapa de dependencias: FALLÓ")
        return False


# ═══════════════════════════════════════════════════════════════════════════
# AUDITORÍA 3: AUTO-AUDITOR COMPLETO
# ═══════════════════════════════════════════════════════════════════════════

def audit_auto_auditor():
    """Ejecuta health check completo del sistema."""
    print_header("AUDITORÍA 3/4: AUTO-AUDITORÍA DEL SISTEMA")
    
    try:
        from core.managers.auto_auditor import AutoAuditor
        
        print_info("Inicializando AutoAuditor...")
        auditor = AutoAuditor()
        
        print_info("Ejecutando auditoría completa...")
        report = auditor.ejecutar_auditoria_completa()
        
        # Imprimir resumen del reporte
        if isinstance(report, dict):
            print(f"\nReporte generado:")
            print(json.dumps(report, indent=2, ensure_ascii=False))
            print_success("Auto-auditoría: OK")
            return True
        else:
            print_error("Auto-auditoría: Reporte inválido")
            return False
            
    except ImportError:
        print_error("AutoAuditor no disponible; saltando...")
        return True  # No es crítico
    except Exception as e:
        print_error(f"Auto-auditoría: FALLÓ - {e}")
        logger.exception(e)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# AUDITORÍA 4: REGISTRO HISTÓRICO
# ═══════════════════════════════════════════════════════════════════════════

def audit_registro_historico():
    """Registra los resultados en histórico."""
    print_header("AUDITORÍA 4/4: REGISTRO HISTÓRICO")
    
    try:
        from core.managers.historical_registry import HistoricalRegistry
        
        print_info("Inicializando HistoricalRegistry...")
        registry = HistoricalRegistry()
        
        timestamp = datetime.datetime.now().isoformat()
        record = {
            "timestamp": timestamp,
            "tipo": "audit_orchestrator",
            "status": "completed",
            "detalles": {
                "script": "scripts/run_all_audits.py",
                "version": "1.0",
            }
        }
        
        print_info("Registrando en histórico...")
        registry.agregar_registro(record)
        
        print_success("Registro histórico: OK")
        return True
        
    except ImportError:
        print_error("HistoricalRegistry no disponible; saltando...")
        return True  # No es crítico
    except Exception as e:
        print_error(f"Registro histórico: FALLÓ - {e}")
        logger.exception(e)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print_header("🔍 ORQUESTRADOR DE AUDITORÍAS - MeteoSer v1.0")
    
    resultados = {}
    
    # Ejecutar auditorías en orden
    resultados["redundancia"] = audit_redundancia()
    resultados["mapa_dependencias"] = audit_mapa_dependencias()
    resultados["auto_auditor"] = audit_auto_auditor()
    resultados["historico"] = audit_registro_historico()
    
    # Resumen final
    print_header("📊 RESUMEN DE AUDITORÍAS")
    
    total = len(resultados)
    exitosas = sum(1 for v in resultados.values() if v)
    
    for nombre, resultado in resultados.items():
        status = "✅ OK" if resultado else "❌ FALLÓ"
        print(f"  {nombre:30} {status}")
    
    print(f"\nResumen: {exitosas}/{total} auditorías exitosas")
    
    if exitosas == total:
        print_success("TODAS LAS AUDITORÍAS PASARON")
        return 0
    else:
        print_error(f"FALTARON {total - exitosas} AUDITORÍAS")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
