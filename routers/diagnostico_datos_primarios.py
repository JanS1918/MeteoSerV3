"""
═════════════════════════════════════════════════════════════════════════════════
DIAGNÓSTICO DE DATOS PRIMARIOS - Sistema de Validación de Sensores Críticos
═════════════════════════════════════════════════════════════════════════════════

Monitorea y valida que TODOS los datos primarios (temperatura, humedad, presión)
lleguen correctamente desde los sensores físicos. 

DATOS CRÍTICOS PRIMARIOS (DEBEN LLEGAR SIEMPRE):
- Temperatura (3 sensores: WH65, WH31, HP2550A)
- Humedad (2 sensores: WH65, WH31)  
- Presión (HP2550A)
- Radiación solar
- Lluvia
- Viento (velocidad + dirección)
- Humedad del suelo (si existe)
- Rayos (si existe)
- PM2.5 (si existe)
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/diagnostico", tags=["Diagnóstico"])

# Almacén de diagnóstico
_diagnostico_state = {
    "ultima_recepcion_ecowitt": None,
    "datos_recibidos_ultimos_5min": [],
    "sensores_primarios_status": {},
    "errores_cadena_datos": []
}


def registrar_ingesta_ecowitt(data: dict, timestamp: datetime = None):
    """
    Registra cada ingesta de datos Ecowitt para diagnóstico.
    Llamar desde main_asgi.py cuando se reciban datos.
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # Extraer datos primarios
    primarios = {
        "timestamp": timestamp.isoformat(),
        "tempf_wh65": data.get("tempf"),
        "humidity_wh65": data.get("humidity"),
        "temp1f_wh31": data.get("temp1f"),
        "humidity1_wh31": data.get("humidity1"),
        "baromrelin": data.get("baromrelin"),  # Presión HP2550A
        "solarradiation": data.get("solarradiation"),
        "rainratein": data.get("rainratein"),
        "windspeedmph": data.get("windspeedmph"),
        "winddir": data.get("winddir"),
        "soilmoisture1": data.get("soilmoisture1"),
        "lightning": data.get("lightning"),
        "pm25": data.get("pm25"),
    }
    
    # Guardar últimos 5 minutos
    _diagnostico_state["datos_recibidos_ultimos_5min"].append(primarios)
    _diagnostico_state["datos_recibidos_ultimos_5min"] = [
        d for d in _diagnostico_state["datos_recibidos_ultimos_5min"]
        if datetime.fromisoformat(d["timestamp"]) > datetime.now() - timedelta(minutes=5)
    ]
    
    _diagnostico_state["ultima_recepcion_ecowitt"] = timestamp
    
    # Validar datos primarios
    validar_datos_primarios(primarios)


def validar_datos_primarios(primarios: dict):
    """Valida que los datos primarios críticos estén presentes y sean válidos."""
    
    status = {
        "wh65_temp": None,
        "wh65_hum": None,
        "wh31_temp": None,
        "wh31_hum": None,
        "presion_hp2550a": None,
        "radiacion": None,
        "lluvia": None,
        "viento_velocidad": None,
        "viento_direccion": None,
    }
    
    errores = []
    
    # WH65 - CRÍTICO
    if primarios.get("tempf_wh65") is None:
        errores.append("❌ WH65 TEMPERATURA: NO RECIBIDA")
        status["wh65_temp"] = "FALTA"
    else:
        try:
            t = float(primarios["tempf_wh65"])
            if -50 <= t <= 130:  # Rango válido Fahrenheit
                status["wh65_temp"] = "OK"
            else:
                errores.append(f"⚠️ WH65 TEMPERATURA: FUERA DE RANGO ({t}°F)")
                status["wh65_temp"] = "RANGO INVÁLIDO"
        except:
            errores.append(f"❌ WH65 TEMPERATURA: NO NUMÉRICA ({primarios['tempf_wh65']})")
            status["wh65_temp"] = "PARSE ERROR"
    
    # WH65 HUMEDAD - CRÍTICO
    if primarios.get("humidity_wh65") is None:
        errores.append("❌ WH65 HUMEDAD: NO RECIBIDA")
        status["wh65_hum"] = "FALTA"
    else:
        try:
            h = float(primarios["humidity_wh65"])
            if 0 <= h <= 100:
                status["wh65_hum"] = "OK"
            else:
                errores.append(f"⚠️ WH65 HUMEDAD: FUERA DE RANGO ({h}%)")
                status["wh65_hum"] = "RANGO INVÁLIDO"
        except:
            errores.append(f"❌ WH65 HUMEDAD: NO NUMÉRICA ({primarios['humidity_wh65']})")
            status["wh65_hum"] = "PARSE ERROR"
    
    # WH31 - IMPORTANTE
    if primarios.get("temp1f_wh31") is None:
        errores.append("⚠️ WH31 TEMPERATURA: NO RECIBIDA")
        status["wh31_temp"] = "FALTA"
    else:
        try:
            t = float(primarios["temp1f_wh31"])
            if -50 <= t <= 130:
                status["wh31_temp"] = "OK"
            else:
                errores.append(f"⚠️ WH31 TEMPERATURA: FUERA DE RANGO ({t}°F)")
                status["wh31_temp"] = "RANGO INVÁLIDO"
        except:
            errores.append(f"⚠️ WH31 TEMPERATURA: NO NUMÉRICA ({primarios['temp1f_wh31']})")
            status["wh31_temp"] = "PARSE ERROR"
    
    # WH31 HUMEDAD - IMPORTANTE
    if primarios.get("humidity1_wh31") is None:
        errores.append("⚠️ WH31 HUMEDAD: NO RECIBIDA")
        status["wh31_hum"] = "FALTA"
    else:
        try:
            h = float(primarios["humidity1_wh31"])
            if 0 <= h <= 100:
                status["wh31_hum"] = "OK"
            else:
                errores.append(f"⚠️ WH31 HUMEDAD: FUERA DE RANGO ({h}%)")
                status["wh31_hum"] = "RANGO INVÁLIDO"
        except:
            errores.append(f"⚠️ WH31 HUMEDAD: NO NUMÉRICA ({primarios['humidity1_wh31']})")
            status["wh31_hum"] = "PARSE ERROR"
    
    # PRESIÓN HP2550A - CRÍTICO
    if primarios.get("baromrelin") is None:
        errores.append("❌ PRESIÓN HP2550A: NO RECIBIDA")
        status["presion_hp2550a"] = "FALTA"
    else:
        try:
            p = float(primarios["baromrelin"])
            if 28 <= p <= 31:  # inHg range
                status["presion_hp2550a"] = "OK"
            else:
                errores.append(f"⚠️ PRESIÓN: FUERA DE RANGO ({p} inHg)")
                status["presion_hp2550a"] = "RANGO INVÁLIDO"
        except:
            errores.append(f"❌ PRESIÓN: NO NUMÉRICA ({primarios['baromrelin']})")
            status["presion_hp2550a"] = "PARSE ERROR"
    
    # RADIACIÓN - IMPORTANTE
    if primarios.get("solarradiation") is None:
        status["radiacion"] = "FALTA"
    else:
        try:
            r = float(primarios["solarradiation"])
            if 0 <= r <= 1500:
                status["radiacion"] = "OK"
        except:
            errores.append(f"⚠️ RADIACIÓN: NO NUMÉRICA")
    
    # LLUVIA - IMPORTANTE
    if primarios.get("rainratein") is None:
        status["lluvia"] = "FALTA"
    else:
        try:
            r = float(primarios["rainratein"])
            if r >= 0:
                status["lluvia"] = "OK"
        except:
            errores.append(f"⚠️ LLUVIA: NO NUMÉRICA")
    
    # VIENTO - IMPORTANTE
    if primarios.get("windspeedmph") is None:
        status["viento_velocidad"] = "FALTA"
    else:
        try:
            v = float(primarios["windspeedmph"])
            if 0 <= v <= 200:
                status["viento_velocidad"] = "OK"
        except:
            errores.append(f"⚠️ VIENTO VELOCIDAD: NO NUMÉRICA")
    
    if primarios.get("winddir") is None:
        status["viento_direccion"] = "FALTA"
    else:
        try:
            d = float(primarios["winddir"])
            if 0 <= d <= 360:
                status["viento_direccion"] = "OK"
        except:
            errores.append(f"⚠️ VIENTO DIRECCIÓN: NO NUMÉRICA")
    
    # Actualizar estado global
    _diagnostico_state["sensores_primarios_status"] = status
    if errores:
        _diagnostico_state["errores_cadena_datos"] = errores[-10:]  # Últimos 10 errores


@router.get("/sensores-primarios")
async def diagnostico_sensores_primarios():
    """Retorna estado de todos los sensores primarios críticos."""
    from core.system.system_manager import SystemManager
    
    try:
        manager = SystemManager()
        system = manager.iniciar()
        sensores = system.sensores
    except:
        sensores = {}
    
    return {
        "timestamp": datetime.now().isoformat(),
        "ultima_recepcion_ecowitt": _diagnostico_state["ultima_recepcion_ecowitt"],
        "datos_recibidos_ultimos_5min": len(_diagnostico_state["datos_recibidos_ultimos_5min"]),
        "estado_sensores": {
            "wh65_temperatura": {
                "valor": sensores.get("temperatura"),
                "estado": _diagnostico_state["sensores_primarios_status"].get("wh65_temp", "DESCONOCIDO"),
                "crítico": True,
                "expect": "Debe llegar SIEMPRE"
            },
            "wh65_humedad": {
                "valor": sensores.get("humedad"),
                "estado": _diagnostico_state["sensores_primarios_status"].get("wh65_hum", "DESCONOCIDO"),
                "crítico": True,
                "expect": "Debe llegar SIEMPRE"
            },
            "wh31_temperatura": {
                "valor": sensores.get("temperatura_wh31"),
                "estado": _diagnostico_state["sensores_primarios_status"].get("wh31_temp", "DESCONOCIDO"),
                "crítico": True,
                "expect": "Debe llegar SIEMPRE"
            },
            "wh31_humedad": {
                "valor": sensores.get("humedad_wh31"),
                "estado": _diagnostico_state["sensores_primarios_status"].get("wh31_hum", "DESCONOCIDO"),
                "crítico": True,
                "expect": "Debe llegar SIEMPRE"
            },
            "presion_hp2550a": {
                "valor": sensores.get("presion"),
                "estado": _diagnostico_state["sensores_primarios_status"].get("presion_hp2550a", "DESCONOCIDO"),
                "crítico": True,
                "expect": "Debe llegar SIEMPRE"
            },
            "radiacion_solar": {
                "valor": sensores.get("radiacion"),
                "estado": _diagnostico_state["sensores_primarios_status"].get("radiacion", "DESCONOCIDO"),
                "crítico": True,
                "expect": "Sensor dedicado"
            },
            "lluvia": {
                "valor": sensores.get("lluvia"),
                "estado": _diagnostico_state["sensores_primarios_status"].get("lluvia", "DESCONOCIDO"),
                "crítico": True,
                "expect": "Sensor dedicado"
            },
            "viento_velocidad": {
                "valor": sensores.get("viento"),
                "estado": _diagnostico_state["sensores_primarios_status"].get("viento_velocidad", "DESCONOCIDO"),
                "crítico": True,
                "expect": "Sensor dedicado"
            },
            "viento_direccion": {
                "valor": sensores.get("direccion_viento"),
                "estado": _diagnostico_state["sensores_primarios_status"].get("viento_direccion", "DESCONOCIDO"),
                "crítico": True,
                "expect": "Sensor dedicado"
            },
            "humedad_suelo_wh51": {
                "valor": sensores.get("wh51"),
                "estado": "OPCIONAL",
                "crítico": False,
                "expect": "Si existe sensor"
            },
            "rayos": {
                "valor": sensores.get("lightning"),
                "estado": "OPCIONAL",
                "crítico": False,
                "expect": "Si existe sensor"
            },
            "pm25": {
                "valor": sensores.get("pm25"),
                "estado": "OPCIONAL",
                "crítico": False,
                "expect": "Si existe sensor"
            }
        },
        "errores_detectados": _diagnostico_state["errores_cadena_datos"],
        "recomendaciones": generar_recomendaciones()
    }


def generar_recomendaciones():
    """Genera recomendaciones basadas en errores detectados."""
    recs = []
    
    status = _diagnostico_state["sensores_primarios_status"]
    
    if status.get("wh65_temp") != "OK":
        recs.append({
            "sensor": "WH65",
            "problema": "Temperatura no llega",
            "pasos": [
                "1. Verificar WH65 está encendido",
                "2. Verificar conexión WiFi del WH65",
                "3. Confirmar IP/URL correcta en WH65",
                "4. Revisar logs de /ecowitt endpoint",
                "5. Enviar test: curl -X POST 'http://localhost:8080/ecowitt?tempf=70&humidity=50'"
            ]
        })
    
    if status.get("presion_hp2550a") != "OK":
        recs.append({
            "sensor": "HP2550A",
            "problema": "Presión no llega",
            "pasos": [
                "1. HP2550A es CRÍTICO - alimentación SIEMPRE",
                "2. Verificar puerto USB del HP2550A",
                "3. Revisar drivers Ecowitt en HP2550A",
                "4. Confirmar endpoint /ecowitt está disponible",
                "5. Revisar puerto 8080 accesible desde HP2550A"
            ]
        })
    
    if len(_diagnostico_state["datos_recibidos_ultimos_5min"]) == 0:
        recs.append({
            "sensor": "TODOS",
            "problema": "Ningún dato se está recibiendo",
            "pasos": [
                "1. CRÍTICO: No hay ingestas en últimos 5 minutos",
                "2. Verificar que /ecowitt endpoint está activo",
                "3. Verificar firewall permite puerto 8080",
                "4. Test manual: python probar_envio_ecowitt.py",
                "5. Revisar logs del servidor en arrancar_meteoser.py"
            ]
        })
    
    return recs


@router.get("/panel-diagnostico", response_class=HTMLResponse)
async def panel_diagnostico():
    """Panel visual de diagnóstico en tiempo real."""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Diagnóstico Datos Primarios MeteoSerV3</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Courier New', monospace;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #00ff00;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(0, 0, 0, 0.8);
                border: 2px solid #00ff00;
                border-radius: 10px;
                padding: 20px;
            }
            h1 {
                text-align: center;
                margin-bottom: 20px;
                color: #00ff00;
                text-shadow: 0 0 10px #00ff00;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            .sensor-box {
                background: rgba(0, 50, 0, 0.5);
                border: 1px solid #00ff00;
                border-radius: 5px;
                padding: 15px;
                font-size: 12px;
            }
            .sensor-box.critico { border-color: #ff4444; background: rgba(100, 0, 0, 0.3); }
            .sensor-box.critico.ok { border-color: #00ff00; background: rgba(0, 100, 0, 0.3); }
            .sensor-box.critico.error { border-color: #ff0000; background: rgba(150, 0, 0, 0.4); }
            
            .sensor-name {
                font-weight: bold;
                color: #ffff00;
                margin-bottom: 5px;
            }
            .sensor-value {
                color: #00ff00;
                margin: 3px 0;
            }
            .sensor-status {
                margin-top: 5px;
                padding-top: 5px;
                border-top: 1px solid #00aa00;
            }
            .status-ok { color: #00ff00; }
            .status-warn { color: #ffaa00; }
            .status-error { color: #ff4444; }
            
            .errores-section {
                background: rgba(100, 0, 0, 0.2);
                border: 2px solid #ff4444;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
            }
            .errores-section h3 { color: #ff4444; margin-bottom: 10px; }
            .error-item {
                color: #ff8888;
                margin: 5px 0;
                padding-left: 20px;
            }
            
            .recomendaciones {
                background: rgba(0, 50, 100, 0.2);
                border: 2px solid #4488ff;
                border-radius: 5px;
                padding: 15px;
            }
            .recomendaciones h3 { color: #4488ff; margin-bottom: 10px; }
            .recomendacion-item {
                background: rgba(0, 0, 0, 0.5);
                border-left: 3px solid #4488ff;
                padding: 10px;
                margin: 10px 0;
                border-radius: 3px;
            }
            .recomendacion-item strong {
                color: #88ccff;
                display: block;
                margin-bottom: 5px;
            }
            .paso {
                color: #00ff00;
                margin: 3px 0;
                margin-left: 15px;
                font-size: 11px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 DIAGNÓSTICO DATOS PRIMARIOS - MeteoSerV3 V50</h1>
            
            <div id="contenido">
                <p style="text-align: center; color: #ffaa00;">Cargando...</p>
            </div>
        </div>
        
        <script>
            async function actualizar() {
                try {
                    const resp = await fetch('/diagnostico/sensores-primarios');
                    const data = await resp.json();
                    
                    let html = `
                        <p style="text-align: center; color: #888;">
                            Actualizado: ${new Date(data.timestamp).toLocaleTimeString('es-ES')}<br>
                            Ingestas últimos 5 min: <span style="color: #ffff00;">${data.datos_recibidos_ultimos_5min}</span>
                        </p>
                    `;
                    
                    // Sensores
                    html += '<div class="grid">';
                    for (const [nombre, sensor] of Object.entries(data.estado_sensores)) {
                        let estilo = sensor.estado === 'OK' ? 'ok' : 'error';
                        if (sensor.estado === 'DESCONOCIDO' || sensor.estado === 'FALTA') estilo = 'warn';
                        
                        html += `
                            <div class="sensor-box ${sensor.crítico ? 'critico ' : ''}${estilo}">
                                <div class="sensor-name">${nombre.toUpperCase()}</div>
                                <div class="sensor-value">Valor: <span style="color: #00ffff;">${sensor.valor ? sensor.valor.toFixed(2) : 'NULL'}</span></div>
                                <div class="sensor-status">
                                    Estado: <span class="status-${estilo}">${sensor.estado}</span><br>
                                    Crítico: ${sensor.crítico ? '🔴 SÍ' : '🟢 NO'}
                                </div>
                            </div>
                        `;
                    }
                    html += '</div>';
                    
                    // Errores
                    if (data.errores_detectados.length > 0) {
                        html += '<div class="errores-section"><h3>⚠️ ERRORES DETECTADOS</h3>';
                        for (const error of data.errores_detectados) {
                            html += `<div class="error-item">${error}</div>`;
                        }
                        html += '</div>';
                    }
                    
                    // Recomendaciones
                    if (data.recomendaciones.length > 0) {
                        html += '<div class="recomendaciones"><h3>💡 RECOMENDACIONES</h3>';
                        for (const rec of data.recomendaciones) {
                            html += `
                                <div class="recomendacion-item">
                                    <strong>${rec.sensor}: ${rec.problema}</strong>
                                    ${rec.pasos.map(p => `<div class="paso">${p}</div>`).join('')}
                                </div>
                            `;
                        }
                        html += '</div>';
                    }
                    
                    document.getElementById('contenido').innerHTML = html;
                } catch (err) {
                    document.getElementById('contenido').innerHTML = `
                        <p style="color: #ff4444;">ERROR: ${err.message}</p>
                    `;
                }
            }
            
            actualizar();
            setInterval(actualizar, 3000); // Actualizar cada 3 segundos
        </script>
    </body>
    </html>
    """


@router.post("/inyectar-test")
async def inyectar_datos_test(request: Request):
    """Endpoint para inyectar datos de test manualmente (DEBUG)."""
    try:
        data = await request.json()
        registrar_ingesta_ecowitt(data)
        return {"status": "SUCCESS", "mensaje": "Datos de test inyectados al diagnóstico"}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}
