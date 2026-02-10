"""
Inicializar Sistema de IA en MeteoSer
======================================

Este script proporciona instrucciones y código para integrar el sistema de IA
en main_asgi.py o main.py.
"""

# ===== PASO 1: Añadir imports en main_asgi.py =====
"""
from ai_controller import initialize_ai_controller, get_ai_controller
from ai_endpoints import router as ai_router
"""

# ===== PASO 2: Inicializar AI Controller al arrancar FastAPI =====
"""
@app.on_event("startup")
async def startup_ai():
    '''Inicializa el sistema de IA'''
    global ai_controller
    
    # Obtener instancia del Bus (ajustar según tu código)
    from core.system.bus import get_bus_instance
    bus = get_bus_instance()
    
    # Inicializar AI Controller
    ai_controller = initialize_ai_controller(
        bus=bus,
        config_dir="data",
        contracts_dir="contracts"
    )
    
    # Inicializar subsistemas
    await ai_controller.initialize()
    
    logger.info("🤖 Sistema de IA inicializado correctamente")
"""

# ===== PASO 3: Registrar endpoints de IA =====
"""
# Registrar router de IA
app.include_router(ai_router)
"""

# ===== PASO 4: Apagar sistema de IA al cerrar =====
"""
@app.on_event("shutdown")
async def shutdown_ai():
    '''Apaga el sistema de IA'''
    ai_controller = get_ai_controller()
    
    if ai_controller:
        await ai_controller.shutdown()
    
    logger.info("🛑 Sistema de IA apagado")
"""

# ===== EJEMPLO COMPLETO DE INTEGRACIÓN =====

EXAMPLE_MAIN_ASGI_INTEGRATION = """
# main_asgi.py (EJEMPLO DE INTEGRACIÓN)

from fastapi import FastAPI
import logging

# Imports existentes...
from core.system.bus import get_bus_instance

# NUEVOS IMPORTS PARA IA
from ai_controller import initialize_ai_controller, get_ai_controller
from ai_endpoints import router as ai_router

logger = logging.getLogger(__name__)

app = FastAPI(title="MeteoSer API")

# Variable global para AI Controller
ai_controller = None


@app.on_event("startup")
async def startup_event():
    '''Inicialización al arrancar'''
    global ai_controller
    
    logger.info("🚀 Iniciando MeteoSer...")
    
    # Inicialización existente del sistema...
    # (tu código actual aquí)
    
    # === NUEVO: Inicializar Sistema de IA ===
    try:
        bus = get_bus_instance()  # Ajustar según tu implementación
        
        ai_controller = initialize_ai_controller(
            bus=bus,
            config_dir="data",
            contracts_dir="contracts"
        )
        
        await ai_controller.initialize()
        
        logger.info("🤖 Sistema de IA inicializado correctamente")
        
        # Programar tareas periódicas opcionales
        ai_controller.schedule_contract_scan()
        ai_controller.schedule_autoheal_scan()
    
    except Exception as e:
        logger.error(f"❌ Error inicializando IA: {e}")
        # No fallar si IA no se inicializa
    
    logger.info("✅ MeteoSer completamente iniciado")


@app.on_event("shutdown")
async def shutdown_event():
    '''Apagar sistema al cerrar'''
    logger.info("🛑 Apagando MeteoSer...")
    
    # === NUEVO: Apagar Sistema de IA ===
    ai_controller = get_ai_controller()
    
    if ai_controller:
        await ai_controller.shutdown()
        logger.info("✅ Sistema de IA apagado")
    
    # Apagar otros componentes...
    logger.info("✅ MeteoSer apagado")


# === NUEVO: Registrar endpoints de IA ===
app.include_router(ai_router)

# Tus otros endpoints...

@app.get("/")
async def root():
    return {"status": "ok", "ai_enabled": ai_controller is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
"""


# ===== ENDPOINTS DISPONIBLES =====

AVAILABLE_ENDPOINTS = """
Una vez integrado, tendrás estos endpoints:

GET  /ai/status          - Estado de todos los subsistemas de IA
POST /ai/dialog          - Diálogo conversacional con IA
POST /ai/explain         - Explicar conceptos de MeteoSer
GET  /ai/contracts       - Listar contratos de componentes
GET  /ai/contracts/{id}  - Obtener contrato específico
POST /ai/generate        - Generar código con IA
POST /ai/autoheal/scan   - Disparar escaneo de auto-curación
GET  /ai/metrics         - Métricas del orchestrator
GET  /ai/history         - Historial de cambios

Ejemplos de uso:

# Diálogo con IA
curl -X POST http://localhost:8080/ai/dialog \
  -H "Content-Type: application/json" \\
  -d '{"message": "¿Cuál es la temperatura actual?"}'

# Explicar concepto
curl -X POST http://localhost:8080/ai/explain \
  -H "Content-Type: application/json" \
  -d '{"query": "qué es el UTCI"}'

# Estado del sistema de IA
curl http://localhost:8080/ai/status

# Listar contratos
curl http://localhost:8080/ai/contracts

# Generar código
curl -X POST http://localhost:8080/ai/generate \
  -H "Content-Type: application/json" \\
  -d '{"prompt": "crear función para leer sensor BME280"}'
"""


if __name__ == "__main__":
    print("=" * 70)
    print("INSTRUCCIONES DE INTEGRACIÓN DEL SISTEMA DE IA")
    print("=" * 70)
    print()
    print(EXAMPLE_MAIN_ASGI_INTEGRATION)
    print()
    print("=" * 70)
    print(AVAILABLE_ENDPOINTS)
    print("=" * 70)
    print()
    print("✅ Sistema de IA ya integrado en main_asgi.py")
    print("✅ Configura OPENROUTER_API_KEY en variables de entorno")
    print("✅ Reinicia MeteoSer: python arrancar_meteoser.py")
    print("✅ Accede a http://localhost:8080/docs para ver todos los endpoints")
    print("✅ Prueba: http://localhost:8080/ai/status")
    print()
