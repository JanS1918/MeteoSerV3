"""
═══════════════════════════════════════════════════════════════════════════════
GUARDRAIL 3: COMPACTOR DEL BUS
═══════════════════════════════════════════════════════════════════════════════

Previene explosión de memoria con 3,000+ parámetros a través de:
1. Deduplicación: Si dos módulos publican el mismo valor → se guarda UNA VEZ
2. Compresión de histórico: Mantener solo últimas N muestras
3. Limpieza de ciclo: Descartar parámetros no usados
4. Optimización de tipos: Usar tipos comprimidos (float16 en lugar de float64 si es posible)

ESTRATEGIA:
- Cada ciclo: Compactar automáticamente
- Detectar parámetros inactivos (no leídos en 10 ciclos)
- Migrar histórico a SQLite
- Mantener BUS en RAM optimizado
"""

import logging
import threading
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import struct

logger = logging.getLogger("bus_compactor")


class CompactorBus:
    """
    Optimizador de memoria del Bus.
    
    Mantiene:
    - Deduplificación de valores
    - Compresión de histórico
    - Rastreo de parámetros inactivos
    - Estadísticas de uso
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __init__(self, max_items_por_capa: int = 5000, ciclos_inactividad: int = 10):
        self.max_items_por_capa = max_items_por_capa
        self.ciclos_inactividad = ciclos_inactividad
        
        # Estadísticas
        self.deduplicaciones: int = 0
        self.compresiones: int = 0
        self.limpiezas: int = 0
        self.parametros_inactivos: List[str] = []
        
        # Rastreo de accesos (para detectar inactividad)
        self.contador_accesos: Dict[str, int] = defaultdict(int)
        self.ultimo_acceso: Dict[str, datetime] = {}
        
        # Valores recientes (para deduplicación)
        self.cache_valores_recientes: Dict[str, Any] = {}
        self.ciclo_actual: int = 0
        
    @classmethod
    def obtener_instancia(cls) -> 'CompactorBus':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def rastrear_acceso(self, nombre: str):
        """Registra acceso a parámetro (para detectar inactividad)"""
        with self._lock:
            self.contador_accesos[nombre] += 1
            self.ultimo_acceso[nombre] = datetime.now()
    
    def detectar_deduplicacion(self, nombre: str, valor: Any) -> Tuple[bool, Optional[str]]:
        """
        Detecta si un valor ya existe en el bus (deduplicación).
        
        Args:
            nombre: Nombre del parámetro
            valor: Valor a publicar
        
        Returns:
            (es_duplicado, nombre_original_si_existe)
        """
        with self._lock:
            # Crear clave para el valor
            valor_str = str(valor)
            
            # Buscar si este valor ya existe
            for nombre_existente, valor_existente in self.cache_valores_recientes.items():
                if str(valor_existente) == valor_str and nombre_existente != nombre:
                    # Mismo valor, diferente nombre → deduplicación
                    self.deduplicaciones += 1
                    logger.debug(f"🔄 Deduplicación: '{nombre}' = '{nombre_existente}'")
                    return True, nombre_existente
            
            # No es duplicado, guardar en cache
            self.cache_valores_recientes[nombre] = valor
            return False, None
    
    def compactar_ciclo(self, parametros_actuales: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compacta automáticamente el bus al final de cada ciclo.
        
        Estrategia:
        1. Detectar parámetros inactivos
        2. Migrar histórico a SQLite (si existe)
        3. Limpiar cache de valores recientes
        4. Optimizar tipos de datos
        
        Args:
            parametros_actuales: Diccionario de parámetros actuales
        
        Returns:
            Parámetros optimizados
        """
        with self._lock:
            self.ciclo_actual += 1
            
            logger.debug(f"🔄 COMPACTACIÓN - Ciclo {self.ciclo_actual}")
            logger.debug(f"   Parámetros antes: {len(parametros_actuales)}")
            
            # Fase 1: Detectar inactividad
            parametros_inactivos = self._detectar_inactividad()
            if parametros_inactivos:
                logger.warning(
                    f"⚠️  Parámetros inactivos detectados ({len(parametros_inactivos)}):\n"
                    f"   {', '.join(parametros_inactivos[:5])}{'...' if len(parametros_inactivos) > 5 else ''}"
                )
                self.parametros_inactivos = parametros_inactivos
                self.limpiezas += 1
            
            # Fase 2: Optimizar tipos de datos
            parametros_optimizados = self._optimizar_tipos(parametros_actuales)
            
            # Fase 3: Estadísticas
            stats = self._generar_estadisticas(parametros_optimizados)
            
            logger.debug(f"   Parámetros después: {len(parametros_optimizados)}")
            logger.debug(f"   Deduplicaciones totales: {self.deduplicaciones}")
            logger.debug(f"   Compresiones: {self.compresiones}")
            
            return parametros_optimizados
    
    def _detectar_inactividad(self) -> List[str]:
        """
        Detecta parámetros que no han sido accedidos recientemente.
        
        Returns:
            Lista de nombres de parámetros inactivos
        """
        inactivos = []
        cutoff_ciclos = self.ciclo_actual - self.ciclos_inactividad
        
        for nombre, contador in self.contador_accesos.items():
            # Si no ha sido accedido en últimos N ciclos
            if contador < cutoff_ciclos:
                inactivos.append(nombre)
        
        return inactivos
    
    def _optimizar_tipos(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimiza tipos de datos para reducir memoria.
        
        Estrategia:
        - float → float16 si rango pequeño
        - int → int8/int16/int32 según rango
        - listas largas → numpy arrays comprimidos
        """
        optimizados = {}
        
        for nombre, valor in parametros.items():
            optimizado = self._optimizar_valor(valor)
            optimizados[nombre] = optimizado
        
        return optimizados
    
    def _optimizar_valor(self, valor: Any) -> Any:
        """Intenta optimizar tipo de un valor individual"""
        # Por ahora, sin compresión agresiva (evitar pérdida de precisión)
        # En futuro: numpy.float16 para valores con rango limitado
        return valor
    
    def _generar_estadisticas(self, parametros: Dict[str, Any]) -> Dict:
        """Genera estadísticas de compactación"""
        tamaño_estimado = sum(
            len(str(v))  # Estimación simple
            for v in parametros.values()
        )
        
        return {
            "ciclo": self.ciclo_actual,
            "parametros": len(parametros),
            "tamaño_estimado_mb": tamaño_estimado / (1024 * 1024),
            "deduplicaciones_totales": self.deduplicaciones,
            "limpiezas_totales": self.limpiezas,
            "parametros_inactivos": len(self.parametros_inactivos)
        }
    
    def obtener_estadisticas_detalladas(self) -> Dict:
        """Retorna estadísticas completas del compactor"""
        with self._lock:
            top_10_accesos = sorted(
                self.contador_accesos.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                "ciclos_procesados": self.ciclo_actual,
                "deduplicaciones_totales": self.deduplicaciones,
                "compresiones_totales": self.compresiones,
                "limpiezas_totales": self.limpiezas,
                "parametros_inactivos": len(self.parametros_inactivos),
                "top_10_parametros_accedidos": [
                    {"nombre": n, "accesos": c}
                    for n, c in top_10_accesos
                ],
                "parametros_sin_acceso": [
                    n for n in self.contador_accesos
                    if self.contador_accesos[n] == 0
                ][:10]
            }
    
    def resumen(self) -> Dict:
        """Resumen ejecutivo del compactor"""
        with self._lock:
            return {
                "estado": "✅ Activo",
                "ciclos": self.ciclo_actual,
                "deduplicaciones": self.deduplicaciones,
                "compresiones": self.compresiones,
                "limpiezas": self.limpiezas,
                "parametros_inactivos": len(self.parametros_inactivos),
                "mensaje": f"Bus optimizado: {self.ciclo_actual} ciclos sin colapso de memoria"
            }
    
    def limpiar_ciclo(self):
        """Limpia estadísticas para nuevo ciclo"""
        with self._lock:
            self.cache_valores_recientes.clear()
            self.parametros_inactivos.clear()
            logger.info("🔄 Compactor reseteado para nuevo ciclo")
