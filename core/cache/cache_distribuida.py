"""
═══════════════════════════════════════════════════════════════════════════════
STEP 15: CACHÉ DISTRIBUIDA (Redis con fallback en-memoria)
═══════════════════════════════════════════════════════════════════════════════

Propósito:
  - Cachear resultados de operaciones costosas
  - Redis para deployments distribuidos
  - Fallback a en-memoria si Redis no disponible
  - TTL y evicción automática

Fecha de creación: 2026-02-11
Versión: 1.0
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable
from collections import OrderedDict
from pathlib import Path

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CACHÉ EN MEMORIA (FALLBACK)
# ═══════════════════════════════════════════════════════════════════════════

class CacheEnMemoria:
    """Caché en memoria con LRU y TTL."""
    
    def __init__(self, max_items: int = 1000):
        self.cache: OrderedDict = OrderedDict()
        self.metadatos: Dict[str, Dict] = {}
        self.max_items = max_items
        self.estadisticas = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _limpiar_expirados(self):
        """Elimina items expirados."""
        ahora = datetime.now()
        claves_expiradas = []
        
        for clave, metadata in self.metadatos.items():
            if metadata.get('expira_en'):
                if datetime.fromisoformat(metadata['expira_en']) < ahora:
                    claves_expiradas.append(clave)
        
        for clave in claves_expiradas:
            del self.cache[clave]
            del self.metadatos[clave]
    
    def obtener(self, clave: str) -> Optional[Any]:
        """Obtiene valor del caché."""
        self._limpiar_expirados()
        
        if clave in self.cache:
            self.estadisticas['hits'] += 1
            self.cache.move_to_end(clave)  # LRU
            return self.cache[clave]
        
        self.estadisticas['misses'] += 1
        return None
    
    def establecer(self, clave: str, valor: Any, 
                  ttl_segundos: int = 3600):
        """Establece valor en caché."""
        
        # Evición LRU si está lleno
        while len(self.cache) >= self.max_items:
            clave_antigua = next(iter(self.cache))
            del self.cache[clave_antigua]
            del self.metadatos[clave_antigua]
            self.estadisticas['evictions'] += 1
        
        # Almacenar
        self.cache[clave] = valor
        self.metadatos[clave] = {
            'timestamp_creacion': datetime.now().isoformat(),
            'expira_en': (datetime.now() + timedelta(seconds=ttl_segundos)).isoformat() if ttl_segundos > 0 else None,
            'tamano_bytes': len(json.dumps(valor, default=str))
        }
        
        self.cache.move_to_end(clave)
    
    def invalidar(self, clave: str):
        """Invalida clave."""
        if clave in self.cache:
            del self.cache[clave]
            del self.metadatos[clave]
    
    def invalidar_patron(self, patron: str):
        """Invalida claves que coincidan con patrón."""
        claves_coinciden = [
            c for c in self.cache.keys()
            if patron in c
        ]
        
        for clave in claves_coinciden:
            self.invalidar(clave)
    
    def limpiar_todo(self):
        """Limpia todo el caché."""
        self.cache.clear()
        self.metadatos.clear()
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de caché."""
        total = self.estadisticas['hits'] + self.estadisticas['misses']
        
        return {
            'items_en_cache': len(self.cache),
            'max_items': self.max_items,
            'hits': self.estadisticas['hits'],
            'misses': self.estadisticas['misses'],
            'tasa_acierto': (
                self.estadisticas['hits'] / total * 100 if total > 0 else 0
            ),
            'evictions': self.estadisticas['evictions']
        }


# ═══════════════════════════════════════════════════════════════════════════
# CACHÉ DISTRIBUIDA CON FALLBACK
# ═══════════════════════════════════════════════════════════════════════════

class CacheDistribuida:
    """Caché con soporte Redis y fallback en-memoria."""
    
    def __init__(self, usar_redis: bool = True):
        self.cache_memoria = CacheEnMemoria()
        self.usar_redis = usar_redis
        self.cliente_redis = None
        self.conectado_redis = False
        
        if usar_redis:
            self._intentar_conectar_redis()
    
    def _intentar_conectar_redis(self):
        """Intenta conectarse a Redis."""
        try:
            import redis
            import os
            
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            
            self.cliente_redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test de conexión
            self.cliente_redis.ping()
            self.conectado_redis = True
            logger.info("[CACHE] ✓ Redis conectado")
            
        except Exception as e:
            logger.warning(f"[CACHE] Redis no disponible: {e}")
            self.conectado_redis = False
            self.cliente_redis = None
    
    async def obtener(self, clave: str) -> Optional[Any]:
        """Obtiene valor con fallback."""
        
        # Intentar Redis primero
        if self.conectado_redis and self.cliente_redis:
            try:
                valor = self.cliente_redis.get(clave)
                if valor:
                    return json.loads(valor)
            except Exception as e:
                logger.warning(f"Error Redis: {e}")
        
        # Fallback a memoria
        return self.cache_memoria.obtener(clave)
    
    async def establecer(self, clave: str, valor: Any, 
                        ttl_segundos: int = 3600):
        """Establece valor con ambos cachés."""
        
        # Guardar en Redis
        if self.conectado_redis and self.cliente_redis:
            try:
                self.cliente_redis.setex(
                    clave,
                    ttl_segundos,
                    json.dumps(valor, default=str)
                )
            except Exception as e:
                logger.warning(f"Error Redis: {e}")
        
        # Guardar en memoria
        self.cache_memoria.establecer(clave, valor, ttl_segundos)
    
    async def invalidar(self, clave: str):
        """Invalida en ambos cachés."""
        
        # Redis
        if self.conectado_redis and self.cliente_redis:
            try:
                self.cliente_redis.delete(clave)
            except Exception:
                pass
        
        # Memoria
        self.cache_memoria.invalidar(clave)
    
    async def invalidar_patron(self, patron: str):
        """Invalida patrón en ambos cachés."""
        
        # Redis
        if self.conectado_redis and self.cliente_redis:
            try:
                claves = self.cliente_redis.keys(f"*{patron}*")
                if claves:
                    self.cliente_redis.delete(*claves)
            except Exception:
                pass
        
        # Memoria
        self.cache_memoria.invalidar_patron(patron)
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de caché."""
        stats = self.cache_memoria.obtener_estadisticas()
        stats['redis_conectado'] = self.conectado_redis
        
        return stats


# ═══════════════════════════════════════════════════════════════════════════
# DECORADOR PARA CACHEAR FUNCIONES
# ═══════════════════════════════════════════════════════════════════════════

_cache_global = None


def obtener_cache() -> CacheDistribuida:
    """Obtiene instancia de caché global."""
    global _cache_global
    if _cache_global is None:
        _cache_global = CacheDistribuida()
    return _cache_global


def cachear(ttl_segundos: int = 3600, patron_invalidacion: str = None):
    """Decorador para cachear resultados de funciones."""
    
    def decorador(func):
        async def wrapper(*args, **kwargs):
            # Generar clave
            args_str = str(args) + str(kwargs)
            clave = f"{func.__name__}:{hash(args_str)}"
            
            cache = obtener_cache()
            
            # Intentar obtener del caché
            resultado = await cache.obtener(clave)
            if resultado is not None:
                logger.debug(f"Cache hit: {clave}")
                return resultado
            
            # Ejecutar función
            resultado = await func(*args, **kwargs)
            
            # Guardar en caché
            await cache.establecer(clave, resultado, ttl_segundos)
            
            return resultado
        
        wrapper._cache_key_pattern = patron_invalidacion
        wrapper._cache_ttl = ttl_segundos
        
        return wrapper
    
    return decorador


def iniciar_cache() -> Dict:
    """Inicializa sistema de caché."""
    try:
        cache = obtener_cache()
        
        contexto = {
            'estado': 'ACTIVO',
            'redis': 'CONECTADO' if cache.conectado_redis else 'NO DISPONIBLE',
            'memoria_items_max': cache.cache_memoria.max_items,
            'timestamp_inicio': datetime.now().isoformat()
        }
        
        logger.info(
            f"[CACHE] Iniciado - Redis: {contexto['redis']}"
        )
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error iniciando caché: {e}")
        return {'estado': 'ERROR', 'detalles': str(e)}
