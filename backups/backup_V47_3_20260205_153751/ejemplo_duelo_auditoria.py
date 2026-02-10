#!/usr/bin/env python3
"""
AUDITORÍA DE DUELO - EJEMPLO DIDÁCTICO

Este script muestra exactamente qué formularia ha mejorado,
qué se implementaría y qué se sustituiría.
SIN IMPLEMENTAR NADA - Solo para auditoría.
"""

import sys
sys.path.insert(0, '.')

import json
from pathlib import Path
from core.bus.formula_hierarchy import FORMULA_HIERARCHY

print("╔" + "═"*68 + "╗")
print("║" + " "*15 + "AUDITORÍA DE DUELO DE FÓRMULAS" + " "*23 + "║")
print("║" + " "*15 + "(Ejemplo Real - Sin Implementación)" + " "*18 + "║")
print("╚" + "═"*68 + "╝")

print("\n" + "="*70)
print("PASO 1: FORMULAS EN COMPETENCIA")
print("="*70)

# Mostrar un parámetro como ejemplo
parametro_ejemplo = "temperatura"

if parametro_ejemplo in FORMULA_HIERARCHY:
    niveles = FORMULA_HIERARCHY[parametro_ejemplo]
    
    print(f"\nParámetro: {parametro_ejemplo.upper()}")
    print(f"Total de fórmulas en jerarquía: {len(niveles)}")
    
    # Mostrar las 3 mejores (que competirían)
    print(f"\nFórmulas Elite que competirían en duelo:")
    for i, nivel in enumerate(niveles[:3], 1):
        print(f"  {i}. ELITE {nivel.elite}: {nivel.nombre}")
        print(f"     Descripción: {nivel.descripcion if hasattr(nivel, 'descripcion') else 'N/A'}")

print("\n" + "="*70)
print("PASO 2: SIMULACION DE DUELO (DATOS HISTÓRICOS)")
print("="*70)

print(f"""
El motor de duelos tomaría:
  - 100 muestras históricas de {parametro_ejemplo}
  - Las últimas 7 días de datos (período de auditoría)
  - Valida que NO haya alertas ni datos simulados
  - Inyecta ruido realista (±0.5% desviación estándar)

Ejemplo de datos que usaría:
  - 2026-01-30: 23.5°C (fórmula ACTUAL vs CANDIDATA)
  - 2026-01-31: 24.1°C
  - 2026-02-01: 22.8°C
  - 2026-02-02: 25.3°C
  - ... (96 muestras más)
""")

print("\n" + "="*70)
print("PASO 3: EVALUACION COMPARATIVA")
print("="*70)

print("""
CRITERIOS DE PUNTUACIÓN (Pesos):
  • Precisión (60%):      ¿Qué formula se acerca más al valor real?
                          Score = 1 - (error_promedio / rango)
  
  • Estabilidad (30%):    ¿Qué formula oscila menos?
                          Score = 1 - (coeficiente_variacion)
  
  • Eficiencia (10%):     ¿Cuál usa menos recursos?
                          Score = 1 - (tiempo_calculo / max_tiempo)

EJEMPLO NUMÉRICO:
┌─────────────────┬──────────┬────────────┬─────────────┬──────────┐
│ Métrica         │ ACTUAL   │ CANDIDATA  │ DIFERENCIA  │ RESULTADO│
├─────────────────┼──────────┼────────────┼─────────────┼──────────┤
│ Precisión (60%) │ 0.9240   │ 0.9512     │ +0.0272     │ ✓ +1.63% │
│ Estabilidad(30%)│ 0.8756   │ 0.8934     │ +0.0178     │ ✓ +0.53% │
│ Eficiencia(10%) │ 0.9500   │ 0.9450     │ -0.0050     │ ✗ -0.05% │
├─────────────────┼──────────┼────────────┼─────────────┼──────────┤
│ SCORE FINAL     │ 0.9163   │ 0.9381     │ +0.0218     │ ✓ +2.18% │
└─────────────────┴──────────┴────────────┴─────────────┴──────────┘

INTERPRETACIÓN:
  - La CANDIDATA gana por +2.18 puntos porcentuales
  - Mejora principalmente en PRECISIÓN (más exacta)
  - Mantiene buena estabilidad
  - Mínimo costo en eficiencia
  - VEREDICTO: CANDIDATA DEBERÍA REEMPLAZAR a ACTUAL
""")

print("\n" + "="*70)
print("PASO 4: QUÉ HARÍA EL SISTEMA (SIN IMPLEMENTAR)")
print("="*70)

print("""
SI GANARA LA CANDIDATA (pero está en DRY-RUN = solo auditoría):

┌─ CAMBIO DE FORMULA ────────────────────────────────────────────┐
│                                                                  │
│  PARÁMETRO:  temperatura                                       │
│  ────────────────────────────────────────────────────────────  │
│  SUSTITUIR:   Elite 7 - "Interpolación Cuadrática Ponderada"   │
│  POR:         Elite 9 - "NIST Psychrometric Refinement"        │
│                                                                  │
│  En formula_override_manager.py se escribiría:                 │
│  ────────────────────────────────────────────────────────────  │
│  {                                                              │
│    "temperatura": {                                             │
│      "override_formula": "Elite9_NISTRefine",                  │
│      "motivo": "Duelo automático - Mejora +2.18%",             │
│      "fecha": "2026-02-04T10:30:45",                           │
│      "puntuacion_ganador": 0.9381,                             │
│      "puntuacion_perdedor": 0.9163,                            │
│      "ventaja": 0.0218,                                        │
│      "auditable": true,                                        │
│      "reversible": true,                                       │
│      "periodo_auditoria": "2026-02-04 a 2026-02-11"           │
│    }                                                            │
│  }                                                              │
│                                                                  │
│  En bus_capas_informacion.py, consumir_elite("temperatura")    │
│  ya NO devolvería Elite 7, sino Elite 9 (NIST)                 │
│                                                                  │
│  RESULTADO EN UI:                                              │
│    - "temperatura: 23.5°C [1 cambio · en revisión]"            │
│    - Auditoría automática en 7 días                            │
│    - Si Elite 9 sigue mejor: se consolida                      │
│    - Si Elite 9 empeora: revertir a Elite 7 automáticamente    │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
""")

print("\n" + "="*70)
print("PASO 5: AUDITORÍA (CÓMO LO VERIFICARÍAS TÚ)")
print("="*70)

print("""
El resultado se guarda en: data/formula_duel_results.json

Contenido del registro:
────────────────────────────────────────────────────────────────

{
  "parametro": "temperatura",
  "ganador": "Elite9_NISTRefine",
  "perdedor": "Elite7_InterpolacionCuadratica",
  "score_actual": 0.9163,        ← Puntuación de la FÓRMULA ACTUAL
  "score_alt": 0.9381,           ← Puntuación de la CANDIDATA
  "diferencia": 0.0218,          ← Ventaja (2.18%)
  "escenarios": {
    "frio_extremo": {"score_alt": 0.9450, "mejora": true},
    "templado": {"score_alt": 0.9425, "mejora": true},
    "calor_extremo": {"score_alt": 0.9290, "mejora": true}
  },
  "muestras_validas": 97,
  "muestras_totales": 100,
  "contaminacion_detectada": false,
  "dry_run": true,               ← NO SE HA IMPLEMENTADO
  "fecha": "2026-02-04T10:30:45"
}

VERIFICACIÓN QUE DEBERÍAS HACER:
  1. ¿El porcentaje de mejora es significativo? (>2%)
  2. ¿Mejora en TODOS los escenarios (frio, templado, calor)?
  3. ¿El número de muestras válidas es suficiente? (>30)
  4. ¿No hay contaminación detectada?
  
SI RESPONDE "SÍ" A TODAS: Es seguro implementar
SI RESPONDE "NO" A ALGUNA: Revisar antes de cambiar
""")

print("\n" + "="*70)
print("PASO 6: CÓMO IMPLEMENTAR (UNA VEZ AUDITADO)")
print("="*70)

print("""
Si AUDITAS y APRUEBAS el cambio:

  1. Cambiar en formula_duel_engine.py:
     ───────────────────────────────────
     dry_run = True  →  dry_run = False
     
  2. Volver a ejecutar el motor:
     python -c "from core.system.system_core import SystemCore; SystemCore().obtener_estado_completo()"
     
  3. El motor aplicará automáticamente los overrides
  
  4. Revisar el cambio en 7 días (auditoría automática)
  
  5. Si mejoró: mantener. Si empeora: revertir (automático).

────────────────────────────────────────────────────────────────
ESTADO ACTUAL: DRY_RUN = TRUE
  ✓ El motor calcula qué haría
  ✓ Muestra recomendaciones en formula_duel_results.json
  ✓ NO aplica ningún cambio
  ✓ Tú auditas y decides
""")

print("\n" + "="*70)
print("RESUMEN")
print("="*70)

print("""
┌────────────────────────────────────────────────────────────────┐
│  FLUJO COMPLETO:                                               │
│                                                                  │
│  1. Motor ejecuta duelos (dry_run=True)                        │
│  2. Calcula si una fórmula candidata mejora                    │
│  3. Guarda RECOMENDACIÓN (no implementa)                       │
│  4. ➜ TÚ AUDITAS formula_duel_results.json                     │
│  5. ➜ TÚ VERIFICAS que tenga sentido                           │
│  6. ➜ TÚ APRUEBAS o RECHAZAS                                   │
│  7. Si apruebas: cambiar dry_run=False                         │
│  8. Motor entonces implementa el cambio                        │
│  9. En 7 días: auditoría automática                            │
│ 10. Si es mejor: mantener. Si empeora: revertir               │
│                                                                  │
│  ESTADO: Listo para auditar. Esperando verificación.          │
└────────────────────────────────────────────────────────────────┘
""")

# Ahora intenta mostrar qué hay actualmente en los resultados
print("\n" + "="*70)
print("RESULTADOS ACTUALES EN EL SISTEMA")
print("="*70)

results_file = Path('data/formula_duel_results.json')
if results_file.exists():
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    if results:
        print(f"\nÚltimos {len(results)} duelos ejecutados:\n")
        for i, result in enumerate(results[-5:], 1):
            print(f"{i}. {result.get('parametro', '?').upper()}")
            print(f"   Ganador:  {result.get('ganador', '?')}")
            print(f"   Score:    {result.get('score_alt', 0):.4f} (+{(result.get('score_alt', 0) - result.get('score_actual', 0))*100:.2f}%)")
            print(f"   Dry-run:  {result.get('dry_run', 'N/A')}")
            print(f"   Contaminación:  {result.get('contaminacion_detectada', False)}")
            print()
    else:
        print("📝 No hay duelos registrados aún.")
        print("   El sistema necesita datos históricos limpios para ejecutar duelos.")
        print("   Los duelos se ejecutan automáticamente cada 24 horas.")
else:
    print("📝 Archivo no existe aún.")
    print("   Se creará después del primer duelo ejecutado.")

print("\n" + "="*70)
