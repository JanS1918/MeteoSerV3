"""
API Routers - Endpoints del sistema MeteoSerV3
"""
from .sensors import router as sensors_router
from .admin import router as admin_router
from .assistant import router as assistant_router
from .voice import router as voice_router
from .config import router as config_router
from .systems import router as systems_router

__all__ = [
    'sensors_router',
    'admin_router',
    'assistant_router',
    'voice_router',
    'config_router',
    'systems_router'
]
