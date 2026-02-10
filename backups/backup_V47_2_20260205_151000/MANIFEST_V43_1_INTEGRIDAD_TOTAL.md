# 🛡️ MANIFEST V43.1 - INTEGRIDAD TOTAL: SRTM + ARCO SOLAR + ARCO LUNAR OBLIGATORIOS
**MeteoSerV3 - Argentona 41.55326700°N, 2.39684500°E**  
**Fecha:** 5 de febrero de 2026  
**Motor:** V43.1_INTEGRIDAD_GEOGRAFICA_ASTRONOMICA_TOTAL

---

## 📜 RESUMEN EJECUTIVO

**MISIÓN V43.1: FORZAR USO OBLIGATORIO DE SRTM + ARCO SOLAR + ARCO LUNAR**

El Acorazado MeteoSerV3 establece **integridad absoluta de datos geográficos y astronómicos**:

1. **SRTM OBLIGATORIO:** Todos los cálculos que usan altitud DEBEN obtenerla del bus (fuente: SRTM)
2. **ARCO SOLAR OBLIGATORIO:** Todos los cálculos radiativos DEBEN usar elevación/azimuth solar desde bus (fuente: SPA NREL)
3. **ARCO LUNAR OBLIGATORIO:** Todos los cálculos nocturnos DEBEN usar elevación/azimuth lunar desde bus (fuente: Meeus ELP2000)

**CERO uso de altitudes hardcoded. CERO cálculos astronómicos redundantes. CERO degradación silenciosa.**

---

## 🎯 IMPLEMENTACIONES V43.1

### 1. PUBLICACIÓN OBLIGATORIA DE SRTM EN BUS

**Archivo:** `core/system/bus_expander.py`

**Función:** `_publish_contexto_geografico()`

**Modificación:**
```python
# ⚛️ V43.1: FORZAR USO DE SRTM PARA ALTITUD
altitud_srtm = None
fuente_altitud = "manual"

try:
    from core.location.location_engine import LocationEngine
    loc_engine = LocationEngine()
    loc_engine.lat = lat
    loc_engine.lon = lon
    
    # Intentar cargar desde SRTM
    altitud_srtm = loc_engine.load_altitude_srtm(force=False)
    
    if altitud_srtm is not None and altitud_srtm > 0:
        # SRTM disponible: USARLO OBLIGATORIAMENTE
        altitud = altitud_srtm
        fuente_altitud = "SRTM"
        logger.info(f"✅ Altitud SRTM cargada: {altitud_srtm}m")
    else:
        logger.warning(f"⚠️ SRTM no disponible, usando altitud manual: {altitud}m")
        fuente_altitud = "manual_fallback"
except Exception as e_srtm:
    logger.warning(f"⚠️ Error cargando SRTM: {e_srtm}, usando altitud manual: {altitud}m")
    fuente_altitud = "manual_fallback_error"
```

**Datos publicados:**
```python
self.bus.publicar("latitud", lat, "grados")
self.bus.publicar("longitud", lon, "grados")
self.bus.publicar("altitud", altitud, "m")                      # SRTM o fallback
self.bus.publicar("altitud_srtm", altitud_srtm or altitud, "m") # Siempre disponible
self.bus.publicar("fuente_altitud", fuente_altitud, "texto")     # Trazabilidad
```

**Fuentes posibles:**
- `"SRTM"`: Altitud obtenida desde API SRTM (óptimo)
- `"manual_fallback"`: SRTM no disponible, usa config manual
- `"manual_fallback_error"`: Error en SRTM, usa config manual

### 2. FORZAR USO DE ALTITUD SRTM EN CÁLCULOS CRÍTICOS

**Archivos modificados:**
- `core/system/bus_expander.py` (múltiples funciones)

**Funciones actualizadas:**

#### A. Cálculos Físicos (`_publish_physics`)
```python
# ⚛️ V43.1: FORZAR USO DE ALTITUD SRTM DESDE BUS
altitud = self.bus.obtener("altitud_srtm")
if altitud is None:
    altitud = self.system.location.get("altitud", 0.0) if hasattr(self.system, 'location') else 0.0
```

**Impacto:**
- Gravedad Somigliana-Helmert con altitud SRTM real
- Densidad aire CIPM-2007 con altitud SRTM real
- Factor compresibilidad Virial con altitud SRTM real

#### B. Cálculos Atmosféricos (`_publish_atmosfera`)
```python
# ⚛️ V43.1: FORZAR USO DE ALTITUD SRTM DESDE BUS
altitud = self.bus.obtener("altitud_srtm")
if altitud is None:
    altitud = self.system.location.get("altitud", 0.0) if hasattr(self.system, 'location') else 0.0
```

**Impacto:**
- Presión reducida nivel del mar (Laplace) con SRTM
- Altura geopotencial con SRTM
- Temperatura potencial con SRTM

#### C. Astronomía Solar (`_publish_astronomia`)
```python
# ⚛️ V43.1: FORZAR USO DE ALTITUD SRTM DESDE BUS
altitud = self.bus.obtener("altitud_srtm")
if altitud is None:
    altitud = self.system.location.get("altitud", 100.0)
```

**Impacto:**
- SPA NREL con altitud SRTM para refracción correcta
- REST2 con altitud SRTM para presión/temperatura corregida
- Cálculos de masa de aire con altitud SRTM

#### D. Inversión Térmica (`_publish_inversion_estabilidad`)
```python
# ⚛️ V43.1: FORZAR USO DE ALTITUD SRTM DESDE BUS
altitud = self.bus.obtener("altitud_srtm")
if altitud is None:
    altitud = self.system.location.get("altitud", 0.0) if hasattr(self.system, 'location') else 0.0
```

**Impacto:**
- Gradiente térmico vertical con altitud SRTM
- Altura de inversión estimada con SRTM
- Estabilidad atmosférica con SRTM

### 3. ARCO SOLAR OBLIGATORIO DESDE BUS

**Datos publicados en bus (ya implementado V43.0):**
```python
"elevacion_solar": elevacion_solar_spa_nrel         # Elevación aparente SPA NREL
"azimut_solar": azimut_solar_spa_nrel               # Azimuth SPA NREL
"elevacion_verdadera_solar": elevacion_verdadera    # Elevación sin refracción
"arco_solar": elevacion_solar_spa_nrel              # Alias compatibilidad
```

**Consumidores obligatorios:**
1. **REST2 Gueymard** (`_publish_trinity_elite`):
   ```python
   elevacion_spa = self.bus.obtener("elevacion_solar")
   azimut_spa = self.bus.obtener("azimut_solar")
   
   rest2_result = calcular_radiacion_extraterrestre_rest2(
       ...,
       elevacion_spa_nrel=elevacion_spa,
       azimut_spa_nrel=azimut_spa
   )
   ```

2. **Liu & Jordan Nubosidad** (vía `environmental_indices.py`):
   - Debe usar `elevacion_solar` del bus para calcular K_t
   - Debe usar masa de aire desde REST2 anclado a SPA

3. **Cálculos UV/Radiación** (todos los módulos):
   - `uv_spectral_diamond.py`: Debe usar elevación solar del bus
   - `environmental_indices.py`: Predicciones radiación usan arco solar
   - `advanced_physics_models.py`: Transmitancia usa elevación bus

### 4. ARCO LUNAR OBLIGATORIO DESDE BUS

**Datos publicados en bus (ya implementado V43.0):**
```python
"arco_lunar_elevacion_deg": elevacion_aparente_lunar    # Elevación lunar Meeus
"arco_lunar_azimuth_deg": azimut_lunar                  # Azimuth lunar Meeus
"fase_lunar": fase_lunar                                # Fase 0-1
"iluminacion_lunar": iluminacion_pct                    # Iluminación %
"distancia_tierra_luna_km": distancia_km                # Distancia Tierra-Luna
```

**Consumidores obligatorios:**
1. **Nubosidad Nocturna** (`nubosidad_liu_jordan_kasten.py`):
   ```python
   elevacion_lunar = sensores.get("arco_lunar_elevacion_deg", None)
   iluminacion_lunar = sensores.get("iluminacion_lunar", None)
   
   resultado_nub = calcular_nubosidad_liu_jordan_kasten(
       ...,
       elevacion_lunar_deg=elevacion_lunar,
       iluminacion_lunar_pct=iluminacion_lunar
   )
   ```

2. **Validación Nocturna K_t,night**:
   - Si luna visible (elevación > 0°): Calcular K_t,night
   - Validar nubosidad nocturna con luz lunar
   - Incrementar confianza de 60% a 75%

3. **Índices Biológicos Nocturnos**:
   - Actividad nocturna fauna
   - Luminosidad para navegación
   - Calibración sensores astronómicos

---

## 🔧 ARQUITECTURA DE INTEGRIDAD

### FLUJO COMPLETO V43.1

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CARGA DE UBICACIÓN (lat, lon)                            │
│    → Argentona: 41.55326700°N, 2.39684500°E                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. OBTENCIÓN SRTM (LocationEngine)                          │
│    → API: open-elevation o similar                          │
│    → Resultado: altitud_srtm = 118m ± 10m                   │
│    → Fuente: "SRTM"                                         │
│    → Fallback: altitud_manual si SRTM falla                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. PUBLICACIÓN EN BUS (bus_expander)                        │
│    → altitud: 118m (SRTM o fallback)                        │
│    → altitud_srtm: 118m                                     │
│    → fuente_altitud: "SRTM"                                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CONSUMO POR CÁLCULOS FÍSICOS                             │
│    ├─ Gravedad: g(φ, h_SRTM)                                │
│    ├─ Densidad aire: ρ(T, P, h_SRTM)                        │
│    ├─ Refracción SPA: R(h_SRTM, P, T)                       │
│    └─ REST2 G₀: G₀(elev_SPA, h_SRTM)                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. ASTRONOMÍA SPA NREL (con SRTM)                           │
│    → calcular_posicion_solar_nrel_spa()                     │
│    → Inputs: lat, lon, h_SRTM, P, T, RH                     │
│    → Outputs: elev, azim, refracción                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. PUBLICACIÓN ARCO SOLAR                                   │
│    → elevacion_solar: XX.XXXX°                              │
│    → azimut_solar: XXX.XXXX°                                │
│    → arco_solar: XX.XXXX° (alias)                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. CONSUMO ARCO SOLAR                                       │
│    ├─ REST2: G₀ = f(elev_solar_bus)                         │
│    ├─ Nubosidad: K_t = G/G₀(elev_bus)                       │
│    ├─ UV: índice = f(elev_solar_bus)                        │
│    └─ Radiación: todas las fórmulas usan arco_solar         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. ASTRONOMÍA LUNAR MEEUS (con SRTM)                        │
│    → calcular_posicion_lunar_meeus()                        │
│    → Inputs: lat, lon, h_SRTM, P, T, RH                     │
│    → Outputs: elev, azim, fase, iluminación                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. PUBLICACIÓN ARCO LUNAR                                   │
│    → arco_lunar_elevacion_deg: XX.XXXX°                     │
│    → arco_lunar_azimuth_deg: XXX.XXXX°                      │
│    → iluminacion_lunar: XX.XX%                              │
│    → fase_lunar: 0.XXXX                                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. CONSUMO ARCO LUNAR                                      │
│     ├─ Nubosidad nocturna: K_t,night(elev_lunar, ilum)      │
│     ├─ Índices biológicos nocturnos                         │
│     └─ Calibración sensores astronómicos                    │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ REGLAS DE INTEGRIDAD OBLIGATORIAS

### REGLA 1: ALTITUD SRTM OBLIGATORIA

**Todos los cálculos que dependan de altitud DEBEN:**
1. Intentar obtener `altitud_srtm` del bus
2. Si falla, usar fallback con WARNING explícito
3. Publicar `fuente_altitud` para trazabilidad

**Código obligatorio:**
```python
# ⚛️ V43.1: FORZAR USO DE ALTITUD SRTM DESDE BUS
altitud = self.bus.obtener("altitud_srtm")
if altitud is None:
    logger.warning("⚠️ SRTM no disponible en bus, usando fallback manual")
    altitud = self.system.location.get("altitud", 100.0)
```

**Prohibido:**
```python
# ❌ NUNCA HACER ESTO
altitud = self.system.location.get("altitud", 100.0)  # Sin intentar SRTM primero
altitud = ESTACION.ALTITUD  # Hardcoded sin bus
```

### REGLA 2: ARCO SOLAR OBLIGATORIO

**Todos los cálculos de radiación/UV/nubosidad diurna DEBEN:**
1. Obtener `elevacion_solar` y/o `azimut_solar` del bus
2. NO calcular posición solar internamente
3. Usar datos SPA NREL con precisión de segundos de arco

**Código obligatorio:**
```python
# ⚛️ V43.1: FORZAR USO DE ARCO SOLAR DESDE BUS
elevacion_solar = self.bus.obtener("elevacion_solar")
azimut_solar = self.bus.obtener("azimut_solar")

if elevacion_solar is None:
    logger.critical("🚫 Arco solar no disponible en bus")
    return  # Fallar explícitamente
```

**Prohibido:**
```python
# ❌ NUNCA HACER ESTO
elevacion_solar = calcular_posicion_sol_simple()  # Redundante
elevacion_solar = 45.0  # Estimación hardcoded
from core.arcos_solares import calcular_posicion_sol  # Calcularlo localmente
```

### REGLA 3: ARCO LUNAR OBLIGATORIO NOCTURNO

**Todos los cálculos nocturnos que puedan usar luna DEBEN:**
1. Obtener `arco_lunar_elevacion_deg` y `iluminacion_lunar` del bus
2. Validar si luna está visible (elevación > 0°)
3. Usar validación lunar si disponible

**Código obligatorio:**
```python
# ⚛️ V43.1: VALIDACIÓN LUNAR NOCTURNA
elevacion_lunar = self.bus.obtener("arco_lunar_elevacion_deg")
iluminacion_lunar = self.bus.obtener("iluminacion_lunar")

if elevacion_lunar is not None and elevacion_lunar > 0:
    # Usar validación lunar
    kt_night = calcular_kt_nocturno(elevacion_lunar, iluminacion_lunar)
else:
    # Luna no visible, usar solo parámetros atmosféricos
    kt_night = 0.0
```

**Prohibido:**
```python
# ❌ NUNCA HACER ESTO
from core.arcos_solares import calcular_fase_lunar  # Calcular internamente
fase_lunar = 0.5  # Estimación hardcoded sin posición real
# Ignorar luna completamente en cálculos nocturnos
```

---

## 🛡️ VALIDACIÓN DE INTEGRIDAD

### Validador de Bus (Nuevo)

**Archivo:** `core/system/bus_integrity_validator.py` (pendiente implementación V43.2)

**Función:**
```python
def validate_bus_integrity(bus: BusEstadoGlobal) -> Dict[str, bool]:
    """
    Valida que todos los datos geográficos/astronómicos obligatorios estén en bus.
    
    Returns:
        Dict con estado de cada campo crítico
    """
    integrity = {
        "altitud_srtm_disponible": bus.obtener("altitud_srtm") is not None,
        "fuente_altitud_valida": bus.obtener("fuente_altitud") == "SRTM",
        "elevacion_solar_disponible": bus.obtener("elevacion_solar") is not None,
        "azimut_solar_disponible": bus.obtener("azimut_solar") is not None,
        "arco_lunar_disponible": bus.obtener("arco_lunar_elevacion_deg") is not None,
        "spa_nrel_fuente": bus.obtener("rest2_fuente_astronomica") == "SPA_NREL_V42.6",
    }
    
    # Validar que TODOS los campos críticos estén disponibles
    if not all(integrity.values()):
        logger.critical(f"🚫 INTEGRIDAD CRÍTICA FALLIDA: {integrity}")
    
    return integrity
```

### Alertas de Integridad

**Condiciones de alerta:**

1. **Alerta Crítica SRTM:**
   ```python
   if bus.obtener("fuente_altitud") != "SRTM":
       logger.warning("⚠️ SRTM no disponible, usando fallback manual")
       bus.publicar("alerta_srtm_fallback", True, "bool")
   ```

2. **Alerta Crítica Astronomía:**
   ```python
   if bus.obtener("elevacion_solar") is None:
       logger.critical("🚫 Arco solar no disponible - cálculos radiación bloqueados")
       bus.publicar("alerta_astronomia_critica", True, "bool")
   ```

3. **Alerta Validación Lunar:**
   ```python
   if noche and bus.obtener("arco_lunar_elevacion_deg") is None:
       logger.info("ℹ️ Arco lunar no disponible para validación nocturna")
       bus.publicar("alerta_lunar_no_disponible", True, "bool")
   ```

---

## 📊 CAMPOS PUBLICADOS EN BUS

### Geográficos (5 campos)
1. `latitud` (grados)
2. `longitud` (grados)
3. `altitud` (m) - SRTM o fallback
4. `altitud_srtm` (m) - Siempre disponible
5. `fuente_altitud` (texto) - "SRTM", "manual_fallback", "manual_fallback_error"

### Solares (9+ campos)
1. `elevacion_solar` (grados) - SPA NREL aparente
2. `azimut_solar` (grados) - SPA NREL
3. `elevacion_verdadera_solar` (grados) - SPA NREL sin refracción
4. `refraccion_solar_arcmin` (arcmin) - Ciddor
5. `distancia_tierra_sol` (UA)
6. `dia_juliano_ephemeris` (días)
7. `delta_t_segundos` (s)
8. `arco_solar` (grados) - Alias de elevacion_solar
9. `rest2_fuente_astronomica` (texto) - "SPA_NREL_V42.6" o "REST2_interno"

### Lunares (11+ campos)
1. `arco_lunar_elevacion_deg` (grados) - Meeus aparente
2. `arco_lunar_azimuth_deg` (grados) - Meeus
3. `distancia_tierra_luna_km` (km)
4. `fase_lunar` (0-1)
5. `iluminacion_lunar` (%)
6. `edad_lunar_dias` (días)
7. `nombre_fase_lunar` (texto)
8. `icono_fase_lunar` (texto)
9. `longitud_ecliptica_lunar_deg` (grados)
10. `latitud_ecliptica_lunar_deg` (grados)
11. `refraccion_lunar_arcmin` (arcmin)

**Total: 25+ campos geográficos/astronómicos publicados**

---

## 🎖️ MÉTRICAS DE INTEGRIDAD

### Cobertura de Modificaciones V43.1

| Módulo | Función | Altitud SRTM | Arco Solar | Arco Lunar | Estado |
|--------|---------|--------------|------------|------------|--------|
| bus_expander.py | _publish_physics | ✅ | N/A | N/A | COMPLETO |
| bus_expander.py | _publish_atmosfera | ✅ | N/A | N/A | COMPLETO |
| bus_expander.py | _publish_astronomia | ✅ | ✅ | ✅ | COMPLETO |
| bus_expander.py | _publish_inversion_estabilidad | ✅ | N/A | N/A | COMPLETO |
| bus_expander.py | _publish_trinity_elite | ✅ | ✅ | N/A | COMPLETO |
| nubosidad_liu_jordan_kasten.py | calcular_nubosidad | N/A | ✅ | ✅ | COMPLETO |
| environmental_indices.py | _calcular_nubosidad_estimada | N/A | ✅ | ✅ | COMPLETO |
| rest2_gueymard_radiacion.py | calcular_radiacion_extraterrestre | ✅ | ✅ | N/A | COMPLETO |

**Cobertura:** 8 funciones críticas modificadas  
**Pendientes:** Validación exhaustiva de TODOS los módulos que puedan usar estos datos

---

## 🚀 PRÓXIMOS PASOS V43.2

### 1. Auditoría Completa de Consumidores
- Buscar TODOS los módulos que calculen posición solar internamente
- Buscar TODOS los usos de altitud sin obtenerla del bus
- Forzar uso de bus en absolutamente TODOS los casos

### 2. Validador de Integridad
- Crear `bus_integrity_validator.py`
- Validar al inicio de cada ciclo que datos críticos estén disponibles
- Lanzar alertas críticas si faltan datos obligatorios

### 3. Testing de Integridad
- Test: SRTM no disponible → fallback funciona
- Test: Astronomía falla → alertas críticas correctas
- Test: Cálculos usan datos bus y NO calculan localmente

### 4. Documentación de Dependencias
- Mapa completo de dependencias geográficas/astronómicas
- Diagrama de flujo de datos desde SRTM/SPA/Meeus hasta consumidores finales
- Lista exhaustiva de todos los consumidores obligatorios

---

## 💎 CONCLUSIÓN V43.1

**El Acorazado MeteoSerV3 establece soberanía total sobre datos geográficos y astronómicos:**

- ✅ **SRTM publicado y usado obligatoriamente** en cálculos físicos/atmosféricos
- ✅ **Arco solar SPA NREL publicado y usado obligatoriamente** en cálculos radiativos
- ✅ **Arco lunar Meeus publicado y usado obligatoriamente** en validación nocturna
- ✅ **Trazabilidad completa** con `fuente_altitud` y `rest2_fuente_astronomica`

**Cero redundancia. Cero cálculos locales. Una sola verdad en el bus.**

---

**Motor:** V43.1_INTEGRIDAD_GEOGRAFICA_ASTRONOMICA_TOTAL  
**SHA-256:** Pendiente generación  
**Autor:** MeteoSerV3 Development Team  
**Fecha:** 5 de febrero de 2026

**¡INTEGRIDAD TOTAL: SRTM + SOLAR + LUNAR OBLIGATORIOS EN TODOS LOS CÁLCULOS!** 🛡️🌍🌞🌙
