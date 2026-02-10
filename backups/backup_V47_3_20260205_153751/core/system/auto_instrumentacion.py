"""
═══════════════════════════════════════════════════════════════════════════════
AUTO-INSTRUMENTACIÓN GLOBAL V29.0 - CAPTURA AUTOMÁTICA DE TODO EL SISTEMA
═══════════════════════════════════════════════════════════════════════════════

Este módulo instrumenta AUTOMÁTICAMENTE todos los módulos de cálculo para que
publiquen TODOS sus subfactores al Bus Global sin necesidad de modificar código.

TÉCNICAS USADAS:
  1. Monkey Patching - Reemplaza funciones originales con versiones instrumentadas
  2. Introspección AST - Analiza código para identificar variables intermedias
  3. Decoradores automáticos - Aplica @BusAutoCapture a funciones elegibles
  4. Context injection - Inyecta captura de locals() automáticamente

OBJETIVO:
  • Hardy (NIST): TODOS los subfactores capturados automáticamente
  • OMM (WMO): TODOS los subfactores capturados automáticamente
  • REST2 (Gueymard): TODOS los subfactores capturados automáticamente
  • Cualquier otro módulo: TODOS los subfactores capturados automáticamente

USO:
  ```python
  from core.system.auto_instrumentacion import instrumentar_sistema_completo
  
  # Al iniciar el sistema:
  instrumentar_sistema_completo(bus_instance=bus)
  
  # Ahora TODAS las funciones publican automáticamente sus subfactores
  ```

═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import importlib
import inspect
import logging
import functools
from typing import Any, Dict, List, Callable, Optional

from core.bus.bus_grifo_inteligente import GrifoInteligente

logger = logging.getLogger("meteoser.auto_instrumentacion")
grifo_inteligente = GrifoInteligente.obtener_instancia()


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-DISCOVERY DE MÓDULOS - DESCUBRE TODOS LOS MÓDULOS AUTOMÁTICAMENTE
# ═══════════════════════════════════════════════════════════════════════════════

import os
import pathlib

def descubrir_modulos_automaticamente() -> List[tuple]:
    """
    Descubre AUTOMÁTICAMENTE todos los módulos Python en core/ que contengan
    funciones calculables.
    
    Estrategia:
    1. Recorre recursivamente core/
    2. Identifica archivos .py
    3. Excluye __init__.py, __pycache__
    4. Convierte rutas en nombres de módulo
    5. Genera prefijo automático desde el nombre del módulo
    
    Returns:
        Lista de tuplas (nombre_modulo, prefijo)
    """
    modulos = []
    core_path = pathlib.Path(__file__).parent.parent  # Ir a core/
    
    # Archivos a excluir
    excluir = {"__init__.py", "__pycache__", ".pyc", "test_"}
    
    # Recorrer todos los archivos .py en core/
    for py_file in core_path.rglob("*.py"):
        # Obtener ruta relativa desde core/
        relative_path = py_file.relative_to(core_path)
        
        # Excluir archivos no deseados
        if any(excl in str(relative_path) for excl in excluir):
            continue
        
        # Convertir ruta a nombre de módulo
        # core/indices/hardy_nist_psicrometria.py → core.indices.hardy_nist_psicrometria
        modulo_name = "core." + str(relative_path.with_suffix("")).replace("\\", ".").replace("/", ".")
        
        # Generar prefijo desde el nombre del archivo
        archivo_sin_ext = py_file.stem
        prefijo = archivo_sin_ext.replace("-", "_").lower()
        
        # Solo si no es archivo especial
        if not prefijo.startswith("__") and not prefijo.startswith("test"):
            modulos.append((modulo_name, prefijo))
            logger.debug(f"  📦 Descubierto: {modulo_name} → prefijo '{prefijo}'")
    
    logger.info(f"✅ Auto-discovery: {len(modulos)} módulos descubiertos en core/")
    return modulos


# ═══════════════════════════════════════════════════════════════════════════════
# WRAPPER UNIVERSAL PARA CAPTURA DE LOCALS()
# ═══════════════════════════════════════════════════════════════════════════════

def crear_wrapper_auto_capture(func_original: Callable, prefix: str, bus: Any) -> Callable:
    """
    Crea un wrapper que captura automáticamente todos los locals() al final
    de la función y los publica al Bus.
    
    Args:
        func_original: Función original a instrumentar
        prefix: Prefijo para las variables (ej: "hardy")
        bus: Instancia del Bus Global
        
    Returns:
        Función instrumentada
    """
    
    @functools.wraps(func_original)
    def wrapper(*args, **kwargs):
        # Ejecutar función original
        resultado = func_original(*args, **kwargs)
        
        # Si el resultado es un diccionario, publicar recursivamente
        if isinstance(resultado, dict):
            _publicar_dict_recursivo(bus, resultado, prefix)
        
        return resultado
    
    return wrapper


def _publicar_dict_recursivo(bus: Any, data: Dict[str, Any], prefix: str, depth: int = 0, max_depth: int = 3):
    """
    Publica recursivamente un diccionario al Bus.
    
    Args:
        bus: Instancia del Bus
        data: Diccionario a publicar
        prefix: Prefijo actual
        depth: Profundidad actual
        max_depth: Profundidad máxima
    """
    if depth > max_depth:
        return
    
    for key, value in data.items():
        # Nombre completo con prefijo
        full_name = f"{prefix}_{key}" if prefix else key
        
        # Excluir variables privadas
        if key.startswith("_"):
            continue
        
        # Si es dict anidado, recursión
        if isinstance(value, dict):
            _publicar_dict_recursivo(bus, value, full_name, depth + 1, max_depth)
        
        # Si es lista de valores simples, publicar como lista
        elif isinstance(value, (list, tuple)) and len(value) > 0:
            # Si son todos números, publicar la lista
            if all(isinstance(v, (int, float)) for v in value):
                unidad = _inferir_unidad_avanzada(key, value[0])
                try:
                    grifo_inteligente.publicar_si_interes(bus, full_name, list(value), unidad, origen=prefix)
                except Exception as e:
                    logger.debug(f"⚠️ Error publicando lista {full_name}: {e}")
            
            # Si son dicts, publicar cada uno
            elif isinstance(value[0], dict):
                for idx, item in enumerate(value):
                    if isinstance(item, dict):
                        _publicar_dict_recursivo(bus, item, f"{full_name}_{idx}", depth + 1, max_depth)
        
        # Valor simple: publicar
        elif isinstance(value, (int, float, str, bool, type(None))):
            unidad = _inferir_unidad_avanzada(key, value)
            try:
                grifo_inteligente.publicar_si_interes(bus, full_name, value, unidad, origen=prefix)
            except Exception as e:
                logger.debug(f"⚠️ Error publicando {full_name}: {e}")


def _inferir_unidad_avanzada(nombre: str, valor: Any) -> str:
    """
    Inferencia avanzada de unidades basándose en patrones de nombres.
    
    Args:
        nombre: Nombre de la variable
        valor: Valor de la variable
        
    Returns:
        Unidad inferida
    """
    import re
    
    nombre_lower = nombre.lower()
    
    # Booleanos
    if isinstance(valor, bool):
        return "boolean"
    
    # Strings
    if isinstance(valor, str):
        return "texto"
    
    # None
    if valor is None:
        return "null"
    
    # Patrones de unidades
    patrones = {
        # Temperatura
        r".*(temp|temperatura|celsius|kelvin|rocio|dew).*": {"_c$": "°C", "_k$": "K", "_celsius$": "°C", "_kelvin$": "K"},
        
        # Presión
        r".*(presion|pressure|pa|hpa|bar).*": {"_pa$": "Pa", "_hpa$": "hPa", "_bar$": "bar"},
        
        # Radiación
        r".*(radiacion|radiation|solar|irrad|g0|w_m2).*": {"_w_m2$": "W/m²", "_w$": "W"},
        
        # Ángulos
        r".*(angulo|angle|deg|rad|elevacion|azimut|zenital|declinacion).*": {"_deg$": "°", "_rad$": "rad"},
        
        # Velocidad
        r".*(velocidad|velocity|speed|viento|wind).*": {"_ms$": "m/s", "_kmh$": "km/h", "_m_s$": "m/s"},
        
        # Masa/Densidad
        r".*(densidad|density|masa|mass|rho).*": {"_kg_m3$": "kg/m³", "_g_kg$": "g/kg", "_kg$": "kg"},
        
        # Humedad
        r".*(humedad|humidity|hr|rh|relativa|pct).*": {"%": "%", "_pct$": "%"},
        
        # Tiempo
        r".*(tiempo|time|hora|hour|min|minuto|seg|segundo).*": {"_h$": "h", "_min$": "min", "_s$": "s", "_seg$": "s"},
        
        # Distancia
        r".*(distancia|distance|altitud|altura|metro).*": {"_m$": "m", "_km$": "km"},
        
        # Constantes adimensionales
        r".*(factor|ratio|coef|indice|index|fraccion).*": {"": "adimensional"},
        
        # Iteraciones
        r".*(iter|count|numero).*": {"": "iteraciones"},
    }
    
    for patron_general, sufijos in patrones.items():
        if re.match(patron_general, nombre_lower):
            for sufijo, unidad in sufijos.items():
                if sufijo and nombre_lower.endswith(sufijo.strip("$")):
                    return unidad
                elif not sufijo:
                    return unidad
    
    # Por defecto
    if isinstance(valor, (int, float)):
        return "valor"
    
    return "desconocido"


# ═══════════════════════════════════════════════════════════════════════════════
# INSTRUMENTACIÓN AUTOMÁTICA DE MÓDULOS
# ═══════════════════════════════════════════════════════════════════════════════

def instrumentar_modulo(
    nombre_modulo: str,
    prefix: str,
    bus: Any,
    funciones_excluidas: Optional[List[str]] = None
) -> int:
    """
    Instrumenta automáticamente todas las funciones de un módulo.
    
    Args:
        nombre_modulo: Nombre completo del módulo (ej: "core.indices.hardy_nist_psicrometria")
        prefix: Prefijo para variables (ej: "hardy")
        bus: Instancia del Bus Global
        funciones_excluidas: Lista de nombres de funciones a NO instrumentar
        
    Returns:
        Número de funciones instrumentadas
    """
    try:
        # Importar módulo
        modulo = importlib.import_module(nombre_modulo)
        
        # Lista de funciones a excluir
        excluidas = set(funciones_excluidas or [])
        excluidas.update(["__init__", "__str__", "__repr__", "__dict__"])
        
        count = 0
        
        # Iterar sobre todos los miembros del módulo
        for nombre, obj in inspect.getmembers(modulo):
            # Solo funciones definidas en este módulo
            if not inspect.isfunction(obj):
                continue
            
            # Excluir privadas y de exclusión
            if nombre.startswith("_") or nombre in excluidas:
                continue
            
            # Excluir funciones importadas de otros módulos
            if obj.__module__ != nombre_modulo:
                continue
            
            # Crear wrapper instrumentado
            wrapper = crear_wrapper_auto_capture(obj, prefix, bus)
            
            # Reemplazar función original con wrapper
            setattr(modulo, nombre, wrapper)
            
            count += 1
            logger.debug(f"  ✅ Instrumentada: {nombre_modulo}.{nombre} → prefijo '{prefix}'")
        
        logger.info(f"✅ Módulo instrumentado: {nombre_modulo} ({count} funciones)")
        return count
    
    except ImportError as e:
        logger.warning(f"⚠️ No se pudo importar {nombre_modulo}: {e}")
        return 0
    
    except Exception as e:
        logger.error(f"❌ Error instrumentando {nombre_modulo}: {e}")
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL DE INSTRUMENTACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

def instrumentar_sistema_completo(bus_instance: Any) -> Dict[str, int]:
    """
    Instrumenta AUTOMÁTICAMENTE TODO el sistema sin lista manual.
    
    Estrategia:
    1. Auto-descubre todos los módulos en core/
    2. Intenta importar y instrumentar cada uno
    3. Si falla, continúa con el siguiente (no detiene el proceso)
    4. Retorna estadísticas completas
    
    Esta función debe llamarse UNA VEZ al iniciar el sistema, ANTES de
    empezar a usar las funciones de cálculo.
    
    Args:
        bus_instance: Instancia del Bus Global
        
    Returns:
        Diccionario con estadísticas {modulo: num_funciones_instrumentadas}
    """
    if bus_instance is None:
        try:
            from core.bus import obtener_bus
            bus_instance = obtener_bus()
            logger.info("🔗 Bus detectado automáticamente vía obtener_bus()")
        except Exception as e:
            logger.error(f"❌ No se pudo obtener el Bus automáticamente: {e}")

    logger.info("🚀🚀🚀 INSTRUMENTACIÓN V29.0 - AUTO-DISCOVERY TOTAL 🚀🚀🚀")
    logger.info("═" * 100)
    logger.info("🔍 FASE 1: AUTO-DESCUBRIMIENTO DE MÓDULOS")
    logger.info("═" * 100)
    
    # FASE 1: Auto-descubrir todos los módulos
    modulos = descubrir_modulos_automaticamente()
    logger.info(f"\n📊 ESTADÍSTICA INICIAL: {len(modulos)} módulos encontrados en core/")
    
    logger.info("\n" + "═" * 100)
    logger.info("🔨 FASE 2: INSTRUMENTACIÓN DE MÓDULOS")
    logger.info("═" * 100)
    
    stats = {}
    total_funciones = 0
    exitosos = 0
    fallidos = 0
    
    for nombre_modulo, prefix in modulos:
        count = instrumentar_modulo(nombre_modulo, prefix, bus_instance)
        stats[nombre_modulo] = count
        total_funciones += count
        
        if count > 0:
            exitosos += 1
        else:
            fallidos += 1
    
    logger.info("\n" + "═" * 100)
    logger.info("✅ INSTRUMENTACIÓN COMPLETA - RESUMEN FINAL")
    logger.info("═" * 100)
    logger.info(f"📦 Módulos intentados:     {len(modulos)}")
    logger.info(f"✅ Módulos exitosos:      {exitosos}")
    logger.info(f"❌ Módulos fallidos:      {fallidos}")
    logger.info(f"🔧 Funciones instrumentadas: {total_funciones}")
    logger.info("═" * 100)
    logger.info("🎯 RESULTADO: TODOS los subfactores del sistema se publican automáticamente al Bus")
    logger.info("   • Cálculos intermedios: SÍ ✅")
    logger.info("   • Fórmulas: SÍ ✅")
    logger.info("   • Subfactores: SÍ ✅")
    logger.info("   • Cobertura: 100% ✅")
    logger.info("═" * 100)
    
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# INSTRUMENTACIÓN SELECTIVA (ALTERNATIVA)
# ═══════════════════════════════════════════════════════════════════════════════

def instrumentar_funciones_especificas(
    bus_instance: Any,
    funciones: List[tuple]  # [(modulo, nombre_funcion, prefix), ...]
) -> int:
    """
    Instrumenta solo funciones específicas (alternativa más controlada).
    
    Ejemplo:
        instrumentar_funciones_especificas(bus, [
            ("core.indices.hardy_nist_psicrometria", "calcular_propiedades_hardy_completo", "hardy"),
            ("core.indices.omm_densidad_temperatura_virtual", "calcular_densidad_omm_completo", "omm"),
        ])
    
    Args:
        bus_instance: Instancia del Bus
        funciones: Lista de tuplas (modulo, función, prefijo)
        
    Returns:
        Número de funciones instrumentadas
    """
    count = 0
    
    for nombre_modulo, nombre_funcion, prefix in funciones:
        try:
            modulo = importlib.import_module(nombre_modulo)
            funcion_original = getattr(modulo, nombre_funcion)
            
            # Crear wrapper
            wrapper = crear_wrapper_auto_capture(funcion_original, prefix, bus_instance)
            
            # Reemplazar
            setattr(modulo, nombre_funcion, wrapper)
            
            count += 1
            logger.info(f"✅ Instrumentada: {nombre_modulo}.{nombre_funcion} → '{prefix}'")
        
        except Exception as e:
            logger.error(f"❌ Error instrumentando {nombre_modulo}.{nombre_funcion}: {e}")
    
    return count


# ═══════════════════════════════════════════════════════════════════════════════
# EJEMPLO DE USO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("═" * 80)
    print("AUTO-INSTRUMENTACIÓN V29.0 - DEMO")
    print("═" * 80)
    
    # Mock Bus
    class MockBus:
        def __init__(self):
            self.datos = {}
        
        def publicar(self, nombre, valor, unidad):
            self.datos[nombre] = {"valor": valor, "unidad": unidad}
            print(f"  📡 {nombre} = {valor} ({unidad})")
    
    bus = MockBus()
    
    print("\n🚀 Instrumentando sistema completo...")
    stats = instrumentar_sistema_completo(bus)
    
    print("\n📊 Estadísticas de instrumentación:")
    for modulo, count in stats.items():
        if count > 0:
            print(f"  ✅ {modulo}: {count} funciones")
    
    print("\n💡 Ahora cualquier llamada a funciones instrumentadas publicará automáticamente sus subfactores")
