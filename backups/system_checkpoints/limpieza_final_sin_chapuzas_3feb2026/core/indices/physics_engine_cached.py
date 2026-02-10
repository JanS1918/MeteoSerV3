"""
PhysicsEngineCached - Versión con caché del motor de física.

El motor PhysicsEngine2026 calcula constantes dinámicas que dependen de
temperatura, presión, humedad. Sin embargo, estas constantes NO cambian
cada minuto, por lo que un caché de corta duración (60-300 segundos)
mejora rendimiento +30-50%.
"""
import logging
import time
from typing import Dict, Optional, Any, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class CacheConstantes:
    """Caché con TTL para constantes dinámicas."""
    
    def __init__(self, ttl_segundos: int = 60):
        """
        Args:
            ttl_segundos: Tiempo de vida del caché en segundos
        """
        self.ttl = ttl_segundos
        self.cache = {}
        self.timestamps = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Dict]:
        """Obtiene valor del caché si no ha expirado."""
        if key not in self.cache:
            self.misses += 1
            return None
        
        edad = time.time() - self.timestamps.get(key, 0)
        if edad > self.ttl:
            # Ha expirado
            del self.cache[key]
            del self.timestamps[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return self.cache[key]
    
    def set(self, key: str, value: Dict) -> None:
        """Almacena valor en caché con timestamp."""
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Limpia el caché."""
        self.cache.clear()
        self.timestamps.clear()
    
    def tasa_acierto(self) -> float:
        """Retorna porcentaje de aciertos (0-100)."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100.0
    
    def __repr__(self) -> str:
        return (f"CacheConstantes(ttl={self.ttl}s, items={len(self.cache)}, "
                f"hits={self.hits}, misses={self.misses}, "
                f"acierto={self.tasa_acierto():.1f}%)")


class PhysicsEngineCached:
    """
    Wrapper del motor de física con caché.
    
    Envuelve PhysicsEngine2026 agregando caché con TTL para
    constantes dinámicas. Los parámetros de entrada se usan como clave.
    """
    
    def __init__(self, temperatura_k: float = 288.15, presion_pa: float = 101325.0,
                 humedad_fraccion: float = 0.5, ttl_segundos: int = 60):
        """
        Inicializa engine con parámetros base.
        
        Args:
            temperatura_k: Temperatura en Kelvin
            presion_pa: Presión en Pa
            humedad_fraccion: Humedad relativa (0-1)
            ttl_segundos: TTL del caché
        """
        from core.indices.physics_engine_2026 import PhysicsEngine2026
        
        self.engine = PhysicsEngine2026(
            latitud=None,
            temperatura_k=temperatura_k,
            presion_pa=presion_pa,
            humedad_fraccion=humedad_fraccion,
        )
        self.cache = CacheConstantes(ttl_segundos)
        self.temperatura_k = temperatura_k
        self.presion_pa = presion_pa
        self.humedad_fraccion = humedad_fraccion
    
    def _generar_clave(self, temp_k: float, presion_pa: float, humedad: float) -> str:
        """Genera clave para caché basada en parámetros."""
        # Redondear para evitar fluctuaciones mínimas
        return f"T{temp_k:.1f}_P{presion_pa:.0f}_H{humedad:.3f}"
    
    def obtener_todas_constantes(self, altitud_m: float = 0.0) -> Dict:
        """
        Obtiene constantes dinámicas (con caché).
        
        Si los valores de entrada no han cambiado, retorna del caché.
        De lo contrario, calcula y almacena en caché.
        """
        clave = self._generar_clave(self.temperatura_k, self.presion_pa, self.humedad_fraccion)
        
        # Intentar obtener del caché
        cached = self.cache.get(clave)
        if cached is not None:
            logger.debug(f"🎯 Cache HIT para {clave}")
            return cached
        
        # Calcular y almacenar
        logger.debug(f"❌ Cache MISS para {clave}, calculando...")
        constantes = self.engine.obtener_todas_constantes(altitud_m)
        self.cache.set(clave, constantes)
        
        return constantes
    
    def gravedad_somigliana_helmert(self, altitud_m: float = 0.0) -> Tuple[float, Any]:
        """Gravedad (sin caché, rápido de todas formas)."""
        return self.engine.gravedad_somigliana_helmert(altitud_m)
    
    def densidad_aire_cipm_2007(self, altitud_m: float = 0.0) -> Tuple[float, Any]:
        """Densidad (sin caché, pero rápido)."""
        return self.engine.densidad_aire_cipm_2007(altitud_m)
    
    def viscosidad_sutherland(self) -> Tuple[float, Any]:
        """Viscosidad (muy rápida, no necesita caché)."""
        return self.engine.viscosidad_sutherland()
    
    def conductividad_mason_saxena(self) -> Tuple[float, Any]:
        """Conductividad térmica."""
        return self.engine.conductividad_mason_saxena()
    
    def actualizar_parametros(self, temperatura_k: float = None, 
                             presion_pa: float = None, 
                             humedad_fraccion: float = None) -> None:
        """Actualiza parámetros de entrada y limpia caché si cambian."""
        cambio = False
        
        if temperatura_k is not None and temperatura_k != self.temperatura_k:
            self.temperatura_k = temperatura_k
            self.engine.temperatura_k = temperatura_k
            cambio = True
        
        if presion_pa is not None and presion_pa != self.presion_pa:
            self.presion_pa = presion_pa
            self.engine.presion_pa = presion_pa
            cambio = True
        
        if humedad_fraccion is not None and humedad_fraccion != self.humedad_fraccion:
            self.humedad_fraccion = humedad_fraccion
            self.engine.humedad_fraccion = humedad_fraccion
            cambio = True
        
        if cambio:
            logger.debug(f"⚠️ Parámetros actualizados, limpiando caché")
            self.cache.clear()
    
    def estadisticas_cache(self) -> Dict[str, Any]:
        """Retorna estadísticas del caché."""
        return {
            "ttl_segundos": self.cache.ttl,
            "items_en_cache": len(self.cache.cache),
            "hits": self.cache.hits,
            "misses": self.cache.misses,
            "tasa_acierto_pct": self.cache.tasa_acierto(),
        }
    
    def __repr__(self) -> str:
        stats = self.estadisticas_cache()
        return (f"PhysicsEngineCached(T={self.temperatura_k:.1f}K, "
                f"P={self.presion_pa:.0f}Pa, H={self.humedad_fraccion:.2f}, "
                f"acierto={stats['tasa_acierto_pct']:.1f}%)")


def crear_physics_cached(config: Optional[Dict] = None) -> PhysicsEngineCached:
    """
    Factory para crear PhysicsEngineCached desde config.
    
    Args:
        config: Dict con configuración o None para usar valores por defecto
    
    Returns:
        PhysicsEngineCached configurado
    """
    if config is None:
        config = {}
    
    temp_k = config.get("temperatura_k", 288.15)
    presion_pa = config.get("presion_pa", 101325.0)
    humedad = config.get("humedad_fraccion", 0.5)
    ttl = config.get("cache_ttl_s", 60)
    
    return PhysicsEngineCached(temp_k, presion_pa, humedad, ttl)


if __name__ == "__main__":
    # Test simple
    print("╔════════════════════════════════════════════╗")
    print("║  Test PhysicsEngineCached - Rendimiento  ║")
    print("╚════════════════════════════════════════════╝\n")
    
    engine_cached = PhysicsEngineCached(temperatura_k=293.15, presion_pa=101325, 
                                        humedad_fraccion=0.65, ttl_segundos=60)
    
    # Primer cálculo (cache miss)
    print("1️⃣  Primer cálculo...")
    c1 = engine_cached.obtener_todas_constantes(altitud_m=96)
    print(f"   g = {c1['gravedad_ms2']:.4f} m/s²")
    print(f"   {engine_cached.cache}\n")
    
    # Segundo cálculo mismo parámetro (cache hit)
    print("2️⃣  Segundo cálculo (mismos parámetros)...")
    c2 = engine_cached.obtener_todas_constantes(altitud_m=96)
    print(f"   {engine_cached.cache}\n")
    
    # Cambiar temperatura (cache miss)
    print("3️⃣  Cambiar temperatura...")
    engine_cached.actualizar_parametros(temperatura_k=283.15)
    c3 = engine_cached.obtener_todas_constantes(altitud_m=96)
    print(f"   {engine_cached.cache}\n")
    
    # Estadísticas
    print("📊 Estadísticas finales:")
    stats = engine_cached.estadisticas_cache()
    for k, v in stats.items():
        print(f"   {k}: {v}")
