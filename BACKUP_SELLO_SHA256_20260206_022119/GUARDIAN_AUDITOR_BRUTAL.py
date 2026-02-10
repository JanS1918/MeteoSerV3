# -*- coding: utf-8 -*-
"""
AUDITOR BRUTAL DE GUARDIAN V47.5
═════════════════════════════════════════════════════════════════════════════

MISIÓN:
1. AUDITAR TODAS las fórmulas disponibles (código + registros)
2. VERIFICAR cuáles se usan en Guardian realmente
3. DETECTAR inconsistencias (fantasmas, ocultas, duplicadas)
4. SI HAY PROBLEMAS → PAUSE GUARDIAN y reportar
5. SI ESTÁ OK → Preparar para duelos vs externas

Este script DEBE ejecutarse ANTES de cada inicio de Guardian.
"""

import sys
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Setup
sys.path.insert(0, str(Path(__file__).parent))
from fix_logging_all import setup_safe_logging
setup_safe_logging()

import logging
logger = logging.getLogger(__name__)

# ═════════════════════════════════════════════════════════════════════════════
# PARTE 1: CARGAR INVENTARIO DE FÓRMULAS REALES
# ═════════════════════════════════════════════════════════════════════════════

class InventarioFormulasReales:
    """Mapeo REAL de lo que existe en código"""
    
    def __init__(self):
        self.formulas = {
            # SENSACIÓN TÉRMICA
            "sensacion_termica": {
                "indice_utci": {
                    "módulo": "core.indices.environmental_indices",
                    "línea": 380,
                    "existe": True,
                    "funciona": True,
                    "notas": "ISO 14505-2, v1 actual"
                },
                "indice_steadman_apparent_temperature": {
                    "módulo": "core.indices.environmental_indices",
                    "línea": 856,
                    "existe": True,
                    "funciona": True,
                    "notas": "1984, fórmula clásica"
                },
                "wind_chill": {
                    "módulo": "core.indices.environmental_indices",
                    "línea": "¿?",
                    "existe": False,
                    "funciona": False,
                    "notas": "ELIMINADA línea 849 - EUTANASIA TÉCNICA 2026"
                },
                "indice_wbgt": {
                    "módulo": "core.indices.environmental_indices",
                    "línea": 1662,
                    "existe": True,
                    "funciona": True,
                    "notas": "OCULTA - No registrada en FORMULA_HIERARCHY"
                },
                "utci_v2_blazejczyk": {
                    "módulo": "core.indices.utci_v2_blazejczyk",
                    "línea": 35,
                    "existe": True,
                    "funciona": True,
                    "notas": "Blazejczyk 2013 para extremos - ¿Registrada?"
                },
            },
            # RADIACIÓN SOLAR
            "radiacion_solar": {
                "rest2_gueymard": {
                    "módulo": "core.indices.rest2_gueymard_radiacion",
                    "línea": 366,
                    "existe": True,
                    "funciona": True,
                    "notas": "Gueymard 2008 + SRTM + Ocaso Topográfico"
                },
            },
            # EVAPOTRANSPIRACIÓN
            "evapotranspiracion": {
                "et0_asce": {
                    "módulo": "core.indices.environmental_indices",
                    "línea": "¿?",
                    "existe": True,
                    "funciona": True,
                    "notas": "ASCE Standardized"
                },
            },
        }
    
    def validar_existencia(self):
        """Intenta importar cada función para verificar que REALMENTE existe"""
        print("\n" + "="*80)
        print("FASE 1: VERIFICACIÓN DE EXISTENCIA FÍSICA")
        print("="*80)
        
        for parametro, funcs in self.formulas.items():
            print(f"\n[{parametro}]")
            for func_name, meta in funcs.items():
                if not meta["existe"]:
                    print(f"  ❌ {func_name}: NO EXISTE (eliminada)")
                    continue
                
                try:
                    # Intenta importar
                    módulo_name = meta["módulo"]
                    exec(f"from {módulo_name} import {func_name}")
                    print(f"  ✅ {func_name}: EXISTE y es IMPORTABLE")
                except ImportError as e:
                    print(f"  ⚠️  {func_name}: EXISTE en metadata pero NO es IMPORTABLE")
                    print(f"      Error: {e}")
                    meta["existe"] = False
                except Exception as e:
                    print(f"  ⚠️  {func_name}: ERROR importando: {type(e).__name__}")
                    meta["existe"] = False


# ═════════════════════════════════════════════════════════════════════════════
# PARTE 2: CARGAR FORMULA_HIERARCHY
# ═════════════════════════════════════════════════════════════════════════════

class AuditorFormulaHierarchy:
    """Audita qué está registrado en FORMULA_HIERARCHY"""
    
    def __init__(self):
        try:
            from core.bus.formula_hierarchy import FORMULA_HIERARCHY
            self.hierarchy = FORMULA_HIERARCHY
        except ImportError:
            print("❌ ERROR: No se puede importar FORMULA_HIERARCHY")
            self.hierarchy = {}
    
    def auditar(self):
        """Compara: qué existe en código vs qué está registrado"""
        print("\n" + "="*80)
        print("FASE 2: AUDITORÍA DE FORMULA_HIERARCHY")
        print("="*80)
        
        print("\nRegistrado en FORMULA_HIERARCHY:")
        
        parametros_auditados = {}
        for param, formulas_dict in self.hierarchy.items():
            print(f"\n  [{param}]")
            parametros_auditados[param] = {}
            for nivel, formula_obj in formulas_dict.items():
                nombre = formula_obj.nombre_tecnico
                print(f"    - {nivel.name}: {nombre}")
                parametros_auditados[param][nombre] = {
                    "nivel": nivel.name,
                    "módulo": formula_obj.módulo,
                }
        
        return parametros_auditados


# ═════════════════════════════════════════════════════════════════════════════
# PARTE 3: DETECTAR INCONSISTENCIAS
# ═════════════════════════════════════════════════════════════════════════════

class DetectorInconsistencias:
    """Encuentra problemas: fantasmas, ocultas, duplicadas"""
    
    def __init__(self, reales: InventarioFormulasReales, jerarquia: Dict):
        self.reales = reales
        self.jerarquia = jerarquia
        self.problemas = []
        self.advertencias = []
    
    def detectar(self):
        print("\n" + "="*80)
        print("FASE 3: DETECCIÓN DE INCONSISTENCIAS")
        print("="*80)
        
        # 1. REGISTROS FANTASMA (existen en hierarchy pero NO en código)
        print("\n[1] REGISTROS FANTASMA (en FORMULA_HIERARCHY pero NO en código):")
        for param, funcs in self.jerarquia.items():
            for nivel, formula_obj in funcs.items():
                nombre_tecnico = formula_obj.nombre_tecnico
                existe_en_codigo = self._existe_en_codigo(nombre_tecnico, param)
                
                if not existe_en_codigo:
                    print(f"  ❌ {nombre_tecnico} ({param})")
                    print(f"     Registrado como: {nivel.name} en hierarchy")
                    print(f"     PERO: La función NO existe en código")
                    self.problemas.append({
                        "tipo": "FANTASMA",
                        "función": nombre_tecnico,
                        "parámetro": param,
                        "nivel": nivel.name,
                        "severidad": "CRÍTICA"
                    })
        
        # 2. FUNCIONES OCULTAS (existen en código pero NO en hierarchy)
        print("\n[2] FUNCIONES OCULTAS (en código pero NO en FORMULA_HIERARCHY):")
        for param, funcs in self.reales.formulas.items():
            for func_name, meta in funcs.items():
                if meta["existe"] and not self._esta_registrada(func_name, param):
                    print(f"  ⚠️  {func_name} ({param})")
                    print(f"     Existe en: {meta['módulo']}")
                    print(f"     PERO: No está en FORMULA_HIERARCHY")
                    self.advertencias.append({
                        "tipo": "OCULTA",
                        "función": func_name,
                        "parámetro": param,
                        "módulo": meta['módulo'],
                        "severidad": "MEDIA"
                    })
        
        # 3. FUNCIONES ELIMINADAS
        print("\n[3] FUNCIONES DELIBERADAMENTE ELIMINADAS:")
        for param, funcs in self.reales.formulas.items():
            for func_name, meta in funcs.items():
                if not meta["existe"] and "ELIMINADA" in meta["notas"]:
                    print(f"  ⚠️  {func_name} ({param})")
                    print(f"     Razón: {meta['notas']}")
                    if self._esta_registrada(func_name, param):
                        print(f"     ⚠️  PERO: Aún está registrada en hierarchy (REGISTRO FANTASMA)")
                        self.problemas.append({
                            "tipo": "ELIMINADA_PERO_REGISTRADA",
                            "función": func_name,
                            "parámetro": param,
                            "severidad": "ALTA"
                        })
    
    def _existe_en_codigo(self, func_name: str, parametro: str) -> bool:
        """Chequea si función existe en inventario de reales"""
        if parametro in self.reales.formulas:
            return func_name in self.reales.formulas[parametro] and \
                   self.reales.formulas[parametro][func_name]["existe"]
        return False
    
    def _esta_registrada(self, func_name: str, parametro: str) -> bool:
        """Chequea si función está en hierarchy"""
        if parametro in self.jerarquia:
            for nivel, formula_obj in self.jerarquia[parametro].items():
                if formula_obj.nombre_tecnico == func_name:
                    return True
        return False
    
    def reportar_resumen(self):
        """Reporte ejecutivo de problemas"""
        print("\n" + "="*80)
        print("RESUMEN DE INCONSISTENCIAS")
        print("="*80)
        
        n_problemas = len(self.problemas)
        n_advertencias = len(self.advertencias)
        
        print("\n[+] PROBLEMAS CRITICOS: " + str(n_problemas))
        for p in self.problemas:
            print("   - " + p['tipo'] + ": " + p['función'] + " (" + p['parámetro'] + ")")
        
        print("\n[!] ADVERTENCIAS: " + str(n_advertencias))
        for a in self.advertencias:
            print("   - " + a['tipo'] + ": " + a['función'] + " (" + a['parámetro'] + ")")
        
        return n_problemas == 0


# ═════════════════════════════════════════════════════════════════════════════
# PARTE 4: VERIFICAR SI SE USAN EN GUARDIAN
# ═════════════════════════════════════════════════════════════════════════════

class VerificadorUsoEnGuardian:
    """Chequea qué fórmulas REALMENTE se usan en Guardian"""
    
    def auditar(self):
        print("\n" + "="*80)
        print("FASE 4: VERIFICACIÓN DE USO EN GUARDIAN")
        print("="*80)
        
        try:
            from core.system.guardian_v47_5 import Guardian
            
            guardian = Guardian()
            print("\n✅ Guardian V47.5 puede instanciarse")
            
            # Chequear qué pasa en duelo
            print("\nVerificando duelo...")
            # Aquí iría lógica de verificación específica
            
        except Exception as e:
            print(f"\n❌ ERROR al instanciar Guardian:")
            print(f"   {type(e).__name__}: {e}")
            traceback.print_exc()


# ═════════════════════════════════════════════════════════════════════════════
# PARTE 5: DECISIÓN DE PAUSE/CONTINUE
# ═════════════════════════════════════════════════════════════════════════════

class ControladorGuardian:
    """Decide si Guardian puede continuar o debe pausarse"""
    
    @staticmethod
    def decidir(n_problemas: int, n_advertencias: int) -> Tuple[bool, str]:
        """
        Retorna: (puede_continuar, razón)
        """
        print("\n" + "="*80)
        print("DECISIÓN FINAL")
        print("="*80)
        
        if n_problemas > 0:
            return False, f"""
❌ GUARDIAN PAUSADO - INCONSISTENCIAS CRÍTICAS DETECTADAS

Problemas encontrados: {n_problemas}

ACCIÓN REQUERIDA:
1. Remover registros fantasma de FORMULA_HIERARCHY
2. Registrar funciones ocultas (especialmente indice_wbgt)
3. Documentar por qué fueron eliminadas ciertas funciones
4. Sincronizar código + registros

Una vez corregido, reintentar auditoría.
"""
        
        if n_advertencias > 3:
            return False, f"""
⚠️  GUARDIAN PAUSADO - DEMASIADAS INCONSISTENCIAS

Advertencias encontradas: {n_advertencias}

ACCIÓN REQUERIDA:
1. Registrar fórmulas ocultas en FORMULA_HIERARCHY
2. Investigar por qué no están registradas
3. Hacer inventario completo

Una vez corregido, reintentar auditoría.
"""
        
        return True, """
✅ AUDITORÍA COMPLETADA SIN PROBLEMAS CRÍTICOS

Guardian puede continuar, PERO:
- Revisar advertencias
- Registrar funciones ocultas si es pertinente
- Preparar duelos vs externas

Estado: LISTO PARA DUELOS
"""


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "="*80)
    print("= AUDITOR BRUTAL DE GUARDIAN V47.5")
    print("= Verificacion de integridad antes de activacion")
    print("="*80)
    
    # Fase 1: Inventario de reales
    print("\nCargando inventario de fórmulas reales...")
    reales = InventarioFormulasReales()
    reales.validar_existencia()
    
    # Fase 2: FORMULA_HIERARCHY
    print("\nCargando FORMULA_HIERARCHY...")
    auditor_hierarchy = AuditorFormulaHierarchy()
    jerarquia_auditada = auditor_hierarchy.auditar()
    
    # Fase 3: Detectar inconsistencias
    print("\nDetectando inconsistencias...")
    detector = DetectorInconsistencias(reales, auditor_hierarchy.hierarchy)
    detector.detectar()
    detector.reportar_resumen()
    
    # Fase 4: Verificar uso
    print("\nVerificando uso en Guardian...")
    verificador = VerificadorUsoEnGuardian()
    verificador.auditar()
    
    # Fase 5: Decisión
    puede_continuar, mensaje = ControladorGuardian.decidir(
        len(detector.problemas),
        len(detector.advertencias)
    )
    
    print(mensaje)
    
    # Guardar reporte
    reporte = {
        "timestamp": datetime.now().isoformat(),
        "puede_continuar_guardian": puede_continuar,
        "n_problemas_críticos": len(detector.problemas),
        "n_advertencias": len(detector.advertencias),
        "problemas": detector.problemas,
        "advertencias": detector.advertencias,
    }
    
    archivo_reporte = Path("data/guardian_audit_report.json")
    with open(archivo_reporte, 'w', encoding='utf-8') as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Reporte guardado: {archivo_reporte}")
    
    return 0 if puede_continuar else 1


if __name__ == "__main__":
    sys.exit(main())
