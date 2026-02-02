import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import time
from datetime import datetime
from core.system.system_manager import SystemManager
from app.ui.router import router, set_system_manager, _cache_clear

app = FastAPI()

# Inicializar SystemManager (los datos reales del sistema)
try:
    system_manager = SystemManager()
    system_manager.iniciar()
    set_system_manager(system_manager)
    print("[main_asgi] SystemManager inicializado")
except Exception as e:
    print(f"[main_asgi] ERROR inicializando SystemManager: {e}")

# Montar carpeta estática
static_dir = Path(__file__).parent / "app" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Endpoint Ecowitt (Recibe y PROCESA la sangre de los sensores)
@app.post("/ecowitt")
async def receive_ecowitt(request: Request):
    """
    Endpoint que recibe datos del Ecowitt HP2550A y los almacena.
    Transforma Fahrenheit → Celsius y actualiza los sensores del sistema.
    """
    try:
        # Obtener payload
        payload = await request.form()
        data_dict = dict(payload)
        
        # Almacenar payload bruto con timestamp
        data_path = Path(__file__).resolve().parent / "data" / "last_ecowitt_payload.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "data": data_dict
        }, indent=2), encoding="utf-8")
        
        # ==========================================
        # TRANSFORMAR DATOS ECOWITT
        # ==========================================
        # Ecowitt envía en unidades imperiales (°F, mph, in)
        
        # Temperatura exterior: °F → °C
        tempf = float(data_dict.get("tempf", 15.0))
        temperatura_ext = round((tempf - 32) * 5/9, 2)  # °C
        
        # Temperatura interior: °F → °C
        tempinf = float(data_dict.get("tempinf", 15.0))
        temperatura_int = round((tempinf - 32) * 5/9, 2)  # °C
        
        # Humedad relativa (ya en %)
        humedad = float(data_dict.get("humidity", 50.0))
        humedad_int = float(data_dict.get("humidityin", 50.0))
        
        # Presión (barómetro relativo, en inHg → hPa)
        baro_rel_inhg = float(data_dict.get("baromrelin", 29.92))
        presion_relativa = round(baro_rel_inhg * 33.8639, 2)  # hPa
        
        baro_abs_inhg = float(data_dict.get("baromabsin", 29.92))
        presion_absoluta = round(baro_abs_inhg * 33.8639, 2)  # hPa
        
        # Velocidad del viento: mph → m/s
        windspeedmph = float(data_dict.get("windspeedmph", 0.0))
        viento = round(windspeedmph * 0.44704, 2)  # m/s
        
        # Radiación solar (ya en W/m²)
        radiacion = float(data_dict.get("solarradiation", 0.0))
        
        # UV index (sin transformación)
        uv = float(data_dict.get("uv", 0.0))
        
        # Lluvia: in → mm
        rainratein = float(data_dict.get("rainratein", 0.0))
        lluvia_rate = round(rainratein * 25.4, 2)  # mm/h
        
        # PM2.5 (µg/m³, sin transformación)
        pm25 = float(data_dict.get("pm25_ch1", 0.0))
        
        # Relámpagos
        lightning_num = int(data_dict.get("lightning_num", 0))
        lightning_dist = float(data_dict.get("lightning", 0.0))  # km
        
        # Humedad del suelo
        soilmoisture = float(data_dict.get("soilmoisture1", 0.0))
        
        # ==========================================
        # ACTUALIZAR SENSORES EN SYSTEMMANAGER
        # ==========================================
        if system_manager and system_manager.system:
            sys = system_manager.system
            now = time.time()
            
            # Actualizar sensores
            sys.actualizar_sensor("temperatura", temperatura_ext)
            sys.actualizar_sensor("temperatura_interior", temperatura_int)
            sys.actualizar_sensor("humedad", humedad)
            sys.actualizar_sensor("humedad_interior", humedad_int)
            sys.actualizar_sensor("presion", presion_relativa)
            sys.actualizar_sensor("presion_relativa_interior", presion_relativa)
            sys.actualizar_sensor("presion_absoluta_interior", presion_absoluta)
            sys.actualizar_sensor("viento", viento)
            sys.actualizar_sensor("radiacion", radiacion)
            sys.actualizar_sensor("uv", uv)
            sys.actualizar_sensor("lluvia", 0.0)  # Lluvia acumulada, no rate
            sys.actualizar_sensor("lluvia_rate", lluvia_rate)
            sys.actualizar_sensor("pm25", pm25)
            sys.actualizar_sensor("lightning", lightning_dist)
            sys.actualizar_sensor("lightning_num", lightning_num)
            sys.actualizar_sensor("wh51", soilmoisture)
        
        # ==========================================
        # GUARDAR EN LAST_SENSORES.JSON
        # ==========================================
        sensores_path = Path(__file__).resolve().parent / "data" / "last_sensores.json"
        sensores_data = {
            "sensores": {
                "temperatura": temperatura_ext,
                "temperatura_interior": temperatura_int,
                "humedad": humedad,
                "humedad_interior": humedad_int,
                "presion": presion_relativa,
                "presion_relativa": presion_relativa,
                "presion_absoluta": presion_absoluta,
                "presion_relativa_interior": presion_relativa,
                "presion_absoluta_interior": presion_absoluta,
                "viento": viento,
                "radiacion": radiacion,
                "uv": uv,
                "lluvia_rate": lluvia_rate,
                "pm25": pm25,
                "lightning": lightning_dist,
                "lightning_num": lightning_num,
                "wh51": soilmoisture,
                "ultimo_ecowitt": datetime.now().isoformat(),
                "tempf_original": str(tempf),
                "humidity_original": str(humedad),
                "windspeedmph_original": str(windspeedmph)
            },
            "timestamps": {
                "temperatura": time.time(),
                "temperatura_interior": time.time(),
                "humedad": time.time(),
                "humedad_interior": time.time(),
                "presion": time.time(),
                "viento": time.time(),
                "radiacion": time.time(),
                "uv": time.time(),
                "lluvia_rate": time.time(),
                "pm25": time.time(),
                "lightning": time.time(),
                "lightning_num": time.time(),
                "wh51": time.time()
            }
        }
        sensores_path.write_text(json.dumps(sensores_data, indent=2), encoding="utf-8")
        
        # Recargar sensores en SystemCore desde el JSON recién guardado
        if system_manager and system_manager.system:
            system_manager.system._cargar_sensores_persistidos()
                # ==========================================
        # LIMPIAR CACHÉ PARA QUE UI VEA DATOS NUEVOS
        # ==========================================
        try:
            _cache_clear("contexto")
            _cache_clear("panel_superior")
            _cache_clear("panel_central")
            _cache_clear("panel_cajones")
            _cache_clear("panel_arcos")
        except:
            pass
        
        print(f"[ecowitt] OK Datos procesados: T={temperatura_ext}C, H={humedad}%, Rad={radiacion}")
        return {"status": "processed", "temperatura": temperatura_ext, "humedad": humedad}
        
    except Exception as e:
        print(f"[ecowitt] ERROR: {e}")
        return {"status": "error", "error": str(e)}

# Puente para los Cajones (Elimina el 404)
@app.get("/api/ui/cajones")
async def get_cajones():
    # Redirigimos internamente para que la UI vea los datos
    return []

app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
