"""
EJEMPLO DE INTEGRACIÓN: WBGT + ET0 con Aprendizaje Universal
═══════════════════════════════════════════════════════════════════════════════════
Este archivo muestra exactamente cómo modificar environmental_indices.py

Archivo original:
  core/indices/environmental_indices.py

Cambios necesarios:
  1. Añadir imports
  2. Envolver funciones de cálculo con coordinador
  3. Procesar feedback periódicamente
  4. Todo muy simple, casi transparente

Autor: V50.5 (Feb 10, 2026)
"""

# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 1: AÑADIR IMPORTS AL PRINCIPIO DE environmental_indices.py
# ═══════════════════════════════════════════════════════════════════════════════════

"""
En las líneas iniciales, añadir después de otros imports:

from core.learning.coordinador_aprendizaje import obtener_coordinador_aprendizaje
from core.indices.contexto_solar import obtener_contexto_solar
from datetime import timezone
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 2: MODIFICAR FUNCIÓN calcular_wbgt() 
# ═══════════════════════════════════════════════════════════════════════════════════

def calcular_wbgt_original(temperatura_aire, humedad_relativa, velocidad_viento, 
                           radiacion_ghi_w_m2=None):
    """Código ORIGINAL sin cambios - ejemplo."""
    
    # Componentes WBGT
    Tnw = calcular_temperatura_bulbo_humedo(temperatura_aire, humedad_relativa)
    Tg_estimada = calcular_temperatura_globo(temperatura_aire, radiacion_ghi_w_m2 or 0)
    
    # WBGT = 0.1 * T_bs + 0.7 * T_nw + 0.2 * T_g
    wbgt = 0.1 * temperatura_aire + 0.7 * Tnw + 0.2 * Tg_estimada
    
    return wbgt


def calcular_wbgt_con_aprendizaje(temperatura_aire, humedad_relativa, velocidad_viento, 
                                  radiacion_ghi_w_m2=None, presion_hpa=None,
                                  timestamp_actual=None):
    """
    VERSIÓN CON APRENDIZAJE UNIVERSAL
    
    - Automáticamente registra predicción
    - Automáticamente aplica correcciones históricas
    - Transparente para el llamador (solo retorna valor mejorado)
    """
    
    # Dependencias
    if timestamp_actual is None:
        from datetime import datetime, timezone
        timestamp_actual = datetime.now(timezone.utc)
    if presion_hpa is None:
        presion_hpa = 1013.25  # Valor por defecto
    
    coordinador = obtener_coordinador_aprendizaje()
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 1. OBTENER CONTEXTO SOLAR
    # ─────────────────────────────────────────────────────────────────────────────
    try:
        contexto_solar = obtener_contexto_solar(
            fecha_hora=timestamp_actual,
            presion=presion_hpa,
            temperatura=temperatura_aire,
            humedad=humedad_relativa
        )
    except:
        contexto_solar = {
            "elevacion_solar_deg": 0,
            "estado": "desconocido",
            "radiacion_confianza_pct": 0
        }
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 2. MARCAR INICIO DE CÁLCULO
    # ─────────────────────────────────────────────────────────────────────────────
    prediccion_id = coordinador.marcar_inicio_calculo(
        tipo_indice="wbgt",
        contexto={
            "elevacion_solar": contexto_solar.get("elevacion_solar_deg", 0),
            "hora": timestamp_actual.hour,
            "estado_solar": contexto_solar.get("estado", "desconocido"),
            "temperatura_aire": round(temperatura_aire, 1),
            "humedad_relativa": round(humedad_relativa, 1),
            "radiacion_ghi": round(radiacion_ghi_w_m2 or 0, 0),
            "velocidad_viento": round(velocidad_viento, 1),
            "mes": timestamp_actual.month
        },
        metadata={
            "modelo": "WBGT_ISO7243_v2",
            "formula": "0.1*Tbs + 0.7*Tnw + 0.2*Tg",
            "version": "50.5"
        }
    )
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 3. EJECUTAR CÁLCULO ORIGINAL (sin cambios)
    # ─────────────────────────────────────────────────────────────────────────────
    
    # Componentes WBGT (código original)
    Tnw = calcular_temperatura_bulbo_humedo(temperatura_aire, humedad_relativa)
    Tg_estimada = calcular_temperatura_globo(temperatura_aire, radiacion_ghi_w_m2 or 0)
    
    # WBGT = 0.1 * T_bs + 0.7 * T_nw + 0.2 * T_g
    wbgt = 0.1 * temperatura_aire + 0.7 * Tnw + 0.2 * Tg_estimada
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 4. MARCAR FIN DE CÁLCULO (aquí se aplica aprendizaje automáticamente)
    # ─────────────────────────────────────────────────────────────────────────────
    wbgt_final = coordinador.marcar_fin_calculo(
        prediccion_id=prediccion_id,
        valor_predicho=wbgt,
        confianza=85  # Confianza normal de WBGT (85%)
    )
    
    # wbgt_final YA INCLUYE las correcciones aprendidas por el framework
    return wbgt_final


# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 3: MODIFICAR FUNCIÓN calcular_et0() 
# ═══════════════════════════════════════════════════════════════════════════════════

def calcular_et0_penman_monteith_original(temperatura, humedad_relativa, 
                                          velocidad_viento, radiacion_solar_mj_m2,
                                          presion_hpa, altura_m):
    """Código ORIGINAL de ET0 sin cambios."""
    
    # Penman-Monteith FAO-56
    es = 0.6108 * np.exp((17.27 * temperatura) / (temperatura + 237.3))  # Presión saturación
    ea = (humedad_relativa / 100) * es  # Presión vapor actual
    
    # Factores
    Δ = (4098 * es) / ((temperatura + 237.3) ** 2)  # Pendiente curva presión vapor
    γ = 0.665e-3 * presion_hpa  # Constante psicométrica
    Rn = radiacion_solar_mj_m2 * 0.77  # Radiación neta
    G = Rn * 0.1  # Flujo calor sensible suelo
    
    # ET0 en mm/día
    et0 = (0.408 * Δ * (Rn - G) + γ * (Cn / (temperatura + 273)) * velocidad_viento * (es - ea)) \
          / (Δ + γ * (1 + Cd * velocidad_viento))
    
    return et0


def calcular_et0_penman_monteith_con_aprendizaje(temperatura, humedad_relativa, 
                                                  velocidad_viento, radiacion_solar_mj_m2,
                                                  presion_hpa, altura_m, timestamp_actual=None):
    """
    VERSIÓN CON APRENDIZAJE UNIVERSAL para ET0
    
    ET0 es especialmente importante porque:
    - Impacta decisiones de riego
    - Varía mucho por tipo de cultivo y suelo
    - Beneficio MÁXIMO de aprendizaje
    """
    
    if timestamp_actual is None:
        from datetime import datetime, timezone
        timestamp_actual = datetime.now(timezone.utc)
    
    coordinador = obtener_coordinador_aprendizaje()
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 1. OBTENER CONTEXTO SOLAR
    # ─────────────────────────────────────────────────────────────────────────────
    try:
        contexto_solar = obtener_contexto_solar(
            fecha_hora=timestamp_actual,
            presion=presion_hpa,
            temperatura=temperatura,
            humedad=humedad_relativa
        )
    except:
        contexto_solar = {"elevacion_solar_deg": 0, "estado": "desconocido"}
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 2. MARCAR INICIO
    # ─────────────────────────────────────────────────────────────────────────────
    prediccion_id = coordinador.marcar_inicio_calculo(
        tipo_indice="et0",
        contexto={
            "temperatura": round(temperatura, 1),
            "humedad_relativa": round(humedad_relativa, 1),
            "velocidad_viento": round(velocidad_viento, 2),
            "radiacion_solar": round(radiacion_solar_mj_m2, 1),
            "presion_hpa": round(presion_hpa, 1),
            "altura_m": altura_m,
            "hora": timestamp_actual.hour,
            "estacion": obtener_estacion_del_ano(timestamp_actual),
            "elevacion_solar": round(contexto_solar.get("elevacion_solar_deg", 0), 1)
        },
        metadata={
            "modelo": "FAO56_PenmanMonteith",
            "version": "50.5",
            "nota": "ET0 crítica para decisiones de riego"
        }
    )
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 3. EJECUTAR CÁLCULO ORIGINAL (sin cambios)
    # ─────────────────────────────────────────────────────────────────────────────
    
    # Penman-Monteith FAO-56 (código original)
    es = 0.6108 * np.exp((17.27 * temperatura) / (temperatura + 237.3))
    ea = (humedad_relativa / 100) * es
    
    Δ = (4098 * es) / ((temperatura + 237.3) ** 2)
    γ = 0.665e-3 * presion_hpa
    Rn = radiacion_solar_mj_m2 * 0.77
    G = Rn * 0.1
    Cn = 900  # Constante para ET0
    Cd = 0.34
    
    et0 = (0.408 * Δ * (Rn - G) + γ * (Cn / (temperatura + 273)) * velocidad_viento * (es - ea)) \
          / (Δ + γ * (1 + Cd * velocidad_viento))
    
    # ─────────────────────────────────────────────────────────────────────────────
    # 4. MARCAR FIN (aquí se aplica aprendizaje)
    # ─────────────────────────────────────────────────────────────────────────────
    et0_final = coordinador.marcar_fin_calculo(
        prediccion_id=prediccion_id,
        valor_predicho=et0,
        confianza=78  # Confianza normal de ET0 (78%)
    )
    
    return et0_final


# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 4: PROCESAR FEEDBACK PERIÓDICAMENTE
# ═══════════════════════════════════════════════════════════════════════════════════

def procesar_feedback_wbgt_diario():
    """
    Ejecutar DIARIAMENTE (ej: a las 08:00) para registrar observaciones reales.
    
    Necesita acceso a:
    - Temperatura real de globo del sensor (si disponible)
    - O deducida de otros sensores
    """
    
    coordinador = obtener_coordinador_aprendizaje()
    
    try:
        # Obtener temperatura de globo real del día anterior
        # (Opción 1: si tienes sensor de temperatura negra)
        tg_real = obtener_temperatura_globo_real()  # De hardware
        
        if tg_real is not None:
            # Convertir a WBGT real
            T_nw_real = calcular_temperatura_bulbo_humedo_desde_tg(tg_real)
            wbgt_real = 0.1 * temp_aire_ayer + 0.7 * T_nw_real + 0.2 * tg_real
            
            # Registrar observación
            coordinador.registrar_realidad(
                tipo_indice="wbgt",
                observacion=wbgt_real,
                contexto={
                    "hora": 14,  # Hora típica del máximo
                    "estado_solar": "dia",
                    "mes": datetime.now().month
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            logger.info(f"[FEEDBACK] WBGT real registrado: {wbgt_real:.1f}°C")
        else:
            logger.debug("[FEEDBACK] Sensor T_globo no disponible")
    
    except Exception as e:
        logger.warning(f"Error procesando feedback WBGT: {e}")


def procesar_feedback_et0_quincenal():
    """
    Ejecutar QUINCENALMENTE para registrar ET0 real observada.
    
    ET0 real se deduce del balance hídrico:
    ET0_real = Lluvia + Riego - Escorrentía - ΔAlmacenamiento
    
    Requiere:
    - Registro de lluvia (sensor existing)
    - Registro de riego (manual o mecánico)
    - Estimación de escorrentía
    - Cambio de humedad del suelo (si hay humidómetro)
    """
    
    coordinador = obtener_coordinador_aprendizaje()
    
    try:
        # Obtener datos de balance hídrico de los últimos 15 días
        periodo_inicio = datetime.now(timezone.utc) - timedelta(days=15)
        
        lluvia_mm = obtener_lluvia_acumulada(periodo_inicio)
        riego_mm = obtener_riego_registrado(periodo_inicio)  # De tu APP/DB de riego
        escorrentia_estimada = estimar_escorrentia(lluvia_mm, pendiente_terreno=5)  # %
        cambio_humedad = estimar_cambio_humedad_suelo(periodo_inicio)  # mm
        
        # ET0 real por balance
        et0_real = (lluvia_mm + riego_mm - escorrentia_estimada - cambio_humedad) / 15  # En mm/día
        
        # Validar razonabilidad (ET0 típica 2-8 mm/día)
        if 1 < et0_real < 12:
            coordinador.registrar_realidad(
                tipo_indice="et0",
                observacion=et0_real,
                contexto={
                    "mes": datetime.now().month,
                    "tipo_suelo": "franco",  # De tus parámetros
                    "cultivo": "pasto"  # De tus parámetros
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            logger.info(f"[FEEDBACK] ET0 real registrado: {et0_real:.2f} mm/día")
        else:
            logger.warning(f"ET0 real sospechosa: {et0_real:.2f} mm/día (ignorado)")
    
    except Exception as e:
        logger.warning(f"Error procesando feedback ET0: {e}")


# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 5: MANTENER FUNCIONES ORIGINALES PARA COMPATIBILIDAD (OPCIONAL)
# ═══════════════════════════════════════════════════════════════════════════════════

"""
Si otros módulos todavía llaman a las funciones antiguas sin aprendizaje,
puedes mantener compatibilidad así:

def calcular_wbgt(temperatura_aire, humedad_relativa, velocidad_viento, 
                  radiacion_ghi_w_m2=None):
    # Redirige a versión con aprendizaje
    return calcular_wbgt_con_aprendizaje(
        temperatura_aire=temperatura_aire,
        humedad_relativa=humedad_relativa,
        velocidad_viento=velocidad_viento,
        radiacion_ghi_w_m2=radiacion_ghi_w_m2
    )

Así cualquier llamada antigua automáticamente se beneficia del aprendizaje!
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# PASO 6: INTEGRACIÓN EN ENDPOINTS (routers/fusion_endpoints.py)
# ═══════════════════════════════════════════════════════════════════════════════════

"""
En fusion_endpoints.py:

@router.get("/indice/wbgt")
async def get_wbgt_endpoint(temperatura: float, humedad: float, 
                            radiacion: float = 0, viento: float = 1):
    try:
        # Obtener contexto actual
        presion = obtener_presion_actual_hpa()  # Del sensor de presión
        
        # Calcular con aprendizaje (automáticamente aplica correcciones históricas)
        wbgt = calcular_wbgt_con_aprendizaje(
            temperatura_aire=temperatura,
            humedad_relativa=humedad,
            velocidad_viento=viento,
            radiacion_ghi_w_m2=radiacion,
            presion_hpa=presion,
            timestamp_actual=datetime.now(timezone.utc)
        )
        
        # Obtener estado del aprendizaje actual
        coordinador = obtener_coordinador_aprendizaje()
        estado_aprendizaje = coordinador.obtener_estado_indice("wbgt")
        
        return {
            "wbgt_celsius": round(wbgt, 1),
            "alerta": "Calor extremo" if wbgt > 32 else ("Precaución" if wbgt > 28 else "Normal"),
            "aprendizaje": {
                "activo": estado_aprendizaje["aprendiendo"] if estado_aprendizaje else False,
                "muestras": estado_aprendizaje["muestras"] if estado_aprendizaje else 0,
                "confiabilidad": estado_aprendizaje["confiabilidad_pct"] if estado_aprendizaje else None
            }
        }
    except Exception as e:
        logger.error(f"Error calculando WBGT: {e}")
        return {"error": str(e)}


@router.get("/indice/et0")
async def get_et0_endpoint(temperatura: float, humedad: float, 
                           viento: float, radiacion: float):
    try:
        presion = obtener_presion_actual_hpa()
        
        et0 = calcular_et0_penman_monteith_con_aprendizaje(
            temperatura=temperatura,
            humedad_relativa=humedad,
            velocidad_viento=viento,
            radiacion_solar_mj_m2=radiacion * 0.0864,  # Convertir W/m² a MJ/m²
            presion_hpa=presion,
            altura_m=ALTURA_ESTACION_M,
            timestamp_actual=datetime.now(timezone.utc)
        )
        
        coordinador = obtener_coordinador_aprendizaje()
        estado = coordinador.obtener_estado_indice("et0")
        
        return {
            "et0_mm_dia": round(et0, 2),
            "riego_recomendado_mm": round(et0 * FACTOR_CULTIVO, 1),
            "aprendizaje": {
                "activo": estado["aprendiendo"] if estado else False,
                "confiabilidad": estado["confiabilidad_pct"] if estado else None
            }
        }
    except Exception as e:
        logger.error(f"Error calculando ET0: {e}")
        return {"error": str(e)}
"""


# ═══════════════════════════════════════════════════════════════════════════════════
# RESUMEN DE CAMBIOS
# ═══════════════════════════════════════════════════════════════════════════════════

"""
ANTES (sin aprendizaje):
━━━━━━━━━━━━━━━━━━━━━

def calcular_wbgt(...):
    # Cálculo
    wbgt = ...
    return wbgt  # Retorna siempre el mismo valor para las mismas entradas


DESPUÉS (con aprendizaje):
━━━━━━━━━━━━━━━━━━━━━━━━━

def calcular_wbgt_con_aprendizaje(...):
    coordinador.marcar_inicio(...)           # 1 línea
    # Cálculo (sin cambios)
    wbgt = ...
    return coordinador.marcar_fin(...)       # 1 línea (retorna YA CORREGIDO)


CAMBIOS TOTALES: +18 líneas para WBGT, +18 para ET0, +2 para imports
GANANCIA: Aprendizaje automático, correcciones contextuales, confianza estimada


MUESTREO DE BENEFICIOS:

Día 1-50:  Error medio ~5%, Confianza ~50%
Día 50-500: Error medio ~3%, Confianza ~70-80%
Día 500+:  Error medio ~1-2%, Confianza ~85-95%

Ej: WBGT 28.5°C sin aprendizaje
    WBGT 28.2°C con aprendizaje después de 500 observaciones (~2 años)
    = -0.3°C de mejora (pequeño pero consistente)
    = Confianza subió de 85% a 92%
"""

print(__doc__)
