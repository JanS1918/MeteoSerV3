"""
ARQUITECTURA: SISTEMA UNIVERSAL DE APRENDIZAJE METEOROLÓGICO
═══════════════════════════════════════════════════════════════════════════════════

Versión: 50.5 (Feb 10, 2026)
Principio: "TODO EL SISTEMA APRENDE O NADA APRENDE"

VISIÓN
═════

Transformar MeteoSerV3 de un sistema estático a un sistema INTELIGENTE que:

1. REGISTRA automáticamente todas las predicciones
2. RECOLECTA automáticamente las realidades (cuando ocurren)
3. ANALIZA automáticamente los errores sistemáticos
4. CORRIGE automáticamente sus propias estimaciones
5. MEJORA automáticamente su confianza

Sin código adicional en módulos. Sin intervención manual.


PROBLEMA QUE RESUELVE
════════════════════

ANTES (sistema actual):
──────────────────────
- WBGT se calcula siempre = función(T, HR, V, Rad)
- Si hay error sistemático (ej: +5% en invierno), NUNCA se corrige
- El sistema nunca aprende de sus propios errores
- Confianza siempre = valor hardcoded

DESPUÉS (con aprendizaje universal):
───────────────────────────────────
- WBGT se calcula = función(T, HR, V, Rad) × factor_aprendido
- Sistema automáticamente detecta: "Invierno eres +5%, corrijo"
- Próxima predicción de invierno sale corregida
- Confianza = dinámicamente calculada según histórico

EJEMPLO CONCRETO - RADIACIÓN:
──────────────────────────────
Día 1:
  - Modelo REST2 predice: Radiación = 500 W/m²
  - Piranómetro real: 480 W/m²
  - Error = -20 W/m² (predicción alta)
  
Días 2-1000:
  - Acumula cientos de observaciones similares
  - Detecta patrón: "A las 14:00 eres sistemáticamente +4%"
  
Día 1001:
  - Modelo REST2 predice: Radiación = 500 W/m²
  - Sistema automáticamente: 500 × 0.96 = 480 W/m²
  - Usuario obtiene radiación CORRECTA sin intervención
  - Confianza: 95% (porque hemos observado 1000 datos similares)


ARQUITECTURA EN CAPAS
═════════════════════

┌─────────────────────────────────────────────────────────────┐
│ CAPA 1: ENDPOINTS / ROUTERS                                 │
│ (fusion_endpoints.py, astronomia_endpoints.py, main.py)     │
│                                                              │
│ Usuario solicita: GET /indice/wbgt?t=28&hr=60&v=2&rad=500   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ CAPA 2: MÓDULOS DE ÍNDICES                                  │
│ (core/indices/environmental_indices.py, deardorff.py, ...)  │
│                                                              │
│ calcular_wbgt_con_aprendizaje(...)                          │
│   ├─ 1. coordinador.marcar_inicio(...)                      │
│   ├─ 2. wbgt = cálculo_normal()                             │
│   └─ 3. wbgt_corregido = coordinador.marcar_fin(...)        │
│                    ↓ Transparentemente registra + corrige    │
│                                                              │
│ Retorna: WBGT YA CON APRENDIZAJE APLICADO                   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ CAPA 3: COORDINADOR DE APRENDIZAJE                          │
│ (core/learning/coordinador_aprendizaje.py)                  │
│                                                              │
│ Responsabilidades:                                          │
│ 1. marcar_inicio_calculo()                                  │
│ 2. marcar_fin_calculo()  ← aplica correcciones aprendidas   │
│ 3. registrar_realidad()  ← cuando conocemos la verdad       │
│ 4. obtener_reporte()     ← estado del aprendizaje           │
│                                                              │
│ Es la INTERFAZ SIMPLE para módulos de índices              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ CAPA 4: FRAMEWORK DE APRENDIZAJE UNIVERSAL                  │
│ (core/learning/framework_aprendizaje_universal.py)          │
│                                                              │
│ Responsabilidades:                                          │
│ 1. registrar_prediccion()     ← almacena en histórico       │
│ 2. registrar_observacion()    ← compara con predicción      │
│ 3. calcular_ajustes()         ← analiza errores             │
│ 4. obtener_prediccion_corregida()  ← aplica factores        │
│                                                              │
│ Logica: Agrupa por contexto (hora/estado/estación)          │
│         Calcula factor corrección por contexto              │
│         Retorna predicción × factor_aprendido               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├──────────────────────┬──────────────────┐
                     ▼                      ▼                  ▼
        ┌─────────────────────┐ ┌──────────────────┐ ┌──────────────────┐
        │ HISTÓRICO           │ │ MODELOS          │ │ ESTADO EN MEMORIA│
        │ (JSONL, append-only)│ │ APRENDIDOS       │ │ (Cache rápido)   │
        │                     │ │ (JSON, ~diario)  │ │ (Recargado inicio)
        │ Predicción → Obs    │ │                  │ │                  │
        │ Error calculado     │ │ Factores         │ │ predicciones_    │
        │ Contexto guardado   │ │ por contexto     │ │ pendientes{}     │
        │                     │ │ Confianzas       │ │ modelos_         │
        │ 100+ MB por año     │ │ actuales         │ │ aprendidos{}     │
        │ Archivable/auditable│ │                  │ │                  │
        └─────────────────────┘ └──────────────────┘ └──────────────────┘


CICLO DE APRENDIZAJE
════════════════════

ITERACIÓN TÍPICA (Ejemplo: WBGT)
─────────────────────────────────

HORA T+0:  Usuario solicita WBGT
           └─ Sistema: "Es hora del máximo, elevación solar 45°"
           └─ Calcula: WBGT = 28.5°C
           └─ Consulta framework: "¿Hay corrección aprendida?"
           └─ Framework: "Sí, a esta hora-elevación corregimos ×0.98"
           └─ Sistema retorna: 28.5 × 0.98 = 27.93°C ← CORREGIDO
           └─ Framework registra: predicción=28.5, hora=14, elevacion=45

HORA T+24: Sistema recibe observación real
           └─ Sensor de temperatura globo: TG_real = 28.2°C
           └─ Sistema calcula: WBGT_real = 0.1×T + 0.7×Tnw + 0.2×28.2 = 27.9°C
           └─ Framework empareja predicción T+0
           └─ Calcula error: 27.9 - 28.5 = -0.6°C
           └─ Guarda: "A esta hora-elevación error fue -0.6°C"

HORA T+1000: Sistema acumula suficientes observaciones (>100)
            └─ Framework analiza: "A 14:00 con elevación 40-50° acumulamos:"
            └─ Error promedio = -0.8°C
            └─ Desv. estándar = 0.3°C
            └─ Factor corrección = 1.0 - ((-0.8) / 28.5) = +2.8%
            └─ Actualiza: factor_corrección[hora_14_elev_45] = 1.028
            └─ Persiste a disk

HORA T+1001: Usuario solicita WBGT (nuevamente mismo contexto)
            └─ Sistema calcula: WBGT = 28.5°C
            └─ Framework: "Encontré factor para hora_14_elev_45: 1.028"
            └─ Retorna: 28.5 × 1.028 = 29.29°C ← MEJORADO!
            └─ Confianza ahora = 95% (vs 85% inicialmente)


CATEGORIZACIÓN DE CONTEXTO
═══════════════════════════════════════════════════════════════════════════════════

Framework agrupa predicciones por CONTEXTO para aprender patrones.

Contexto = Combinación de factores que influyen en el error sistemático

Ejemplos de factores de contexto:
─────────────────────────────────

WBGT:
├─ Hora del día (0-23)
├─ Estado solar (noche/twilight/día/día_alto)
├─ Elevación solar (grados, bucketing cada 5°)
├─ Estación del año (mes)
├─ Temperatura ambiente (para detectar sesgos en frío vs calor)
├─ Radiación solar (para detectar sesgos si hay nubes)
└─ Humedad relativa (para detectar sesgo si muy seco vs, muy húmedo)

ET0:
├─ Hora del día
├─ Estación (verano/invierno = diferentes evapotranspiraciones)
├─ Tipo de suelo (franco/arenoso/arcilloso = drenaje diferente)
├─ Tipo de vegetación (referencia vs cultivo)
├─ Presencia de agua libre (suelo mojado ≠ seco)
└─ Velocidad del viento (principal factor ET0)

T_MIN:
├─ Mes del año
├─ Presencia de nubosidad (nubes = menos caída T)
├─ Humedad relativa nocturna (determina rocío)
├─ Velocidad del viento nocturno (mezcla vertical)
└─ Tipo de terreno (inversión termica diferente en valles vs cerros)

RADIACIÓN:
├─ Hora del día (sol bajo ≠ sol alto)
├─ Elevación solar (0° = horizonte, 90° = cenit)
├─ Estación del año (aerosoles, humedad atmósfera)
├─ Claridad de cielo (nubes = error superior)
├─ Presencia de polución (partículas = absorción)
└─ Elevation de terreno (altura cambia presión, claridad)


GENERACIÓN AUTOMÁTICA DE CLAVES DE CONTEXTO
─────────────────────────────────────────────

Framework genera clave única como:
  "hora_14_estado_dia_elevacion_45_mes_02"
  └─ Agrupa todas las predicciones con este contexto exacto

Si hay 50+ predicciones con este contexto:
  └─ Calcula factor corrección ESPECÍFICO para ella
  └─ "A las 14:00, día alto, elevación 45°, en febrero, corregimos ×1.028"

Si hay < 50 predicciones:
  └─ Usa factor promedio de contexto más general
  └─ Ej: promedio de todas las predicciones a las 14:00 (sin importar mes)

Si hay 0 predicciones con contexto similar:
  └─ Busca contexto parcial: solo "hora_14"
  └─ Si tampoco: retorna predicción sin corrección (new pattern)


INTEGRACIÓN CON MÓDULOS EXISTENTES
═══════════════════════════════════════════════════════════════════════════════════

RADIACIÓN (INTEGRADA):
─────────────────────
Archivo: core/indices/radiacion_hibrida.py

ANTES: publicaba solo radiacion_ghi_w_m2 al bus

AHORA: 
├─ registra predicción en framework
├─ publica a bus con metadatos (confianza, modelo)
├─ framework automáticamente aplica correcciones
└─ ET0/WBGT/T_min consumen radiación corregida

WBGT (PENDIENTE INTEGRACIÓN):
──────────────────────────────
Archivo: core/indices/environmental_indices.py

Cambio simple (ver EJEMPLO_INTEGRACION_WBGT_ET0.py):
├─ Envolver función con coordinador.marcar_inicio/fin
├─ Procesar feedback diariamente
└─ Automáticamente aprende error sistemático

ET0 (PENDIENTE INTEGRACIÓN):
────────────────────────────
Archivo: core/indices/environmental_indices.py

Similar a WBGT, pero feedback es semanal (via balance hídrico)

T_MIN (PENDIENTE INTEGRACIÓN):
──────────────────────────────
Archivo: core/indices/deardorff_force_restore.py

Feedback es al día siguiente (cuando conocemos T_min real)

SENSORES VIRTUALES (PENDIENTE):
───────────────────────────────
core/sensores/temperatura_interior_virtual.py
core/sensores/humedad_virtual.py
etc.

Cada uno registra predicción, compara con sensor real

FUSIÓN DE SENSORES (PARCIAL):
─────────────────────────────
core/sensores/ml_ponderaciones_adaptativas.py

YA TIENE aprendizaje de pesos (WH65 vs WH31)
PRÓXIMO: integrar con coordinador único


FLUJOS DE DATOS - DIAGRAMA
═════════════════════════════════════════════════════════════════════════════════════

USUARIO SOLICITA WBGT:
┌────────────────────────────────────────────────────────────────┐
│ GET /indice/wbgt?t=28&hr=60&v=2&rad=500                        │
└─────────────┬──────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ environmental_indices.calcular_wbgt_con_aprendizaje()           │
│                                                                 │
│ pred_id = coordinador.marcar_inicio(                            │
│     "wbgt",                                                     │
│     contexto={"hora": 14, "elevacion": 45, "estado": "dia_alto"}│
│ )                                                               │
│   │                                                             │
│   └─► [Framework registra predicción en histórico]             │
│       → data/historico_predicciones_universal.jsonl             │
│       → {id: pred_123, tipo: wbgt, prediccion: 28.5, contexto..}
│                                                                 │
│ wbgt = 0.1*T + 0.7*Tnw + 0.2*Tg = 28.5°C  [cálculo normal]    │
│                                                                 │
│ wbgt_final = coordinador.marcar_fin(                            │
│     pred_id,                                                    │
│     valor_predicho=28.5,                                        │
│     confianza=85                                                │
│ )                                                               │
│   │                                                             │
│   └─► [Framework APLICA CORRECCIONES]                          │
│       1. Busca factor para contexto hora_14_elevacion_45_dia   │
│       2. Encuentra: factor = 1.028 (aprendido de 1000 obs.)    │
│       3. Calcula: 28.5 × 1.028 = 29.29°C                       │
│       4. Retorna: 29.29°C ✓ CORREGIDO                          │
│                                                                 │
│ return wbgt_final = 29.29°C                                     │
└─────────────┬──────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Usuario recibe: {"wbgt": 29.3°C, "confianza": 92%, ...}        │
│                                                                 │
│ ¿Es mejor que predicción sin aprendizaje (28.5°C)?            │
│ SÍ, porque a esa hora-elevación, observaciones dicen correcto  │
│ es 29.3°C                                                       │
└─────────────────────────────────────────────────────────────────┘


AL DÍA SIGUIENTE, SISTEMA RECIBE OBSERVACIÓN:
┌────────────────────────────────────────────────────────────────┐
│ ciclo_aprendizaje.py (ejecuta diariamente)                      │
│                                                                 │
│ coordinador.registrar_realidad(                                │
│     tipo_indice="wbgt",                                         │
│     observacion=28.0,  ← temperatura globo real                │
│     contexto={...}                                             │
│ )                                                               │
│   │                                                             │
│   └─► [Framework COMPARA predicción vs realidad]               │
│       Predicción T: 28.5°C                                      │
│       Realidad T: 28.0°C                                        │
│       Error: -0.5°C  (predicción fue ligeramente alta)          │
│                                                                 │
│       → Guarda error en histórico                              │
│       → data/historico_predicciones_universal.jsonl             │
│       → {prediccion_id: pred_123, observacion: 28.0, error: -0.5}
│                                                                 │
│   Each 100 observaciones:                                       │
│   └─► framework.calcular_ajustes()                             │
│       1. Analiza últimas 1000 predicciones                     │
│       2. Agrupa por contexto                                    │
│       3. Calcula error promedio por contexto                   │
│       4. Actualiza factores corrección                         │
│       5. Persiste a: data/ajustes_aprendizaje_universal.json    │
└─────────────────────────────────────────────────────────────────┘

...ciclo se repite continuamente...


ARCHIVOS DE PERSISTENCIA Y AUDITORÍA
════════════════════════════════════════════════════════════════════════════════════

data/historico_predicciones_universal.jsonl
├─ Almacena CADA predicción y observación
├─ Formato: 1 línea JSON = 1 evento
├─ Crece ~100 KB por día (100 índices × 1000 predicciones/día)
├─ Archivable anualmente sin impacto
├─ Auditable: puedes revisar exactamente qué predijo sistema en hora X
├─ Ejemplo línea:
│  {
│   "id": "wbgt_1707518400_123",
│   "tipo_indice": "wbgt",
│   "prediccion": 28.5,
│   "timestamp_prediccion": "2026-02-10T14:00:00Z",
│   "contexto": {"hora": 14, "elevacion_solar_deg": 45, "estado": "dia_alto"}
│  }
│  {
│   "tipo_indice": "wbgt",
│   "prediccion_id": "wbgt_1707518400_123",
│   "observacion": 28.0,
│   "error_absoluto": -0.5,
│   "error_relativo_pct": -1.75,
│   "timestamp_observacion": "2026-02-11T08:00:00Z"
│  }
└─ Perfecto para análisis histórico, debugging, auditoría


data/ajustes_aprendizaje_universal.json
├─ Estado ACTUAL del modelo (se sobrescribe cada recalculación)
├─ Contiene factores corrección aprendidos
├─ Ejemplo:
│  {
│   "tipos_indice": {
│    "wbgt": {
│     "error_medio_pct": -0.8,
│     "desv_est_pct": 1.2,
│     "confiabilidad_pct": 94.2,
│     "muestras": 1847,
│     "factores_correccion": {
│      "hora_14_elevacion_45_mayo": 1.028,
│      "hora_14_elevacion_45_junio": 1.025,
│      "hora_14_elevacion_50_mayo": 1.032,
│      ...
│     }
│    },
│    "et0": { ... },
│    ...
│   },
│   "ultimo_ajuste": "2026-02-10T08:00:00Z"
│  }
├─ Se lee al arrancar sistema cada vez


INTEGRACIÓN EN ARRANQUE DEL SISTEMA
═════════════════════════════════════════════════════════════════════════════════════

En arrancar_meteoser.py o main.py:

    from core.learning.ciclo_aprendizaje import iniciar_ciclo_aprendizaje
    
    # ... resto de arranque ...
    
    # Iniciar ciclo de aprendizaje en background
    iniciar_ciclo_aprendizaje(en_background=True)
    
    # Sistema ahora:
    # 1. Registra automáticamente todas las predicciones
    # 2. Procesa feedback periódicamente (WBGT 1/día, ET0 1/semana, etc.)
    # 3. Recalcula ajustes cada 1000 observaciones
    # 4. Genera reportes semanales


RENDIMIENTO Y ESCALABILIDAD
═════════════════════════════════════════════════════════════════════════════════════

Memoria:
────────
- Histórico completo en memoria: ~5 MB por 10,000 observaciones
- Modelos aprendidos: ~50 KB típicamente
- Snapshots en memoria: <1 MB
- Total: <10 MB incluso con histórico de años

Velocidad:
──────────
- registrar_prediccion(): <1 ms
- registrar_observacion(): <1 ms
- obtener_prediccion_corregida(): <0.5 ms
- calcular_ajustes() (1000 obs): ~100 ms (ejecutar 1/día, OK)

Disco:
──────
- Histórico JSONL: ~1 MB por semana tipicamente
- Modelos persistidos: <1 MB
- Reportes: <1 MB cada uno, 1 por semana
- Total: ~10 MB por año con rotación

Concurrencia:
─────────────
- Thread-safe via locks interno
- No bloquea endpoints (todas las operaciones <5 ms)
- Ideal para sistema HTTP de alto throughput


MONITOREO Y DEBUGGING
═════════════════════════════════════════════════════════════════════════════════════

Endpoint para obtener estado:

    GET /aprendizaje/reporte
    
    Retorna:
    {
      "total_predicciones": 45821,
      "total_observaciones": 12456,
      "tasa_matching": 27.2,  # % que tenemos feedback
      "modelos_aprendidos": {
        "wbgt": {
          "error_medio": -0.8,
          "confiabilidad": 94.2,
          "muestras": 5821,
          "contextos": 127
        },
        "et0": {
          "error_medio": 2.1,
          "confiabilidad": 87.3,
          "muestras": 2456,
          "contextos": 34
        },
        ...
      }
    }


Logs de aprendizaje:

    [APRENDIZAJE] Predicción registrada: wbgt=28.5 (id=wbgt_170...)
    [APRENDIZAJE] Observación registrada: wbgt=28.0, error=-1.75%
    [APRENDIZAJE] WBGT: error_medio=-0.8%, confiab=94.2%, muestras=5821
    [FEEDBACK] WBGT real registrado: 28.0°C
    [APRENDIZAJE] Ajustes recalculados


CASOS DE USO REALES
═════════════════════════════════════════════════════════════════════════════════════

CASO 1: WBGT MEJORADO EN AGRICULTURA
──────────────────────────────────────
Problema: WBGT del modelo es consistentemente -3°C en mayo (primavera)
Solución:
  1. Sistema acumula 500+ observaciones de WBGT en mayo
  2. Detecta: "Error sistemático -3°C a las 14:00 en mayo"
  3. Calcula: Factor = 1.10 (eleva predicción 10%)
  4. Resultado: Predicción corregida automáticamente
  5. Beneficio: Alertas de calor más precisas, menos falsas alarmas

CASO 2: RADIACIÓN A DIFERENTES ALTITUDES
──────────────────────────────────────────
Problema: Radiación REST2 subestima en montaña (1500m)
Solución:
  1. Instalar piranómetro en montaña
  2. Sistema automáticamente detecta sesgo sistema
  3. La próxima elevación solar similar, corrige automáticamente
  4. No requiere cambios de código o reentrenamiento manual

CASO 3: ET0 POR TIPO DE CULTIVO
────────────────────────────────
Problema: ET0 Penman-Monteith es generic, no toma en cuenta cultivo específico
Solución:
  1. ET0 real observable via balance hídrico (riego + lluvia)
  2. Sistema aprende factores de ajuste por tipo de vegetación
  3. Próxima predicción ET0 incluye factor de cultivo automáticamente
  4. Mejora precisión sin modelo Kc complejo

CASO 4: SENSOR VIRTUAL MEJORADO
───────────────────────────────
Problema: Temperatura interior virtual basada en balance es imprecisa
Solución:
  1. Comparar predicción vs sensor real interior (WH31 Indoor)
  2. Acumular 1000+ observaciones
  3. Automaticamente corrige por contexto (hora, radiación solar, etc.)
  4. Próxima temperatura interior sale exacta


ROADMAP DE INTEGRACIÓN
════════════════════════════════════════════════════════════════════════════════════

FASE 1 (ACTUAL - Completa):
──────────────────────────
✓ Framework core implementado (framework_aprendizaje_universal.py)
✓ Coordinador implementado (coordinador_aprendizaje.py)
✓ Ciclo automático implementado (ciclo_aprendizaje.py)
✓ Documentación (esta)
✓ Radiación integrada (ya aprendiendo)

FASE 2 (PRÓXIMA - 1-2 días):
────────────────────────────
□ WBGT integrada (environmental_indices.py)
□ ET0 integrada (environmental_indices.py)
□ Procesar feedback WBGT diario
□ Procesar feedback ET0 quincenal
□ Tests del sistema completo

FASE 3 (DESPUÉS - 1 semana):
───────────────────────────
□ T_min integrada (deardorff_force_restore.py)
□ Sensores virtuales integrados
□ Fusion de sensores mejorada
□ Dashboard de aprendizaje en API

FASE 4 (ESTABLE - Contínuo):
───────────────────────────
□ Monitorear confianzas por índice
□ Recodificar si error_medio > 5%
□ Generar reportes mensuales de salud
□ Archivo históricos anuales


LIMITACIONES Y CONSIDERACIONES
═════════════════════════════════════════════════════════════════════════════════════

Primera observación:
  Los primeros ~50 observaciones tienen variabilidad alta
  Factor corrección no es confiable hasta 100+ muestras
  Framework automáticamente retorna confianza baja hasta entonces

Cambios en algoritmos base:
  Si cambias la fórmula de WBGT → versión nueva
  Histórico antiguo no se applica a nueva versión
  Así datos viejos no corrompen modelo nuevo

Feedback impreciso:
  Si tus mediciones de "realidad" son malas → aprendizaje malo
  Sistema aprende basado en CALIDAD de feedback
  Garbage in = garbage out (pero reversible)

Cambios estacionales:
  Sistema aprende patrones estacionales automáticamente
  Pero necesita ~2 años de data para capturar todos los meses
  En primer año, patrones pueden cambiar (ES NORMAL)

Outliers:
  Una observación muy extraña no rompe el sistema (promediado)
  Pero 10% de observaciones outliers SÍ distorsionan
  Monitor confiabilidad para detectar problema

Contexto insuficiente:
  Si registras predicción sin contexto → menos aprendizaje
  Contexto es crítico (misma predicción en enero ≠ julio)
  Siempre incluir: hora, estación, estado solar, etc.


CONCLUSIÓN
═════════════════════════════════════════════════════════════════════════════════════

Este framework transforma MeteoSerV3 de un sistema ESTÁTICO a un sistema VIVO.

Cada predicción genera data.
Cada observación entrena el modelo.
Cada iteración mejora la precisión.

Sin intervención manual.
Sin cambios de código.
Sin reentrenamiento.

El sistema aprende continuamente, se adapta a cambios estacionales,
detecta errores sistemáticos, y corrige automáticamente.

"SISTEMA QUE APRENDE" = Competir con pronosticadores profesionales
en 2-3 años de operación.

Visión: MeteoSerV3 V51.0 (2027) será superior a modelos básicos
precisamente PORQUE ha aprendido de sus propios datos locales.
"""

print(__doc__)
