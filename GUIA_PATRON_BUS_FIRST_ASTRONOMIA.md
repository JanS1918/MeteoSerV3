# Guía de Patrón BUS-FIRST para Datos Astronómicos
**Versión:** 1.0  
**Fecha:** 11 de febrero de 2026  
**Estado:** ✅ Implementado y validado

---

## 📋 Introducción

El patrón **BUS-FIRST** es un estándar de arquitectura de MeteoSerV3 que establece que:

> **Todos los datos astronómicos (elevación, azimuth, posición solar/lunar) deben ser consumidos desde un bus central de datos, no recalculados localmente.**

---

## 🏗️ Arquitectura

### 1. Publicador Central: BusExpander
**Archivo:** `core/system/bus_expander.py`  
**Función:** `async def _publish_astronomia()`

El `BusExpander` es el **único publicador autorizado** de datos astronómicos. Calcula:
- Elevación solar (SPA NREL): `elevacion_solar_deg`
- Azimuth solar: `azimut_solar_deg`
- Distancia Tierra-Sol: `distancia_tierra_sol_AU`
- Subfactores: refracción, delta-T, etc.

**Frecuencia:** Cada ciclo del sistema (típicamente cada minuto)

### 2. Consumidores: Patrón BUS-FIRST
Todos los módulos que necesitan datos astronómicos deben:

```python
# ⚛️ PASO 1: Intentar leer del bus
try:
    from core.system.bus import obtener_bus
    bus = obtener_bus()
    if bus:
        elevacion_solar = bus.leer("elevacion_solar_deg")
        azimut_solar = bus.leer("azimut_solar_deg")
        
        if elevacion_solar is not None and azimut_solar is not None:
            # ✅ Datos encontrados en bus
            logger.debug(f"Datos astronómicos del bus: elev={elevacion_solar:.1f}°")
            # Continuar con lógica principal
        else:
            raise ValueError("Bus sin datos astronómicos")
except:
    pass

# ⚛️ PASO 2: Fallback - calcular localmente
if elevacion_solar is None:
    try:
        from core.indices.astronomia_recursiva import AstronomiaRecursiva
        astro = AstronomiaRecursiva(lat, lon, alt)
        resultado = astro.calcular_posicion_solar_nrel_spa(...)
        elevacion_solar = resultado.get("elevacion_aparente_deg")
        logger.debug("Datos astronómicos calculados localmente (fallback)")
    except:
        # Último recurso: valores por defecto
        elevacion_solar = 45.0  # Fallback: mediodía perpendicular
```

---

## 📍 Consumidores Implementados

### ✅ Módulos Con Patrón BUS-FIRST

| Módulo | Líneas | Tipo | Estado |
|--------|--------|------|--------|
| `app/ui/router.py` | 80, 397, 782, 846, 1654, 2549, 2667 | UI Router | ✅ Implementado |
| `routers/fusion_endpoints.py` | 385-408 | API Endpoints | ✅ Implementado |
| `core/indices/contexto_solar.py` | 118-143 | Índices | ✅ Implementado |
| `core/arcos_solares.py` | 199-227 | Utilidades | ✅ Implementado |
| `core/indices/radiacion_hibrida.py` | 175-230 | Índices | ✅ Implementado |
| `core/integration/ecowitt_receiver.py` | (integración) | Sensores | ✅ Implementado |
| `main_asgi.py` | (integración) | Aplicación | ✅ Implementado |
| `core/context/contexto_maestro_global.py` | (integración) | Contexto | ✅ Implementado |
| `core/indices/environmental_indices.py` | 3455-3490 | Índices | ✅ Implementado |

---

## 🔄 Datos Disponibles en el Bus

### Datos Solares Primarios
```python
{
    "elevacion_solar_deg": float,           # Elevación sobre horizonte (°)
    "azimut_solar_deg": float,              # Dirección desde norte (°)
    "distancia_tierra_sol_AU": float,       # Distancia Tierra-Sol (UA)
    "elevacion_verdadera_solar": float,     # Elevación sin refracción
    "refraccion_solar_arcmin": float,       # Refracción atmosférica (arcmin)
    "dia_juliano_ephemeris": float,         # JDE para cálculos
    "delta_t_segundos": float               # Delta-T (segundos)
}
```

### Datos Lunares
```python
{
    "elevacion_lunar_deg": float,           # Elevación lunar
    "azimut_lunar_deg": float,              # Azimuth lunar
    "fase_lunar": str,                      # Nombre de fase
    "arco_lunar_azimuth_deg": float         # Azimuth lunar completo
}
```

### Contexto Temporal
```python
{
    "amanecer": str,                        # HH:MM
    "atardecer": str,                       # HH:MM
    "duracion_dia_h": float,                # Duración día (horas)
    "es_dia": bool                          # ¿Es de día?
}
```

---

## 💡 Ejemplo Completo: Integración en Nuevo Módulo

Si creas un nuevo módulo que necesita datos astronómicos:

```python
"""
Módulo: custom_radiacion_calculo.py
Patrón: BUS-FIRST para elevación solar
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def calcular_indice_radiativo(
    temp_c: float,
    humedad_rel: float,
    latitud: float,
    longitud: float,
    altitud_m: float = 100.0
) -> float:
    """
    Calcula índice radiativo usando elevación solar del bus si está disponible.
    
    Args:
        temp_c: Temperatura (°C)
        humedad_rel: Humedad relativa (%)
        latitud: Latitud (°)
        longitud: Longitud (°)
        altitud_m: Altitud (m), por defecto 100m
    
    Returns:
        Índice radiativo (0-1)
    
    Pattern: BUS-FIRST
    """
    elevacion_solar = None
    
    # ⚛️ PASO 1: Bus-first - intentar leer del bus
    try:
        from core.system.bus import obtener_bus
        bus = obtener_bus()
        
        if bus:
            elevacion_solar_bus = bus.leer("elevacion_solar_deg")
            
            if elevacion_solar_bus is not None:
                elevacion_solar = float(elevacion_solar_bus)
                logger.debug(f"[custom_radiacion] Elevación del bus: {elevacion_solar:.1f}°")
            else:
                logger.debug("[custom_radiacion] Bus disponible pero sin elevacion_solar_deg")
    except Exception as e:
        logger.debug(f"[custom_radiacion] Error accediendo bus: {e}")
    
    # ⚛️ PASO 2: Fallback - calcular localmente
    if elevacion_solar is None:
        try:
            from core.indices.astronomia_recursiva import AstronomiaRecursiva
            from datetime import datetime, timezone
            
            astro = AstronomiaRecursiva(latitud, longitud, altitud_m)
            fecha_utc = datetime.now(timezone.utc)
            
            resultado = astro.calcular_posicion_solar_nrel_spa(
                fecha_utc=fecha_utc,
                presion_hpa=1013.25,
                temperatura_c=temp_c,
                humedad_fraccion=humedad_rel / 100.0
            )
            
            elevacion_solar = resultado.get("elevacion_aparente_deg", 0.0)
            logger.debug(f"[custom_radiacion] Elevación calculada (fallback): {elevacion_solar:.1f}°")
        
        except Exception as e:
            logger.warning(f"[custom_radiacion] Error en fallback: {e}")
            elevacion_solar = 45.0  # Por defecto: mediodía
    
    # ⚛️ PASO 3: Calcular índice usando elevación
    if elevacion_solar < -6.0:
        # Noche civil - sin radiación significativa
        indice = 0.0
    elif elevacion_solar < 0.0:
        # Crepúsculo - radiación baja
        indice = 0.1
    elif elevacion_solar < 10.0:
        # Mañana temprano/tarde baja
        indice = 0.3 + (elevacion_solar + 10.0) / 100.0
    elif elevacion_solar < 30.0:
        # Medio día
        indice = 0.5 + (elevacion_solar - 10.0) / 40.0
    else:
        # Sol alto - máxima radiación
        indice = 0.9 + (elevacion_solar - 30.0) / 100.0
    
    return min(1.0, max(0.0, indice))
```

---

## ✅ Checklist para Nuevos Desarrollos

Cuando implementes funcionalidad que usa datos astronómicos:

- [ ] ¿Intentas leer del bus primero? (`obtener_bus()` → `leer()`)
- [ ] ¿Validas que el dato no sea None?
- [ ] ¿Tienes un fallback a `AstronomiaRecursiva`?
- [ ] ¿Logueas claramente qué fuente usas (bus vs local)?
- [ ] ¿Manejas excepciones de forma defensiva?
- [ ] ¿Tienes un valor por defecto sensato?
- [ ] ¿Los tests pasan sin regressions?

---

## 🚀 Ventajas del Patrón BUS-FIRST

| Ventaja | Beneficio |
|---------|-----------|
| **Centralización** | Un único cálculo de posición solar para todo el sistema |
| **Consistencia** | Todos los módulos usan los mismos datos |
| **Performance** | Evita recálculos redundantes (~100ms ahorro por ciclo) |
| **Debugging** | Los datos astronómicos están centralizados en el bus |
| **Resilencia** | Fallback automático a cálculo local si bus falla |
| **Testabilidad** | Puedes mockear datos en tests |

---

## ⚠️ Errores Comunes

### ❌ INCORRECTO: Calcular directo sin consultar bus
```python
# MAL - Recalcula innecesariamente
from core.indices.astronomia_recursiva import AstronomiaRecursiva
astro = AstronomiaRecursiva(lat, lon, alt)
resultado = astro.calcular_posicion_solar_nrel_spa(...)
```

### ✅ CORRECTO: Bus-first con fallback
```python
# BIEN - Consulta bus primero
elevacion = None
try:
    bus = obtener_bus()
    if bus:
        elevacion = bus.leer("elevacion_solar_deg")
except:
    pass

if elevacion is None:
    # Fallback a cálculo local
    from core.indices.astronomia_recursiva import AstronomiaRecursiva
    astro = AstronomiaRecursiva(lat, lon, alt)
    resultado = astro.calcular_posicion_solar_nrel_spa(...)
    elevacion = resultado.get("elevacion_aparente_deg")
```

---

## 📊 Metrics y Monitoreo

### KPI: Uso del Bus
```
Métrica: % de consumidores que leen del bus en primer intento
Objetivo: > 95%
Verificación: Revisar logs de debug "[SOURCE: BUS]"
```

### KPI: Fallbacks
```
Métrica: Frecuencia de fallbacks locales
Objetivo: < 5% (indica problemas con bus)
Alarma: Si > 10%, revisar salud del BusExpander
```

---

## 🔗 Referencias

- [BusExpander (publicador central)](core/system/bus_expander.py#L1973)
- [AstronomiaRecursiva (cálculo local)](core/indices/astronomia_recursiva.py)
- [Módulos con patrón implementado](#-consumidores-implementados)

---

## 📝 Versión del Documento

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-02-11 | Documento inicial - Patrón BUS-FIRST completamente implementado |

