"""
Demo: SpecValidationEngine - Validador PROACTIVO
Muestra cómo el sistema detecta gaps de especificación automáticamente
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from core.monitoring.spec_validation_engine import SpecValidationEngine
from core.bus.formula_hierarchy import FORMULA_HIERARCHY
from core.indices.hardy_nist_psicrometria import (
    hardy_temperatura_rocio_c,
    hardy_e_pa
)
from core.indices.environmental_indices import (
    saturacion_vapor_iapws_elite,
    presion_vapor_iapws_mejorada,
    indice_utci,
    et0_asce_standardized
)
from core.indices.omm_densidad_temperatura_virtual import (
    omm_densidad_temperatura_virtual
)

print("\n" + "="*80)
print("🚀 DEMOSTRACIÓN: VALIDADOR PROACTIVO DE ESPECIFICACIONES")
print("="*80)
print()

# Crear instancias de implementaciones
implementations = {
    "hardy_temperatura_rocio_c": hardy_temperatura_rocio_c,
    "hardy_e_pa": hardy_e_pa,
    "saturacion_vapor_iapws_elite": saturacion_vapor_iapws_elite,
    "presion_vapor_iapws_mejorada": presion_vapor_iapws_mejorada,
    "indice_utci": indice_utci,
    "et0_asce_standardized": et0_asce_standardized,
    "omm_densidad_temperatura_virtual": omm_densidad_temperatura_virtual,
}

# Ejecutar validador
validator = SpecValidationEngine()
results = validator.validate_all_formulas(FORMULA_HIERARCHY, implementations)

# Generar reporte
fatal_count, warning_count = validator.generate_report()

print()
print("="*80)
print("📋 FÓRMULAS BLOQUEADAS (No cumplen especificación)")
print("="*80)

blocked = validator.block_incomplete_formulas()
if blocked:
    for formula in blocked:
        result = results[formula]
        print(f"\n❌ {formula}")
        print(f"   Errores: {len(result.errors)}")
        for error in result.errors:
            print(f"   • {error}")
else:
    print("✅ Ninguna fórmula bloqueada (todas cumplen)")

print()
print("="*80)
print("🔐 CONCLUSIÓN")
print("="*80)

if fatal_count > 0:
    print(f"\n🚫 {fatal_count} ERROR(ES) FATAL(ES) DETECTADO(S)")
    print("   El sistema iniciaría en modo SEGURO (restricción sobre daño)")
    print("   Las fórmulas incompletas serían BLOQUEADAS automáticamente")
else:
    print(f"\n✅ TODAS LAS ESPECIFICACIONES CUMPLEN")
    print("   El sistema puede iniciar en modo normal")

print()
print("="*80)
print("💡 CÓMO FUNCIONA")
print("="*80)
print("""
1️⃣ PROACTIVO EN STARTUP:
   - Al iniciar, valida TODAS las fórmulas vs especificación
   - Si detecta gaps, LOG WARNING/ERROR
   - Si es crítico, CONGELA el watchdog (24h)

2️⃣ EN WATCHDOG (CAMBIOS):
   - Antes de aplicar cambio: validate_spec_compliance()
   - Si incumple: block_noncompliant_change()
   - Resultado: Cambio bloqueado + watchdog congelado

3️⃣ EN OPERACIÓN:
   - Fórmulas incompletas jamás se aplican automáticamente
   - Solo por aprobación MANUAL después de correción
   - Garantiza "restricción sobre daño" a nivel de especificación

EJEMPLO: Si alguien intenta cambiar a "presion_vapor_iapws" sin Enhancement Factor:
   ❌ BLOQUEADO AUTOMÁTICAMENTE
   ✅ Razón: Incumple especificación (falta parámetro 'humedad')
   🔒 Watchdog congelado 24h para evitar intentos maliciosos
""")

print()
print("✅ DEMO COMPLETADA")
print()
