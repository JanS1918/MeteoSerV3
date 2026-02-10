"""
Router de configuración
"""
from fastapi import APIRouter, Body
import logging
import json
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/config", tags=["config"])


@router.get("/layout")
async def get_layout():
    """Obtiene configuración de layout"""
    try:
        layout_file = "data/dashboard_layout.json"
        if os.path.exists(layout_file):
            with open(layout_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"panels": []}
    except Exception as e:
        logger.error(f"Error cargando layout: {e}")
        return {"error": str(e)}


@router.post("/layout")
async def save_layout(layout_data: dict = Body(...)):
    """Guarda configuración de layout"""
    try:
        layout_file = "data/dashboard_layout.json"
        with open(layout_file, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2, ensure_ascii=False)
        return {"status": "OK"}
    except Exception as e:
        logger.error(f"Error guardando layout: {e}")
        return {"error": str(e)}


@router.get("/panels")
async def get_panels():
    """Obtiene configuración de paneles"""
    try:
        panels_file = "data/dashboard_panels.json"
        if os.path.exists(panels_file):
            with open(panels_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"panels": {}}
    except Exception as e:
        logger.error(f"Error cargando paneles: {e}")
        return {"error": str(e)}


@router.post("/panels")
async def save_panels(panels_data: dict = Body(...)):
    """Guarda configuración de paneles"""
    try:
        panels_file = "data/dashboard_panels.json"
        with open(panels_file, 'w', encoding='utf-8') as f:
            json.dump(panels_data, f, indent=2, ensure_ascii=False)
        return {"status": "OK"}
    except Exception as e:
        logger.error(f"Error guardando paneles: {e}")
        return {"error": str(e)}
