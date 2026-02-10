#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEGRACIÓN: Validación Proactiva en Startup de main_asgi.py
---------------------------------------------------------

Este módulo es el TEMPLATE que debe añadirse a main_asgi.py
para activar la validación proactiva de especificaciones al iniciar.
"""

import sys
from pathlib import Path
from typing import Dict, Callable, Tuple

# ============================================================================
# TEMPLATE PARA INTEGRAR EN main_asgi.py
# ============================================================================

"""
# COPIAR ESTO EN main_asgi.py EN LA SECCIÓN DE IMPORTS:

from core.monitoring.spec_validation_engine import SpecValidationEngine
from core.monitoring.auto_change_watchdog import auto_change_watchdog
from core.bus.formula_hierarchy import FORMULA_HIERARCHY
from core.logger import logger

# Importar TODAS las fórmulas que van a validarse:
from core.indices.environmental_indices import (
    indice_sensacion_termica_simple,
    presion_vapor_hardy,
    presion_vapor_iapws_mejorada,
    temperatura_rocio_c,
    # ... agregar todas
)

from core.indices.hardy_nist_psicrometria import (
    hardy_temperatura_rocio_c,
    hardy_e_pa,
    # ... agregar todas
)

# ... importar de otros módulos según corresponda


# LUEGO EN LA SECCIÓN DE STARTUP:

@app.on_event("startup")
async def validate_formulas_on_startup():
    \"\"\"
    Validación PROACTIVA de todas las fórmulas.
    Corre al iniciar la aplicación.
    Detiene si hay errores FATALES.
    \"\"\"
    
    logger.info("[BUSCAR] INICIANDO VALIDACIÓN PROACTIVA DE FÓRMULAS...")
    
    # 1. Crear mapa de implementaciones
    implementations = {
        # Vapor Pressure
        "hardy_e_pa": hardy_e_pa,
        "presion_vapor_iapws_mejorada": presion_vapor_iapws_mejorada,
        "presion_vapor_hardy": presion_vapor_hardy,
        
        # Temperature
        "hardy_temperatura_rocio_c": hardy_temperatura_rocio_c,
        "temperatura_rocio_c": temperatura_rocio_c,
        
        # Thermal Sensation
        "indice_sensacion_termica_simple": indice_sensacion_termica_simple,
        
        # ... agregar todas
    }
    
    # 2. Instanciar validador
    validator = SpecValidationEngine()
    
    # 3. Validar TODAS las fórmulas
    logger.info(f"[STATS] Validando {len(implementations)} fórmulas...")
    validation_results = {}
    
    for formula_name, impl_func in implementations.items():
        is_compliant, issues = validator.validate_spec_compliance(
            formula_name=formula_name,
            impl_func=impl_func,
            spec_required_params=FORMULA_HIERARCHY.get(
                formula_name, 
                {"requisitos_datos": []}
            ).get("requisitos_datos", [])
        )
        
        validation_results[formula_name] = {
            "compliant": is_compliant,
            "issues": issues
        }
        
        if not is_compliant:
            logger.warning(
                f"[WARNING]  {formula_name} incumple especificación: {issues}"
            )
        else:
            logger.info(f"[OK] {formula_name} validada correctamente")
    
    # 4. Generar reporte
    fatal_errors = sum(
        1 for r in validation_results.values() 
        if not r["compliant"] and len(r["issues"]) > 0
    )
    
    if fatal_errors > 0:
        logger.critical(
            f"[CRITICAL] {fatal_errors} FÓRMULAS CON ERRORES FATALES DETECTADOS"
        )
        logger.critical("   Sistema iniciará en modo SEGURO")
        logger.critical("   Las fórmulas incompletas serán BLOQUEADAS")
        
        # Opción 1: Solo warnings (sistema continúa)
        # Opción 2: Crash (sistema no inicia)
        # --> Descomentar según necesidad:
        
        # raise RuntimeError("🚫 Validación crítica falló. Sistema no iniciará.")
    
    else:
        logger.info(f"[OK] TODAS LAS FÓRMULAS VALIDADAS EXITOSAMENTE")
    
    # 5. Guardar resultados en watchdog
    auto_change_watchdog._last_startup_validation = {
        "timestamp": datetime.datetime.now(),
        "total_formulas": len(implementations),
        "compliant_count": sum(1 for r in validation_results.values() if r["compliant"]),
        "errors": fatal_errors,
        "details": validation_results
    }
    
    logger.info("[OK] VALIDACIÓN PROACTIVA COMPLETADA")


# INTEGRACIÓN CON WATCHDOG:
# Cuando reciba proposición de cambio:

@app.post("/api/formulas/propose-change")
async def propose_formula_change(change_request: ChangeRequest):
    \"\"\"
    NUEVO: Valida ANTES de aplicar cambio.
    \"\"\"
    
    formula_name = change_request.formula_name
    new_implementation = change_request.implementation
    
    # 1. VALIDACIÓN PROACTIVA
    is_compliant, issues = auto_change_watchdog.validate_spec_compliance(
        formula_name=formula_name,
        impl_func=new_implementation,
        spec_required_params=FORMULA_HIERARCHY.get(
            formula_name,
            {"requisitos_datos": []}
        ).get("requisitos_datos", [])
    )
    
    if not is_compliant:
        # [ERROR] BLOQUEADO
        auto_change_watchdog.block_noncompliant_change(
            formula_name=formula_name,
            reason=f"Incumple especificación: {issues}"
        )
        
        return {
            "status": "blocked",
            "reason": "Cambio incumple especificación de fórmula",
            "issues": issues,
            "watchdog_frozen": True,
            "freeze_duration": "24 horas"
        }
    
    # 2. Si pasa validación PROACTIVA, continuar con REACTIVA (duelo, etc)
    logger.info(f"[OK] Cambio de {formula_name} pasó validación proactiva")
    # ... continuar con duelo_automatico(), etc
    
    return {
        "status": "pending_evaluation",
        "message": "Pasó validación proactiva. Iniciando evaluación reactiva..."
    }
"""

# ============================================================================
# INSTALACIONES NECESARIAS
# ============================================================================

INSTALL_CHECKLIST = """
[OK] Instalaciones Manuales Necesarias:

1. En main_asgi.py:
   - Importar SpecValidationEngine
   - Importar TODAS las funciones de fórmulas
   - Agregar @app.on_event("startup") con validate_formulas_on_startup()
   - Adaptar @app.post("/api/formulas/propose-change") para validar ANTES

2. En auto_change_watchdog.py:
   - [OK] HECHO: validate_spec_compliance() ya existe
   - [OK] HECHO: block_noncompliant_change() ya existe
   - [OK] HECHO: _freeze_watchdog() ya existe

3. En spec_validation_engine.py:
   - [OK] HECHO: SpecValidationEngine clase completa

4. Normalización de parámetros (OPCIONAL pero recomendado):
   - Crear PARAM_MAPPING en spec_validation_engine.py
   - Adaptar _normalize_param_names()
   - Esto elimina los 15 warnings de parámetros
"""

# ============================================================================
# TESTING DESPUÉS DE INTEGRACIÓN
# ============================================================================

TESTING_STEPS = """
1. Reiniciar app:
   python main_asgi.py

2. Buscar en logs:
   "[BUSCAR] INICIANDO VALIDACIÓN PROACTIVA"
   "[OK] TODAS LAS FÓRMULAS VALIDADAS EXITOSAMENTE"
   
   O si hay errores:
   "[WARNING]  [formula] incumple especificación"
   "[CRITICAL] X FÓRMULAS CON ERRORES FATALES"

3. Probar bloqueo:
   - POST /api/formulas/propose-change
   - Con fórmula incompleta
   - Debe retornar "status": "blocked"

4. Probar aceptación:
   - POST /api/formulas/propose-change
   - Con fórmula completa
   - Debe retornar "status": "pending_evaluation"
"""

print(__doc__)
print(INSTALL_CHECKLIST)
print(TESTING_STEPS)
