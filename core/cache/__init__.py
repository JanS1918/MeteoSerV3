"""core.cache - Sistema de caché distribuida"""
from .cache_distribuida import obtener_cache, iniciar_cache, CacheDistribuida, CacheEnMemoria, cachear

__all__ = ['obtener_cache', 'iniciar_cache', 'CacheDistribuida', 'CacheEnMemoria', 'cachear']
