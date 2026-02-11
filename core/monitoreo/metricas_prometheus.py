"""
═══════════════════════════════════════════════════════════════════════════════
STEP 17: MONITORING & PROMETHEUS METRICS
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Exportar métricas para Prometheus
  - Monitoreo con Grafana
  - KPIs del sistema

Fecha: 2026-02-11
"""

import time
from typing import Dict, Callable
from prometheus_client import Counter, Gauge, Histogram, Summary

# ═══════════════════════════════════════════════════════════════════════════
# MÉTRICAS
# ═══════════════════════════════════════════════════════════════════════════

# Contadores
alertas_generadas = Counter(
    'alertas_generadas_total',
    'Total de alertas generadas',
    ['nivel', 'dominio']
)

alertas_resueltas = Counter(
    'alertas_resueltas_total',
    'Total de alertas resueltas',
    ['dominio']
)

requests_api = Counter(
    'api_requests_total',
    'Total de requests a la API',
    ['metodo', 'endpoint', 'codigo_estado']
)

webhooks_entregados = Counter(
    'webhooks_entregados_total',
    'Total de webhooks entregados',
    ['webhook_id', 'estado']
)

# Gauges
alertas_activas = Gauge(
    'alertas_activas',
    'Alertas activas en el sistema'
)

puntuacion_salud = Gauge(
    'puntuacion_salud_sistema',
    'Puntuación de salud 0-100'
)

servicios_disponibles = Gauge(
    'servicios_disponibles',
    'Servicios disponibles',
    ['servicio']
)

# Histogramas
latencia_api = Histogram(
    'latencia_api_segundos',
    'Latencia de API en segundos',
    ['metodo', 'endpoint']
)

latencia_bd = Histogram(
    'latencia_bd_segundos',
    'Latencia de base de datos'
)

# Summary
tiempo_procesamiento_alerta = Summary(
    'tiempo_procesamiento_alerta',
    'Tiempo de procesamiento de alerta'
)


def decorador_metrica_api(metodo: str, endpoint: str):
    """Decorador para medir latencia de API."""
    def decorador(func):
        async def wrapper(*args, **kwargs):
            inicio = time.time()
            try:
                resultado = await func(*args, **kwargs)
                codigo = 200
                return resultado
            except Exception as e:
                codigo = 500
                raise
            finally:
                duracion = time.time() - inicio
                latencia_api.labels(
                    metodo=metodo,
                    endpoint=endpoint
                ).observe(duracion)
        return wrapper
    return decorador
