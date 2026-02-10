"""
═══════════════════════════════════════════════════════════════════════════════
ARQUITECTURA RADIATIVA ROBUSTA V51.0 - DOCUMENTO TÉCNICO INTEGRAL
═══════════════════════════════════════════════════════════════════════════════

Fecha: 10 de febrero de 2026
Estado: En implementación (módulos base completados)
Objetivo: Transformar el piranómetro virtual de "muy bueno" a "adulto"

═══════════════════════════════════════════════════════════════════════════════
1. FILOSO DE LA ARQUITECTURA
═══════════════════════════════════════════════════════════════════════════════

PRINCIPIO CERO (NO NEGOCIABLE):
El sistema NO aprende por defecto. Solo aprende cuando el contexto es físicamente limpio.

Esto invierte la lógica tradicional:
  Traditional: "Aprendo siempre, y sí algo va mal, corrijo"
  Robusto:     "No aprendo salvo que esté 100% seguro"

El resultado es un sistema que nunca aprendes basura, aunque ocasionalmente deje de aprender.

═══════════════════════════════════════════════════════════════════════════════
2. ARQUITECTURA POR CAPAS
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 1: CLASIFICACIÓN DE CONTEXTO                                           │
│ (core/radiation/clasificador_contexto_radiativo.py)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Función: Decidir si el contexto permite aprendizaje                         │
│                                                                              │
│ ENTRADA: elevación solar, GHI, presión, HR, viento, precipitación          │
│                                                                              │
│ PROCESA:                                                                     │
│  1. Validación de entrada (no sea sensor defectuoso)                        │
│  2. Cálculo de derivada GHI (detecta nubes rápidas)                         │
│  3. Aplicación de reglas de BLOQUEO (duro):                                │
│     - Sol < 15° → BLOQUEADO                                                │
│     - Lluvia > 0.5mm/min → BLOQUEADO                                       │
│     - Niebla (visibilidad < 5km) → BLOQUEADO                               │
│     - dGHI/dt > 50 W/m²/s → BLOQUEADO (nubes rápidas)                      │
│     - Viento > 8 m/s + sol bajo → BLOQUEADO                                │
│  4. Aplicación de reglas de DEGRADACIÓN (confianza):                        │
│     - HR < 20% o > 95% → confianza -10%                                    │
│     - 20 < dGHI/dt < 50 → confianza -15%                                   │
│                                                                              │
│ SALIDA: EstadoContextoRadiativo {                                          │
│   es_valido_para_aprendizaje: bool,                                        │
│   confianza_general: [0.0, 1.0],                                           │
│   motivos_bloqueo: List[str],                                              │
│   motivos_degradacion: List[str]                                           │
│ }                                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 2: APRENDIZAJE SEPARADO                                               │
│ (core/radiation/estrategias_aprendizaje.py)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ SUBCAPA 2A: APRENDIZAJE CORRECTIVO (lento, estructural)                    │
│ ───────────────────────────────────────────────────────────────────        │
│                                                                              │
│ Función: Ajustar sesgos sistemáticos de REST2 en tu contexto local         │
│                                                                              │
│ ENTRADA: GHI modelo, GHI observado, elevación, contexto limpio, confianza  │
│                                                                              │
│ PROCESA:                                                                     │
│  1. Validación: ¿Contexto limpio? ¿Confianza > 70%? ¿Sol > 15°?          │
│  2. Si NO pasa validación → retorna último conocimiento                    │
│  3. Si SÍ pasa validación → agrega observación al historial                │
│  4. Si historial >= 20 observaciones:                                      │
│     - Calcula diferencia media (GHI observado - GHI modelo)                │
│     - Ajusta Kt_local: máximo ±10%                                         │
│     - Calcula confianza del ajuste (error relativo bajo = mayor confianza) │
│  5. Olvida datos > 14 días                                                 │
│                                                                              │
│ SALIDA: ResultadoAprendizajeCorrectivo {                                   │
│   kt_local: float,         # Índice de claridad ajustado                   │
│   pesos_ajuste: Dict,      # Otros ajustes                                 │
│   numero_observaciones: int,                                               │
│   confianza_ajuste: [0.0, 1.0],                                            │
│   motivos_bloqueo: List[str]                                               │
│ }                                                                            │
│                                                                              │
│ SUBCAPA 2B: APRENDIZAJE DIAGNÓSTICO (rápido, superficial)                 │
│ ─────────────────────────────────────────────────────────────────          │
│                                                                              │
│ Función: Detectar anomalías SIN corregir radiación                         │
│                                                                              │
│ ENTRADA: GHI modelo, GHI observado, elevación, temperatura, HR            │
│                                                                              │
│ PROCESA:                                                                     │
│  1. DIAGNÓSTICO 1: Calima (aerosoles altos)                                │
│     Síntoma: GHI observado < modelo * 0.85 + HR baja + elevación > 20°    │
│     Acción: NO corregir, solo DETECTAR con confianza                       │
│  2. DIAGNÓSTICO 2: Ensuciamiento gradual                                   │
│     Síntoma: DNI bajo sistemáticamente                                     │
│     Acción: NO corregir, solo MARCAR                                       │
│  3. DIAGNÓSTICO 3: Nubosidad fina                                          │
│     Síntoma: 0.6 <= GHI_obs/GHI_mod <= 0.8                                │
│     Acción: NO corregir, solo DETECTAR                                     │
│  4. Establecer FLAGS DE CONFIANZA por tipo de radiación                    │
│     (nunca toca valores, solo confianzas)                                  │
│                                                                              │
│ SALIDA: ResultadoAprendizajeDiagnostico {                                  │
│   calima_detectada: bool,                                                  │
│   calima_confianza: [0.0, 1.0],                                            │
│   ensuciamiento_detectado: bool,                                           │
│   nubosidad_fina_detectada: bool,                                          │
│   confianza_ghi, confianza_dni, confianza_dhi: [0.0, 1.0]                 │
│ }                                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 3: PUBLICACIÓN CON JERARQUÍA DE CONFIANZA                              │
│ (core/radiation/publicador_radiacion_robusto.py)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Función: Publicar estados radiativos con confianza y jerarquía             │
│                                                                              │
│ ESTADOS PUBLICADOS:                                                         │
│                                                                              │
│ NIVEL 1: Fundamentales (siempre)                                           │
│  ├─ radiacion_ghi_w_m2: Horizontal (valor, confianza)                      │
│  ├─ radiacion_dni_w_m2: Normal directo (valor, confianza)                  │
│  ├─ radiacion_dhi_w_m2: Difusa horizontal (valor, confianza)               │
│  └─ radiacion_rn_noche: Neta nocturna (valor, confianza)                   │
│                                                                              │
│ NIVEL 2: Derivados (si disponible)                                         │
│  ├─ radiacion_poa_humano: Plano ~60° (para WBGT)                          │
│  ├─ radiacion_poa_suelo: Suelo (para agricultura)                         │
│  └─ radiacion_poa_vertical: Vertical sur/norte                             │
│                                                                              │
│ NIVEL 3: Diagnósticos (flags)                                              │
│  ├─ flag_calima_presente: bool                                             │
│  ├─ flag_ensuciamiento: factor [0.85, 1.0]                                │
│  └─ flag_nubosidad_fina: bool                                              │
│                                                                              │
│ JERARQUÍA POR ÍNDICE:                                                       │
│                                                                              │
│ WBGT:                                                                        │
│   Prioritarios: [poa_humano, dni, dhi]     (confianza >= 0.6)              │
│   Secundarios: [ghi]                       (confianza >= 0.5)              │
│   No usar: []                                                               │
│                                                                              │
│ ET0:                                                                         │
│   Prioritarios: [dni, dhi, poa_suelo]      (confianza >= 0.6)              │
│   Secundarios: [ghi]                       (confianza >= 0.5)              │
│   No usar: []                                                               │
│                                                                              │
│ T_MIN:                                                                       │
│   Prioritarios: [rn_noche, lw_down]        (confianza >= 0.6)              │
│   Secundarios: [temperatura_c]             (confianza >= 0.5)              │
│   No usar: [ghi]                           (irrelevante de noche)          │
│                                                                              │
│ CONSUMO INTELIGENTE:                                                        │
│ Los índices NO solicitan estados directamente. Usan consumir_para_indice(): │
│   valor = publicador.consumir_para_indice('wbgt', 'poa_humano')           │
│ El publicador respeta jerarquía y umbrales de confianza automáticamente.   │
│                                                                              │
│ PUBLICACIÓN FORMATO:                                                        │
│ Cada estado incluye:                                                        │
│  {                                                                          │
│    clave: str,                                                              │
│    valor: float,                                                            │
│    unidad: str,                                                             │
│    confianza: [0.0, 1.0],  # Peso en decisiones                           │
│    fuente: 'modelo' | 'sensor' | 'hibrido',                               │
│    contexto_limpio: bool,                                                  │
│    timestamp: datetime,                                                     │
│    formula: str,            # Trazabilidad                                │
│    anotaciones: Dict        # Diagnósticos                                │
│  }                                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 4: VALIDACIÓN CRUZADA RADIACIÓN-TEMPERATURA                            │
│ (core/radiation/publicador_radiacion_robusto.py)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Función: Detectar datos sospechosos mediante correlación física             │
│                                                                              │
│ REGLA 1: Radiación alta + Temperatura no sube                              │
│   Si: GHI > 600 W/m² AND dT/dt < 0.1 °C/min                              │
│   Acción: Marcar radiación como sospechosa, penalizar confianza           │
│                                                                              │
│ REGLA 2: Radiación baja + Temperatura sube mucho                          │
│   Si: GHI < 200 W/m² AND dT/dt > 2.0 °C/min                              │
│   Acción: Marcar temperatura como sospechosa                               │
│                                                                              │
│ RESULTADO: {radiacion_sospechosa, temperatura_sospechosa, balance_ok}     │
│                                                                              │
│ USO: Penalizar confianza general si balance no es OK                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 5: ORQUESTADOR CENTRAL                                                │
│ (core/radiation/controlador_radiacion_robusto.py)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ FLUJO COMPLETO DE UN CICLO:                                                │
│                                                                              │
│  1. ENTRADA: Sensores (WH65, WH31, presión, etc.) + REST2                 │
│              Sensor radiación real (si disponible)                         │
│                                                                              │
│  2. FASE 1: CLASIFICAR CONTEXTO                                            │
│     Decir: ¿Es seguro aprender?                                           │
│     Salida: contexto (bloqueado/degradado/limpio)                         │
│                                                                              │
│  3. FASE 2: APRENDIZAJE CORRECTIVO                                        │
│     Si contexto limpio Y confianza > 70% AND observación válida:          │
│       → Agregar a historial                                                │
│     Si historial >= 20 observaciones:                                      │
│       → Recalcular Kt_local (máximo ±10%)                                 │
│     Else:                                                                   │
│       → Retornar último conocimiento                                       │
│                                                                              │
│  4. FASE 3: APRENDIZAJE DIAGNÓSTICO                                       │
│     Detectar: calima, ensuciamiento, nubosidad fina                       │
│     NO corregir, solo marcar confianzas                                   │
│                                                                              │
│  5. FASE 4: VALIDACIÓN CRUZADA                                            │
│     ¿Radiación y temperatura correlacionan bien?                          │
│     Si no: penalizar confianza                                            │
│                                                                              │
│  6. FASE 5: FUSIÓN INTELIGENTE CON SENSOR REAL                            │
│     Si sensor disponible, confiable Y balance OK:                         │
│       GHI_final = w_modelo * GHI_modelo + w_sensor * GHI_sensor           │
│     Donde w depende de confianzas calculadas                              │
│                                                                              │
│  7. FASE 6: PUBLICACIÓN EN BUS                                             │
│     Publicar GHI, DNI, DHI con confianzas calculadas                      │
│     Publicar estados secundarios (POA, Rn_noche, etc.)                    │
│     Publicar flags de diagnóstico                                          │
│                                                                              │
│  SALIDA: {                                                                  │
│    contexto: EstadoContextoRadiativo,                                      │
│    ghi_final: float,                                                       │
│    dni_final: float,                                                       │
│    dhi_final: float,                                                       │
│    confianza: float,  # Confianza global [0, 1]                           │
│    advertencias: List[str],                                                │
│    estados_publicados: List[str]                                           │
│  }                                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
3. PRINCIPIOS OPERATIVOS CLAVE
═══════════════════════════════════════════════════════════════════════════════

[P1] PARADIGMA DE NO APRENDIZAJE POR DEFECTO
     El sistema NO aprende salvo contexto sea físicamente limpio.
     Mejor ser ignorante que aprender mal.

[P2] BLOQUEO DURO vs DEGRADACIÓN SUAVE
     Bloqueo: Invalida aprendizaje completamente (Sol < 15°, lluvia, etc.)
     Degradación: Reduce confianza pero permite consumo (HR extrema, etc.)

[P3] SEPARACIÓN CORRECTIVO/DIAGNÓSTICO
     Correctivo: Ajusta pesos (Kt_local) lentamente, memoria weeks
     Diagnóstico: Detecta anomalías rápidamente, solo flags de confianza

[P4] NUNCA CORREGIR DIRECTAMENTE
     Los diagnósticos NUNCA tocan valores de radiación.
     Solo modifican confianzas y pesos en fusiones.

[P5] JERARQUÍA DE CONFIANZA EN CONSUMO
     Cada índice consume estados prioritarios si existen y son confiables.
     Si no: degrada a secundarios, o rechaza si no permite.

[P6] PENALIZAR LA DUDA, NO INTENTAR CORREGIRLA
     Si hay ambigüedad: baja confianza.
     Nunca "inventa" precisión.

[P7] VALIDACIÓN CRUZADA OBLIGATORIA
     Radiación y temperatura deben correlacionar.
     Si no: ambos bajo sospecha.

[P8] ESTADOS SAGRADOS (NO APRENDIBLES)
     Nunca aprenden:
     - Geometría solar (SPA es verdad)
     - Constantes físicas (Stefan-Boltzmann, etc.)
     - REST2 clear-sky (núcleo físico intocable)
     - Emisividades base

═══════════════════════════════════════════════════════════════════════════════
4. DIFERENCIAS CON ARQUITECTURA ANTERIOR
═══════════════════════════════════════════════════════════════════════════════

ANTES (Aprendizaje Universal):
├─ Aprendizaje "libre" con límites físicos
├─ No diferencia correctivo vs diagnóstico
├─ Confía en auditoría para evitar autoengaños
├─ Publica estados sin jerarquía
└─ Mayor aprendizaje, mayor riesgo

DESPUÉS (Robusto V51):
├─ Aprendizaje bloqueado por contexto
├─ Separación clara correctivo/diagnóstico
├─ Confía en reglas duras, no en auditoría
├─ Publica con jerarquía y confianza
└─ Menor aprendizaje, mayor estabilidad

═══════════════════════════════════════════════════════════════════════════════
5. INTEGRACIÓN CON SISTEMA EXISTENTE
═══════════════════════════════════════════════════════════════════════════════

COMPATIBILIDAD:
✓ No requiere cambios en WBGT, ET0, T_MIN, etc.
✓ No requiere cambios en contexto_solar, astronomia_indices, etc.
✓ Se integra como "capas inferiores" transparentes
✓ Los índices usan consumir_para_indice() en lugar de acceso directo

ADOPCIÓN GRADUAL:
1. Crear módulos (✓ COMPLETADO)
2. Integrar ControladorRadiacionRobusto en arranque
3. Hacer que radiacion_hibrida.py use ControladorRadiacionRobusto
4. Validar sin romper sistema actual
5. Documentar cambios
6. Deprecar acceso directo a radiación (mantener compatibilidad)

═══════════════════════════════════════════════════════════════════════════════
6. PRÓXIMOS PASOS
═══════════════════════════════════════════════════════════════════════════════

INMEDIATOS:
[ ] Crear wrapper de integración con radiacion_hibrida.py
[ ] Crear tests unitarios para cada componente
[ ] Validar sin romper sistema (dry-run)
[ ] Integración en arranque
[ ] Documentación operativa

MEDIANO PLAZO:
[ ] Integración completa de ciclo_aprendizaje con nuevas capas
[ ] Actualizar documentación de índices
[ ] Auditoría de estabilidad (7-14 días)
[ ] Ajustes finos

LARGO PLAZO:
[ ] Deprecación de acceso directo a radiación
[ ] Integración de transposición inclinada (POA)
[ ] Modelos de radiación neta nocturna avanzados

═══════════════════════════════════════════════════════════════════════════════
Autor: Sistema Robusto V51.0
Fecha: 10 de febrero de 2026
Estado: En implementación
═══════════════════════════════════════════════════════════════════════════════
"""
