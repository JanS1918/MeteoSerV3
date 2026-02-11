"""
API REST - AUDITORÍAS Y ALERTAS v1.0
═════════════════════════════════════════════════════════════════════════════

Proporciona endpoints REST para acceso a:
- Auditorías post-ciclo del bus
- Alertas predictivas activas y histórico
- Validaciones WH31
- Estadísticas y tendencias

Endpoints:
  GET /api/v1/auditorias/actual - Última auditoría
  GET /api/v1/auditorias/historico - Histórico de auditorías
  GET /api/v1/alertas/activas - Alertas en vivo
  GET /api/v1/alertas/historico - Histórico de alertas
  GET /api/v1/alertas/estadisticas - Estadísticas
  GET /api/v1/validaciones/wh31 - Última validación WH31
  GET /api/v1/validaciones/wh31/historico - Histórico WH31

Fecha: 11 de febrero de 2026
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Router para los endpoints
router = APIRouter(
    prefix="/api/v1",
    tags=["auditorias-alertas"],
    responses={404: {"description": "No encontrado"}}
)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS AUDITORÍAS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/auditorias/actual")
async def obtener_auditoria_actual():
    """Obtiene la última auditoría post-ciclo."""
    try:
        from core.system.auditor_bus import auditar_publicacion_bus
        
        # Simular: en producción, obtendría del bus expandido
        constantes_simuladas = {}  # Obtendría del bus real
        
        return {
            "status": "success",
            "data": {
                "estado": "PENDING",
                "mensaje": "Esperando próximo ciclo del bus",
                "ultima_actualizacion": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error en auditoría: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/auditorias/historico")
async def obtener_historico_auditorias(limites: int = Query(10, ge=1, le=100)):
    """Obtiene histórico de auditorías (últimas N)."""
    try:
        from pathlib import Path
        import json
        
        archivo_historico = Path("data/auditorias/historico.json")
        
        if not archivo_historico.exists():
            return {
                "status": "success",
                "data": [],
                "total": 0
            }
        
        with open(archivo_historico, 'r') as f:
            datos = json.load(f)
            auditorias = datos.get('auditorias', [])[-limites:]
        
        return {
            "status": "success",
            "data": auditorias,
            "total": len(auditorias)
        }
    except Exception as e:
        logger.error(f"Error obteniendo histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS ALERTAS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/alertas/activas")
async def obtener_alertas_activas():
    """Obtiene alertas predictivas activas en vivo."""
    try:
        from core.system.servicio_alertas_vivo import obtener_servicio
        
        servicio = obtener_servicio()
        estado = servicio.obtener_alertas_activas()
        
        return {
            "status": "success",
            "data": {
                "total_activas": estado['total'],
                "criticas": estado['criticas'],
                "alertas": [
                    {
                        "dominio": d,
                        "nivel": a.get('nivel'),
                        "magnitud": a.get('impacto_magnitud'),
                        "recomendacion": a.get('recomendacion')
                    }
                    for d, a in estado['alertas'].items()
                ],
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alertas/historico")
async def obtener_historico_alertas(
    limites: int = Query(100, ge=1, le=1000),
    nivel: Optional[str] = Query(None, regex="^(CRÍTICO|SEVERO|MODERADO|LEVE)$")
):
    """Obtiene histórico de alertas (últimas N, opcionalmente filtrado por nivel)."""
    try:
        from core.system.servicio_alertas_vivo import obtener_servicio
        
        servicio = obtener_servicio()
        historico = servicio.obtener_historico(limites=limites, filtro_nivel=nivel)
        
        return {
            "status": "success",
            "data": historico,
            "total": len(historico),
            "filtro_nivel": nivel
        }
    except Exception as e:
        logger.error(f"Error obteniendo histórico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alertas/estadisticas")
async def obtener_estadisticas_alertas():
    """Obtiene estadísticas globales de alertas."""
    try:
        from core.system.servicio_alertas_vivo import obtener_servicio
        
        servicio = obtener_servicio()
        stats = servicio.obtener_estadisticas()
        
        return {
            "status": "success",
            "data": {
                "total_generadas": stats['total_generadas'],
                "total_resueltas": stats['total_resueltas'],
                "criticas_activas": stats['criticas_activas'],
                "historico_total": stats['historico_total'],
                "ultima_actualizacion": stats['ultima_actualizacion'],
                "alertas_por_dominio": stats['alertas_activas_por_dominio']
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS VALIDACIONES WH31
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/validaciones/wh31")
async def obtener_validacion_wh31_actual():
    """Obtiene la última validación WH31 vs WH65."""
    try:
        from core.scheduler.scheduler_wh31_validator import obtener_scheduler
        import json
        
        scheduler = obtener_scheduler()
        resultado = scheduler.obtener_resultado_actual()
        
        if not resultado:
            return {
                "status": "success",
                "data": {
                    "mensaje": "Sin validación ejecutada aún",
                    "proxima_ejecucion": scheduler._proxima_ejecucion()
                }
            }
        
        stats = resultado.get('estadisticas', {})
        
        return {
            "status": "success",
            "data": {
                "timestamp_ejecucion": resultado.get('timestamp_ejecucion'),
                "total_registros": stats.get('total_registros'),
                "periodo_dias": stats.get('periodo_dias'),
                "diferencial_promedio": stats.get('diferencial_wh31_vs_wh65', {}).get('promedio'),
                "error_sistematico": stats.get('error_sistematico_wh31', {}).get('promedio'),
                "conclusion": resultado.get('conclusion'),
                "recomendaciones": resultado.get('recomendaciones')
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo validación WH31: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validaciones/wh31/historico")
async def obtener_historico_wh31(limites: int = Query(5, ge=1, le=12)):
    """Obtiene histórico de validaciones WH31 (últimas N)."""
    try:
        from core.scheduler.scheduler_wh31_validator import obtener_scheduler
        
        scheduler = obtener_scheduler()
        historico = scheduler.obtener_historico(limites=limites)
        
        return {
            "status": "success",
            "data": [
                {
                    "timestamp": r.get('timestamp_ejecucion'),
                    "total_registros": r.get('estadisticas', {}).get('total_registros'),
                    "diferencial_promedio": r.get('estadisticas', {}).get('diferencial_wh31_vs_wh65', {}).get('promedio'),
                    "error_sistematico": r.get('estadisticas', {}).get('error_sistematico_wh31', {}).get('promedio')
                }
                for r in historico
            ],
            "total": len(historico)
        }
    except Exception as e:
        logger.error(f"Error obteniendo histórico WH31: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validaciones/wh31/tendencias")
async def obtener_tendencias_wh31():
    """Obtiene análisis de tendencias en validaciones WH31."""
    try:
        from core.scheduler.scheduler_wh31_validator import obtener_scheduler
        
        scheduler = obtener_scheduler()
        tendencias = scheduler.analizar_tendencias()
        
        return {
            "status": "success",
            "data": {
                "promedio_total": tendencias.get('promedio_total'),
                "maximo": tendencias.get('maximo'),
                "minimo": tendencias.get('minimo'),
                "cambio_reciente": tendencias.get('cambio_reciente'),
                "alerta": tendencias.get('alerta'),
                "valores_historicos": tendencias.get('valores')
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo tendencias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS SALUD GENERAL
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/salud/sistema")
async def obtener_salud_sistema():
    """Obtiene estado general del sistema de auditorías, alertas y validaciones."""
    try:
        from core.system.servicio_alertas_vivo import obtener_servicio as obtener_alertas
        from core.scheduler.scheduler_wh31_validator import obtener_scheduler as obtener_wh31
        
        alertas = obtener_alertas().obtener_estadisticas()
        wh31 = obtener_wh31().obtener_resultado_actual()
        
        return {
            "status": "success",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "servicios": {
                    "alertas_vivo": {
                        "estado": "ACTIVO",
                        "alertas_criticas": alertas.get('criticas_activas', 0),
                        "alertas_totales": alertas.get('total_generadas', 0)
                    },
                    "validador_wh31": {
                        "estado": "ACTIVO",
                        "ultima_validacion": wh31.get('timestamp_ejecucion') if wh31 else "NUNCA"
                    }
                },
                "salud": "OK" if alertas.get('criticas_activas', 0) == 0 else "WARNING_ALERTAS_CRITICAS"
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo salud del sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/dashboard/alertas", response_class=HTMLResponse)
async def obtener_dashboard_alertas():
    """Obtiene dashboard HTML con alertas en vivo integrado."""
    try:
        from core.system.dashboard_alertas_integrado import generar_dashboard_desde_servicios
        
        html = await generar_dashboard_desde_servicios()
        return html
        
    except Exception as e:
        logger.error(f"Error generando dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# ANÁLISIS HISTÓRICO (STEP 8)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/analisis/tendencias-alertas")
async def obtener_tendencias_alertas(dias: int = Query(7, ge=1, le=365)):
    """Obtiene tendencias de alertas para período especificado."""
    try:
        from core.analytics.analisis_historico import obtener_analizador
        
        analizador = obtener_analizador()
        tendencia = analizador.analizar_tendencia_alertas(dias=dias)
        
        return {
            "status": "success",
            "data": tendencia
        }
    except Exception as e:
        logger.error(f"Error obteniendo tendencias alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analisis/tendencias-wh31")
async def obtener_tendencias_wh31():
    """Obtiene tendencias de WH31 (drift progresivo)."""
    try:
        from core.analytics.analisis_historico import obtener_analizador
        
        analizador = obtener_analizador()
        tendencia = analizador.analizar_tendencia_wh31()
        
        return {
            "status": "success",
            "data": tendencia
        }
    except Exception as e:
        logger.error(f"Error obteniendo tendencias WH31: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analisis/reportes/semanal")
async def obtener_reporte_semanal():
    """Obtiene reporte semanal completo."""
    try:
        from core.analytics.analisis_historico import obtener_analizador
        
        analizador = obtener_analizador()
        reporte = analizador.generar_reporte_semanal()
        
        return {
            "status": "success",
            "data": reporte
        }
    except Exception as e:
        logger.error(f"Error generando reporte semanal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analisis/reportes/mensual")
async def obtener_reporte_mensual():
    """Obtiene reporte mensual completo."""
    try:
        from core.analytics.analisis_historico import obtener_analizador
        
        analizador = obtener_analizador()
        reporte = analizador.generar_reporte_mensual()
        
        return {
            "status": "success",
            "data": reporte
        }
    except Exception as e:
        logger.error(f"Error generando reporte mensual: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# SALUD DEL SISTEMA (STEP 9)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/salud/puntuacion")
async def obtener_puntuacion_salud():
    """Obtiene puntuación integral de salud (0-100)."""
    try:
        from core.analytics.calculador_salud import obtener_calculador
        
        calculador = obtener_calculador()
        salud = calculador.calcular_puntuacion_total()
        
        return {
            "status": "success",
            "data": salud
        }
    except Exception as e:
        logger.error(f"Error obteniendo puntuación salud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/salud/tendencia-7dias")
async def obtener_tendencia_salud():
    """Obtiene tendencia de puntuación últimos 7 días."""
    try:
        from core.analytics.calculador_salud import obtener_calculador
        
        calculador = obtener_calculador()
        tendencia = calculador.obtener_tendencia_7dias()
        
        return {
            "status": "success",
            "data": tendencia
        }
    except Exception as e:
        logger.error(f"Error obteniendo tendencia salud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/salud/resumen")
async def obtener_resumen_salud():
    """Obtiene resumen completo de salud del sistema."""
    try:
        from core.analytics.calculador_salud import obtener_calculador
        
        calculador = obtener_calculador()
        resumen = calculador.obtener_resumen_salud()
        
        return {
            "status": "success",
            "data": resumen
        }
    except Exception as e:
        logger.error(f"Error obteniendo resumen salud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# GESTIÓN DE TENANTS (STEP 10)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/tenants")
async def listar_tenants():
    """Obtiene lista de todos los tenants."""
    try:
        from core.analytics.gestor_tenants import obtener_gestor_tenants
        
        gestor = obtener_gestor_tenants()
        tenants = [
            {
                'tenant_id': t.tenant_id,
                'nombre': t.nombre,
                'estado': t.estado.value,
                'descripcion': t.descripcion
            }
            for t in gestor.obtener_todos_tenants()
        ]
        
        return {
            "status": "success",
            "data": {"tenants": tenants, "total": len(tenants)}
        }
    except Exception as e:
        logger.error(f"Error listando tenants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}")
async def obtener_tenant(tenant_id: str):
    """Obtiene información de un tenant específico."""
    try:
        from core.analytics.gestor_tenants import obtener_gestor_tenants
        
        gestor = obtener_gestor_tenants()
        tenant = gestor.obtener_tenant(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
        return {
            "status": "success",
            "data": {
                'tenant_id': tenant.tenant_id,
                'nombre': tenant.nombre,
                'estado': tenant.estado.value,
                'descripcion': tenant.descripcion,
                'dominio_primario': tenant.dominio_primario,
                'thresholds': {
                    'critico_wh31': tenant.umbral_critico_wh31,
                    'severo_wh31': tenant.umbral_severo_wh31,
                    'critico_cobertura': tenant.umbral_critico_cobertura
                }
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/alertas")
async def obtener_alertas_tenant(tenant_id: str, limites: int = Query(100, ge=1, le=1000)):
    """Obtiene alertas aisladas de un tenant específico."""
    try:
        from core.analytics.gestor_tenants import obtener_gestor_tenants
        
        gestor = obtener_gestor_tenants()
        alertas = gestor.obtener_alertas_tenant(tenant_id, limites=limites)
        
        return {
            "status": "success",
            "data": {
                "tenant_id": tenant_id,
                "alertas": alertas,
                "total": len(alertas)
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo alertas tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tenants/{tenant_id}/estadisticas")
async def obtener_estadisticas_tenant(tenant_id: str):
    """Obtiene estadísticas agregadas de un tenant."""
    try:
        from core.analytics.gestor_tenants import obtener_gestor_tenants
        
        gestor = obtener_gestor_tenants()
        stats = gestor.obtener_estadisticas_tenant(tenant_id)
        
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("API REST - Auditorías y Alertas v1.0")
    print("Endpoints disponibles:")
    print("  GET /api/v1/auditorias/actual")
    print("  GET /api/v1/auditorias/historico")
    print("  GET /api/v1/alertas/activas")
    print("  GET /api/v1/alertas/historico")
    print("  GET /api/v1/alertas/estadisticas")
    print("  GET /api/v1/validaciones/wh31")
    print("  GET /api/v1/validaciones/wh31/historico")
    print("  GET /api/v1/validaciones/wh31/tendencias")
    print("  GET /api/v1/salud/sistema")
