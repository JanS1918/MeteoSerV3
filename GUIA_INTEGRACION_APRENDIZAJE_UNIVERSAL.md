"""
GUÍA DE INTEGRACIÓN: Framework Universal de Aprendizaje
═══════════════════════════════════════════════════════════════════════════════════

OBJETIVO: Que TODOS los índices, sensores y predicciones aprendan automáticamente
de sus errores históricos sin cambios invasivos de código.

═══════════════════════════════════════════════════════════════════════════════════
ARQUITECTURA
═══════════════════════════════════════════════════════════════════════════════════

Capas del Sistema:

    ┌─────────────────────────────────────────────────────────┐
    │ ROUTERS & ENDPOINTS (API)                               │
    │ - fusion_endpoints.py                                   │
    │ - astronomia_endpoints.py                               │
    │ - main.py                                               │
    └────────────────────┬────────────────────────────────────┘
                         │
    ┌────────────────────▼────────────────────────────────────┐
    │ COORDINADOR DE APRENDIZAJE                              │
    │ coordinador_aprendizaje.py                              │
    │ - marcar_inicio_calculo("wbgt", contexto)               │
    │ - marcar_fin_calculo(pred_id, valor, confianza)         │
    │ - registrar_realidad("wbgt", observacion)               │
    └────────────────────┬────────────────────────────────────┘
                         │
    ┌────────────────────▼────────────────────────────────────┐
    │ FRAMEWORK DE APRENDIZAJE UNIVERSAL                      │
    │ framework_aprendizaje_universal.py                      │
    │ - registrar_prediccion()                                │
    │ - registrar_observacion()                               │
    │ - calcular_ajustes()                                    │
    │ - obtener_prediccion_corregida()                        │
    └──────────────┬──────────────────────┬──────────────────┘
                   │                      │
    ┌──────────────▼──────┐  ┌───────────▼────────────────┐
    │ HISTÓRICOS          │  │ MODELOS APRENDIDOS         │
    │ (JSONL)             │  │ (JSON)                      │
    │ Predicción → Obs    │  │ Factors de corrección      │
    │ Error calculado     │  │ Confianzas por contexto    │
    └─────────────────────┘  └────────────────────────────┘


Flujo de Datos:

    PREDICCIÓN:
    ─────────
    1. Módulo inicia: pred_id = coordinador.marcar_inicio_calculo("wbgt", contexto)
    2. Módulo calcula: wbgt = calcular_wbgt(...)
    3. Módulo termina: wbgt_corregido = coordinador.marcar_fin_calculo(pred_id, wbgt, confianza)
       ↓
       - Framework registra predicción en histórico
       - Framework aplica correcciones aprendidas
       - Framework retorna valor ya ajustado
    
    APRENDIZAJE:
    ──────────
    1. Sistema detecta realidad: coordinador.registrar_realidad("wbgt", temp_real)
       ↓
       - Framework empareja con predicción más reciente
       - Framework calcula error: error = realidad - prediccion
       - Framework guarda error en histórico
    
    2. Cada 100 observaciones: framework.calcular_ajustes()
       ↓
       - Analiza todos los errores históricos
       - Agrupa por contexto (hora, elevación solar, estación)
       - Calcula factores de corrección por contexto
       - Actualiza confianzas puntuales
       - Persiste ajustes a disk
    
    3. Próxima predicción (más adelante):
       - Framework automáticamente aplica factores aprendidos
       - Valor sale YA CORREGIDO


═══════════════════════════════════════════════════════════════════════════════════
CÓMO INTEGRAR EN CADA MÓDULO
═══════════════════════════════════════════════════════════════════════════════════

1. WBGT (core/indices/environmental_indices.py)
   ─────────────────────────────────────────────

ANTES (código actual):
━━━━━━━━━━━━━━━━━━━
def calcular_wbgt(temperatura, humedad, velocidad_viento, radiacion_ghi):
    # Cálculo WBGT
    wbgt = ...cálculo...
    return wbgt

DESPUÉS (con aprendizaje):
━━━━━━━━━━━━━━━━━━━━━━━━
from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje
from core.indices.contexto_solar import obtener_contexto_solar

def calcular_wbgt_con_aprendizaje(temperatura, humedad, velocidad_viento, radiacion_ghi, 
                                  presion, timestamp_actual):
    coordinador = obtener_coordinador_aprendizaje()
    
    # Obtener contexto actual
    contexto_solar = obtener_contexto_solar(timestamp_actual, presion, temperatura, humedad)
    
    # 1. MARCAR INICIO
    pred_id = coordinador.marcar_inicio_calculo(
        tipo_indice="wbgt",
        contexto={
            "elevacion_solar": contexto_solar.get("elevacion_solar_deg"),
            "hora": timestamp_actual.hour,
            "estado_solar": contexto_solar.get("estado"),
            "temperatura_aire": temperatura,
            "humedad_relativa": humedad,
            "radiacion_ghi": radiacion_ghi,
            "velocidad_viento": velocidad_viento
        },
        metadata={"modelo": "WBGT_ISO7243_2", "version": "1.0"}
    )
    
    # 2. CÁLCULO NORMAL (código existente sin cambios)
    wbgt = ...cálculo WBGT normal...
    
    # 3. MARCAR FIN (este retorna el valor YA CORREGIDO con aprendizaje)
    wbgt_final = coordinador.marcar_fin_calculo(
        prediccion_id=pred_id,
        valor_predicho=wbgt,
        confianza=85  # Tu confianza normal (0-100)
    )
    
    return wbgt_final  # ← Ya incluye aprendizaje automático!

# En un proceso separado (ej: cada hora) recolectar realidad:
def procesar_feedback_wbgt():
    coordinador = obtener_coordinador_aprendizaje()
    
    # Obtener temperatura de globo real del sensor (si disponible)
    tg_real = obtener_temperatura_globo_real()  # De hardware
    
    coordinador.registrar_realidad(
        tipo_indice="wbgt",
        observacion=calcular_wbgt_desde_tg(tg_real),
        contexto={
            "hora": datetime.now().hour,
            "estado_solar": obtener_contexto_solar(...).get("estado")
        },
        timestamp=datetime.now(timezone.utc)
    )


2. ET0 - Evapotranspiración (core/indices/environmental_indices.py)
   ──────────────────────────────────────────────────────────────────

INTEGRACIÓN:
━━━━━━━━━━
def calcular_et0_penman_monteith_con_aprendizaje(temperatura, humedad, velocidad_viento,
                                                  radiacion_ghi_w_m2, presion, altura, 
                                                  timestamp_actual):
    coordinador = obtener_coordinador_aprendizaje()
    
    # Marcar inicio
    pred_id = coordinador.marcar_inicio_calculo(
        tipo_indice="et0",
        contexto={
            "temperatura": temperatura,
            "humedad": humedad,
            "viento": velocidad_viento,
            "radiacion": radiacion_ghi_w_m2,
            "hora": timestamp_actual.hour,
            "estacion": obtener_estacion(timestamp_actual)
        }
    )
    
    # Cálculo
    et0 = ...cálculo Penman-Monteith...
    
    # Marcar fin
    et0_final = coordinador.marcar_fin_calculo(pred_id, et0, confianza=78)
    
    return et0_final

# Feedback: requiere balance hídrico observado (riego registrado + lluvia - escorrentía)
def procesar_feedback_et0():
    coordinador = obtener_coordinador_aprendizaje()
    
    # Obtener ET0 real del balance hídrico
    et0_real = calcular_et0_real_desde_balance_hidrico(
        riego_mm=registros_riego.obtener_total_diario(),
        lluvia_mm=estacion.lluvia_acumulada,
        escorrentia_mm=estimacion_escorrentia,
        capacidad_campo_mm=parametros_suelo.capacidad_campo
    )
    
    coordinador.registrar_realidad("et0", et0_real)


3. TEMPERATURA MÍNIMA (core/indices/deardorff_force_restore.py)
   ────────────────────────────────────────────────────────────

def calcular_temperatura_minima_con_aprendizaje(T_actual, nubosidad, 
                                                humedad, viento_nocturno, 
                                                inversión_termica, timestamp):
    coordinador = obtener_coordinador_aprendizaje()
    
    # Marcar
    pred_id = coordinador.marcar_inicio_calculo(
        tipo_indice="temperatura_minima",
        contexto={
            "t_actual": T_actual,
            "nubosidad_pct": nubosidad,
            "humedad": humedad,
            "viento_nocturno": viento_nocturno,
            "mes": timestamp.month,
            "latitude": COORDENADAS.lat
        },
        metadata={"modelo": "Deardorff_Force_Restore_Modified"}
    )
    
    # Cálculo
    t_min = ...modelo Deardorff...
    
    # Retorna ya con aprendizaje
    t_min_final = coordinador.marcar_fin_calculo(pred_id, t_min, confianza=72)
    
    return t_min_final

# Feedback: se obtiene al día siguiente con la temperatura mínima real
def procesar_feedback_t_minima():
    coordinador = obtener_coordinador_aprendizaje()
    
    # Obtener T_mín real de ayer
    t_min_real = sensor_interior.obtener_minima_del_dia_anterior()
    
    coordinador.registrar_realidad(
        tipo_indice="temperatura_minima",
        observacion=t_min_real,
        contexto={
            "mes": (datetime.now() - timedelta(days=1)).month,
            "nublado": fue_nublado_ayer()
        },
        timestamp=datetime.now(timezone.utc)
    )


4. RADIACIÓN (core/indices/radiacion_hibrida.py)
   ──────────────────────────────────────────

Ya está integrado! Ahora:
- Publica a bus: radiacion_ghi_w_m2 + contexto_solar
- Consume aprendizaje: ya corrige según histñórico

Feedback: si installer piranómetro real más adelante
    coordinador.registrar_realidad("radiacion", radiacion_piranometro_real)


5. SENSORES VIRTUALES (por ejemplo virtual_interior_temp)
   ──────────────────────────────────────────────────────

def procesar_temperatura_interior_con_aprendizaje(temp_exterior, humedad_exterior,
                                                   T_interior_estimada, radiacion_ghi,
                                                   tau_respuesta_ms):
    coordinador = obtener_coordinador_aprendizaje()
    
    # Marcar
    pred_id = coordinador.marcar_inicio_calculo(
        tipo_indice="sensor_virtual_temperatura_interior",
        contexto={
            "temp_exterior": temp_exterior,
            "humedad_exterior": humedad_exterior,
            "radiacion": radiacion_ghi,
            "tau_respuesta": tau_respuesta_ms
        }
    )
    
    # Cálculo de balance térmico
    T_int_pred = ...modelo de balance...
    
    # Con aprendizaje
    T_int_final = coordinador.marcar_fin_calculo(pred_id, T_int_pred, confianza=65)
    
    return T_int_final

# Feedback: comparar con sensor real interior
def procesar_feedback_temperatura_virtual():
    coordinador = obtener_coordinador_aprendizaje()
    
    # Obtener T interior real del sensor WH31 interior
    T_interior_real = sensor_wh31_interior.obtener_temperatura()
    
    coordinador.registrar_realidad(
        tipo_indice="sensor_virtual_temperatura_interior",
        observacion=T_interior_real
    )


6. FUSIÓN DE SENSORES (ml_ponderaciones_adaptativas.py)
   ──────────────────────────────────────────────────

def fusionar_temperatura_con_aprendizaje(temp_wh65, temp_wh31):
    coordinador = obtener_coordinador_aprendizaje()
    
    # Marcar
    pred_id = coordinador.marcar_inicio_calculo(
        tipo_indice="fusion_temperatura",
        contexto={
            "temp_wh65": temp_wh65,
            "temp_wh31": temp_wh31,
            "diferenciaΔT": temp_wh65 - temp_wh31
        }
    )
    
    # Peso actual (con aprendizaje histórico de ponderaciones)
    peso_wh65 = obtener_ponderacion_wh65_actual()  # El que calcula ml_ponderaciones
    temp_fusionada = peso_wh65 * temp_wh65 + (1 - peso_wh65) * temp_wh31
    
    # Con aprendizaje
    temp_final = coordinador.marcar_fin_calculo(pred_id, temp_fusionada, confianza=92)
    
    return temp_final

# Feedback: requiere referencia confiable (ej: estación meteorológica profesional)
def procesar_feedback_fusion():
    coordinador = obtener_coordinador_aprendizaje()
    
    # Obtener temperatura de referencia
    temp_referencia = estacion_profesional.obtener_temperatura()
    
    coordinador.registrar_realidad(
        tipo_indice="fusion_temperatura",
        observacion=temp_referencia
    )


═══════════════════════════════════════════════════════════════════════════════════
INTEGRACIÓN EN ENDPOINTS
═══════════════════════════════════════════════════════════════════════════════════

En routers/fusion_endpoints.py:

@router.get("/indice/wbgt")
async def obtener_wbgt(temperatura: float, humedad: float, 
                       radiacion: float, viento: float):
    # Todo el aprendizaje sucede transparentemente aquí:
    wbgt = calcular_wbgt_con_aprendizaje(
        temperatura=temperatura,
        humedad=humedad,
        radiacion_ghi=radiacion,
        velocidad_viento=viento,
        presion=obtener_presion_actual(),
        timestamp_actual=datetime.now(timezone.utc)
    )
    
    # wbgt YA INCLUYE las correcciones aprendidas automáticamente
    return {
        "wbgt_celsius": round(wbgt, 1),
        "unidad": "°C",
        "tipo_calculo": "con_aprendizaje",
        "reporte_aprendizaje": obtener_coordinador_aprendizaje().obtener_reporte_aprendizaje()
    }


═══════════════════════════════════════════════════════════════════════════════════
MONITOREO DE APRENDIZAJE
═══════════════════════════════════════════════════════════════════════════════════

Obtener reporte en cualquier momento:

    coordinador = obtener_coordinador_aprendizaje()
    reporte = coordinador.obtener_reporte_aprendizaje()
    
    Retorna:
    {
        "total_predicciones_registradas": 5847,
        "total_observaciones_registradas": 2134,
        "tasa_matching_pct": 36.5,  # % observaciones vs predicciones
        "modelos_aprendidos": {
            "wbgt": {
                "error_medio_pct": -2.3,  # Predicción 2.3% baja
                "confiabilidad_pct": 94.1,
                "muestras": 2134,
                "contextos_aprendidos": 47  # Diferentes contextos (hora/estado/etc)
            },
            "et0": {
                "error_medio_pct": 5.7,
                "confiabilidad_pct": 87.3,
                "muestras": 456,
                "contextos_aprendidos": 18
            },
            ...
        },
        "último_ajuste": "2026-02-10T14:32:00Z",
        "tipos_indice_activos": ["wbgt", "et0", "temperatura_minima", ...]
    }

Obtener estado de un índice específico:

    estado_wbgt = coordinador.obtener_estado_indice("wbgt")
    
    Retorna:
    {
        "tipo": "wbgt",
        "error_medio_pct": -2.3,
        "confiabilidad_pct": 94.1,
        "muestras": 2134,
        "contextos_aprendidos": 47,
        "aprendiendo": True
    }


═══════════════════════════════════════════════════════════════════════════════════
CICLO DE VIDA COMPLETO - EJEMPLO TEMPORAL
═══════════════════════════════════════════════════════════════════════════════════

DÍA 1 - TARDE (14:00):
─────────────────────
1. Usuario solicita WBGT
2. Sistema calcula: 28.5°C (sin correcciones aún, aprendizaje vacío)
3. Sistema registra predicción en histórico
4. Usuario obtiene WBGT = 28.5°C

DÍA 2 - MAÑANA (08:00):
───────────────────────
1. Sistema recolecta temp real de globo = 28.3°C
2. Sistema registra observación
3. Sistema calcula: error = 28.3 - 28.5 = -0.2°C (predicción fue 0.2°C alta)

DÍA 3 - TARDE (14:00):
─────────────────────
1. Usuario solicita WBGT nuevamente (mismas condiciones)
2. Sistema calcula nuevamente: 28.5°C
3. Pero framework detecta: "Ayer a las 14:00 resultaste 0.2°C alto"
4. Framework retorna: 28.3°C (automáticamente)
5. Usuario obtiene WBGT = 28.3°C ← YA CORREGIDO!

Después de 100+ observaciones:
└─ Framework recalcula: "Sistemáticamente a las 14:00 eres 0.8% bajo"
└─ Factor de corrección = 1.008
└─ WBGT (28.5) × 1.008 = 28.7°C
└─ Y TAMBIÉN actualiza confianza: Ahora reporta 94% confianza en WBGT


═══════════════════════════════════════════════════════════════════════════════════
CONSEJOS PRÁCTICOS
═══════════════════════════════════════════════════════════════════════════════════

1. INTEGRACIÓN GRADUAL
   - Comienza con RADIACION (ya integrada)
   - Luego WBGT, ET0 (indices principales)
   - Sensores virtuales secundarios después
   - No necesita ser todo de una vez

2. FEEDBACK REALISTA
   - WBGT: Usar temperatura real de globo si disponible
   - ET0: Balance hídrico del suelo (riego + lluvia - consumo)
   - T_MIN: Cuando pase la noche, obtener T_mín real
   - No presiones feedback artificial si no tienes datos reales

3. CONTEXTO IMPORTANTE
   - Incluye HORA (patrones diarios)
   - Incluye ESTACIÓN (errores cambian estacionalmente)
   - Incluye ESTADO SOLAR (noche/día/twilight)
   - Cuanto más contexto, mejor aprende

4. NÚMERO DE MUESTRAS
   - Primeras 50: Alta variabilidad (confianza ~50%)
   - 100-500: Emergiendo patrones (confianza ~70-80%)
   - 500+: Modelos sólidos (confianza ~85-95%)
   - 2000+: Molto confiable, aprende cambios estacionales

5. VALIDACIÓN
   Monitorea regularmente:
   - Reporte aprendizaje cada semana
   - Si error_medio_pct > 10%, revisar modelo base
   - Si confiabilidad < 60%, insuficientes muestras aún
   - Si muestras == 1 pero contextos_aprendidos > 50, algo está mal

6. VERSIONES DE MODELOS
   - Incluir número versión en metadata ({\"modelo\": \"WBGT_v2.1\"})
   - Si cambias algoritmo > 20% → versión nueva
   - Framework mantiene histórico separado por versión


═══════════════════════════════════════════════════════════════════════════════════
PERSISTENCIA DE DATOS
═══════════════════════════════════════════════════════════════════════════════════

Archivos creados automáticamente:

data/historico_predicciones_universal.jsonl
├─ 1 línea = 1 evento
├─ Predicciones sin observación:
│  {\"id\": \"wbgt_1707518...\", \"tipo_indice\": \"wbgt\", \"prediccion\": 28.5, ...}
└─ Observaciones (con error calculado):
   {\"prediccion_id\": \"wbgt_1707518...\", \"observacion\": 28.3, \"error\": -0.2, ...}

data/ajustes_aprendizaje_universal.json
├─ Modelos aprendidos
├─ Factores de corrección por contexto
├─ Confianzas actuales
└─ Timestamp del último ajuste

Puedes revisar en tiempo real:
  cat data/historico_predicciones_universal.jsonl | tail -20  # Últimas 20 predicciones
  python -m json.tool data/ajustes_aprendizaje_universal.json  # Ver modelos


═══════════════════════════════════════════════════════════════════════════════════
TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════════

P: Los valores no cambian. ¿Está aprendiendo?
R: Revisa: coordinador.obtener_reporte_aprendizaje()["total_observaciones"]
   - Si < 100: Aún muy pocas muestras
   - Si = 0: No estás registrando realidades (falta procesar_feedback_*)

P: Correcciones son muy grandes/pequeñas
R: Revisa contexto:
   - ¿Incluyes hora? (sin hora, agrupa cosas que no son comparables)
   - ¿Incluyes estado solar? (noche vs día son très diferentes)
   - Contexto vago = correcciones erráticas

P: Error_medio_pct está siempre > 5%
R: Dos posibilidades:
   1. Modelo base mal (WBGT, ET0, etc.) - revisar implementación
   2. Feedback impreciso (T real mal medida) - revisar sensores

P: ¿Cuántas observaciones necesito para confiar?
R: 
   - Desarrollo: ~100
   - Producción inicial: ~500
   - Producción estable: ~2000+
   - Multi-estacional: ~5000+ (para capturar variación anual)
"""

print(__doc__)
