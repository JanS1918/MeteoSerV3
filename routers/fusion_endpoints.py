"""
═══════════════════════════════════════════════════════════════════════════════
MÓDULO: ENDPOINTS API DE FUSIÓN ADAPTATIVA WH65 + WH31
═══════════════════════════════════════════════════════════════════════════════

Endpoints para consultar, configurar y monitorear la fusión adaptativa de sensores.
"""

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Importar componentes de fusión
try:
    from core.sensors.adaptive_sensor_fusion import (
        media_adaptativa,
        detectar_anomalia,
        evaluar_sesgo_radiacion_wh65,
        analizar_patrones_fusion
    )
    from core.sensors.fusion_config import configuracion as config_fusion
    from core.sensors.fusion_alertas import gestor_alertas
    FUSION_DISPONIBLE = True
except ImportError as e:
    FUSION_DISPONIBLE = False
    logger.warning(f"[FUSION API] Módulos de fusión no disponibles: {e}")

# Crear router
router = APIRouter(prefix="/api/v1/fusion", tags=["Fusión Sensores"])


@router.get("/status")
async def fusion_status():
    """Estado actual del sistema de fusión adaptativa."""
    if not FUSION_DISPONIBLE:
        return {"status": "unavailable", "error": "Módulos de fusión no disponibles"}
    
    return {
        "status": "operational",
        "version": "1.0.0",
        "sensores_esperados": {
            "principal": "temperatura (WH65)",
            "complementario": "temperatura_wh31 (WH31)"
        },
        "contextos_disponibles": list(
            config_fusion.obtener('ponderaciones', {}).keys()
            if config_fusion else []
        ),
        "alertas_activas": len(gestor_alertas.obtener_alertas_activas()) if FUSION_DISPONIBLE else 0
    }


@router.get("/sensor-mix")
async def sensor_mix(
    temp_wh65: float = Query(..., description="Temperatura WH65 en °C"),
    hum_wh65: float = Query(..., description="Humedad WH65 en %"),
    temp_wh31: Optional[float] = Query(None, description="Temperatura WH31 en °C (opcional)"),
    hum_wh31: Optional[float] = Query(None, description="Humedad WH31 en %"),
    contexto: str = Query("prediccion_general", description="Contexto: confort, lluvia, rocio_niebla, etc.")
):
    """
    Calcular media adaptativa de sensores.
    
    Ejemplo:
    /api/v1/fusion/sensor-mix?temp_wh65=20&hum_wh65=60&temp_wh31=18&hum_wh31=70&contexto=confort
    """
    if not FUSION_DISPONIBLE:
        return {"error": "Módulos de fusión no disponibles"}, 503
    
    if temp_wh31 is None or hum_wh31 is None:
        return {
            "error": "Se requieren temp_wh31 y hum_wh31",
            "nota": "Si WH31 no está disponible, pasar sin fusión"
        }, 400
    
    try:
        fusion = media_adaptativa(
            temp_wh65=temp_wh65,
            hum_wh65=hum_wh65,
            temp_wh31=temp_wh31,
            hum_wh31=hum_wh31,
            contexto=contexto
        )
        
        return {
            "success": True,
            "datos_entrada": {
                "wh65": {"temperatura": round(temp_wh65, 2), "humedad": round(hum_wh65, 1)},
                "wh31": {"temperatura": round(temp_wh31, 2), "humedad": round(hum_wh31, 1)}
            },
            "media_adaptativa": {
                "temperatura": round(fusion.temperatura_media, 2),
                "humedad": round(fusion.humedad_media, 1)
            },
            "ponderaciones": {
                "temperatura": {
                    "wh65": round(fusion.peso_wh65_temp, 3),
                    "wh31": round(fusion.peso_wh31_temp, 3)
                },
                "humedad": {
                    "wh65": round(fusion.peso_wh65_hum, 3),
                    "wh31": round(fusion.peso_wh31_hum, 3)
                }
            },
            "contexto": contexto,
            "anomalia_detectada": fusion.anomalia,
            "razon_anomalia": fusion.razon_anomalia,
            "razon_fusion": fusion.razon_fusion
        }
    except Exception as e:
        logger.error(f"[FUSION API] Error en sensor-mix: {e}")
        return {"error": str(e)}, 500


@router.get("/anomalia")
async def detectar_anomalia_endpoint(
    temp_wh65: float = Query(...),
    hum_wh65: float = Query(...),
    temp_wh31: float = Query(...),
    hum_wh31: float = Query(...)
):
    """Detectar anomalía entre sensores."""
    if not FUSION_DISPONIBLE:
        return {"error": "Módulos de fusión no disponibles"}, 503
    
    anomalia, razon = detectar_anomalia(temp_wh65, hum_wh65, temp_wh31, hum_wh31)
    
    return {
        "anomalia_detectada": anomalia,
        "razon": razon,
        "datos": {
            "wh65": {"temperatura": temp_wh65, "humedad": hum_wh65},
            "wh31": {"temperatura": temp_wh31, "humedad": hum_wh31},
            "diferencias": {
                "temperatura_delta": round(abs(temp_wh65 - temp_wh31), 2),
                "humedad_delta": round(abs(hum_wh65 - hum_wh31), 1)
            }
        },
        "umbrales": {
            "temperatura_max_delta": config_fusion.obtener_umbral_anomalia_temperatura() if config_fusion else 15.0,
            "humedad_max_delta": config_fusion.obtener_umbral_anomalia_humedad() if config_fusion else 40.0
        }
    }


@router.get("/sesgo-radiacion")
async def sesgo_radiacion_endpoint(
    temp_wh65: float = Query(...),
    temp_wh31: float = Query(...),
    radiacion_w_m2: float = Query(0, description="Radiación solar en W/m²")
):
    """Evaluar si WH65 está sesgado por radiación solar."""
    if not FUSION_DISPONIBLE:
        return {"error": "Módulos de fusión no disponibles"}, 503
    
    sesgo = evaluar_sesgo_radiacion_wh65(temp_wh65, temp_wh31, radiacion_w_m2)
    
    return {
        "sesgo_probable": sesgo['sesgo_radiacion_probable'],
        "radiacion_w_m2": sesgo['radiacion_w_m2'],
        "temperatura_wh65_mayor_que_wh31": sesgo['diferencia_temp_wh65_mayor'],
        "confiabilidad_wh31": sesgo['confiabilidad_wh31'],
        "recomendacion": sesgo['recomendacion']
    }


@router.get("/alertas")
async def obtener_alertas():
    """Obtener alertas activas de anomalías y microclima."""
    if not FUSION_DISPONIBLE:
        return {"error": "Módulos de fusión no disponibles"}, 503
    
    alertas = gestor_alertas.obtener_alertas_activas()
    estadisticas = gestor_alertas.obtener_estadisticas()
    
    return {
        "alertas_activas": len(alertas),
        "alertas": alertas,
        "estadisticas": estadisticas
    }


@router.get("/config")
async def obtener_configuracion():
    """Obtener configuración actual de ponderaciones."""
    if not FUSION_DISPONIBLE or not config_fusion:
        return {"error": "Sistema de configuración no disponible"}, 503
    
    return {
        "version": "1.0.0",
        "configuracion": config_fusion.exportar_json()
    }


@router.post("/config/reload")
async def recargar_configuracion():
    """Recargar configuración desde archivo JSON."""
    if not config_fusion:
        return {"error": "Sistema de configuración no disponible"}, 503
    
    exito = config_fusion.recargar()
    
    return {
        "success": exito,
        "mensaje": "Configuración recargada" if exito else "Error recargando configuración"
    }


@router.get("/analisis")
async def analisis_patrones(
    ultimas_n: int = Query(1000, description="Últimas N líneas a analizar")
):
    """Analizar patrones en archivo de decisiones para ajustes."""
    if not FUSION_DISPONIBLE:
        return {"error": "Módulos de fusión no disponibles"}, 503
    
    stats = analizar_patrones_fusion(ultimas_n=ultimas_n)
    
    if stats is None:
        return {
            "status": "sin_datos",
            "mensaje": "No hay suficientes datos de historial"
        }
    
    return {
        "status": "success",
        "estadisticas": stats
    }


@router.post("/alertas/limpiar")
async def limpiar_alertas(horas_max: int = Query(24, description="Limpiar alertas mayores a N horas")):
    """Limpiar alertas antiguas del archivo de log."""
    if not FUSION_DISPONIBLE:
        return {"error": "Módulos de fusión no disponibles"}, 503
    
    eliminadas = gestor_alertas.limpiar_alertas_antiguas(horas_max=horas_max)
    
    return {
        "success": True,
        "alertas_eliminadas": eliminadas,
        "mensaje": f"Se eliminaron {eliminadas} alertas mayores a {horas_max}h"
    }


@router.get("/metricas")
async def metricas_fusion():
    """Obtener métricas de rendimiento del sistema de fusión."""
    if not FUSION_DISPONIBLE:
        return {"error": "Módulos de fusión no disponibles"}, 503
    
    stats = gestor_alertas.obtener_estadisticas()
    
    return {
        "alertas_totales": stats.get('total_alertas', 0),
        "distribucion": stats.get('por_tipo', {}),
        "tipos_alertas": stats.get('tipos_unicos', []),
        "sistema": {
            "modulo": "adaptive_sensor_fusion",
            "version": "1.0.0",
            "status": "operational"
        }
    }


@router.get("/dashboard-data")
async def get_dashboard_data(request: Request):
    """Endpoint que proporciona datos en tiempo real para el dashboard de fusión"""
    from datetime import datetime as dt_now
    import math
    try:
        
        # Asegurar que el sistema está disponible
        # Intentar obtener del app state o usar variable global
        if hasattr(request.app, 'state') and hasattr(request.app.state, 'system'):
            system = request.app.state.system
        else:
            # Importar variable global del módulo principal
            from main_asgi import system as global_system
            system = global_system
        
        if system is None:
            # Último recurso: crear uno nuevo
            from core.system.system_manager import SystemManager
            manager = SystemManager()
            system = manager.iniciar()
        
        # Acceder a sensores (están en la dict)
        sensores = system.sensores if hasattr(system, 'sensores') else {}
        
        # Obtener WH65 (exterior expuesto)
        wh65_temp = sensores.get("temperatura", 0.0) or 0.0
        wh65_hum = sensores.get("humedad", 0.0) or 0.0
        
        # Obtener WH31 (exterior sombreado) 
        wh31_temp = sensores.get("temperatura_wh31", 0.0) or 0.0
        wh31_hum = sensores.get("humedad_wh31", 0.0) or 0.0
        
        # Obtener Interior (HP2550A)
        interior_temp = sensores.get("temperatura_interior", 0.0) or 0.0
        interior_hum = sensores.get("humedad_interior", 0.0) or 0.0
        
        # Obtener datos ambientales
        presion = sensores.get("presion", 1013.25) or 1013.25
        radiacion_medida = sensores.get("solarradiation_original")
        viento_vel = sensores.get("viento_velocidad", 0.0) or 0.0
        
        # Calcular punto de rocío (Magnus formula)
        def calcular_punto_rocio(temp_c, humedad_rel):
            """Calcula punto de rocío con formula Magnus precisa"""
            if humedad_rel <= 0:
                return temp_c
            a = 17.27
            b = 237.7
            alpha = ((a * temp_c) / (b + temp_c)) + math.log(humedad_rel / 100.0)
            tdp = (b * alpha) / (a - alpha)
            return round(tdp, 1)
        
        punto_rocio_exterior = calcular_punto_rocio(wh65_temp, wh65_hum)
        punto_rocio_interior = calcular_punto_rocio(interior_temp, interior_hum)
        
        # Procesar radiación con modelo hibrido REST2
        radiacion_data = {}
        ghi_final = 0
        confianza_rad = 0
        hay_nubes = False
        
        try:
            from core.indices.radiacion_hibrida import procesar_radiacion_sistema
            radiacion_data = procesar_radiacion_sistema(sensores, system) or {}
            
            # EXTRAER TODO DE RADIACION_DATA (V51 COMPLETO)
            ghi_final = radiacion_data.get("ghi_final_w_m2") or 0
            dni_final = radiacion_data.get("dni_w_m2") or 0
            dhi_final = radiacion_data.get("dhi_w_m2") or 0
            confianza_rad = radiacion_data.get("confianza_pct") or 0
            hay_nubes = radiacion_data.get("hay_nubes", False)
            clearness_index = radiacion_data.get("clearness_index", 0.0)
            arquitectura_v51 = radiacion_data.get("arquitectura_v51", False)
            fuente_radiacion = radiacion_data.get("fuente", "modelo")
            
            # Parámetros atmosféricos
            agua_precipitable = radiacion_data.get("agua_precipitable_cm", 1.5)
            aerosol_optical_depth = radiacion_data.get("aerosol_optical_depth", 0.1)
            
            # Validación térmica
            diferencial_termico = radiacion_data.get("diferencial_termico", {})
            
            # Validar que son numéricos
            if not isinstance(ghi_final, (int, float)):
                ghi_final = float(ghi_final) if ghi_final else 0
            if not isinstance(confianza_rad, (int, float)):
                confianza_rad = int(confianza_rad) if confianza_rad else 0
            
            # LOGUEAR RADIACION COMPLETA EN DEBUG
            logger.debug(f"[RADIACION COMPLETA] GHI={ghi_final:.1f} W/m², DNI={dni_final:.1f} W/m², DHI={dhi_final:.1f} W/m²")
            logger.debug(f"[RADIACION] Arquitectura: {'V51_ROBUSTO' if arquitectura_v51 else 'REST2_v3'}, Confianza: {confianza_rad}%, Fuente: {fuente_radiacion}")
            logger.debug(f"[ATMOSFERA] Agua precipitable: {agua_precipitable:.2f} cm, AOD500: {aerosol_optical_depth:.4f}")
                
        except Exception as e:
            logger.warning(f"Radiación híbrida no disponible: {e}")
            ghi_final = float(radiacion_medida) if radiacion_medida else 0
            dni_final = 0
            dhi_final = 0
            confianza_rad = 60 if radiacion_medida else 0
            hay_nubes = False
            clearness_index = 0.0
            arquitectura_v51 = False
            fuente_radiacion = "fallback"
            agua_precipitable = 1.5
            aerosol_optical_depth = 0.1
            diferencial_termico = {}
        
        # Detectar anomalías considerando que WH65 está al SOL (diferencia esperada)
        # Si elevación solar > 30°, diferencia de hasta 5°C es NORMAL
        # Si elevación solar < 10°, diferencia > 2°C seria anómala
        delta_t_absoluto = abs(wh65_temp - wh31_temp)
        
        # Obtener elevación solar para contexto
        try:
            from core.indices.radiacion_hibrida import PiranometroHibrido
            pir = PiranometroHibrido()
            pos_solar = pir.calcular_posicion_solar(dt_now.now())
            elevacion_solar = pos_solar.get("elevacion_deg", 0)
        except:
            elevacion_solar = 45  # Asumir mediodía despejado
        
        # Umbral dinámico de anomalía según elevación solar
        if elevacion_solar > 30:
            umbral_anomalia = 8  # Más margen con sol alto
        elif elevacion_solar > 10:
            umbral_anomalia = 5
        else:
            umbral_anomalia = 2  # Noche: casi nada de diferencia esperada
        
        anomalia = None
        if delta_t_absoluto > umbral_anomalia:
            anomalia = f"Diferencia térmica importante (esperada para elevación solar {elevacion_solar:.0f}°): {delta_t_absoluto:.1f}°C"
        elif abs(wh65_hum - wh31_hum) > 40:
            anomalia = f"Diferencia extrema de humedad: {abs(wh65_hum - wh31_hum):.0f}%"
        
        # Alertas
        alertas = []
        if delta_t_absoluto > 3 and elevacion_solar > 20:
            alertas.append({
                "tipo": "microclima",
                "severidad": "info",
                "mensaje": f"Microclima: ΔT={delta_t_absoluto:.1f}°C (sol está en altura)"
            })
        
        # Alerta de condensación potencial
        if punto_rocio_interior > interior_temp - 2:  # Punto rocío muy cerca de aire
            alertas.append({
                "tipo": "condensacion",
                "severidad": "warning",
                "mensaje": f"Riesgo de condensación: T={interior_temp:.1f}°C, Tdp={punto_rocio_interior:.1f}°C"
            })
        
        if hay_nubes and elevacion_solar > 10:
            alertas.append({
                "tipo": "nubosidad",
                "severidad": "info",
                "mensaje": "Nubosidad detectada por radiación baja"
            })
        
        # Calcular fusión con datos mejorados
        try:
            from core.sensors.adaptive_sensor_fusion import media_adaptativa, FusionConfig
            config = FusionConfig()
            result = media_adaptativa(wh65_temp, wh65_hum, wh31_temp, wh31_hum, contexto='confort')
            pond = config.obtener_ponderaciones('confort')
        except:
            result = None
            pond = {'temperatura': {'wh65': 0.3, 'wh31': 0.7}, 'humedad': {'wh65': 0.4, 'wh31': 0.6}}
        
        fusion_temp = result.temp_media if result else (wh65_temp * pond['temperatura']['wh65'] + wh31_temp * pond['temperatura']['wh31'])
        fusion_hum = result.hum_media if result else (wh65_hum * pond['humedad']['wh65'] + wh31_hum * pond['humedad']['wh31'])
        
        return {
            "timestamp": dt_now.now().isoformat(),
            "sensores": {
                "wh65": {
                    "temp_c": round(wh65_temp, 1),
                    "humedad_pct": round(wh65_hum, 1),
                    "punto_rocio_c": punto_rocio_exterior,
                    "ubicacion": "Exterior Expuesto (al sol)"
                },
                "wh31": {
                    "temp_c": round(wh31_temp, 1),
                    "humedad_pct": round(wh31_hum, 1),
                    "punto_rocio_c": calcular_punto_rocio(wh31_temp, wh31_hum),
                    "ubicacion": "Exterior Sombreado (referencia)"
                },
                "interior": {
                    "temp_c": round(interior_temp, 1),
                    "humedad_pct": round(interior_hum, 1),
                    "punto_rocio_c": punto_rocio_interior,
                    "ubicacion": "Estación HP2550A"
                }
            },
            "fusion_adaptativa": {
                "temp_c": round(fusion_temp, 1),
                "humedad_pct": round(fusion_hum, 1),
                "ponderaciones": pond,
                "contexto": "confort",
                "delta_t_exterior": round(delta_t_absoluto, 1),
                "explicacion": f"WH65 al sol está {delta_t_absoluto:.1f}°C más caliente que WH31 (normal con elevación solar {elevacion_solar:.0f}°)"
            },
            "radiacion": {
                "ghi_final_w_m2": round(float(ghi_final), 1),
                "dni_final_w_m2": round(float(dni_final), 1),
                "dhi_final_w_m2": round(float(dhi_final), 1),
                "confianza_pct": int(confianza_rad),
                "hay_nubes": bool(hay_nubes),
                "clearness_index": round(float(clearness_index), 3),
                "elevacion_solar_deg": round(elevacion_solar, 1),
                "fuente": fuente_radiacion,
                "modelo_usado": "V51_ROBUSTO" if arquitectura_v51 else "REST2_v3_NREL",
                "agua_precipitable_cm": round(float(agua_precipitable), 2),
                "aerosol_optical_depth": round(float(aerosol_optical_depth), 4),
                "validacion_termica": diferencial_termico
            },
            "ambiente_exterior": {
                "temp_promedio_c": round((wh65_temp + wh31_temp) / 2, 1),
                "humedad_promedio_pct": round((wh65_hum + wh31_hum) / 2, 1),
                "presion_hpa": round(float(presion), 1),
                "viento_m_s": round(float(viento_vel), 1),
                "radiacion_w_m2": round(float(ghi_final), 1),
                "hay_nubes": bool(hay_nubes)
            },
            "anomalia": anomalia,
            "alertas": alertas,
            "metadata": {
                "timestamp_captura": dt_now.now().isoformat(),
                "actualizacion_segundos_atras": 0,
                "sensores_activos": 3,
                "radiacion_validada": confianza_rad > 70
            }
        }
    except Exception as e:
        from datetime import datetime
        import traceback
        logger.error(f"Error en dashboard-data endpoint: {e}\n{traceback.format_exc()}")
        return {
            "timestamp": datetime.now().isoformat(),
            "sensores": {
                "wh65": {"temp_c": 0.0, "humedad_pct": 0.0, "punto_rocio_c": 0.0},
                "wh31": {"temp_c": 0.0, "humedad_pct": 0.0, "punto_rocio_c": 0.0},
                "interior": {"temp_c": 0.0, "humedad_pct": 0.0, "punto_rocio_c": 0.0}
            },
            "fusion_adaptativa": {"temp_c": 0.0, "humedad_pct": 0.0, "contexto": "error"},
            "radiacion": {"ghi_final_w_m2": 0, "confianza_pct": 0},
            "ambiente_exterior": {"temp_promedio_c": 0.0, "humedad_promedio_pct": 0.0, "presion_hpa": 0, "viento_m_s": 0},
            "anomalia": f"Error del servicio: {str(e)}",
            "alertas": [],
            "metadata": {"error": str(e)}
        }


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Interfaz web del dashboard de fusión adaptativa WH65 + WH31"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Fusión Adaptativa WH65+WH31 - MeteoSerV3</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #001a4d 0%, #003d99 50%, #0066cc 100%);
                color: #fff;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            header {
                text-align: center;
                margin-bottom: 30px;
                animation: slideDown 0.6s ease-out;
            }
            header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            header p {
                font-size: 1em;
                opacity: 0.9;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: rgba(30, 60, 120, 0.8);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(100, 200, 255, 0.3);
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                transition: all 0.3s ease;
                animation: fadeIn 0.6s ease-out;
            }
            .card:hover {
                transform: translateY(-5px);
                border-color: rgba(100, 200, 255, 0.6);
                box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.5);
            }
            .card h2 {
                font-size: 1.3em;
                margin-bottom: 15px;
                color: #64c8ff;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .sensor-value {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 10px 0;
                padding: 8px;
                background: rgba(0, 102, 204, 0.2);
                border-radius: 8px;
            }
            .sensor-label {
                font-size: 0.9em;
                opacity: 0.85;
            }
            .sensor-val {
                font-size: 1.4em;
                font-weight: bold;
                color: #64c8ff;
            }
            .ponderaciones {
                background: rgba(0, 30, 80, 0.6);
                border-radius: 10px;
                padding: 10px;
                margin-top: 15px;
                font-size: 0.85em;
            }
            .ponderacion-item {
                display: flex;
                justify-content: space-between;
                margin: 5px 0;
                padding: 5px 0;
                border-bottom: 1px solid rgba(100, 200, 255, 0.2);
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #00ff00;
                animation: pulse 2s infinite;
                margin-right: 8px;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            @keyframes slideDown {
                from { transform: translateY(-30px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .charts-section {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .chart-card {
                background: rgba(30, 60, 120, 0.8);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(100, 200, 255, 0.3);
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }
            .anomalia-section {
                background: rgba(255, 100, 100, 0.2);
                border: 2px solid rgba(255, 100, 100, 0.6);
                border-radius: 10px;
                padding: 15px;
                margin-top: 20px;
                display: none;
            }
            .anomalia-section.show {
                display: block;
                animation: pulse 1s infinite;
            }
            .alerts-list {
                background: rgba(100, 50, 0, 0.3);
                border-left: 4px solid #ffaa00;
                border-radius: 8px;
                padding: 12px;
                margin-top: 15px;
            }
            .alert-item {
                padding: 8px 0;
                font-size: 0.9em;
                border-bottom: 1px solid rgba(255, 170, 0, 0.2);
            }
            .alert-item:last-child {
                border-bottom: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1><span class="status-indicator"></span>Dashboard Fusión Adaptativa</h1>
                <p>WH65 (expuesto) + WH31 (sombreado) | Actualización en tiempo real</p>
            </header>
            
            <div class="grid">
                <!-- EXTERIOR CARD -->
                <div class="card">
                    <h2>📡 Exterior</h2>
                    <div class="sensor-value">
                        <span class="sensor-label">Temperatura:</span>
                        <span class="sensor-val" id="wh65-temp">-- °C</span>
                    </div>
                    <div class="sensor-value">
                        <span class="sensor-label">Humedad:</span>
                        <span class="sensor-val" id="wh65-hum">-- %</span>
                    </div>
                </div>
                
                <!-- WH31 CARD -->
                <div class="card">
                    <h2>🌳 WH31</h2>
                    <div class="sensor-value">
                        <span class="sensor-label">Temperatura:</span>
                        <span class="sensor-val" id="wh31-temp">-- °C</span>
                    </div>
                    <div class="sensor-value">
                        <span class="sensor-label">Humedad:</span>
                        <span class="sensor-val" id="wh31-hum">-- %</span>
                    </div>
                </div>
                
                <!-- INTERIOR CARD -->
                <div class="card">
                    <h2>🏠 Interior</h2>
                    <div class="sensor-value">
                        <span class="sensor-label">Temperatura:</span>
                        <span class="sensor-val" id="interior-temp">-- °C</span>
                    </div>
                    <div class="sensor-value">
                        <span class="sensor-label">Humedad:</span>
                        <span class="sensor-val" id="interior-hum">-- %</span>
                    </div>
                </div>
                
                <!-- FUSION CARD -->
                <div class="card">
                    <h2>🔄 Fusión Adaptativa</h2>
                    <div class="sensor-value">
                        <span class="sensor-label">Temperatura Fusionada:</span>
                        <span class="sensor-val" id="fusion-temp">-- °C</span>
                    </div>
                    <div class="sensor-value">
                        <span class="sensor-label">Humedad Fusionada:</span>
                        <span class="sensor-val" id="fusion-hum">-- %</span>
                    </div>
                    <div class="ponderaciones">
                        <div style="font-weight: bold; margin-bottom: 8px; color: #64c8ff;">Ponderaciones (Contexto: Confort)</div>
                        <div class="ponderacion-item">
                            <span>Temperatura WH65:</span>
                            <span id="pond-temp-wh65">-- %</span>
                        </div>
                        <div class="ponderacion-item">
                            <span>Temperatura WH31:</span>
                            <span id="pond-temp-wh31">-- %</span>
                        </div>
                        <div class="ponderacion-item">
                            <span>Humedad WH65:</span>
                            <span id="pond-hum-wh65">-- %</span>
                        </div>
                        <div class="ponderacion-item">
                            <span>Humedad WH31:</span>
                            <span id="pond-hum-wh31">-- %</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- CHARTS SECTION -->
            <div class="charts-section">
                <div class="chart-card">
                    <h2 style="margin-bottom: 15px; color: #64c8ff;">📈 Evolución de Temperatura (últimas 24h)</h2>
                    <canvas id="tempChart"></canvas>
                </div>
                <div class="chart-card">
                    <h2 style="margin-bottom: 15px; color: #64c8ff;">💧 Evolución de Humedad (últimas 24h)</h2>
                    <canvas id="humChart"></canvas>
                </div>
            </div>
            
            <!-- ANOMALIAS / ALERTAS -->
            <div class="anomalia-section" id="anomaliaSection">
                <h3>⚠️ Anomalía Detectada</h3>
                <p id="anomaliaText"></p>
            </div>
            
            <div class="alerts-list" id="alertsList">
                <div style="font-weight: bold; margin-bottom: 10px; color: #ffaa00;">📢 Alertas de Microclima</div>
                <div id="alertsContent">Sin alertas activas</div>
            </div>
        </div>
        
        <script>
            let tempChart, humChart;
            let tempData = [], humData = [], timestamps = [];
            const maxDataPoints = 24;
            
            function initCharts() {
                const ctxTemp = document.getElementById('tempChart').getContext('2d');
                tempChart = new Chart(ctxTemp, {
                    type: 'line',
                    data: {
                        labels: timestamps,
                        datasets: [
                            {
                                label: 'WH65 (Expuesto)',
                                data: tempData.map(d => d.wh65 || 0),
                                borderColor: '#ff6b6b',
                                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'WH31 (Sombreado)',
                                data: tempData.map(d => d.wh31 || 0),
                                borderColor: '#51cf66',
                                backgroundColor: 'rgba(81, 207, 102, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'Fusionada',
                                data: tempData.map(d => d.fusion || 0),
                                borderColor: '#64c8ff',
                                backgroundColor: 'rgba(100, 200, 255, 0.1)',
                                tension: 0.4,
                                borderWidth: 3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { labels: { color: '#fff' } } },
                        scales: {
                            y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#fff' } },
                            x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#fff' } }
                        }
                    }
                });
                
                const ctxHum = document.getElementById('humChart').getContext('2d');
                humChart = new Chart(ctxHum, {
                    type: 'line',
                    data: {
                        labels: timestamps,
                        datasets: [
                            {
                                label: 'WH65 (Expuesto)',
                                data: humData.map(d => d.wh65 || 0),
                                borderColor: '#ff6b6b',
                                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'WH31 (Sombreado)',
                                data: humData.map(d => d.wh31 || 0),
                                borderColor: '#51cf66',
                                backgroundColor: 'rgba(81, 207, 102, 0.1)',
                                tension: 0.4
                            },
                            {
                                label: 'Fusionada',
                                data: humData.map(d => d.fusion || 0),
                                borderColor: '#64c8ff',
                                backgroundColor: 'rgba(100, 200, 255, 0.1)',
                                tension: 0.4,
                                borderWidth: 3
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { labels: { color: '#fff' } } },
                        scales: {
                            y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#fff' } },
                            x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#fff' } }
                        }
                    }
                });
            }
            
            async function updateData() {
                try {
                    const response = await fetch('/api/v1/fusion/dashboard-data');
                    const data = await response.json();
                    
                    // Update sensor values
                    document.getElementById('wh65-temp').textContent = data.wh65.temp.toFixed(1) + ' °C';
                    document.getElementById('wh65-hum').textContent = data.wh65.hum.toFixed(0) + ' %';
                    document.getElementById('wh31-temp').textContent = data.wh31.temp.toFixed(1) + ' °C';
                    document.getElementById('wh31-hum').textContent = data.wh31.hum.toFixed(0) + ' %';
                    document.getElementById('interior-temp').textContent = data.interior.temp.toFixed(1) + ' °C';
                    document.getElementById('interior-hum').textContent = data.interior.hum.toFixed(0) + ' %';
                    document.getElementById('fusion-temp').textContent = data.fusion.temp.toFixed(1) + ' °C';
                    document.getElementById('fusion-hum').textContent = data.fusion.hum.toFixed(0) + ' %';
                    
                    // Update ponderations
                    document.getElementById('pond-temp-wh65').textContent = (data.ponderaciones.temperatura.wh65 * 100).toFixed(0) + '%';
                    document.getElementById('pond-temp-wh31').textContent = (data.ponderaciones.temperatura.wh31 * 100).toFixed(0) + '%';
                    document.getElementById('pond-hum-wh65').textContent = (data.ponderaciones.humedad.wh65 * 100).toFixed(0) + '%';
                    document.getElementById('pond-hum-wh31').textContent = (data.ponderaciones.humedad.wh31 * 100).toFixed(0) + '%';
                    
                    // Update anomaly
                    const anomaliaSection = document.getElementById('anomaliaSection');
                    if (data.anomalia) {
                        document.getElementById('anomaliaText').textContent = data.anomalia;
                        anomaliaSection.classList.add('show');
                    } else {
                        anomaliaSection.classList.remove('show');
                    }
                    
                    // Update alerts
                    const alertsList = document.getElementById('alertsContent');
                    if (data.alertas && data.alertas.length > 0) {
                        alertsList.innerHTML = data.alertas.map(a => 
                            `<div class="alert-item">🔔 ${a.mensaje}</div>`
                        ).join('');
                    } else {
                        alertsList.innerHTML = 'Sin alertas activas';
                    }
                    
                    // Update charts
                    const now = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
                    timestamps.push(now);
                    tempData.push({
                        wh65: data.wh65.temp,
                        wh31: data.wh31.temp,
                        fusion: data.fusion.temp
                    });
                    humData.push({
                        wh65: data.wh65.hum,
                        wh31: data.wh31.hum,
                        fusion: data.fusion.hum
                    });
                    
                    if (timestamps.length > maxDataPoints) {
                        timestamps.shift();
                        tempData.shift();
                        humData.shift();
                    }
                    
                    if (tempChart && humChart) {
                        tempChart.data.labels = timestamps;
                        tempChart.data.datasets[0].data = tempData.map(d => d.wh65);
                        tempChart.data.datasets[1].data = tempData.map(d => d.wh31);
                        tempChart.data.datasets[2].data = tempData.map(d => d.fusion);
                        tempChart.update('none');
                        
                        humChart.data.labels = timestamps;
                        humChart.data.datasets[0].data = humData.map(d => d.wh65);
                        humChart.data.datasets[1].data = humData.map(d => d.wh31);
                        humChart.data.datasets[2].data = humData.map(d => d.fusion);
                        humChart.update('none');
                    }
                } catch (error) {
                    console.error('Error actualizando datos:', error);
                }
            }
            
            document.addEventListener('DOMContentLoaded', () => {
                initCharts();
                updateData();
                setInterval(updateData, 5000); // Actualizar cada 5 segundos
            });
        </script>
    </body>
    </html>
    """
