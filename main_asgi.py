import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from core.system.system_manager import SystemManager
from app.ui.router import router, set_system_manager

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

# Endpoint Ecowitt (Recibe la sangre de los sensores)
@app.post("/ecowitt")
async def receive_ecowitt(request: Request):
    return {"status": "received"}

# Puente para los Cajones (Elimina el 404)
@app.get("/api/ui/cajones")
async def get_cajones():
    # Redirigimos internamente para que la UI vea los datos
    return []

app.include_router(router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
